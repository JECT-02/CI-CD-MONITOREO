# Diseño Experimental

## 1. Propósito

Este documento define formalmente el experimento que mide la efectividad de la
reversión automática de despliegues fallidos en un pipeline CI/CD, comparando
dos estrategias de detección de fallos contra un baseline de intervención
manual. El experimento se ejecuta sobre un entorno local (WSL2 + Docker +
Terraform), sin servicios cloud.

---

## 2. Variable independiente 1: tipo de fallo inyectado

Se definen cuatro categorías de fallo, cada una inyectada mediante una
modificación deliberada de la configuración Terraform o del artefacto de
build:

| ID | Tipo de fallo | Mecanismo de inyección |
|---|---------------|------------------------|
| F1 | Error de sintaxis en build | Dockerfile con instrucción inválida que impide la construcción de la imagen. |
| F2 | Puerto de servicio cerrado | Contenedor que expone un puerto distinto al que el health check consulta. |
| F3 | Timeout de verificación de salud | Servicio que responde al health check con latencia superior al umbral de espera configurado. |
| F4 | Dependencia faltante | Contenedor arrancado sin una variable de entorno o archivo de configuración que el servicio requiere para responder. |

Cada fallo se materializa como una variante independiente dentro de
`experimento/infra/version_fallo/`, de forma que la reversión consista en
volver a aplicar la configuración de `version_estable/` (que no contiene ningún
fallo). Los cuatro fallos están diseñados para ser detectables por el mismo
endpoint de salud (`GET /health`) en el mismo puerto, variando únicamente el
comportamiento del servicio.

---

## 3. Variable independiente 2: estrategia de detección

Se comparan dos políticas de decisión que determinan cuándo el sistema se
considera en "estado degradado" y se dispara la reversión automática:

| ID | Estrategia | Definición operacional |
|---|------------|------------------------|
| E1 | Umbral fijo de fallos consecutivos | Si N verificaciones de salud consecutivas devuelven un resultado negativo, se declara estado degradado. Para este experimento, N = 3, con intervalo de polling de 5 segundos entre verificaciones. |
| E2 | Ventana deslizante de observación | Si, dentro de una ventana de M verificaciones, al menos K resultan negativas, se declara estado degradado. Para este experimento, M = 6, K = 3, con el mismo intervalo de 5 segundos. La ventana se desplaza una verificación a la vez, descartando la más antigua. |

El criterio E1 es el más simple posible y está ampliamente documentado en
herramientas de monitoreo tradicionales. El criterio E2 es una variante que
tolera fallos aislados (por ejemplo, un timeout puntual por congestión de red)
sin activar una reversión innecesaria, pero que detecta una tendencia
consistente al fallo dentro de la ventana. La comparación busca determinar si
E2 ofrece un MTTR menor sin incrementar la tasa de falsos positivos.

---

## 4. Variable dependiente

| Métrica | Definición | Unidad |
|---------|-----------|--------|
| MTTR (Tiempo medio de recuperación) | Diferencia entre el timestamp en que la estrategia activa declara "estado degradado" y el timestamp en que el health check confirma que la versión estable volvió a responder correctamente tras la reversión. | Segundos, con media aritmética y desviación estándar por condición. |
| Tasa de detección correcta | Proporción de corridas en las que el fallo inyectado fue detectado por la estrategia activa. | Porcentaje (%), reportado como fracción X/N. |
| Falsos negativos | Proporción de corridas en las que el fallo inyectado no fue detectado y el sistema permaneció en estado fallido sin reversión. | Porcentaje (%). |
| Falsos positivos | Proporción de corridas de control (sin fallo inyectado) en las que la estrategia activó una reversión de todas formas. | Porcentaje (%). |

---

## 5. Variables de control

Todas las corridas comparten el mismo entorno y configuración base:

- Mismo servidor físico (WSL2 sobre Windows 11, 8 GB RAM asignada, 4 CPUs
  virtuales).
- Misma red local (loopback de WSL2, sin variación de latencia externa).
- Mismo pipeline base (workflow de GitHub Actions con la misma secuencia de
  pasos).
- Mismo intervalo de polling de salud: 5 segundos entre verificaciones.
- Misma imagen base del contenedor para la versión estable (versión 1).
- Mismo endpoint de salud (`GET /health`, puerto 8080).
- Mismo timeout de espera por verificación individual: 2 segundos.

Cada corrida utiliza un nombre de contenedor único que codifica el tipo de
fallo, la estrategia y el número de repetición, siguiendo el formato
`exp_<fallo>_<estrategia>_run<NN>`, para permitir la trazabilidad sin
ambigüedad entre logs de Docker, logs de monitoreo y resultados.

---

## 6. Criterio formal de "estado degradado"

El sistema se considera en estado degradado cuando el endpoint de salud no
responde con un código HTTP 200 dentro del timeout de 2 segundos. Este criterio
se evalúa según la estrategia activa:

- **Para E1 (umbral fijo):** 3 fallos consecutivos sin ninguna respuesta
  exitosa intermedia. Justificación: tres fallos consecutivos descartan la
  posibilidad de un falso aislado por congestión transitoria (como reporta [9]
  para sistemas con latencia de red típica en entornos locales), sin requerir
  una ventana de memoria adicional.
- **Para E2 (ventana deslizante):** 3 o más fallos dentro de una ventana de 6
  verificaciones (30 segundos). Justificación: la ventana de 6 es
  suficientemente corta para no retrasar la detección de un fallo persistente,
  pero admite hasta 2 fallos aislados sin activar la reversión, lo cual reduce
  el riesgo de reversiones innecesarias por fluctuaciones breves. La relación
  K/M = 0.5 está dentro del rango recomendado por [10] para entornos con
  perfiles de fallo transitorio conocidos.

Ambos criterios parten del mismo endpoint de salud y del mismo intervalo de
polling, de forma que la diferencia observada entre E1 y E2 es atribuible a la
política de decisión, no a la instrumentación.

---

## 7. Baseline de intervención manual

Para cada tipo de fallo, se mide también el tiempo de recuperación bajo
intervención manual simulada. El procedimiento es:

1. Se despliega la versión con fallo.
2. Se inicia un cronómetro (timestamp inicial).
3. Un operador (simulado mediante un script con una pausa fija, representativa
   del tiempo humano de detección, diagnóstico y ejecución de comandos)
   detecta el fallo, identifica la causa y ejecuta manualmente
   `terraform apply` con la configuración de la versión estable.
4. Se registra el timestamp en que el health check confirma la recuperación.
5. El MTTR manual es la diferencia entre ambos timestamps.

La pausa fija del operador simulado se calibra antes de las corridas
experimentales, midiendo el tiempo que un humano tarda en: abrir la terminal,
identificar el contenedor fallido, revisar los logs de Docker, localizar la
configuración de Terraform correcta y ejecutar `terraform apply`. Este tiempo
se mide en una sesión de prueba preliminar y se fija como constante para todas
las corridas del baseline.

---

## 8. Número de repeticiones y diseño factorial

El experimento sigue un diseño factorial completo 4 × 2, más el baseline
manual para cada tipo de fallo:

| Condición | Fallos | Estrategias | Repeticiones | Total corridas |
|-----------|--------|-------------|-------------|----------------|
| Automático (E1 y E2) | 4 (F1–F4) | 2 (E1, E2) | 10 | 80 |
| Baseline manual | 4 (F1–F4) | 1 (manual) | 5 | 20 |
| Control (sin fallo) | 0 | 2 (E1, E2) | 5 | 10 |
| **Total** | | | | **110** |

Las corridas de control (sin fallo inyectado) permiten medir la tasa de falsos
positivos de cada estrategia: si la estrategia activa una reversión cuando no
hay fallo, se registra como falso positivo. No se incluyen corridas de control
para el baseline manual porque la intervención manual no se activa sin fallo.

Cada corrida es independiente: entre corridas, el contenedor se destruye
(`docker rm -f`) y se vuelve a desplegar desde cero, eliminando cualquier
efecto de estado residual.

---

## 9. Arquitectura de ejecución (resumen)

El experimento se ejecuta sobre cuatro capas, descritas en detalle en
`configuracion_plan.md`:

1. **Orquestación:** GitHub Actions dispara cada corrida con los parámetros
   (tipo de fallo, estrategia, número de repetición) como variables de entrada.
2. **Infraestructura:** Terraform con provider `kreuzwerker/docker` declara y
   aplica el estado deseado del contenedor. La reversión consiste en volver a
   aplicar la configuración de `version_estable/`.
3. **Ejecución:** Docker Engine dentro de WSL2 corre los contenedores.
4. **Observación:** Script de polling HTTP que implementa la estrategia activa
   (E1 o E2) y registra cada evento con timestamp.



---

## 10. Formato de los datos de salida

Cada corrida genera un archivo de log en `experimento/resultados/` con los
siguientes campos, uno por línea en formato JSON:

```
{"evento": "inicio_despliegue", "timestamp": "...", "fallo": "F1", "estrategia": "E1", "run": "01"}
{"evento": "fin_despliegue", "timestamp": "...", "fallo": "F1", "estrategia": "E1", "run": "01"}
{"evento": "health_check_fallo", "timestamp": "...", "codigo": 503}
{"evento": "decision_reversion", "timestamp": "...", "motivo": "umbral_fijo_3_fallos"}
{"evento": "inicio_reversion", "timestamp": "...", "comando": "terraform apply version_estable"}
{"evento": "fin_reversion", "timestamp": "...", "exito": true}
{"evento": "health_check_exitoso", "timestamp": "...", "codigo": 200}
```

La consolidación de estos logs en tablas resumen se realiza mediante el script
`consolidate.py`, que calcula los estadísticos definidos en la sección 4
de este documento y los vierte en `experimento/tablas_resumen.md`.

---

## 11. Validación previa a la ejecución completa

Antes de lanzar las 110 corridas, se ejecuta una prueba de verificación por
cada condición:

1. Cada variante de fallo (F1–F4) se despliega manualmente con Terraform y se
   confirma que el health check reporta el fallo esperado.
2. Cada estrategia (E1, E2) se prueba contra un contenedor estable para
   confirmar que no genera falsos positivos durante al menos 2 minutos de
   monitoreo continuo.
3. El baseline manual se calibra con una medición preliminar del tiempo de
   intervención simulada, que se fija como constante para todas las corridas.
4. El workflow de GitHub Actions se prueba de extremo a extremo con una corrida
   completa de cada combinación fallo × estrategia antes de lanzar el conjunto
   completo.
