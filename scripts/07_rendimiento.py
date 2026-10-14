#!/usr/bin/env python
"""Validación leave-one-campaign-out del modelo de rendimiento.

Uso: python scripts/07_rendimiento.py --cultivo soja
Salida: rendimiento_pred_{cultivo}.parquet (depto, campaña, y, base, pred, modelo)
        rendimiento_metricas_{cultivo}.parquet (RMSE/MAPE modelo vs línea base)
"""

from __future__ import annotations

import argparse

import pandas as pd

from agro import config, rendimiento

OUT_DIR = config.RAIZ / "data" / "processed"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cultivo", required=True)
    p.add_argument(
        "--region",
        default=None,
        help="por defecto, la región del cultivo en cultivos.yaml (o pampa-humeda)",
    )
    args = p.parse_args()
    args.region = args.region or config.cultivo(args.cultivo).get("region", "pampa-humeda")

    magyp = pd.read_parquet(OUT_DIR / f"magyp_{args.region}.parquet").query(
        "cultivo == @args.cultivo"
    )
    features = pd.read_parquet(OUT_DIR / f"features_{args.cultivo}.parquet")
    clima = pd.read_parquet(OUT_DIR / f"clima_{args.cultivo}_{args.region}.parquet")
    tabla = rendimiento.armar_tabla(features, clima, magyp)
    print(
        f"{len(tabla)} filas, {tabla['campania'].nunique()} campañas, {tabla['depto_id'].nunique()} deptos"
    )

    preds, mets, pron = [], [], []
    for nombre, modelo in rendimiento.MODELOS.items():
        pred = rendimiento.loco(tabla, modelo)
        preds.append(pred.assign(modelo=nombre))
        pron.append(rendimiento.pronosticar(tabla, features, clima, modelo).assign(modelo=nombre))
        mets.append(
            rendimiento.metricas(pred).assign(modelo=nombre).rename_axis("campania").reset_index()
        )
    pd.concat(preds, ignore_index=True).to_parquet(
        OUT_DIR / f"rendimiento_pred_{args.cultivo}.parquet", index=False
    )
    pron = pd.concat(pron, ignore_index=True)
    pron.to_parquet(OUT_DIR / f"rendimiento_pronostico_{args.cultivo}.parquet", index=False)
    print(
        f"pronóstico: {pron['campania'].unique().tolist()}, {pron['depto_id'].nunique() if len(pron) else 0} deptos"
    )
    m = pd.concat(mets, ignore_index=True)
    m.to_parquet(OUT_DIR / f"rendimiento_metricas_{args.cultivo}.parquet", index=False)
    print(m.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
