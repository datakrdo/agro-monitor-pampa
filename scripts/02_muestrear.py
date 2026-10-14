#!/usr/bin/env python
"""Toma ~N puntos de cultivo por departamento sobre el MNC del INTA.

Uso: python scripts/02_muestrear.py --cultivo soja --campania 2024 --region pampa-humeda
`--campania` es el año de siembra (2024 -> MNC_ver25.tif para soja 2024/25;
trigo usa el mismo año calendario: 2024 -> MNC_inv24.tif).
"""

from __future__ import annotations

import argparse

import geopandas as gpd

from agro import config, muestreo

RAW = config.RAIZ / "data" / "raw"
OUT_DIR = config.RAIZ / "data" / "processed"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cultivo", required=True)
    p.add_argument("--campania", type=int, required=True)
    p.add_argument(
        "--region",
        default=None,
        help="por defecto, la región del cultivo en cultivos.yaml (o pampa-humeda)",
    )
    p.add_argument("-n", type=int, default=300)
    p.add_argument(
        "--mascara",
        type=int,
        help="año de siembra del MNC a usar si el de --campania todavía no salió (máscara provisoria)",
    )
    args = p.parse_args()
    args.region = args.region or config.cultivo(args.cultivo).get("region", "pampa-humeda")

    cfg = config.cultivo(args.cultivo)
    anio_mnc = args.mascara or args.campania
    aa = anio_mnc + 1 if cfg["cruza_anio"] else anio_mnc
    est = "ver" if cfg["mnc_estacion"] == "verano" else "inv"
    raster = RAW / "mnc" / f"MNC_{est}{aa % 100:02d}.tif"

    deptos = gpd.read_file(OUT_DIR / f"geometrias_{args.region}.geojson")
    puntos = muestreo.muestrear(
        raster, deptos, cfg.get("mnc_clase_campania", {}).get(anio_mnc, cfg["mnc_clase"]), n=args.n
    )
    salida = OUT_DIR / f"puntos_{args.cultivo}_{args.campania}_{args.region}.parquet"
    puntos.to_parquet(salida, index=False)
    print(f"{raster.name}: {puntos['depto_id'].nunique()} deptos, {len(puntos)} puntos -> {salida}")


if __name__ == "__main__":
    main()
