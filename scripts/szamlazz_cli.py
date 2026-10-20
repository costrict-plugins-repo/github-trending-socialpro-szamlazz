#!/usr/bin/env python3
"""socialpro-szamlazz CLI — single entry point for all szamlazz.hu operations.

Subcommands:
  doctor      Report current config state as JSON or text
  init        Interactive first-run setup
  invoice     Issue a new invoice from a JSON config
  storno      Cancel an existing invoice
  proforma    Issue a proforma (díjbekérő)
  pdf-fetch   Re-download the PDF of a previously issued invoice
  xml-fetch   Fetch the XML of a previously issued invoice (for customer data)
  taxpayer    Look up a Hungarian company by tax number via NAV

All subcommands read config from the first matching location:
  1. $SZAMLAZZ_CONFIG_DIR
  2. ./.szamlazz/
  3. OS-default global dir
  4. ~/.claude/szamlazz/  (legacy)

API key is loaded from $SZAMLAZZ_AGENT_KEY or the .env file in the config dir.
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Ensure lib/ is importable
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from lib import config  # noqa: E402
from lib import http_client  # noqa: E402
from lib import errors as err_module  # noqa: E402

try:
    import yaml  # PyYAML
    _YAML_OK = True
    _YAML_ERROR = ""
except ImportError as e:
    _YAML_OK = False
    _YAML_ERROR = str(e)


# ---------------------------------------------------------------------------
# doctor subcommand
# ---------------------------------------------------------------------------

def cmd_doctor(args) -> int:
    if not _YAML_OK:
        state = {
            "status": "error",
            "message": f"PyYAML not installed: {_YAML_ERROR}. Run: pip install pyyaml",
        }
        _emit(state, args.json)
        return 2

    config_dir = config.resolve_config_dir()
    if config_dir is None:
        state = {
            "status": "no_config_dir",
            "default_setup_dir": str(config.default_config_dir_for_setup()),
        }
        _emit(state, args.json)
        return 0

    seller_file = config_dir / "seller.yaml"
    seller_ok = False
    if seller_file.is_file():
        try:
            data = yaml.safe_load(seller_file.read_text(encoding="utf-8")) or {}
            required = ["cegnev", "irszam", "telepules", "cim", "adoszam"]
            bank = data.get("bank") or {}
            if all(data.get(k) for k in required) and bank.get("nev") and bank.get("szamlaszam"):
                seller_ok = True
        except yaml.YAMLError as e:
            state = {
                "status": "error",
                "config_dir": str(config_dir),
                "message": f"seller.yaml parse error: {e}",
            }
            _emit(state, args.json)
            return 2

    if not seller_ok:
        state = {
            "status": "missing_seller",
            "config_dir": str(config_dir),
        }
        _emit(state, args.json)
        return 0

    key = config.load_agent_key(config_dir)
    if not key:
        state = {
            "status": "missing_key",
            "config_dir": str(config_dir),
        }
        _emit(state, args.json)
        return 0

    state = {
        "status": "ready",
        "config_dir": str(config_dir),
    }
    _emit(state, args.json)
    return 0


def _emit(state: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(state, ensure_ascii=False))
    else:
        for k, v in state.items():
            print(f"{k}: {v}")


# ---------------------------------------------------------------------------
# taxpayer subcommand
# ---------------------------------------------------------------------------

def _fetch_taxpayer_xml(tax_id: str, agent_key: str) -> str:
    """POST a taxpayer query to szamlazz.hu and return the XML response body."""
    request_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xmlTaxpayer xmlns="http://www.szamlazz.hu/xmlTaxpayer">\n'
        f'  <beallitasok><szamlaagentkulcs>{agent_key}</szamlaagentkulcs></beallitasok>\n'
        f'  <torzsszam>{tax_id}</torzsszam>\n'
        '</xmlTaxpayer>\n'
    )

    response = http_client.post_multipart(
        url="https://www.szamlazz.hu/szamla/",
        files={"action-xmltaxpayer": ("taxpayer.xml", request_xml.encode("utf-8"))},
    )
    return response.body.decode("utf-8", errors="replace")


def _taxpayer_lookup(tax_id: str, agent_key: str):
    from lib import nav_lookup
    normalized = nav_lookup.normalize_tax_number(tax_id)
    short_id = normalized.split("-")[0]
    xml_text = _fetch_taxpayer_xml(short_id, agent_key)
    return nav_lookup.parse_taxpayer_xml(xml_text)


def cmd_taxpayer(args) -> int:
    config_dir = config.resolve_config_dir()
    agent_key = config.load_agent_key(config_dir)
    if not agent_key:
        print(
            "Error: no SZAMLAZZ_AGENT_KEY found. Run `szamlazz_cli doctor` for details.",
            file=sys.stderr,
        )
        return 2

    try:
        info = _taxpayer_lookup(args.tax_id, agent_key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if info is None:
        result = {"status": "not_found", "tax_id": args.tax_id}
    else:
        result = {
            "status": "found",
            "tax_id": args.tax_id,
            "name": info.name,
            "postal_code": info.postal_code,
            "city": info.city,
            "street_line": info.street_line,
        }

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for k, v in result.items():
            print(f"{k}: {v}")
    return 0


# ---------------------------------------------------------------------------
# invoice subcommand
# ---------------------------------------------------------------------------

def _build_xml_from_json(json_path: Path, mode: str, agent_key: str) -> bytes:
    """Run build_invoice_xml.py as a subprocess and capture the XML output.

    We inject the agent key by writing an intermediate JSON copy with the key
    placed in `beallitasok.szamlaagentkulcs` so the existing script picks it up.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))
    data.setdefault("beallitasok", {})["szamlaagentkulcs"] = agent_key

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".json", delete=False,
    ) as f:
        json.dump(data, f, ensure_ascii=False)
        tmp_json = Path(f.name)

    try:
        env = {**__import__("os").environ, "PYTHONUTF8": "1"}
        result = subprocess.run(
            [
                sys.executable,
                str(_HERE / "build_invoice_xml.py"),
                "--mode", mode,
                "--config", str(tmp_json),
            ],
            capture_output=True, check=True, env=env,
        )
        return result.stdout
    finally:
        try:
            tmp_json.unlink()
        except OSError:
            pass


def cmd_invoice(args) -> int:
    config_dir = config.resolve_config_dir()
    agent_key = config.load_agent_key(config_dir)
    if not agent_key:
        print("Error: no SZAMLAZZ_AGENT_KEY configured.", file=sys.stderr)
        return 2

    xml_bytes = _build_xml_from_json(Path(args.config), mode="invoice", agent_key=agent_key)

    if args.dry_run:
        sys.stdout.write(xml_bytes.decode("utf-8", errors="replace"))
        return 0

    response = http_client.post_multipart(
        url="https://www.szamlazz.hu/szamla/",
        files={"action-xmlagentxmlfile": ("szamla.xml", xml_bytes)},
    )

    error_code = response.headers.get("szlahu_error_code", "")
    if error_code:
        exp = err_module.explain_error(
            code=error_code,
            raw_message=response.headers.get("szlahu_error", ""),
        )
        print(err_module.format_error(exp), file=sys.stderr)
        return 1

    invoice_number = response.headers.get("szlahu_szamlaszam", "unknown")
    netto = response.headers.get("szlahu_nettovegosszeg", "")
    afa = response.headers.get("szlahu_afaertek", "")
    brutto = response.headers.get("szlahu_bruttovegosszeg", "")

    # Save the returned PDF
    output_dir = Path(args.output_dir or "./invoices")
    ym = datetime.date.today().strftime("%Y-%m")
    pdf_dir = output_dir / ym
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{invoice_number}.pdf"
    pdf_path.write_bytes(response.body)

    result = {
        "status": "ok",
        "invoice_number": invoice_number,
        "netto": netto,
        "afa": afa,
        "brutto": brutto,
        "pdf_path": str(pdf_path),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"✓ Számla kiállítva: {invoice_number}")
        print(f"  Nettó:  {netto}")
        print(f"  ÁFA:    {afa}")
        print(f"  Bruttó: {brutto}")
        print(f"  PDF:    {pdf_path}")
    return 0


# ---------------------------------------------------------------------------
# storno subcommand
# ---------------------------------------------------------------------------

def cmd_storno(args) -> int:
    config_dir = config.resolve_config_dir()
    agent_key = config.load_agent_key(config_dir)
    if not agent_key:
        print("Error: no SZAMLAZZ_AGENT_KEY configured.", file=sys.stderr)
        return 2

    # Build the storno XML inline (no JSON config needed — just invoice number)
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xmlszamlast xmlns="http://www.szamlazz.hu/xmlszamlast">\n'
        '  <beallitasok>\n'
        f'    <szamlaagentkulcs>{agent_key}</szamlaagentkulcs>\n'
        '    <eszamla>false</eszamla>\n'
        '    <szamlaLetoltes>true</szamlaLetoltes>\n'
        '  </beallitasok>\n'
        '  <fejlec>\n'
        f'    <szamlaszam>{args.invoice_number}</szamlaszam>\n'
    )
    if args.reason:
        xml += f'    <keltDatum>{datetime.date.today().isoformat()}</keltDatum>\n'
    xml += '  </fejlec>\n</xmlszamlast>\n'

    if args.dry_run:
        sys.stdout.write(xml)
        return 0

    response = http_client.post_multipart(
        url="https://www.szamlazz.hu/szamla/",
        files={"action-szamla_agent_st": ("storno.xml", xml.encode("utf-8"))},
    )

    error_code = response.headers.get("szlahu_error_code", "")
    if error_code:
        exp = err_module.explain_error(code=error_code, raw_message=response.headers.get("szlahu_error", ""))
        print(err_module.format_error(exp), file=sys.stderr)
        return 1

    storno_number = response.headers.get("szlahu_szamlaszam", "unknown")
    output_dir = Path(args.output_dir or "./invoices")
    ym = datetime.date.today().strftime("%Y-%m")
    pdf_dir = output_dir / ym
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{storno_number}.pdf"
    pdf_path.write_bytes(response.body)

    result = {
        "status": "ok",
        "storno_of": args.invoice_number,
        "storno_number": storno_number,
        "pdf_path": str(pdf_path),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"✓ Sztornó számla kiállítva: {storno_number}")
        print(f"  Az eredeti számlához: {args.invoice_number}")
        print(f"  PDF: {pdf_path}")
    return 0


# ---------------------------------------------------------------------------
# proforma subcommand — thin wrapper around invoice with mode=proforma
# ---------------------------------------------------------------------------

def cmd_proforma(args) -> int:
    config_dir = config.resolve_config_dir()
    agent_key = config.load_agent_key(config_dir)
    if not agent_key:
        print("Error: no SZAMLAZZ_AGENT_KEY configured.", file=sys.stderr)
        return 2

    xml_bytes = _build_xml_from_json(Path(args.config), mode="proforma", agent_key=agent_key)

    if args.dry_run:
        sys.stdout.write(xml_bytes.decode("utf-8", errors="replace"))
        return 0

    response = http_client.post_multipart(
        url="https://www.szamlazz.hu/szamla/",
        files={"action-xmlagentxmlfile": ("proforma.xml", xml_bytes)},
    )
    error_code = response.headers.get("szlahu_error_code", "")
    if error_code:
        exp = err_module.explain_error(code=error_code, raw_message=response.headers.get("szlahu_error", ""))
        print(err_module.format_error(exp), file=sys.stderr)
        return 1

    pf_number = response.headers.get("szlahu_szamlaszam", "unknown")
    output_dir = Path(args.output_dir or "./invoices")
    ym = datetime.date.today().strftime("%Y-%m")
    pdf_dir = output_dir / ym
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{pf_number}.pdf"
    pdf_path.write_bytes(response.body)

    result = {"status": "ok", "proforma_number": pf_number, "pdf_path": str(pdf_path)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"✓ Díjbekérő kiállítva: {pf_number}")
        print(f"  PDF: {pdf_path}")
    return 0


# ---------------------------------------------------------------------------
# pdf-fetch subcommand
# ---------------------------------------------------------------------------

def cmd_pdf_fetch(args) -> int:
    config_dir = config.resolve_config_dir()
    agent_key = config.load_agent_key(config_dir)
    if not agent_key:
        print("Error: no SZAMLAZZ_AGENT_KEY configured.", file=sys.stderr)
        return 2

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xmlszamlapdf xmlns="http://www.szamlazz.hu/xmlszamlapdf">\n'
        f'  <szamlaagentkulcs>{agent_key}</szamlaagentkulcs>\n'
        f'  <szamlaszam>{args.invoice_number}</szamlaszam>\n'
        '</xmlszamlapdf>\n'
    )

    response = http_client.post_multipart(
        url="https://www.szamlazz.hu/szamla/",
        files={"action-szamla_agent_pdf": ("pdf_fetch.xml", xml.encode("utf-8"))},
    )
    error_code = response.headers.get("szlahu_error_code", "")
    if error_code:
        exp = err_module.explain_error(code=error_code, raw_message=response.headers.get("szlahu_error", ""))
        print(err_module.format_error(exp), file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir or "./invoices")
    ym = datetime.date.today().strftime("%Y-%m")
    pdf_dir = output_dir / ym
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / f"{args.invoice_number}.pdf"
    pdf_path.write_bytes(response.body)

    result = {"status": "ok", "invoice_number": args.invoice_number, "pdf_path": str(pdf_path)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"✓ PDF letöltve: {pdf_path}")
    return 0


# ---------------------------------------------------------------------------
# xml-fetch subcommand
# ---------------------------------------------------------------------------

def cmd_xml_fetch(args) -> int:
    config_dir = config.resolve_config_dir()
    agent_key = config.load_agent_key(config_dir)
    if not agent_key:
        print("Error: no SZAMLAZZ_AGENT_KEY configured.", file=sys.stderr)
        return 2

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xmlszamlaxml xmlns="http://www.szamlazz.hu/xmlszamlaxml">\n'
        f'  <szamlaagentkulcs>{agent_key}</szamlaagentkulcs>\n'
        f'  <szamlaszam>{args.invoice_number}</szamlaszam>\n'
        '</xmlszamlaxml>\n'
    )

    response = http_client.post_multipart(
        url="https://www.szamlazz.hu/szamla/",
        files={"action-szamla_agent_xml": ("xml_fetch.xml", xml.encode("utf-8"))},
    )
    error_code = response.headers.get("szlahu_error_code", "")
    if error_code:
        exp = err_module.explain_error(code=error_code, raw_message=response.headers.get("szlahu_error", ""))
        print(err_module.format_error(exp), file=sys.stderr)
        return 1

    sys.stdout.write(response.body.decode("utf-8", errors="replace"))
    return 0


# ---------------------------------------------------------------------------
# init subcommand — write seller.yaml + .env from CLI flags
# (the SKILL.md handles user interaction via AskUserQuestion)
# ---------------------------------------------------------------------------

def cmd_init(args) -> int:
    target = Path(args.target_dir) if args.target_dir else config.default_config_dir_for_setup()
    target.mkdir(parents=True, exist_ok=True)

    seller = {
        "cegnev": args.cegnev,
        "irszam": args.irszam,
        "telepules": args.telepules,
        "cim": args.cim,
        "adoszam": args.adoszam,
        "bank": {
            "nev": args.bank_nev,
            "szamlaszam": args.bank_szamlaszam,
        },
        "email": args.email,
        "kisadozo": args.kisadozo.lower() == "true",
    }
    seller_path = target / "seller.yaml"
    seller_path.write_text(
        yaml.safe_dump(seller, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    if args.agent_key:
        env_path = target / ".env"
        env_path.write_text(
            f"SZAMLAZZ_AGENT_KEY={args.agent_key}\n",
            encoding="utf-8",
        )
        # Restrict perms on Unix (chmod is a no-op on Windows)
        try:
            import stat
            env_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600
        except (OSError, NotImplementedError):
            pass

    # Initialize empty partners.yaml if missing
    partners_path = target / "partners.yaml"
    if not partners_path.exists():
        partners_path.write_text("partners: []\n", encoding="utf-8")

    result = {
        "status": "ok",
        "config_dir": str(target),
        "seller_yaml": str(seller_path),
        "partners_yaml": str(partners_path),
        "env_file": str(target / ".env") if args.agent_key else "",
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"✓ Beállítás mentve: {target}")
    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="szamlazz_cli",
        description="socialpro-szamlazz CLI for szamlazz.hu Agent API operations",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_doctor = sub.add_parser("doctor", help="Report config state")
    p_doctor.add_argument("--json", action="store_true", help="Emit JSON output")
    p_doctor.set_defaults(func=cmd_doctor)

    p_inv = sub.add_parser("invoice", help="Issue a new invoice")
    p_inv.add_argument("--config", required=True, help="Path to input JSON config")
    p_inv.add_argument("--output-dir", default="./invoices", help="Where to save the returned PDF")
    p_inv.add_argument("--json", action="store_true", help="Emit JSON output")
    p_inv.add_argument("--dry-run", action="store_true", help="Print XML without sending")
    p_inv.set_defaults(func=cmd_invoice)

    p_st = sub.add_parser("storno", help="Cancel an invoice")
    p_st.add_argument("--invoice-number", required=True, help="Invoice number to cancel")
    p_st.add_argument("--reason", default="", help="Reason for cancellation (stored internally)")
    p_st.add_argument("--output-dir", default="./invoices")
    p_st.add_argument("--json", action="store_true")
    p_st.add_argument("--dry-run", action="store_true")
    p_st.set_defaults(func=cmd_storno)

    p_pf = sub.add_parser("proforma", help="Issue a proforma (díjbekérő)")
    p_pf.add_argument("--config", required=True)
    p_pf.add_argument("--output-dir", default="./invoices")
    p_pf.add_argument("--json", action="store_true")
    p_pf.add_argument("--dry-run", action="store_true")
    p_pf.set_defaults(func=cmd_proforma)

    p_pdf = sub.add_parser("pdf-fetch", help="Re-download an invoice PDF")
    p_pdf.add_argument("--invoice-number", required=True)
    p_pdf.add_argument("--output-dir", default="./invoices")
    p_pdf.add_argument("--json", action="store_true")
    p_pdf.set_defaults(func=cmd_pdf_fetch)

    p_xf = sub.add_parser("xml-fetch", help="Fetch an invoice XML for customer data extraction")
    p_xf.add_argument("--invoice-number", required=True)
    p_xf.set_defaults(func=cmd_xml_fetch)

    p_init = sub.add_parser("init", help="Write seller.yaml and .env from flags")
    p_init.add_argument("--target-dir", help="Config dir (default: platform-specific)")
    p_init.add_argument("--cegnev", required=True)
    p_init.add_argument("--irszam", required=True)
    p_init.add_argument("--telepules", required=True)
    p_init.add_argument("--cim", required=True)
    p_init.add_argument("--adoszam", required=True)
    p_init.add_argument("--bank-nev", required=True)
    p_init.add_argument("--bank-szamlaszam", required=True)
    p_init.add_argument("--email", required=True)
    p_init.add_argument("--kisadozo", default="false", choices=["true", "false"])
    p_init.add_argument("--agent-key", default="")
    p_init.add_argument("--json", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_tx = sub.add_parser("taxpayer", help="NAV taxpayer lookup")
    p_tx.add_argument("tax_id", help="Hungarian tax number (8 digits, or 8-1-2 with dashes)")
    p_tx.add_argument("--json", action="store_true", help="Emit JSON output")
    p_tx.set_defaults(func=cmd_taxpayer)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
