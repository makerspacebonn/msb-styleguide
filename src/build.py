"""Build index.html from src/template.html: inlines logos/*.png and the contrast matrix.

Usage: python3 src/build.py
"""
import base64
import pathlib

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


html = (ROOT / 'src' / 'template.html').read_text().replace('{{matrix}}', matrix())
for p in (ROOT / 'logos').glob('*.png'):
    html = html.replace('{{' + p.stem + '}}', 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode())
missing = [line.strip() for line in html.splitlines() if '{{' in line]
if missing:
    raise SystemExit(f'Unresolved placeholders: {missing[:3]}')
tmp = ROOT / 'index.html.tmp'
tmp.write_text(html)
tmp.replace(ROOT / 'index.html')
print(f'index.html written ({len(html) // 1024} KB)')
