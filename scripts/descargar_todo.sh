#!/usr/bin/env bash
# Descarga CDSE reanudable: soja 2025 y trigo, empezando por las campañas con menos deptos faltantes.
# Re-correr retoma lo que falte. Evita suspensión/apagado mientras corre (systemd-inhibit).
# Parada ordenada: `touch data/processed/PARAR` -> termina los deptos en curso y no empieza otros.
cd "$(dirname "$0")/.." || exit 1
if [ -z "${INHIBIDO:-}" ]; then
  INHIBIDO=1 exec systemd-inhibit --what=sleep:idle:shutdown --who=agro --why="descarga CDSE" "$0" "$@"
fi
rm -f data/processed/PARAR
pares=$(uv run python -c '
import pandas as pd
from pathlib import Path
P = Path("data/processed")
filas = []
for c, a in [("soja", 2025)] + [("trigo", a) for a in range(2018, 2025)]:
    total = pd.read_parquet(P / f"puntos_{c}_{a}_pampa-humeda.parquet")["depto_id"].nunique()
    hechos = len(list((P / "series" / f"{c}_{a}").glob("*.parquet")))
    if total > hechos:
        filas.append((total - hechos, c, a))
print(*[f"{c}:{a}" for _, c, a in sorted(filas)])
')
echo "orden: $pares" | tee -a data/processed/descarga.log
for par in $pares; do
  [ -e data/processed/PARAR ] && break
  uv run python scripts/04_extraer_cdse.py --cultivo "${par%%:*}" --campania "${par##*:}" --workers 2 2>&1 \
    | tee -a data/processed/descarga.log
done
