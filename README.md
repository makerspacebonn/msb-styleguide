# MakerSpace Bonn Styleguide

Überarbeitungsentwurf (Version 2026-11) des Styleguides des MakerSpace Bonn e.V., auf Basis der Version vom 15.02.2026.

**Online lesen:** https://makerspacebonn.github.io/msb-styleguide/

Oben in der Navigation blendet der Schalter „Änderungen zeigen“ alle Hinweise auf Änderungen gegenüber der Vorversion ein oder aus.

## Inhalt

| Pfad | Was |
|---|---|
| `index.html` | Der Styleguide (gebaut, eigenständig, Logos eingebettet) |
| `styleguide-2026-11-entwurf.pdf` | Druckfassung (A4) |
| `logos/` | Logo horizontal, vertikal, Cube – jeweils Farbe, Negativ, Weiß, Schwarz (PNG) |
| `src/template.html` | Quelle des Styleguides – **hier bearbeiten** |
| `src/build.py` | Baut `index.html` (Logos einbetten, Kontrasttabelle berechnen) |
| `src/extract_logos.py` | Schneidet die Logo-PNGs aus dem Original-PDF |

## Ändern

1. `src/template.html` bearbeiten.
2. `python3 src/build.py` ausführen.
3. Optional PDF neu erzeugen: `index.html` im Browser öffnen → Drucken → Als PDF sichern (Schalter vorher nach Wunsch setzen).

Die Logo-PNGs sind aus dem PDF gerastert. Für den Druck die Vektor-Originale verwenden.
