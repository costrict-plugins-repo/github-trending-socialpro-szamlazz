"""Tests for `proforma`, `pdf-fetch`, `xml-fetch` subcommands."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import szamlazz_cli  # noqa: E402
from lib.http_client import HttpResponse  # noqa: E402


@pytest.fixture
def ready(tmp_path, monkeypatch):
    config_dir = tmp_path / "szamlazz"
    config_dir.mkdir()
    (config_dir / "seller.yaml").write_text(
        "cegnev: T\nirszam: '1'\ntelepules: B\ncim: x\nadoszam: 12345678-2-42\n"
        "bank:\n  nev: OTP\n  szamlaszam: 11700000-00000000-12345678\n"
        "email: a@b.hu\nkisadozo: false\n", encoding="utf-8",
    )
    (config_dir / ".env").write_text("SZAMLAZZ_AGENT_KEY=tk\n", encoding="utf-8")
    monkeypatch.setenv("SZAMLAZZ_CONFIG_DIR", str(config_dir))
    return config_dir


def test_pdf_fetch_saves_file(ready, tmp_path, capsys):
    fake = HttpResponse(body=b"%PDF fetched", headers={"szlahu_error_code": ""}, status=200)
    with patch.object(szamlazz_cli.http_client, "post_multipart", return_value=fake):
        rc = szamlazz_cli.main([
            "pdf-fetch", "--invoice-number", "SOC-2026-0042",
            "--output-dir", str(tmp_path / "out"), "--json",
        ])
    assert rc == 0
    out_files = list((tmp_path / "out").rglob("*.pdf"))
    assert len(out_files) == 1
    assert out_files[0].read_bytes() == b"%PDF fetched"


def test_xml_fetch_returns_xml(ready, tmp_path, capsys):
    fake = HttpResponse(
        body=b"<?xml version=\"1.0\"?>\n<szamla><vevo>Test</vevo></szamla>",
        headers={"szlahu_error_code": ""}, status=200,
    )
    with patch.object(szamlazz_cli.http_client, "post_multipart", return_value=fake):
        rc = szamlazz_cli.main([
            "xml-fetch", "--invoice-number", "SOC-2026-0042",
        ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "<vevo>Test</vevo>" in out


def test_proforma_dry_run(ready, tmp_path, capsys):
    input_json = tmp_path / "proforma.json"
    input_json.write_text("""{
      "fejlec": {"szamlaszamElotag": "P", "keltDatum": "2026-04-12",
                 "teljesitesDatum": "2026-04-12", "fizetesiHataridoDatum": "2026-04-19",
                 "fizmod": "Átutalás", "penznem": "HUF", "szamlaNyelve": "hu"},
      "vevo": {"nev": "X", "irsz": "1", "telepules": "B", "cim": "y",
               "adoszam": "12345678-2-42", "email": "x@y.hu"},
      "tetelek": [{"megnevezes": "t", "mennyiseg": "1", "mennyisegiEgyseg": "db",
                   "nettoEgysegar": "100", "afakulcs": "27"}]
    }""", encoding="utf-8")
    rc = szamlazz_cli.main(["proforma", "--config", str(input_json), "--dry-run"])
    assert rc == 0
