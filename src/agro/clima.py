"""Clima diario por departamento desde Open-Meteo (reanálisis ERA5, sin
cuenta) y features de la ventana crítica del cultivo."""

from __future__ import annotations

import time

import geopandas as gpd
import pandas as pd
import requests

URL = "https://archive-api.open-meteo.com/v1/archive"
VARIABLES = ["precipitation_sum", "temperature_2m_max", "et0_fao_evapotranspiration"]
TMAX_CALOR = 32.0  # °C; default (soja/trigo). Otros cultivos: `tmax_calor` en cultivos.yaml


def puntos_representativos(geometrias: gpd.GeoDataFrame) -> pd.DataFrame:
    """depto_id, lon, lat de un punto siempre dentro del departamento
    (el centroide puede caer afuera en polígonos irregulares)."""
    p = geometrias.to_crs("EPSG:4326").geometry.representative_point()
    return pd.DataFrame(
        {
            "depto_id": geometrias["depto_id"].to_numpy(),
            "lon": p.x.to_numpy(),
            "lat": p.y.to_numpy(),
        }
    )


def descargar(lon: float, lat: float, inicio: str, fin: str, reintentos: int = 8) -> pd.DataFrame:
    """Serie diaria: fecha, precipitation_sum (mm), temperature_2m_max (°C),
    et0_fao_evapotranspiration (mm)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": inicio,
        "end_date": fin,
        "daily": ",".join(VARIABLES),
        "timezone": "America/Argentina/Buenos_Aires",
    }
    for i in range(reintentos):
        r = requests.get(URL, params=params, timeout=60)
        if r.status_code != 429:
            r.raise_for_status()
            d = r.json()["daily"]
            return (
                pd.DataFrame(d)
                .rename(columns={"time": "fecha"})
                .assign(fecha=lambda x: pd.to_datetime(x["fecha"]))
            )
        time.sleep(60 * (i + 1))
    r.raise_for_status()


def tramos_faltantes(fechas: pd.Series, inicio, fin) -> list[tuple[str, str]]:
    """Tramos (desde, hasta, ambos inclusive) de [inicio, fin) que `fechas`
    todavía no cubre. Sin datos previos pide todo; si no, solo los extremos."""
    ini, ult = pd.Timestamp(inicio), pd.Timestamp(fin) - pd.Timedelta(days=1)
    f = lambda t: t.strftime("%Y-%m-%d")
    if fechas.empty:
        return [(f(ini), f(ult))]
    tramos = []
    if fechas.min() > ini:
        tramos.append((f(ini), f(fechas.min() - pd.Timedelta(days=1))))
    if fechas.max() < ult:
        tramos.append((f(fechas.max() + pd.Timedelta(days=1)), f(ult)))
    return tramos


def features_ventana(diario: pd.DataFrame, inicio, fin, tmax_calor: float = TMAX_CALOR) -> dict:
    """Features climáticas en [inicio, fin): lluvia acumulada, días de calor
    (Tmax > `tmax_calor`, 32 °C por defecto), balance hídrico (lluvia - ET0) y Tmax media. Con la ventana
    incompleta (campaña en curso) los acumulados son a la fecha, no comparables
    con campañas cerradas: `dias` permite detectarlo."""
    v = diario[(diario["fecha"] >= inicio) & (diario["fecha"] < fin)]
    return {
        "lluvia_mm": v["precipitation_sum"].sum(),
        "dias_calor": int((v["temperature_2m_max"] > tmax_calor).sum()),
        "balance_mm": (v["precipitation_sum"] - v["et0_fao_evapotranspiration"]).sum(),
        "tmax_media": v["temperature_2m_max"].mean(),
        "dias": len(v),
    }
