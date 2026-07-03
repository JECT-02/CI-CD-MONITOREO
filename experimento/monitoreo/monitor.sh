#!/bin/bash
# Uso: monitor.sh <tipo_fallo> <estrategia> <run_id> <log_dir>
#   tipo_fallo: 0=control, 1=sintaxis, 2=puerto, 3=timeout, 4=dependencia
#   estrategia: umbral_fijo, ventana_deslizante, manual

set -euo pipefail

FALLO="${1:?fallo}"
ESTRATEGIA="${2:?estrategia}"
RUN_ID="${3:?run_id}"
LOG_DIR="${4:?log_dir}"
POLL_INTERVAL=5
HEALTH_URL="http://localhost:8080/health"

LOG_FILE="${LOG_DIR}/run_${FALLO}_${ESTRATEGIA}_${RUN_ID}.jsonl"
STABLE_DIR="/home/ject/proyecto/experimento/infra"
FALLO_DIR="/home/ject/proyecto/experimento/infra/version_fallo/f${FALLO}"

# Limpieza inicial: remover contenedores residuales de corridas anteriores
docker rm -f rollback-exp-estable rollback-exp-f1-sintaxis rollback-exp-f2-puerto rollback-exp-f3-timeout rollback-exp-f4-dependencia 2>/dev/null || true

log_event() {
    local evento="$1"
    local extra="${2:-}"
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    local line="{\"evento\": \"${evento}\", \"timestamp\": \"${ts}\", \"fallo\": \"${FALLO}\", \"estrategia\": \"${ESTRATEGIA}\", \"run\": \"${RUN_ID}\"${extra:+", ${extra}"}}"
    echo "$line" >> "$LOG_FILE" 2>/dev/null || true
    echo "$line"
}

check_health() {
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$HEALTH_URL" 2>/dev/null) || code="000"
    echo "$code"
}

# Fase de despliegue
if [ "$FALLO" = "0" ]; then
    # Control: asegurar que estable esta corriendo
    cd "$STABLE_DIR"
    terraform apply -auto-approve -no-color > /dev/null 2>&1 || true
    log_event "control_inicio" "\"detalle\": \"version_estable_desplegada\""
else
    # Destruir estable para liberar puerto
    cd "$STABLE_DIR"
    terraform destroy -auto-approve -no-color > /dev/null 2>&1 || true
    log_event "estable_destruido"

    log_event "inicio_despliegue_fallo"
    if [ "$FALLO" = "1" ]; then
        cd "$FALLO_DIR"
        terraform init -no-color > /dev/null 2>&1 || true
        terraform apply -auto-approve -no-color 2>&1 || true
        log_event "fallo_build" "\"detalle\": \"build_failed_syntax_error\""
    else
        cd "$FALLO_DIR"
        terraform init -no-color > /dev/null 2>&1
        terraform apply -auto-approve -no-color 2>&1 | tail -1
        log_event "fin_despliegue_fallo"
    fi
fi

sleep 2

# Bucle de monitoreo
FALLOS_CONSECUTIVOS=0
VENTANA=()
MAX_VENTANA=6
UMBRAL_FIJO=3
UMBRAL_VENTANA=3
ESTADO_DEGRADADO=false
CONTROL_MAX_CHECKS=20  # 100s sin fallo = no_false_positive
CONTROL_CHECK_COUNT=0

log_event "inicio_monitoreo" "\"intervalo_s\": ${POLL_INTERVAL}"

while [ "$ESTADO_DEGRADADO" = false ]; do
    sleep "$POLL_INTERVAL"
    CODIGO=$(check_health)
    TS_CHECK=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")

    if [ "$CODIGO" = "200" ]; then
        FALLOS_CONSECUTIVOS=0
        log_event "health_check_exitoso" "\"codigo\": \"${CODIGO}\""
    else
        FALLOS_CONSECUTIVOS=$((FALLOS_CONSECUTIVOS + 1))
        log_event "health_check_fallo" "\"codigo\": \"${CODIGO}\", \"fallos_consecutivos\": ${FALLOS_CONSECUTIVOS}"
    fi

    VENTANA+=("$CODIGO")
    if [ ${#VENTANA[@]} -gt $MAX_VENTANA ]; then
        VENTANA=("${VENTANA[@]:1}")
    fi

    DECISION=false
    MOTIVO=""

    if [ "$ESTRATEGIA" = "umbral_fijo" ] || [ "$ESTRATEGIA" = "manual" ]; then
        if [ "$FALLOS_CONSECUTIVOS" -ge "$UMBRAL_FIJO" ]; then
            DECISION=true
            MOTIVO="umbral_fijo_${UMBRAL_FIJO}_fallos_consecutivos"
        fi
    elif [ "$ESTRATEGIA" = "ventana_deslizante" ]; then
        CONTEO=0
        for c in "${VENTANA[@]}"; do
            if [ "$c" != "200" ]; then
                CONTEO=$((CONTEO + 1))
            fi
        done
        if [ "$CONTEO" -ge "$UMBRAL_VENTANA" ]; then
            DECISION=true
            MOTIVO="ventana_deslizante_${CONTEO}_fallos_en_${#VENTANA[@]}_checks"
        fi
    fi

    if [ "$DECISION" = true ]; then
        ESTADO_DEGRADADO=true
        log_event "decision_reversion" "\"motivo\": \"${MOTIVO}\""
    fi

    # Control: si no hay degradacion tras N checks, terminar
    if [ "$FALLO" = "0" ]; then
        CONTROL_CHECK_COUNT=$((CONTROL_CHECK_COUNT + 1))
        if [ "$CONTROL_CHECK_COUNT" -ge "$CONTROL_MAX_CHECKS" ]; then
            log_event "control_sin_fallo" "\"checks_realizados\": ${CONTROL_CHECK_COUNT}"
            exit 0
        fi
    fi
done

# Reversion
log_event "inicio_reversion"

if [ "$ESTRATEGIA" = "manual" ]; then
    DEMORA_HUMANA=15
    log_event "demora_manual" "\"segundos\": ${DEMORA_HUMANA}"
    sleep "$DEMORA_HUMANA"
fi

# Destruir contenedor con fallo para liberar puerto 8080
docker rm -f rollback-exp-estable rollback-exp-f1-sintaxis rollback-exp-f2-puerto rollback-exp-f3-timeout rollback-exp-f4-dependencia 2>/dev/null || true
if [ "$FALLO" != "0" ]; then
    cd "$FALLO_DIR"
    terraform destroy -auto-approve -no-color > /dev/null 2>&1 || true
    log_event "fallo_destruido"
fi

cd "$STABLE_DIR"
timeout 90 terraform apply -auto-approve -no-color 2>&1 | tail -1
log_event "fin_reversion"

# Esperar recuperacion
for i in $(seq 1 12); do
    sleep 2
    CODIGO=$(check_health)
    if [ "$CODIGO" = "200" ]; then
        log_event "recuperacion_confirmada" "\"codigo\": \"${CODIGO}\""
        exit 0
    fi
done

log_event "recuperacion_no_confirmada" "\"codigo\": \"${CODIGO}\""
exit 1
