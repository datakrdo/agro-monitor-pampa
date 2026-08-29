# Agro Monitor Pampa 🌱🛰️

Sistema de monitoreo satelital de cultivos de **soja y trigo** en la Pampa húmeda argentina, con series históricas desde la campaña 2016/17. Procesamiento en la nube con Google Earth Engine, datos oficiales abiertos como referencia y dashboard interactivo en Streamlit.

Stack 100% gratuito y open source.

## Alcance

- **Región**: Pampa húmeda (norte de Buenos Aires, sur de Santa Fe, sur de Córdoba)
- **Resolución administrativa**: nivel departamental / partido
- **Cultivos**: soja y trigo (incluye detección de doble siembra trigo/soja)
- **Historia**: desde la campaña 2016/17 (Sentinel-2) con extensión histórica vía MODIS (2000+) y Landsat (1984+)

## Fuentes de datos

| Fuente | Uso | Acceso |
|---|---|---|
| Google Earth Engine | Sentinel-2 SR Harmonized (10 m, 2017+), MODIS MOD13Q1 (250 m, 2000+), Landsat 8/9 (30 m), ESA WorldCover (máscara de cultivo) | Gratuito uso no comercial |
| Estimaciones agrícolas (MAGyP) — datos.gob.ar | Superficie sembrada/cosechada, producción y rendimiento por cultivo, campaña y departamento. Serie de trigo desde 1923 | CSV + API de Series de Tiempo |
| CONAE — Geoportal / SAOCOM | Mapa de clasificación de cultivos (ground truth para validación), humedad de suelo, índice de producción | Geoportal libre |
| API Georef | Geometrías oficiales de provincias y departamentos | API REST |
| FAO GAUL 2015 nivel 2 | Límites departamentales dentro de GEE | Asset `FAO/GAUL/2015/level2` |

## Stack

- **Extracción**: `earthengine-api`, `geemap`, `eemont`
- **Procesamiento**: `pandas`, DuckDB / GeoParquet (fase 2)
- **Modelado**: scikit-learn / XGBoost sobre features fenológicos (fase 3)
- **Dashboard**: Streamlit + Plotly (entregable final)
- **Calidad**: pytest, GitHub Actions

## Estructura del repositorio

```
agro-monitor-pampa/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/                      # series extraídas (CSV)
│   └── processed/                # features y datasets modelados
├── notebooks/
│   └── 01_piloto_pergamino.py    # piloto NDVI/EVI — celdas # %% (VS Code / Jupytext)
├── src/
│   ├── gee/                      # extracción satelital (GEE)
│   ├── datos_gob/                # ingesta API estimaciones agrícolas
│   └── features/                 # features fenológicos
├── app/
│   └── streamlit_app.py          # dashboard (entregable final)
└── tests/
```

## Instalación

```bash
git clone <url-de-tu-repo>
cd agro-monitor-pampa
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

Requisito previo: cuenta registrada en [Google Earth Engine](https://earthengine.google.com) con un proyecto Cloud (uso no comercial).

## Uso — piloto NDVI/EVI

1. Abrí `notebooks/01_piloto_pergamino.py` en VS Code (se detecta como notebook por las celdas `# %%`).
2. Reemplazá `PROJECT_ID` por el ID de tu proyecto de Earth Engine (visible en el Code Editor de GEE).
3. Ejecutá las celdas: la primera vez se abre el navegador para el flujo OAuth.
4. Salida: `data/raw/ndvi_evi_pergamino_mensual.csv` con NDVI, EVI y cantidad de imágenes por mes desde junio de 2016.

> Nota: Sentinel-2 tiene cobertura plena sobre Argentina desde 2017. Los meses iniciales de la campaña 2016/17 pueden quedar vacíos; se completan con MODIS/Landsat en la fase 1.

## Roadmap

- [ ] **Fase 0 — Piloto**: serie NDVI/EVI mensual, Pergamino (BA) ✅ en curso
- [ ] **Fase 1 — Escalamiento**: todos los departamentos de la Pampa húmeda; backbone histórico MODIS (2000+) + Landsat 8
- [ ] **Fase 2 — Ground truth**: ingesta de estimaciones oficiales MAGyP vía API de datos.gob.ar, alineadas por campaña y departamento
- [ ] **Fase 3 — Clasificador**: features fenológicos (NDVI máx., fecha del pico, integral de curva) + Random Forest; validación contra mapa de cultivos CONAE
- [ ] **Fase 4 — Dashboard**: Streamlit con mapa interactivo, series por departamento y comparación modelo vs. estimaciones oficiales

## Licencia

MIT — ver archivo `LICENSE`.
