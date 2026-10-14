# Agro Monitor Pampa — site

Static SvelteKit 2 + Svelte 5 site (MapLibre, Observable Plot). It computes nothing: it draws the JSON that `scripts/08_exportar_web.py` writes to `static/data/` and `src/lib/data/` from the pipeline's parquet files.

```bash
uv run python scripts/08_exportar_web.py --cultivo soja   # run from the repo root
npm ci && npm run dev      # http://localhost:5173
npm run check && npx vitest --run && npm run build && npx playwright test
```
