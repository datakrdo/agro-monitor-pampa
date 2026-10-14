🇬🇧 [English](README.md) · 🇪🇸 [Español](README_es.md)

# Agro Monitor Pampa 🌱🛰️

**How is this season's soybean crop doing today in each department compared with its history on the same date, and what yield does it anticipate?**

An in-season monitor for Argentina's humid Pampas (152 soybean departments in Buenos Aires, Santa Fe and Córdoba), built on Sentinel-2 through Copernicus Data Space. The site is static (SvelteKit + MapLibre) and hosted for free on Cloudflare Pages. It answers on two layers:

- **Anomaly to date** (early warning, useful for insurers and banks): biomass accumulated so far against the same date in previous campaigns of the same department.
- **Estimated yield with its out-of-sample error** (useful for traders and consultancies): a leave-one-campaign-out validated model, always compared against an honest baseline.

**[Live demo →](https://agro-monitor-pampa.pages.dev)** _(deploy pending: see [Phases](#phases-))_

## Tools 🛠️

- Python, pandas, scikit-learn (Ridge and gradient boosting, leave-one-campaign-out validation), SciPy, rasterio, geopandas
- openEO on Copernicus Data Space (Sentinel-2 L2A), Open-Meteo (ERA5), INTA MNC and MAGyP as sources
- SvelteKit 2 + Svelte 5, MapLibre GL, Observable Plot, vitest and Playwright
- uv, ruff, pytest, GitHub Actions, Cloudflare Pages

## Skills 🧠

- Operational remote sensing: per-campaign crop masks, dense NDVI series with cloud masking and Whittaker smoothing
- Honest model validation with few groups (leave-one-campaign-out, explicit baseline, anti-leakage test, reporting the campaigns where it loses)
- Incremental, resumable pipelines under a compute quota (CDSE credits)
- Static data site: reproducible export, interactive map, accessibility and end-to-end CI

## Design decisions 🧭

- **Crop mask per campaign.** The INTA National Crop Map (MNC) of each year, not a static mask: soybean/maize rotation changes where soybean grows each campaign, and a fixed mask contaminates the "soybean" NDVI.
- **Sampling, not raster averages.** Up to ~300 crop pixels per department with a fixed seed: ~1000× less compute, reproducible, and it allows bootstrap confidence intervals.
- **Dense, smoothed series.** A 10-day median with clouds masked (SCL) and Whittaker smoothing, instead of monthly composites.
- **Leakage-free validation.** The yield model is validated leaving one campaign out; neither the model nor the historical-mean baseline sees the evaluated campaign. A test checks it.
- **Negative results on display.** If the model does not beat the baseline, the site says so.

## How it works 🏗️

1. **Sampling** (`scripts/02_muestrear.py`): crop points per department over each campaign's MNC.
2. **Extraction** (`scripts/04_extraer_cdse.py`, `src/agro/cdse.py`): an openEO graph on CDSE computes NDVI per dekad at each point. It is incremental and detects half-downloaded campaigns, so updating a running campaign only requests what is missing.
3. **Features** (`scripts/05_features.py`, `src/agro/fenologia.py`): Whittaker smoothing, integral, peak and cover/senescence dates per department, with 90% bootstrap CIs.
4. **Weather** (`scripts/06_clima.py`, `src/agro/clima.py`): rainfall, hot days (Tmax > 32 °C) and water balance from Open-Meteo (ERA5 reanalysis).
5. **Model** (`scripts/07_rendimiento.py`, `src/agro/rendimiento.py`): Ridge and gradient boosting on each feature's deviation from the department's normal, against official MAGyP yield. It also estimates campaigns that have no official yield yet.
6. **Site** (`scripts/08_exportar_web.py`, `web/`): the export turns the parquet files in `data/processed/` into two JSON files and a GeoJSON; the site computes nothing, it only draws. It never touches CDSE or asks for credentials.

## Data sources 📎

| Source | Use | Access |
|---|---|---|
| Sentinel-2 L2A | NDVI at 10 m every 10 days | Copernicus Data Space (openEO), free account |
| National Crop Map (INTA) | Crop mask per campaign, 2018/19–2024/25 (2025/26 provisionally uses the 2024/25 one) | Zenodo |
| Agricultural estimates (MAGyP) | Official yield by crop × campaign × department | CKAN `datos.magyp.gob.ar` |
| Open-Meteo | Daily weather (ERA5) | Public API, no account |
| IGN — departments | Official polygons; the INDEC code gives an exact join with MAGyP | `ign_departamento.zip` |

Google Earth Engine (`src/agro/gee.py`) is kept from v1 to compare both sources later; the current pipeline does not use it. v1 was blocked by GEE's monthly noncommercial quota, and CDSE unblocked it.

## Results 📊

Leave-one-campaign-out validation on 932 observations (137 departments, 7 campaigns 2018/19–2024/25) against MAGyP departmental yield. The baseline is the department's historical mean without the evaluated campaign.

| | Model RMSE (Ridge) | Model RMSE (HGB) | Baseline RMSE | Ridge gain | HGB gain |
|---|---|---|---|---|---|
| All 7 campaigns | 444 kg/ha | 542 kg/ha | 680 kg/ha | 35% | 20% |
| Without 2022/23 (drought) | 404 kg/ha | 407 kg/ha | 484 kg/ha | 17% | 16% |

- **The 2022/23 drought weighs a lot.** Mean yield fell to 1,734 kg/ha (2,640–3,210 in the other six) and the historical mean predicts 2,845, so the baseline misses by 1,352 kg/ha. The model recovers part of the way (RMSE 633 with Ridge) but it is still its worst campaign. With all seven campaigns the gain is 35%; **without that campaign it drops to 17%**, the more honest figure for a normal year. The gain is mostly the ability to detect an anomalous year, not to fine-tune normal ones.
- **With only 7 campaigns there is a single drought.** We cannot tell whether the model gets other droughts right or just learned 2022/23.
- **Ridge beats HGB** over all 7 campaigns; in normal years they tie.
- **It does not win every campaign.** Ridge beats the baseline in 5 of 7, ties in 2021/22 (327 vs 327) and loses in 2024/25 (493 vs 416 kg/ha).

## Limitations ⚠️

- **Extraction window.** For soybean it is November–May: the integral is not the full-cycle biomass, and what is measured is "cover" and "senescence", not sowing or maturity.
- **Few campaigns.** With 7 campaigns the anomaly has low statistical power: it is reported as a difference against the historical median, not as a z-score.
- **Campaign 2025/26 is provisional.** INTA has not published its MNC yet, so the 2024/25 one was used as the mask (`02_muestrear.py --mascara 2024`); once it is out, the campaign must be deleted and re-extracted in full because the points change. Only 115 of 152 departments were extracted (CDSE credits ran out; the rest next month). Its yield is an **estimate with no benchmark**: the model is trained on the 7 campaigns that have MAGyP yield and predicts 2025/26 for 102 departments (`rendimiento_pronostico_soja.parquet`); the site flags it as provisional until MAGyP publishes the official figure. It is not part of the validation metrics.
- **MNC 2018/19.** A single map with a different legend (first- and second-crop soybean; in wheat it includes barley, oats and cover crops). That campaign is less comparable.
- **Wheat.** The MNC class is "winter cereals" and includes barley. Separating them is under analysis (details, strategies and a failed first experiment in the [Spanish README](README_es.md#cebada-separarla-del-trigo-propuesta-en-análisis)).
- **Running campaign.** If INTA has not published its MNC yet, the mask is provisional (pixels that held the crop in previous campaigns).
- **Alternatives.** CONAE's SAOCOM maps (800 m pixels, no departmental scale) and the Government's Crop Map (per-field NDVI) exist. This project targets the departmental scale with explicit validation against MAGyP.

## Structure

```
agro-monitor-pampa/
├── web/                      # static site (SvelteKit + MapLibre + Observable Plot)
├── config/
│   ├── cultivos.yaml         # window, MNC class and per-campaign exceptions
│   └── regiones.yaml         # provinces per region (empty = whole country)
├── src/agro/
│   ├── config.py             # loads/validates the YAML files
│   ├── geometrias.py         # IGN SHP -> simplified GeoJSON per region
│   ├── magyp.py              # CKAN ingestion of agricultural estimates
│   ├── muestreo.py           # crop points over the MNC
│   ├── cdse.py               # incremental S2 extraction via openEO
│   ├── fenologia.py          # Whittaker, features, bootstrap CIs
│   ├── anomalia.py           # campaign, anomaly and anomaly-to-date
│   ├── clima.py              # Open-Meteo and window features
│   ├── rendimiento.py        # model and leave-one-campaign-out validation
│   └── gee.py                # v1 GEE extraction (kept for comparison)
├── scripts/                  # 01 geometries · 02 sampling · 03 MAGyP · 04 extraction · 05 features · 06 weather · 07 model · 08 site export · 09 hero images · 10 share thumbnail
├── data/processed/           # pipeline parquet/geojson; the site export reads them
├── data/raw/                 # MNC, raw CDSE output (not committed)
└── tests/
```

## Quick start 🚀

Site only (no credentials, no extraction: the data is already in `data/processed/`):

```bash
uv sync && uv run python scripts/08_exportar_web.py --cultivo soja   # builds the site JSON
cd web && npm ci && npm run dev                                       # http://localhost:5173
```

`npm run build` leaves the static site in `web/build/`; `npm test` runs the unit (vitest) and end-to-end (Playwright) tests.

Full pipeline (needs a [Copernicus Data Space](https://dataspace.copernicus.eu) account):

```bash
uv sync
uv run python -c "import openeo; openeo.connect('openeo.dataspace.copernicus.eu').authenticate_oidc()"  # once
uv run python scripts/01_geometrias.py --region pampa-humeda
uv run python scripts/03_magyp.py --region pampa-humeda
uv run python scripts/02_muestrear.py --cultivo soja --campania 2024     # needs the MNC in data/raw/mnc/
uv run python scripts/04_extraer_cdse.py --cultivo soja --campania 2024
uv run python scripts/05_features.py --cultivo soja
uv run python scripts/06_clima.py --cultivo soja --campanias 2018 2019 2020 2021 2022 2023 2024 2025   # pass all: it rewrites the parquet
uv run python scripts/07_rendimiento.py --cultivo soja
```

**Extraction cost.** CDSE charges credits by area × time window, not by number of points: about 6 credits per department and campaign (~1,000 per full soybean campaign); the free plan gives a monthly quota. Extraction is idempotent and resumable: if it stops, rerun it and it continues where it left off.

**Adding a crop or a region.** A region is an entry in `config/regiones.yaml`; a crop is an entry in `config/cultivos.yaml` with no code changes (`src/agro/config.py` rejects incomplete entries). The checklist and the planned crops (maize, cotton, potato, pea, barley) are in the [Spanish README](README_es.md#agregar-un-cultivo-o-una-región).

## Tests

```bash
uv run pytest
uv run ruff check src scripts tests
```

Covers campaign and anomaly-to-date, sampling (points inside the class, fixed seed), incremental extraction and partial-campaign detection, Whittaker and phenology, weather, the model with the no-leakage test, and the validation the site shows. The site has unit tests for classification and formatting and an end-to-end Playwright test. It runs without network or credentials.

## Phases ✅

- [x] Crop/region config, IGN geometries with exact INDEC join
- [x] MAGyP estimates ingestion
- [x] Sampling over INTA's MNC and Sentinel-2 extraction through CDSE, incremental
- [x] Phenology, anomaly to date, weather and validated yield model
- [x] Full soybean extraction: 7 campaigns (2018/19–2024/25), Nov–May window
- [x] Final model metrics with the 7 campaigns (see Results)
- [x] Static site (SvelteKit + MapLibre) replacing the Streamlit dashboard
- [ ] Soybean 2025/26: 115 of 152 departments extracted with a provisional mask and an estimated yield; 37 departments missing (CDSE credits) and a full re-extraction with the 2025/26 MNC once INTA publishes it
- [ ] Wheat: full extraction (today only the small barley experiment: 29 departments × 2023 and 2024, Aug–Jan)
- [ ] Barley: separate it from wheat (strategies under analysis)
- [ ] Monthly refresh workflow for the running campaign (GitHub Actions)
- [ ] Deploy to Cloudflare Pages (`.github/workflows/deploy.yml`; the secrets `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` are missing)
- [ ] Soil moisture (NASA SMAP L4) as a model feature
- [ ] Comparison with the GEE extraction

## Out of scope (deliberately)

- Own crop classifier: INTA's MNC, a published and validated dataset, is used.
- Foundation models or embeddings: the marginal value does not justify the cost while the MNC covers the mask.
- Database, API or Docker, and email/Telegram alerts (added if a client asks).

## License

MIT — see the `LICENSE` file.
