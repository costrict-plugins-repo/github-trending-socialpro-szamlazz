"""Shared pytest fixtures for socialpro-szamlazz tests."""
import os
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def clean_env(monkeypatch):
    """Remove all SZAMLAZZ_* env vars so tests start from a clean slate."""
    for key in list(os.environ.keys()):
        if key.startswith("SZAMLAZZ_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    return monkeypatch


@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Redirect HOME and USERPROFILE to a temp dir for isolation."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))  # Windows
    return home
