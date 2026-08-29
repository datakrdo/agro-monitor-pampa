# %% [markdown]
# # Piloto — Series NDVI/EVI departamentales
# **Departamento:** Pergamino (Buenos Aires) · **Desde:** campaña 2016/17
# **Sensor:** Sentinel-2 SR Harmonized (cobertura plena sobre Argentina desde 2017)
#
# Requiere: `pip install -r requirements.txt` y cuenta activa en Google Earth Engine.
# En VS Code este archivo se abre como notebook interactivo (celdas `# %%`).

# %%
import os
import ee
import pandas as pd

PROJECT_ID = "REEMPLAZAR_CON_TU_PROJECT_ID"  # visible en https://code.earthengine.google.com
OUT_DIR = "data/raw"
ESCALA_M = 30  # bajar a 10 para máxima precisión (bastante más lento)

# %%
def init_gee(project_id: str) -> None:
    """Inicializa Earth Engine; abre el flujo OAuth del navegador la primera vez."""
    try:
        ee.Initialize(project=project_id)
    except ee.EEException:
        ee.Authenticate()
        ee.Initialize(project=project_id)

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
# ESA WorldCover 2021: clase 40 = cropland. Se usa para recortar la señal
# a píxeles agrícolas y evitar mezclar NDVI de monte, urbano o agua.
MASCARA_CULTIVOS = ee.Image("ESA/WorldCover/v200/2021").select("Map").eq(40)

def preparar_s2(img: ee.Image) -> ee.Image:
    """Enmascara nubes/sombras (banda SCL), agrega NDVI y EVI, recorta a cultivo."""
    scl = img.select("SCL")
    limpio = (
        scl.neq(3)    # sombra de nubes
        .And(scl.neq(8))    # nube, probabilidad media
        .And(scl.neq(9))    # nube, probabilidad alta
        .And(scl.neq(10))   # cirros
        .And(scl.neq(11))   # nieve/hielo
    )
    ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
    evi = img.expression(
        "2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))",
        {"NIR": img.select("B8"), "RED": img.select("B4"), "BLUE": img.select("B2")},
    ).rename("EVI")
    return img.updateMask(limpio).addBands([ndvi, evi]).updateMask(MASCARA_CULTIVOS)

# %%
def serie_mensual(region: ee.Geometry, inicio: str = "2016-06-01",
                  fin: "str | None" = None) -> pd.DataFrame:
    """Compuestos mensuales (mediana) de NDVI/EVI promediados sobre el departamento."""
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .map(preparar_s2)
    )
    meses = pd.date_range(inicio, fin or pd.Timestamp.today(), freq="MS")
    filas = []
    for i, m in enumerate(meses, start=1):
        m_fin = m + pd.offsets.MonthBegin(1)
        col_mes = s2.filterDate(m.strftime("%Y-%m-%d"), m_fin.strftime("%Y-%m-%d"))
        stats = (
            col_mes.median()
            .select(["NDVI", "EVI"])
            .reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=ESCALA_M,
                maxPixels=1e10,
                bestEffort=True,
            )
            .getInfo()
        )
        filas.append({
            "fecha": m.strftime("%Y-%m"),
            "ndvi": stats.get("NDVI"),
            "evi": stats.get("EVI"),
            "n_imagenes": col_mes.size().getInfo(),
        })
        print(f"{m:%Y-%m} listo ({i}/{len(meses)})   ", end="\r")
    return pd.DataFrame(filas)

# %%
if __name__ == "__main__":
    init_gee(PROJECT_ID)
    region = geometria_departamento("Pergamino", "Buenos Aires")
    df = serie_mensual(region)
    os.makedirs(OUT_DIR, exist_ok=True)
    salida = os.path.join(OUT_DIR, "ndvi_evi_pergamino_mensual.csv")
    df.to_csv(salida, index=False)
    print(f"\nGuardado: {salida} ({len(df)} meses)")
    print(df.dropna().tail(12))
