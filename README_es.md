🇬🇧 [English](README.md) · 🇪🇸 [Español](README_es.md)

# Agro Monitor Pampa 🌱🛰️

**¿Cómo viene hoy la campaña de soja en cada departamento frente a su historial a la misma fecha, y qué rendimiento anticipa?**

Dashboard de monitoreo en campaña para la pampa húmeda (152 departamentos con soja de Buenos Aires, Santa Fe y Córdoba), hecho con Sentinel-2 vía Copernicus Data Space. El sitio es estático (SvelteKit + MapLibre) y se publica gratis en Cloudflare Pages. Dos capas de respuesta:

- **Anomalía a la fecha** (alerta temprana, útil para seguros y bancos): la biomasa acumulada hasta hoy contra la misma fecha de las campañas anteriores del mismo departamento.
- **Rendimiento estimado con su error fuera de muestra** (útil para traders y consultoras): un modelo validado leave-one-campaign-out, siempre comparado contra una línea base honesta.

**[Ver demo en vivo →](https://agro-monitor-pampa.pages.dev)** _(deploy pendiente: ver [Fases](#fases-))_

## Herramientas 🛠️

- Python, pandas, scikit-learn (Ridge y gradient boosting, validación leave-one-campaign-out), SciPy, rasterio, geopandas
- openEO sobre Copernicus Data Space (Sentinel-2 L2A), Open-Meteo (ERA5), INTA MNC y MAGyP como fuentes
- SvelteKit 2 + Svelte 5, MapLibre GL, Observable Plot, vitest y Playwright
- uv, ruff, pytest, GitHub Actions, Cloudflare Pages

## Habilidades 🧠

- Teledetección operativa: máscaras de cultivo por campaña, series NDVI densas con nubes enmascaradas y suavizado Whittaker
- Validación honesta de modelos con pocos grupos (leave-one-campaign-out, línea base explícita, test anti-fuga, reporte de campañas donde pierde)
- Pipelines incrementales y reanudables bajo una cuota de cómputo (créditos CDSE)
- Sitio estático de datos: export reproducible, mapa interactivo, accesibilidad y CI de punta a punta

## Por qué está hecho así 🧭

- **Máscara de cultivo por campaña.** Se usa el Mapa Nacional de Cultivos (MNC) del INTA de cada año, no una máscara estática: la rotación soja/maíz cambia dónde hay soja cada campaña, y con una máscara fija el NDVI "de soja" queda contaminado.
- **Muestreo, no promedio del raster.** Se toman hasta ~300 píxeles de cultivo por departamento con semilla fija. Cuesta ~1000× menos cómputo, es reproducible y permite dar intervalos de confianza por bootstrap.
- **Serie densa y suavizada.** Mediana cada 10 días con nubes enmascaradas (SCL) y suavizado Whittaker, en vez de compuestos mensuales.
- **Validación sin fuga.** El modelo de rendimiento se valida dejando una campaña afuera; ni el modelo ni el promedio histórico de referencia ven la campaña evaluada. Hay un test que lo verifica.
- **Resultados negativos a la vista.** Si el modelo no le gana a la línea base, el dashboard lo dice.

## Cómo funciona 🏗️

1. **Muestreo** (`scripts/02_muestrear.py`): puntos de cultivo por departamento sobre el MNC de cada campaña.
2. **Extracción** (`scripts/04_extraer_cdse.py`, `src/agro/cdse.py`): grafo openEO en CDSE que calcula NDVI por década en cada punto. Es incremental y verifica si una campaña quedó descargada a medias, así que actualizar una campaña en curso solo pide lo que falta.
3. **Features** (`scripts/05_features.py`, `src/agro/fenologia.py`): suavizado Whittaker, integral, pico y fechas de cobertura y senescencia por depto, con IC 90% por bootstrap.
4. **Clima** (`scripts/06_clima.py`, `src/agro/clima.py`): lluvia, días de calor (Tmax > 32 °C) y balance hídrico de Open-Meteo (reanálisis ERA5).
5. **Modelo** (`scripts/07_rendimiento.py`, `src/agro/rendimiento.py`): Ridge y gradient boosting sobre el desvío de cada feature respecto de lo normal del departamento, contra el rendimiento oficial del MAGyP.
6. **Sitio** (`scripts/08_exportar_web.py`, `web/`): el export convierte los parquet de `data/processed/` en dos JSON y un GeoJSON; el sitio no calcula nada, solo los dibuja. No toca CDSE ni pide credenciales. Las imágenes del hero salen de `scripts/09_imagenes_hero.py` (una vez) y la miniatura para compartir de `scripts/10_og_image.py`.

## Fuentes de datos 📎

| Fuente | Uso | Acceso |
|---|---|---|
| Sentinel-2 L2A | NDVI a 10 m cada 10 días | Copernicus Data Space (openEO), cuenta gratuita |
| Mapa Nacional de Cultivos (INTA) | Máscara de cultivo por campaña, 2018/19–2024/25 (2025/26 usa provisoriamente la de 2024/25) | Zenodo |
| Estimaciones agrícolas (MAGyP) | Rendimiento oficial por cultivo × campaña × departamento | CKAN `datos.magyp.gob.ar` |
| Open-Meteo | Clima diario (ERA5) | API pública sin cuenta |
| IGN — departamentos | Polígonos oficiales; el código INDEC hace el join exacto con MAGyP | `ign_departamento.zip` |

Google Earth Engine (`src/agro/gee.py`, `scripts/02_extraer_series.py`) se conserva de la v1 para poder comparar las dos fuentes más adelante; el pipeline actual no lo usa. La v1 quedó bloqueada por la cuota mensual noncommercial de GEE, y CDSE la destrabó.

## Resultados 📊

Validación leave-one-campaign-out sobre 932 observaciones (137 departamentos, 7 campañas 2018/19–2024/25), contra el rinde departamental del MAGyP. La línea base es el promedio histórico del departamento sin la campaña evaluada.

| | RMSE modelo (Ridge) | RMSE modelo (HGB) | RMSE base | Mejora Ridge | Mejora HGB |
|---|---|---|---|---|---|
| Las 7 campañas | 444 kg/ha | 542 kg/ha | 680 kg/ha | 35% | 20% |
| Sin 2022/23 (sequía) | 404 kg/ha | 407 kg/ha | 484 kg/ha | 17% | 16% |

- **La sequía de 2022/23 pesa mucho.** El rinde medio cayó a 1.734 kg/ha (2.640–3.210 en las otras seis) y el promedio histórico predice 2.845, así que la base se equivoca por 1.352 kg/ha en esa campaña. El modelo la corrige parte del camino (RMSE de 633 con Ridge), pero sigue siendo su peor campaña. Con las siete campañas la mejora es de 35%; **sin esa campaña baja a 17%**, que es la cifra más honesta para un año normal. La mejora es sobre todo capacidad de detectar un año anómalo, no de afinar los años normales.
- **Con solo 7 campañas hay una única sequía.** No se puede saber si el modelo acierta en otras sequías o si aprendió la de 2022/23; con más años se revisaría.
- **Ridge le gana a HGB** con las 7 campañas; en años normales empatan.
- **No gana en todas las campañas.** Ridge le gana a la base en 5 de 7, empata en 2021/22 (327 contra 327) y pierde en 2024/25 (493 contra 416 kg/ha).

## Limitaciones ⚠️

- **Ventana de extracción.** En soja es noviembre–mayo: la integral no es la biomasa del ciclo completo, y lo que se mide es "cobertura" y "senescencia", no siembra ni madurez.
- **Pocas campañas.** Con 7 campañas la anomalía es una foto de baja potencia estadística: se reporta como diferencia contra la mediana histórica, no como z-score.
- **Campaña 2025/26, provisoria.** Es la campaña recién cerrada. El INTA todavía no publicó su MNC, así que se usó el de 2024/25 como máscara (`02_muestrear.py --mascara 2024`); cuando salga hay que borrar la campaña y re-extraerla entera, porque cambian los puntos. Además se extrajeron 115 de 152 departamentos (se acabaron los créditos de CDSE; el resto, el mes que viene). Su rinde es una **estimación sin contraste**: el modelo se entrena con las 7 campañas que tienen rinde MAGyP y predice 2025/26 en 102 departamentos (`rendimiento_pronostico_soja.parquet`), y el panel la marca como provisoria hasta que el MAGyP publique el dato oficial. No entra en las métricas de validación.
- **MNC 2018/19.** Es un mapa único con otra leyenda (soja de primera y de segunda; en trigo incluye cebada, avena y verdeos). Esa campaña es menos comparable.
- **Trigo.** La clase del MNC es "cereales de invierno" e incluye cebada. Hay estrategias propuestas para separarla (ver [Cebada: separarla del trigo](#cebada-separarla-del-trigo-propuesta-en-análisis)).
- **Campaña en curso.** Si el INTA todavía no publicó su MNC, la máscara es provisoria (píxeles que fueron del cultivo en campañas previas) y el dashboard la marca.
- **Alternativas.** Existen los mapas de CONAE con SAOCOM (píxel de 800 m, sin escala departamental) y el Mapa de Cultivos del Gobierno (NDVI por lote). Este proyecto apunta a la escala departamental con validación explícita contra el MAGyP.

## Estructura

```
agro-monitor-pampa/
├── web/                      # sitio estático (SvelteKit + MapLibre + Observable Plot)
├── config/
│   ├── cultivos.yaml         # ventana, clase MNC y excepciones por campaña
│   └── regiones.yaml         # provincias por región (vacío = todo el país)
├── src/agro/
│   ├── config.py             # carga/valida los YAML
│   ├── geometrias.py         # IGN SHP -> GeoJSON simplificado por región
│   ├── magyp.py              # ingesta CKAN de estimaciones agrícolas
│   ├── muestreo.py           # puntos de cultivo sobre el MNC
│   ├── cdse.py               # extracción S2 vía openEO, incremental
│   ├── fenologia.py          # Whittaker, features, IC por bootstrap
│   ├── anomalia.py           # campaña, anomalía y anomalía a la fecha
│   ├── clima.py              # Open-Meteo y features de ventana
│   ├── rendimiento.py        # modelo y validación leave-one-campaign-out
│   └── gee.py                # extracción GEE de la v1 (se conserva para comparar)
├── scripts/                  # 01 geometrías · 02 muestreo · 03 MAGyP · 04 extracción · 05 features · 06 clima · 07 modelo · 08 export al sitio · 09 imágenes del hero · 10 miniatura
├── data/processed/           # parquet/geojson del pipeline; el export al sitio los lee
├── data/raw/                 # MNC, salidas crudas de CDSE (no se commitean)
└── tests/
```

## Inicio rápido 🚀

Solo el sitio (sin credenciales ni Python: los datos ya están en `data/processed/`):

```bash
uv sync && uv run python scripts/08_exportar_web.py --cultivo soja   # genera los JSON del sitio
cd web && npm ci && npm run dev                                                                      # http://localhost:5173
```

`npm run build` deja el sitio estático en `web/build/`; `npm test` corre los tests unitarios (vitest) y de punta a punta (Playwright).

Pipeline completo (necesita una cuenta de [Copernicus Data Space](https://dataspace.copernicus.eu)):

```bash
uv sync
uv run python -c "import openeo; openeo.connect('openeo.dataspace.copernicus.eu').authenticate_oidc()"  # una vez
uv run python scripts/01_geometrias.py --region pampa-humeda
uv run python scripts/03_magyp.py --region pampa-humeda
uv run python scripts/02_muestrear.py --cultivo soja --campania 2024     # requiere el MNC en data/raw/mnc/
uv run python scripts/04_extraer_cdse.py --cultivo soja --campania 2024
uv run python scripts/05_features.py --cultivo soja
uv run python scripts/06_clima.py --cultivo soja --campanias 2018 2019 2020 2021 2022 2023 2024 2025   # pasar todas: reescribe el parquet
uv run python scripts/07_rendimiento.py --cultivo soja
```

**Costo de la extracción.** CDSE cobra créditos según el área × ventana temporal, no según el número de puntos. En la práctica son ~6 créditos por departamento y campaña (unos 1.000 por campaña de soja completa); el plan gratuito da una cuota mensual. La extracción es idempotente y reanudable: si se corta, se relanza y sigue donde quedó.

## Agregar un cultivo o una región

- **Región nueva:** una entrada en `config/regiones.yaml` con la lista de provincias (`[]` = todo el país) y correr el pipeline con `--region <nombre>`. Un cultivo puede fijar su región con `region:` en su entrada, y los scripts la toman de ahí.
- **Cultivo nuevo:** una entrada en `config/cultivos.yaml`, sin cambios de código. Los campos están documentados en el encabezado del archivo, y `src/agro/config.py` rechaza al cargar una entrada incompleta. Checklist, en este orden (lo gratis primero):
  1. **Máscara.** Confirmar en el `.qml` de cada campaña del MNC (Zenodo) el código del cultivo: la leyenda cambia entre campañas y 2018/19 usa otra (`mnc_clase_campania`). Los GeoTIFF no traen la leyenda embebida.
  2. **MAGyP.** Confirmar el nombre exacto en el CSV (`magyp_cultivo`) y que haya rendimiento por departamento.
  3. **Región.** Si el cultivo está fuera de BA/SF/Córdoba, agregar la región.
  4. **Ventanas.** `mes_*` (campaña) y `ext_mes_*` (extracción, la que paga créditos). Opcional: `tmax_calor` si el umbral de estrés térmico no es 32 °C.
  5. **Correr** `03` → `02` → `04` (primero con `--limite 1` para medir créditos) → `05` → `06` → `07`.

  **Cultivos previstos.** Están como entradas comentadas en `cultivos.yaml`, con cada dato incierto marcado como `VERIFICAR`:

  | Cultivo | MNC 2024/25 | Estrategia y riesgo |
  |---|---|---|
  | Maíz | verano, clase 10 | Una sola entrada con ventana larga (sep–jun, ~2× los créditos de la soja). Mezcla siembras tempranas y tardías. Mejora futura: separarlas con el mapa de estacionalidad del MNC o con k-means sobre la curva NDVI. |
  | Algodón | verano, clase 15 | Requiere una región nueva (NEA). No hay antecedentes de rendimiento por teledetección en Argentina. |
  | Papa | verano e invierno, clase 26 | Región nueva (sudeste bonaerense). Poca superficie: la mayoría de los departamentos quedarían bajo el mínimo de puntos. Hay que confirmar en qué mapa está. |
  | Arveja | invierno, clase 24 | Zona chica. Confirmar que el código exista en cada campaña. |
  | Cebada | dentro de "cereales de invierno" (16) | **No se suma por ahora.** El MNC no la separa del trigo; hay estrategias propuestas en análisis (ver [Cebada: separarla del trigo](#cebada-separarla-del-trigo-propuesta-en-análisis)). La bibliografía la separa con Sentinel-1 y Sentinel-2 solo a escala de partido ([Marini 2021](https://www.scielo.org.mx/scielo.php?pid=S0188-46112021000100109&script=sci_abstract)). |

  Referencia útil: [ML13-DEV/crops-yield-price-forecast](https://github.com/ML13-DEV/crops-yield-price-forecast) predice rendimiento por departamento con MAGyP y MODIS, con ventanas de floración y llenado por cultivo. No tiene licencia, así que se consulta como idea y no se copia código.

## Cebada: separarla del trigo (propuesta en análisis)

El MNC agrupa trigo, cebada, avena y centeno en "cereales de invierno", así que hoy la máscara de trigo incluye cebada. Hay un cliente con interés específico en cebada. Esta sección documenta el problema y las estrategias propuestas: **ninguna está implementada ni decidida**, y mientras tanto la cebada no se suma como cultivo.

**El problema, medido con el MAGyP** (superficie sembrada 2018/19–2024/25, departamentos de la pampa húmeda, CSV 2026-03):

- **Está concentrada.** El 96% de la cebada es de Buenos Aires. 25 departamentos reúnen el 80% del área y 40 reúnen el 90%.
- **La mezcla es grande.** En los 29 departamentos con 10.000 ha o más por año, la cebada es el 44% de trigo+cebada (de 19% a 66% según el departamento): la máscara de "cereales de invierno" es casi mitad cebada. Esa proporción cambia entre campañas dentro del mismo departamento (mediana de 21 puntos entre la más alta y la más baja), así que un factor fijo por departamento no alcanza.
- **La mezcla ya capta parte de la señal.** En esos 29 departamentos, el desvío del rinde de cebada y el del trigo (mismo departamento y campaña) correlacionan r = 0,81 (203 observaciones): una señal "de trigo" ya explicaría ~2/3 del desvío de la cebada. Separar apunta al resto, más la superficie y la fecha de cosecha. Es una cota heurística, no una medición del modelo.
- **Hay con qué validar.** El MAGyP trae superficie y rinde de "cebada total" por departamento y campaña. Desde 2016/17 no distingue cervecera de forrajera: esa diferencia no se puede validar, y tampoco se ve por satélite.
- **La ventana de trigo actual no alcanza.** `cultivos.yaml` extrae de agosto a noviembre (hasta el 30/11), antes de la senescencia final y la cosecha (diciembre), que es donde se nota el adelanto de la cebada. Hay que extenderla antes de extraer trigo.

**Qué dice la bibliografía**

- Trigo y cebada tienen perfiles muy parecidos y se confunden con pocas fechas ópticas ([Deep Resolution 3.0, 2025](https://doi.org/10.3390/rs17060957)). La cebada va 10–20 días adelante en un estudio de Europa central citado ahí, y el INASE habla de 10–15 días de adelanto en la cosecha en Argentina ([INASE](https://www.argentina.gob.ar/sites/default/files/if_sisa_cebada_20_21.pdf)).
- [Marini (2021)](https://www.scielo.org.mx/scielo.php?pid=S0188-46112021000100109&script=sci_abstract), Coronel Rosales (Buenos Aires): Random Forest con Sentinel-1 (VV, VH, coherencia y textura) más NDVI de Sentinel-2 llega a F1 de 87% en trigo y 89% en cebada. Es un solo partido y un clasificador supervisado, o sea que necesita lotes etiquetados.
- Con series de Sentinel-1 se ubica la espigazón de trigo y cebada de invierno con un error de ~3–6 días respecto de la fecha observada ([Remote Sensing, 2021](https://doi.org/10.3390/rs13245036)).
- Aprender un clasificador a partir de proporciones regionales de cultivos, sin etiquetas por píxel, está probado en Brasil con SAR y óptico ([Learning crop type mapping from regional label proportions](https://arxiv.org/pdf/2208.11607)). No encontramos código publicado.
- [WorldCereal](https://github.com/WorldCereal/worldcereal-classification) permite entrenar un cabezal propio de tipos de cultivo (CatBoost sobre embeddings de Presto) y correrlo en openEO de CDSE, pero necesita etiquetas. No encontramos un repositorio abierto que separe trigo y cebada en Argentina.

**Estrategias propuestas**

| # | Estrategia | Qué necesita | Notas |
|---|---|---|---|
| 1 | **Clasificador supervisado con Sentinel-1 + Sentinel-2** (Random Forest sobre curvas NDVI/NDRE y retrodispersión) | Lotes georreferenciados de cebada y trigo (cientos, de 2–3 campañas), del cliente o de una maltería | Mejor desempeño esperado (Marini). Exige pasar de NDVI a NDVI+NDRE+S1, y S1 todavía no está probado en el proyecto. |
| 2 | **Supervisión débil con las proporciones del MAGyP** | Nada nuevo | Variante simple: en cada departamento y campaña, ordenar los píxeles muestreados por fecha de senescencia y asignar a cebada el s% más temprano, con s = proporción de cebada del MAGyP. Variante fina: mezcla de 2–3 componentes (trigo, cebada, otros) sobre features fenológicas, con esa proporción como prior por departamento y campaña. Riesgos: avena y centeno forman un tercer grupo; trigos de ciclo y siembra distintos solapan la fecha de la cebada; en la campaña en curso no hay proporción oficial y se usaría la histórica. |
| 3 | **Más señal en la extracción de invierno** | Decidirlo antes de extraer trigo: todavía no hay nada extraído, así que no cuesta re-descargas | Ventana agosto–enero (`ext_mes_fin: 1`), NDRE además de NDVI (`INDICES_S2` en `cdse.py` ya lo soporta), S1 VH/VV opcional y compuestos de 5 días en lugar de 10 para ubicar la senescencia (verificar que no cambie el costo). |
| 4 | **Acotar a la zona cebadera** | Región con `deptos:` (ya implementado, ver `regiones.yaml`) | Los 40 departamentos del 90% de la cebada son el 41% del área de los 144 con cereales de invierno (~59% menos créditos); los 29 de 10.000 ha o más, el 28% (~72% menos). Son más grandes que el promedio, así que ahorran menos de lo que sugiere el conteo. |
| 5 | **Presto/WorldCereal con cabezal propio** | Etiquetas (las mismas de la estrategia 1) | No recomendado por ahora: más créditos y complejidad, y los modelos de fundación están fuera de alcance. |

Descartado: usar departamentos "puros" del norte como referencia de trigo, porque la fenología se corre semanas con la latitud.

**Cómo validar sin circularidad**

1. Proporción de cebada estimada, sin usar el prior, contra la del MAGyP, en departamentos y campañas que no se usaron para ajustar (correlación y RMSE).
2. Que la estimación siga la variación entre campañas dentro de cada departamento, no solo la geografía.
3. Rinde de cebada con el modelo leave-one-campaign-out, con y sin separar (contra la mezcla de cereales de invierno): ¿baja el RMSE?
4. Con etiquetas (estrategia 1): matriz de confusión por campaña.

**Secuencia propuesta**

1. **Experimento chico**, cuando termine la soja: 29 departamentos (10.000 ha o más de cebada por año) × 2 campañas, ventana agosto–enero, NDVI+NDRE. Costo estimado de ~550 créditos con NDVI y hasta ~700 con NDRE, a ~1,2–1,3 créditos por 1.000 km² de bbox con ventana de 5 meses (medido en soja; el trigo todavía no se extrajo y la banda extra no está medida). Criterio de éxito: correlación ≥ 0,7 entre la proporción estimada (sin prior) y la del MAGyP.
   **Resultado (2026-10-07): no pasa.** Se extrajeron los 29 departamentos en 2023/24 y 2024/25 (ago–ene, solo NDVI) y se estimó, por departamento y campaña, la fecha de senescencia de cada píxel (caída a la mitad de la amplitud tras el pico) y una mezcla de 2 gaussianas sobre esas fechas, sin usar el prior. La proporción de cebada estimada (peso del componente temprano) contra la del MAGyP da **r = −0,10** en las 58 combinaciones departamento-campaña (Spearman −0,08), y la fecha media de senescencia r = 0,12; dentro de cada departamento, r = −0,24. Lejos del 0,7 pedido. La proporción oficial varía de 0,15 a 0,71 (media 0,45), así que había señal que explicar. Es una prueba de una sola variante de la estrategia 2: no descarta la separación, pero con NDVI cada 10 días y una mezcla simple la fecha de senescencia no distingue cebada de trigo (avena, centeno y fechas de siembra distintas la ensucian). El código del experimento no se versionó.
2. Si pasa, extender a los 40 departamentos × 7 campañas: ~2.700 créditos con NDVI.
3. Una sola extracción de "cereales de invierno" alimenta trigo y cebada: la separación se hace después, en el paso de features (`scripts/05_features.py`), no en la extracción.

**Preguntas abiertas**

1. ¿El cliente puede aportar lotes georreferenciados de cebada y trigo? Con eso se pasa a la estrategia 1.
2. ¿Qué necesita: rinde, superficie, anomalía en campaña, fecha de cosecha o calidad maltera? La calidad (proteína, calibre) no se ve por satélite.
3. ¿Alcanza con el sur de Buenos Aires?

## Tests

```bash
uv run pytest
uv run ruff check src scripts tests
```

Cubre campaña y anomalía a la fecha, muestreo (puntos dentro de la clase, semilla fija), extracción incremental y detección de campañas parciales, Whittaker y fenología, clima, el modelo con el test de no-fuga y la validación que muestra el sitio (acierto por fecha y resumen del modelo). El sitio tiene tests unitarios de la clasificación y el formato, y uno de punta a punta con Playwright (el mapa dibuja, buscar un departamento actualiza el panel, el gráfico de acierto y las tablas alternativas existen). Corre sin red ni credenciales.

## Fases ✅

- [x] Config de cultivos/regiones, geometrías IGN con join INDEC exacto
- [x] Ingesta de estimaciones MAGyP
- [x] Muestreo sobre el MNC del INTA y extracción Sentinel-2 vía CDSE, incremental
- [x] Fenología, anomalía a la fecha, clima y modelo de rendimiento validado
- [x] Extracción completa de soja: 7 campañas (2018/19–2024/25) con ventana nov–may
- [ ] Soja 2025/26: 115 de 152 departamentos extraídos con máscara provisoria y rinde estimado; faltan 37 departamentos (créditos CDSE) y re-extraer con el MNC 2025/26 cuando el INTA lo publique
- [ ] Trigo: extracción completa (hoy solo el experimento chico de cebada: 29 deptos × 2023 y 2024, ago–ene)
- [x] Métricas finales del modelo con las 7 campañas (ver Resultados)
- [ ] Cebada: separarla del trigo (estrategias propuestas, en análisis)
- [ ] Workflow mensual de actualización de la campaña en curso (GitHub Actions)
- [x] Sitio estático (SvelteKit + MapLibre) que reemplaza al dashboard de Streamlit
- [ ] Deploy en Cloudflare Pages (`.github/workflows/deploy.yml`; faltan los secrets `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ACCOUNT_ID`)
- [ ] Humedad de suelo (NASA SMAP L4) como feature del modelo
- [ ] Comparación con la extracción vía GEE

## Fuera de alcance (deliberado)

- Clasificador propio de cultivos: se usa el MNC del INTA, un dataset publicado y validado.
- Foundation models o embeddings: el valor marginal no compensa el costo mientras el MNC cubre la máscara.
- Base de datos, API o Docker, y alertas por mail o Telegram (se agregan si un cliente las pide).

## Licencia

MIT — ver archivo `LICENSE`.
