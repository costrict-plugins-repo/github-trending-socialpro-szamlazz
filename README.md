# socialpro-szamlazz

Hungarian invoicing from Claude Code — issue, cancel, and fetch invoices via the szamlazz.hu Agent API. Cross-platform, near-zero-dependency (PyYAML only), with an interactive first-run setup that uses NAV auto-lookup to configure itself in 30 seconds.

> *Magyar olvasóknak: [README magyarul →](./README.hu.md)*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet)
![Cross-platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-informational)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)

Built by [SocialPro](https://www.socialpro.hu) — a Hungarian AI automation and digital marketing agency. This plugin is one of several open-source Claude Code integrations we maintain for Hungarian small businesses.

## What it does

Hungarian invoicing (számlázás) via [szamlazz.hu](https://www.szamlazz.hu/) is one of the most common SaaS-driven time sinks for Hungarian SMEs. Their Agent API exists but is XML-only and undocumented in English — so most people issue invoices manually through the web UI, which takes 5-15 minutes per invoice.

This plugin turns any Hungarian invoicing task into a natural-language prompt in Claude Code:

> "állíts ki egy 150 000 Ft-os számlát Példa Kft.-nek webfejlesztésről"

Claude reads your seller config, looks up the customer in the local partner cache, calculates net/VAT/gross amounts with proper 2-decimal rounding, shows you a confirmation block, and fires the invoice to szamlazz.hu — all in one prompt.

## Features

- **Issue invoices**: regular, proforma (díjbekérő), and storno (cancellation)
- **NAV taxpayer auto-lookup** — type a Hungarian tax number, get the company name and address back
- **Automatic partner cache** — customers are remembered by tax ID for name-based reuse
- **Hungarian VAT handling**: 27% / 18% / 5% / 0% / AAM, KATA (kisadózó) support
- **Cross-platform**: native on macOS, Linux, and Windows — only requires Python 3.9+ and PyYAML
- **Bilingual auto-invoke**: the plugin activates on Hungarian AND English trigger words
- **Interactive setup**: the first-run flow asks 3 questions and configures itself in 30 seconds
- **Secure by default**: API key stored in your OS credential store via Claude Code's `userConfig`

## Installation

```bash
# Once, per machine: install PyYAML (the only runtime dependency)
pip install pyyaml

# In Claude Code:
/plugin marketplace add socialproKGCMG/socialpro-plugins
/plugin install szamlazz@socialpro-plugins
```

During install, Claude Code will prompt you for your szamlazz.hu Agent API key. You can skip this and the first-run flow will ask for it interactively.

## First-run experience

No YAML editing required. On your first invoicing prompt, the plugin asks 3 questions:

```
1. "Szamlazz.hu Agent API kulcsod?"
       ↓ (paste the key from szamlazz.hu → Beállítások → Számla Agent kulcsok)

2. "A saját céged adószáma?"  (e.g. 12345678-2-42)
       ↓ (plugin calls NAV and auto-fills name, postal code, city, street)

3. "Bankszámlaszámod?"  (e.g. 12345678-12345678-12345678)
       ↓ (plugin auto-detects the bank name from the giro prefix — e.g. "UniCredit Bank")

✓ Beállítás kész. Most folytatom az eredeti kéréseddel...
```

## Usage examples

Type these in Claude Code and the plugin handles the rest:

```
állíts ki egy számlát Példa Kft.-nek 150 000 Ft-ról webfejlesztésről
sztornózd a SOC-2026-0042 számlát
díjbekérő Acme Ltd-nek 500 EUR-ról konzultációért
töltsd le a SOC-2026-0042 PDF-jét
ki ez a cég: 12345678-2-42
```

## Configuration

The plugin looks for config files in this priority order:

| Priority | macOS | Linux | Windows |
|---:|---|---|---|
| 1 | `$SZAMLAZZ_CONFIG_DIR` (env var) | (same) | `%SZAMLAZZ_CONFIG_DIR%` |
| 2 | `./.szamlazz/` in current dir | (same) | `.\.szamlazz\` |
| 3 | `~/Library/Application Support/szamlazz/` | `$XDG_CONFIG_HOME/szamlazz/` | `%APPDATA%\szamlazz\` |
| 4 | `~/.claude/szamlazz/` (legacy) | (same) | `%USERPROFILE%\.claude\szamlazz\` |

This is deliberately flexible — a solo developer uses the global dir; an accountant with multiple clients uses `./.szamlazz/` per project. For more Hungarian-market AI automation patterns, see the [SocialPro blog for detailed AI and SEO case studies](https://www.socialpro.hu/blog).

### Config files in each directory

- `seller.yaml` — your company info (name, tax number, address, bank)
- `partners.yaml` — customer cache (managed automatically, never edit)
- `.env` — `SZAMLAZZ_AGENT_KEY=...` (or use Claude Code's `userConfig` instead)

## Troubleshooting

The szamlazz.hu Agent API returns numeric error codes. The plugin translates the 7 most common ones into Hungarian with actionable recovery steps:

| Code | Meaning | Fix |
|---:|---|---|
| 3 | Auth failed | Wrong or revoked Agent key — regenerate at szamlazz.hu |
| 54, 55 | e-Számla certificate issue | Retry with `eszamla=false` (plain PDF) |
| 57 | Calculation mismatch | Re-run with Decimal rounding |
| 259-264 | Same, line-specific | Same fix as 57 |
| 136 | Unpaid szamlazz.hu balance | Pay your subscription on the szamlazz.hu website |

## How it compares

|  | socialpro-szamlazz (this plugin) | szamlazz.hu web UI | szamlazz.hu Agent API directly |
|---|---|---|---|
| Setup time | ~30 seconds (interactive) | ~0 (browser only) | ~1-2 hours (XML, curl, debugging) |
| Per-invoice time | ~10 seconds (one prompt) | 5-15 minutes | Depends |
| NAV taxpayer lookup | Automatic | Manual (separate page) | Manual (separate endpoint) |
| Hungarian VAT handling | Automatic | Automatic | Manual |
| Partner memory | Local cache | Paid tier only | None |
| Best for | Frequent issuers, developers, automation | Occasional manual invoices | Custom integrations |

## About the author

This plugin is built and maintained by [SocialPro / KG Creative Media Group Kft.](https://www.socialpro.hu/rolunk) — a Hungarian digital marketing and AI automation agency specializing in custom AI integrations for SMEs. Our broader work includes SEO, Meta advertising, and Hungarian-market case studies which you can browse in [our case studies archive](https://www.socialpro.hu/esettanulmanyok).

## Support

- **Bug reports / feature requests**: [GitHub Issues](https://github.com/socialproKGCMG/socialpro-szamlazz/issues)
- **Custom automation or enterprise setup**: for bespoke [Hungarian accounting and billing automation](https://www.socialpro.hu/kapcsolat) contact SocialPro directly.

## License

MIT License — see [LICENSE](./LICENSE) for details.

Copyright © 2026 KG Creative Media Group Kft. (SocialPro)
