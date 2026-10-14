#!/usr/bin/env python
"""Exporta lo que el sitio (web/) necesita, sin que el sitio calcule nada:
las curvas, anomalías y estimaciones por depto y campaña, los departamentos
y las cifras de validación (cuánto acierta el satélite y a qué fecha).

Uso: python scripts/08_exportar_web.py --cultivo soja
Salida: web/static/data/monitor.json   (se pide al abrir el mapa)
        web/static/data/deptos.geojson (polígonos con coordenadas redondeadas)
        web/src/lib/data/validacion.json (cifras del texto y del gráfico de acierto; se inlinea en el HTML)
"""

from __future__ import annotations

import argparse
import json
from datetime import date

import pandas as pd

from agro import config, rendimiento
from agro.anomalia import MIN_PUNTOS, UMBRAL_ANOMALIA, acierto_por_decada, anomalias_por_decada

OUT_DIR = config.RAIZ / "data" / "processed"
WEB = config.RAIZ / "web"
MODELO_WEB = "ridge"  # el que mejor valida (ver Resultados en el README)
HERO_DEPTO = "06623"  # Pergamino, el piloto de la v1
DECADA_SEQUIA = "12-01"  # a qué fecha se cuenta cuántos deptos ya estaban en rojo


def redondear(valores, decimales: int) -> list:
    return [None if pd.isna(v) else round(float(v), decimales) for v in valores]


def guardar_json(ruta, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, separators=(",", ":"), ensure_ascii=False))
    print(f"{ruta.relative_to(config.RAIZ)}: {ruta.stat().st_size / 1024:.0f} KB")


def geojson_liviano(geojson: dict, decimales: int = 4) -> dict:
    """Solo el id y coordenadas con ~10 m de precisión: el nombre y la provincia viajan en monitor.json."""

    def redondeo(c):
        return (
            [round(c[0], decimales), round(c[1], decimales)]
            if isinstance(c[0], (int, float))
            else [redondeo(x) for x in c]
        )

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"depto_id": f["properties"]["depto_id"]},
                "geometry": {
                    "type": f["geometry"]["type"],
                    "coordinates": redondeo(f["geometry"]["coordinates"]),
                },
            }
            for f in geojson["features"]
        ],
    }


def etiquetas_decadas(curvas: pd.DataFrame) -> list[str]:
    """'MM-DD' de cada década; tiene que ser igual en todas las campañas."""
    por_campania = {
        c: g.groupby("decada")["fecha"].first().dt.strftime("%m-%d").tolist()
        for c, g in curvas.groupby("campania")
    }
    etiquetas = max(por_campania.values(), key=len)
    for c, e in por_campania.items():
        if e != etiquetas[: len(e)]:
            raise ValueError(f"las décadas de {c} no coinciden con las de las demás campañas")
    return etiquetas


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

    curvas = pd.read_parquet(OUT_DIR / f"curvas_{args.cultivo}.parquet")
    curvas["fecha"] = pd.to_datetime(curvas["fecha"])
    features = pd.read_parquet(OUT_DIR / f"features_{args.cultivo}.parquet")
    pred = pd.read_parquet(OUT_DIR / f"rendimiento_pred_{args.cultivo}.parquet").query(
        "modelo == @MODELO_WEB"
    )
    deptos = pd.read_parquet(OUT_DIR / f"departamentos_{args.region}.parquet").set_index("depto_id")
    geojson = json.loads((OUT_DIR / f"geometrias_{args.region}.geojson").read_text())

    decadas = etiquetas_decadas(curvas)
    anomalias = anomalias_por_decada(curvas)
    ndvi = curvas.pivot(index=["campania", "depto_id"], columns="decada", values="valor").reindex(
        columns=range(len(decadas))
    )
    anom = anomalias.pivot(
        index=["campania", "depto_id"], columns="decada", values="anomalia_pct"
    ).reindex(columns=range(len(decadas)))
    pron = pd.read_parquet(OUT_DIR / f"rendimiento_pronostico_{args.cultivo}.parquet").query(
        "modelo == @MODELO_WEB"
    )
    extra = (
        features.set_index(["campania", "depto_id"])["n_puntos"]
        .to_frame()
        .join(pd.concat([pred, pron]).set_index(["campania", "depto_id"])[["y", "base", "pred"]])
    )

    series: dict = {}
    for (campania, depto_id), fila in ndvi.iterrows():
        e = extra.loc[(campania, depto_id)] if (campania, depto_id) in extra.index else None
        series.setdefault(campania, {})[depto_id] = {
            "ndvi": redondear(fila, 3),
            "an": redondear(anom.loc[(campania, depto_id)], 1)
            if (campania, depto_id) in anom.index
            else [None] * len(decadas),
            "np": None if e is None else int(e["n_puntos"]),
            **(
                {}
                if e is None or pd.isna(e["pred"])
                else {"base": round(e["base"]), "pred": round(e["pred"])}
            ),
            **({} if e is None or pd.isna(e["y"]) else {"y": round(e["y"])}),
        }
    guardar_json(
        WEB / "static" / "data" / "monitor.json",
        {
            "cultivo": args.cultivo,
            "umbral": UMBRAL_ANOMALIA,
            "min_puntos": MIN_PUNTOS,
            "decadas": decadas,
            "campanias": sorted(series),
            "deptos": {i: {"n": d["depto"], "p": d["provincia"]} for i, d in deptos.iterrows()},
            "series": series,
        },
    )
    guardar_json(WEB / "static" / "data" / "deptos.geojson", geojson_liviano(geojson))

    # --- validación ---
    resumen = rendimiento.resumen_validacion(pred)
    peor = resumen["campania_peor"]
    dec_sequia = decadas.index(DECADA_SEQUIA)
    sequia = anomalias[(anomalias["campania"] == peor) & (anomalias["decada"] == dec_sequia)]
    real = pred.assign(real=pred["y"] / pred["base"] - 1).query("campania == @peor")
    por_campania = rendimiento.metricas(pred).drop(index="total")
    campanias = sorted(series)
    normal = campanias[campanias.index(peor) + 1] if peor != campanias[-1] else campanias[-1 - 1]
    h = {
        c: (
            features.query("depto_id == @HERO_DEPTO and campania == @c").iloc[0],
            pred.query("depto_id == @HERO_DEPTO and campania == @c").iloc[0],
        )
        for c in (peor, normal)
    }

    guardar_json(
        WEB / "src" / "lib" / "data" / "validacion.json",
        {
            "cultivo": args.cultivo,
            "generado": date.today().isoformat(),
            "umbral": UMBRAL_ANOMALIA,
            "acierto": [
                {
                    "decada": int(r["decada"]),
                    "fecha": decadas[int(r["decada"])],
                    **{
                        k: round(float(r[k]), 3)
                        for k in (
                            "marcados",
                            "acierto",
                            "acierto_sin_umbral",
                            "acierto_mala",
                            "acierto_buena",
                        )
                    },
                }
                for _, r in acierto_por_decada(anomalias, pred).iterrows()
            ],
            "modelo": {
                "nombre": MODELO_WEB,
                **{k: round(v, 3) if isinstance(v, float) else v for k, v in resumen.items()},
            },
            "por_campania": [
                {
                    "campania": c,
                    "rmse_modelo": round(r["rmse_modelo"]),
                    "rmse_base": round(r["rmse_base"]),
                    "mejora": round(100 * (1 - r["rmse_modelo"] / r["rmse_base"]), 1),
                }
                for c, r in por_campania.iterrows()
            ],
            "sequia": {
                "campania": peor,
                "fecha": DECADA_SEQUIA,
                "n_deptos": len(sequia),
                "deptos_en_rojo": round(
                    float((sequia["anomalia_pct"] < -UMBRAL_ANOMALIA).mean()), 3
                ),
                "deptos_bajo_lo_normal": round(float((real["real"] < 0).mean()), 3),
                "desvio_medio": round(float(real["real"].mean()), 3),
            },
            "hero": {
                "depto_id": HERO_DEPTO,
                "depto": deptos.loc[HERO_DEPTO, "depto"],
                "provincia": deptos.loc[HERO_DEPTO, "provincia"],
                **{
                    f"{k}_{tipo}": v
                    for tipo, c in (("mala", peor), ("normal", normal))
                    for k, v in (
                        ("campania", c),
                        ("rinde", int(h[c][1]["y"])),
                        ("base", int(h[c][1]["base"])),
                        ("pico", round(float(h[c][0]["pico"]), 2)),
                    )
                },
            },
        },
    )


if __name__ == "__main__":
    main()
