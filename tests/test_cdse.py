import pandas as pd
import pytest

from agro import cdse

PUNTOS = pd.DataFrame({"lon": [-60.0, -60.1], "lat": [-33.0, -33.1]})


def _serie(fechas, valor):
    filas = [
        {
            "punto_idx": i,
            "fecha": pd.Timestamp(f),
            **{b: valor for b in cdse.INDICES_S2},
            "lon": PUNTOS.lon[i],
            "lat": PUNTOS.lat[i],
        }
        for i in range(2)
        for f in fechas
    ]
    return pd.DataFrame(filas)


def test_incremental_pide_desde_ultima_decada_y_la_reemplaza(tmp_path, monkeypatch):
    salida = tmp_path / "s.parquet"
    pedidos = []

    def falso_extraer(cubo, json_job):
        pedidos.append(cubo)
        return _serie(cubo, 0.9).drop(columns=["lon", "lat"])

    monkeypatch.setattr(
        cdse,
        "cubo_s2",
        lambda conn, p, ini, fin: (
            ["2025-01-11", "2025-01-21"] if ini == "2025-01-11" else ["2025-01-01", "2025-01-11"]
        ),
    )
    monkeypatch.setattr(cdse, "extraer", falso_extraer)

    cdse.extraer_incremental(None, PUNTOS, "2025-01-01", "2025-01-21", salida)  # primera vez: todo
    df = cdse.extraer_incremental(None, PUNTOS, "2025-01-01", "2025-02-01", salida)  # incremental

    assert pedidos[-1] == ["2025-01-11", "2025-01-21"]  # arrancó en la última década guardada
    assert sorted(df["fecha"].unique()) == [
        pd.Timestamp(f) for f in ("2025-01-01", "2025-01-11", "2025-01-21")
    ]
    assert not df.duplicated(["punto_idx", "fecha"]).any()


def test_incremental_no_llama_a_cdse_si_ya_esta_al_dia(tmp_path, monkeypatch):
    salida = tmp_path / "s.parquet"
    _serie(["2025-01-01", "2025-01-11", "2025-01-21"], 0.5).to_parquet(salida)
    monkeypatch.setattr(cdse, "cubo_s2", lambda *a: pytest.fail("no debía pedir nada"))
    assert len(cdse.extraer_incremental(None, PUNTOS, "2025-01-01", "2025-01-21", salida)) == 6


def test_incremental_rechaza_puntos_distintos(tmp_path):
    salida = tmp_path / "s.parquet"
    _serie(["2025-01-01"], 0.5).to_parquet(salida)
    otros = PUNTOS.assign(lon=[-61.0, -61.1])
    with pytest.raises(ValueError, match="puntos cambiaron"):
        cdse.extraer_incremental(None, otros, "2025-01-01", "2025-02-01", salida)


def test_estado_campania_detecta_bajada_parcial():
    completa = _serie(["2025-01-01", "2025-01-11", "2025-01-21"], 0.5)
    assert cdse.estado_campania(completa, "2025-01-01", "2025-02-01")["completa"]

    parcial = _serie(["2025-01-01", "2025-01-21"], 0.5)  # falta la del medio
    e = cdse.estado_campania(parcial, "2025-01-01", "2025-02-01")
    assert not e["completa"] and e["faltantes"] == [pd.Timestamp("2025-01-11")]
    assert not cdse.estado_campania(None, "2025-01-01", "2025-02-01")["completa"]


def test_estado_campania_separa_sin_dato_de_faltante():
    df = _serie(["2025-01-01", "2025-01-11"], 0.5)
    df.loc[df["fecha"] == "2025-01-11", cdse.INDICES_S2] = None  # década toda nublada
    e = cdse.estado_campania(df, "2025-01-01", "2025-01-21")
    assert e["completa"] and e["sin_dato"] == [pd.Timestamp("2025-01-11")]


def test_incremental_rellena_hueco_en_el_medio(tmp_path, monkeypatch):
    salida = tmp_path / "s.parquet"
    _serie(["2025-01-01", "2025-01-21"], 0.5).to_parquet(salida)  # se cortó: falta 01-11
    pedidos = []
    monkeypatch.setattr(cdse, "cubo_s2", lambda conn, p, ini, fin: pedidos.append(ini) or [ini])
    monkeypatch.setattr(
        cdse,
        "extraer",
        lambda cubo, j: _serie(["2025-01-11", "2025-01-21"], 0.9).drop(columns=["lon", "lat"]),
    )

    df = cdse.extraer_incremental(None, PUNTOS, "2025-01-01", "2025-02-01", salida)

    assert pedidos == ["2025-01-11"]
    assert cdse.estado_campania(df, "2025-01-01", "2025-02-01")["completa"]


def test_ampliar_ventana_hacia_atras_pide_solo_el_tramo_nuevo(tmp_path, monkeypatch):
    salida = tmp_path / "s.parquet"
    _serie(["2025-01-11", "2025-01-21"], 0.5).to_parquet(salida)  # ya bajado
    pedidos = []
    monkeypatch.setattr(
        cdse, "cubo_s2", lambda conn, p, ini, fin: pedidos.append((ini, fin)) or [ini]
    )
    monkeypatch.setattr(
        cdse, "extraer", lambda cubo, j: _serie(["2025-01-01"], 0.9).drop(columns=["lon", "lat"])
    )

    df = cdse.extraer_incremental(
        None, PUNTOS, "2025-01-01", "2025-02-01", salida
    )  # antes empezaba el 01-11

    assert pedidos == [("2025-01-01", "2025-01-11")]  # solo lo nuevo; no reextrae 01-11 ni 01-21
    assert sorted(df["fecha"].unique()) == [
        pd.Timestamp(f) for f in ("2025-01-01", "2025-01-11", "2025-01-21")
    ]
    assert (df[df["fecha"] == "2025-01-11"]["NDVI"] == 0.5).all()  # lo viejo quedó intacto
    assert cdse.estado_campania(df, "2025-01-01", "2025-02-01")["completa"]


def test_ampliar_ventana_a_ambos_lados_pide_dos_tramos(tmp_path, monkeypatch):
    salida = tmp_path / "s.parquet"
    _serie(["2025-01-11", "2025-01-21"], 0.5).to_parquet(salida)
    pedidos = []
    monkeypatch.setattr(
        cdse, "cubo_s2", lambda conn, p, ini, fin: pedidos.append((ini, fin)) or [ini]
    )
    monkeypatch.setattr(
        cdse,
        "extraer",
        lambda cubo, j: _serie(
            ["2025-01-01"] if cubo == ["2025-01-01"] else ["2025-01-21", "2025-02-01"], 0.9
        ).drop(columns=["lon", "lat"]),
    )

    df = cdse.extraer_incremental(None, PUNTOS, "2025-01-01", "2025-02-11", salida)

    assert pedidos == [("2025-01-01", "2025-01-11"), ("2025-01-21", "2025-02-11")]
    assert cdse.estado_campania(df, "2025-01-01", "2025-02-11")["completa"]
