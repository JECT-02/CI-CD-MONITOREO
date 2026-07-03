#!/bin/bash

set -uo pipefail

PROYECTO_DIR="/home/ject/proyecto"
RESULTADOS_DIR="${PROYECTO_DIR}/experimento/resultados"
MONITOR="${PROYECTO_DIR}/experimento/monitoreo/monitor.sh"

mkdir -p "$RESULTADOS_DIR"

echo "Fase 4 (continuacion): Corridas de control (sin fallo)"

for run in 02 03 04 05; do
    echo "[RUN] fallo=F0 estrategia=umbral_fijo run=${run}"
    bash "$MONITOR" "0" "umbral_fijo" "$run" "$RESULTADOS_DIR"
    ec=$?
    if [ $ec -eq 0 ]; then
        echo "[OK] F0/umbral_fijo/run${run} completado"
    else
        echo "[FAIL] F0/umbral_fijo/run${run} fallo (ec=${ec})"
    fi
done

for run in 01 02 03 04 05; do
    echo "[RUN] fallo=F0 estrategia=ventana_deslizante run=${run}"
    bash "$MONITOR" "0" "ventana_deslizante" "$run" "$RESULTADOS_DIR"
    ec=$?
    if [ $ec -eq 0 ]; then
        echo "[OK] F0/ventana_deslizante/run${run} completado"
    else
        echo "[FAIL] F0/ventana_deslizante/run${run} fallo (ec=${ec})"
    fi
done

echo ""
echo "Fase 4 completada. Resultados en: ${RESULTADOS_DIR}"
