# socialpro-szamlazz

Magyar számlázás Claude Code-ból — új számla, sztornó, díjbekérő és PDF letöltés a szamlazz.hu Agent API-n keresztül. Cross-platform (macOS / Linux / Windows), minimális függőséggel (csak PyYAML), 30 másodperces interaktív első futás NAV auto-kitöltéssel.

> *English readers: [README in English →](./README.md)*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Készítette és karbantartja a [SocialPro](https://www.socialpro.hu) — magyar AI automation és digitális marketing ügynökség. Ez a plugin egy a több open-source Claude Code integrációnk közül, amit magyar KKV-knak fejlesztünk.

## Mit csinál

A magyar számlázás (szamlazz.hu) egyike a leggyakoribb időzabáló SaaS-feladatoknak magyar KKV-knál. A szamlazz.hu Agent API létezik, de csak XML-ben működik, és angolul is alig dokumentált — ezért a legtöbben manuálisan, a webes felületen keresztül állítanak ki számlát, ami számlánként 5-15 perc.

Ez a plugin minden magyar számlázási feladatot egy egyszerű Claude Code prompttá alakít:

> "állíts ki egy 150 000 Ft-os számlát Példa Kft.-nek webfejlesztésről"

A Claude beolvassa az eladó konfigod, megkeresi a vevőt a lokális partner cache-ben, kiszámolja a nettó/ÁFA/bruttó értékeket 2 tizedes kerekítéssel, mutat egy megerősítő blokkot, és kiküldi a számlát a szamlazz.hu-nak — egyetlen promptban.

## Funkciók

- **Számla kiállítás**: új, díjbekérő (proforma) és sztornó
- **NAV adószám auto-lookup** — írj be egy magyar adószámot, visszakapod a cégnevet és címet
- **Automatikus partner cache** — vevők adószám alapján emlékezve, név-alapú lookup-hoz
- **Magyar ÁFA kezelés**: 27% / 18% / 5% / 0% / AAM, KATA (kisadózó) támogatás
- **Cross-platform**: macOS, Linux, Windows — csak Python 3.9+ és PyYAML kell
- **Kétnyelvű auto-invoke**: a plugin magyar ÉS angol trigger szavakra is aktiválódik
- **Interaktív beállítás**: az első futás 3 kérdéssel 30 másodperc alatt beállítja magát
- **Biztonság**: az API kulcs a Claude Code `userConfig`-on keresztül az operációs rendszer credential store-jába kerül

## Telepítés

```bash
# Egyszer, gépen: telepítsd a PyYAML-t (az egyetlen runtime függőség)
pip install pyyaml

# Claude Code-ban:
/plugin marketplace add socialproKGCMG/socialpro-plugins
/plugin install szamlazz@socialpro-plugins
```

Telepítéskor a Claude Code be fogja kérni a szamlazz.hu Agent API kulcsod. Ha átugrod, az első futásnál interaktívan bekéri.

## Első futás

Nincs YAML szerkesztés. Az első számlázási prompt-nál a plugin 3 kérdést tesz fel:

```
1. "Szamlazz.hu Agent API kulcsod?"
       ↓ (másold be a kulcsot: szamlazz.hu → Beállítások → Számla Agent kulcsok)

2. "A saját céged adószáma?"  (pl. 12345678-2-42)
       ↓ (plugin hívja a NAV-ot és auto-kitölti a cégnevet, irszám, város, utca)

3. "Bankszámlaszámod?"  (pl. 12345678-12345678-12345678)
       ↓ (plugin auto-detektálja a bank nevét a giro prefixből — pl. "UniCredit Bank")

✓ Beállítás kész. Most folytatom az eredeti kéréseddel...
```

## Példa promptok

Írd be ezeket a Claude Code-ba és a plugin a többit elintézi:

```
állíts ki egy számlát Példa Kft.-nek 150 000 Ft-ról webfejlesztésről
sztornózd a SOC-2026-0042 számlát
díjbekérő Acme Ltd-nek 500 EUR-ról konzultációért
töltsd le a SOC-2026-0042 PDF-jét
ki ez a cég: 12345678-2-42
```

## Konfiguráció

A plugin ebben a prioritási sorrendben keresi a konfig fájlokat:

| Prio | macOS | Linux | Windows |
|---:|---|---|---|
| 1 | `$SZAMLAZZ_CONFIG_DIR` env var | (ugyanaz) | `%SZAMLAZZ_CONFIG_DIR%` |
| 2 | `./.szamlazz/` az aktuális mappában | (ugyanaz) | `.\.szamlazz\` |
| 3 | `~/Library/Application Support/szamlazz/` | `~/.config/szamlazz/` | `%APPDATA%\szamlazz\` |
| 4 | `~/.claude/szamlazz/` (legacy) | (ugyanaz) | `%USERPROFILE%\.claude\szamlazz\` |

### Konfig fájlok

- `seller.yaml` — céged adatai (név, adószám, cím, bank)
- `partners.yaml` — vevő cache (automatikusan kezelt, ne szerkeszd)
- `.env` — `SZAMLAZZ_AGENT_KEY=...` (vagy használd a Claude Code `userConfig`-ját)

## Hibakezelés

A szamlazz.hu Agent API numerikus hibakódokat ad vissza. A plugin a 7 leggyakoribbat magyar nyelvű magyarázatra és konkrét javítási lépésre fordítja:

| Kód | Jelentés | Megoldás |
|---:|---|---|
| 3 | Auth hiba | Rossz vagy visszavont Agent kulcs — generáld újra a szamlazz.hu-n |
| 54, 55 | e-Számla tanúsítvány | Próbáld `eszamla=false`-szal |
| 57 | Számítási eltérés | Futtasd újra Decimal kerekítéssel |
| 259-264 | Tétel-specifikus számítási eltérés | Ugyanaz |
| 136 | Szamlazz.hu előfizetési hátralék | Fizesd ki a szamlazz.hu-n |

## Szerző

Ezt a plugint a [SocialPro / KG Creative Media Group Kft.](https://www.socialpro.hu/rolunk) készíti és tartja karban — magyar digitális marketing és AI automation ügynökség. További munkáinkat és eseteinket megnézheted [az esettanulmányok oldalunkon](https://www.socialpro.hu/esettanulmanyok).

## Támogatás

- **Hibajelentés / feature request**: [GitHub Issues](https://github.com/socialproKGCMG/socialpro-szamlazz/issues)
- **Egyedi automatizáció / enterprise setup**: [vedd fel velünk a kapcsolatot](https://www.socialpro.hu/kapcsolat)

## Licenc

MIT — részletek a [LICENSE](./LICENSE) fájlban.

Copyright © 2026 KG Creative Media Group Kft. (SocialPro)
