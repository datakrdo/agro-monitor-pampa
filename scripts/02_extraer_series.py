#!/usr/bin/env python
"""Extrae series NDVI/EVI mensuales por departamento, cultivo y campaña.

Una tarea de export asíncrona por (cultivo, campaña) — no por mes: un
reduceRegions síncrono sobre toda la región excede el presupuesto de
~5 min de la API síncrona de GEE sin importar scale/tileScale
(confirmado con pruebas reales), así que cada campaña arma sus
reduceRegions mensuales server-side y se exporta como asset con
Export.table.toAsset (ver src/agro/gee.py). Sentinel-2 tiene cobertura
plena sobre Argentina recién desde 2017.

El proyecto está en modo restringido de cuota noncommercial de GEE:
cada tarea puede tardar varios minutos. El script es reanudable —
si un asset ya existe lo reusa en vez de re-exportarlo.

Uso: python scripts/02_extraer_series.py --region pampa-humeda --project satelite-agro
"""

from __future__ import annotations

import argparse

import ee
import geopandas as gpd
import pandas as pd

from agro import config, gee
from agro.anomalia import ventana_campania

OUT_DIR = config.RAIZ / "data" / "processed"
ASSET_FOLDER = "projects/{project}/assets/agro_monitor_exports"
ANIO_INICIO_MIN = 2017


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="pampa-humeda")
    parser.add_argument("--project", required=True, help="Project ID de Google Earth Engine")
    parser.add_argument("--anio-desde", type=int, default=ANIO_INICIO_MIN)
    args = parser.parse_args()

    gee.inicializar(args.project)
    asset_folder = ASSET_FOLDER.format(project=args.project)

    geojson_path = OUT_DIR / f"geometrias_{args.region}.geojson"
    deptos_gdf = gpd.read_file(geojson_path)
    deptos_fc = gee.fc_departamentos(deptos_gdf)

    hoy = pd.Timestamp.today().normalize()
    anio_hasta = hoy.year

    assets_existentes = {
        a["name"].rsplit("/", 1)[-1]
        for a in ee.data.listAssets({"parent": asset_folder}).get("assets", [])
    }

    tareas = {}
    for cultivo_id, cultivo_cfg in config.cargar_cultivos().items():
        for anio_inicio in range(args.anio_desde, anio_hasta + 1):
            inicio, fin = ventana_campania(cultivo_cfg, anio_inicio)
            if inicio > hoy:
                continue
            fin = min(fin, hoy)
            nombre = f"{cultivo_id}_{anio_inicio}"
            if nombre in assets_existentes:
                print(f"{nombre}: ya exportado, se reusa")
                continue
            fc = gee.tabla_campania(deptos_fc, cultivo_cfg, inicio, fin)
            tareas[nombre] = gee.exportar_a_asset(fc, asset_folder, nombre)

    if tareas:
        print(f"Esperando {len(tareas)} tareas de export...")
        estados = gee.esperar_tareas(tareas)
        fallidas = [n for n, e in estados.items() if e != "COMPLETED"]
        if fallidas:
            raise RuntimeError(f"Tareas fallidas: {fallidas}")

    nombres_totales = assets_existentes | set(tareas)
    filas = []
    for nombre in sorted(nombres_totales):
        cultivo_id, anio_inicio = nombre.rsplit("_", 1)
        tabla = gee.leer_asset(f"{asset_folder}/{nombre}")
        tabla["cultivo"] = cultivo_id
        filas.append(tabla)

    serie = pd.concat(filas, ignore_index=True)
    serie["fecha"] = pd.to_datetime(serie["fecha"])
    serie = serie.merge(
        pd.read_parquet(OUT_DIR / f"departamentos_{args.region}.parquet")[
            ["depto_id", "depto", "provincia"]
        ],
        on="depto_id",
        how="left",
    )
    out_path = OUT_DIR / f"series_{args.region}.parquet"
    serie.to_parquet(out_path, index=False)
    print(f"{len(serie)} filas -> {out_path}")


if __name__ == "__main__":
    main()
