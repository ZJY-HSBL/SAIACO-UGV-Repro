"""Approximate 30x30 obstacle occupancy extraction from six paper figures.

Dependency: pymupdf, pillow, numpy. Bounding boxes match the supplied PDF when
rendered at 2.5x (page 8/9). Text path graphics and raster grid may cause errors.
The start/goal are fixed research probes, not recovered author waypoints.
"""
from __future__ import annotations
from pathlib import Path
import fitz
import numpy as np
from PIL import Image

FIGURES = {
 'u_maze': (7, (223,1197,685,1554)),
 'double_hook_maze': (7, (872,281,1335,643)),
 'loop_maze': (7, (872,838,1335,1199)),
 'traditional_maze': (7, (872,1395,1335,1752)),
 'staircase_maze': (8, (222,300,685,657)),
 'x_maze': (8, (222,856,685,1214)),
}


def extract(pdf: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    for name, (page, box) in FIGURES.items():
        pix = doc[page].get_pixmap(matrix=fitz.Matrix(2.5,2.5),alpha=False)
        gray = np.asarray(Image.frombytes(
            'RGB', [pix.width,pix.height], pix.samples).convert('L'))
        x1,y1,x2,y2 = box
        walls = np.zeros((30,30), dtype=bool)
        for r in range(30):
            for c in range(30):
                bx1 = round(x1 + (c+.22)*(x2-x1)/30)
                bx2 = round(x1 + (c+.78)*(x2-x1)/30)
                by1 = round(y1 + (r+.22)*(y2-y1)/30)
                by2 = round(y1 + (r+.78)*(y2-y1)/30)
                walls[r,c] = np.mean(gray[by1:by2,bx1:bx2]<105)>.60
        start, goal = (29,0), (0,29)
        walls[start] = walls[goal] = False
        lines=[''.join('S' if (r,c)==start else 'G' if (r,c)==goal
                       else '#' if walls[r,c] else '.' for c in range(30))
               for r in range(30)]
        (out / (name+'.txt')).write_text(
           '; Approximate figure-digitization; endpoints are evaluation assumptions.\n'
           +'\n'.join(lines)+'\n', encoding='utf-8')
        print(name, int(walls.sum()))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--out', type=Path,
                        default=Path('src/saiaco_ugv/maps'))
    args = parser.parse_args()
    extract(args.pdf, args.out)
