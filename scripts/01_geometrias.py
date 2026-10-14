#!/usr/bin/env python
"""Descarga los departamentos del IGN y guarda, por región de
config/regiones.yaml, un GeoJSON (para el mapa) y una tabla plana
depto_id/depto/provincia (para joins, sin geometría).

Uso: python scripts/01_geometrias.py --region pampa-humeda
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import requests

from agro import config, geometrias

CACHE_DIR = config.RAIZ / "data" / "raw" / "ign_departamento"
OUT_DIR = config.RAIZ / "data" / "processed"


def descargar_ign(cache_dir: Path) -> Path:
    existentes = list(cache_dir.glob("**/ign_departamento.shp"))
    if existentes:
        return existentes[0]
    cache_dir.mkdir(parents=True, exist_ok=True)
    resp = requests.get(geometrias.IGN_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=180)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        z.extractall(cache_dir)
    return next(cache_dir.glob("**/ign_departamento.shp"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="pampa-humeda")
    args = parser.parse_args()

    region_cfg = config.region(args.region)
    shp_path = descargar_ign(CACHE_DIR)
    deptos = geometrias.cargar_departamentos(shp_path)
    deptos_region = geometrias.filtrar_region(deptos, region_cfg)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    deptos_region.drop(columns="geometry").to_parquet(
        OUT_DIR / f"departamentos_{args.region}.parquet", index=False
    )
    (OUT_DIR / f"geometrias_{args.region}.geojson").write_text(
        json.dumps(geometrias.geojson_simplificado(deptos_region))
    )
    print(f"{len(deptos_region)} departamentos en '{args.region}' -> {OUT_DIR}")


if __name__ == "__main__":
    main()
