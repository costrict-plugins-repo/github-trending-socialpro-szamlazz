"""Hungarian bank name detection from giro account prefix.

The first 5 digits of a Hungarian giro account (formerly "pénzforgalmi
jelzőszám") identify the bank. We look up a static JSON table of the top
~20 banks shipped in the plugin.

Used by the interactive init flow to propose a bank name to the user
after they enter their account number.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

_DATA_FILE = Path(__file__).parent / "bank_prefixes.json"
_PREFIXES: dict[str, str] = {}


def _load() -> dict[str, str]:
    global _PREFIXES
    if not _PREFIXES:
        _PREFIXES = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    return _PREFIXES


def detect_bank(account_number: str) -> Optional[str]:
    """Return the bank name for a Hungarian giro account, or None if unknown.

    Accepts any format: "10918001-00000000-12345678", "109180010000000012345678",
    or with spaces. Only the first 5 digits matter.
    """
    if not account_number:
        return None
    digits = re.sub(r"\D", "", account_number)
    if len(digits) < 5:
        return None
    prefix = digits[:5]
    return _load().get(prefix)
