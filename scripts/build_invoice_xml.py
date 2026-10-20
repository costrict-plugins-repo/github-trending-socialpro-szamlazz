#!/usr/bin/env python3
"""
build_invoice_xml.py — Szamlazz.hu Agent API XML generátor

Input: JSON config stdin-ről vagy --config path. YAML helyett JSON-t használunk,
hogy ne legyen pyyaml függőség (stdlib elég). A skill a seller.yaml + vevő + tételek
adataiból JSON-t épít és ezt a scriptbe pipe-olja.

Output: szigorú sorrendű xmlszamla/xmlszamlast XML stdout-ra.

Használat:
    echo '{...}' | python3 build_invoice_xml.py --mode invoice
    python3 build_invoice_xml.py --mode storno --config /tmp/storno.json
    python3 build_invoice_xml.py --mode proforma --config /tmp/proforma.json > /tmp/out.xml

Módok:
    invoice   — Új számla (xmlszamla)
    proforma  — Díjbekérő (xmlszamla + dijbekero=true)
    storno    — Sztornó (xmlszamlast)

Számítások:
    nettoErtek  = mennyiseg * nettoEgysegar
    afaErtek    = nettoErtek * afakulcs / 100
    bruttoErtek = nettoErtek + afaErtek
    Minden érték Decimal-lal, 2 tizedesre kerekítve (ROUND_HALF_UP).
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from xml.sax.saxutils import escape as xml_escape


# ---------- segédfüggvények ----------

def money(value) -> Decimal:
    """Bemeneti szám → Decimal, 2 tizedes, ROUND_HALF_UP."""
    if value is None or value == "":
        return Decimal("0.00")
    d = Decimal(str(value))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def qty(value) -> Decimal:
    """Mennyiség → Decimal. Megőrzi a pontosságot (pl. 0.5, 1.25)."""
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value)).normalize()


def fmt_dec(d: Decimal) -> str:
    """Decimal → string, felesleges nullák nélkül, de legalább 1 tizedes."""
    s = format(d, "f")
    if "." not in s:
        s += ".0"
    return s


def fmt_money(d: Decimal) -> str:
    """Pénz: mindig 2 tizedes."""
    return format(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def e(value) -> str:
    """XML-escape + None/üres stringgé konvertálás."""
    if value is None:
        return ""
    return xml_escape(str(value), {'"': "&quot;", "'": "&apos;"})


def add(lines: list, indent: int, tag: str, value, required: bool = False):
    """Opcionális XML elem hozzáadása. Ha value üres és nem kötelező, kihagyja."""
    if value is None or value == "":
        if required:
            lines.append(f"{' ' * indent}<{tag}></{tag}>")
        return
    lines.append(f"{' ' * indent}<{tag}>{e(value)}</{tag}>")


def add_bool(lines: list, indent: int, tag: str, value):
    """Bool elem (true/false)."""
    if value is None:
        return
    v = "true" if bool(value) else "false"
    lines.append(f"{' ' * indent}<{tag}>{v}</{tag}>")


# ---------- számla generálás ----------

def build_tetel(t: dict, indent: int = 4) -> list:
    """Egy tétel XML-je, automatikus netto/afa/brutto számítással."""
    lines = []
    pad = " " * indent
    pad2 = " " * (indent + 2)

    mennyiseg = qty(t.get("mennyiseg", 1))
    netto_egyseg = Decimal(str(t.get("nettoEgysegar", 0)))
    afakulcs_raw = t.get("afakulcs", 27)

    # ÁFA kulcs: lehet szám (27, 5, 0) vagy speciális kód (TAHK, TAM, AAM stb.)
    try:
        afakulcs_num = Decimal(str(afakulcs_raw))
        is_numeric = True
    except Exception:
        is_numeric = False
        afakulcs_num = Decimal("0")

    # Számítások: nettoErtek = mennyiseg * nettoEgysegar
    netto_ertek = (mennyiseg * netto_egyseg).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Ha override van a configban, használd azt, különben számold
    if "nettoErtek" in t and t["nettoErtek"] not in (None, ""):
        netto_ertek = money(t["nettoErtek"])

    if is_numeric:
        afa_ertek = (netto_ertek * afakulcs_num / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        afa_ertek = Decimal("0.00")

    if "afaErtek" in t and t["afaErtek"] not in (None, ""):
        afa_ertek = money(t["afaErtek"])

    brutto_ertek = (netto_ertek + afa_ertek).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    if "bruttoErtek" in t and t["bruttoErtek"] not in (None, ""):
        brutto_ertek = money(t["bruttoErtek"])

    lines.append(f"{pad}<tetel>")
    add(lines, indent + 2, "megnevezes", t.get("megnevezes"), required=True)
    add(lines, indent + 2, "azonosito", t.get("azonosito"))
    lines.append(f"{pad2}<mennyiseg>{fmt_dec(mennyiseg)}</mennyiseg>")
    add(lines, indent + 2, "mennyisegiEgyseg", t.get("mennyisegiEgyseg", "db"), required=True)
    lines.append(f"{pad2}<nettoEgysegar>{fmt_money(netto_egyseg)}</nettoEgysegar>")
    add(lines, indent + 2, "afakulcs", afakulcs_raw, required=True)
    lines.append(f"{pad2}<nettoErtek>{fmt_money(netto_ertek)}</nettoErtek>")
    lines.append(f"{pad2}<afaErtek>{fmt_money(afa_ertek)}</afaErtek>")
    lines.append(f"{pad2}<bruttoErtek>{fmt_money(brutto_ertek)}</bruttoErtek>")
    add(lines, indent + 2, "megjegyzes", t.get("megjegyzes"))
    lines.append(f"{pad}</tetel>")
    return lines


def build_invoice(config: dict, mode: str) -> str:
    """Számla vagy díjbekérő XML (xmlszamla gyökérrel)."""
    is_proforma = (mode == "proforma")

    beallitasok = config.get("beallitasok", {})
    fejlec = config.get("fejlec", {})
    elado = config.get("elado", {})
    vevo = config.get("vevo", {})
    tetelek = config.get("tetelek", [])

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        '<xmlszamla xmlns="http://www.szamlazz.hu/xmlszamla" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.szamlazz.hu/xmlszamla '
        'https://www.szamlazz.hu/szamla/docs/xsds/agent/xmlszamla.xsd">'
    )

    # --- beallitasok ---
    lines.append("  <beallitasok>")
    add(lines, 4, "szamlaagentkulcs", beallitasok.get("szamlaagentkulcs"), required=True)
    add_bool(lines, 4, "eszamla", beallitasok.get("eszamla", True))
    add_bool(lines, 4, "szamlaLetoltes", beallitasok.get("szamlaLetoltes", True))
    add(lines, 4, "szamlaLetoltesPld", beallitasok.get("szamlaLetoltesPld", 1))
    add(lines, 4, "valaszVerzio", beallitasok.get("valaszVerzio", 1))
    add(lines, 4, "aggregator", beallitasok.get("aggregator"))
    add(lines, 4, "szamlaKulsoAzon", beallitasok.get("szamlaKulsoAzon"))
    lines.append("  </beallitasok>")

    # --- fejlec ---
    lines.append("  <fejlec>")
    add(lines, 4, "keltDatum", fejlec.get("keltDatum"))
    add(lines, 4, "teljesitesDatum", fejlec.get("teljesitesDatum"))
    add(lines, 4, "fizetesiHataridoDatum", fejlec.get("fizetesiHataridoDatum"))
    add(lines, 4, "fizmod", fejlec.get("fizmod", "Átutalás"), required=True)
    add(lines, 4, "penznem", fejlec.get("penznem", "HUF"), required=True)
    add(lines, 4, "szamlaNyelve", fejlec.get("szamlaNyelve", "hu"), required=True)
    add(lines, 4, "megjegyzes", fejlec.get("megjegyzes"))
    # Devizás számlához
    if fejlec.get("penznem") and fejlec.get("penznem") != "HUF":
        add(lines, 4, "arfolyamBank", fejlec.get("arfolyamBank", "MNB"))
        add(lines, 4, "arfolyam", fejlec.get("arfolyam", "0.0"))
    add(lines, 4, "rendelesSzam", fejlec.get("rendelesSzam"))
    add(lines, 4, "elorefizetesiSzamla", fejlec.get("elorefizetesiSzamla"))
    add_bool(lines, 4, "dijbekero", is_proforma)
    add(lines, 4, "szamlaszamElotag", fejlec.get("szamlaszamElotag"))
    lines.append("  </fejlec>")

    # --- elado ---
    lines.append("  <elado>")
    add(lines, 4, "bank", elado.get("bank"))
    add(lines, 4, "bankszamlaszam", elado.get("bankszamlaszam"))
    add(lines, 4, "emailReplyto", elado.get("emailReplyto"))
    add(lines, 4, "emailTargy", elado.get("emailTargy"))
    add(lines, 4, "emailSzoveg", elado.get("emailSzoveg"))
    add(lines, 4, "alairoNeve", elado.get("alairoNeve"))
    lines.append("  </elado>")

    # --- vevo ---
    lines.append("  <vevo>")
    add(lines, 4, "nev", vevo.get("nev"), required=True)
    add(lines, 4, "orszag", vevo.get("orszag", "Magyarország"))
    add(lines, 4, "irsz", vevo.get("irsz"), required=True)
    add(lines, 4, "telepules", vevo.get("telepules"), required=True)
    add(lines, 4, "cim", vevo.get("cim"), required=True)
    add(lines, 4, "email", vevo.get("email"))
    add_bool(lines, 4, "sendEmail", vevo.get("sendEmail", False))
    add(lines, 4, "adoalany", vevo.get("adoalany"))
    add(lines, 4, "adoszam", vevo.get("adoszam"))
    add(lines, 4, "adoszamEU", vevo.get("adoszamEU"))
    add(lines, 4, "postazasiNev", vevo.get("postazasiNev"))
    add(lines, 4, "postazasiOrszag", vevo.get("postazasiOrszag"))
    add(lines, 4, "postazasiIrsz", vevo.get("postazasiIrsz"))
    add(lines, 4, "postazasiTelepules", vevo.get("postazasiTelepules"))
    add(lines, 4, "postazasiCim", vevo.get("postazasiCim"))
    add(lines, 4, "azonosito", vevo.get("azonosito"))
    add(lines, 4, "telefonszam", vevo.get("telefonszam"))
    add(lines, 4, "megjegyzes", vevo.get("megjegyzes"))
    lines.append("  </vevo>")

    # --- tetelek ---
    lines.append("  <tetelek>")
    if not tetelek:
        print("ERROR: legalább egy tétel szükséges", file=sys.stderr)
        sys.exit(2)
    for t in tetelek:
        lines.extend(build_tetel(t, indent=4))
    lines.append("  </tetelek>")

    lines.append("</xmlszamla>")
    return "\n".join(lines) + "\n"


def build_storno(config: dict) -> str:
    """Sztornó számla XML (xmlszamlast gyökérrel)."""
    beallitasok = config.get("beallitasok", {})
    fejlec = config.get("fejlec", {})
    elado = config.get("elado", {})
    vevo = config.get("vevo", {})

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        '<xmlszamlast xmlns="http://www.szamlazz.hu/xmlszamlast" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xsi:schemaLocation="http://www.szamlazz.hu/xmlszamlast '
        'https://www.szamlazz.hu/szamla/docs/xsds/agentst/xmlszamlast.xsd">'
    )

    lines.append("  <beallitasok>")
    add(lines, 4, "szamlaagentkulcs", beallitasok.get("szamlaagentkulcs"), required=True)
    add_bool(lines, 4, "eszamla", beallitasok.get("eszamla", False))
    add_bool(lines, 4, "szamlaLetoltes", beallitasok.get("szamlaLetoltes", True))
    add(lines, 4, "szamlaLetoltesPld", beallitasok.get("szamlaLetoltesPld", 1))
    lines.append("  </beallitasok>")

    lines.append("  <fejlec>")
    add(lines, 4, "szamlaszam", fejlec.get("szamlaszam"), required=True)
    add(lines, 4, "keltDatum", fejlec.get("keltDatum"))
    add(lines, 4, "teljesitesDatum", fejlec.get("teljesitesDatum"))
    add(lines, 4, "tipus", fejlec.get("tipus", "SS"))
    lines.append("  </fejlec>")

    lines.append("  <elado>")
    add(lines, 4, "emailReplyto", elado.get("emailReplyto"))
    add(lines, 4, "emailTargy", elado.get("emailTargy"))
    add(lines, 4, "emailSzoveg", elado.get("emailSzoveg"))
    lines.append("  </elado>")

    lines.append("  <vevo>")
    add(lines, 4, "email", vevo.get("email"))
    lines.append("  </vevo>")

    lines.append("</xmlszamlast>")
    return "\n".join(lines) + "\n"


# ---------- main ----------

def load_config(path: str | None) -> dict:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    data = sys.stdin.read()
    if not data.strip():
        print("ERROR: üres input (--config vagy stdin kell)", file=sys.stderr)
        sys.exit(2)
    return json.loads(data)


def main():
    parser = argparse.ArgumentParser(
        description="Szamlazz.hu Agent API XML generátor (JSON input → XML output)"
    )
    parser.add_argument(
        "--mode",
        choices=["invoice", "storno", "proforma"],
        default="invoice",
        help="A generálandó XML típusa",
    )
    parser.add_argument(
        "--config",
        help="JSON config fájl útvonala (alternatíva: stdin)",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except json.JSONDecodeError as ex:
        print(f"ERROR: érvénytelen JSON input: {ex}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"ERROR: config fájl nem található: {args.config}", file=sys.stderr)
        sys.exit(2)

    if args.mode == "storno":
        xml = build_storno(config)
    else:
        xml = build_invoice(config, args.mode)

    sys.stdout.write(xml)


if __name__ == "__main__":
    main()
