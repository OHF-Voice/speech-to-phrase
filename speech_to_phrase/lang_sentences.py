"""Lists and sentences for a language."""

import itertools
import re
from dataclasses import dataclass, fields
from typing import Any, Optional

from hassil import SlotList, TextChunk, TextSlotList, TextSlotValue


@dataclass
class SentenceBlock:
    """Block of sentence templates"""

    sentences: list[str]
    domains: Optional[set[str]] = None
    device_class: Optional[set[str]] = None

    # Domain-specific features
    light_supports_color: Optional[bool] = None
    light_supports_brightness: Optional[bool] = None
    fan_supports_speed: Optional[bool] = None
    cover_supports_position: Optional[bool] = None
    media_player_supports_pause: Optional[bool] = None
    media_player_supports_volume_set: Optional[bool] = None
    media_player_supports_next_track: Optional[bool] = None

    @staticmethod
    def from_dict(block_dict: dict[str, Any]) -> "SentenceBlock":
        block = SentenceBlock(
            sentences=block_dict["sentences"],
            domains=set(block_dict["domains"]),
            device_class=set(block_dict["device_class"]),
        )

        for supports_field in fields(block):
            if "supports" not in supports_field.name:
                continue

            setattr(block, supports_field.name, block_dict.get(supports_field.name))

        return block

    def to_data(self) -> dict[str, Any]:
        """Convert to data dict."""
        data: dict[str, Any] = {"sentences": self.sentences}

        context: dict[str, Any] = {}
        if self.domains:
            context["domain"] = list(self.domains)

        if self.device_class:
            context["device_class"] = list(self.device_class)

        for supports_field in fields(self):
            if "supports" not in supports_field.name:
                continue

            supports_value = getattr(self, supports_field.name)
            if supports_value is not None:
                context[supports_field.name] = supports_value

        if context:
            data["requires_context"] = context

        return data


@dataclass
class Transformation:
    """Single transformation."""

    outputs: list[str]
    match_regex: Optional[re.Pattern] = None


@dataclass
class TransformedList:
    """Transformations to apply to a list's values."""

    source_list_name: str
    transformations: list[Transformation]

    def apply(self, value: str) -> list[str]:
        """Generate output values."""
        for transformation in self.transformations:
            if transformation.match_regex is not None:
                if not transformation.match_regex.search(value):
                    continue

            return [
                output_str.format(value=value) for output_str in transformation.outputs
            ]

        return [value]


@dataclass
class LanguageData:
    """Lists and sentences for a language."""

    language: str
    sentence_blocks: list[SentenceBlock]
    list_values: dict[str, list[str]]
    expansion_rules: dict[str, str]
    wildcard_names: set[str]
    transformed_lists: dict[str, TransformedList]

    def to_intents_dict(self) -> dict[str, Any]:
        """Convert to hassil format."""
        return {
            "language": self.language,
            "lists": {
                **{
                    list_name: {"values": list_values}
                    for list_name, list_values in self.list_values.items()
                },
                **{
                    wildcard_name: {"wildcard": True}
                    for wildcard_name in self.wildcard_names
                },
            },
            "expansion_rules": self.expansion_rules,
            "intents": {
                "SpeechToPhrase": {
                    "data": [block.to_data() for block in self.sentence_blocks],
                }
            },
        }

    @staticmethod
    def from_dict(data_dict: dict[str, Any]) -> "LanguageData":
        """Load from a YAML dict."""
        sentence_blocks: list[SentenceBlock] = []
        transformed_lists: dict[str, TransformedList] = {}

        for sentence_info in data_dict["data"]:
            if isinstance(sentence_info, str):
                sentence_blocks.append(SentenceBlock(sentences=[sentence_info]))
            else:
                sentence_blocks.append(SentenceBlock.from_dict(sentence_info))

        transformations: dict[str, list[Transformation]] = {}
        for tr_name, tr_info in data_dict.get("transformations", {}).items():
            tr_list: list[Transformation] = []
            for tr_dict in tr_info:
                match_regex = tr_dict.get("match")
                tr_list.append(
                    Transformation(
                        outputs=tr_dict["outputs"],
                        match_regex=(
                            re.compile(match_regex, re.IGNORECASE)
                            if match_regex
                            else None
                        ),
                    )
                )

            transformations[tr_name] = tr_list

        for tr_list_name, tr_list_info in data_dict.get(
            "transformed_lists", {}
        ).items():
            transformed_lists[tr_list_name] = TransformedList(
                source_list_name=tr_list_info["source"],
                transformations=[
                    tr
                    for tr_name in tr_list_info["transformations"]
                    for tr in transformations[tr_name]
                ],
            )

        return LanguageData(
            language=data_dict["language"],
            sentence_blocks=sentence_blocks,
            list_values=data_dict.get("lists", {}),
            expansion_rules=data_dict.get("expansion_rules", {}),
            wildcard_names=set(data_dict.get("wildcards", [])),
            transformed_lists=transformed_lists,
        )

    def add_transformed_lists(
        self, list_values: dict[str, list[str]]
    ) -> dict[str, list[str]]:
        """Add transformed versions of list values."""
        tr_list_values: dict[str, list[str]] = {}
        for src_list_name, src_list_values in itertools.chain(
            self.list_values.items(), list_values.items()
        ):
            for tr_list_name, tr_list in self.transformed_lists.items():
                if tr_list.source_list_name != src_list_name:
                    continue

                tr_list_values[tr_list_name] = [
                    output_value
                    for value in src_list_values
                    for output_value in tr_list.apply(value)
                ]

        list_values.update(tr_list_values)

        return tr_list_values

    def add_transformed_slot_lists(
        self, slot_lists: dict[str, SlotList]
    ) -> dict[str, TextSlotList]:
        """Add transformed versions of slot lists."""
        tr_slot_lists: dict[str, TextSlotList] = {}

        for list_name, slot_list in slot_lists.items():
            if not isinstance(slot_list, TextSlotList):
                continue

            for tr_list_name, tr_list in self.transformed_lists.items():
                if tr_list.source_list_name != list_name:
                    continue

                tr_slot_lists[tr_list_name] = TextSlotList(
                    name=tr_list_name,
                    values=[
                        TextSlotValue(
                            TextChunk(output_value),
                            output_value,
                            context=value.context,
                            metadata=value.metadata,
                        )
                        for value in slot_list.values
                        if isinstance(value.text_in, TextChunk)
                        for output_value in tr_list.apply(value.text_in.text)
                    ],
                )

        slot_lists.update(tr_slot_lists)

        return tr_slot_lists


def load_shared_lists(lists_dict: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Convert shared lists to hassil format."""
    slot_lists: dict[str, Any] = {}

    for list_name, list_info in lists_dict.items():
        ranges = []
        if list_range := list_info.get("range"):
            ranges.append(
                (list_range["from"], list_range["to"], list_range.get("step", 1))
            )
        elif list_multi_range := list_info.get("multi_range"):
            for list_range in list_multi_range:
                ranges.append(
                    (
                        list_range["from"],
                        list_range["to"],
                        list_range.get("step", 1),
                    )
                )

        slot_lists[list_name] = {
            "values": [
                str(number)
                for range_from, range_to, range_step in ranges
                for number in range(range_from, range_to + 1, range_step)
            ]
        }

    return slot_lists
