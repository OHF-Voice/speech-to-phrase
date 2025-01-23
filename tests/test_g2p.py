"""Tests for grapheme-to-phoneme (g2p) methods."""

from speech_to_phrase.g2p import LexiconDatabase, split_words
from unicode_rbnf import RbnfEngine


def test_split_words() -> None:
    lexicon = LexiconDatabase()
    engine = RbnfEngine.for_language("en")

    # Initialisms
    assert split_words("HVAC", lexicon, engine) == ["H", "V", "A", "C"]
    assert split_words("H.V.A.C.", lexicon, engine) == ["H", "V", "A", "C"]

    # Word + number
    assert split_words("PM2.5", lexicon, engine) == [
        "P",
        "M",
        ("two", "2.5"),
        ("point", None),
        ("five", None),
    ]