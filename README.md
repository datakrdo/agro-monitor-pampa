🇬🇧 [English](README.md) · 🇪🇸 [Español](README_es.md)

# Agro Monitor Pampa 🌱🛰️

**How is this season's soybean crop doing today in each department compared with its history on the same date, and what yield does it anticipate?**

An in-season monitor for Argentina's humid Pampas (152 soybean departments in Buenos Aires, Santa Fe and Córdoba), built on Sentinel-2 through Copernicus Data Space. The site is static (SvelteKit + MapLibre) and hosted for free on Cloudflare Pages. It answers on two layers:

- **Anomaly to date** (early warning, useful for insurers and banks): biomass accumulated so far against the same date in previous campaigns of the same department.
- **Estimated yield with its out-of-sample error** (useful for traders and consultancies): a leave-one-campaign-out validated model, always compared against an honest baseline.

**[Live demo →](https://agro-monitor-pampa.pages.dev)** · [English version](https://agro-monitor-pampa.pages.dev/en/) · [versión en español](https://agro-monitor-pampa.pages.dev)

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

## Design decisions 🧭

- **Crop mask per campaign.** The INTA National Crop Map (MNC) of each year, not a static mask: soybean/maize rotation changes where soybean grows each campaign, and a fixed mask contaminates the "soybean" NDVI.
- **Sampling, not raster averages.** Up to ~300 crop pixels per department with a fixed seed: ~1000× less compute, reproducible, and it allows bootstrap confidence intervals.
- **Dense, smoothed series.** A 10-day median with clouds masked (SCL) and Whittaker smoothing, instead of monthly composites.
- **Leakage-free validation.** The yield model is validated leaving one campaign out; neither the model nor the historical-mean baseline sees the evaluated campaign. A test checks it.
- **Negative results on display.** If the model does not beat the baseline, the site says so.

## Tools 🛠️

- Python, pandas, scikit-learn (Ridge and gradient boosting, leave-one-campaign-out validation), SciPy, rasterio, geopandas
- openEO on Copernicus Data Space (Sentinel-2 L2A), Open-Meteo (ERA5), INTA MNC and MAGyP as sources
- SvelteKit 3 + Svelte 5, MapLibre GL, Observable Plot, vitest and Playwright
- uv, ruff, pytest, GitHub Actions, Cloudflare Pages

## Skills 🧠

- Operational remote sensing: per-campaign crop masks, dense NDVI series with cloud masking and Whittaker smoothing
- Honest model validation with few groups (leave-one-campaign-out, explicit baseline, anti-leakage test, reporting the campaigns where it loses)
- Incremental, resumable pipelines under a compute quota (CDSE credits)
- Static data site: reproducible export, interactive map, accessibility and end-to-end CI

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

## Adding a crop or a region

- **New region:** an entry in `config/regiones.yaml` with the list of provinces (`[]` = the whole country), then run the pipeline with `--region <name>`. A crop can pin its region with `region:` in its entry, and the scripts take it from there.
- **New crop:** an entry in `config/cultivos.yaml`, no code changes. The fields are documented in the file header, and `src/agro/config.py` rejects an incomplete entry on load. Checklist, in this order (free things first):
  1. **Mask.** Confirm the crop code in the `.qml` of each MNC campaign (Zenodo): the legend changes between campaigns and 2018/19 uses a different one (`mnc_clase_campania`). The GeoTIFFs do not embed the legend.
  2. **MAGyP.** Confirm the exact name in the CSV (`magyp_cultivo`) and that yield exists per department.
  3. **Region.** If the crop is outside BA/SF/Córdoba, add the region.
  4. **Windows.** `mes_*` (campaign) and `ext_mes_*` (extraction, the one that spends credits). Optional: `tmax_calor` if the heat-stress threshold is not 32 °C.
  5. **Run** `03` → `02` → `04` (first with `--limite 1` to measure credits) → `05` → `06` → `07`.

  **Candidate crops.** They are commented-out entries in `cultivos.yaml`, with every uncertain value marked `VERIFICAR`:

  | Crop | MNC 2024/25 | Strategy and risk |
  |---|---|---|
  | Maize | summer, class 10 | A single entry with a long window (Sep–Jun, ~2× the credits of soybean). It mixes early and late plantings. Future improvement: separate them with the MNC seasonality map or k-means on the NDVI curve. |
  | Cotton | summer, class 15 | Needs a new region (NEA). There is no remote-sensing yield precedent in Argentina. |
  | Potato | summer and winter, class 26 | New region (southeast Buenos Aires). Small area: most departments would fall under the minimum number of points. We still need to confirm which map it is on. |
  | Pea | winter, class 24 | Small area. Confirm the code exists in every campaign. |
  | Barley | inside "winter cereals" (16) | **Not added for now.** The MNC does not separate it from wheat; strategies are proposed and under analysis (see [Barley: separating it from wheat](#barley-separating-it-from-wheat-proposal-under-analysis)). The literature separates it with Sentinel-1 and Sentinel-2 only at county scale ([Marini 2021](https://www.scielo.org.mx/scielo.php?pid=S0188-46112021000100109&script=sci_abstract)). |

  Useful reference: [ML13-DEV/crops-yield-price-forecast](https://github.com/ML13-DEV/crops-yield-price-forecast) predicts yield per department with MAGyP and MODIS, with flowering and grain-filling windows per crop. It has no license, so it is consulted as an idea and no code is copied.

## Barley: separating it from wheat (proposal under analysis)

The MNC groups wheat, barley, oats and rye as "winter cereals", so today the wheat mask includes barley. A client has a specific interest in barley. This section documents the problem and the proposed strategies: **none is implemented or decided**, and in the meantime barley is not added as a crop.

**The problem, measured with MAGyP** (planted area 2018/19–2024/25, humid-pampa departments, CSV 2026-03):

- **It is concentrated.** 96% of barley is in Buenos Aires. 25 departments hold 80% of the area and 40 hold 90%.
- **The mix is large.** In the 29 departments with 10,000 ha or more per year, barley is 44% of wheat+barley (from 19% to 66% depending on the department): the "winter cereals" mask is almost half barley. That share changes between campaigns within the same department (median 21 points between the highest and the lowest), so a fixed factor per department is not enough.
- **The mix already captures part of the signal.** In those 29 departments, the yield deviation of barley and of wheat (same department and campaign) correlate at r = 0.81 (203 observations): a "wheat" signal would already explain ~2/3 of the barley deviation. Separating them targets the rest, plus area and harvest date. It is a heuristic bound, not a model measurement.
- **There is something to validate against.** MAGyP has area and yield of "total barley" per department and campaign. Since 2016/17 it does not distinguish malting from feed barley: that difference cannot be validated, and it is not visible from satellite either.
- **The current wheat window is not enough.** `cultivos.yaml` extracts from August to November (until 30/11), before the final senescence and the harvest (December), which is where barley's earlier timing shows. It has to be extended before extracting wheat.

**What the literature says**

- Wheat and barley have very similar profiles and are confused with few optical dates ([Deep Resolution 3.0, 2025](https://doi.org/10.3390/rs17060957)). Barley is 10–20 days ahead in a central-European study cited there, and INASE mentions a 10–15 day earlier harvest in Argentina ([INASE](https://www.argentina.gob.ar/sites/default/files/if_sisa_cebada_20_21.pdf)).
- [Marini (2021)](https://www.scielo.org.mx/scielo.php?pid=S0188-46112021000100109&script=sci_abstract), Coronel Rosales (Buenos Aires): Random Forest with Sentinel-1 (VV, VH, coherence and texture) plus Sentinel-2 NDVI reaches an F1 of 87% for wheat and 89% for barley. It is a single county and a supervised classifier, so it needs labeled fields.
- With Sentinel-1 series, heading of winter wheat and barley is located with an error of ~3–6 days against the observed date ([Remote Sensing, 2021](https://doi.org/10.3390/rs13245036)).
- Learning a classifier from regional crop proportions, without per-pixel labels, has been shown in Brazil with SAR and optical ([Learning crop type mapping from regional label proportions](https://arxiv.org/pdf/2208.11607)). We did not find published code.
- [WorldCereal](https://github.com/WorldCereal/worldcereal-classification) lets you train your own crop-type head (CatBoost on Presto embeddings) and run it on CDSE openEO, but it needs labels. We did not find an open repository that separates wheat and barley in Argentina.

**Proposed strategies**

| # | Strategy | What it needs | Notes |
|---|---|---|---|
| 1 | **Supervised classifier with Sentinel-1 + Sentinel-2** (Random Forest on NDVI/NDRE curves and backscatter) | Georeferenced barley and wheat fields (hundreds, from 2–3 campaigns), from the client or a malting company | Best expected performance (Marini). It requires moving from NDVI to NDVI+NDRE+S1, and S1 is not yet proven in the project. |
| 2 | **Weak supervision with the MAGyP proportions** | Nothing new | Simple variant: in each department and campaign, sort the sampled pixels by senescence date and assign the earliest s% to barley, with s = the MAGyP barley share. Fine variant: a mixture of 2–3 components (wheat, barley, others) on phenological features, with that share as a prior per department and campaign. Risks: oats and rye form a third group; wheats with different cycle and sowing date overlap barley's date; in the current campaign there is no official share and the historical one would be used. |
| 3 | **More signal in the winter extraction** | Decide it before extracting wheat: nothing has been extracted yet, so it costs no re-downloads | August–January window (`ext_mes_fin: 1`), NDRE in addition to NDVI (`INDICES_S2` in `cdse.py` already supports it), optional S1 VH/VV and 5-day composites instead of 10 to locate senescence (check that it does not change the cost). |
| 4 | **Narrow to the barley zone** | A region with `deptos:` (already implemented, see `regiones.yaml`) | The 40 departments holding 90% of barley are 41% of the area of the 144 with winter cereals (~59% fewer credits); the 29 with 10,000 ha or more, 28% (~72% fewer). They are larger than average, so they save less than the count suggests. |
| 5 | **Presto/WorldCereal with its own head** | Labels (the same as strategy 1) | Not recommended for now: more credits and complexity, and foundation models are out of scope. |

Discarded: using "pure" northern departments as a wheat reference, because phenology shifts by weeks with latitude.

**How to validate without circularity**

1. Estimated barley share, without using the prior, against MAGyP's, in departments and campaigns that were not used for fitting (correlation and RMSE).
2. That the estimate follows the variation between campaigns within each department, not only the geography.
3. Barley yield with the leave-one-campaign-out model, with and without separating (against the winter-cereals mix): does the RMSE go down?
4. With labels (strategy 1): confusion matrix per campaign.

**Proposed sequence**

1. **Small experiment**, when soybean finishes: 29 departments (10,000 ha or more of barley per year) × 2 campaigns, August–January window, NDVI+NDRE. Estimated cost of ~550 credits with NDVI and up to ~700 with NDRE, at ~1.2–1.3 credits per 1,000 km² of bbox with a 5-month window (measured on soybean; wheat has not been extracted yet and the extra band is not measured). Success criterion: correlation ≥ 0.7 between the estimated share (without prior) and MAGyP's.
   **Result (2026-10-07): it does not pass.** The 29 departments were extracted for 2023/24 and 2024/25 (Aug–Jan, NDVI only) and, per department and campaign, the senescence date of each pixel was estimated (a drop to half the amplitude after the peak) along with a 2-Gaussian mixture on those dates, without using the prior. The estimated barley share (weight of the early component) against MAGyP's gives **r = −0.10** across the 58 department-campaign combinations (Spearman −0.08), and the mean senescence date r = 0.12; within each department, r = −0.24. Far from the 0.7 required. The official share varies from 0.15 to 0.71 (mean 0.45), so there was signal to explain. It is a test of a single variant of strategy 2: it does not rule out the separation, but with NDVI every 10 days and a simple mixture the senescence date does not tell barley from wheat (oats, rye and different sowing dates blur it). The experiment code was not versioned.
2. If it passes, extend to the 40 departments × 7 campaigns: ~2,700 credits with NDVI.
3. A single "winter cereals" extraction feeds both wheat and barley: the separation happens afterwards, in the features step (`scripts/05_features.py`), not in the extraction.

**Open questions**

1. Can the client provide georeferenced barley and wheat fields? With them we move to strategy 1.
2. What does it need: yield, area, in-season anomaly, harvest date or malting quality? Quality (protein, grain size) is not visible from satellite.
3. Is the south of Buenos Aires enough?

## Out of scope (deliberately)

- Own crop classifier: INTA's MNC, a published and validated dataset, is used.
- Foundation models or embeddings: the marginal value does not justify the cost while the MNC covers the mask.
- Database, API or Docker, and email/Telegram alerts (added if a client asks).

## Limitations ⚠️

- **Extraction window.** For soybean it is November–May: the integral is not the full-cycle biomass, and what is measured is "cover" and "senescence", not sowing or maturity.
- **Few campaigns.** With 7 campaigns the anomaly has low statistical power: it is reported as a difference against the historical median, not as a z-score.
- **Campaign 2025/26 is provisional.** INTA has not published its MNC yet, so the 2024/25 one was used as the mask (`02_muestrear.py --mascara 2024`); once it is out, the campaign must be deleted and re-extracted in full because the points change. Only 115 of 152 departments were extracted (CDSE credits ran out; the rest next month). Its yield is an **estimate with no benchmark**: the model is trained on the 7 campaigns that have MAGyP yield and predicts 2025/26 for 102 departments (`rendimiento_pronostico_soja.parquet`); the site flags it as provisional until MAGyP publishes the official figure. It is not part of the validation metrics.
- **MNC 2018/19.** A single map with a different legend (first- and second-crop soybean; in wheat it includes barley, oats and cover crops). That campaign is less comparable.
- **Wheat.** The MNC class is "winter cereals" and includes barley. Separating them is under analysis (details, strategies and a failed first experiment in the [Spanish README](README_es.md#cebada-separarla-del-trigo-propuesta-en-análisis)).
- **Running campaign.** If INTA has not published its MNC yet, the mask is provisional (pixels that held the crop in previous campaigns).
- **Alternatives.** CONAE's SAOCOM maps (800 m pixels, no departmental scale) and the Government's Crop Map (per-field NDVI) exist. This project targets the departmental scale with explicit validation against MAGyP.

## License

MIT — see the `LICENSE` file.
