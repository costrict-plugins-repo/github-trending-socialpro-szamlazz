"""Tests for scripts/lib/errors.py — error code → user-facing explanation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import errors  # noqa: E402


class TestExplainError:
    def test_unknown_code_returns_generic(self):
        result = errors.explain_error(code="9999", raw_message="foo")
        assert result.code == "9999"
        assert "Ismeretlen" in result.reason_hu
        assert result.recovery_options  # at least one option

    def test_code_3_is_auth_failed(self):
        result = errors.explain_error(code="3", raw_message="Authentication failed")
        assert "Agent kulcs" in result.reason_hu
        assert any("kulcsot" in opt.label for opt in result.recovery_options)

    def test_code_54_is_eszamla_cert(self):
        result = errors.explain_error(code="54", raw_message="...")
        assert "tanúsítvány" in result.reason_hu
        assert any("eszamla=false" in opt.label for opt in result.recovery_options)

    def test_code_57_is_calc_error(self):
        result = errors.explain_error(code="57", raw_message="...")
        assert "számítási" in result.reason_hu.lower() or "számítás" in result.reason_hu.lower()

    def test_code_136_is_szamlazz_balance(self):
        result = errors.explain_error(code="136", raw_message="...")
        assert "szamlazz.hu" in result.reason_hu or "fizetési" in result.reason_hu.lower()


class TestFormatError:
    def test_format_returns_multiline_hu_text(self):
        result = errors.explain_error(code="3", raw_message="Auth failed")
        text = errors.format_error(result)
        assert "✗ Hiba" in text
        assert "Hibakód:" in text
        assert "3" in text
        assert "Mit szeretnél" in text
