"""Approximate paper grid digitization, requiring pymupdf, numpy, Pillow."""
from __future__ import annotations
import argparse
from pathlib import Path
import fitz
import numpy as np
from PIL import Image

FIGURES = [
    (5, 20, [(587,191,899,430),(587,553,899,792),(587,917,899,1156)],(3,0),(19,19),'paper20'),
    (6, 30, [(587,202,900,441),(587,577,900,816),(587,951,900,1190)],(29,0),(0,29),'paper30'),
]


def main():
    p = argparse.ArgumentParser(description='Digitize approximate paper figure grids')
    p.add_argument('pdf', type=Path)
    p.add_argument('--out', type=Path, default=Path('src/saiaco_ugv/maps'))
    args = p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    doc = fitz.open(args.pdf)
    for pageid,n,boxes,start,goal,name in FIGURES:
        pix = doc[pageid].get_pixmap(matrix=fitz.Matrix(125/72,125/72),alpha=False)
        gray = np.asarray(Image.frombytes('RGB',[pix.width,pix.height],pix.samples).convert('L'))
        estimates = []
        for x1,y1,x2,y2 in boxes:
            fractions = np.zeros((n,n))
            for r in range(n):
                for c in range(n):
                    xlo = int(x1+(c+.23)*(x2-x1)/n)
                    xhi = int(x1+(c+.77)*(x2-x1)/n)
                    ylo = int(y1+(r+.23)*(y2-y1)/n)
                    yhi = int(y1+(r+.77)*(y2-y1)/n)
                    fractions[r,c] = np.mean(gray[ylo:yhi,xlo:xhi]<95)
            estimates.append(fractions)
        walls = np.median(estimates,axis=0)>.65
        if walls[start] or walls[goal]:
            raise ValueError('Incorrect crop or input PDF edition')
        rows = [''.join('S' if (r,c)==start else 'G' if (r,c)==goal else '#' if walls[r,c] else '.' for c in range(n)) for r in range(n)]
        path = args.out/f'{name}.txt'
        path.write_text('; Figure-derived approximation; not author-provided obstacle matrix.\n'+'\n'.join(rows)+'\n',encoding='utf-8')
        print(path, 'obstacle cells:',int(walls.sum()))


if __name__ == '__main__':
    main()
