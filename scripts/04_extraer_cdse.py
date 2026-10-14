#!/usr/bin/env python
"""Extrae la serie NDVI por década de los puntos MNC vía CDSE openEO,
un job por departamento, incremental (reanuda lo que falte).

Uso: python scripts/04_extraer_cdse.py --cultivo soja --campania 2024 [--limite 3]
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from agro import cdse, config
from agro.anomalia import ventana_extraccion

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
    p.add_argument("--limite", type=int, help="solo los primeros N deptos (prueba)")
    p.add_argument(
        "--deptos", help="solo estos deptos (ids separados por coma), p. ej. 06063,06280"
    )
    p.add_argument("--workers", type=int, default=1)
    args = p.parse_args()
    args.region = args.region or config.cultivo(args.cultivo).get("region", "pampa-humeda")

    cfg = config.cultivo(args.cultivo)
    inicio, fin = ventana_extraccion(cfg, args.campania)
    puntos = pd.read_parquet(
        OUT_DIR / f"puntos_{args.cultivo}_{args.campania}_{args.region}.parquet"
    )
    deptos = sorted(puntos["depto_id"].unique())
    if args.deptos:
        deptos = [d for d in deptos if d in args.deptos.split(",")]
    deptos = deptos[: args.limite]
    carpeta = OUT_DIR / "series" / f"{args.cultivo}_{args.campania}"
    carpeta.mkdir(parents=True, exist_ok=True)
    print(f"{args.cultivo} {args.campania}: {len(deptos)} deptos, {inicio} -> {fin}")

    conn = cdse.conectar()

    def uno(depto_id):
        pts = puntos[puntos["depto_id"] == depto_id].reset_index(drop=True)
        for intento in range(5):
            try:
                cdse.extraer_incremental(conn, pts, inicio, fin, carpeta / f"{depto_id}.parquet")
                return depto_id, None
            except Exception as e:  # un depto fallado no frena al resto; se reintenta al re-correr
                if "429" not in str(e) or intento == 4:
                    return depto_id, e
                time.sleep(60 * (intento + 1))  # CDSE limita jobs simultáneos

    with ThreadPoolExecutor(args.workers) as pool:
        fallas = [(d, e) for d, e in pool.map(uno, deptos) if e]
    for d, e in fallas:
        print(f"FALLÓ {d}: {e}")
    print(f"listo: {len(deptos) - len(fallas)}/{len(deptos)}")


if __name__ == "__main__":
    main()
