"""Vectorise the partner logos from the supplied key visual into SVGs (assets/logos/*.svg).

Each logo is cropped, upscaled, split into colour layers by nearest palette colour and
traced with potrace (pip install potracer pillow numpy). Coordinates stay in source pixels.
Usage: python3 tools/trace_logos.py path/to/keyvisual.jpg
"""
import sys, os
import numpy as np
from PIL import Image
import potrace

UP = 8
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logos')

# Pixel-grid icons are redrawn by hand (measured from the key visual) instead of traced:
# name: (x in crop px left of which tracing is skipped, svg markup in crop px)
U = 12.5
ICONS = {
    'asseto': (64, '<g id="icon"><rect x="7" y="8" width="55" height="54" rx="2" fill="#01102B"/>'
                   '<rect x="39" y="40" width="14" height="14" fill="#fff"/></g>'),
    'gauntlet': (75, '<g id="icon" transform="translate(9 6)">'
                     f'<path fill="#7180F5" d="M0 0H{4*U}V{U}H{U}V{4*U}H{3*U}V{3*U}H{2*U}V{2*U}H{4*U}V{5*U}H{U}V{4*U}H0Z"/>'
                     f'<rect x="{4*U}" y="{U}" width="{U}" height="{U}" fill="#FF7A94"/>'
                     f'<rect x="0" y="{5*U}" width="{U}" height="{U}" fill="#1E1C2D"/></g>'),
}

# name: (crop box in the 1920x1080 key visual, [(layer id, rgb, svg fill)])
LOGOS = {
    'startale-word': ((180, 100, 660, 205), [('ink', (0, 0, 0), '#000000')]),
    'asseto': ((70, 805, 420, 875), [('ink', (1, 16, 43), '#01102B')]),
    'gauntlet': ((550, 795, 900, 885), [('g', (113, 128, 245), '#7180F5'), ('pink', (255, 122, 148), '#FF7A94'),
                                         ('ink', (30, 28, 45), '#1E1C2D')]),
    'morpho': ((1025, 800, 1360, 880), [('wing', (36, 113, 255), '#2471FF'), ('wing2', (0, 72, 200), '#0A4BC8'),
                                        ('ink', (15, 15, 15), '#0F0F0F')]),
    'flowmark': ((1490, 805, 1855, 875), [('ink', (0, 0, 0), '#000000')]),
}


def path_d(plist, scale):
    out = []
    f = lambda p: f'{p.x / scale:.2f} {p.y / scale:.2f}'
    for curve in plist:
        out.append('M' + f(curve.start_point))
        for s in curve.segments:
            if s.is_corner:
                out.append('L' + f(s.c) + 'L' + f(s.end_point))
            else:
                out.append('C' + f(s.c1) + ' ' + f(s.c2) + ' ' + f(s.end_point))
        out.append('Z')
    return ''.join(out)


def trace(src, name, box, layers):
    im = src.crop(box)
    big = np.asarray(im.resize((im.width * UP, im.height * UP), Image.LANCZOS)).astype(float)
    pal = np.array([(255, 255, 255)] + [l[1] for l in layers], float)
    # anything close to white (incl. the faint green background tint) is background
    d = ((big[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    d[:, :, 0] *= 0.6
    cls = d.argmin(-1)
    skip, icon = ICONS.get(name, (0, ''))
    cls[:, :skip * UP] = 0
    parts = []
    for i, (lid, _, fill) in enumerate(layers, 1):
        mask = cls == i  # potracer traces the False pixels, hence ~mask below
        plist = potrace.Bitmap(~mask).trace(turdsize=40, alphamax=1.0, opticurve=True, opttolerance=0.2)
        parts.append(f'<path id="{lid}" fill="{fill}" fill-rule="evenodd" d="{path_d(plist, UP)}"/>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{im.width}" height="{im.height}" '
           f'viewBox="0 0 {im.width} {im.height}">' + icon + ''.join(parts) + '</svg>')
    with open(os.path.join(OUT, name + '.svg'), 'w') as fh:
        fh.write(svg)
    print(name, len(svg))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    src = Image.open(sys.argv[1]).convert('RGB')
    for n, (b, l) in LOGOS.items():
        trace(src, n, b, l)
