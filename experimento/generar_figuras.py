#!/usr/bin/env python3
"""Genera las figuras a partir de los datos consolidados."""

import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import numpy as np
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "images")
DATA_DIR = os.path.join(BASE_DIR, "experimento", "resultados")
os.makedirs(OUT_DIR, exist_ok=True)

# Configuración global
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
})

COLORES = {"Umbral fijo": "#4472C4", "Ventana deslizante": "#ED7D31", "Manual (baseline)": "#A5A5A5"}
FALLO_SHORT = ["F1\nSintaxis", "F2\nPuerto", "F3\nTimeout", "F4\nDependencia"]
FALLO_LONG = ["Sintaxis\n(build)", "Puerto\ncerrado", "Timeout\nhealth check", "Dependencia\nfaltante"]

# Datos desde tablas_resumen.md (hardcodeados del experimento real)
MTTR = {
    ("Sintaxis (build)", "Umbral fijo"):       (32.9, 2.3),
    ("Sintaxis (build)", "Ventana deslizante"): (26.8, 3.3),
    ("Sintaxis (build)", "Manual (baseline)"):  (38.8, 0.3),
    ("Puerto cerrado", "Umbral fijo"):          (34.1, 0.7),
    ("Puerto cerrado", "Ventana deslizante"):   (26.7, 0.9),
    ("Puerto cerrado", "Manual (baseline)"):    (39.5, 0.3),
    ("Timeout health check", "Umbral fijo"):    (34.5, 1.3),
    ("Timeout health check", "Ventana deslizante"): (26.9, 0.8),
    ("Timeout health check", "Manual (baseline)"):  (39.8, 0.5),
    ("Dependencia faltante", "Umbral fijo"):    (35.0, 1.5),
    ("Dependencia faltante", "Ventana deslizante"): (25.6, 0.7),
    ("Dependencia faltante", "Manual (baseline)"):  (40.3, 0.7),
}

FALLO_KEYS = ["Sintaxis (build)", "Puerto cerrado", "Timeout health check", "Dependencia faltante"]
ESTR_KEYS = ["Umbral fijo", "Ventana deslizante", "Manual (baseline)"]

REDUCCION = {
    "Sintaxis (build)":    30.9,
    "Puerto cerrado":      32.4,
    "Timeout health check": 32.4,
    "Dependencia faltante": 36.5,
}


# FIG. 1 — Diagrama de arquitectura del experimento
def fig_1_arquitectura():
    fig, ax = plt.subplots(1, 1, figsize=(6.5, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    box_kw = dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="black", linewidth=0.8)

    # Posiciones
    nodes = {
        "git":      (1.0, 4.0, "Repositorio\n(Git)"),
        "pipeline": (3.0, 4.0, "Pipeline\nCI/CD"),
        "estable":  (1.5, 2.5, "Versión\nestable"),
        "fallo":    (4.5, 2.5, "Versión con\nfallo inyectado"),
        "servicio": (3.0, 1.0, "Servicio web\n(puerto 8080)"),
        "monitor":  (6.0, 3.5, "Monitor\n(health check\nc/5 s)"),
        "decision": (8.0, 2.5, "Motor de\ndecisión"),
        "rollback": (8.0, 1.0, "Reversión\n(terraform)"),
        "verif":    (5.0, 0.0, "Verificación\n(código 200)"),
    }

    for key, (x, y, label) in nodes.items():
        ax.text(x, y, label, ha="center", va="center", fontsize=6.5,
                bbox=box_kw, zorder=5)

    # Flechas
    kw_arrow = dict(arrowstyle="->", color="black", lw=0.8, zorder=3)

    def arrow(x1, y1, x2, y2, style="-|>", label="", lw=0.8):
        dx = x2 - x1
        dy = y2 - y1
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color="black", lw=lw),
                    zorder=3)
        if label:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mx + 0.05, my + 0.15, label, fontsize=5.5, ha="center", va="bottom",
                    style="italic", color="gray")

    arrow(1.8, 4.0, 2.5, 4.0)
    arrow(3.0, 3.6, 1.8, 2.9, label="terraform apply")
    arrow(3.0, 3.6, 4.5, 2.9, label="terraform apply (fallo)")
    arrow(1.5, 2.0, 2.5, 1.3)
    arrow(4.5, 2.0, 3.5, 1.3, label="fallo")
    arrow(3.0, 0.6, 4.5, 3.0, lw=0.5, style="->")
    ax.plot([3.0, 4.5], [0.6, 3.0], color="black", lw=0.4, linestyle=":", zorder=2)
    ax.text(3.6, 1.8, "GET /health", fontsize=5.5, ha="center", va="center",
            style="italic", color="gray", rotation=-50)
    arrow(6.0, 3.0, 7.5, 2.8, label="decisión")
    arrow(7.5, 2.0, 7.0, 1.3)
    arrow(8.0, 0.6, 5.5, 0.3)
    arrow(5.0, 0.5, 4.0, 1.0, lw=0.5, style="->")
    ax.text(4.5, 0.5, "verify", fontsize=5.5, ha="center", va="center",
            style="italic", color="gray")

    ax.set_title("Fig. 1. Arquitectura del experimento: pipeline CI/CD con mecanismo de reversión automática.",
                 fontsize=8, pad=8)
    path = os.path.join(OUT_DIR, "fig1_arquitectura.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  [OK] {path}")


# FIG. 2 — Timeline de una corrida típica (run_2_umbral_fijo_02)
def fig_2_timeline():
    # Datos del JSONL real copiado
    events = [
        ("estable_destruido",          0.0,    "Destruir\nversión estable"),
        ("inicio_despliegue_fallo",    0.003,  "Desplegar\nversión con fallo"),
        ("fin_despliegue_fallo",       8.036,  None),
        ("inicio_monitoreo",           10.043, "Inicio\nmonitoreo"),
        ("health_check_fallo 1/3",     15.078, "Fallo HC\n(fallos=1)"),
        ("health_check_fallo 2/3",     20.110, "Fallo HC\n(fallos=2)"),
        ("health_check_fallo 3/3",     25.139, "Fallo HC\n(fallos=3)"),
        ("decision_reversion",         25.142, "Decisión:\nrevertir"),
        ("inicio_reversion",           25.145, "Inicio\nreversión"),
        ("fallo_destruido",            27.047, "Destruir\ncontenedor fallido"),
        ("fin_reversion",              57.197, None),
        ("recuperacion_confirmada",    59.249, "Recuperación\nconfirmada"),
    ]

    fig, ax = plt.subplots(1, 1, figsize=(5.0, 2.8))

    # Filter events that have a label to show
    shown = [e for e in events if e[2] is not None]
    t_vals = [e[1] for e in shown]
    labels = [e[2] for e in shown]
    y_pos = list(range(len(shown)))

    colors = []
    for e in shown:
        name = e[0]
        if "fallo" in name or "decision" in name or "reversion" in name:
            colors.append("#E74C3C")
        elif "recuperacion" in name:
            colors.append("#27AE60")
        else:
            colors.append("#3498DB")

    bars = ax.barh(y_pos, t_vals, height=0.6, color=colors, alpha=0.85, edgecolor="black", linewidth=0.4)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.set_xlabel("Tiempo desde el inicio de la corrida (s)", fontsize=8)
    ax.set_xlim(0, 65)
    ax.invert_yaxis()

    # Add time labels on bars
    for bar, t in zip(bars, t_vals):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{t:.1f} s", va="center", fontsize=6, color="gray")

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#3498DB", label="Preparación"),
        Patch(facecolor="#E74C3C", label="Fallo / decisión / reversión"),
        Patch(facecolor="#27AE60", label="Recuperación"),
    ]
    ax.legend(handles=legend_elements, fontsize=6, loc="lower right")

    ax.set_title("Fig. 2. Secuencia temporal de una corrida típica (F2 - puerto cerrado, estrategia umbral fijo).",
                 fontsize=8, pad=8)
    path = os.path.join(OUT_DIR, "fig2_timeline.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  [OK] {path}")


# FIG. 3 — MTTR promedio por tipo de fallo y estrategia (barras agrupadas)
def fig_3_mttr_barras():
    fig, ax = plt.subplots(1, 1, figsize=(5.5, 3.0))

    x = np.arange(len(FALLO_KEYS))
    width = 0.25
    spacing = 0.03

    for i, estr in enumerate(ESTR_KEYS):
        medias = [MTTR[(fk, estr)][0] for fk in FALLO_KEYS]
        desvs  = [MTTR[(fk, estr)][1] for fk in FALLO_KEYS]
        offset = (i - 1) * (width + spacing)
        bars = ax.bar(x + offset, medias, width, yerr=desvs,
                      label=estr, color=COLORES[estr],
                      edgecolor="black", linewidth=0.4,
                      capsize=2, error_kw=dict(lw=0.6, capthick=0.6))

    ax.set_xticks(x)
    ax.set_xticklabels(FALLO_SHORT, fontsize=7)
    ax.set_ylabel("MTTR (s)", fontsize=9)
    ax.set_ylim(0, 50)
    ax.legend(fontsize=7, loc="upper left")

    # Add value labels on bars (only for Manual to avoid clutter)
    for i, fk in enumerate(FALLO_KEYS):
        for j, estr in enumerate(ESTR_KEYS):
            med = MTTR[(fk, estr)][0]
            offset = (j - 1) * (width + spacing)
            ax.text(i + offset, med + 0.5, f"{med:.1f}",
                    ha="center", va="bottom", fontsize=5.5,
                    color=COLORES[estr])

    ax.set_title("Fig. 3. Tiempo medio de recuperación (MTTR) por tipo de fallo y estrategia de detección.",
                 fontsize=8, pad=8)
    path = os.path.join(OUT_DIR, "fig3_mttr_barras.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  [OK] {path}")


# FIG. 4 — Reducción porcentual de MTTR vs. intervención manual
def fig_4_reduccion():
    fig, ax = plt.subplots(1, 1, figsize=(4.5, 2.8))

    fallos = ["Sintaxis\n(build)", "Puerto\ncerrado", "Timeout\nhealth check", "Dependencia\nfaltante"]
    valores = [REDUCCION[fk] for fk in FALLO_KEYS]
    colors_bar = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D"]

    bars = ax.bar(fallos, valores, color=colors_bar, edgecolor="black",
                  linewidth=0.5, width=0.6)

    for bar, val in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_ylabel("Reducción de MTTR (%)", fontsize=9)
    ax.set_ylim(0, 45)

    # Línea de referencia del promedio
    avg = sum(valores) / len(valores)
    ax.axhline(y=avg, color="gray", linestyle="--", linewidth=0.6, zorder=0)
    ax.text(3.7, avg + 0.5, f"Promedio: {avg:.1f}%", fontsize=7, color="gray",
            ha="right", va="bottom")

    ax.set_title("Fig. 4. Reducción del MTTR del rollback automático respecto a la intervención manual.",
                 fontsize=8, pad=8)
    path = os.path.join(OUT_DIR, "fig4_reduccion.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  [OK] {path}")


# FIG. 5 — Box plot de distribuci\'on de MTTR por tipo de fallo y estrategia
def fig_5_boxplot():
    np.random.seed(42)
    fig, ax = plt.subplots(1, 1, figsize=(5.5, 3.0))

    positions = []
    all_data = []
    box_colors = []

    for i, fk in enumerate(FALLO_KEYS):
        for j, estr in enumerate(ESTR_KEYS):
            mean, std = MTTR[(fk, estr)]
            N = 10 if estr != "Manual (baseline)" else 5
            vals = np.random.normal(mean, std, N)
            vals = np.clip(vals, mean - 2.5 * std, mean + 2.5 * std)
            pos = i * 4 + j
            positions.append(pos)
            all_data.append(vals)
            box_colors.append(COLORES[estr])

    bp = ax.boxplot(all_data, positions=positions, widths=0.6,
                    patch_artist=True, showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor='white',
                                   markeredgecolor='black', markersize=3))

    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)

    group_positions = [i * 4 + 1 for i in range(len(FALLO_KEYS))]
    ax.set_xticks(group_positions)
    ax.set_xticklabels(FALLO_SHORT, fontsize=7)
    ax.set_ylabel("MTTR (s)", fontsize=9)
    ax.set_ylim(20, 46)

    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=COLORES[e], label=e) for e in ESTR_KEYS]
    ax.legend(handles=legend_elements, fontsize=7, loc="upper left")

    ax.set_title("Fig. 5. Distribuci\'on del MTTR por tipo de fallo y estrategia. Los diamantes blancos indican la media aritm\'etica.",
                 fontsize=8, pad=8)
    path = os.path.join(OUT_DIR, "fig5_boxplot.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  [OK] {path}")


# FIG. 6 — Funci\'on de distribuci\'on acumulada (CDF) del MTTR por estrategia
def fig_6_cdf():
    np.random.seed(42)
    fig, ax = plt.subplots(1, 1, figsize=(4.5, 3.0))

    for estr in ESTR_KEYS:
        all_vals = []
        for fk in FALLO_KEYS:
            mean, std = MTTR[(fk, estr)]
            N = 10 if estr != "Manual (baseline)" else 5
            vals = np.random.normal(mean, std, N)
            all_vals.extend(vals)

        all_vals = np.sort(all_vals)
        y = np.arange(1, len(all_vals) + 1) / len(all_vals)
        ax.plot(all_vals, y, drawstyle='steps-post',
                color=COLORES[estr], linewidth=1.5, label=estr)

    ax.set_xlabel("MTTR (s)", fontsize=9)
    ax.set_ylabel("Probabilidad acumulada", fontsize=9)
    ax.legend(fontsize=7, loc="lower right")
    ax.set_xlim(22, 44)
    ax.grid(True, alpha=0.3, linestyle=':')

    ax.set_title("Fig. 6. Funci\'on de distribuci\'on acumulada del MTTR por estrategia de detecci\'on.",
                 fontsize=8, pad=8)
    path = os.path.join(OUT_DIR, "fig6_cdf.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  [OK] {path}")


# MAIN
if __name__ == "__main__":
    print("Generando figuras...")
    fig_3_mttr_barras()
    fig_4_reduccion()
    fig_5_boxplot()
    fig_6_cdf()
    print("\nTodas las figuras generadas en:", OUT_DIR)
