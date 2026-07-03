# Reproducción del Experimento: Automatización de Mecanismos de Rollback en CI/CD

Este directorio contiene todo lo necesario para reproducir el experimento
que mide la efectividad de dos estrategias de detección de fallos (umbral
fijo vs. ventana deslizante) en un pipeline CI/CD, contrastando los
resultados contra una intervención manual de referencia.

## Prerrequisitos

### Sistema operativo
- **Windows 11** con WSL2 (recomendado: distribución Debian o Ubuntu)
- O **Linux** nativo con Docker y Terraform instalados

### Software necesario
| Herramienta | Versión mínima | Propósito |
|---|---|---|
| Docker Engine | 24+ | Ejecución de contenedores |
| Terraform | 1.0+ | Infraestructura como código (provider kreuzwerker/docker ~> 3.0) |
| Python | 3.10+ | Consolidación de datos y generación de figuras |
| curl | Cualquiera | Verificación de salud HTTP |
| Git | Cualquiera | Clonar el repositorio |

### Dependencias Python
```bash
pip install -r experimento/requirements.txt
```
Requiere `matplotlib` y `numpy` (solo para generar figuras;
la consolidación de datos usa solo la biblioteca estándar).

### Configuración de WSL2 (solo Windows)
1. Instalar WSL2 con una distribución Linux (por ejemplo, Debian).
2. Instalar Docker dentro de WSL2.
3. Instalar Terraform dentro de WSL2.
4. Clonar el repositorio dentro del directorio home de WSL2, o accederlo desde
   `/mnt/c/`.

## Estructura del directorio

```
experimento/
├── README.md                 # Este archivo
├── requirements.txt          # Dependencias Python
├── diseno_experimental.md    # Definición formal del diseño experimental
├── runner.sh                 # Orquestador de las 110 corridas
├── runner_phase4.sh          # Subconjunto: solo corridas de control
├── lanzar.sh                 # Lanzador con nohup
├── lanzar2.sh                # Lanzador alternativo con screen
├── launch_runner.ps1         # Lanzador desde PowerShell (Windows)
├── cleanup.sh                # Limpieza de contenedores y estados Terraform
├── status_check.sh           # Verificación de progreso del experimento
├── consolidate.py            # Consolidación de JSONL → tablas resumen
├── validate_json.py          # Validación de archivos JSONL generados
├── fix_json.py               # Corrección de formato en JSONL (si es necesario)
├── generar_figuras.py        # Generación de figuras
├── generar_figuras_metodologia.py  # Figuras de metodología
├── infra/                    # Infraestructura como código (Terraform + Docker)
│   ├── main.tf               # Configuración Terraform de la versión estable
│   ├── variables.tf          # Variables Terraform
│   ├── Dockerfile            # Imagen Docker del servicio web
│   ├── server.py             # Servidor HTTP con endpoint /health
│   └── version_fallo/        # Versiones con fallo inyectado (F1–F4)
│       ├── f1/               # F1: Error de sintaxis en build
│       ├── f2/               # F2: Puerto de servicio cerrado
│       ├── f3/               # F3: Timeout de verificación de salud
│       └── f4/               # F4: Dependencia faltante
├── monitoreo/
│   └── monitor.sh            # Script de monitoreo y decisión de reversión
└── resultados/               # Generado al ejecutar el experimento (no trackeado)
```

## Descripción del experimento

### Diseño factorial
- **4 tipos de fallo** (F1: sintaxis en build, F2: puerto cerrado,
  F3: timeout health check, F4: dependencia faltante)
- **2 estrategias de detección** (E1: umbral fijo de 3 fallos consecutivos,
  E2: ventana deslizante de 3/6)
- **1 baseline manual**: intervención humana simulada con pausa fija
- **Corridas de control**: sin fallo inyectado, para medir falsos positivos

### Total de corridas
| Condición | Fallos | Estrategias | Repeticiones | Total |
|---|---|---|---|---|
| Automático | F1–F4 | E1, E2 | 10 | 80 |
| Baseline manual | F1–F4 | Manual | 5 | 20 |
| Control | Ninguno | E1, E2 | 5 | 10 |
| **Total** | | | | **110** |

### Métricas registradas
- **MTTR**: tiempo desde la declaración de estado degradado hasta la
  confirmación de recuperación (segundos)
- **Tasa de detección**: proporción de fallos detectados
- **Falsos negativos**: fallos no detectados
- **Falsos positivos**: reversiones activadas sin fallo

### Estrategias de detección
- **E1 (Umbral fijo)**: 3 verificaciones de salud consecutivas fallidas
- **E2 (Ventana deslizante)**: 3 o más fallos en una ventana de 6
  verificaciones (30 segundos)

Ambas estrategias usan el mismo endpoint de salud (`GET /health`, puerto 8080)
y el mismo intervalo de polling (5 segundos).

## Cómo ejecutar el experimento

### 1. Preparación del entorno
```bash
# Limpiar contenedores y estados Terraform previos
bash experimento/cleanup.sh

# Crear directorio de resultados
mkdir -p experimento/resultados
```

### 2. Ejecución completa (110 corridas)
```bash
# Linux nativo
cd /ruta/al/proyecto
bash experimento/runner.sh

# Windows con WSL2
# Usar el lanzador PowerShell
powershell -File experimento/launch_runner.ps1

# O manualmente dentro de WSL2
wsl -d Debian --user <usuario> bash /ruta/en/wsl/experimento/runner.sh
```

### 3. Monitoreo del progreso
```bash
bash experimento/status_check.sh
```

### 4. Verificación de datos generados
```bash
python experimento/validate_json.py experimento/resultados/
```

Cada corrida genera un archivo JSONL en `experimento/resultados/` con el
formato `run_<fallo>_<estrategia>_<run>.jsonl`.

## Consolidación de resultados

Una vez completadas las 110 corridas:

```bash
python experimento/consolidate.py
```

Esto genera `experimento/tablas_resumen.md` con:
- MTTR promedio y desviación estándar por tipo de fallo y estrategia
- Matriz de detección de fallos
- Comparación contra baseline manual
- Tasa de falsos positivos

Para re-generar las tablas desde cero con datos nuevos, simplemente
ejecutar `consolidate.py` apuntando al directorio de resultados:
```bash
python experimento/consolidate.py
```
(La ruta está configurada por defecto para el entorno esperado.)

## Generación de figuras

```bash
python experimento/generar_figuras.py
python experimento/generar_figuras_metodologia.py
```

Las figuras se generan en el directorio `images/` del proyecto.

## Solución de problemas

### Error: "docker: command not found"
Asegurarse de que Docker Engine esté instalado y en ejecución dentro de WSL2:
```bash
sudo service docker start
```

### Error: Terraform provider no encontrado
Ejecutar `terraform init` en cada directorio de versión:
```bash
cd experimento/infra && terraform init
cd experimento/infra/version_fallo/f{1..4} && terraform init
```

### Error: Puerto 8080 ocupado
Liberar el puerto manualmente:
```bash
docker rm -f rollback-exp-estable rollback-exp-f1-sintaxis rollback-exp-f2-puerto rollback-exp-f3-timeout rollback-exp-f4-dependencia 2>/dev/null || true
```

### Archivos JSONL con formato inválido
```bash
python experimento/fix_json.py experimento/resultados/
```
