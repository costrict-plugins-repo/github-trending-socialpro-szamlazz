"""Tests for the `taxpayer` subcommand using mocked HTTP."""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

CLI = Path(__file__).resolve().parent.parent / "scripts" / "szamlazz_cli.py"
FIXTURE_XML = (Path(__file__).parent / "fixtures" / "taxpayer_response.xml").read_text(encoding="utf-8")


@pytest.fixture
def mock_config_ready(tmp_path):
    config_dir = tmp_path / "szamlazz"
    config_dir.mkdir()
    (config_dir / ".env").write_text("SZAMLAZZ_AGENT_KEY=testkey\n")
    return config_dir


def test_taxpayer_requires_tax_id(mock_config_ready):
    env = {
        **os.environ,
        "SZAMLAZZ_CONFIG_DIR": str(mock_config_ready),
    }
    result = subprocess.run(
        [sys.executable, str(CLI), "taxpayer"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode != 0
    assert "tax" in result.stderr.lower() or "required" in result.stderr.lower()


def test_taxpayer_parses_nav_response_unit():
    """Unit test — call the function directly with injected XML."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import szamlazz_cli

    with patch.object(szamlazz_cli, "_fetch_taxpayer_xml", return_value=FIXTURE_XML):
        result = szamlazz_cli._taxpayer_lookup(tax_id="27947353", agent_key="dummy")
        assert result is not None
        assert "KG CREATIVE MEDIA GROUP" in result.name
        assert result.postal_code == "7200"
        assert result.city == "Dombóvár"
