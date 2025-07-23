import base64
import json
import logging
import math
import re
from collections import defaultdict
from collections.abc import Callable
from collections.abc import Sequence as ABCSequence
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import reduce
from typing import Dict, List, Optional, Set, TextIO, Tuple, Union

from hassil.expression import (
    Expression,
    ListReference,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    TextChunk,
)
from hassil.intents import IntentData, Intents, RangeSlotList, SlotList, TextSlotList
from hassil.util import check_excluded_context, check_required_context
from unicode_rbnf import RbnfEngine

from .g2p import LexiconDatabase, split_words

EPS = "<eps>"
SPACE = "<space>"
BEGIN_OUTPUT = "__begin_output:"
END_OUTPUT = "__end_output"
SENTENCE_OUTPUT = "__sentence_output:"
OUTPUT_PREFIX = "__output:"
WORD_PENALTY = 0.03

_LOGGER = logging.getLogger(__name__)


class SuppressOutput(Enum):
    DISABLED = auto()
    UNTIL_END = auto()
    UNTIL_SPACE = auto()


@dataclass
class FstArc:
    to_state: int
    in_label: str = EPS
    out_label: str = EPS
    log_prob: Optional[float] = None


@dataclass
class Fst:
    arcs: Dict[int, List[FstArc]] = field(default_factory=lambda: defaultdict(list))
    states: Set[int] = field(default_factory=lambda: {0})
    final_states: Set[int] = field(default_factory=set)
    words: Set[str] = field(default_factory=set)
    output_words: Set[str] = field(default_factory=set)
    start: int = 0
    current_state: int = 0

    def next_state(self) -> int:
        self.states.add(self.current_state)
        self.current_state += 1
        return self.current_state

    def next_edge(
        self,
        from_state: int,
        in_label: Optional[str] = None,
        out_label: Optional[str] = None,
        log_prob: Optional[float] = None,
    ) -> int:
        to_state = self.next_state()
        self.add_edge(from_state, to_state, in_label, out_label, log_prob)
        return to_state

    def add_edge(
        self,
        from_state: int,
        to_state: int,
        in_label: Optional[str] = None,
        out_label: Optional[str] = None,
        log_prob: Optional[float] = None,
    ) -> None:
        if in_label is None:
            in_label = EPS

        if out_label is None:
            out_label = in_label

        if (" " in in_label) or (" " in out_label):
            raise ValueError(
                f"Cannot have white space in labels: from={in_label}, to={out_label}"
            )

        if (not in_label) or (not out_label):
            raise ValueError(f"Labels cannot be empty: from={in_label}, to={out_label}")

        if in_label != EPS:
            self.words.add(in_label)

        if out_label != EPS:
            self.output_words.add(out_label)

        self.states.add(from_state)
        self.states.add(to_state)
        self.arcs[from_state].append(FstArc(to_state, in_label, out_label, log_prob))

    def accept(self, state: int) -> None:
        self.states.add(state)
        self.final_states.add(state)

    def write(self, fst_file: TextIO, symbols_file: Optional[TextIO] = None) -> None:
        symbols = {EPS: 0}

        for state, arcs in self.arcs.items():
            for arc in arcs:
                if arc.in_label not in symbols:
                    symbols[arc.in_label] = len(symbols)

                if arc.out_label not in symbols:
                    symbols[arc.out_label] = len(symbols)

                if arc.log_prob is None:
                    print(
                        state, arc.to_state, arc.in_label, arc.out_label, file=fst_file
                    )
                else:
                    print(
                        state,
                        arc.to_state,
                        arc.in_label,
                        arc.out_label,
                        arc.log_prob,
                        file=fst_file,
                    )

        for state in self.final_states:
            print(state, file=fst_file)

        if symbols_file is not None:
            for symbol, symbol_id in symbols.items():
                print(symbol, symbol_id, file=symbols_file)

    def remove_spaces(self) -> "Fst":
        """Remove <space> tokens and merge partial word labels."""
        visited: Dict[Tuple[int, int, int], int] = {}

        fst_without_spaces = Fst()
        for arc in self.arcs[self.start]:
            # Copy initial weighted intent arc
            output_state = fst_without_spaces.next_edge(
                fst_without_spaces.start, log_prob=arc.log_prob
            )

            for next_arc_idx, next_arc in enumerate(self.arcs[arc.to_state]):
                self._remove_spaces(
                    arc.to_state,
                    next_arc,
                    next_arc_idx,
                    "",
                    None,
                    visited,
                    fst_without_spaces,
                    output_state,
                )

        return fst_without_spaces

    def _remove_spaces(
        self,
        state: int,
        arc: FstArc,
        arc_idx: int,
        word: str,
        output_word: Optional[str],
        visited: Dict[Tuple[int, int, int], int],
        fst_without_spaces: "Fst",
        output_state: int,
        suppress_output: SuppressOutput = SuppressOutput.DISABLED,
    ) -> None:
        if arc.in_label == SPACE:
            key = (state, arc.to_state, arc_idx)
            cached_state = visited.get(key)
            input_symbol = word or EPS
            output_symbol = input_symbol

            if suppress_output in (
                SuppressOutput.UNTIL_END,
                SuppressOutput.UNTIL_SPACE,
            ):
                # Suppress output
                output_symbol = output_word or EPS
                output_word = None  # consume
            elif output_word is not None:
                # Override output
                output_symbol = output_word
                output_word = None  # consume

            if cached_state is not None:
                fst_without_spaces.add_edge(
                    output_state,
                    cached_state,
                    input_symbol,
                    output_symbol,
                    log_prob=WORD_PENALTY if input_symbol != EPS else None,
                )
                return

            output_state = fst_without_spaces.next_edge(
                output_state,
                input_symbol,
                output_symbol,
                log_prob=WORD_PENALTY if input_symbol != EPS else None,
            )
            visited[key] = output_state

            if arc.to_state in self.final_states:
                fst_without_spaces.final_states.add(output_state)

            word = ""

            if suppress_output == SuppressOutput.UNTIL_SPACE:
                suppress_output = SuppressOutput.DISABLED
        elif arc.in_label != EPS:
            word += arc.in_label

            if (
                (suppress_output == SuppressOutput.DISABLED)
                and (arc.out_label != EPS)
                and (arc.out_label != arc.in_label)
            ):
                # Short-term output override
                suppress_output = SuppressOutput.UNTIL_SPACE
                output_word = arc.out_label

        if arc.out_label.startswith(BEGIN_OUTPUT):
            # Start suppressing output
            suppress_output = SuppressOutput.UNTIL_END
        elif arc.out_label.startswith(END_OUTPUT):
            # Stop suppressing output
            suppress_output = SuppressOutput.UNTIL_SPACE
        elif arc.out_label.startswith(SENTENCE_OUTPUT):
            output_state = fst_without_spaces.next_edge(
                output_state, EPS, arc.out_label
            )
        elif arc.out_label.startswith(OUTPUT_PREFIX):
            # Output on next space
            output_word = arc.out_label

        for next_arc_idx, next_arc in enumerate(self.arcs[arc.to_state]):
            self._remove_spaces(
                arc.to_state,
                next_arc,
                next_arc_idx,
                word,
                output_word,
                visited,
                fst_without_spaces,
                output_state,
                suppress_output=suppress_output,
            )

    def prune(self) -> None:
        """Remove paths not connected to a final state."""
        while True:
            states_to_prune: Set[int] = set()

            for state in self.states:
                if (not self.arcs[state]) and (state not in self.final_states):
                    states_to_prune.add(state)

            if not states_to_prune:
                break

            self.states.difference_update(states_to_prune)

            # Prune outgoing arcs
            for state in states_to_prune:
                self.arcs.pop(state, None)

            # Prune incoming arcs
            for state in self.states:
                needs_pruning = any(
                    arc.to_state in states_to_prune for arc in self.arcs[state]
                )
                if needs_pruning:
                    self.arcs[state] = [
                        arc
                        for arc in self.arcs[state]
                        if arc.to_state not in states_to_prune
                    ]

    def to_strings(self, add_spaces: bool) -> List[str]:
        strings: List[str] = []
        self._to_strings("", strings, self.start, add_spaces)

        return strings

    def _to_strings(self, text: str, strings: List[str], state: int, add_spaces: bool):
        if state in self.final_states:
            text_norm = " ".join(text.strip().split())
            if text_norm:
                strings.append(text_norm)

        for arc in self.arcs[state]:
            if arc.in_label == SPACE:
                arc_text = text + " "
            elif arc.in_label != EPS:
                if add_spaces:
                    arc_text = text + " " + arc.in_label
                else:
                    arc_text = text + arc.in_label
            else:
                # Skip <eps>
                arc_text = text

            self._to_strings(arc_text, strings, arc.to_state, add_spaces)

    def to_tokens(self, only_connected: bool = True) -> List[List[str]]:
        tokens: List[List[str]] = []
        self._to_tokens([], tokens, self.start, only_connected)

        # Remove final spaces
        for path in tokens:
            if path and (path[-1] == SPACE):
                path.pop()

        return tokens

    def _to_tokens(
        self,
        path: List[str],
        tokens: List[List[str]],
        state: int,
        only_connected: bool,
    ):
        if (state in self.final_states) and path:
            tokens.append(path)

        has_arcs = False
        for arc in self.arcs[state]:
            has_arcs = True

            # Skip <eps> and initial <space>
            if (arc.in_label == EPS) or (arc.in_label == SPACE and (not path)):
                arc_path = path
            else:
                arc_path = path + [arc.in_label.strip()]

            self._to_tokens(arc_path, tokens, arc.to_state, only_connected)

        if path and (not has_arcs) and (not only_connected):
            # Dead path
            tokens.append(path)


@dataclass
class NumToWords:
    engine: RbnfEngine
    cache: Dict[Tuple[int, int, int], Sequence] = field(default_factory=dict)


@dataclass
class G2PInfo:
    lexicon: LexiconDatabase
    casing_func: Callable[[str], str] = field(default=lambda s: s)


@dataclass
class ExpressionWithOutput:
    expression: Expression
    output_text: str
    list_name: Optional[str] = None


def expression_to_fst(
    expression: Union[Expression, ExpressionWithOutput],
    state: int,
    fst: Fst,
    intent_data: IntentData,
    intents: Intents,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    num_to_words: Optional[NumToWords] = None,
    g2p_info: Optional[G2PInfo] = None,
    suppress_output: bool = False,
) -> Optional[int]:
    if isinstance(expression, ExpressionWithOutput):
        exp_output: ExpressionWithOutput = expression
        output_data = {"text": exp_output.output_text}
        if exp_output.list_name:
            output_data["list"] = exp_output.list_name

        output_word = encode_meta(json.dumps(output_data))

        state = fst.next_edge(state, EPS, BEGIN_OUTPUT)
        state = fst.next_edge(state, EPS, output_word)
        maybe_state = expression_to_fst(
            exp_output.expression,
            state,
            fst,
            intent_data,
            intents,
            slot_lists,
            num_to_words,
            g2p_info,
            suppress_output=suppress_output,
        )
        if maybe_state is None:
            # Dead branch
            return None

        state = maybe_state
        return fst.next_edge(state, EPS, END_OUTPUT)

    if isinstance(expression, TextChunk):
        chunk: TextChunk = expression

        space_before = False
        space_after = False

        if chunk.original_text == " ":
            return fst.next_edge(state, SPACE)

        if chunk.original_text.startswith(" "):
            space_before = True

        if chunk.original_text.endswith(" "):
            space_after = True

        word = chunk.original_text.strip()
        if not word:
            return state

        if space_before:
            state = fst.next_edge(state, SPACE)

        sub_words: ABCSequence[Union[str, Tuple[str, Optional[str]]]]
        if g2p_info is not None:
            sub_words = split_words(
                word,
                g2p_info.lexicon,
                num_to_words.engine if num_to_words is not None else None,
            )
        else:
            sub_words = word.split()

        last_sub_word_idx = len(sub_words) - 1
        for sub_word_idx, sub_word in enumerate(sub_words):
            if isinstance(sub_word, str):
                sub_output_word: Optional[str] = sub_word
            else:
                sub_word, sub_output_word = sub_word
                sub_output_word = sub_output_word or EPS

            if g2p_info is not None:
                sub_word = g2p_info.casing_func(sub_word)

            state = fst.next_edge(
                state, sub_word, EPS if suppress_output else sub_output_word
            )
            if sub_word_idx != last_sub_word_idx:
                # Add spaces between words
                state = fst.next_edge(state, SPACE)

        if space_after:
            state = fst.next_edge(state, SPACE)

        return state

    if isinstance(expression, Sequence):
        seq: Sequence = expression
        if seq.type == SequenceType.ALTERNATIVE:
            start = state
            end = fst.next_state()

            for item in seq.items:
                maybe_state = expression_to_fst(
                    item,
                    start,
                    fst,
                    intent_data,
                    intents,
                    slot_lists,
                    num_to_words,
                    g2p_info,
                )
                if maybe_state is None:
                    # Dead branch
                    continue

                state = maybe_state
                if state == start:
                    # Empty item
                    continue

                fst.add_edge(state, end)

            if seq.is_optional:
                fst.add_edge(start, end)

            return end

        if seq.type == SequenceType.GROUP:
            for item in seq.items:
                maybe_state = expression_to_fst(
                    item,
                    state,
                    fst,
                    intent_data,
                    intents,
                    slot_lists,
                    num_to_words,
                    g2p_info,
                )

                if maybe_state is None:
                    # Dead branch
                    return None

                state = maybe_state

            return state

    if isinstance(expression, ListReference):
        # {list}
        list_ref: ListReference = expression

        slot_list: Optional[SlotList] = None
        if slot_lists is not None:
            slot_list = slot_lists.get(list_ref.list_name)

        if slot_list is None:
            slot_list = intent_data.slot_lists.get(list_ref.list_name)

        if slot_list is None:
            slot_list = intents.slot_lists.get(list_ref.list_name)

        if isinstance(slot_list, TextSlotList):
            text_list: TextSlotList = slot_list

            values: List[Union[Expression, ExpressionWithOutput]] = []
            for value in text_list.values:
                if (intent_data.requires_context is not None) and (
                    not check_required_context(
                        intent_data.requires_context,
                        value.context,
                        allow_missing_keys=True,
                    )
                ):
                    continue

                if (intent_data.excludes_context is not None) and (
                    not check_excluded_context(
                        intent_data.excludes_context,
                        value.context,
                    )
                ):
                    continue

                value_output_text: Optional[str] = None
                if isinstance(value.text_in, TextChunk):
                    value_chunk: TextChunk = value.text_in
                    value_output_text = value_chunk.text
                if value.value_out is not None:
                    value_output_text = str(value.value_out)

                if value_output_text:
                    values.append(
                        ExpressionWithOutput(
                            value.text_in,
                            output_text=value_output_text,
                            list_name=list_ref.slot_name,
                        )
                    )
                else:
                    values.append(value.text_in)

            if not values:
                # Dead branch
                return None

            return expression_to_fst(
                Sequence(values, type=SequenceType.ALTERNATIVE),  # type: ignore[arg-type]
                state,
                fst,
                intent_data,
                intents,
                slot_lists,
                num_to_words,
                g2p_info,
            )

        if isinstance(slot_list, RangeSlotList):
            range_list: RangeSlotList = slot_list

            if num_to_words is None:
                # Dead branch
                return None

            num_cache_key = (range_list.start, range_list.stop + 1, range_list.step)
            number_sequence = num_to_words.cache.get(num_cache_key)

            if number_sequence is None:
                values = []
                if num_to_words is not None:
                    for number in range_list.get_numbers():
                        number_str = str(number)
                        number_result = num_to_words.engine.format_number(number)
                        number_words = {
                            w.replace("-", " ")
                            for w in number_result.text_by_ruleset.values()
                        }
                        values.extend(
                            ExpressionWithOutput(
                                TextChunk(w),
                                output_text=number_str,
                                list_name=list_ref.slot_name,
                            )
                            for w in number_words
                        )

                number_sequence = Sequence(
                    values, type=SequenceType.ALTERNATIVE  # type: ignore[arg-type]
                )

                if num_to_words is not None:
                    num_to_words.cache[num_cache_key] = number_sequence

                if not values:
                    # Dead branch
                    return None

            return expression_to_fst(
                number_sequence,
                state,
                fst,
                intent_data,
                intents,
                slot_lists,
                num_to_words,
                g2p_info,
            )

        # Will be pruned
        word = f"{{{list_ref.list_name}}}"
        fst.next_edge(state, word, word)
        return None

    if isinstance(expression, RuleReference):
        # <rule>
        rule_ref: RuleReference = expression

        rule_body: Optional[Sentence] = intent_data.expansion_rules.get(
            rule_ref.rule_name
        )
        if rule_body is None:
            rule_body = intents.expansion_rules.get(rule_ref.rule_name)

        if rule_body is None:
            raise ValueError(f"Missing expansion rule <{rule_ref.rule_name}>")

        return expression_to_fst(
            rule_body,
            state,
            fst,
            intent_data,
            intents,
            slot_lists,
            num_to_words,
            g2p_info,
        )

    return state


def get_count(
    e: Expression,
    intents: Intents,
    intent_data: IntentData,
) -> int:
    if isinstance(e, Sequence):
        seq: Sequence = e
        item_counts = [get_count(item, intents, intent_data) for item in seq.items]

        if seq.type == SequenceType.ALTERNATIVE:
            return sum(item_counts)

        if seq.type == SequenceType.GROUP:
            return reduce(lambda x, y: x * y, item_counts, 1)

    if isinstance(e, ListReference):
        list_ref: ListReference = e
        slot_list: Optional[SlotList] = None

        slot_list = intent_data.slot_lists.get(list_ref.list_name)
        if not slot_list:
            slot_list = intents.slot_lists.get(list_ref.list_name)

        if isinstance(slot_list, TextSlotList):
            text_list: TextSlotList = slot_list
            return sum(
                get_count(v.text_in, intents, intent_data) for v in text_list.values
            )

        if isinstance(slot_list, RangeSlotList):
            range_list: RangeSlotList = slot_list
            if range_list.step == 1:
                return range_list.stop - range_list.start + 1

            return len(range(range_list.start, range_list.stop + 1, range_list.step))

    if isinstance(e, RuleReference):
        rule_ref: RuleReference = e
        rule_body: Optional[Sentence] = None

        rule_body = intent_data.expansion_rules.get(rule_ref.rule_name)
        if not rule_body:
            rule_body = intents.expansion_rules.get(rule_ref.rule_name)

        if rule_body:
            return get_count(rule_body, intents, intent_data)

    return 1


def lcm(*nums: int) -> int:
    """Returns the least common multiple of the given integers"""
    if nums:
        nums_lcm = nums[0]
        for n in nums[1:]:
            nums_lcm = (nums_lcm * n) // math.gcd(nums_lcm, n)

        return nums_lcm

    return 1


def intents_to_fst(
    intents: Intents,
    slot_lists: Optional[Dict[str, SlotList]] = None,
    number_language: Optional[str] = None,
    exclude_intents: Optional[Set[str]] = None,
    include_intents: Optional[Set[str]] = None,
    g2p_info: Optional[G2PInfo] = None,
) -> Fst:
    num_to_words: Optional[NumToWords] = None
    if number_language:
        try:
            num_to_words = NumToWords(engine=RbnfEngine.for_language(number_language))
        except ValueError:
            _LOGGER.exception("Unable to convert numbers to words")

    filtered_intents = []
    sentence_counts: Dict[str, int] = {}
    total_sentences = 0

    for intent in intents.intents.values():
        if (exclude_intents is not None) and (intent.name in exclude_intents):
            continue

        if (include_intents is not None) and (intent.name not in include_intents):
            continue

        num_sentences = 0
        for data in intent.data:
            for sentence in data.sentences:
                num_sentences += get_count(sentence, intents, data)

        sentence_counts[intent.name] = num_sentences
        total_sentences += num_sentences

        filtered_intents.append(intent)

    _LOGGER.debug("Total sentences: %s", total_sentences)
    _LOGGER.debug("Sentence count by intent: %s", sentence_counts)

    fst_with_spaces = Fst()
    final = fst_with_spaces.next_state()

    for intent in filtered_intents:
        for data in intent.data:
            sentence_output: Optional[str] = None
            if data.metadata is not None:
                sentence_output = data.metadata.get("output")

            for sentence in data.sentences:
                sentence_state = fst_with_spaces.next_edge(
                    fst_with_spaces.start,
                    SPACE,
                    SPACE,
                )

                if sentence_output:
                    # Sentence has different output than input
                    sentence_state = fst_with_spaces.next_edge(
                        sentence_state,
                        EPS,
                        encode_meta(sentence_output, SENTENCE_OUTPUT),
                    )

                state = expression_to_fst(
                    sentence,
                    sentence_state,
                    fst_with_spaces,
                    data,
                    intents,
                    slot_lists,
                    num_to_words,
                    g2p_info,
                    suppress_output=(sentence_output is not None),
                )

                if state is None:
                    # Dead branch
                    continue

                fst_with_spaces.add_edge(state, final, SPACE, SPACE)

    fst_with_spaces.accept(final)

    return fst_with_spaces


def decode_meta(text: str) -> str:
    slots: Dict[str, str] = {}

    def handle_match(m: re.Match) -> str:
        data = json.loads(decode_meta_single(m.group(1)))
        slot_name = data.get("list")
        slot_value = data["text"]
        if slot_name:
            slots[slot_name] = slot_value

        return slot_value

    text = re.sub(re.escape(OUTPUT_PREFIX) + "([0-9A-Z=]+)", handle_match, text)
    match = re.search(re.escape(SENTENCE_OUTPUT) + "([0-9A-Z=]+)", text)

    if match is None:
        return text

    sentence_output = decode_meta_single(match.group(1))
    return sentence_output.format(**slots)


def decode_meta_single(text: str) -> str:
    return base64.b32decode(text.encode("utf-8")).strip().decode("utf-8")


def encode_meta(text: str, prefix: str = OUTPUT_PREFIX) -> str:
    return prefix + (base64.b32encode(text.encode("utf-8")).strip().decode("utf-8"))
