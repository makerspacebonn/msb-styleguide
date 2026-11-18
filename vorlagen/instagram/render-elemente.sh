#!/bin/sh
# Rendert elemente/ki-label.html in einzelne PNGs (2x, transparent) nach elemente/png/.
# Braucht Google Chrome, Internet (Google Fonts) und Python mit Pillow.
set -e
cd "$(dirname "$0")/elemente"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p png
for v in generiert-dunkel generiert-hell bearbeitet-dunkel bearbeitet-hell; do
  sed "s#</style>#body > :not(\#$v){display:none}</style>#" ki-label.html > _tmp.html
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --default-background-color=00000000 --window-size=600,200 --virtual-time-budget=8000 \
    --screenshot="png/ki-$v.png" "file://$PWD/_tmp.html" 2>/dev/null
  python3 -I -c "from PIL import Image; im=Image.open('png/ki-$v.png'); im.crop(im.getbbox()).save('png/ki-$v.png')"
done
rm -f _tmp.html
ls -1 png
