import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import nav_lookup  # noqa: E402

FIXTURE_XML = (Path(__file__).parent / "fixtures" / "taxpayer_response.xml").read_text(encoding="utf-8")


class TestParseTaxpayerXml:
    def test_parses_kg_creative_fixture(self):
        result = nav_lookup.parse_taxpayer_xml(FIXTURE_XML)
        assert result is not None
        assert "KG CREATIVE MEDIA GROUP" in result.name
        assert result.tax_id_short == "27947353"
        assert result.postal_code == "7200"
        assert result.city == "Dombóvár"
        assert "Ady Endre" in result.street_line
        assert "10." in result.street_line

    def test_returns_none_for_invalid_xml(self):
        result = nav_lookup.parse_taxpayer_xml("<broken>")
        assert result is None

    def test_returns_none_when_taxpayer_invalid(self):
        xml = """<?xml version="1.0"?>
        <QueryTaxpayerResponse>
          <taxpayerValidity>false</taxpayerValidity>
        </QueryTaxpayerResponse>"""
        result = nav_lookup.parse_taxpayer_xml(xml)
        assert result is None


class TestNormalizeTaxNumber:
    def test_accepts_full_format(self):
        assert nav_lookup.normalize_tax_number("27947353-2-17") == "27947353-2-17"

    def test_accepts_short_format(self):
        assert nav_lookup.normalize_tax_number("27947353") == "27947353"

    def test_strips_whitespace(self):
        assert nav_lookup.normalize_tax_number("  27947353-2-17  ") == "27947353-2-17"

    def test_rejects_wrong_length(self):
        with pytest.raises(ValueError):
            nav_lookup.normalize_tax_number("12345")
