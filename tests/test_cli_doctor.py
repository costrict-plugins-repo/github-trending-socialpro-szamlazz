"""Tests for the `doctor` subcommand — config state report."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

CLI = Path(__file__).resolve().parent.parent / "scripts" / "szamlazz_cli.py"


def _base_env(tmp_path):
    """Return a minimal env dict that works on all OSes.

    Windows needs SystemRoot, TEMP, etc. for Python to even start.
    """
    env = {
        "HOME": str(tmp_path),
        "USERPROFILE": str(tmp_path),
        "PATH": os.environ.get("PATH", ""),
        "PYTHONUTF8": "1",
    }
    for key in ["SystemRoot", "SystemDrive", "TEMP", "TMP", "COMSPEC", "WINDIR", "APPDATA"]:
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def run_cli(*args, env=None):
    result = subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True, text=True, env=env,
    )
    return result


class TestDoctor:
    def test_no_config_dir_status(self, tmp_path):
        env = _base_env(tmp_path)
        result = run_cli("doctor", "--json", env=env)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "no_config_dir"

    def test_missing_seller_status(self, tmp_path):
        config_dir = tmp_path / "szamlazz"
        config_dir.mkdir()
        (config_dir / ".env").write_text("SZAMLAZZ_AGENT_KEY=abc\n")
        env = _base_env(tmp_path)
        env["SZAMLAZZ_CONFIG_DIR"] = str(config_dir)
        result = run_cli("doctor", "--json", env=env)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "missing_seller"
        assert str(config_dir) in data["config_dir"]

    def test_missing_key_status(self, tmp_path):
        config_dir = tmp_path / "szamlazz"
        config_dir.mkdir()
        (config_dir / "seller.yaml").write_text(
            "cegnev: Test Kft.\n"
            "irszam: '1111'\n"
            "telepules: Budapest\n"
            "cim: Utca 1.\n"
            "adoszam: 12345678-2-42\n"
            "bank:\n"
            "  nev: OTP Bank\n"
            "  szamlaszam: 11700000-00000000-12345678\n"
            "email: a@b.hu\n"
            "kisadozo: false\n"
        )
        env = _base_env(tmp_path)
        env["SZAMLAZZ_CONFIG_DIR"] = str(config_dir)
        result = run_cli("doctor", "--json", env=env)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "missing_key"

    def test_ready_status(self, tmp_path):
        config_dir = tmp_path / "szamlazz"
        config_dir.mkdir()
        (config_dir / "seller.yaml").write_text(
            "cegnev: Test Kft.\n"
            "irszam: '1111'\n"
            "telepules: Budapest\n"
            "cim: Utca 1.\n"
            "adoszam: 12345678-2-42\n"
            "bank:\n"
            "  nev: OTP Bank\n"
            "  szamlaszam: 11700000-00000000-12345678\n"
            "email: a@b.hu\n"
            "kisadozo: false\n"
        )
        (config_dir / ".env").write_text("SZAMLAZZ_AGENT_KEY=abc\n")
        env = _base_env(tmp_path)
        env["SZAMLAZZ_CONFIG_DIR"] = str(config_dir)
        result = run_cli("doctor", "--json", env=env)
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert data["status"] == "ready"
