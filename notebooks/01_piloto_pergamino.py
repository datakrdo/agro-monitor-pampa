 # Piloto — Series NDVI/EVI departamentales
# **Departamento:** Pergamino (Buenos Aires) · **Desde:** campaña 2016/17
# **Sensor:** Sentinel-2 SR Harmonized (cobertura plena sobre Argentina desde 2017)
#
# Piloto original del proyecto. Reescrito para usar `src/agro/gee.py`
# (compuestos mensuales vía `eemont`) en vez de duplicar la lógica de
# nubes/índices a mano: la versión anterior calculaba EVI sobre
# reflectancia sin escalar (Sentinel-2 SR viene ×10000) y daba
# ~0.88-0.99 constante, sin sentido físico. `eemont.scaleAndOffset()`
# lo corrige gratis.
#
# Requiere: `pip install -e . -r requirements-pipeline.txt` y cuenta
# activa en Google Earth Engine. En VS Code este archivo se abre como
# notebook interactivo (celdas `# %%`).

# %%
import os
import sys

import ee
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from agro import gee  # noqa: E402  (después del sys.path.insert)

PROJECT_ID = "satelite-agro"  # visible en https://code.earthengine.google.com
OUT_DIR = "data/raw"

# %% [markdown]
# La inicialización (`gee.inicializar`) y los compuestos mensuales
# (`gee.compuesto_mensual`, con enmascarado de nubes + escalado de
# reflectancia + índices espectrales vía `eemont`) ya viven en
# `src/agro/gee.py` — este piloto solo agrega la geometría de un único
# departamento y el loop mes a mes.

# %%
gee.inicializar(PROJECT_ID)

# %%
def geometria_departamento(dep: str, prov: str) -> ee.Geometry:
    """Límite departamental (partido/departamento) desde FAO GAUL 2015 nivel 2."""
    gaul = ee.FeatureCollection("FAO/GAUL/2015/level2")
    seleccion = gaul.filter(
        ee.Filter.And(
            ee.Filter.eq("ADM0_NAME", "Argentina"),
            ee.Filter.eq("ADM1_NAME", prov),
            ee.Filter.eq("ADM2_NAME", dep),
        )
    )
    if seleccion.size().getInfo() == 0:
        disponibles = (
            gaul.filter(ee.Filter.eq("ADM1_NAME", prov))
            .aggregate_array("ADM2_NAME")
            .getInfo()
        )
        raise ValueError(f"'{dep}' no encontrado en {prov}. Opciones: {sorted(disponibles)}")
    return seleccion.geometry()

# %%
def serie_mensual(region: ee.Geometry, inicio: str = "2016-06-01",
                  fin: "str | None" = None) -> pd.DataFrame:
    """Compuestos mensuales (mediana) de NDVI/EVI promediados sobre el departamento.

    Meses sin imágenes (p. ej. previos a la cobertura de Sentinel-2) quedan
    con NDVI/EVI vacíos y n_imagenes = 0, en lugar de fallar: la mediana de
    una colección vacía es una imagen sin bandas y no se puede reducir.
    """
    meses = pd.date_range(inicio, fin or pd.Timestamp.today(), freq="MS")
    filas = []
    for i, m in enumerate(meses, start=1):
        m_fin = m + pd.offsets.MonthBegin(1)
        n = (
            ee.ImageCollection(gee.S2)
            .filterBounds(region)
            .filterDate(m.strftime("%Y-%m-%d"), m_fin.strftime("%Y-%m-%d"))
            .size()
            .getInfo()
        )
        ndvi = evi = None
        if n > 0:
            compuesto = gee.compuesto_mensual(region, m.strftime("%Y-%m-%d"), m_fin.strftime("%Y-%m-%d"))
            stats = compuesto.reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region,
                scale=gee.ESCALA_M, maxPixels=1e10, bestEffort=True,
            ).getInfo()
            ndvi, evi = stats.get("NDVI"), stats.get("EVI")
        filas.append({
            "fecha": m.strftime("%Y-%m"),
            "ndvi": ndvi,
            "evi": evi,
            "n_imagenes": n,
        })
        print(f"{m:%Y-%m} listo ({i}/{len(meses)})   ", end="\r")
    return pd.DataFrame(filas)

# %%
if __name__ == "__main__":
    region = geometria_departamento("Pergamino", "Buenos Aires")
    df = serie_mensual(region)
    os.makedirs(OUT_DIR, exist_ok=True)
    salida = os.path.join(OUT_DIR, "ndvi_evi_pergamino_mensual.csv")
    df.to_csv(salida, index=False)
    print(f"\nGuardado: {salida} ({len(df)} meses)")
    print(df.dropna().tail(12))
