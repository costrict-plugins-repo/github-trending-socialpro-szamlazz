# Szamlazz.hu Agent API — Referencia

Rövid, praktikus reference a `/szamlazz` skill számára. Teljes doksi: https://docs.szamlazz.hu/

## Authentikáció

- **Agent kulcs**: a szamlazz.hu Vezérlőpult → "Számla Agent kulcsok" menüpontban generálható
- **Csak kisbetűs** karakterek. Nagybetű → 3-as hibakód (sikertelen bejelentkezés)
- XML mezőben: `<szamlaagentkulcs>KULCS</szamlaagentkulcs>`
- Tárolás: `<config_dir>/.env` → `SZAMLAZZ_AGENT_KEY=...` (a `<config_dir>` platformfüggő — lásd a fő SKILL.md cross-platform lookup táblázatát)

## Endpoint

Minden művelet ugyanarra az URL-re megy:
```
POST https://www.szamlazz.hu/szamla/
Content-Type: multipart/form-data
```

A művelet típusát a **form mező neve** határozza meg.

## Form mezők (művelet → form field név)

| Művelet | Form field | XML gyökér |
|---|---|---|
| Új számla / díjbekérő | `action-xmlagentxmlfile` | `<xmlszamla>` |
| Sztornó számla | `action-szamla_agent_st` | `<xmlszamlast>` |
| Befizetés rögzítés | `action-szamla_agent_kifiz` | `<xmlszamlakifiz>` |
| Számla PDF újralekérés | `action-szamla_agent_pdf` | `<xmlszamlapdf>` |
| Számla XML lekérés | `action-szamla_agent_xml` | `<xmlszamlaxml>` |
| Adószám lekérdezés (NAV) | `action-szamla_agent_taxpayer` | `<xmltaxpayer>` |
| Nyugta létrehozás | `action-szamla_agent_nyugta_create` | `<xmlnyugtacreate>` |

## Válasz — HTTP header-ek (szlahu_ prefix)

| Header | Tartalom |
|---|---|
| `szlahu_szamlaszam` | elkészült számla száma (URL-encoded) |
| `szlahu_nettovegosszeg` | összesen nettó |
| `szlahu_bruttovegosszeg` | összesen bruttó |
| `szlahu_fizetesmod` | fizetési mód |
| `szlahu_vevoifiokurl` | vevői fiók URL (ha aktív) |
| `szlahu_error` | hibaüzenet (URL-encoded) |
| `szlahu_error_code` | hibakód (szám) |

**Ha `szlahu_error_code` nem üres:** hiba történt, a szamlaszam és az összegek NEM szerepelnek.

## Válasz body (valaszVerzio=1)

- **Siker + `szamlaLetoltes=true`**: a body maga a PDF (binary, `%PDF` magic)
- **Siker + `szamlaLetoltes=false`**: `xmlagentresponse=DONE;SZAMLASZAM`
- **Hiba**: szöveges error log, `[ERR]` prefix + stack trace

## Hibakódok (gyakoriak)

| Kód | Jelentés |
|---|---|
| 1 | Rendszerkarbantartás |
| 3 | Sikertelen bejelentkezés (rossz agent kulcs, vagy nagybetűs!) |
| 53 | XML nem fájlként érkezett a form-ban |
| 54 | E-számla nincs engedélyezve a fiókon |
| 55 | E-számla aláírás sikertelen (tanúsítvány hiba) |
| 57 | XML beolvasási / validációs hiba |
| 135 | Még bejelentkezve a webes felületen (agent kulcs ajánlott) |
| 136 | Lejárt előfizetés / függő számla / fizetési hátralék |
| 164 | Több fiókhoz való hozzáférés (agent kulcs ajánlott) |
| 202 | Ismeretlen számlaszám előtag |
| 259-264 | Tétel számítás hiba (nettó/áfa/bruttó eltérés) |

**FIGYELEM**: NE próbálkozz automatikus újraküldéssel ciklusban. Max 5 próbálkozás, tesztmódban max 100 számla/óra.

## Kötelező számítások a tételeknél

A szamlazz.hu **NEM** számítja ki automatikusan, a kliensnek kell pontosan megadnia:

```
nettoErtek  = mennyiseg × nettoEgysegar
afaErtek    = nettoErtek × afakulcs / 100
bruttoErtek = nettoErtek + afaErtek
```

**Kerekítés**: 2 tizedes, ROUND_HALF_UP. Float helyett Decimal. Ha nem stimmel → 57/259/260/261/262/263/264 hibakód.

## ÁFA kulcs (afakulcs) lehetséges értékei

**Numerikus %**: `0, 5, 18, 27` (és speciális: 2.1, 4.8, 5.5, 7.7, 8.1, 9.5, stb.)

**Speciális kódok** (% jel nélkül):
- `TAHK` — tárgyi hatályán kívüli
- `TAM` — tárgyi adómentes
- `AAM` — alanyi adómentes
- `EUT` — EU-n belüli termékértékesítés
- `EUKT` — EU-n kívüli termékértékesítés
- `F.AFA` — fordított ÁFA fizetés
- `K.AFA` — különbözeti ÁFA
- `HO` — harmadik ország
- `EUE`, `EUFADE`, `EUFAD37`, `ATK`, `NAM`, `EAM`, `KBAUK`, `KBAET`

## Fizetési módok (fizmod)

`Átutalás, Készpénz, Bankkártya, PayPal, Egyéb`

## Pénznemek

`HUF, EUR, CHF, USD, GBP, PLN, CZK, RON, HRK, ...`

**Devizás számlánál** (nem HUF) kötelező:
- `<arfolyamBank>` — pl. `MNB`
- `<arfolyam>` — szám, pl. `395.50`. Ha `0.0` → automatikusan az aznapi MNB árfolyam.

## Dátum formátum

Szigorúan ISO 8601: `YYYY-MM-DD`.

## Számla nyelv (szamlaNyelve)

`hu, de, en, it, fr, ro, sk, hr`

## Karakterkódolás

UTF-8, BOM nélkül. Magyar ékezetek (á é í ó ö ő ú ü ű) natívan működnek.

## Vevő azonosító (`<azonosito>`) — ÓVATOSAN

Ha egyszer beállítasz egy azonosítót egy vevőhöz, a szamlazz.hu ezután **auto-update**-eli azzal a vevőt. Ha ugyanaz az azonosító több vevőnél → adatok keverednek. **Ajánlás**: vagy egyedi AZ, vagy üresen hagyni.
