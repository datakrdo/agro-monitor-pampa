"""Carga de config/*.yaml. Sin clases: los YAML ya son la fuente de
verdad, esto solo los resuelve a rutas absolutas y valida lo mínimo
para fallar temprano si falta un campo.
"""

from __future__ import annotations

from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
CONFIG_DIR = RAIZ / "config"

# worldcereal_clase es opcional: solo lo usa gee.py (v1). Opcionales: region, tmax_calor,
# mnc_clase_campania, notas (ver el encabezado de cultivos.yaml).
_CAMPOS_CULTIVO = {
    "nombre",
    "mes_inicio",
    "mes_fin",
    "cruza_anio",
    "ext_mes_inicio",
    "ext_mes_fin",
    "mnc_estacion",
    "mnc_clase",
    "magyp_cultivo",
}
_CAMPOS_REGION = {"nombre", "provincias"}


def cargar_cultivos() -> dict:
    """cultivo_id -> dict de configuración (ver config/cultivos.yaml)."""
    datos = yaml.safe_load((CONFIG_DIR / "cultivos.yaml").read_text())
    for cultivo_id, cfg in datos.items():
        faltan = _CAMPOS_CULTIVO - cfg.keys()
        if faltan:
            raise ValueError(f"cultivos.yaml/{cultivo_id}: faltan campos {faltan}")
        if cfg["mnc_estacion"] not in ("verano", "invierno"):
            raise ValueError(
                f"cultivos.yaml/{cultivo_id}: mnc_estacion debe ser 'verano' o 'invierno'"
            )
    return datos


def cargar_regiones() -> dict:
    """region_id -> dict de configuración (ver config/regiones.yaml)."""
    datos = yaml.safe_load((CONFIG_DIR / "regiones.yaml").read_text())
    for region_id, cfg in datos.items():
        faltan = _CAMPOS_REGION - cfg.keys()
        if faltan:
            raise ValueError(f"regiones.yaml/{region_id}: faltan campos {faltan}")
    return datos


def cultivo(cultivo_id: str) -> dict:
    cultivos = cargar_cultivos()
    if cultivo_id not in cultivos:
        raise KeyError(
            f"Cultivo '{cultivo_id}' no está en cultivos.yaml. Opciones: {sorted(cultivos)}"
        )
    return cultivos[cultivo_id]


def region(region_id: str) -> dict:
    regiones = cargar_regiones()
    if region_id not in regiones:
        raise KeyError(
            f"Región '{region_id}' no está en regiones.yaml. Opciones: {sorted(regiones)}"
        )
    return regiones[region_id]
