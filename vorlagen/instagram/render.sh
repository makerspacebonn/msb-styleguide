#!/bin/sh
# Rendert alle Vorlagen nach png/ (1080×1350). Braucht Google Chrome und Internet (Google Fonts).
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in [0-9][0-9]-*.html; do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size=1080,1350 --virtual-time-budget=8000 \
    --screenshot="png/${f%.html}.png" "file://$PWD/$f" 2>/dev/null
done
ls -1 png
