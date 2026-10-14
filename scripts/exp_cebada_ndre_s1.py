#!/usr/bin/env python
"""Experimento cebada vs trigo: NDRE (Sentinel-2) y VV/VH (Sentinel-1) por década
sobre los mismos puntos de trigo, ventana ago-ene. Escribe en
data/processed/series_exp/trigo_{campania}/{depto}_{ndre|s1}.json, aparte de la
serie principal. Un job por depto y producto; si el JSON existe no se repite.

Uso: python scripts/exp_cebada_ndre_s1.py --campania 2023 --deptos 06063,06280 [--productos ndre,s1]
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from agro import cdse, config
from agro.anomalia import ventana_extraccion

OUT_DIR = config.RAIZ / "data" / "processed"


def cubo_s1(conn, puntos, inicio, fin):
    """VV y VH (sigma0, lineal) medios por década; mezcla órbitas ascendente y descendente."""
    s1 = conn.load_collection(
        "SENTINEL1_GRD",
        spatial_extent=cdse._bbox(puntos),
        temporal_extent=[inicio, fin],
        bands=["VV", "VH"],
    )
    s1 = s1.sar_backscatter(coefficient="sigma0-ellipsoid")
    return s1.aggregate_temporal_period("dekad", reducer="mean").aggregate_spatial(
        geometries=cdse.puntos_geojson(puntos), reducer="mean"
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--campania", type=int, required=True)
    p.add_argument("--deptos", required=True)
    p.add_argument("--productos", default="ndre,s1")
    p.add_argument("--workers", type=int, default=3)
    args = p.parse_args()

    inicio, fin = ventana_extraccion(config.cultivo("trigo"), args.campania)
    puntos = pd.read_parquet(OUT_DIR / f"puntos_trigo_{args.campania}_pampa-humeda.parquet")
    carpeta = OUT_DIR / "series_exp" / f"trigo_{args.campania}"
    carpeta.mkdir(parents=True, exist_ok=True)
    conn = cdse.conectar()
    tareas = [(d, pr) for d in args.deptos.split(",") for pr in args.productos.split(",")]

    def uno(tarea):
        depto, producto = tarea
        salida = carpeta / f"{depto}_{producto}.json"
        pts = puntos[puntos["depto_id"] == depto].reset_index(drop=True)
        for intento in range(6):
            try:
                if producto == "ndre":
                    cdse.INDICES_S2 = ["NDRE"]  # misma lista para todos los hilos
                    cubo = cdse.cubo_s2(conn, pts, inicio, fin)
                else:
                    cubo = cubo_s1(conn, pts, inicio, fin)
                cdse.extraer(cubo, salida)
                return tarea, None
            except Exception as e:
                if intento == 5:
                    return tarea, e
                time.sleep(60 * (intento + 1))

    with ThreadPoolExecutor(args.workers) as pool:
        fallas = [(t, e) for t, e in pool.map(uno, tareas) if e]
    for t, e in fallas:
        print(f"FALLÓ {t}: {e}")
    print(f"listo: {len(tareas) - len(fallas)}/{len(tareas)}")


if __name__ == "__main__":
    main()
