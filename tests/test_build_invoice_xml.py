"""Tests for scripts/build_invoice_xml.py — JSON → szamlazz.hu XML generator."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_invoice_xml.py"


@pytest.fixture
def sample_invoice_json(tmp_path):
    data = {
        "beallitasok": {
            "szamlaagentkulcs": "dummy_key",
            "eszamla": False,
            "szamlaLetoltes": True,
        },
        "fejlec": {
            "szamlaszamElotag": "SOC",
            "kelt": "2026-04-12",
            "teljesites": "2026-04-12",
            "fizetesiHatarido": "2026-04-19",
            "fizmod": "Átutalás",
            "penznem": "HUF",
            "szamlaNyelve": "hu",
        },
        "elado": {
            "bank": "UniCredit Bank",
            "bankszamlaszam": "10918001-00000000-12345678",
            "emailReplyto": "seller@example.hu",
        },
        "vevo": {
            "nev": "Példa Kft.",
            "irsz": "1111",
            "telepules": "Budapest",
            "cim": "Példa utca 1.",
            "adoszam": "12345678-2-42",
            "email": "vevo@example.hu",
        },
        "tetelek": [
            {
                "megnevezes": "Webfejlesztés",
                "mennyiseg": "1",
                "mennyisegiEgyseg": "db",
                "nettoEgysegar": "100000",
                "afakulcs": "27",
            },
        ],
    }
    path = tmp_path / "invoice.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_builds_invoice_xml(sample_invoice_json):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "invoice", "--config", str(sample_invoice_json)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "<xmlszamla" in result.stdout
    assert "<vevo>" in result.stdout
    assert "Példa Kft." in result.stdout
    assert "27" in result.stdout  # VAT rate

def test_builds_proforma_xml(sample_invoice_json):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--mode", "proforma", "--config", str(sample_invoice_json)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "dijbekero" in result.stdout.lower()
