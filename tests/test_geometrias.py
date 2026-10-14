import geopandas as gpd
from shapely.geometry import Point

from agro.geometrias import filtrar_region


def _gdf():
    return gpd.GeoDataFrame(
        {
            "depto_id": ["06623", "82014", "14007"],
            "depto": ["Pergamino", "Belgrano", "Colón"],
            "provincia": ["Buenos Aires", "Santa Fe", "Córdoba"],
            "geometry": [Point(0, 0), Point(1, 1), Point(2, 2)],
        },
        crs="EPSG:4326",
    )


def test_filtrar_region_por_provincias():
    gdf = _gdf()
    out = filtrar_region(gdf, {"provincias": ["Buenos Aires", "Santa Fe"]})
    assert set(out["depto_id"]) == {"06623", "82014"}


def test_filtrar_region_acota_por_deptos():
    out = filtrar_region(_gdf(), {"provincias": ["Buenos Aires", "Santa Fe"], "deptos": ["82014"]})
    assert set(out["depto_id"]) == {"82014"}


def test_filtrar_region_vacia_es_todo_el_pais():
    gdf = _gdf()
    out = filtrar_region(gdf, {"provincias": []})
    assert len(out) == len(gdf)
