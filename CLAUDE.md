# MakerSpace Bonn Styleguide

Style guide of MakerSpace Bonn e.V. Edit `src/template.html`; `src/build.py` builds the standalone `index.html` (logos inlined, contrast tables, light/dark palette, version history). Details in `README.md`.

## Commands
```bash
python3 src/build.py                          # build index.html
python3 src/build.py --version "Was"          # record version + time in src/versionen.json, then build
python3 -m unittest discover -s src           # tests
git config core.hooksPath .githooks           # once per clone: pre-commit runs the gate
```

## Gate
- Fast check: `python3 -m unittest discover -s src -q`
- Full gate: `python3 src/build.py --pruefen` (contrast check, version entry for the current document, `index.html` up to date)

## Rules
- **Every change to the document gets a version before the commit:** `python3 src/build.py --version "…"` (German text, what changed for readers). Numbering `YYYY-MM.N` with date and time (Europe/Berlin), stored in UTC. Running it again before the commit updates the open version instead of adding one, so one commit = one version.
- Version and Stand are shown on the cover, in the nav and in the footer, independent of the "Änderungen zeigen" switch. Don't put them inside `.chg`/`.diff`/`.chg-txt`/`.chg-block`.
- The light/dark palette has one source: `MODI`/`KONSTANT` in `src/build.py`. Change values there, never in the generated HTML.
