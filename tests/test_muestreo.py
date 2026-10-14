import geopandas as gpd
import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box

from agro.muestreo import muestrear


def _raster_sintetico(path):
    # 10x10 píxeles de 0.1°: clase 11 en la mitad izquierda, 22 en la derecha.
    datos = np.full((10, 10), 22, dtype="uint8")
    datos[:, :5] = 11
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=from_origin(0, 10, 1, 1),
        nodata=255,
    ) as dst:
        dst.write(datos, 1)


def test_muestrear_puntos_dentro_de_la_clase_y_reproducibles(tmp_path):
    ruta = tmp_path / "mnc.tif"
    _raster_sintetico(ruta)
    deptos = gpd.GeoDataFrame({"depto_id": ["A"]}, geometry=[box(0, 0, 10, 10)], crs="EPSG:4326")

    p1 = muestrear(ruta, deptos, clase=11, n=20, seed=1)
    p2 = muestrear(ruta, deptos, clase=11, n=20, seed=1)

    assert len(p1) == 20
    assert (p1["lon"] < 5).all()  # solo la mitad de clase 11
    assert p1["n_pixeles_cultivo"].iloc[0] == 50
    assert p1.equals(p2)


def test_muestrear_depto_sin_cultivo_queda_afuera(tmp_path):
    ruta = tmp_path / "mnc.tif"
    _raster_sintetico(ruta)
    deptos = gpd.GeoDataFrame({"depto_id": ["B"]}, geometry=[box(6, 0, 10, 10)], crs="EPSG:4326")
    assert muestrear(ruta, deptos, clase=11, n=20).empty


def test_muestrear_acepta_varias_clases(tmp_path):
    ruta = tmp_path / "mnc.tif"
    _raster_sintetico(ruta)
    deptos = gpd.GeoDataFrame({"depto_id": ["A"]}, geometry=[box(0, 0, 10, 10)], crs="EPSG:4326")
    p = muestrear(ruta, deptos, clase=[11, 22], n=20, seed=1)
    assert p["n_pixeles_cultivo"].iloc[0] == 100
