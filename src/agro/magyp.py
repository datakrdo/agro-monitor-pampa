"""Ingesta de las Estimaciones Agrícolas del MAGyP (datos.gob.ar).

El CSV trae `departamento_id` con código INDEC de 5 dígitos: el mismo
que usa el IGN en `IN1` (ver geometrias.py), así que el join contra las
geometrías o las series satelitales es directo, sin normalizar
nombres.
"""

from __future__ import annotations

import pandas as pd
import requests

CKAN_PACKAGE_URL = "https://datos.magyp.gob.ar/api/3/action/package_show?id=estimaciones-agricolas"


def url_csv_actual() -> str:
    """Resuelve la URL del CSV vigente vía CKAN (el nombre de archivo
    lleva la fecha de la última actualización y cambia con el tiempo)."""
    resp = requests.get(CKAN_PACKAGE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    for recurso in resp.json()["result"]["resources"]:
        if recurso["format"] == "CSV" and "estimaciones-agricolas" in recurso["url"]:
            return recurso["url"]
    raise RuntimeError("No se encontró el CSV de estimaciones agrícolas en el paquete CKAN")


def cargar_estimaciones(
    csv_path_o_url: str, cultivo_magyp: str, depto_ids: set[str] | None = None
) -> pd.DataFrame:
    """Filtra el CSV completo (~160k filas, todos los cultivos y
    departamentos del país desde 1969) a un solo cultivo, opcionalmente
    restringido a una región vía `depto_ids`.

    Devuelve: depto_id, campania, rendimiento_kgxha, superficie_sembrada_ha, produccion_tm.
    """
    df = pd.read_csv(csv_path_o_url, dtype={"departamento_id": str}, low_memory=False)
    df["departamento_id"] = df["departamento_id"].str.zfill(5)
    df = df[df["cultivo"] == cultivo_magyp]
    if depto_ids is not None:
        df = df[df["departamento_id"].isin(depto_ids)]
    return df.rename(columns={"departamento_id": "depto_id"})[
        ["depto_id", "campania", "superficie_sembrada_ha", "produccion_tm", "rendimiento_kgxha"]
    ].reset_index(drop=True)
