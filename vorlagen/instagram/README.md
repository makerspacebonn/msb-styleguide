# Instagram-Post-Vorlagen (Entwurf 2026-11)

Vorlagen für Instagram-Posts im Format 1080×1350 px (4:5). 01–10 sind Event-Ankündigungen (Beispiel: Workshop „Lebkuchenhaus bauen“, 28.11.), 11–13 Rückblicke, 14–17 emotionale Posts nur mit Text und Logo (Beispiel: Pop-up-Workshop, 15.11.). Die fertigen Bilder liegen in `png/`.

| Datei | Wofür | Bildstil |
|---|---|---|
| `01-foto-balken` | Standard-Ankündigung, wenn ein gutes Foto da ist | Foto unverändert, unten ein Balken in Grün 800 mit Warnband |
| `03-werkbank` | Workshops und Mitmach-Events | Foto als Abzug mit Klebeband auf Kraftpapier, Handnotiz |
| `04-termin-cube` | „Save the date“, wenn das Datum wichtiger ist als das Bild | Ausschnitt als Sechseck wie der Cube |
| `05-infos-slide` | Folie 2 im Karussell, kombinierbar mit allen anderen | ohne Foto |
| `06-bauplan` | Technische Workshops | Foto mit Bemaßungslinien auf grünem Rasterpapier, Schriftfeld wie in einer Technischen Zeichnung |
| `07-sucher` | Foto-zentriert, technisch | Foto mit Kamerasucher-Overlay (Ecken, Fadenkreuz, oranger Fokusrahmen) |
| `08-anschnitt` | Laut, plakativ | Foto oben, riesiges „bauen.“ vom Fotorand angeschnitten |
| `09-spalte` | Datum im Fokus | Foto 70 % links, grüne Spalte mit Lineal-Kante und großem Datum |
| `10-kante` | Ruhig, markentypisch | Foto mit 30°-Kante wie der Cube, grüne Fläche unten |
| `11-rueckblick-anschnitt` | Rückblick, laut | wie 08, mit Datum des Workshops |
| `12-rueckblick-kante` | Rückblick, ruhig | wie 10 |
| `13-rueckblick-plotter` | Rückblick Plotter/Laser | Foto mit Passermarken wie beim Schneideplotter |
| `14-emo-satz` | Ein Satz, viel Gefühl | Foto vollflächig, dunkler Verlauf unten, weißer Satz |
| `15-emo-streifen` | Kurze Abfolge | Zeilen auf Tinte-Streifen, letzte in Grün 500, Logo auf weißer Fahne |
| `16-emo-rahmen` | Ruhig | Grün-500-Passepartout, kurzer Satz |
| `17-emo-notiz` | Persönlich | Handnotiz mit Pfeil auf dem Foto, Tinte-Leiste mit Logo |

06–10 weichen bewusst stellenweise vom Styleguide ab (z. B. Orange als Fläche, Versalien-Titel). Die Abweichungen stehen jeweils als Kommentar am Anfang der HTML-Datei.

## Feste Regeln für alle Vorlagen
- Außenrand 72 px. Das Profilraster schneidet seitlich etwa 34 px ab.
- Akzent für Events ist **Orange**, als Sticker höchstens einmal pro Post. Für MINT-Posts das Orange durch Violett ersetzen, nicht ergänzen.
- Schrift auf Grün 500 und Orange immer in Tinte, auf Grün 800 und Tinte in Weiß. Grüne Schrift auf Papier/Creme in Grün 600, auf Creme kräftig in Grün 800.
- Labels in IBM Plex Mono, Versalien. Alles andere in IBM Plex Sans.

## In Canva nachbauen
- **Cube-Ausschnitt:** Rahmen „Sechseck“ hochkant, dahinter ein etwas größeres Sechseck in Tinte.
- **Warnband:** Streifen-Element im Winkel −45°, Farben `#5EB130` und `#1B3714`.
- **Handnotiz:** Die Caveat-Schrift ist nur ein Platzhalter. Echte Handschrift einscannen (siehe Styleguide, Kapitel Maker-Elemente).

## Für Canva
- `pdf/14-emo-satz.pdf`, `pdf/15-emo-streifen.pdf`, `pdf/17-emo-notiz.pdf`: in Canva hochladen, sie öffnen sich als bearbeitbares Design.
- `overlays/`: Elemente, die Canva beim Import verliert (Lineal aus 09, Verlauf aus 14), als transparente PNGs.
- Logo auf Social Media: Variante ohne Claim (`logos/logo-h-ohne-claim-*.png`), mindestens 54 px hoch.

## Neu rendern
`./render.sh` braucht Google Chrome und Internet (für die Google Fonts).

## Offen
Das Beispielfoto von der Website sieht KI-generiert aus. Laut Styleguide (Kap. 11) ist das erlaubt, wenn kein echtes Foto da ist, muss dann aber gekennzeichnet werden. Besser: ein Foto vom letzten Workshop.
