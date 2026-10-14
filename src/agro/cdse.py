"""Extracción de series Sentinel-2 / Sentinel-1 sobre puntos vía openEO
del Copernicus Data Space Ecosystem (CDSE).

Todo el cómputo corre del lado del servidor: se manda un grafo, CDSE lo
procesa y devuelve solo los números por punto y por década (10 días).
Requiere haber autenticado una vez (`authenticate_oidc()`, el token
queda guardado localmente).
"""

from __future__ import annotations

import json
from pathlib import Path

import openeo
import pandas as pd
from openeo.processes import array_create, array_element, tanh

CDSE = "openeo.dataspace.copernicus.eu"
# SCL: 0 sin dato, 1 saturado, 3 sombra de nube, 8-9 nube media/alta, 10 cirro.
SCL_INVALIDO = (0, 1, 3, 8, 9, 10)
BANDAS_INDICE = {
    "NDVI": ["B04", "B08"],
    "EVI": ["B02", "B04", "B08"],
    "NDRE": ["B05", "B08"],
    "KNDVI": ["B04", "B08"],
}
INDICES_S2 = [
    "NDVI"
]  # los que extrae la corrida; ["NDVI", "EVI", "NDRE", "KNDVI"] pide todos (más bandas = más créditos)


def conectar() -> openeo.Connection:
    return openeo.connect(CDSE).authenticate_oidc_refresh_token()


def puntos_geojson(puntos: pd.DataFrame) -> dict:
    """FeatureCollection de puntos en el mismo orden que `puntos`
    (aggregate_spatial devuelve un resultado por feature, en orden)."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }
            for lon, lat in zip(puntos["lon"], puntos["lat"])
        ],
    }


def _bbox(puntos: pd.DataFrame, margen: float = 0.01) -> dict:
    return {
        "west": puntos["lon"].min() - margen,
        "east": puntos["lon"].max() + margen,
        "south": puntos["lat"].min() - margen,
        "north": puntos["lat"].max() + margen,
    }


def _formula(indice: str, d):
    """Fórmula de cada índice; `d` es el vector de bandas cargadas (reflectancia x10000)."""
    b = lambda n: array_element(d, label=n) / 10000
    ndvi = lambda: (b("B08") - b("B04")) / (b("B08") + b("B04"))
    return {
        "NDVI": ndvi,
        "EVI": lambda: 2.5 * (b("B08") - b("B04")) / (b("B08") + 6 * b("B04") - 7.5 * b("B02") + 1),
        "NDRE": lambda: (b("B08") - b("B05")) / (b("B08") + b("B05")),
        "KNDVI": lambda: tanh(
            ndvi() * ndvi()
        ),  # kNDVI (Camps-Valls 2021) con sigma = 0.5*(nir+rojo)
    }[indice]()


def mascara_nubes(s2, invalidos=SCL_INVALIDO, dilatar: int = 0):
    """`s2` (con la banda SCL) sin nubes, sombras ni cirros. `dilatar` ensancha
    la máscara esa cantidad de píxeles: los bordes de las nubes finas quedan
    clasificados como suelo o cultivo y manchan las imágenes en color."""
    scl = s2.band("SCL")
    invalido = scl == invalidos[0]
    for clase in invalidos[1:]:
        invalido = invalido | (scl == clase)
    if dilatar:
        lado = 2 * dilatar + 1
        invalido = (invalido * 1.0).apply_kernel([[1.0] * lado] * lado) > 0
    return s2.mask(invalido)


def cubo_s2(conn, puntos: pd.DataFrame, inicio: str, fin: str):
    """Mediana por década de los índices de `INDICES_S2` en cada punto, con
    nubes/sombras enmascaradas vía SCL. Solo se cargan las bandas que esos
    índices necesitan: el costo en CDSE es proporcional a los píxeles leídos."""
    bandas = sorted({b for i in INDICES_S2 for b in BANDAS_INDICE[i]})
    s2 = conn.load_collection(
        "SENTINEL2_L2A",
        spatial_extent=_bbox(puntos),
        temporal_extent=[inicio, fin],
        bands=bandas + ["SCL"],
    )
    indices = (
        mascara_nubes(s2)
        .apply_dimension(
            dimension="bands", process=lambda d: array_create([_formula(i, d) for i in INDICES_S2])
        )
        .rename_labels("bands", INDICES_S2)
    )
    return indices.aggregate_temporal_period("dekad", reducer="median").aggregate_spatial(
        geometries=puntos_geojson(puntos), reducer="mean"
    )


def extraer(cubo, salida: Path) -> pd.DataFrame:
    """Corre el grafo como batch job y lo deja en `salida` (JSON). Si ya
    existe, lo reusa: la extracción es idempotente. Devuelve una fila por
    (punto, década): punto_idx, fecha y una columna por banda."""
    salida = Path(salida)
    if not salida.exists():
        salida.parent.mkdir(parents=True, exist_ok=True)
        job = cubo.execute_batch(outputfile=salida, out_format="JSON", title=salida.stem)
        print("créditos:", job.describe().get("usage", {}).get("credits"))
    return _json_a_df(json.loads(salida.read_text()))


def _json_a_df(datos: dict) -> pd.DataFrame:
    """aggregate_spatial+JSON: {fecha: [[b1, b2, ...] por punto]}."""
    filas = []
    for fecha, por_punto in datos.items():
        for i, valores in enumerate(por_punto):
            filas.append(
                {
                    "punto_idx": i,
                    "fecha": pd.Timestamp(fecha).tz_localize(None),
                    **dict(zip(INDICES_S2, valores)),
                }
            )
    return pd.DataFrame(filas)


def _decadas(inicio, fin) -> pd.DatetimeIndex:
    """Inicios de década (días 1, 11 y 21) en [inicio, fin)."""
    dias = pd.date_range(inicio, fin, freq="D", inclusive="left")
    return dias[dias.day.isin([1, 11, 21])]


def estado_campania(previo: pd.DataFrame | None, inicio: str, fin: str) -> dict:
    """¿Está completa la bajada de la ventana inicio→fin? `faltantes` son
    décadas que nunca se guardaron (bajada cortada o parcial); `sin_dato`
    son décadas guardadas pero sin ningún valor (todo nube): esas no se
    arreglan volviendo a bajar."""
    esperadas = _decadas(inicio, fin)
    if previo is None or previo.empty:
        return {
            "completa": False,
            "esperadas": len(esperadas),
            "faltantes": list(esperadas),
            "sin_dato": [],
            "ultima": None,
        }
    presentes = pd.DatetimeIndex(previo["fecha"].unique())
    con_valor = previo.dropna(subset=INDICES_S2, how="all")["fecha"].unique()
    faltantes = esperadas.difference(presentes)
    return {
        "completa": len(faltantes) == 0,
        "esperadas": len(esperadas),
        "faltantes": list(faltantes),
        "sin_dato": list(presentes.difference(pd.DatetimeIndex(con_valor))),
        "ultima": presentes.max(),
    }


def _combinar(previo: pd.DataFrame, nuevo: pd.DataFrame) -> pd.DataFrame:
    """`nuevo` pisa a `previo` en el rango de fechas que cubre: la última
    década ya guardada pudo estar incompleta (nubes, imágenes tardías)."""
    fuera = (previo["fecha"] < nuevo["fecha"].min()) | (previo["fecha"] > nuevo["fecha"].max())
    return pd.concat([previo[fuera], nuevo], ignore_index=True).sort_values(
        ["punto_idx", "fecha"], ignore_index=True
    )


def _tramos_a_pedir(previo: pd.DataFrame, inicio: str, fin: str) -> list[tuple[str, str]]:
    """Ventanas [desde, hasta) que hay que pedir a CDSE. Una si no hay parquet
    previo. Con parquet: un tramo hacia atrás si la ventana se agrandó antes de
    lo guardado (solo el tramo nuevo, no todo) y un tramo hacia adelante desde
    el primer hueco o la última década guardada (que se reextrae)."""
    if previo is None:
        return [(inicio, fin)]
    dia = lambda ts: ts.strftime("%Y-%m-%d")
    primera, ultima = previo["fecha"].min(), previo["fecha"].max()
    faltantes = estado_campania(previo, inicio, fin)["faltantes"]
    antes = [f for f in faltantes if f < primera]
    despues = [f for f in faltantes if f >= primera]
    tramos = [(inicio, dia(primera))] if antes else []
    if (
        despues or pd.Timestamp(fin) > pd.Timestamp.today()
    ):  # campaña abierta: reextraer la última década
        tramos.append((dia(min(despues + [ultima])), fin))
    return tramos


def extraer_incremental(
    conn, puntos: pd.DataFrame, inicio: str, fin: str, salida: Path
) -> pd.DataFrame:
    """Serie por punto y década en el parquet `salida`, pidiendo a CDSE solo
    lo que falta (ver `_tramos_a_pedir`). Sin parquet previo baja todo
    `inicio`→`fin`. Los puntos deben ser los mismos que en la corrida
    anterior (mismo orden)."""
    salida = Path(salida)
    previo = pd.read_parquet(salida) if salida.exists() else None
    if previo is not None:
        guardados = previo.drop_duplicates("punto_idx").set_index("punto_idx")[["lon", "lat"]]
        actuales = puntos[["lon", "lat"]].reset_index(drop=True)
        if (
            len(guardados) != len(actuales)
            or not (guardados.to_numpy() == actuales.to_numpy()).all()
        ):
            raise ValueError(
                f"Los puntos cambiaron respecto de {salida}: no se puede extender incrementalmente."
            )

    coords = puntos[["lon", "lat"]].reset_index(drop=True).rename_axis("punto_idx").reset_index()
    resultado = previo
    for desde, hasta in _tramos_a_pedir(previo, inicio, fin):
        json_job = (
            salida.parent / f"{salida.stem}_{desde}_{hasta}.json"
        )  # incluye el rango: un job viejo no se reusa
        nuevo = extraer(cubo_s2(conn, puntos, desde, hasta), json_job).merge(coords, on="punto_idx")
        resultado = nuevo if resultado is None else _combinar(resultado, nuevo)
        resultado.to_parquet(salida, index=False)  # guarda tramo a tramo: si se corta, reanuda
    return previo if resultado is None else resultado
