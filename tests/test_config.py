"""Tests for scripts/lib/config.py — cross-platform config resolution."""
import os
import sys
from pathlib import Path

import pytest

# Import under test — scripts/lib added to path in a moment
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import config  # noqa: E402


class TestResolveConfigDir:
    def test_returns_none_when_nothing_exists(self, clean_env, tmp_home):
        assert config.resolve_config_dir() is None

    def test_priority_1_env_var_override(self, clean_env, tmp_home, tmp_path):
        custom = tmp_path / "custom_conf"
        custom.mkdir()
        clean_env.setenv("SZAMLAZZ_CONFIG_DIR", str(custom))
        assert config.resolve_config_dir() == custom

    def test_priority_2_project_local(self, clean_env, tmp_home, tmp_path, monkeypatch):
        project = tmp_path / "project"
        project.mkdir()
        (project / ".szamlazz").mkdir()
        monkeypatch.chdir(project)
        result = config.resolve_config_dir()
        assert result is not None
        assert result.name == ".szamlazz"

    def test_priority_3_linux_xdg(self, clean_env, tmp_home, monkeypatch):
        if sys.platform == "win32":
            pytest.skip("Linux XDG path only applies to non-Windows")
        xdg = tmp_home / ".config" / "szamlazz"
        xdg.mkdir(parents=True)
        # Force platform to linux for this test
        monkeypatch.setattr(sys, "platform", "linux")
        result = config.resolve_config_dir()
        assert result == xdg

    def test_priority_3_macos_application_support(self, clean_env, tmp_home, monkeypatch):
        app_support = tmp_home / "Library" / "Application Support" / "szamlazz"
        app_support.mkdir(parents=True)
        monkeypatch.setattr(sys, "platform", "darwin")
        result = config.resolve_config_dir()
        assert result == app_support

    def test_priority_3_windows_appdata(self, clean_env, tmp_home, monkeypatch, tmp_path):
        appdata = tmp_path / "AppData" / "Roaming"
        (appdata / "szamlazz").mkdir(parents=True)
        clean_env.setenv("APPDATA", str(appdata))
        monkeypatch.setattr(sys, "platform", "win32")
        result = config.resolve_config_dir()
        assert result == appdata / "szamlazz"

    def test_priority_4_legacy_claude_dir(self, clean_env, tmp_home, monkeypatch):
        legacy = tmp_home / ".claude" / "szamlazz"
        legacy.mkdir(parents=True)
        monkeypatch.setattr(sys, "platform", "linux")
        result = config.resolve_config_dir()
        assert result == legacy


class TestLoadAgentKey:
    def test_returns_none_when_no_key(self, clean_env, tmp_path):
        assert config.load_agent_key(tmp_path) is None

    def test_reads_from_env(self, clean_env, tmp_path):
        clean_env.setenv("SZAMLAZZ_AGENT_KEY", "abc123")
        assert config.load_agent_key(tmp_path) == "abc123"

    def test_reads_from_dotenv_file(self, clean_env, tmp_path):
        (tmp_path / ".env").write_text('SZAMLAZZ_AGENT_KEY="xyz789"\n', encoding="utf-8")
        assert config.load_agent_key(tmp_path) == "xyz789"

    def test_env_var_takes_priority_over_file(self, clean_env, tmp_path):
        (tmp_path / ".env").write_text("SZAMLAZZ_AGENT_KEY=from_file\n", encoding="utf-8")
        clean_env.setenv("SZAMLAZZ_AGENT_KEY", "from_env")
        assert config.load_agent_key(tmp_path) == "from_env"


class TestDefaultConfigDirForSetup:
    def test_linux_returns_xdg(self, clean_env, tmp_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        result = config.default_config_dir_for_setup()
        assert result == tmp_home / ".config" / "szamlazz"

    def test_macos_returns_application_support(self, clean_env, tmp_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        result = config.default_config_dir_for_setup()
        assert result == tmp_home / "Library" / "Application Support" / "szamlazz"

    def test_windows_returns_appdata(self, clean_env, tmp_home, monkeypatch, tmp_path):
        appdata = tmp_path / "AppData"
        appdata.mkdir()
        clean_env.setenv("APPDATA", str(appdata))
        monkeypatch.setattr(sys, "platform", "win32")
        result = config.default_config_dir_for_setup()
        assert result == appdata / "szamlazz"
