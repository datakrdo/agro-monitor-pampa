"""Extracción de NDVI/EVI desde Sentinel-2 vía Google Earth Engine.

Usa `eemont` para el trabajo pesado: enmascarado de nubes
(Cloud Score+), escalado de reflectancia y cálculo de índices
espectrales con las fórmulas canónicas de Awesome Spectral Indices.
Sin `scaleAndOffset()` el EVI da valores sin sentido (~0.9 plano)
porque la reflectancia de Sentinel-2 SR viene ×10000 — ver el piloto
original en notebooks/ para el bug que esto reemplaza.

La máscara de cultivo es ESA WorldCereal 2021 (soja ~ temporarycrops,
trigo ~ wintercereals) en vez de un clasificador propio: es un dataset
publicado y validado, y separar soja/trigo con precisión de pixel no
es el problema que este proyecto resuelve.
"""

from __future__ import annotations

import ee
import eemont  # noqa: F401  (registra los métodos .maskClouds/.scaleAndOffset/.spectralIndices)
import geemap
import geopandas as gpd
import pandas as pd

BANDAS = ["NDVI", "EVI"]
WORLDCEREAL = "ESA/WorldCereal/2021/MODELS/v100"
S2 = "COPERNICUS/S2_SR_HARMONIZED"
ESCALA_M = 30  # suficiente para un promedio departamental; a 10-20m
# reduceRegions sobre una región de 3 provincias no termina.


def inicializar(project_id: str) -> None:
    try:
        ee.Initialize(project=project_id)
    except ee.EEException:
        ee.Authenticate()
        ee.Initialize(project=project_id)


def fc_departamentos(gdf: gpd.GeoDataFrame) -> ee.FeatureCollection:
    return geemap.geopandas_to_ee(gdf[["depto_id", "geometry"]])


def mascara_cultivo(cultivo_cfg: dict) -> ee.Image:
    wc = ee.ImageCollection(WORLDCEREAL).filter(
        ee.Filter.eq("product", cultivo_cfg["worldcereal_clase"])
    )
    return wc.mosaic().select("classification").eq(100)


def compuesto_mensual(roi: ee.Geometry, inicio: str, fin: str) -> ee.Image:
    """Mediana mensual de NDVI/EVI, nubes enmascaradas, reflectancia escalada."""
    return (
        ee.ImageCollection(S2)
        .filterBounds(roi)
        .filterDate(inicio, fin)
        .maskClouds(method="cloud_score+", prob=60)
        .scaleAndOffset()
        .spectralIndices(BANDAS)
        .median()
        .select(BANDAS)
    )


def _reducir_mes(
    roi: ee.Geometry, deptos_fc: ee.FeatureCollection, mascara: ee.Image, mes: pd.Timestamp
) -> ee.FeatureCollection:
    mes_fin = mes + pd.offsets.MonthBegin(1)
    imagen = compuesto_mensual(
        roi, mes.strftime("%Y-%m-%d"), mes_fin.strftime("%Y-%m-%d")
    ).updateMask(mascara)
    reducido = imagen.reduceRegions(
        collection=deptos_fc,
        reducer=ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True),
        scale=ESCALA_M,
        tileScale=4,
    )
    return reducido.map(lambda f: f.set("fecha", mes.strftime("%Y-%m-%d")))


def tabla_campania(
    deptos_fc: ee.FeatureCollection, cultivo_cfg: dict, inicio: pd.Timestamp, fin: pd.Timestamp
) -> ee.FeatureCollection:
    """Une los reduceRegions mensuales de una campaña en una sola
    FeatureCollection server-side (sin getInfo intermedios), lista
    para exportarse en una única tarea asíncrona.

    Un reduceRegions síncrono sobre toda la pampa húmeda (602.954 km²,
    179 deptos) excede el presupuesto de cómputo de ~5 min de la API
    síncrona a cualquier scale/tileScale probado — confirmado con
    pruebas reales. Por eso esto no llama .getInfo(): arma la
    colección y el caller la exporta con Export.table.toAsset.
    """
    roi = deptos_fc.geometry()
    mascara = mascara_cultivo(cultivo_cfg)
    meses = pd.date_range(inicio, fin, freq="MS", inclusive="left")
    tablas = [_reducir_mes(roi, deptos_fc, mascara, mes) for mes in meses]
    return ee.FeatureCollection(tablas).flatten()


def exportar_a_asset(fc: ee.FeatureCollection, asset_folder: str, nombre: str) -> ee.batch.Task:
    """Dispara una tarea de export asíncrona (Export.table.toAsset) y
    la devuelve sin esperarla — el caller la agrupa con otras y las
    poll-ea juntas (ver esperar_tareas)."""
    task = ee.batch.Export.table.toAsset(
        collection=fc, description=nombre, assetId=f"{asset_folder}/{nombre}"
    )
    task.start()
    return task


def esperar_tareas(tareas: dict[str, ee.batch.Task], intervalo_s: int = 20) -> dict[str, str]:
    """Bloquea hasta que todas las tareas terminan (COMPLETED/FAILED/
    CANCELLED). Devuelve {nombre: estado_final}. El proyecto está en
    modo restringido de cuota noncommercial, así que esto puede tardar
    bastante — se hace polling en vez de una espera fija."""
    import time

    pendientes = dict(tareas)
    finales: dict[str, str] = {}
    while pendientes:
        time.sleep(intervalo_s)
        for nombre, task in list(pendientes.items()):
            estado = task.status()["state"]
            if estado in ("COMPLETED", "FAILED", "CANCELLED"):
                finales[nombre] = estado
                del pendientes[nombre]
                print(f"{nombre}: {estado}")
    return finales


def leer_asset(asset_id: str) -> pd.DataFrame:
    filas = ee.FeatureCollection(asset_id).getInfo()["features"]
    df = pd.DataFrame([f["properties"] for f in filas])
    return df.rename(columns={"NDVI_mean": "ndvi", "EVI_mean": "evi", "NDVI_count": "n_pixeles"})
