"""Tests for the `init` subcommand — writes config files from flags."""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import szamlazz_cli  # noqa: E402


def test_init_writes_seller_yaml(tmp_path, monkeypatch):
    target = tmp_path / "szamlazz"
    monkeypatch.setenv("SZAMLAZZ_CONFIG_DIR", str(target))
    rc = szamlazz_cli.main([
        "init",
        "--target-dir", str(target),
        "--cegnev", "KG Creative Media Group Kft.",
        "--irszam", "7200",
        "--telepules", "Dombóvár",
        "--cim", "Ady Endre utca 10.",
        "--adoszam", "27947353-2-17",
        "--bank-nev", "UniCredit Bank",
        "--bank-szamlaszam", "10918001-00000000-12345678",
        "--email", "krasznai.gabor@socialpro.hu",
        "--kisadozo", "false",
        "--agent-key", "test-key-abc-123",
    ])
    assert rc == 0
    seller = yaml.safe_load((target / "seller.yaml").read_text(encoding="utf-8"))
    assert seller["cegnev"] == "KG Creative Media Group Kft."
    assert seller["bank"]["nev"] == "UniCredit Bank"
    env_content = (target / ".env").read_text(encoding="utf-8")
    assert "SZAMLAZZ_AGENT_KEY=test-key-abc-123" in env_content


def test_init_permissions_env_file_unix(tmp_path, monkeypatch):
    if sys.platform == "win32":
        pytest.skip("POSIX permissions test")
    target = tmp_path / "szamlazz"
    szamlazz_cli.main([
        "init", "--target-dir", str(target),
        "--cegnev", "x", "--irszam", "1", "--telepules", "x", "--cim", "x",
        "--adoszam", "12345678-2-42", "--bank-nev", "OTP",
        "--bank-szamlaszam", "11700000-00000000-12345678",
        "--email", "x@y.hu", "--kisadozo", "false",
        "--agent-key", "abc",
    ])
    mode = (target / ".env").stat().st_mode & 0o777
    assert mode == 0o600
