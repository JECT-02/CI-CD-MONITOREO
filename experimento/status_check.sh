#!/bin/bash
LOGFILE="/home/ject/proyecto/experimento/runner.log"
RESDIR="/home/ject/proyecto/experimento/resultados"

echo "Status check"
echo "Proceso runner:"
ps aux | grep runner.sh | grep -v grep

echo ""
echo "Archivos de resultado:"
ls "$RESDIR"/*.jsonl 2>/dev/null | wc -l

echo ""
echo "Ultimas 15 lineas del log:"
tail -15 "$LOGFILE"

echo ""
echo "Resumen de fases:"
total=$(wc -l < "$LOGFILE")
echo "Total lineas en log: $total"

echo ""
echo "Eventos de recuperacion:"
grep -c "recuperacion_confirmada" "$LOGFILE" 2>/dev/null; echo " recuperacion_confirmada"
grep -c "recuperacion_no_confirmada" "$LOGFILE" 2>/dev/null; echo " recuperacion_no_confirmada"
grep -c "control_sin_fallo" "$LOGFILE" 2>/dev/null; echo " control_sin_fallo"
grep -c "fallo_build" "$LOGFILE" 2>/dev/null; echo " fallo_build"
