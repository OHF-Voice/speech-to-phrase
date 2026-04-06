"""Uses Coqui STT and OpenFST for training.

See:
- https://github.com/coqui-ai/STT
- https://arxiv.org/pdf/2206.14589
"""

import logging
import shlex
import unicodedata
from pathlib import Path
from typing import Dict, List, Set, Union

from .const import BLANK, EPS, SPACE, Settings
from .hassil_fst import Fst
from .models import Model
from .speech_tools import SpeechTools

_LOGGER = logging.getLogger(__name__)


async def train_coqui_stt(model: Model, settings: Settings, fst: Fst) -> None:
    """Train a Coqui STT speech model."""
    model_dir = settings.model_data_dir(model.id).absolute()
    train_dir = settings.model_train_dir(model.id).absolute()
    train_dir.mkdir(parents=True, exist_ok=True)

    idx2char: Dict[int, str] = {}
    char2idx: Dict[str, int] = {}

    alphabet_path = model_dir / "alphabet.txt"

    # Load alphabet
    a_idx = 1  # <eps> = 0
    with open(alphabet_path, "r", encoding="utf-8") as a_file:
        for line in a_file:
            line = line.strip()
            if line.startswith("#"):
                continue

            if not line:
                line = " "
            elif line == "\\#":
                line = "#"

            c = line[0]
            if c == " ":
                c = SPACE

            idx2char[a_idx] = c
            char2idx[c] = a_idx
            a_idx += 1

    blank_id = a_idx
    idx2char[blank_id] = BLANK
    char2idx[BLANK] = blank_id

    # CTC tokens
    tokens_with_blank = train_dir / "tokens_with_blank.txt"
    tokens_without_blank = train_dir / "tokens_without_blank.txt"
    with open(tokens_with_blank, "w", encoding="utf-8") as tokens_with_blank_file, open(
        tokens_without_blank, "w", encoding="utf-8"
    ) as tokens_without_blank_file:
        # NOTE: <eps> *MUST* be id 0
        for tokens_file in (tokens_with_blank_file, tokens_without_blank_file):
            print(EPS, 0, file=tokens_file)
            for i, c in idx2char.items():
                if c == BLANK:
                    continue

                print(c, i, file=tokens_file)

        print(BLANK, blank_id, file=tokens_with_blank_file)

    # token -> char
    token2char_txt = train_dir / "token2char.fst.txt"
    with open(token2char_txt, "w", encoding="utf-8") as token2char_file:
        start = 0

        # Accept blank
        print(start, start, BLANK, EPS, file=token2char_file)
        print(start, file=token2char_file)

        # Each token has a state
        char2state = {c: i for i, c in enumerate(char2idx, start=1)}

        for c, c_state in char2state.items():
            if c == BLANK:
                continue

            # First token (emits char)
            print(start, c_state, c, c, file=token2char_file)

            # Subsequent repeated tokens
            print(c_state, c_state, c, EPS, file=token2char_file)

            # Back to start on blank
            print(c_state, start, BLANK, EPS, file=token2char_file)

            for c_other, c_other_state in char2state.items():
                if c_other in (c, BLANK):
                    continue

                # Switch to other token
                print(c_state, c_other_state, c_other, c_other, file=token2char_file)

            # Return to start
            # NOTE: This is critical
            print(c_state, start, EPS, EPS, file=token2char_file)

    # All possible words
    words_txt = train_dir / "words.txt"
    with open(words_txt, "w", encoding="utf-8") as words_file:
        print(EPS, 0, file=words_file)
        for i, word in enumerate(sorted(fst.words), start=1):
            if word == EPS:
                continue

            print(word, i, file=words_file)

    output_txt = train_dir / "output.txt"
    with open(output_txt, "w", encoding="utf-8") as output_file:
        print(EPS, 0, file=output_file)
        for i, word in enumerate(sorted(fst.words), start=1):
            if word == EPS:
                continue

            print(word, i, file=output_file)

        # Output labels
        for i, word in enumerate(
            sorted(fst.output_words),
            start=len(fst.words) + 1,
        ):
            print(word, i, file=output_file)

    # char -> word
    char2word_txt = train_dir / "char2word.fst.txt"
    warned_chars: Set[str] = set()
    with open(char2word_txt, "w", encoding="utf-8") as char2word_file:
        start = 0
        current = 1

        for word in fst.words:
            if word == EPS:
                continue

            c_idx = 0
            for word_char in word:
                chars_to_use: List[str] = []

                if word_char not in char2idx:
                    # Try decomposing (splitting out accent marks)
                    nfd_c = unicodedata.normalize("NFD", word_char)
                    unusable_chars: List[str] = []
                    for c in nfd_c:
                        if c in char2idx:
                            chars_to_use.append(c)
                        else:
                            unusable_chars.append(c)

                    for c in unusable_chars:
                        # None of the decomposed characters could be used
                        if c not in warned_chars:
                            _LOGGER.warning("Skipping '%s' in '%s'", c, word)
                            warned_chars.add(c)

                    if not chars_to_use:
                        c_idx += 1
                        continue
                else:
                    chars_to_use.append(word_char)

                for c in chars_to_use:
                    if c_idx == 0:
                        # First char, emit word
                        print(start, current, c, word, file=char2word_file)
                    else:
                        # Subsequent chars
                        print(current, current + 1, c, EPS, file=char2word_file)
                        current += 1

                c_idx += 1

            # Add space
            print(current, current + 1, SPACE, EPS, file=char2word_file)
            current += 1

            # Loop back to start
            print(current, start, EPS, EPS, file=char2word_file)
            current += 1

        print(start, file=char2word_file)

    # word -> sentence
    word2sen_txt = train_dir / "word2sen.fst.txt"
    with open(word2sen_txt, "w", encoding="utf-8") as word2sen_file:
        fst.write(word2sen_file)

    token2char_fst = train_dir / "token2char.fst"
    await settings.tools.async_run_pipeline(
        [
            "fstcompile",
            shlex.quote(f"--isymbols={tokens_with_blank}"),
            shlex.quote(f"--osymbols={tokens_without_blank}"),
            shlex.quote(str(token2char_txt)),
        ],
        ["fstdeterminize"],
        ["fstminimize"],
        ["fstpush", "--push_weights"],
        ["fstarcsort", "--sort_type=ilabel", "-", shlex.quote(str(token2char_fst))],
    )

    char2word_fst = train_dir / "char2word.fst"
    await _try_minimize(
        [
            "fstcompile",
            shlex.quote(f"--isymbols={tokens_without_blank}"),
            shlex.quote(f"--osymbols={words_txt}"),
            shlex.quote(str(char2word_txt)),
        ],
        char2word_fst,
        settings.tools,
    )

    word2sen_fst = train_dir / "word2sen.fst"
    await _try_minimize(
        [
            "fstcompile",
            shlex.quote(f"--isymbols={words_txt}"),
            shlex.quote(f"--osymbols={output_txt}"),
            shlex.quote(str(word2sen_txt)),
        ],
        word2sen_fst,
        settings.tools,
    )

    # token -> char -> word
    token2word_fst = train_dir / "token2word.fst"
    await _try_minimize(
        [
            "fstcompose",
            shlex.quote(str(token2char_fst)),
            shlex.quote(str(char2word_fst)),
        ],
        token2word_fst,
        settings.tools,
    )

    # token -> char -> word -> sentence
    token2sen_fst = train_dir / "token2sen.fst"
    await settings.tools.async_run_pipeline(
        [
            "fstcompose",
            shlex.quote(str(token2word_fst)),
            shlex.quote(str(word2sen_fst)),
        ],
        ["fstrmepsilon"],
        ["fstpush", "--push_weights"],
        ["fstarcsort", "--sort_type=ilabel", "-", shlex.quote(str(token2sen_fst))],
    )


async def _try_minimize(
    compile_command: List[str],
    fst_path: Union[str, Path],
    tools: SpeechTools,
    arc_sort_type: str = "ilabel",
) -> None:
    try:
        # With minimize
        await tools.async_run_pipeline(
            compile_command,
            ["fstdeterminize"],
            ["fstminimize"],
            ["fstpush", "--push_weights"],
            [
                "fstarcsort",
                f"--sort_type={arc_sort_type}",
                "-",
                shlex.quote(str(fst_path)),
            ],
        )
    except Exception as e:
        _LOGGER.warning(
            "fstminimize pipeline failed for %s. Executing fallback. Reason: %s",
            fst_path,
            e,
        )
        # Without minimize
        await tools.async_run_pipeline(
            compile_command,
            ["fstpush", "--push_weights"],
            [
                "fstarcsort",
                f"--sort_type={arc_sort_type}",
                "-",
                shlex.quote(str(fst_path)),
            ],
        )
