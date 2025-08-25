"""Tests for Home Assistant API."""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from speech_to_phrase.hass_api import Entity, Things, get_hass_info


class MockWebsocket:
    """Mock websocket responses from Home Assistant server."""

    def __init__(
        self,
        responses: List[
            Union[
                Tuple[Optional[str], Dict[str, Any]],
                Tuple[Optional[str], Dict[str, Any], Dict[str, Any]],
            ]
        ],
    ) -> None:
        # list of (type, response) tuples
        self.responses = responses

        self._next_msg: Optional[Dict[str, Any]] = None

    async def receive_json(self) -> Dict[str, Any]:
        """Get next response message."""
        assert self.responses

        response = self.responses[0]
        expected_msg: Optional[Dict[str, Any]] = None

        if len(response) == 3:
            response_type, response_data, expected_msg = response
        else:
            response_type, response_data = response

        if response_type:
            assert self._next_msg
            assert response_type == self._next_msg["type"]

        if expected_msg:
            assert self._next_msg
            for key, value in expected_msg.items():
                assert key in self._next_msg
                assert self._next_msg[key] == value

        self.responses = self.responses[1:]
        self._next_msg = None

        response_data["success"] = True
        return response_data

    async def send_json(self, msg):
        """Set type of next command."""
        self._next_msg = msg

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


def _make_session(mock_websocket: MockWebsocket) -> AsyncMock:
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.ws_connect = MagicMock(return_value=mock_websocket)

    return mock_session


def test_template_syntax_removed() -> None:
    """Test that entity names have template syntax removed."""
    things = Things(
        entities=[
            Entity(names=["<test> {entity} [with] (template) syntax>]("], domain="test")
        ],
        areas=[],
        floors=[],
    )
    assert things.to_lists_dict() == {
        "area": {"values": []},
        "floor": {"values": []},
        "name": {
            "values": [
                {
                    "in": "test entity with template syntax",
                    "out": "<test> {entity} [with] (template) syntax>](",
                    "context": {"domain": "test"},
                    "metadata": {"domain": "test"},
                }
            ]
        },
    }


@pytest.mark.asyncio
async def test_system_and_pipeline_languages() -> None:
    """Test retrieval of HA system language and pipeline STT languages."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {
                    "result": {
                        "pipelines": [{"stt_language": "de"}, {"stt_language": "nl"}]
                    }
                },
            ),
            (
                "homeassistant/expose_entity/list",
                {"result": {"exposed_entities": {}}},
            ),
            ("get_states", {"result": []}),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            ("config/entity_registry/get_entries", {"result": {}}),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": ["trigger 1", "trigger 2"]}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert ha_info.system_language == "en"
        assert ha_info.pipeline_languages == {"de", "nl"}
        assert set(ha_info.things.extra_sentences) == {"trigger 1", "trigger 2"}


@pytest.mark.asyncio
async def test_unexposed_and_disabled_entities() -> None:
    """Test that unexposed and disabled entities are skipped."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": []}},
            ),
            (
                "homeassistant/expose_entity/list",
                {
                    "result": {
                        "exposed_entities": {
                            "light.unexposed_light": {"conversation": False},
                            "light.disabled_light": {"conversation": True},
                        }
                    }
                },
            ),
            (
                "get_states",
                {
                    "result": [
                        {"entity_id": "light.unexposed_light"},
                        {
                            "entity_id": "light.disabled_light",
                        },
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            (
                "config/entity_registry/get_entries",
                {
                    "result": {
                        "light.disabled_light": {
                            "name": "Disabled Light",
                            "disabled_by": {},
                        },
                    }
                },
                {"entity_ids": ["light.disabled_light"]},
            ),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert not ha_info.things.entities


@pytest.mark.asyncio
async def test_areas_and_floors() -> None:
    """Test retrieval of areas and floors."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": []}},
            ),
            ("homeassistant/expose_entity/list", {"result": {"exposed_entities": {}}}),
            ("get_states", {"result": []}),
            (
                "config/floor_registry/list",
                {
                    "result": [
                        {
                            "floor_id": "floor_1",
                            "name": "Floor 1",
                            "aliases": ["Floor One"],
                        }
                    ]
                },
            ),
            (
                "config/area_registry/list",
                {
                    "result": [
                        {"area_id": "area_1", "name": "Area 1", "aliases": ["Area One"]}
                    ]
                },
            ),
            ("config/entity_registry/get_entries", {"result": {}}),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert len(ha_info.things.areas) == 1
        area = ha_info.things.areas[0]
        assert area.names == ["Area 1", "Area One"]

        assert len(ha_info.things.floors) == 1
        floor = ha_info.things.floors[0]
        assert floor.names == ["Floor 1", "Floor One"]


@pytest.mark.asyncio
async def test_entity_names() -> None:
    """Test retrieval of entity names."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": []}},
            ),
            (
                "homeassistant/expose_entity/list",
                {
                    "result": {
                        "exposed_entities": {
                            "light.friendly_name": {"conversation": True},
                            "light.registry_name": {"conversation": True},
                            "light.original_name": {"conversation": True},
                        }
                    }
                },
            ),
            (
                "get_states",
                {
                    "result": [
                        {
                            "entity_id": "light.friendly_name",
                            "attributes": {"friendly_name": "Friendly Name"},
                        }
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            (
                "config/entity_registry/get_entries",
                {
                    "result": {
                        "light.friendly_name": {},
                        "light.registry_name": {"name": "Registry Name"},
                        "light.original_name": {"original_name": "Original Name"},
                    }
                },
            ),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert len(ha_info.things.entities) == 3

        names: Set[str] = set()
        for entity in ha_info.things.entities:
            assert entity.domain == "light"
            assert len(entity.names) == 1
            names.add(entity.names[0])

        assert names == {"Friendly Name", "Registry Name", "Original Name"}


@pytest.mark.asyncio
async def test_light_features() -> None:
    """Test that light entities report supported features."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": [{"stt_language": "de"}]}},
            ),
            (
                "homeassistant/expose_entity/list",
                {
                    "result": {
                        "exposed_entities": {
                            "light.rgb_light": {"conversation": True},
                            "light.brightness_only_light": {"conversation": True},
                        }
                    }
                },
            ),
            (
                "get_states",
                {
                    "result": [
                        {
                            "entity_id": "light.rgb_light",
                            "attributes": {
                                "friendly_name": "RGB Light",
                                "supported_color_modes": ["rgb"],
                            },
                        },
                        {
                            "entity_id": "light.brightness_only_light",
                            "attributes": {
                                "friendly_name": "Brightness Only Light",
                                "supported_color_modes": ["brightness"],
                            },
                        },
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            (
                "config/entity_registry/get_entries",
                {
                    "result": {
                        "light.rgb_light": {},
                        "light.brightness_only_light": {},
                    }
                },
            ),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert len(ha_info.things.entities) == 2

        rgb_light = next(e for e in ha_info.things.entities if "RGB Light" in e.names)
        assert rgb_light.domain == "light"
        assert rgb_light.light_supports_color
        assert rgb_light.light_supports_brightness

        brightness_only_light = next(
            e for e in ha_info.things.entities if "Brightness Only Light" in e.names
        )
        assert brightness_only_light.domain == "light"
        assert brightness_only_light.light_supports_brightness
        assert not brightness_only_light.light_supports_color


@pytest.mark.asyncio
async def test_fan_features() -> None:
    """Test that fan entities report supported features."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": [{"stt_language": "de"}]}},
            ),
            (
                "homeassistant/expose_entity/list",
                {
                    "result": {
                        "exposed_entities": {
                            "fan.with_speed": {"conversation": True},
                            "fan.without_speed": {"conversation": True},
                        }
                    }
                },
            ),
            (
                "get_states",
                {
                    "result": [
                        {
                            "entity_id": "fan.with_speed",
                            "attributes": {
                                "friendly_name": "Fan With Speed",
                                "supported_features": 1,  # SET_SPEED
                            },
                        },
                        {
                            "entity_id": "fan.without_speed",
                            "attributes": {
                                "friendly_name": "Fan Without Speed",
                                "supported_features": 0,
                            },
                        },
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            (
                "config/entity_registry/get_entries",
                {
                    "result": {
                        "fan.with_speed": {},
                        "fan.without_speed": {},
                    }
                },
            ),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert len(ha_info.things.entities) == 2

        speed_fan = next(
            e for e in ha_info.things.entities if "Fan With Speed" in e.names
        )
        assert speed_fan.domain == "fan"
        assert speed_fan.fan_supports_speed

        no_speed_fan = next(
            e for e in ha_info.things.entities if "Fan Without Speed" in e.names
        )
        assert no_speed_fan.domain == "fan"
        assert not no_speed_fan.fan_supports_speed


@pytest.mark.asyncio
async def test_cover_features() -> None:
    """Test that cover entities report supported features."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": [{"stt_language": "de"}]}},
            ),
            (
                "homeassistant/expose_entity/list",
                {
                    "result": {
                        "exposed_entities": {
                            "cover.with_position": {"conversation": True},
                            "cover.without_position": {"conversation": True},
                        }
                    }
                },
            ),
            (
                "get_states",
                {
                    "result": [
                        {
                            "entity_id": "cover.with_position",
                            "attributes": {
                                "friendly_name": "Cover With Position",
                                "supported_features": 4,  # SET_POSITION
                            },
                        },
                        {
                            "entity_id": "cover.without_position",
                            "attributes": {
                                "friendly_name": "Cover Without Position",
                                "supported_features": 0,
                            },
                        },
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            (
                "config/entity_registry/get_entries",
                {
                    "result": {
                        "cover.with_position": {},
                        "cover.without_position": {},
                    }
                },
            ),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert len(ha_info.things.entities) == 2

        position_cover = next(
            e for e in ha_info.things.entities if "Cover With Position" in e.names
        )
        assert position_cover.domain == "cover"
        assert position_cover.cover_supports_position

        no_position_cover = next(
            e for e in ha_info.things.entities if "Cover Without Position" in e.names
        )
        assert no_position_cover.domain == "cover"
        assert not no_position_cover.cover_supports_position


@pytest.mark.asyncio
async def test_media_player_features() -> None:
    """Test that media player entities report supported features."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": [{"stt_language": "de"}]}},
            ),
            (
                "homeassistant/expose_entity/list",
                {
                    "result": {
                        "exposed_entities": {
                            "media_player.with_extra": {"conversation": True},
                            "media_player.without_extra": {"conversation": True},
                        }
                    }
                },
            ),
            (
                "get_states",
                {
                    "result": [
                        {
                            "entity_id": "media_player.with_extra",
                            "attributes": {
                                "friendly_name": "Media Player With Extra",
                                "supported_features": 1  # PAUSE
                                | 4  # VOLUME_SET
                                | 32,  # NEXT_TRACK
                            },
                        },
                        {
                            "entity_id": "media_player.without_extra",
                            "attributes": {
                                "friendly_name": "Media Player Without Extra",
                                "supported_features": 0,
                            },
                        },
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            (
                "config/entity_registry/get_entries",
                {
                    "result": {
                        "media_player.with_extra": {},
                        "media_player.without_extra": {},
                    }
                },
            ),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert len(ha_info.things.entities) == 2

        extra_media_player = next(
            e for e in ha_info.things.entities if "Media Player With Extra" in e.names
        )
        assert extra_media_player.domain == "media_player"
        assert extra_media_player.media_player_supports_pause
        assert extra_media_player.media_player_supports_volume_set
        assert extra_media_player.media_player_supports_next_track

        no_extra_media_player = next(
            e
            for e in ha_info.things.entities
            if "Media Player Without Extra" in e.names
        )
        assert no_extra_media_player.domain == "media_player"
        assert not no_extra_media_player.media_player_supports_pause
        assert not no_extra_media_player.media_player_supports_volume_set
        assert not no_extra_media_player.media_player_supports_next_track


@pytest.mark.asyncio
async def test_automation_script_answers() -> None:
    """Test retrieval of ask_question answers for scripts and automations."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": [{"stt_language": "en"}]}},
            ),
            (
                "homeassistant/expose_entity/list",
                {"result": {"exposed_entities": {}}},
            ),
            (
                "get_states",
                {
                    "result": [
                        {"entity_id": "automation.test_automation", "state": "on"},
                        {"entity_id": "script.test_script", "state": "off"},
                    ]
                },
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            ("config/entity_registry/get_entries", {"result": {}}),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            (
                "automation/config",
                {
                    "result": {
                        "config": {
                            "actions": [
                                {
                                    "action": "assist_satellite.ask_question",
                                    "data": {
                                        "answers": [
                                            {
                                                "sentences": [
                                                    "answer 1",
                                                    "answer with {{ variable }}",
                                                ]
                                            }
                                        ]
                                    },
                                }
                            ]
                        }
                    }
                },
            ),
            (
                "script/config",
                {
                    "result": {
                        "config": {
                            "sequence": [
                                {
                                    "action": "assist_satellite.ask_question",
                                    "data": {
                                        "answers": [
                                            {
                                                "sentences": [
                                                    "answer 2",
                                                    "answer with {{ variable }}",
                                                ]
                                            }
                                        ]
                                    },
                                }
                            ]
                        }
                    }
                },
            ),
            ("conversation/agent/homeassistant/custom_sentences", {"result": {}}),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert set(ha_info.things.extra_sentences) == {"answer 1", "answer 2"}


@pytest.mark.asyncio
async def test_custom_sentences() -> None:
    """Test retrieval of custom sentences."""
    mock_websocket = MockWebsocket(
        [
            (None, {"type": "auth_required"}),
            ("auth", {"type": "auth_ok"}),
            ("get_config", {"result": {"language": "en"}}),
            (
                "assist_pipeline/pipeline/list",
                {"result": {"pipelines": [{"stt_language": "en"}]}},
            ),
            (
                "homeassistant/expose_entity/list",
                {"result": {"exposed_entities": {}}},
            ),
            (
                "get_states",
                {"result": []},
            ),
            ("config/floor_registry/list", {"result": []}),
            ("config/area_registry/list", {"result": []}),
            ("config/entity_registry/get_entries", {"result": {}}),
            (
                "conversation/sentences/list",
                {"result": {"trigger_sentences": []}},
            ),
            (
                "conversation/agent/homeassistant/custom_sentences",
                {
                    "result": {
                        "en": {
                            "language": "en",
                            "intents": {
                                "TestIntent": {"data": {"sentences": ["test sentence"]}}
                            },
                        }
                    }
                },
            ),
        ]
    )

    with patch("aiohttp.ClientSession", return_value=_make_session(mock_websocket)):
        ha_info = await get_hass_info("<token>", "<url>")
        assert ha_info.things.custom_sentences == {
            "en": {
                "language": "en",
                "intents": {"TestIntent": {"data": {"sentences": ["test sentence"]}}},
            }
        }
