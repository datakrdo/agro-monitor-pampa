"""Geometrías departamentales oficiales (IGN) filtradas por región.

El shapefile del IGN no trae el nombre de provincia por depto, pero el
código INDEC (campo IN1) sí lo codifica en sus dos primeros dígitos —
igual que el `departamento_id` del CSV de MAGyP, lo que permite el
join sin fuzzy matching. La tabla de provincias se resuelve una vez
contra la API de Georef en lugar de hardcodear los 24 códigos a mano.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import requests

IGN_URL = "http://www.ign.gob.ar/descargas/geodatos/SHAPES/ign_departamento.zip"
GEOREF_PROVINCIAS_URL = "https://apis.datos.gob.ar/georef/api/provincias?max=30&campos=id,nombre"

# Tolerancia de simplificación en grados (~1km) para que el GeoJSON
# de la coropleta cargue liviano en el navegador.
TOLERANCIA_SIMPLIFICACION = 0.005


def tabla_provincias() -> dict[str, str]:
    """id INDEC (2 dígitos) -> nombre de provincia."""
    resp = requests.get(GEOREF_PROVINCIAS_URL, timeout=30)
    resp.raise_for_status()
    return {p["id"]: p["nombre"] for p in resp.json()["provincias"]}


def cargar_departamentos(shp_path: str | Path) -> gpd.GeoDataFrame:
    """Lee el shapefile del IGN y devuelve depto_id/depto/provincia/geometry."""
    gdf = gpd.read_file(shp_path)
    provincias = tabla_provincias()
    gdf["depto_id"] = gdf["IN1"].astype(str).str.zfill(5)
    gdf["provincia"] = gdf["depto_id"].str[:2].map(provincias)
    gdf["depto"] = gdf["NAM"]
    # El shapefile trae Z=0 espurio en cada vértice; GEE rechaza coordenadas
    # 3D como GeoJSON inválido, así que se aplana antes de usarlas.
    gdf["geometry"] = gdf.geometry.force_2d()
    return gdf[["depto_id", "depto", "provincia", "geometry"]]


def filtrar_region(gdf: gpd.GeoDataFrame, region_cfg: dict) -> gpd.GeoDataFrame:
    """region_cfg['provincias'] vacío = todo el país. `deptos` (opcional, códigos
    INDEC de 5 dígitos) acota además a esos departamentos."""
    provincias = region_cfg["provincias"]
    if provincias:
        gdf = gdf[gdf["provincia"].isin(provincias)]
    if region_cfg.get("deptos"):
        gdf = gdf[gdf["depto_id"].isin(region_cfg["deptos"])]
    return gdf.copy()


def geojson_simplificado(gdf: gpd.GeoDataFrame) -> dict:
    """GeoJSON liviano para el mapa (coropleta)."""
    simplificado = gdf.copy()
    simplificado["geometry"] = simplificado.geometry.simplify(TOLERANCIA_SIMPLIFICACION)
    return simplificado.__geo_interface__
