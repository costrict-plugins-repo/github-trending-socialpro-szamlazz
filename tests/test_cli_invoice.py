"""Tests for the `invoice` subcommand — end-to-end with mocked HTTP."""
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
        "cegnev: Test Kft.\n"
        "irszam: '1111'\n"
        "telepules: Budapest\n"
        "cim: Utca 1.\n"
        "adoszam: 12345678-2-42\n"
        "bank:\n"
        "  nev: OTP Bank\n"
        "  szamlaszam: 11700000-00000000-12345678\n"
        "email: a@b.hu\n"
        "kisadozo: false\n", encoding="utf-8",
    )
    (config_dir / ".env").write_text("SZAMLAZZ_AGENT_KEY=testkey\n", encoding="utf-8")
    monkeypatch.setenv("SZAMLAZZ_CONFIG_DIR", str(config_dir))
    return config_dir


def test_invoice_dry_run_prints_xml(ready_config, tmp_path, capsys):
    input_json = tmp_path / "invoice.json"
    input_json.write_text("""{
      "fejlec": {"szamlaszamElotag": "SOC", "keltDatum": "2026-04-12",
                 "teljesitesDatum": "2026-04-12", "fizetesiHataridoDatum": "2026-04-19",
                 "fizmod": "Átutalás", "penznem": "HUF", "szamlaNyelve": "hu"},
      "vevo": {"nev": "Példa Kft.", "irsz": "1111", "telepules": "Budapest",
               "cim": "Példa utca 1.", "adoszam": "12345678-2-42", "email": "v@e.hu"},
      "tetelek": [{"megnevezes": "Szolgáltatás", "mennyiseg": "1",
                   "mennyisegiEgyseg": "db", "nettoEgysegar": "10000", "afakulcs": "27"}]
    }""", encoding="utf-8")

    rc = szamlazz_cli.main(["invoice", "--config", str(input_json), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "<xmlszamla" in out
    assert "Példa Kft." in out


def test_invoice_success_returns_invoice_number(ready_config, tmp_path, capsys):
    input_json = tmp_path / "invoice.json"
    input_json.write_text("""{
      "fejlec": {"szamlaszamElotag": "SOC", "keltDatum": "2026-04-12",
                 "teljesitesDatum": "2026-04-12", "fizetesiHataridoDatum": "2026-04-19",
                 "fizmod": "Átutalás", "penznem": "HUF", "szamlaNyelve": "hu"},
      "vevo": {"nev": "Példa Kft.", "irsz": "1111", "telepules": "Budapest",
               "cim": "Példa utca 1.", "adoszam": "12345678-2-42", "email": "v@e.hu"},
      "tetelek": [{"megnevezes": "Szolgáltatás", "mennyiseg": "1",
                   "mennyisegiEgyseg": "db", "nettoEgysegar": "10000", "afakulcs": "27"}]
    }""", encoding="utf-8")

    fake_response = HttpResponse(
        body=b"%PDF-1.4 fake pdf bytes",
        headers={
            "szlahu_szamlaszam": "SOC-2026-0042",
            "szlahu_nettovegosszeg": "10000.00",
            "szlahu_afaertek": "2700.00",
            "szlahu_bruttovegosszeg": "12700.00",
            "szlahu_error_code": "",
        },
        status=200,
    )
    with patch.object(szamlazz_cli.http_client, "post_multipart", return_value=fake_response):
        rc = szamlazz_cli.main([
            "invoice", "--config", str(input_json),
            "--output-dir", str(tmp_path / "invoices"),
            "--json",
        ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "SOC-2026-0042" in out
    assert (tmp_path / "invoices" / __import__("datetime").date.today().strftime("%Y-%m") / "SOC-2026-0042.pdf").exists()
