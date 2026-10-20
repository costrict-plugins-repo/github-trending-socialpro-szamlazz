import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import bank_prefixes  # noqa: E402


class TestDetectBank:
    def test_unicredit(self):
        assert bank_prefixes.detect_bank("10918001-00000000-12345678") == "UniCredit Bank"

    def test_erste(self):
        assert bank_prefixes.detect_bank("11600006-00000000-12345678") == "Erste Bank"

    def test_otp(self):
        assert bank_prefixes.detect_bank("11700000-00000000-12345678") == "OTP Bank"

    def test_kh(self):
        assert bank_prefixes.detect_bank("12600000-00000000-12345678") == "K&H Bank"

    def test_unknown_returns_none(self):
        assert bank_prefixes.detect_bank("99999999-00000000-12345678") is None

    def test_strips_non_digits(self):
        assert bank_prefixes.detect_bank("10918001 00000000 12345678") == "UniCredit Bank"

    def test_empty_returns_none(self):
        assert bank_prefixes.detect_bank("") is None
