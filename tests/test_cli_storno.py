"""Tests for the `storno` subcommand."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import szamlazz_cli  # noqa: E402
from lib.http_client import HttpResponse  # noqa: E402


@pytest.fixture
def ready_config(tmp_path, monkeypatch):
    config_dir = tmp_path / "szamlazz"
    config_dir.mkdir()
    (config_dir / "seller.yaml").write_text(
        "cegnev: Test\nirszam: '1111'\ntelepules: Budapest\ncim: Utca 1.\n"
        "adoszam: 12345678-2-42\nbank:\n  nev: OTP\n  szamlaszam: 11700000-00000000-12345678\n"
        "email: a@b.hu\nkisadozo: false\n", encoding="utf-8",
    )
    (config_dir / ".env").write_text("SZAMLAZZ_AGENT_KEY=testkey\n", encoding="utf-8")
    monkeypatch.setenv("SZAMLAZZ_CONFIG_DIR", str(config_dir))
    return config_dir


def test_storno_success(ready_config, tmp_path, capsys):
    fake_response = HttpResponse(
        body=b"%PDF fake",
        headers={
            "szlahu_szamlaszam": "SOC-2026-0042-S",
            "szlahu_error_code": "",
        },
        status=200,
    )
    with patch.object(szamlazz_cli.http_client, "post_multipart", return_value=fake_response):
        rc = szamlazz_cli.main([
            "storno",
            "--invoice-number", "SOC-2026-0042",
            "--reason", "Számlázási hiba",
            "--output-dir", str(tmp_path / "invoices"),
            "--json",
        ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SOC-2026-0042-S" in out
