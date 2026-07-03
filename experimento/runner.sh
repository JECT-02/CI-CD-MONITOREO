#!/bin/bash

set -euo pipefail

PROYECTO_DIR="/home/ject/proyecto"
RESULTADOS_DIR="${PROYECTO_DIR}/experimento/resultados"
MONITOR="${PROYECTO_DIR}/experimento/monitoreo/monitor.sh"

mkdir -p "$RESULTADOS_DIR"

REP_AUTOMATICAS=10
REP_BASELINE=5
REP_CONTROL=5

run_and_log() {
    local fallo="$1"
    local estrategia="$2"
    local run="$3"
    echo "[RUN] fallo=F${fallo} estrategia=${estrategia} run=${run}"
    bash "$MONITOR" "$fallo" "$estrategia" "$run" "$RESULTADOS_DIR"
    local ec=$?
    if [ $ec -eq 0 ]; then
        echo "[OK] F${fallo}/${estrategia}/run${run} completado"
    else
        echo "[FAIL] F${fallo}/${estrategia}/run${run} fallo (ec=${ec})"
    fi
    return 0
}

echo "Fase 1: Corridas automaticas E1 (umbral fijo)"
for fallo in 1 2 3 4; do
    for run in $(seq -w 1 $REP_AUTOMATICAS); do
        run_and_log "$fallo" "umbral_fijo" "$run"
    done
done

echo "Fase 2: Corridas automaticas E2 (ventana deslizante)"
for fallo in 1 2 3 4; do
    for run in $(seq -w 1 $REP_AUTOMATICAS); do
        run_and_log "$fallo" "ventana_deslizante" "$run"
    done
done

echo "Fase 3: Corridas baseline manual"
for fallo in 1 2 3 4; do
    for run in $(seq -w 1 $REP_BASELINE); do
        run_and_log "$fallo" "manual" "$run"
    done
done

echo "Fase 4: Corridas de control (sin fallo)"
for estrategia in umbral_fijo ventana_deslizante; do
    for run in $(seq -w 1 $REP_CONTROL); do
        run_and_log "0" "$estrategia" "$run"
    done
done

echo ""
echo "Experimento completado. Resultados en: ${RESULTADOS_DIR}"
