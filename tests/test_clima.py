import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

from agro import clima


def test_features_ventana_solo_cuenta_la_ventana():
    fechas = pd.date_range("2025-01-01", "2025-01-10")
    d = pd.DataFrame(
        {
            "fecha": fechas,
            "precipitation_sum": 2.0,
            "temperature_2m_max": [30, 33, 35, 31, 32, 33, 20, 20, 20, 20],
            "et0_fao_evapotranspiration": 5.0,
        }
    )
    f = clima.features_ventana(d, "2025-01-01", "2025-01-07")  # fin exclusivo: 6 días
    assert f["dias"] == 6 and f["lluvia_mm"] == 12.0
    assert f["dias_calor"] == 3  # 33, 35, 33; el 32 exacto no cuenta
    assert f["balance_mm"] == 12.0 - 30.0


def test_punto_representativo_cae_dentro_de_un_poligono_concavo():
    u = Polygon(
        [(0, 0), (10, 0), (10, 10), (7, 10), (7, 3), (3, 3), (3, 10), (0, 10)]
    )  # U: el centroide cae afuera
    g = gpd.GeoDataFrame({"depto_id": ["A"]}, geometry=[u], crs="EPSG:4326")
    p = clima.puntos_representativos(g).iloc[0]
    from shapely.geometry import Point

    assert u.contains(Point(p["lon"], p["lat"]))


def test_tramos_faltantes_pide_solo_los_extremos():
    f = pd.Series(pd.date_range("2018-12-01", "2019-04-30"))
    assert clima.tramos_faltantes(f, "2018-11-01", "2019-06-01") == [
        ("2018-11-01", "2018-11-30"),
        ("2019-05-01", "2019-05-31"),
    ]
    assert clima.tramos_faltantes(f, "2018-12-01", "2019-05-01") == []
    assert clima.tramos_faltantes(
        pd.Series([], dtype="datetime64[ns]"), "2018-11-01", "2018-12-01"
    ) == [("2018-11-01", "2018-11-30")]


def test_features_ventana_umbral_de_calor_por_cultivo():
    d = pd.DataFrame(
        {
            "fecha": pd.date_range("2025-01-01", "2025-01-10"),
            "precipitation_sum": 0.0,
            "temperature_2m_max": 30.0,
            "et0_fao_evapotranspiration": 0.0,
        }
    )
    assert clima.features_ventana(d, "2025-01-01", "2025-01-11")["dias_calor"] == 0
    assert clima.features_ventana(d, "2025-01-01", "2025-01-11", tmax_calor=28)["dias_calor"] == 10
