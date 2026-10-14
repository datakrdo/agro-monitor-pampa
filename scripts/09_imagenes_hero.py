#!/usr/bin/env python
"""Dos imágenes Sentinel-2 en color real del mismo lote de Pergamino, en la
misma fecha de dos campañas (la de la sequía y la que le siguió), para el
antes/después del sitio. Cuesta unos pocos créditos de CDSE; se corre una vez
y las imágenes se versionan.

Uso: python scripts/09_imagenes_hero.py --cultivo soja
Salida: web/static/img/pergamino_{año}.webp y web/src/lib/data/hero_imagenes.json
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd
import rasterio
from PIL import Image

from agro import cdse, config

OUT_DIR = config.RAIZ / "data" / "processed"
WEB = config.RAIZ / "web"
DEPTO = "06623"  # Pergamino
MEDIA_VENTANA = 22  # días a cada lado de la década: mediana de ~6 semanas con nubes enmascaradas
MEDIO_LADO = (0.09, 0.11)  # grados (lat, lon): ~20 x 20 km
ANCHO_PX = 1600
INVALIDOS = cdse.SCL_INVALIDO + (7,)  # además, nube de baja probabilidad / sin clasificar
DILATAR = 3  # píxeles: los bordes de las nubes finas manchan una imagen en color real


def fecha_de_mayor_contraste(curvas: pd.DataFrame, depto: str, mala: str, normal: str) -> int:
    """Década donde más se separan las dos campañas en NDVI (la que mejor se ve en una foto)."""
    c = curvas[curvas["depto_id"] == depto].pivot(
        index="decada", columns="campania", values="valor"
    )
    return int((c[normal] - c[mala]).idxmax())


def descargar(conn, bbox: dict, desde: str, hasta: str, salida) -> None:
    s2 = conn.load_collection(
        "SENTINEL2_L2A",
        spatial_extent=bbox,
        temporal_extent=[desde, hasta],
        bands=["B04", "B03", "B02", "SCL"],
    )
    rgb = (
        cdse.mascara_nubes(s2, INVALIDOS, DILATAR)
        .filter_bands(["B04", "B03", "B02"])
        .reduce_dimension(dimension="t", reducer="median")
    )
    for intento in range(6):
        try:
            rgb.execute_batch(outputfile=salida, out_format="GTiff", title=salida.stem)
            return
        except Exception as e:  # 429 por el tope de conexiones de CDSE
            if "429" not in str(e) or intento == 5:
                raise
            time.sleep(60 * (intento + 1))


def recorte(validos: np.ndarray, minimo: float = 0.995) -> tuple[slice, slice]:
    """Filas y columnas a conservar: se sacan de los bordes las que tienen píxeles sin dato (el tile no cubre todo el bbox)."""
    f0, f1, c0, c1 = 0, validos.shape[0], 0, validos.shape[1]
    while True:
        sub = validos[f0:f1, c0:c1]
        malo = {
            "izq": sub[:, 0].mean(),
            "der": sub[:, -1].mean(),
            "arr": sub[0].mean(),
            "aba": sub[-1].mean(),
        }
        peor = min(malo, key=malo.get)
        if malo[peor] >= minimo:
            return slice(f0, f1), slice(c0, c1)
        f0, f1, c0, c1 = (
            f0 + (peor == "arr"),
            f1 - (peor == "aba"),
            c0 + (peor == "izq"),
            c1 - (peor == "der"),
        )


def a_webp(tifs: list, salidas: list) -> list[float]:
    """Mismo recorte y mismo estiramiento (percentiles 2-98 de las dos imágenes juntas) para que sean comparables."""
    imgs = []
    for t in tifs:
        with rasterio.open(t) as r:
            imgs.append(r.read().astype("float32"))
    validos = np.logical_and.reduce(
        [np.isfinite(i).all(axis=0) & (i > 0).all(axis=0) for i in imgs]
    )
    filas, cols = recorte(validos)
    imgs = [i[:, filas, cols] for i in imgs]
    todo = np.concatenate([i.ravel() for i in imgs])
    lo, hi = np.percentile(todo, [2, 98])
    for img, salida in zip(imgs, salidas):
        rgb = np.clip((np.nan_to_num(img) - lo) / (hi - lo), 0, 1) ** 0.8
        im = Image.fromarray((rgb.transpose(1, 2, 0) * 255).astype("uint8"))
        im.resize((ANCHO_PX, round(ANCHO_PX * im.height / im.width)), Image.LANCZOS).save(
            salida, "WEBP", quality=82
        )
    return [float(lo), float(hi)]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cultivo", default="soja")
    args = p.parse_args()

    validacion = json.loads((WEB / "src" / "lib" / "data" / "validacion.json").read_text())["hero"]
    mala, normal = validacion["campania_mala"], validacion["campania_normal"]
    curvas = pd.read_parquet(OUT_DIR / f"curvas_{args.cultivo}.parquet")
    curvas["fecha"] = pd.to_datetime(curvas["fecha"])
    d = fecha_de_mayor_contraste(curvas, DEPTO, mala, normal)
    puntos = pd.read_parquet(
        OUT_DIR / f"puntos_{args.cultivo}_{mala.split('/')[0]}_pampa-humeda.parquet"
    ).query("depto_id == @DEPTO")
    lat, lon = puntos["lat"].median(), puntos["lon"].median()
    bbox = {
        "west": lon - MEDIO_LADO[1],
        "east": lon + MEDIO_LADO[1],
        "south": lat - MEDIO_LADO[0],
        "north": lat + MEDIO_LADO[0],
    }

    conn = cdse.conectar()
    imagenes, tifs, webps = [], [], []
    (WEB / "static" / "img").mkdir(parents=True, exist_ok=True)
    for campania in (mala, normal):
        centro = curvas[
            (curvas["depto_id"] == DEPTO)
            & (curvas["campania"] == campania)
            & (curvas["decada"] == d)
        ]["fecha"].iloc[0]
        desde, hasta = (
            (centro - pd.Timedelta(days=MEDIA_VENTANA)).date(),
            (centro + pd.Timedelta(days=MEDIA_VENTANA)).date(),
        )
        tif = OUT_DIR / f"hero_{centro.year}.tif"
        if not tif.exists():
            descargar(conn, bbox, str(desde), str(hasta), tif)
        tifs.append(tif)
        webps.append(WEB / "static" / "img" / f"pergamino_{centro.year}.webp")
        imagenes.append(
            {
                "campania": campania,
                "anio": int(centro.year),
                "centro": str(centro.date()),
                "desde": str(desde),
                "hasta": str(hasta),
                "archivo": f"/img/pergamino_{centro.year}.webp",
            }
        )
    estiramiento = a_webp(tifs, webps)
    (WEB / "src" / "lib" / "data" / "hero_imagenes.json").write_text(
        json.dumps(
            {"depto_id": DEPTO, "bbox": bbox, "estiramiento": estiramiento, "imagenes": imagenes},
            indent=1,
        )
    )
    print(json.dumps(imagenes, indent=1))


if __name__ == "__main__":
    main()
