#!/usr/bin/env python
"""Descarga las estimaciones agrícolas del MAGyP y guarda, por cultivo
y región, una tabla lista para el join de validación.

Uso: python scripts/03_magyp.py --region pampa-humeda
"""

from __future__ import annotations

import argparse

import pandas as pd

from agro import config, magyp

OUT_DIR = config.RAIZ / "data" / "processed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default="pampa-humeda")
    args = parser.parse_args()

    deptos = pd.read_parquet(OUT_DIR / f"departamentos_{args.region}.parquet")
    depto_ids = set(deptos["depto_id"])

    url = magyp.url_csv_actual()
    print(f"CSV: {url}")

    tablas = []
    for cultivo_id, cfg in config.cargar_cultivos().items():
        tabla = magyp.cargar_estimaciones(url, cfg["magyp_cultivo"], depto_ids)
        tabla.insert(0, "cultivo", cultivo_id)
        tablas.append(tabla)
        print(f"{cultivo_id}: {len(tabla)} filas ({tabla['depto_id'].nunique()} departamentos)")

    salida = pd.concat(tablas, ignore_index=True)
    salida.to_parquet(OUT_DIR / f"magyp_{args.region}.parquet", index=False)
    print(f"-> {OUT_DIR / f'magyp_{args.region}.parquet'} ({len(salida)} filas)")


if __name__ == "__main__":
    main()
