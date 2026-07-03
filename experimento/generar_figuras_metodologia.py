import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 8

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(OUT_DIR, exist_ok=True)

# FIGURA 1 — Flujo del experimento (tres zonas con espaciado verificado)
# ylim=3.4, figsize=6.8x3.2
# Zona superior: anotaciones (y=2.70-3.20)
# Zona media:    cajas de etapas (y=1.80-2.55)
# Zona inferior: MTTR (y=0.50-1.20) y eje temporal (y=0.0-0.50)

fig, ax = plt.subplots(1, 1, figsize=(6.8, 3.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 3.4)
ax.axis('off')

# Stage boxes
sy = 1.80  # stage bottom y
sh = 0.75  # stage height
sc = sy + sh / 2  # stage center y

# (x, w, lines)
stages_def = [
    (0.0,  1.3, ['Despliegue']),
    (1.7,  1.1, ['Fallo', 'activo']),
    (3.2,  1.5, ['Verificaci\u00f3n', 'de salud']),
    (5.1,  1.5, ['Decisi\u00f3n:', '\u00bfumbral?']),
    (7.1,  1.1, ['Reversi\u00f3n', 'autom\u00e1tica']),
    (8.6,  1.2, ['Recuperaci\u00f3n']),
]

for x, w, lines in stages_def:
    rect = plt.Rectangle((x, sy), w, sh, facecolor='#eaeaea',
                         edgecolor='#444444', linewidth=0.8, joinstyle='round')
    ax.add_patch(rect)
    n = len(lines)
    for j, line in enumerate(lines):
        # Distribute lines vertically within the box
        yy = sy + sh * (j + 0.5) / n
        ax.text(x + w/2, yy, line, ha='center', va='center',
                fontsize=7)

# Arrows between stages
for i in range(len(stages_def) - 1):
    x_start = stages_def[i][0] + stages_def[i][1]
    x_end = stages_def[i+1][0]
    ax.annotate('', xy=(x_end, sc), xytext=(x_start, sc),
                arrowprops=dict(arrowstyle='->', color='#444444', lw=0.9))

# Annotations
# Connector from stage top (sy+sh=2.55) to annotation zone
# Polling annotation (above "Verificaci\u00f3n")
px = 3.95
ax.plot([px, px], [2.55, 2.75], color='#888888', linewidth=0.5)
ax.text(px, 2.90, 'Cada 5 s',
        fontsize=6.5, ha='center', va='bottom', color='#555555',
        fontstyle='italic')

# Strategy annotations (above "Decisi\u00f3n")
dx = 5.85
ax.plot([dx, dx], [2.55, 2.75], color='#888888', linewidth=0.5)
ax.text(dx, 2.90, 'E2: 3/6 en ventana deslizante',
        fontsize=6.5, ha='center', va='bottom', color='#2980b9')
ax.text(dx, 3.10, 'E1: 3 fallos consecutivos',
        fontsize=6.5, ha='center', va='bottom', color='#c0392b')

# Time axis and MTTR
# Time axis at y=0.55, ticks from 0.30 to 0.80
ax.plot([0.8, 9.0], [0.55, 0.55], color='#333333', linewidth=0.8)
ax.plot([0.8, 0.8], [0.30, 0.80], color='#333333', linewidth=0.6)
ax.plot([9.0, 9.0], [0.30, 0.80], color='#333333', linewidth=0.6)
# t0, t1 labels (va='top' para que queden debajo de la linea)
ax.text(0.8, 0.22, 't\u2080', fontsize=6.5, ha='center', va='top',
        color='#333333')
ax.text(9.0, 0.22, 't\u2081', fontsize=6.5, ha='center', va='top',
        color='#333333')

# MTTR bracket at y=1.15
my = 1.15
ax.plot([0.8, 9.0], [my, my], color='#c0392b', linewidth=1.3)
ax.plot([0.8, 0.8], [my - 0.10, my], color='#c0392b', linewidth=0.6)
ax.plot([9.0, 9.0], [my - 0.10, my], color='#c0392b', linewidth=0.6)
ax.text(4.9, my + 0.10, 'Tiempo de recuperaci\u00f3n (MTTR)',
        fontsize=7, ha='center', va='bottom', color='#c0392b',
        fontweight='bold')

plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'figura_timeline.png'), dpi=300, bbox_inches='tight',
            pad_inches=0.05, facecolor='white')
plt.close()

# FIGURA 2 — Estrategias de detecci\u00f3n
fig, axes = plt.subplots(3, 1, figsize=(6.8, 2.6),
                          gridspec_kw={'height_ratios': [0.5, 0.7, 0.7]})
fig.subplots_adjust(hspace=0.08)

n = 8
is_fail = [True, False, True, False, True, True, True, False]

# Panel superior: verificaciones
ax = axes[0]
for i in range(n):
    c = '#e74c3c' if is_fail[i] else '#2ecc71'
    lbl = 'Fallo' if is_fail[i] else '\u00c9xito'
    rect = plt.Rectangle((i + 0.1, 0.15), 0.8, 0.7, facecolor=c,
                         edgecolor='#333333', linewidth=0.6, joinstyle='round')
    ax.add_patch(rect)
    ax.text(i + 0.5, 0.50, lbl, ha='center', va='center',
            fontsize=6.5, color='white', fontweight='bold')
    ax.text(i + 0.5, -0.05, str(i + 1), ha='center', va='top',
            fontsize=7, color='#555555')

ax.set_xlim(0, n); ax.set_ylim(-0.15, 0.95); ax.axis('off')
ax.text(-0.20, 0.50, 'Verificaciones:', fontsize=7, ha='right',
        va='center', color='#333333')

# Panel medio: Umbral fijo (E1)
ax = axes[1]
for i in range(n):
    if is_fail[i]:
        consec = 1 if i == 0 or not is_fail[i-1] else consec + 1
    else:
        consec = 0
    trigger = is_fail[i] and consec >= 3
    if trigger:
        bg, txt, tc, ec, lw_ = '#d62728', 'Reversi\u00f3n', 'white', '#d62728', 1.8
    elif is_fail[i]:
        bg, txt, tc, ec, lw_ = '#fde8e8', f'{consec}', '#333333', '#cccccc', 0.5
    else:
        bg, txt, tc, ec, lw_ = '#e8f8e8', '0', '#999999', '#cccccc', 0.5

    rect = plt.Rectangle((i + 0.15, 0.15), 0.7, 0.6, facecolor=bg,
                         edgecolor=ec, linewidth=lw_, joinstyle='round')
    ax.add_patch(rect)
    ax.text(i + 0.50, 0.45, txt, ha='center', va='center',
            fontsize=7, color=tc, fontweight='bold' if trigger else 'normal')

ax.set_xlim(0, n); ax.set_ylim(0, 0.9); ax.axis('off')
ax.text(-0.20, 0.45, 'Umbral fijo (E1):', fontsize=7, ha='right',
        va='center', color='#333333')

# Panel inferior: Ventana deslizante (E2)
ax = axes[2]
for i in range(n):
    start = max(0, i - 5)
    n_fail = sum(1 for j in range(start, i + 1) if is_fail[j])
    n_total = i - start + 1
    ready = n_total >= 6
    trigger = ready and n_fail >= 3
    if trigger:
        bg, txt, tc, ec, lw_ = '#d62728', 'Reversi\u00f3n', 'white', '#d62728', 1.8
    elif ready:
        bg = '#fde8e8' if n_fail >= 2 else '#e8f8e8'
        bg, txt, tc, ec, lw_ = bg, f'{n_fail}/{n_total}', '#333333', '#cccccc', 0.5
    else:
        bg, txt, tc, ec, lw_ = '#f5f5f5', f'{n_fail}/{n_total}', '#999999', '#e0e0e0', 0.5

    rect = plt.Rectangle((i + 0.15, 0.15), 0.7, 0.6, facecolor=bg,
                         edgecolor=ec, linewidth=lw_, joinstyle='round')
    ax.add_patch(rect)
    ax.text(i + 0.50, 0.45, txt, ha='center', va='center',
            fontsize=7, color=tc, fontweight='bold' if trigger else 'normal')

ax.set_xlim(0, n); ax.set_ylim(0, 0.9); ax.axis('off')
ax.text(-0.20, 0.45, 'Ventana deslizante (E2):', fontsize=7, ha='right',
        va='center', color='#333333')

axes[0].set_title(
    'Comparaci\u00f3n de estrategias de detecci\u00f3n',
    fontsize=8, fontweight='bold', pad=6)

plt.savefig(os.path.join(OUT_DIR, 'figura_estrategias.png'), dpi=300, bbox_inches='tight',
            pad_inches=0.05, facecolor='white')
plt.close()

print("Figuras regeneradas correctamente.")
