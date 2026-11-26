# Dokumente (A4)

Vorlage für Satzung, Ordnungen, Pressemitteilungen und andere offizielle Texte des MakerSpace Bonn e.V.
Eine gemeinsame Druck-CSS (`dokument.css`), eine HTML-Datei pro Dokument, PDFs in `pdf/`.

## PDFs neu bauen

```bash
node vorlagen/dokumente/build-pdfs.mjs              # alle Dokumente
node vorlagen/dokumente/build-pdfs.mjs satzung      # nur eines (Dateiname ohne .html)
```

Braucht Google Chrome unter `/Applications/Google Chrome.app` und Internet (Schriften kommen von Google Fonts).
Das Skript startet Chrome headless (Port 9335), wartet auf `document.fonts.ready`, bricht ab, wenn eine Schrift
oder das Logo fehlt, und druckt per `Page.printToPDF` mit dem Seitenformat aus der CSS.

Kontrolle danach: `pdffonts vorlagen/dokumente/pdf/<name>.pdf` muss Archivo, IBMPlexSans und IBMPlexMono als
CID TrueType zeigen. Taucht `Type 3` auf, hat Chrome variable Schriften bekommen (siehe Kommentar im Skript).

## Neues Dokument anlegen

1. Eine vorhandene HTML-Datei kopieren, z. B. `beitragsordnung.html` → `geschaeftsordnung.html`.
2. Anpassen:
   - `<title>`;
   - die Fußzeile im `<style>`-Block, mit Stand auf der ersten Zeile und Seitenzahl auf der zweiten: `content:"Geschäftsordnung · Stand: Mai 2027\A Seite " counter(page) " von " counter(pages)`;
   - im Kopf: `.art` (Dokumentart, wird in Versalien gesetzt), `<h1>` (Titel), `.stand` („Stand: …“, „Beschlossen am …“, „Bonn, …“).
3. Inhalt mit diesen Bausteinen setzen:
   - `<h2><span class="nr">§3</span> Titel</h2>`: §-Überschrift, Nummer hängt links;
   - `<h2 class="ohne-nr">`: Überschrift ohne Nummer;
   - `<ol class="abs"><li><span class="n">1.</span>…</li></ol>`: nummerierte Absätze mit hängendem Einzug; `(1)` geht genauso;
   - `<ol class="buchst"><li><span class="n">(a)</span>…</li></ol>`: Unterpunkte (a), (b) in einem Absatz;
   - `<ul class="pkt">`: Aufzählung (offener Kreis; verschachtelt: Quadrat; `pkt voll`: gefüllter Punkt);
   - `p.einzug` / `ul.pkt.einzug`: Text ohne Nummer auf der Textachse;
   - `li.kurz`: Absatz nicht über einen Seitenumbruch teilen;
   - Pressemitteilung: `ul.kernpunkte` für die Kernaussagen, `.markiert` für im Original unterstrichene Angaben,
     `div.kontakt` für den Pressekontakt (nur Angaben aus der Vorlage).
4. `<body class="kompakt">`, wenn ein Aushang auf eine Seite passen soll (Fließtext 9,5 pt statt 10,5 pt).
5. Bauen und die PDF ansehen: keine §-Überschrift allein am Seitenende, Fußzeile auf jeder Seite.

## Regeln

- **Wortlaut nicht ändern.** Rechtstexte werden zeichengenau übernommen. Erlaubt ist nur, Export-Müll zu entfernen
  (Null-Breite-Leerzeichen, Trennstriche am Zeilenende, alte Kopf- und Fußzeilen). Automatische Silbentrennung ist aus,
  damit die PDF-Textebene wortgleich bleibt.
- Logo: `logos/logo-h-ohne-claim-farbe.png` (Styleguide §3: Briefe und Verträge, min. 25 mm; hier 52 mm). Nie abtippen.
- Farben und Schriften wie im Styleguide (§5, §9): Text Tinte auf Weiß, Metadaten Stein, eine dünne Linie in Markengrün
  unter dem Kopf. Keine Farbflächen, damit es auch im Schwarz-Weiß-Druck funktioniert.
- Archivo erst ab 18 pt (Titel 30 pt, §-Überschrift 18 pt), Fließtext IBM Plex Sans 9,5–10,5 pt, Labels und Fußzeile IBM Plex Mono.
- Ränder nach DIN 5008: links 25 mm (Lochung/Heftung), rechts 22 mm, oben 18 mm, unten 24 mm inkl. Fußzeile.
