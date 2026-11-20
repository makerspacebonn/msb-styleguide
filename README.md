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
| `src/build.py` | Baut `index.html` (Logos einbetten, Kontrasttabelle berechnen, Hell/Dunkel-Palette erzeugen und prüfen; bricht ab, wenn eine Farbrolle unter den WCAG-Kontrast fällt) |
| `src/extract_logos.py` | Schneidet die Logo-PNGs aus dem Original-PDF |
| `src/versionen.json` | Versionen mit Datum, Uhrzeit und Beschreibung (Quelle für Titel, Navigation, Fuß und Änderungsprotokoll) |
| `src/test_build.py` | Tests für die Versionslogik |
| `.githooks/pre-commit` | Prüft vor jedem Commit: Tests, Kontraste, Versionseintrag, `index.html` aktuell |

## Ändern

1. `src/template.html` bearbeiten.
2. `python3 src/build.py` ausführen.
3. Vor dem Commit die Version eintragen: `python3 src/build.py --version "Was sich geändert hat"`. Das legt eine neue Version an (Jahr-Monat.Nummer, z. B. 2026-11.7) mit Datum und Uhrzeit. Wer danach noch etwas ändert, ruft es vor dem Commit einfach noch einmal auf: Dann wird die offene Version aktualisiert, keine neue angelegt.
4. Optional PDF neu erzeugen: `index.html` im Browser öffnen → Drucken → Als PDF sichern (Schalter vorher nach Wunsch setzen).

Einmalig pro Klon: `git config core.hooksPath .githooks`. Dann verweigert Git den Commit, wenn eine Änderung keine Version hat oder `index.html` nicht neu gebaut ist.

Die Logo-PNGs sind aus dem PDF gerastert. Für den Druck die Vektor-Originale verwenden.
