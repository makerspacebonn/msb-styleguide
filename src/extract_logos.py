"""Extract transparent logo PNGs (Farbe, Negativ, Weiß, Schwarz) from the original style guide PDF.

Usage: python3 src/extract_logos.py "<path to MakerSpace Bonn Styleguide V2026-02-15 PDF>"
Needs poppler (pdftoppm), Pillow and numpy. Crop boxes match the 2026-02-15 layout (pages 9 and 12).
"""
import pathlib
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'logos'
GREEN, INK, WHITE = (94, 177, 48), (30, 28, 25), (255, 255, 255)


def render(pdf, page, tmp):
    prefix = pathlib.Path(tmp) / f'p{page}'
    subprocess.run(['pdftoppm', '-r', '300', '-png', '-f', str(page), '-l', str(page), pdf, str(prefix)], check=True, timeout=60)
    return next(pathlib.Path(tmp).glob(f'p{page}*.png'))


def extract(src, box, name):
    im = np.asarray(Image.open(src).convert('RGB').crop(box)).astype(float)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    green = (g - r) > 25
    a = np.clip(np.where(green, (255 - b) / (255 - 48), (255 - np.minimum(np.minimum(r, g), b)) / 255), 0, 1)
    ys, xs = np.where(a > 0.05)
    a, green = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1], green[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    for suffix, gcol, tcol in [('farbe', GREEN, INK), ('negativ', GREEN, WHITE), ('weiss', WHITE, WHITE), ('schwarz', INK, INK)]:
        out = np.zeros(a.shape + (4,), np.uint8)
        for i in range(3):
            out[..., i] = np.where(green, gcol[i], tcol[i])
        out[..., 3] = (a * 255).astype(np.uint8)
        Image.fromarray(out, 'RGBA').save(OUT / f'{name}-{suffix}.png', optimize=True)


if __name__ == '__main__':
    pdf = sys.argv[1]
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        p9, p12 = render(pdf, 9, tmp), render(pdf, 12, tmp)
        extract(p9, (255, 786, 1365, 1155), 'logo-h')
        extract(p12, (255, 786, 735, 1500), 'logo-v')
        extract(p12, (255, 786, 735, 1275), 'cube')
    print('logos written to', OUT)
