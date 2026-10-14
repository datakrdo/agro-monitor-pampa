#!/usr/bin/env python
"""Miniatura para compartir el sitio (og:image, 1200x630): las dos imágenes
del hero lado a lado con el título. Sale de web/static/img/pergamino_*.webp.

Uso: python scripts/10_og_image.py
Salida: web/static/img/og.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
from PIL import Image, ImageDraw, ImageFont

from agro import config

IMG = config.RAIZ / "web" / "static" / "img"
FUENTES = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
W, H = 1200, 630


def main() -> None:
    meta = json.loads(
        (config.RAIZ / "web" / "src" / "lib" / "data" / "hero_imagenes.json").read_text()
    )["imagenes"]
    lienzo = Image.new("RGB", (W, H))
    for i, m in enumerate(meta):
        im = Image.open(IMG / Path(m["archivo"]).name).convert("RGB")
        lado = min(im.size)
        im = im.crop(
            (
                (im.width - lado) // 2,
                (im.height - lado) // 2,
                (im.width + lado) // 2,
                (im.height + lado) // 2,
            )
        ).resize((H, H))
        lienzo.paste(
            im.crop(((H - W // 2) // 2, 0, (H - W // 2) // 2 + W // 2, H)), (i * W // 2, 0)
        )
    d = ImageDraw.Draw(lienzo, "RGBA")
    d.rectangle((0, H - 250, W, H), fill=(18, 28, 20, 218))
    d.rectangle((W // 2 - 1, 0, W // 2 + 1, H - 250), fill=(255, 255, 255, 235))
    titulo = "¿Viene buena o mala la campaña de soja?"
    tam = 54
    while (
        d.textlength(titulo, font=ImageFont.truetype(str(FUENTES / "DejaVuSerif-Bold.ttf"), tam))
        > W - 112
    ):
        tam -= 2
    serif = ImageFont.truetype(str(FUENTES / "DejaVuSerif-Bold.ttf"), tam)
    sans = ImageFont.truetype(str(FUENTES / "DejaVuSans.ttf"), 27)
    chico = ImageFont.truetype(str(FUENTES / "DejaVuSans-Bold.ttf"), 22)
    d.text((56, H - 228), titulo, font=serif, fill="white")
    d.text(
        (56, H - 143),
        "Lo anticipamos con imágenes satelitales Sentinel-2.",
        font=sans,
        fill=(226, 232, 226),
    )
    d.text((56, H - 70), "AGRO MONITOR PAMPA", font=chico, fill=(150, 214, 170))
    for i, m in enumerate(meta):
        texto = f"Pergamino, enero {m['anio']}" + (" · sequía" if i == 0 else "")
        d.rounded_rectangle(
            (20 + i * W // 2, 20, 20 + i * W // 2 + 12 + d.textlength(texto, font=chico), 62),
            20,
            fill=(20, 24, 20, 200),
        )
        d.text((32 + i * W // 2, 29), texto, font=chico, fill="white")
    lienzo.save(IMG / "og.png", optimize=True)
    print(IMG / "og.png")


if __name__ == "__main__":
    main()
