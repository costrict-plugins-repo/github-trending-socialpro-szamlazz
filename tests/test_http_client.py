"""Tests for scripts/lib/http_client.py — stdlib multipart/form-data POST."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import http_client  # noqa: E402


class TestBuildMultipartBody:
    def test_builds_body_with_single_file_field(self):
        body, content_type = http_client.build_multipart_body(
            fields={},
            files={"action-xmlagentxmlfile": ("szamla.xml", b"<xml>hi</xml>")},
        )
        assert "multipart/form-data; boundary=" in content_type
        assert b'name="action-xmlagentxmlfile"' in body
        assert b'filename="szamla.xml"' in body
        assert b"<xml>hi</xml>" in body

    def test_builds_body_with_multiple_files(self):
        body, content_type = http_client.build_multipart_body(
            fields={},
            files={
                "action-xmlagentxmlfile": ("invoice.xml", b"<one/>"),
                "action-xmlagentstornoxmlfile": ("storno.xml", b"<two/>"),
            },
        )
        assert b'name="action-xmlagentxmlfile"' in body
        assert b'name="action-xmlagentstornoxmlfile"' in body
        assert b"<one/>" in body
        assert b"<two/>" in body

    def test_body_ends_with_closing_boundary(self):
        body, content_type = http_client.build_multipart_body(
            fields={}, files={"f": ("x.xml", b"<x/>")},
        )
        boundary = content_type.split("boundary=")[1]
        assert body.endswith(f"--{boundary}--\r\n".encode("utf-8"))


class TestPostMultipart:
    @patch("lib.http_client.urllib.request.urlopen")
    def test_post_returns_response_headers_and_body(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"OK-body-content"
        mock_response.headers = {
            "szlahu_szamlaszam": "SOC-2026-0042",
            "szlahu_nettovegosszeg": "150000.00",
            "szlahu_bruttovegosszeg": "190500.00",
            "szlahu_error_code": "",
        }
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = http_client.post_multipart(
            url="https://www.szamlazz.hu/szamla/",
            files={"action-xmlagentxmlfile": ("szamla.xml", b"<xml/>")},
        )
        assert result.body == b"OK-body-content"
        assert result.headers["szlahu_szamlaszam"] == "SOC-2026-0042"
        assert result.headers["szlahu_error_code"] == ""

    @patch("lib.http_client.urllib.request.urlopen")
    def test_post_raises_on_http_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://www.szamlazz.hu/szamla/", 500, "Internal Server Error", {}, None
        )
        with pytest.raises(http_client.SzamlazzHttpError) as exc_info:
            http_client.post_multipart(
                url="https://www.szamlazz.hu/szamla/",
                files={"action-xmlagentxmlfile": ("szamla.xml", b"<xml/>")},
            )
        assert exc_info.value.status_code == 500
