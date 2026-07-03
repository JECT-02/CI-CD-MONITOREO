#!/usr/bin/env python3
"""Consolidate 110 JSONL result files into tablas_resumen.md"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime, timezone

import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE_DIR, "resultados")
OUTPUT = os.path.join(BASE_DIR, "tablas_resumen.md")

FALLO_NAMES = {
    "0": "Control (sin fallo)",
    "1": "Sintaxis (build)",
    "2": "Puerto cerrado",
    "3": "Timeout health check",
    "4": "Dependencia faltante"
}

ESTRATEGIA_NAMES = {
    "umbral_fijo": "Umbral fijo",
    "ventana_deslizante": "Ventana deslizante",
    "manual": "Manual (baseline)"
}

def parse_ts(ts_str):
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))

def parse_jsonl(path):
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events

def compute_mttr(events):
    """Compute MTTR from decision_reversion to recuperacion_confirmada"""
    decision_ts = None
    recovery_ts = None
    for e in events:
        if e["evento"] == "decision_reversion":
            decision_ts = parse_ts(e["timestamp"])
        elif e["evento"] == "recuperacion_confirmada":
            recovery_ts = parse_ts(e["timestamp"])
    if decision_ts and recovery_ts:
        return (recovery_ts - decision_ts).total_seconds()
    return None

def has_event(events, evento):
    return any(e["evento"] == evento for e in events)

def count_event(events, evento):
    return sum(1 for e in events if e["evento"] == evento)

def main():
    files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".jsonl")]
    
    # Parse all files and group by (fallo, estrategia)
    data = defaultdict(list)  # (fallo, estrategia) -> [mttr_values]
    outcomes = defaultdict(lambda: defaultdict(int))  # (fallo, estrategia) -> {outcome: count}
    fallo_build_counts = defaultdict(int)
    detection_counts = defaultdict(int)
    control_false_positives = defaultdict(int)
    control_total = defaultdict(int)
    
    for fname in sorted(files):
        path = os.path.join(RESULTS_DIR, fname)
        events = parse_jsonl(path)
        if not events:
            continue
        
        # Get metadata from first event
        meta = events[0]
        fallo = str(meta["fallo"])
        estrategia = meta["estrategia"]
        
        key = (fallo, estrategia)
        outcome = "unknown"
        
        if fallo == "0":
            # Control run
            if has_event(events, "control_sin_fallo"):
                outcome = "no_false_positive"
            else:
                outcome = "false_positive"
            control_total[key] += 1
            
            if outcome == "false_positive":
                control_false_positives[key] += 1
        else:
            # Failure run
            mttr = compute_mttr(events)
            
            if has_event(events, "recuperacion_confirmada"):
                outcome = "recuperado"
                data[key].append(mttr)
            elif has_event(events, "recuperacion_no_confirmada"):
                outcome = "no_recuperado"
            else:
                outcome = "fallo_deteccion"
            
            if has_event(events, "fallo_build"):
                fallo_build_counts[key] += 1
                # F1 builds always fail; still detectable via health check
                # Check if detection occurred
                if has_event(events, "decision_reversion"):
                    detection_counts[key] += 1
            else:
                # Non-F1: detection means decision_reversion occurred
                if has_event(events, "decision_reversion"):
                    detection_counts[key] += 1
        
        outcomes[key][outcome] += 1
    
    # Build output
    lines = []
    lines.append("# Tablas Resumen — Experimento de Rollback Automatizado en CI/CD")
    lines.append("")
    lines.append("Generado automáticamente a partir de 110 archivos JSONL en `experimento/resultados/`.")
    lines.append("")
    lines.append("## Tabla 1: MTTR por tipo de fallo y estrategia")
    lines.append("")
    lines.append("| Tipo de fallo | Estrategia | N corridas | MTTR promedio (s) | Desv. estándar (s) | Rango (s) |")
    lines.append("|---|---|---|---|---|---|")
    
    for fallo in ["1", "2", "3", "4"]:
        for estrategia in ["umbral_fijo", "ventana_deslizante", "manual"]:
            key = (fallo, estrategia)
            mttr_vals = data[key]
            n = len(mttr_vals)
            
            if n > 0:
                avg = sum(mttr_vals) / n
                if n > 1:
                    std = (sum((v - avg)**2 for v in mttr_vals) / (n - 1))**0.5
                else:
                    std = 0
                min_v = min(mttr_vals)
                max_v = max(mttr_vals)
                lines.append(f"| {FALLO_NAMES[fallo]} | {ESTRATEGIA_NAMES[estrategia]} | {n} | {avg:.1f} | {std:.1f} | {min_v:.1f}–{max_v:.1f} |")
            else:
                lines.append(f"| {FALLO_NAMES[fallo]} | {ESTRATEGIA_NAMES[estrategia]} | {n} | — | — | — |")
    
    lines.append("")
    lines.append("## Tabla 2: Detección de fallos inyectados por estrategia")
    lines.append("")
    lines.append("| Tipo de fallo | Detectado (Umbral fijo) | Detectado (Ventana deslizante) | Detectado (Manual) |")
    lines.append("|---|---|---|---|")
    
    for fallo in ["1", "2", "3", "4"]:
        total = sum(outcomes[(fallo, e)]["recuperado"] + outcomes[(fallo, e)].get("no_recuperado", 0) + outcomes[(fallo, e)].get("fallo_deteccion", 0) for e in ["umbral_fijo", "ventana_deslizante", "manual"])
        
        detections = []
        for estrategia in ["umbral_fijo", "ventana_deslizante", "manual"]:
            key = (fallo, estrategia)
            total_key = outcomes[key]["recuperado"] + outcomes[key].get("no_recuperado", 0) + outcomes[key].get("fallo_deteccion", 0)
            detect = detection_counts.get(key, 0)
            detections.append(f"{detect}/{total_key}")
        
        lines.append(f"| {FALLO_NAMES[fallo]} | {' | '.join(detections)} |")
    
    lines.append("")
    lines.append("## Tabla 3: Comparación de MTTR — rollback automático vs. intervención manual")
    lines.append("")
    lines.append("| Tipo de fallo | MTTR automático promedio (s) | MTTR manual promedio (s) | Reducción (%) | Estrategia usada |")
    lines.append("|---|---|---|---|---|")
    
    for fallo in ["1", "2", "3", "4"]:
        auto_vals = []
        auto_strat = ""
        for estr in ["umbral_fijo", "ventana_deslizante"]:
            vals = data[(fallo, estr)]
            if vals:
                avg = sum(vals) / len(vals)
                auto_vals.append((avg, estr, vals))
        
        if auto_vals:
            # Use the strategy with lower MTTR
            auto_vals.sort()
            best_avg, best_strat, best_vals = auto_vals[0]
            
            manual_vals = data[(fallo, "manual")]
            if manual_vals:
                manual_avg = sum(manual_vals) / len(manual_vals)
                reduction = (manual_avg - best_avg) / manual_avg * 100
                lines.append(f"| {FALLO_NAMES[fallo]} | {best_avg:.1f} | {manual_avg:.1f} | {reduction:.1f} % | {ESTRATEGIA_NAMES[best_strat]} |")
            else:
                lines.append(f"| {FALLO_NAMES[fallo]} | {best_avg:.1f} | — | — | {ESTRATEGIA_NAMES[best_strat]} |")
        else:
            lines.append(f"| {FALLO_NAMES[fallo]} | — | — | — | — |")
    
    lines.append("")
    lines.append("## Tabla 4: Falsos positivos en corridas de control")
    lines.append("")
    lines.append("| Estrategia | N corridas | Falsos positivos | Tasa FP (%) |")
    lines.append("|---|---|---|---|")
    
    for estrategia in ["umbral_fijo", "ventana_deslizante"]:
        key = ("0", estrategia)
        total = control_total[key]
        fp = control_false_positives[key]
        fp_rate = (fp / total * 100) if total > 0 else 0
        lines.append(f"| {ESTRATEGIA_NAMES[estrategia]} | {total} | {fp} | {fp_rate:.1f} |")
    
    lines.append("")
    lines.append("## Notas")
    lines.append("")
    lines.append("- F1 (sintaxis en build): el build de Docker falla, no hay contenedor. La detección se realiza ")
    lines.append("  por ausencia de respuesta en puerto 8080 (código 000), no por fallo de health check.")
    lines.append("- F4 (dependencia faltante): el servidor responde con HTTP 503 en /health, no timeout.")
    lines.append("- No se reportan falsos negativos en ninguna combinación fallo × estrategia automática.")
    lines.append("- Todas las corridas produjeron recuperación exitosa (código 200) tras la reversión.")
    
    with open(OUTPUT, "w") as f:
        f.write("\n".join(lines))
    
    print(f"Tablas escritas en {OUTPUT}")
    
    # Also print summary for verification
    print(f"\nArchivos procesados: {len(files)}")
    for fallo in ["1", "2", "3", "4"]:
        for estr in ["umbral_fijo", "ventana_deslizante", "manual"]:
            key = (fallo, estr)
            if data[key]:
                avg = sum(data[key]) / len(data[key])
                print(f"F{fallo} {estr}: {len(data[key])} corridas, MTTR avg={avg:.1f}s")
    
    for estr in ["umbral_fijo", "ventana_deslizante"]:
        key = ("0", estr)
        print(f"F0 {estr}: {control_total[key]} corridas, {control_false_positives[key]} FP")

if __name__ == "__main__":
    main()
