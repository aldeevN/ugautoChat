"""
Convert main-logo.svg -> main-logo.png (writes to project root).
Requires cairosvg + Pillow. Run locally in project folder:

python3 -m pip install --user cairosvg Pillow
python3 scripts/convert_logo.py

This script will exit with error if conversion fails.
"""
import sys
from pathlib import Path

svg = Path('main-logo.svg')
png = Path('main-logo.png')
if not svg.exists():
    print('main-logo.svg not found in current directory.')
    sys.exit(1)

try:
    import cairosvg
    from PIL import Image
except Exception as e:
    print('Missing dependencies:', e)
    print('Install: python3 -m pip install --user cairosvg Pillow')
    sys.exit(2)

try:
    cairosvg.svg2png(url=str(svg), write_to=str(png))
    print('Wrote', png)
except Exception as e:
    print('Conversion failed:', e)
    sys.exit(3)

# Optionally resize to a friendly height
try:
    img = Image.open(png)
    target_h = 48
    w, h = img.size
    if h != target_h:
        try:
            res = Image.Resampling.LANCZOS
        except Exception:
            res = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS
        img = img.resize((int(w * (target_h / h)), target_h), res)
        img.save(png)
        print('Resized PNG to height', target_h)
except Exception as e:
    print('Post-resize failed (non-fatal):', e)

print('Done.')
