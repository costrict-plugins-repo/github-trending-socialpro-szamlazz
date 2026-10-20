"""szamlazz.hu Agent API error code → Hungarian user-facing explanation.

Maps the most common szamlazz.hu `szlahu_error_code` values to a
structured ErrorExplanation with a reason (Hungarian), one or more
RecoveryOption choices the skill can present via AskUserQuestion, and
a formatted text block ready for display.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class RecoveryOption:
    key: str  # machine-readable id, e.g. "reenter_key"
    label: str  # human-readable label shown to the user


@dataclass
class ErrorExplanation:
    code: str
    raw_message: str
    reason_hu: str
    recovery_options: List[RecoveryOption] = field(default_factory=list)


_MAP = {
    "3": ErrorExplanation(
        code="3",
        raw_message="",
        reason_hu=(
            "A szamlazz.hu Agent kulcs nem érvényes. A kulcs kis/nagybetű-érzékeny, "
            'és a "Számla kiállítás" jogosultsággal kell rendelkeznie.'
        ),
        recovery_options=[
            RecoveryOption("reenter_key", "Új kulcsot írok be"),
            RecoveryOption("check_current", "Meglévő kulcsot ellenőrzöm (maszkolva)"),
            RecoveryOption("exit", "Kilépek"),
        ],
    ),
    "54": ErrorExplanation(
        code="54",
        raw_message="",
        reason_hu=(
            "e-Számla tanúsítvány hiba. A számlázó nem tud elektronikus aláírt "
            "számlát generálni ezzel a beállítással."
        ),
        recovery_options=[
            RecoveryOption("try_eszamla_false", "Próbáld újra eszamla=false-szal (sima PDF)"),
            RecoveryOption("exit", "Kilépek"),
        ],
    ),
    "55": ErrorExplanation(
        code="55",
        raw_message="",
        reason_hu=(
            "e-Számla tanúsítvány érvénytelen vagy lejárt. Ellenőrizd a szamlazz.hu "
            "fiókodban a tanúsítvány állapotát."
        ),
        recovery_options=[
            RecoveryOption("try_eszamla_false", "Próbáld újra eszamla=false-szal"),
            RecoveryOption("exit", "Kilépek"),
        ],
    ),
    "57": ErrorExplanation(
        code="57",
        raw_message="",
        reason_hu=(
            "Számítási hiba — a nettó/ÁFA/bruttó érték nem egyezik a szamlazz.hu "
            "oldali ellenőrzéssel. Gyakori ok: kerekítési eltérés."
        ),
        recovery_options=[
            RecoveryOption("recalc", "Újraszámolom a tételeket Decimallel"),
            RecoveryOption("show_details", "Mutasd a részleteket"),
            RecoveryOption("exit", "Kilépek"),
        ],
    ),
    "136": ErrorExplanation(
        code="136",
        raw_message="",
        reason_hu=(
            "Fizetési hátralék a szamlazz.hu szolgáltatásnál — a fiók aktuális "
            "előfizetési számláját ki kell egyenlíteni a webes felületen."
        ),
        recovery_options=[
            RecoveryOption("open_browser", "Nyisd meg a szamlazz.hu-t böngészőben"),
            RecoveryOption("exit", "Kilépek"),
        ],
    ),
}

# Code ranges 259-264 are all "calculation mismatch" variants → same handler as 57
for _code in ["259", "260", "261", "262", "263", "264"]:
    _MAP[_code] = ErrorExplanation(
        code=_code,
        raw_message="",
        reason_hu=(
            f"Számítási hiba (kód {_code}) — az összegek nem egyeznek a szamlazz.hu "
            "oldali ellenőrzéssel. Kerekítést használj (ROUND_HALF_UP, 2 tizedes)."
        ),
        recovery_options=[
            RecoveryOption("recalc", "Újraszámolom a tételeket Decimallel"),
            RecoveryOption("show_details", "Mutasd a részleteket"),
            RecoveryOption("exit", "Kilépek"),
        ],
    )


def explain_error(code: str, raw_message: str = "") -> ErrorExplanation:
    """Look up the error code and return an explanation with recovery options.

    Unknown codes get a generic explanation with a single "exit" option.
    """
    if code in _MAP:
        base = _MAP[code]
        return ErrorExplanation(
            code=base.code,
            raw_message=raw_message,
            reason_hu=base.reason_hu,
            recovery_options=list(base.recovery_options),
        )

    return ErrorExplanation(
        code=code,
        raw_message=raw_message,
        reason_hu=(
            f"Ismeretlen szamlazz.hu hiba (kód: {code}). "
            f"Eredeti üzenet: {raw_message or '(nincs)'}"
        ),
        recovery_options=[
            RecoveryOption("exit", "Kilépek és manuálisan ellenőrzöm"),
        ],
    )


def format_error(exp: ErrorExplanation) -> str:
    """Format an ErrorExplanation as a Hungarian multiline text block."""
    lines = [
        "",
        "✗ Hiba a szamlazz.hu művelet során",
        "",
        f"  Hibakód:  {exp.code}",
    ]
    if exp.raw_message:
        lines.append(f"  Üzenet:   {exp.raw_message}")
    lines.append(f"  Ok:       {exp.reason_hu}")
    lines.append("")
    lines.append("  Mit szeretnél?")
    for i, opt in enumerate(exp.recovery_options, 1):
        lines.append(f"    {i}. {opt.label}")
    lines.append("")
    return "\n".join(lines)
