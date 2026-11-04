# Agro Monitor Pampa — site

Static SvelteKit 2 + Svelte 5 site (MapLibre, Observable Plot). It computes nothing: it draws the JSON that `scripts/08_exportar_web.py` writes to `static/data/` and `src/lib/data/` from the pipeline's parquet files.

```bash
uv run python scripts/08_exportar_web.py --cultivo soja   # run from the repo root; repeat with --cultivo trigo
npm ci && npm run dev      # http://localhost:5173
npm run check && npx vitest --run && npm run build && npx playwright test
```

Pinned on purpose: TypeScript 6 (svelte-check and SvelteKit need the JS API that TS 7 does not ship yet) and `@observablehq/plot` ~0.6.17 (0.6.18 dropped its `types` export, so `npm run check` fails). Revisit both.
