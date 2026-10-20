"""NAV (Hungarian tax authority) taxpayer lookup helpers.

The szamlazz.hu Agent API exposes a taxpayer query endpoint that wraps
the NAV Online Számla taxpayer database. We send a minimal XML request
with a tax ID and parse the response into a structured TaxpayerInfo
record used by the init flow to pre-fill seller.yaml automatically.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaxpayerInfo:
    name: str
    tax_id_short: str  # e.g. "27947353" — 8 digits without suffix
    postal_code: str
    city: str
    street_line: str  # assembled street address incl. floor/door


def normalize_tax_number(value: str) -> str:
    """Accept '27947353' or '27947353-2-17' and return it trimmed.

    Raises ValueError if the format is clearly wrong.
    """
    v = value.strip()
    if re.fullmatch(r"\d{8}", v):
        return v
    if re.fullmatch(r"\d{8}-\d-\d{2}", v):
        return v
    raise ValueError(
        f"Invalid Hungarian tax number format: {value!r}. "
        "Expected 8 digits, or 8-1-2 with dashes."
    )


def _text(node: Optional[ET.Element]) -> str:
    return (node.text or "").strip() if node is not None else ""


def parse_taxpayer_xml(xml_text: str) -> Optional[TaxpayerInfo]:
    """Parse a szamlazz.hu taxpayer query response XML into TaxpayerInfo.

    Returns None if the XML is unparseable or the taxpayer is marked invalid.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    # Strip namespaces if present
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    validity = root.find(".//taxpayerValidity")
    if validity is not None and _text(validity).lower() != "true":
        return None

    data = root.find(".//taxpayerData")
    if data is None:
        return None

    # Use explicit `is not None` guards — ET elements without children
    # may be falsy, so short-circuited `or` would fail on some Python versions.
    name_node = data.find("taxpayerShortName")
    if name_node is None or not _text(name_node):
        name_node = data.find("taxpayerName")
    name = _text(name_node)

    tax_id_short = _text(data.find(".//taxpayerId"))

    addr = data.find(".//taxpayerAddress")
    if addr is None:
        return TaxpayerInfo(
            name=name, tax_id_short=tax_id_short,
            postal_code="", city="", street_line="",
        )

    postal = _text(addr.find("postalCode"))
    city = _text(addr.find("city"))

    street_parts = [
        _text(addr.find("streetName")),
        _text(addr.find("publicPlaceCategory")),
        _text(addr.find("number")),
    ]
    floor = _text(addr.find("floor"))
    door = _text(addr.find("door"))
    if floor:
        street_parts.append(f"{floor} em.")
    if door:
        street_parts.append(door)
    street_line = " ".join(p for p in street_parts if p)

    return TaxpayerInfo(
        name=name,
        tax_id_short=tax_id_short,
        postal_code=postal,
        city=city,
        street_line=street_line,
    )
