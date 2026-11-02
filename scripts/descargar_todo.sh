#!/usr/bin/env bash
# Descarga CDSE reanudable: soja 2025 y luego trigo. Re-correr retoma lo que falte.
# Evita suspensión/apagado mientras corre (systemd-inhibit).
cd "$(dirname "$0")/.." || exit 1
if [ -z "${INHIBIDO:-}" ]; then
  INHIBIDO=1 exec systemd-inhibit --what=sleep:idle:shutdown --who=agro --why="descarga CDSE" "$0" "$@"
fi
for par in soja:2025 trigo:2024 trigo:2023 trigo:2022 trigo:2021 trigo:2020 trigo:2019 trigo:2018; do
  uv run python scripts/04_extraer_cdse.py --cultivo "${par%%:*}" --campania "${par##*:}" --workers 2 2>&1 \
    | tee -a data/processed/descarga.log
done
