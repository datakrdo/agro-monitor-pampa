import pytest
import yaml

from agro import config


def test_cultivos_reales_cargan():
    assert {"soja", "trigo"} <= set(config.cargar_cultivos())


def test_cultivo_sin_campo_obligatorio_falla(tmp_path, monkeypatch):
    cfg = yaml.safe_load((config.CONFIG_DIR / "cultivos.yaml").read_text())["soja"]
    del cfg["mnc_clase"]
    (tmp_path / "cultivos.yaml").write_text(yaml.safe_dump({"maiz": cfg}))
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    with pytest.raises(ValueError, match="mnc_clase"):
        config.cargar_cultivos()


def test_mnc_estacion_invalida_falla(tmp_path, monkeypatch):
    cfg = yaml.safe_load((config.CONFIG_DIR / "cultivos.yaml").read_text())["soja"] | {
        "mnc_estacion": "otoño"
    }
    (tmp_path / "cultivos.yaml").write_text(yaml.safe_dump({"maiz": cfg}))
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    with pytest.raises(ValueError, match="mnc_estacion"):
        config.cargar_cultivos()
