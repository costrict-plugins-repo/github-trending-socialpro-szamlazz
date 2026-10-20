# XML sablonok — szamlazz.hu Agent API

Gyakorlati sablonok minden művelethez. A `/szamlazz` skill ezeket használja hivatkozásként.

## 1. Új számla (xmlszamla)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xmlszamla xmlns="http://www.szamlazz.hu/xmlszamla"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.szamlazz.hu/xmlszamla https://www.szamlazz.hu/szamla/docs/xsds/agent/xmlszamla.xsd">
  <beallitasok>
    <szamlaagentkulcs>AGENT_KEY</szamlaagentkulcs>
    <eszamla>true</eszamla>
    <szamlaLetoltes>true</szamlaLetoltes>
    <szamlaLetoltesPld>1</szamlaLetoltesPld>
    <valaszVerzio>1</valaszVerzio>
  </beallitasok>
  <fejlec>
    <keltDatum>2026-04-08</keltDatum>
    <teljesitesDatum>2026-04-08</teljesitesDatum>
    <fizetesiHataridoDatum>2026-04-16</fizetesiHataridoDatum>
    <fizmod>Átutalás</fizmod>
    <penznem>HUF</penznem>
    <szamlaNyelve>hu</szamlaNyelve>
    <megjegyzes>Köszönjük a bizalmat!</megjegyzes>
  </fejlec>
  <elado>
    <bank>Példa Bank</bank>
    <bankszamlaszam>12345678-12345678-12345678</bankszamlaszam>
    <emailReplyto>billing@yourcompany.example</emailReplyto>
    <emailTargy>Számla - Example Ltd.</emailTargy>
    <emailSzoveg>Mellékelten küldjük a számlát.</emailSzoveg>
    <alairoNeve>Aláíró Neve</alairoNeve>
  </elado>
  <vevo>
    <nev>Vevő Kft.</nev>
    <orszag>Magyarország</orszag>
    <irsz>1117</irsz>
    <telepules>Budapest</telepules>
    <cim>Petőfi utca 12.</cim>
    <email>info@vevo.hu</email>
    <sendEmail>false</sendEmail>
    <adoszam>12345678-2-42</adoszam>
  </vevo>
  <tetelek>
    <tetel>
      <megnevezes>Webfejlesztés</megnevezes>
      <mennyiseg>1.0</mennyiseg>
      <mennyisegiEgyseg>db</mennyisegiEgyseg>
      <nettoEgysegar>100000.00</nettoEgysegar>
      <afakulcs>27</afakulcs>
      <nettoErtek>100000.00</nettoErtek>
      <afaErtek>27000.00</afaErtek>
      <bruttoErtek>127000.00</bruttoErtek>
    </tetel>
  </tetelek>
</xmlszamla>
```

## 2. Díjbekérő (proforma)

Ugyanaz mint a számla, csak a `<fejlec>`-ben: `<dijbekero>true</dijbekero>`. A `build_invoice_xml.py --mode proforma` ezt automatikusan beállítja.

## 3. Sztornó számla (xmlszamlast)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xmlszamlast xmlns="http://www.szamlazz.hu/xmlszamlast"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://www.szamlazz.hu/xmlszamlast https://www.szamlazz.hu/szamla/docs/xsds/agentst/xmlszamlast.xsd">
  <beallitasok>
    <szamlaagentkulcs>AGENT_KEY</szamlaagentkulcs>
    <eszamla>false</eszamla>
    <szamlaLetoltes>true</szamlaLetoltes>
    <szamlaLetoltesPld>1</szamlaLetoltesPld>
  </beallitasok>
  <fejlec>
    <szamlaszam>ABC-2026-0001</szamlaszam>
    <keltDatum>2026-04-08</keltDatum>
    <teljesitesDatum>2026-04-08</teljesitesDatum>
    <tipus>SS</tipus>
  </fejlec>
  <elado>
    <emailReplyto>billing@yourcompany.example</emailReplyto>
    <emailTargy>Sztornó számla</emailTargy>
    <emailSzoveg>Mellékelten küldjük a sztornó számlát.</emailSzoveg>
  </elado>
  <vevo>
    <email>info@vevo.hu</email>
  </vevo>
</xmlszamlast>
```

## 4. Korábbi számla PDF újralekérés (xmlszamlapdf)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xmlszamlapdf xmlns="http://www.szamlazz.hu/xmlszamlapdf">
  <szamlaagentkulcs>AGENT_KEY</szamlaagentkulcs>
  <szamlaszam>ABC-2026-0001</szamlaszam>
  <valaszVerzio>1</valaszVerzio>
</xmlszamlapdf>
```

## 5. Korábbi számla XML lekérés (xmlszamlaxml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xmlszamlaxml xmlns="http://www.szamlazz.hu/xmlszamlaxml">
  <szamlaagentkulcs>AGENT_KEY</szamlaagentkulcs>
  <szamlaszam>ABC-2026-0001</szamlaszam>
</xmlszamlaxml>
```

A válaszban a teljes `<xmlszamla>` visszajön — ebből a `<vevo>` blokk kinyerhető és a `partners.yaml` cache-be tölthető.

## 6. Adószám → NAV céginformáció (xmltaxpayer)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xmltaxpayer xmlns="http://www.szamlazz.hu/xmltaxpayer">
  <beallitasok>
    <szamlaagentkulcs>AGENT_KEY</szamlaagentkulcs>
  </beallitasok>
  <torzsszam>12345678</torzsszam>
</xmltaxpayer>
```

`<torzsszam>` = az adószám első 8 számjegye. A válasz XML tartalmazza a cég nevét, címét, státuszát (a NAV online ellenőrző rendszerből).

## Devizás számla különlegességek

Ha `penznem != HUF`, a `<fejlec>` tartalmazza:

```xml
<fejlec>
  ...
  <penznem>EUR</penznem>
  <arfolyamBank>MNB</arfolyamBank>
  <arfolyam>395.50</arfolyam>
  ...
</fejlec>
```

`<arfolyam>0.0</arfolyam>` esetén a szamlazz.hu az aznapi MNB árfolyamot használja.

## Több tétel egy számlán

A `<tetelek>` blokk tetszőleges számú `<tetel>` elemet tartalmazhat, mindegyiknek saját nettó/áfa/bruttó számmal.

```xml
<tetelek>
  <tetel>
    <megnevezes>Szolgáltatás A</megnevezes>
    <mennyiseg>2.5</mennyiseg>
    <mennyisegiEgyseg>óra</mennyisegiEgyseg>
    <nettoEgysegar>20000.00</nettoEgysegar>
    <afakulcs>27</afakulcs>
    <nettoErtek>50000.00</nettoErtek>
    <afaErtek>13500.00</afaErtek>
    <bruttoErtek>63500.00</bruttoErtek>
  </tetel>
  <tetel>
    <megnevezes>Szolgáltatás B</megnevezes>
    <mennyiseg>1.0</mennyiseg>
    <mennyisegiEgyseg>db</mennyisegiEgyseg>
    <nettoEgysegar>100000.00</nettoEgysegar>
    <afakulcs>AAM</afakulcs>
    <nettoErtek>100000.00</nettoErtek>
    <afaErtek>0.00</afaErtek>
    <bruttoErtek>100000.00</bruttoErtek>
  </tetel>
</tetelek>
```

Megjegyzés a második tételhez: `AAM` = alanyi adómentes, így `afaErtek=0` és `bruttoErtek=nettoErtek`.
