"""YAML-backed partner cache for szamlazz.hu invoice customers.

Each successful invoice appends / upserts the customer into this cache so
that future invoices to the same customer can use name-based lookup.

The cache is keyed by `adoszam` (tax ID) — the only reliably unique field
for Hungarian companies. Upsert replaces the existing entry when tax IDs
match; otherwise appends.

Dependencies: PyYAML (the only external runtime dependency of the plugin).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

try:
    import yaml  # PyYAML
except ImportError as e:
    raise ImportError(
        "PyYAML is required for socialpro-szamlazz. Install it with: pip install pyyaml"
    ) from e


@dataclass
class Partner:
    nev: str
    adoszam: str = ""
    irszam: str = ""
    telepules: str = ""
    cim: str = ""
    email: str = ""
    utolso_szamlazas: str = ""
    szamlaszamok: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Partner":
        return cls(
            nev=data.get("nev", ""),
            adoszam=data.get("adoszam", ""),
            irszam=data.get("irszam", ""),
            telepules=data.get("telepules", ""),
            cim=data.get("cim", ""),
            email=data.get("email", ""),
            utolso_szamlazas=data.get("utolso_szamlazas", ""),
            szamlaszamok=list(data.get("szamlaszamok", [])),
        )


@dataclass
class PartnerCache:
    partners: List[Partner] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "PartnerCache":
        if not path.is_file():
            return cls(partners=[])
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        items = raw.get("partners") or []
        return cls(partners=[Partner.from_dict(p) for p in items])

    def save(self, path: Path) -> None:
        data = {"partners": [p.to_dict() for p in self.partners]}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )

    def find_by_name(self, needle: str) -> Optional[Partner]:
        needle_lower = needle.lower()
        for p in self.partners:
            if needle_lower in p.nev.lower():
                return p
        return None

    def find_by_tax_id(self, tax_id: str) -> Optional[Partner]:
        for p in self.partners:
            if p.adoszam == tax_id:
                return p
        return None

    def upsert(self, partner: Partner) -> None:
        if partner.adoszam:
            for i, existing in enumerate(self.partners):
                if existing.adoszam == partner.adoszam:
                    self.partners[i] = partner
                    return
        self.partners.append(partner)
