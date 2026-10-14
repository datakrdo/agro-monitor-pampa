"""Muestreo de puntos de cultivo por departamento sobre el MNC del INTA.

En vez de reducir el raster completo (lo que agotó la cuota de GEE),
se toman ~N píxeles aleatorios de la clase del cultivo dentro de cada
departamento y se extraen series solo ahí. N=300 alcanza para estimar
la media departamental con error estándar despreciable, y permite dar
intervalos de confianza por bootstrap.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.warp import transform as warp_transform


def muestrear_departamento(
    src: rasterio.DatasetReader, geom, clase: int | list[int], n: int, rng: np.random.Generator
) -> pd.DataFrame:
    """Hasta `n` puntos (lon, lat) de píxeles de `clase` (código o lista de códigos) dentro de `geom`.

    `geom` ya debe estar en el CRS del raster. Devuelve además el total
    de píxeles de la clase, que sirve para ponderar por superficie.
    """
    datos, transf = rio_mask(src, [geom], crop=True, filled=True, nodata=255)
    filas, cols = np.nonzero(np.isin(datos[0], clase))
    total = len(filas)
    if total == 0:
        return pd.DataFrame(columns=["lon", "lat", "n_pixeles_cultivo"])
    idx = rng.choice(total, size=min(n, total), replace=False)
    xs, ys = rasterio.transform.xy(transf, filas[idx], cols[idx])
    lon, lat = warp_transform(src.crs, "EPSG:4326", xs, ys)
    return pd.DataFrame({"lon": lon, "lat": lat, "n_pixeles_cultivo": total})


def muestrear(
    raster_path, deptos: gpd.GeoDataFrame, clase: int | list[int], n: int = 300, seed: int = 42
) -> pd.DataFrame:
    """Puntos por departamento: depto_id, lon, lat, n_pixeles_cultivo.

    Semilla fija: la misma llamada devuelve los mismos puntos, así las
    series de distintas campañas se pueden reextraer y auditar.
    """
    rng = np.random.default_rng(seed)
    partes = []
    with rasterio.open(raster_path) as src:
        deptos = deptos.to_crs(src.crs)
        for depto_id, geom in zip(deptos["depto_id"], deptos.geometry):
            try:
                p = muestrear_departamento(src, geom, clase, n, rng)
            except ValueError:  # el departamento no intersecta el raster
                continue
            if not p.empty:
                partes.append(p.assign(depto_id=depto_id))
    columnas = ["depto_id", "lon", "lat", "n_pixeles_cultivo"]
    if not partes:
        return pd.DataFrame(columns=columnas)
    return pd.concat(partes, ignore_index=True)[columnas]
