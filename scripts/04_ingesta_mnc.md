# Ingesta del Mapa Nacional de Cultivos (INTA) — pendiente, con fallback activo

## Estado actual

La serie NDVI/EVI que consume el dashboard usa como máscara de cultivo
**`ESA/WorldCereal/2021/MODELS/v100`** (`temporarycrops` para soja,
`wintercereals` para trigo) combinada con la ventana estacional de
`config/cultivos.yaml`, no el Mapa Nacional de Cultivos (MNC) del
INTA. Esto era el fallback ya previsto en el plan original si la fase
de ingesta del MNC se trababa — se trabó, así que se siguió con el
fallback.

## Por qué no se hizo la ingesta

El MNC se publica en Zenodo (ej. `zenodo.org/records/17652712` para la
campaña 2024/25) como GeoTIFF de 30 m para todo el país. Desde este
entorno, tanto `curl` (probado con varios User-Agent) como `WebFetch`
no pudieron alcanzar Zenodo: 403 persistente vía API, 504 Gateway
Timeout vía la página del record. No es un problema de credenciales
de GEE ni del proyecto — es la red de este entorno la que no llega a
Zenodo.

## Costo de la máscara actual (WorldCereal + ventana estacional)

- **Ventaja:** disponible en GEE hoy, sin subir nada, sin permisos
  adicionales de Cloud Storage.
- **Limitación:** WorldCereal es un producto global (no calibrado
  específicamente para la pampa húmeda) y de una sola campaña (2021)
  reutilizada como máscara estática para todos los años — no capta
  rotación de cultivos entre campañas dentro de un mismo pixel. El
  MNC, en cambio, publica una máscara por campaña.
- La ventana estacional de `cultivos.yaml` compensa parte de esto:
  aunque la máscara no cambia año a año, el compuesto mensual sí se
  restringe al período agronómico de cada cultivo, así que un pixel
  de invierno-cereal enmascarado como trigo no puede colar señal de
  soja de verano ni viceversa.

## Cómo migrar al MNC más adelante (pasos, no ejecutados)

1. Descargar el GeoTIFF de la campaña deseada desde Zenodo (fuera de
   este entorno, donde la red sí llegue).
2. Recortar al bounding box de la región (`geometrias_{region}.geojson`)
   con `rasterio`/`gdalwarp` para no subir el ráster nacional completo.
3. Subir el recorte como asset de GEE: `earthengine upload image` (CLI)
   o `Assets > Upload` en el Code Editor, bajo
   `projects/satelite-agro/assets/mnc_{campania}`.
4. En `src/agro/gee.py`, agregar una función `mascara_cultivo_mnc(cultivo_cfg, campania)`
   análoga a `mascara_cultivo()` pero leyendo el asset subido y
   filtrando por el código de clase del MNC (no `classification == 100`
   de WorldCereal), y usarla en `tabla_campania()` cuando el asset de
   esa campaña exista, con el fallback a WorldCereal si no.
5. Repetir la extracción (`scripts/02_extraer_series.py`) y comparar
   la validación contra MAGyP (tab "Validación" del dashboard) antes/
   después — si la correlación no mejora, no vale la complejidad
   adicional de mantener dos máscaras.

No se agenda esto como trabajo activo: es documentación de la
limitación conocida y la salida, tal como preveía el plan original.
