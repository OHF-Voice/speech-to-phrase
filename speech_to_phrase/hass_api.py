"""Home Assistant API."""

import hashlib
import logging
import json
import re
from collections.abc import Generator
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Set, Union

import aiohttp

_LOGGER = logging.getLogger(__name__)

RGB_MODES = {"hs", "rgb", "rgbw", "rgbww", "xy"}
BRIGHTNESS_MODES = RGB_MODES | {"brightness", "white"}
FAN_SET_SPEED = 1
COVER_SET_POSITION = 4
MEDIA_PLAYER_PAUSE = 1
MEDIA_PLAYER_VOLUME_SET = 4
MEDIA_PLAYER_NEXT_TRACK = 32


@dataclass
class Entity:
    """Home Assistant entity."""

    names: List[str]
    domain: str

    # Domain-specific features
    light_supports_color: Optional[bool] = None
    light_supports_brightness: Optional[bool] = None
    fan_supports_speed: Optional[bool] = None
    cover_supports_position: Optional[bool] = None
    media_player_supports_pause: Optional[bool] = None
    media_player_supports_volume_set: Optional[bool] = None
    media_player_supports_next_track: Optional[bool] = None

    _hash: str = ""

    def get_hash(self) -> str:
        """Get a stable hash for this entity."""
        if not self._hash:
            hasher = hashlib.sha256()

            hasher.update(self.domain.encode("utf-8"))

            for supports_field in fields(self):
                if "supports" not in supports_field.name:
                    continue

                supports_value = getattr(self, supports_field.name)
                if supports_value is None:
                    continue

                hasher.update(f"{supports_field.name}={supports_value}".encode("utf-8"))

            for name in sorted(self.names):
                hasher.update(name.encode("utf-8"))

            self._hash = hasher.hexdigest()

        return self._hash


@dataclass
class Area:
    """Home Assistant area."""

    names: List[str]
    _hash: str = ""

    def get_hash(self) -> str:
        """Get a stable hash for this area."""
        if not self._hash:
            hasher = hashlib.sha256()

            for name in sorted(self.names):
                hasher.update(name.encode("utf-8"))

            self._hash = hasher.hexdigest()

        return self._hash


@dataclass
class Floor:
    """Home Assistant floor."""

    names: List[str]
    _hash: str = ""

    def get_hash(self) -> str:
        """Get a stable hash for this floor."""
        if not self._hash:
            hasher = hashlib.sha256()

            for name in sorted(self.names):
                hasher.update(name.encode("utf-8"))

            self._hash = hasher.hexdigest()

        return self._hash


@dataclass
class Things:
    """Exposed things in Home Assistant."""

    entities: List[Entity] = field(default_factory=list)
    areas: List[Area] = field(default_factory=list)
    floors: List[Floor] = field(default_factory=list)
    extra_sentences: List[str] = field(default_factory=list)
    custom_sentences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _hash: str = ""

    def get_hash(self) -> str:
        """Get a stable hash for all the things."""
        if not self._hash:
            hasher = hashlib.sha256()

            for entity_hash in sorted(e.get_hash() for e in self.entities):
                hasher.update(entity_hash.encode("utf-8"))

            for area_hash in sorted(e.get_hash() for e in self.entities):
                hasher.update(area_hash.encode("utf-8"))

            for floor_hash in sorted(e.get_hash() for e in self.entities):
                hasher.update(floor_hash.encode("utf-8"))

            for extra_sentence in sorted(self.extra_sentences):
                hasher.update(extra_sentence.encode("utf-8"))

            for lang, lang_sentences in sorted(self.custom_sentences.items()):
                hasher.update(lang.encode("utf-8"))
                hasher.update(json.dumps(lang_sentences).encode("utf-8"))

            self._hash = hasher.hexdigest()

        return self._hash

    def to_lists_dict(self) -> Dict[str, Any]:
        """Get lists dictionary for hassil intents."""
        lists_dict: Dict[str, Any] = {}
        lists_dict["name"] = {
            "values": [
                {
                    "in": _remove_template_syntax(e_name),
                    "out": e_name,
                    "context": _get_context(e),
                    # Used for tests
                    "metadata": {"domain": e.domain},
                }
                for e in self.entities
                for e_name in e.names
            ]
        }

        lists_dict["area"] = {
            "values": [a_name for a in self.areas for a_name in a.names]
        }

        lists_dict["floor"] = {
            "values": [f_name for f in self.floors for f_name in f.names]
        }

        return lists_dict

    @staticmethod
    def from_dict(things_dict: Dict[str, Any]) -> "Things":
        """Load things from a dict."""
        return Things(
            entities=[
                Entity(
                    names=_coerce_list(entity_dict["name"]),
                    domain=entity_dict["domain"],
                    light_supports_brightness=entity_dict.get(
                        "light_supports_brightness"
                    ),
                    light_supports_color=entity_dict.get("light_supports_color"),
                    fan_supports_speed=entity_dict.get("fan_supports_speed"),
                    cover_supports_position=entity_dict.get("cover_supports_position"),
                    media_player_supports_pause=entity_dict.get(
                        "media_player_supports_pause"
                    ),
                    media_player_supports_volume_set=entity_dict.get(
                        "media_player_supports_volume_set"
                    ),
                    media_player_supports_next_track=entity_dict.get(
                        "media_player_supports_next_track"
                    ),
                )
                for entity_dict in things_dict.get("entities", [])
            ],
            areas=[
                Area(names=_coerce_list(area_dict["name"]))
                for area_dict in things_dict.get("areas", [])
            ],
            floors=[
                Floor(names=_coerce_list(floor_dict["name"]))
                for floor_dict in things_dict.get("floors", [])
            ],
        )


def _get_context(entity: Entity) -> Dict[str, Any]:
    """Get context dictionary for an entity."""
    context = {"domain": entity.domain}
    for supports_field in fields(entity):
        if "supports" not in supports_field.name:
            continue

        supports_value = getattr(entity, supports_field.name)
        if supports_value is not None:
            context[supports_field.name] = supports_value

    return context


def _remove_template_syntax(name: str) -> str:
    """Remove template syntax from a name."""
    return re.sub(r"[{}\[\]<>()]", "", name)


def _coerce_list(str_or_list: Union[str, List[str]]) -> List[str]:
    if isinstance(str_or_list, str):
        return [str_or_list]

    return str_or_list


@dataclass
class HomeAssistantInfo:
    """Information loaded from Home Assistant websocket API."""

    system_language: str
    things: Things
    pipeline_languages: Set[str] = field(default_factory=set)


async def get_hass_info(token: str, uri: str) -> HomeAssistantInfo:
    """Use HA websocket API to get exposed entities/areas/floors."""
    things = Things()
    pipeline_languages: Set[str] = set()

    current_id = 0

    def next_id() -> int:
        nonlocal current_id
        current_id += 1
        return current_id

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(uri, max_msg_size=0) as websocket:
            # Authenticate
            msg = await websocket.receive_json()
            assert msg["type"] == "auth_required", msg

            await websocket.send_json(
                {
                    "type": "auth",
                    "access_token": token,
                }
            )

            msg = await websocket.receive_json()
            assert msg["type"] == "auth_ok", msg

            # Get system language
            await websocket.send_json({"id": next_id(), "type": "get_config"})

            msg = await websocket.receive_json()
            assert msg["success"], msg

            system_language: str = msg["result"]["language"]

            # Get pipeline STT languages
            await websocket.send_json(
                {"id": next_id(), "type": "assist_pipeline/pipeline/list"}
            )
            msg = await websocket.receive_json()
            assert msg["success"], msg

            for pipeline in msg["result"]["pipelines"]:
                stt_language = pipeline.get("stt_language")
                if stt_language:
                    pipeline_languages.add(stt_language)

            # Get exposed entities
            await websocket.send_json(
                {"id": next_id(), "type": "homeassistant/expose_entity/list"}
            )

            msg = await websocket.receive_json()
            assert msg["success"], msg

            entity_ids = []
            for entity_id, exposed_info in msg["result"]["exposed_entities"].items():
                if exposed_info.get("conversation"):
                    entity_ids.append(entity_id)

            await websocket.send_json(
                {
                    "id": next_id(),
                    "type": "get_states",
                }
            )
            msg = await websocket.receive_json()
            assert msg["success"], msg
            states = {s["entity_id"]: s for s in msg["result"]}

            # Get device info
            # await websocket.send_json(
            #     {"id": next_id(), "type": "config/device_registry/list"}
            # )
            # msg = await websocket.receive_json()
            # assert msg["success"], msg
            # devices = {device_info["id"]: device_info for device_info in msg["result"]}

            # Floors
            await websocket.send_json(
                {"id": next_id(), "type": "config/floor_registry/list"}
            )
            msg = await websocket.receive_json()
            assert msg["success"], msg
            floors = {
                floor_info["floor_id"]: floor_info for floor_info in msg["result"]
            }
            for floor_info in floors.values():
                names = [floor_info["name"]]
                names.extend(floor_info.get("aliases", []))
                things.floors.append(Floor(names=[name.strip() for name in names]))

            # Areas
            await websocket.send_json(
                {"id": next_id(), "type": "config/area_registry/list"}
            )
            msg = await websocket.receive_json()
            assert msg["success"], msg
            areas = {area_info["area_id"]: area_info for area_info in msg["result"]}
            for area_info in areas.values():
                names = [area_info["name"]]
                names.extend(area_info.get("aliases", []))
                things.areas.append(Area(names=[name.strip() for name in names]))

            # Contains aliases
            # Check area_id as well as area of device_id
            # Use original_device_class
            await websocket.send_json(
                {
                    "id": next_id(),
                    "type": "config/entity_registry/get_entries",
                    "entity_ids": entity_ids,
                }
            )

            msg = await websocket.receive_json()
            assert msg["success"], msg
            for entity_id, entity_info in msg["result"].items():
                domain = entity_id.split(".")[0]
                name = None
                names = []

                if entity_info:
                    if entity_info.get("disabled_by") is not None:
                        # Skip disabled entities
                        continue

                    name = entity_info.get("name") or entity_info["original_name"]
                    names.extend(entity_info.get("aliases", []))

                attributes = states.get(entity_id, {}).get("attributes", {})
                if not name:
                    # Try friendly name
                    name = attributes.get("friendly_name")

                if name:
                    names.append(name)

                supported_features = attributes.get("supported_features", 0)

                # Domain-specific features
                light_supports_color: Optional[bool] = None
                light_supports_brightness: Optional[bool] = None
                fan_supports_speed: Optional[bool] = None
                cover_supports_position: Optional[bool] = None
                media_player_supports_pause: Optional[bool] = None
                media_player_supports_volume_set: Optional[bool] = None
                media_player_supports_next_track: Optional[bool] = None

                if domain == "light":
                    color_modes = set(attributes.get("supported_color_modes", []))
                    light_supports_color = not RGB_MODES.isdisjoint(color_modes)
                    light_supports_brightness = not BRIGHTNESS_MODES.isdisjoint(
                        color_modes
                    )
                elif domain == "fan":
                    fan_supports_speed = (
                        supported_features & FAN_SET_SPEED
                    ) == FAN_SET_SPEED
                elif domain == "cover":
                    cover_supports_position = (
                        supported_features & COVER_SET_POSITION
                    ) == COVER_SET_POSITION
                elif domain == "media_player":
                    media_player_supports_pause = (
                        supported_features & MEDIA_PLAYER_PAUSE
                    ) == MEDIA_PLAYER_PAUSE
                    media_player_supports_volume_set = (
                        supported_features & MEDIA_PLAYER_VOLUME_SET
                    ) == MEDIA_PLAYER_VOLUME_SET
                    media_player_supports_next_track = (
                        supported_features & MEDIA_PLAYER_NEXT_TRACK
                    ) == MEDIA_PLAYER_NEXT_TRACK

                things.entities.append(
                    Entity(
                        names=[name.strip() for name in names],
                        domain=domain,
                        light_supports_color=light_supports_color,
                        light_supports_brightness=light_supports_brightness,
                        fan_supports_speed=fan_supports_speed,
                        cover_supports_position=cover_supports_position,
                        media_player_supports_pause=media_player_supports_pause,
                        media_player_supports_volume_set=media_player_supports_volume_set,
                        media_player_supports_next_track=media_player_supports_next_track,
                    )
                )

            # Get sentences from sentence triggers
            await websocket.send_json(
                {"id": next_id(), "type": "conversation/sentences/list"}
            )
            msg = await websocket.receive_json()
            if msg["success"]:
                things.extra_sentences.extend(set(msg["result"]["trigger_sentences"]))

            # Get ask_question answers
            for entity_id, state in states.items():
                domain = entity_id.split(".", maxsplit=1)[0]
                if domain not in ("automation", "script"):
                    continue

                if (domain == "automation") and (state.get("state") != "on"):
                    # Ignore disabled automations
                    continue

                await websocket.send_json(
                    {
                        "id": next_id(),
                        "type": f"{domain}/config",
                        "entity_id": entity_id,
                    }
                )
                msg = await websocket.receive_json()
                if not msg["success"]:
                    continue

                entity_config = msg["result"]["config"]
                for answer_sentence in _find_ask_question_answers(entity_config):
                    if "{{" in answer_sentence:
                        # Skip sentences with HA template variables
                        continue

                    things.extra_sentences.append(answer_sentence)

            # Get custom sentences
            await websocket.send_json(
                {
                    "id": next_id(),
                    "type": "conversation/agent/homeassistant/custom_sentences",
                }
            )
            msg = await websocket.receive_json()
            if msg["success"]:
                things.custom_sentences = msg["result"]

    return HomeAssistantInfo(
        system_language=system_language,
        things=things,
        pipeline_languages=pipeline_languages,
    )


def _find_ask_question_answers(item: Any) -> Generator[str]:
    """Yields answer sentences from automation or script config for ask_question."""
    if isinstance(item, dict):
        if item.get("action") == "assist_satellite.ask_question":
            for answer in item.get("data", {}).get("answers", []):
                sentences = answer.get("sentences", [])
                if isinstance(sentences, str):
                    # Single sentence
                    yield sentences
                else:
                    # List of sentences
                    yield from sentences
        else:
            for sub_item in item.values():
                yield from _find_ask_question_answers(sub_item)
    elif isinstance(item, list):
        for sub_item in item:
            yield from _find_ask_question_answers(sub_item)
