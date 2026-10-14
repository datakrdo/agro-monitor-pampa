#!/usr/bin/env python
"""Curvas suavizadas y features fenológicas por depto y campaña, a partir de
las series extraídas (data/processed/series/{cultivo}_{año}/{depto}.parquet).

Uso: python scripts/05_features.py --cultivo soja
Salida: curvas_{cultivo}.parquet (depto_id, campania, fecha, decada, valor)
        features_{cultivo}.parquet (una fila por depto y campaña)
"""

from __future__ import annotations

import argparse

import pandas as pd

from agro import config, fenologia
from agro.anomalia import etiqueta_campania

OUT_DIR = config.RAIZ / "data" / "processed"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cultivo", required=True)
    args = p.parse_args()

    curvas, feats = [], []
    for carpeta in sorted((OUT_DIR / "series").glob(f"{args.cultivo}_*")):
        campania = etiqueta_campania(int(carpeta.name.split("_")[1]))
        for f in sorted(carpeta.glob("*.parquet")):
            serie = pd.read_parquet(f)
            c = fenologia.curva_depto(serie)
            curvas.append(
                pd.DataFrame(
                    {
                        "depto_id": f.stem,
                        "campania": campania,
                        "fecha": c.index,
                        "decada": range(len(c)),
                        "valor": c.to_numpy(),
                    }
                )
            )
            feats.append(
                {"depto_id": f.stem, "campania": campania, **fenologia.features_depto(serie)}
            )
        print(f"{carpeta.name}: {len(list(carpeta.glob('*.parquet')))} deptos")
    pd.concat(curvas, ignore_index=True).to_parquet(
        OUT_DIR / f"curvas_{args.cultivo}.parquet", index=False
    )
    pd.DataFrame(feats).to_parquet(OUT_DIR / f"features_{args.cultivo}.parquet", index=False)


if __name__ == "__main__":
    main()
