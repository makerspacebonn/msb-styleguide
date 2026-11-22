"""Build index.html from src/template.html: inlines logos/*.png, the contrast matrix,
the light/dark palette and the version history from src/versionen.json.

Usage:
  python3 src/build.py                    # bauen
  python3 src/build.py --version "Was"    # Version mit Zeit eintragen (oder offene aktualisieren), dann bauen
  python3 src/build.py --pruefen          # nur prüfen: Versionseintrag da, index.html aktuell (Pre-Commit-Hook)
"""
import argparse
import base64
import hashlib
import json
import pathlib
import subprocess
from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + .05) / (y + .05)


BGS = [('Weiß', '#FFFFFF'), ('Papier', '#FBF8F2'), ('Creme', '#FAF2E4'), ('Creme kräftig', '#F5E6C9'),
       ('Grün 50', '#F0F7EA'), ('Grün 100', '#DCEFD0'), ('Grün 500 (Marke)', '#5EB130'),
       ('Grün 600 (Text)', '#33791A'), ('Grün 800', '#325725'), ('Grün 900', '#1B3714'),
       ('MINT-Fond', '#E6F5FC'), ('MINT-Violett', '#6D3E91'), ('Mitglieder-Gelb', '#FCBD30'),
       ('Maker-Orange', '#F2711C'), ('Sicherheitsrot', '#C62828'), ('Tinte', '#1E1C19')]
TXT = [('Tinte', '#1E1C19'), ('Weiß', '#FFFFFF'), ('Textgrün', '#33791A'), ('Grün 800', '#325725'),
       ('Markengrün', '#5EB130'), ('Violett', '#6D3E91'), ('Textblau', '#0070A8')]


def matrix():
    rows = ['<table class="t matrix"><tr><th>Hintergrund ↓ · Schrift →</th>'
            + ''.join(f'<th>{n}</th>' for n, _ in TXT) + '</tr>']
    for bn, bc in BGS:
        row = f'<tr><th>{bn}<br><span class="mono" style="font-weight:400">{bc}</span></th>'
        for _, tc in TXT:
            if tc == bc:
                row += '<td class="no">·</td>'
                continue
            v = ratio(bc, tc)
            if v >= 4.5:
                row += f'<td class="ok" style="background:{bc};color:{tc}">✓ Text<br><span style="font-size:12px">{v:.1f}:1</span></td>'
            elif v >= 3:
                row += f'<td class="big" style="background:{bc};color:{tc}">Groß<br><span style="font-size:12px">{v:.1f}:1</span></td>'
            else:
                row += f'<td class="no">–<br><span style="font-size:12px">{v:.1f}:1</span></td>'
        rows.append(row + '</tr>')
    rows.append('</table>')
    return '\n'.join(rows)


# Hell/Dunkel: eine Quelle für Rollentabelle, Vorschauen und Code zum Kopieren.
# (Token, Rolle, (HEX hell, Name hell), (HEX dunkel, Name dunkel), Wofür)
MODI = [
    ('hintergrund', 'Hintergrund', ('#FBF8F2', 'Papier'), ('#0C1511', 'Tannennacht'), 'Ebene 0: Seitenhintergrund'),
    ('raster', 'Raster', ('#EBF1DF', 'Rastergrün'), ('#111E13', 'Tanne Raster'), 'Rasterlinie auf Ebene 0, wenn die Seite Millimeterpapier zeigt (1 px, alle 27 px). Nur Deko, nie Schrift oder Rahmen'),
    ('flaeche', 'Fläche', ('#FFFFFF', 'Weiß'), ('#13201A', 'Tannenschwarz'), 'Ebene 1: Karten, Tabellen, Kopfleiste'),
    ('fond', 'Fond', ('#FAF2E4', 'Creme'), ('#213129', 'Tanne hell'), 'Ebene 2: Hover, Tabellenkopf, Zweitbuttons, Infokästen'),
    ('linie', 'Linie', ('#E4DCCB', 'Linie'), ('#2A3C33', 'Tanne Linie'), 'Rahmen um Karten und Tabellen, Trenner. Nicht für Eingabefelder (dafür Feld-Rand)'),
    ('text', 'Text', ('#1E1C19', 'Tinte'), ('#EDE8DE', 'Kreide'), 'Fließtext, Überschriften, harter Sticker-Schatten'),
    ('text-leise', 'Text leise', ('#5F5850', 'Stein'), ('#9BA6A0', 'Salbei'), 'Metadaten, Deaktiviertes, Rand von Eingabefeldern unter Maus oder Finger'),
    ('text-gruen', 'Grüne Schrift', ('#33791A', 'Grün 600'), ('#9CD27D', 'Grün 300'), 'Links (immer unterstrichen), Status OK, Icons mit Bedeutung'),
    ('fokus', 'Fokus', ('#33791A', 'Grün 600'), ('#9CD27D', 'Grün 300'), 'Fokusring (Tastatur): 3 px, 2 px Abstand'),
    ('button', 'Button', ('#33791A', 'Grün 600'), ('#5EB130', 'Grün 500'), 'Hauptbutton, einer pro Ansicht'),
    ('button-hover', 'Button Hover', ('#325725', 'Grün 800'), ('#9CD27D', 'Grün 300'), 'Hauptbutton unter Maus oder Finger'),
    ('button-text', 'Button-Schrift', ('#FFFFFF', 'Weiß'), ('#1E1C19', 'Tinte'), 'Schrift auf dem Hauptbutton'),
    ('fond-gruen', 'Grüner Fond', ('#F0F7EA', 'Grün 50'), ('#1B3714', 'Grün 900'), 'Status OK, ausgewählte Zeile, Tags, Icon-Kacheln'),
    ('fond-gelb', 'Gelber Fond', ('#FDF3D7', 'Gelb-Fond'), ('#33280F', 'Gelb-Fond dunkel'), 'Status Achtung (z. B. ruhend, Entscheidung nötig)'),
    ('text-gelb', 'Gelbe Schrift', ('#8A5A00', 'Ocker'), ('#FCBD30', 'Mitglieder-Gelb'), 'Schrift auf gelbem Fond'),
    ('fond-rot', 'Roter Fond', ('#FCEBE9', 'Rot-Fond'), ('#3B1A17', 'Rot-Fond dunkel'), 'Status Problem (z. B. Lastschrift fehlgeschlagen)'),
    ('text-rot', 'Warnschrift', ('#C62828', 'Sicherheitsrot'), ('#FF7B7B', 'Rot hell'), 'Fehler, Warnungen, Schrift auf rotem Fond'),
    ('fond-mint', 'MINT-Fond', ('#E6F5FC', 'MINT-Fond'), ('#152D37', 'MINT-Fond dunkel'), 'Infokästen in MINT-Medien'),
    ('text-violett', 'MINT-Violett Schrift', ('#6D3E91', 'MINT-Violett'), ('#BC94DB', 'Violett hell'), 'Violette Überschriften, schmale Balken, Icons'),
    ('text-blau', 'MINT-Blau Schrift', ('#0070A8', 'Textblau'), ('#009FE3', 'MINT-Blau'), 'Blaue Überschriften, Links in MINT-Medien'),
    ('leiste', 'Leiste', ('#13201A', 'Tannenschwarz'), ('#13201A', 'Tannenschwarz'), 'Seitenleiste in Anwendungen, auf dem Handy Kopfleiste'),
    ('leiste-text', 'Leiste Schrift', ('#D6E0DA', 'Nebel'), ('#D6E0DA', 'Nebel'), 'Menüpunkte und Icons in der Leiste'),
    ('leiste-leise', 'Leiste leise', ('#9BA6A0', 'Salbei'), ('#9BA6A0', 'Salbei'), 'Gruppentitel, Tastenkürzel in der Leiste'),
    ('leiste-feld', 'Leiste Feld', ('#1F2B26', 'Tanne Feld'), ('#1F2B26', 'Tanne Feld'), 'Suchfeld in der Leiste'),
    ('leiste-hover', 'Leiste Hover', ('#213129', 'Tanne hell'), ('#213129', 'Tanne hell'), 'Menüpunkt unter Maus oder Finger'),
    ('leiste-linie', 'Leiste Linie', ('#2A3C33', 'Tanne Linie'), ('#2A3C33', 'Tanne Linie'), 'Rand des Suchfelds, Trennlinie zum Inhalt'),
    ('leiste-aktiv', 'Leiste aktiv', ('#5EB130', 'Markengrün'), ('#5EB130', 'Markengrün'), 'Aktiver Menüpunkt: volle Fläche, kein Balken'),
    ('leiste-aktiv-text', 'Leiste aktiv Schrift', ('#1E1C19', 'Tinte'), ('#1E1C19', 'Tinte'), 'Schrift auf dem aktiven Punkt, fett'),
    ('leiste-fokus', 'Leiste Fokus', ('#5EB130', 'Markengrün'), ('#5EB130', 'Markengrün'), 'Fokusring in der Leiste'),
    ('feld', 'Feld', ('#FFFFFF', 'Weiß'), ('#13201A', 'Tannenschwarz'), 'Hintergrund von Eingabefeldern'),
    ('feld-rand', 'Feld-Rand', ('#948D81', 'Kiesel'), ('#606E67', 'Flechte'), 'Rand von Eingabefeldern, Checkbox, Radio, Schalter aus'),
    ('feld-aus', 'Feld deaktiviert', ('#FAF2E4', 'Creme'), ('#213129', 'Tanne hell'), 'Deaktivierte Felder'),
]
# In beiden Modi gleich: (Token, HEX, Name, Wofür)
KONSTANT = [
    ('marke', '#5EB130', 'Markengrün', 'Logo, Balken, Deko-Icons, Flächen. Schrift darauf Tinte'),
    ('tinte', '#1E1C19', 'Tinte', 'Schrift auf Markengrün, Gelb, Orange, auch im Dunkelmodus'),
    ('kreide', '#EDE8DE', 'Kreide', 'Schrift auf Grün 800/900, auch im Hellmodus'),
    ('gruen-800', '#325725', 'Grün 800', 'Markenflächen: Kopf, Fuß, Schilder'),
    ('gruen-900', '#1B3714', 'Grün 900', 'Dunkle Markenflächen, dunkle Posts'),
    ('matte-linie', '#49693D', 'Mattenlinie', 'Rasterlinie der Schneidematte auf Grün 800 (1 px, alle 34 px)'),
    ('matte-skala', '#98AB92', 'Mattenskala', 'Lineal-Striche am Rand der Schneidematte. Nicht für Schrift'),
    ('violett', '#6D3E91', 'MINT-Violett', 'Große Flächen mit weißer Schrift'),
    ('gelb', '#FCBD30', 'Mitglieder-Gelb', 'Mitglieder-Fahne, Schrift darauf Tinte'),
    ('orange', '#F2711C', 'Maker-Orange', 'Sticker, Events, Schrift darauf Tinte'),
    ('rot', '#C62828', 'Sicherheitsrot', 'Warnflächen mit weißer Schrift'),
]
NEU = {'Tannennacht', 'Tannenschwarz', 'Tanne hell', 'Tanne Linie', 'Tanne Feld', 'Salbei', 'Nebel', 'Kreide',
       'MINT-Fond dunkel', 'Violett hell', 'Rot hell', 'Gelb-Fond', 'Gelb-Fond dunkel', 'Ocker', 'Rot-Fond', 'Rot-Fond dunkel', 'Kiesel', 'Flechte',
       'Rastergrün', 'Tanne Raster', 'Mattenlinie', 'Mattenskala'}
# Rolle -> (Flächen, Mindestkontrast). Schrift braucht 4,5:1, Fokus 3:1 (WCAG 1.4.3 / 1.4.11).
# Gilt für beide Modi; der Build bricht ab, wenn eine Paarung durchfällt.
MODI_PRUEFEN = {
    'text': (['hintergrund', 'raster', 'flaeche', 'fond', 'fond-gruen', 'fond-gelb', 'fond-rot', 'fond-mint', 'feld'], 4.5),
    'text-leise': (['hintergrund', 'raster', 'flaeche', 'fond', 'fond-gruen', 'fond-mint', 'feld'], 4.5),
    'feld-rand': (['hintergrund', 'flaeche', 'feld'], 3),
    'text-gruen': (['hintergrund', 'raster', 'flaeche', 'fond', 'fond-gruen'], 4.5),
    'button-text': (['button', 'button-hover'], 4.5),
    'text-gelb': (['hintergrund', 'flaeche', 'fond-gelb'], 4.5),
    'text-rot': (['hintergrund', 'flaeche', 'fond', 'fond-rot'], 4.5),
    'text-violett': (['hintergrund', 'flaeche', 'fond-mint'], 4.5),
    'text-blau': (['hintergrund', 'flaeche', 'fond-mint'], 4.5),
    'fokus': (['hintergrund', 'flaeche', 'fond', 'fond-gruen', 'feld'], 3),
    'leiste-text': (['leiste', 'leiste-hover', 'leiste-feld'], 4.5),
    'leiste-leise': (['leiste', 'leiste-feld'], 4.5),
    'leiste-aktiv-text': (['leiste-aktiv'], 4.5),
    'leiste-fokus': (['leiste'], 3),
}
# Feste Paarungen (Schrift, Fläche, Minimum): Token oder HEX
KONSTANT_PRUEFEN = [
    ('kreide', 'gruen-900', 4.5), ('kreide', 'gruen-800', 4.5), ('kreide', 'matte-linie', 4.5),
    ('tinte', 'marke', 4.5), ('tinte', 'gelb', 4.5), ('tinte', 'orange', 4.5),
    ('#FFFFFF', 'violett', 4.5), ('#FFFFFF', 'rot', 4.5), ('marke', 'gruen-900', 3),
]

# Deko darf nicht auffallen: (Linie, Fläche, Höchstkontrast). Gilt in beiden Modi, damit das Raster
# im Dunkeln genauso ruhig wirkt wie im Hellen (Homepage: Markengrün 10 % über Papier = 1,09:1).
MODI_LEISE = [('raster', 'hintergrund', 1.10)]
# Raster- und Mattenmaß in px, wie auf der Homepage
RASTER_PX, MATTE_PX = 27, 34


def modi_werte(i):
    w = {tok: farben[i][0] for tok, _, *farben, _ in MODI}
    w.update({tok: wert for tok, wert, _, _ in KONSTANT})
    return w


def modi_namen(i):
    return {tok: farben[i][1] for tok, _, *farben, _ in MODI}


def modi_kontrast():
    """Kleinster Kontrast je geprüfter Rolle und Modus; Abbruch, wenn eine Paarung unter ihrem Minimum liegt."""
    out, fehler = {}, []
    for i, modus in ((0, 'hell'), (1, 'dunkel')):
        w = modi_werte(i)
        for tok, (flaechen, minimum) in MODI_PRUEFEN.items():
            werte = [(ratio(w[tok], w[f]), f) for f in flaechen]
            out[tok, i] = min(werte)[0]
            fehler += [f'{tok} auf {f} ({modus}): {v:.2f}:1 < {minimum}' for v, f in werte if v < minimum]
        for linie, flaeche, maximum in MODI_LEISE:
            v = ratio(w[linie], w[flaeche])
            out[linie, i] = v
            if v > maximum:
                fehler.append(f'{linie} auf {flaeche} ({modus}): {v:.2f}:1 > {maximum}, zu auffällig')
    w = modi_werte(0)
    for vorn, hinten, minimum in KONSTANT_PRUEFEN:
        v = ratio(w.get(vorn, vorn), w[hinten])
        if v < minimum:
            fehler.append(f'{vorn} auf {hinten}: {v:.2f}:1 < {minimum}')
    if fehler:
        raise SystemExit('Hell/Dunkel-Palette zu kontrastarm: ' + '; '.join(fehler))
    return out


def chip(hexwert, name, neu=False):
    tag = ' <span class="chg new" style="margin-left:4px">Neu</span>' if neu else ''
    return (f'<span class="m-chip" style="background:{hexwert}"></span>'
            f'<span class="mono">{hexwert}</span><br><span class="small">{name}</span>{tag}')


def modi_tabelle():
    k = modi_kontrast()
    zahl = lambda v: f'{v:.1f}'.replace('.', ',')
    rows = ['<table class="t modi-t"><tr><th>Rolle · Token</th><th>Hell</th><th>Dunkel</th>'
            '<th>Kontrast min.<br>hell · dunkel</th><th>Wofür</th></tr>']
    for tok, rolle, (hh, hn), (dh, dn), wofuer in MODI:
        kontrast = f'{zahl(k[tok, 0])} · {zahl(k[tok, 1])}' if (tok, 0) in k else '–'
        leise = {linie: maximum for linie, _, maximum in MODI_LEISE}
        if tok in leise:
            z2 = lambda v: f'{v:.2f}'.replace('.', ',')
            kontrast = f'{z2(k[tok, 0])} · {z2(k[tok, 1])}<br><span class="small">Deko, höchstens {z2(leise[tok])}</span>'
        rows.append(f'<tr><td><b>{rolle}</b><br><code>--{tok}</code></td><td>{chip(hh, hn, hn in NEU)}</td>'
                    f'<td>{chip(dh, dn, dn in NEU)}</td><td>{kontrast}</td><td>{wofuer}</td></tr>')
    rows.append('<tr><th colspan="5">In beiden Modi gleich</th></tr>')
    for tok, wert, name, wofuer in KONSTANT:
        rows.append(f'<tr><td><b>{name}</b><br><code>--{tok}</code></td><td colspan="2">{chip(wert, "hell und dunkel")}</td>'
                    f'<td>–</td><td>{wofuer}</td></tr>')
    rows.append('</table>')
    return '\n'.join(rows)


# ---- Code zum Kopieren (roh; wird beim Einsetzen HTML-maskiert) ----
def css_block(paare, einzug):
    return '\n'.join(f'{einzug}--{tok}: {wert};  /* {name} */' for tok, wert, name in paare)


def modi_css():
    konst = [(tok, wert, name) for tok, wert, name, _ in KONSTANT]
    hell = [(tok, farben[0][0], farben[0][1]) for tok, _, *farben, _ in MODI]
    dunkel = [(tok, farben[1][0], farben[1][1]) for tok, _, *farben, _ in MODI]
    return f'''/* MakerSpace Bonn · Farben hell/dunkel · Styleguide 2026-11 */

/* In beiden Modi gleich */
:root {{
{css_block(konst, '  ')}
}}

/* Hell (Standard) */
:root {{
  color-scheme: light;
{css_block(hell, '  ')}
}}

/* Dunkel: folgt dem System, außer data-theme="light" erzwingt Hell */
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
{css_block(dunkel, '    ')}
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
{css_block(dunkel, '  ')}
}}

/* Anwenden */
body {{ background: var(--hintergrund); color: var(--text); }}
a {{ color: var(--text-gruen); text-decoration: underline; }}
:focus-visible {{ outline: 3px solid var(--fokus); outline-offset: 2px; }}

/* Raster (optional): Millimeterpapier nur auf Ebene 0, z. B. <body class="raster">.
   Karten und Flächen darüber bleiben einfarbig. Nicht in Anwendungen. */
.raster {{
  background-color: var(--hintergrund);
  background-image: linear-gradient(var(--raster) 1px, transparent 1px),
                    linear-gradient(90deg, var(--raster) 1px, transparent 1px);
  background-size: {RASTER_PX}px {RASTER_PX}px;
}}

/* Schneidematte: Markenfläche für Hero und Kopf, in beiden Modi gleich. Schrift Kreide. */
.schneidematte {{
  background-color: var(--gruen-800);
  background-image: linear-gradient(var(--matte-linie) 1px, transparent 1px),
                    linear-gradient(90deg, var(--matte-linie) 1px, transparent 1px);
  background-size: {MATTE_PX}px {MATTE_PX}px;
  color: var(--kreide);
}}

/* Logo tauschen: <img class="logo-hell" …> und <img class="logo-dunkel" …> */
.logo-dunkel {{ display: none; }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) .logo-hell {{ display: none; }}
  :root:not([data-theme="light"]) .logo-dunkel {{ display: block; }}
}}
:root[data-theme="dark"] .logo-hell {{ display: none; }}
:root[data-theme="dark"] .logo-dunkel {{ display: block; }}'''


def modi_meta():
    return (f'<meta name="theme-color" content="{MODI[0][2][0]}" media="(prefers-color-scheme: light)">\n'
            f'<meta name="theme-color" content="{MODI[0][3][0]}" media="(prefers-color-scheme: dark)">')


MODI_UMSCHALTER = '''<!-- 1. Im <head>, vor dem CSS: gemerkte Wahl sofort setzen, sonst blitzt die Seite hell auf -->
<script>try{var m=localStorage.getItem('darstellung');if(m==='light'||m==='dark')document.documentElement.dataset.theme=m}catch(e){}</script>

<!-- 2. Der Knopf: drei Icons, z. B. Lucide "contrast", "sun", "moon" -->
<button type="button" class="modus-schalter" data-modus="auto" aria-label="Darstellung: Auto (wie Gerät)">
  <svg class="i-auto">…</svg><svg class="i-light">…</svg><svg class="i-dark">…</svg>
</button>

/* 3. CSS: nur das Icon für den aktuellen Zustand zeigen */
.modus-schalter { width: 44px; height: 44px; display: grid; place-items: center;
  border: 0; border-radius: 8px; background: none; color: var(--text); }
.modus-schalter:hover { background: var(--fond); }
.modus-schalter svg { display: none; width: 20px; height: 20px; }
.modus-schalter[data-modus="auto"] .i-auto,
.modus-schalter[data-modus="light"] .i-light,
.modus-schalter[data-modus="dark"] .i-dark { display: block; }

// 4. JS: jeder Klick schaltet weiter, Auto → Hell → Dunkel → Auto
const MODI = ['auto', 'light', 'dark'];
const NAME = { auto: 'Auto (wie Gerät)', light: 'Hell', dark: 'Dunkel' };
const knopf = document.querySelector('.modus-schalter');
function setze(m) {
  if (m === 'auto') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = m;
  knopf.dataset.modus = m;
  knopf.title = `Darstellung: ${NAME[m]}`;
  knopf.setAttribute('aria-label', knopf.title);
  try { localStorage.setItem('darstellung', m); } catch {}
}
knopf.addEventListener('click', () => setze(MODI[(MODI.indexOf(knopf.dataset.modus) + 1) % 3]));
let gemerkt = 'auto';
try { gemerkt = localStorage.getItem('darstellung') ?? 'auto'; } catch {}
setze(MODI.includes(gemerkt) ? gemerkt : 'auto');'''

MODI_SHADCN = '''/* shadcn/ui, z. B. Vereinssoftware: nach den Farben oben einfügen.
   Gilt für beide Modi, weil jede Zeile auf eine Rolle zeigt. */
:root {
  --background: var(--hintergrund);
  --foreground: var(--text);
  --card: var(--flaeche);
  --card-foreground: var(--text);
  --popover: var(--flaeche);
  --popover-foreground: var(--text);
  --primary: var(--button);
  --primary-foreground: var(--button-text);
  --secondary: var(--fond);
  --secondary-foreground: var(--text);
  --muted: var(--fond);
  --muted-foreground: var(--text-leise);
  --accent: var(--fond);
  --accent-foreground: var(--text);
  --destructive: var(--text-rot);
  --border: var(--linie);
  --input: var(--feld-rand);
  --ring: var(--fokus);
  --sidebar: var(--leiste);
  --sidebar-foreground: var(--leiste-text);
  --sidebar-primary: var(--leiste-aktiv);
  --sidebar-primary-foreground: var(--leiste-aktiv-text);
  --sidebar-accent: var(--leiste-hover);
  --sidebar-accent-foreground: var(--leiste-text);
  --sidebar-border: var(--leiste-linie);
  --sidebar-ring: var(--leiste-fokus);
  /* Status-Pills der Vereinssoftware */
  --success: var(--text-gruen);
  --success-strong: var(--text-gruen);
  --success-surface: var(--fond-gruen);
  --warning: var(--text-gelb);
  --warning-surface: var(--fond-gelb);
}'''


# ---- Vorschauen: gleiches HTML, nur die Tokens wechseln ----
LOGO = ('logo-h-ohne-claim-farbe', 'logo-h-ohne-claim-negativ')
MODUS = ('Hell', 'Dunkel')
ICON = {
    'suche': '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    'haus': '<path d="M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z"/>',
    'leute': '<circle cx="9" cy="8" r="4"/><path d="M2 21c0-4 3-6 7-6s7 2 7 6M16 4a4 4 0 0 1 0 8M22 21c0-3-1.5-5-4-5.6"/>',
    'geld': '<rect x="2" y="6" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/>',
    'regler': '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>',
    'menue': '<path d="M4 6h16M4 12h16M4 18h16"/>',
    'auto': '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/>',
    'hell': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    'dunkel': '<path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a6.5 6.5 0 0 0 11 11z"/>',
    'fehler': '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.5v.01"/>',
    'schloss': '<rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    'runter': '<path d="m6 9 6 6 6-6"/>',
}


def icon(name, klasse=''):
    k = f' class="{klasse}"' if klasse else ''
    return f'<svg viewBox="0 0 24 24" aria-hidden="true"{k}>{ICON[name]}</svg>'


def paar(inhalt, klasse=''):
    return ''.join(f'<div class="modus {MODUS[i].lower()} {klasse}" style="{";".join(f"--{t}:{v}" for t, v in modi_werte(i).items())}">'
                   f'<span class="m-modus mono">{MODUS[i]}</span>{inhalt(i)}</div>' for i in (0, 1))


def vorschau_inhalt(i):
    return '''<div class="tape" style="height:8px"></div>
      <div class="m-body">
        <span class="m-sticker">Heute<br>offen!</span>
        <span class="label m-label">Repair Café</span>
        <div class="m-h">Kaputt? Wir reparieren das zusammen.</div>
        <p>Bring mit, was nicht mehr geht. Werkzeug und Leute mit Erfahrung sind da. <a href="#modi">Termine im Wiki</a></p>
        <p class="m-leise">Montag ab 18 Uhr · Kennedyallee 18</p>
        <div class="m-karte"><span class="m-tag-gruen">Anfänger:innen</span><span class="m-button">→ Anmelden</span></div>
        <div class="m-fond"><b>Gut zu wissen:</b> Laser und CNC nur nach Einweisung.<br><span class="m-rot">Schutzbrille tragen.</span></div>
      </div>'''


def vorschau_ebenen(i):
    n = modi_namen(i)
    return f'''<div class="m-ebene0"><span class="m-eb">0 · Hintergrund · {n['hintergrund']}</span>
        <div class="m-ebene1"><span class="m-eb">1 · Fläche · {n['flaeche']} · Linie · {n['linie']}</span>
          <div class="m-ebene2"><span class="m-eb">2 · Fond · {n['fond']}</span></div>
        </div>
      </div>'''


def vorschau_raster(i):
    n = modi_namen(i)
    return f'''<div class="m-raster">
        <span class="m-eb m-raster-eb">0 · Hintergrund · {n['hintergrund']} + Raster · {n['raster']} · {RASTER_PX} px</span>
        <div class="m-karte m-raster-karte">
          <div><b>Offene Werkstatt</b><br><span class="m-leise">Donnerstag 18–21 Uhr · Kennedyallee 18</span></div>
          <span class="m-button">Vorbeikommen</span>
        </div>
        <span class="m-eb m-raster-eb">1 · Fläche liegt einfarbig auf dem Raster</span>
      </div>'''


def vorschau_matte(i):
    return f'''<div class="m-raster m-raster-matte">
        <div class="m-matte">
          <div class="m-skala m-skala-oben"></div><div class="m-skala m-skala-links"></div>
          <div class="m-matte-inhalt">
            <div class="m-matte-h">Bau, was du dir vorstellst.</div>
            <p>Löten, fräsen, nähen, 3D-drucken: sechs Werkstätten und Leute, die mit anpacken.</p>
            <span class="m-matte-button">Offene Tür besuchen</span>
          </div>
        </div>
        <span class="m-eb m-raster-eb">Schneidematte · Grün 800 + Mattenlinie · {MATTE_PX} px · gleich in beiden Modi</span>
      </div>'''


def vorschau_app(i):
    def punkt(ic, text, extra='', aktiv=False):
        return (f'<span class="app-punkt{" aktiv" if aktiv else ""}">{icon(ic)}<span class="app-l">{text}</span>{extra}</span>')

    def zeile(nr, name, status, beitrag, zustand=''):
        return (f'<tr class="{zustand}"><td class="app-opt app-num">{nr}</td><td>{name}</td><td>{status}</td>'
                f'<td class="app-opt app-zahl">{beitrag}</td></tr>')

    def pill(art, text):
        return f'<span class="app-pill {art}"><i aria-hidden="true"></i>{text}</span>'

    modus = ('light', 'dark')[i]
    return f'''<div class="app">
        <aside class="app-seite">
          <img src="{{{{{LOGO[1]}}}}}" alt="" class="app-logo">
          <span class="app-burger">{icon('menue')}</span>
          <span class="app-suche">{icon('suche')}<span class="app-l">Suchen</span><kbd class="app-l">⌘K</kbd></span>
          <span class="app-gruppe">Verwaltung</span>
          {punkt('haus', 'Start')}
          {punkt('leute', 'Mitglieder', aktiv=True)}
          {punkt('geld', 'Beiträge', '<span class="app-zahlmarke">3</span>')}
          {punkt('regler', 'Einstellungen')}
        </aside>
        <div class="app-haupt">
          <div class="app-kopf">
            <span class="app-pfad">Mitglieder <span aria-hidden="true">›</span> Übersicht</span>
            <button type="button" class="app-schalter" data-modus="{modus}" aria-label="Darstellung: {MODUS[i]}" title="Darstellung: {MODUS[i]}">{icon('auto', 'i-auto')}{icon('hell', 'i-light')}{icon('dunkel', 'i-dark')}</button>
            <span class="app-profil" aria-hidden="true">AB</span>
          </div>
          <div class="app-inhalt">
            <div class="app-titel"><span class="app-h">Mitglieder</span>
              <span class="app-knoepfe"><span class="app-btn zweit">Export</span><span class="app-btn haupt">+ Mitglied</span></span></div>
            <div class="m-feld">{icon('suche')}<span>Name oder Nummer</span></div>
            <div class="app-tabelle-rahmen"><table class="app-tabelle">
              <tr><th class="app-opt">Nr.</th><th>Name</th><th>Status</th><th class="app-opt app-zahl">Beitrag</th></tr>
              {zeile('2001', 'Alex Beispiel', pill('ok', 'Aktiv'), '20,00 €')}
              {zeile('2002', 'Kim Muster', pill('achtung', 'Ruhend'), '0,00 €', 'hover')}
              {zeile('2003', 'Sam Probe', pill('problem', 'Lastschrift offen'), '20,00 €', 'gewaehlt')}
              {zeile('2004', 'Robin Test', pill('neutral', 'Ausgetreten'), '–')}
            </table></div>
          </div>
        </div>
      </div>'''


def vorschau_formular(i):
    """Formular „Mitglied anlegen“: gleiches HTML in beiden Modi, IDs je Modus eindeutig (paar() rendert zweimal)."""
    p = f'fm{i}'
    stern = '<span class="fm-stern" aria-hidden="true">*</span>'

    def feld(name, label, wert='', *, typ='text', ph='', pflicht=False, zustand='', fehler='', hilfe='',
             aus=False, ro=False, optionen=()):
        fid = f'{p}-{name}'
        attr = [f'id="{fid}"']
        attr += ['required'] if pflicht else []
        attr += ['disabled'] if aus else []
        attr += ['readonly'] if ro else []
        unten, besch, ic = '', [], ''
        if fehler:
            attr.append('aria-invalid="true"')
            besch.append(f'{fid}-f')
            unten += f'<p class="fm-meldung" id="{fid}-f">{icon("fehler")}<span>{fehler}</span></p>'
            ic = icon('fehler', 'fm-ico')
        elif ro:
            ic = icon('schloss', 'fm-ico')
        if hilfe:
            besch.append(f'{fid}-h')
            unten += f'<p class="fm-hilfe" id="{fid}-h">{hilfe}</p>'
        if besch:
            attr.append(f'aria-describedby="{" ".join(besch)}"')
        a = ' '.join(attr)
        if typ == 'select':
            opts = ''.join(f'<option{" selected" if o == wert else ""}>{o}</option>' for o in optionen)
            ctl, ic = f'<select class="fm-in" {a}>{opts}</select>', icon('runter', 'fm-ico')
        else:
            ph_attr = f' placeholder="{ph}"' if ph else ''
            ctl = f'<input class="fm-in" type="{typ}" {a} value="{wert}"{ph_attr}>'
        k = ' '.join(x for x in ['fm-feld', zustand, 'fm-fehler' if fehler else '', 'fm-aus' if aus else '',
                                  'fm-ro' if ro else ''] if x)
        return (f'<div class="{k}"><label class="fm-label" for="{fid}">{label}{stern if pflicht else ""}</label>'
                f'<div class="fm-ctl{" fm-ico-r" if ic else ""}">{ctl}{ic}</div>{unten}</div>')

    def wahl(name, text, art, an=False, wert='x'):
        typ = 'radio' if art == 'radio' else 'checkbox'
        rolle = ' role="switch"' if art == 'switch' else ''
        return (f'<label class="fm-wahl" for="{p}-{name}-{wert}"><input type="{typ}" class="fm-{art}" id="{p}-{name}-{wert}" '
                f'name="{p}-{name}" value="{wert}"{rolle}{" checked" if an else ""}><span>{text}</span></label>')

    arten = ('Ordentlich · 20 € im Monat', 'Ermäßigt · 10 € im Monat', 'Fördermitglied · ab 5 € im Monat')
    zustaende = ''.join([
        feld('z-leer', 'Leer', ph='z. B. 53175'),
        feld('z-voll', 'Ausgefüllt', '53175'),
        feld('z-hover', 'Hover', '53175', zustand='fm-hover'),
        feld('z-fokus', 'Fokus', '53175', zustand='fm-fokus'),
        feld('z-fehler', 'Fehler', '5317', fehler='5 Ziffern nötig.'),
        feld('z-aus', 'Deaktiviert', '53175', aus=True, hilfe='Nur der Vorstand.'),
        feld('z-ro', 'Schreibgeschützt', '53175', ro=True),
    ])
    return f'''<div class="fm-body">
        <form class="fm-karte" novalidate onsubmit="return false" aria-labelledby="{p}-titel">
          <div class="fm-kopf"><span class="fm-h" id="{p}-titel">Mitglied anlegen</span><span class="fm-legende">{stern} Pflichtfeld</span></div>
          <div class="fm-reihe">
            {feld('name', 'Name', 'Alex Beispiel', pflicht=True, zustand='fm-hover')}
            {feld('mail', 'E-Mail', 'alex.beispiel', typ='email', pflicht=True, fehler='Die E-Mail braucht ein @, z. B. alex@beispiel.de')}
          </div>
          <div class="fm-reihe">
            {feld('art', 'Mitgliedsart', arten[0], typ='select', pflicht=True, optionen=arten, hilfe='Ermäßigt mit Nachweis.')}
            {feld('eintritt', 'Eintritt am', '2026-12-01', typ='date', pflicht=True, zustand='fm-fokus')}
          </div>
          <div class="fm-reihe">
            {feld('nr', 'Mitgliedsnummer', '2005', ro=True, hilfe='Wird beim Anlegen vergeben.')}
            <fieldset class="fm-gruppe"><legend class="fm-label">Beitrag per{stern}</legend><div class="fm-wahlen">
              {wahl('zahlung', 'Lastschrift', 'radio', True, 'ls')}{wahl('zahlung', 'Überweisung', 'radio', wert='ue')}</div></fieldset>
          </div>
          <div class="fm-wahlen">
            {wahl('news', 'Newsletter per E-Mail', 'switch', True)}
            {wahl('satzung', f'Satzung gelesen{stern}', 'check', True)}
          </div>
          <div class="fm-knoepfe"><button type="submit" class="fm-btn haupt">Mitglied anlegen</button><button type="button" class="fm-btn zweit">Abbrechen</button></div>
        </form>
        <span class="fm-zt">Ein Feld in allen Zuständen</span>
        <div class="fm-zgrid">{zustaende}</div>
      </div>'''


def vorschau_mint(i):
    return '''<div class="m-body m-mint-body">
        <div class="m-mint"><span class="m-violett">MINT</span> Löten für Kinder ab 10 · <a href="#modi" class="m-blau">mehr Infos</a></div>
        <div class="m-violett-flaeche">MINT-Violett als Fläche bleibt gleich</div>
      </div>'''


# ---- Versionen: jede Änderung am Dokument bekommt Nummer und Zeit ----
VERSIONEN = ROOT / 'src' / 'versionen.json'
BERLIN = ZoneInfo('Europe/Berlin')
# Alles, woraus index.html entsteht. versionen.json selbst zählt nicht, sonst ändert jeder Eintrag den Abdruck.
EINGABEN = ('src/template.html', 'src/build.py', 'logos/*.png')


def fingerabdruck(root=ROOT):
    h = hashlib.sha256()
    for muster in EINGABEN:
        for datei in sorted(root.glob(muster)):
            h.update(str(datei.relative_to(root)).encode() + b'\0' + datei.read_bytes() + b'\0')
    return h.hexdigest()[:12]


def naechste_nummer(versionen, jetzt):
    """Jahr-Monat.laufende Nummer, im Monat von `jetzt` (Europe/Berlin)."""
    monat = jetzt.astimezone(BERLIN).strftime('%Y-%m')
    nummern = [int(v['version'].split('.')[1]) for v in versionen if v['version'].startswith(monat + '.')]
    return f'{monat}.{max(nummern, default=0) + 1}'


def mit_version(versionen, was, jetzt, abdruck, im_commit):
    """Neue Version vorn eintragen. Ist die neueste noch nicht committet, wird sie stattdessen aktualisiert,
    damit ein Commit genau eine Version bekommt. `im_commit`: Versionsnummern, die schon in HEAD stehen."""
    zeit = jetzt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    neueste = versionen[0] if versionen else None
    if neueste and neueste.get('fingerabdruck') and neueste['version'] not in im_commit:
        return [{**neueste, 'zeit': zeit, 'was': was or neueste['was'], 'fingerabdruck': abdruck}] + versionen[1:]
    if not was:
        raise SystemExit('Neue Version braucht eine Beschreibung: --version "Was sich geändert hat"')
    return [{'version': naechste_nummer(versionen, jetzt), 'zeit': zeit, 'was': was, 'fingerabdruck': abdruck}] + versionen


def versionen_im_commit():
    """Versionsnummern in HEAD:src/versionen.json; leer, wenn es die Datei dort (noch) nicht gibt."""
    try:
        r = subprocess.run(['git', 'show', 'HEAD:src/versionen.json'], cwd=ROOT, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return set()
    return {v['version'] for v in json.loads(r.stdout)} if r.returncode == 0 else set()


def lade_versionen():
    versionen = json.loads(VERSIONEN.read_text())
    if not versionen or not all({'version', 'zeit', 'was'} <= v.keys() for v in versionen):
        raise SystemExit(f'{VERSIONEN.name}: jeder Eintrag braucht version, zeit und was')
    return versionen


def speichere_versionen(versionen):
    tmp = VERSIONEN.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(versionen, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(VERSIONEN)


def stand(eintrag):
    """'20.11.2026, 19:55 Uhr' in Berliner Zeit; Einträge ohne Uhrzeit nur mit Datum."""
    z = eintrag['zeit']
    if 'T' not in z:
        return datetime.strptime(z, '%Y-%m-%d').strftime('%d.%m.%Y')
    return datetime.strptime(z, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).astimezone(BERLIN).strftime('%d.%m.%Y, %H:%M Uhr')


def protokoll(versionen):
    rows = ['<table class="t"><tr><th>Version</th><th>Stand</th><th>Was</th></tr>']
    rows += [f'<tr><td class="mono" style="white-space:nowrap">{escape(v["version"])}</td>'
             f'<td style="white-space:nowrap">{stand(v)}</td><td>{escape(v["was"])}</td></tr>' for v in versionen]
    return '\n'.join(rows + ['</table>'])


def render(versionen):
    html = (ROOT / 'src' / 'template.html').read_text().replace('{{matrix}}', matrix())
    aktuell = versionen[0]
    for platzhalter, wert in {
        'modi_tabelle': modi_tabelle(),
        'modi_css': escape(modi_css(), quote=False), 'modi_meta': escape(modi_meta(), quote=False),
        'modi_umschalter': escape(MODI_UMSCHALTER, quote=False), 'modi_shadcn': escape(MODI_SHADCN, quote=False),
        'vorschau_inhalt': paar(vorschau_inhalt), 'vorschau_ebenen': paar(vorschau_ebenen),
        'vorschau_raster': paar(vorschau_raster), 'vorschau_matte': paar(vorschau_matte),
        'vorschau_app': paar(vorschau_app, 'app-modus'), 'vorschau_formular': paar(vorschau_formular, 'fm-modus'), 'vorschau_mint': paar(vorschau_mint, 'kompakt'),
        'version': escape(aktuell['version']), 'stand': stand(aktuell), 'stand_datum': stand(aktuell).split(',')[0],
        'protokoll': protokoll(versionen),
    }.items():
        html = html.replace('{{' + platzhalter + '}}', wert)
    for p in (ROOT / 'logos').glob('*.png'):
        html = html.replace('{{' + p.stem + '}}', 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode())
    missing = [line.strip() for line in html.splitlines() if '{{' in line]
    if missing:
        raise SystemExit(f'Unresolved placeholders: {missing[:3]}')
    return html


def main(argv=None):
    ap = argparse.ArgumentParser(description='Baut index.html aus src/template.html.')
    ap.add_argument('--version', metavar='WAS', nargs='?', const='',
                    help='Version mit aktueller Zeit eintragen (offene, noch nicht committete Version wird aktualisiert)')
    ap.add_argument('--pruefen', action='store_true', help='nichts schreiben, nur prüfen (Pre-Commit-Hook)')
    args = ap.parse_args(argv)
    versionen, abdruck = lade_versionen(), fingerabdruck()
    if args.version is not None:
        versionen = mit_version(versionen, args.version, datetime.now(timezone.utc), abdruck, versionen_im_commit())
        speichere_versionen(versionen)
        print(f'Version {versionen[0]["version"]} · {stand(versionen[0])}')
    html = render(versionen)
    ohne_version = versionen[0].get('fingerabdruck') != abdruck
    if args.pruefen:
        fehler = []
        if ohne_version:
            fehler.append('Änderung ohne Versionseintrag: python3 src/build.py --version "Was sich geändert hat"')
        if (ROOT / 'index.html').read_text() != html:
            fehler.append('index.html ist nicht aktuell: python3 src/build.py')
        if fehler:
            raise SystemExit('\n'.join(fehler))
        print(f'ok: Version {versionen[0]["version"]}, index.html aktuell')
        return
    tmp = ROOT / 'index.html.tmp'
    tmp.write_text(html)
    tmp.replace(ROOT / 'index.html')
    print(f'index.html written ({len(html) // 1024} KB) · Version {versionen[0]["version"]}')
    if ohne_version:
        print('Hinweis: Änderung noch ohne Versionseintrag. Vor dem Commit: python3 src/build.py --version "Was sich geändert hat"')


if __name__ == '__main__':
    main()
