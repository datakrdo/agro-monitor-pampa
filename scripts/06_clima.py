#!/usr/bin/env python
"""Baja el clima diario (Open-Meteo/ERA5) por departamento y calcula las
features de la ventana de cada cultivo y campaña.

Uso: python scripts/06_clima.py --cultivo soja --campanias 2018 2019 2020 2021 2022 2023 2024
El diario se guarda una vez y se reutiliza (borrar el parquet para refrescar).
Salida: clima_diario_{region}.parquet y clima_{cultivo}_{region}.parquet
"""

from __future__ import annotations

import argparse

import geopandas as gpd
import pandas as pd

from agro import clima, config
from agro.anomalia import etiqueta_campania, ventana_extraccion

OUT_DIR = config.RAIZ / "data" / "processed"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cultivo", required=True)
    p.add_argument("--campanias", type=int, nargs="+", required=True)
    p.add_argument(
        "--region",
        default=None,
        help="por defecto, la región del cultivo en cultivos.yaml (o pampa-humeda)",
    )
    args = p.parse_args()
    args.region = args.region or config.cultivo(args.cultivo).get("region", "pampa-humeda")

    cfg = config.cultivo(args.cultivo)
    ventanas = {a: ventana_extraccion(cfg, a) for a in args.campanias}
    inicio = min(v[0] for v in ventanas.values())
    fin = min(
        max(v[1] for v in ventanas.values()),
        (pd.Timestamp.today() - pd.Timedelta(days=7)).strftime("%Y-%m-%d"),
    )  # ERA5 llega con ~5 días de retraso

    ruta = OUT_DIR / f"clima_diario_{args.region}.parquet"
    diario = pd.read_parquet(ruta) if ruta.exists() else pd.DataFrame(columns=["depto_id", "fecha"])
    puntos = clima.puntos_representativos(
        gpd.read_file(OUT_DIR / f"geometrias_{args.region}.geojson")
    )
    for r in puntos.itertuples():
        d = diario[diario["depto_id"] == r.depto_id]
        tramos = clima.tramos_faltantes(d["fecha"], inicio, fin)
        if not tramos:
            continue
        nuevos = [
            clima.descargar(r.lon, r.lat, ini, hasta).assign(depto_id=r.depto_id)
            for ini, hasta in tramos
        ]
        diario = pd.concat([diario, *nuevos], ignore_index=True).sort_values(["depto_id", "fecha"])
        diario.to_parquet(ruta, index=False)  # guarda de a uno: si se corta, reanuda
    print(
        f"diario: {diario['depto_id'].nunique()} deptos, {diario['fecha'].min().date()} -> {diario['fecha'].max().date()}"
    )

    filas = [
        {
            "depto_id": depto_id,
            "campania": etiqueta_campania(a),
            **clima.features_ventana(
                g, *ventanas[a], tmax_calor=cfg.get("tmax_calor", clima.TMAX_CALOR)
            ),
        }
        for depto_id, g in diario.groupby("depto_id")
        for a in args.campanias
    ]
    salida = OUT_DIR / f"clima_{args.cultivo}_{args.region}.parquet"
    pd.DataFrame(filas).to_parquet(salida, index=False)
    print(f"-> {salida} ({len(filas)} filas)")


if __name__ == "__main__":
    main()
