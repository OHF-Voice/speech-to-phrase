"""Tests for resolving argument defaults from the environment."""

import pytest

from speech_to_phrase.__main__ import env_default


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("TEST_SECRET", raising=False)
    monkeypatch.delenv("TEST_SECRET_FILE", raising=False)


def test_unset() -> None:
    """Nothing in the environment means no default."""
    assert env_default("TEST_SECRET") is None


def test_from_env(monkeypatch) -> None:
    """Value comes from the plain environment variable."""
    monkeypatch.setenv("TEST_SECRET", "from-env")
    assert env_default("TEST_SECRET") == "from-env"


def test_from_file(tmp_path, monkeypatch) -> None:
    """Value comes from the file named by <NAME>_FILE, with whitespace stripped."""
    secret_file = tmp_path / "secret"
    secret_file.write_text("from-file\n", encoding="utf-8")
    monkeypatch.setenv("TEST_SECRET_FILE", str(secret_file))
    assert env_default("TEST_SECRET") == "from-file"


def test_file_wins_over_env(tmp_path, monkeypatch) -> None:
    """<NAME>_FILE takes precedence over <NAME>."""
    secret_file = tmp_path / "secret"
    secret_file.write_text("from-file", encoding="utf-8")
    monkeypatch.setenv("TEST_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("TEST_SECRET", "from-env")
    assert env_default("TEST_SECRET") == "from-file"


def test_empty_is_unset(monkeypatch) -> None:
    """An empty value is treated as unset so real defaults still apply."""
    monkeypatch.setenv("TEST_SECRET", "   ")
    assert env_default("TEST_SECRET") is None


def test_missing_file_is_an_error(tmp_path, monkeypatch) -> None:
    """A <NAME>_FILE pointing nowhere fails loudly instead of starting unconfigured."""
    monkeypatch.setenv("TEST_SECRET_FILE", str(tmp_path / "nope"))
    with pytest.raises(FileNotFoundError):
        env_default("TEST_SECRET")
