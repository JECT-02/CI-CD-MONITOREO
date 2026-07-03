# Resultados Experimentales

## MTTR por tipo de fallo y estrategia

Los valores provienen de 110 corridas independientes (80 autom\'aticas, 20 baseline manual, 10 control).

| Tipo de fallo | Estrategia | MTTR medio (s) | Desv. est\'andar (s) | n |
|---|---|---|---|---|
| Sintaxis (build) | Umbral fijo | 32.9 | 2.3 | 10 |
| Sintaxis (build) | Ventana deslizante | 26.8 | 3.3 | 10 |
| Sintaxis (build) | Manual | 38.8 | 0.3 | 5 |
| Puerto cerrado | Umbral fijo | 34.1 | 0.7 | 10 |
| Puerto cerrado | Ventana deslizante | 26.7 | 0.9 | 10 |
| Puerto cerrado | Manual | 39.5 | 0.3 | 5 |
| Timeout health check | Umbral fijo | 34.5 | 1.3 | 10 |
| Timeout health check | Ventana deslizante | 26.9 | 0.8 | 10 |
| Timeout health check | Manual | 39.8 | 0.5 | 5 |
| Dependencia faltante | Umbral fijo | 35.0 | 1.5 | 10 |
| Dependencia faltante | Ventana deslizante | 25.6 | 0.7 | 10 |
| Dependencia faltante | Manual | 40.3 | 0.7 | 5 |

## Detecci\'on de fallos

| Estrategia | Corridas totales | Detectados | Tasa detecci\'on | Falsos negativos | Falsos positivos |
|---|---|---|---|---|---|
| Umbral fijo | 40 | 40 | 100 % | 0 | 0/5 |
| Ventana deslizante | 40 | 40 | 100 % | 0 | 0/5 |
| Manual (baseline) | 20 | 20 | 100 % | 0 | -- |

## Reducci\'on del MTTR autom\'atico respecto al manual

| Tipo de fallo | MTTR auto (s) | MTTR manual (s) | Reducci\'on (s) | Reducci\'on (%) |
|---|---|---|---|---|
| Sintaxis (build) | 26.8 | 38.8 | 12.0 | 30.9 |
| Puerto cerrado | 26.7 | 39.5 | 12.8 | 32.4 |
| Timeout health check | 26.9 | 39.8 | 12.9 | 32.4 |
| Dependencia faltante | 25.6 | 40.3 | 14.7 | 36.5 |
| **Promedio** | **26.5** | **39.6** | **13.1** | **33.0** |

## Notas

- Todas las corridas se ejecutaron en el mismo entorno aislado (VM + Docker + Terraform).
- Intervalo de verificaci\'on de salud: 5 s. Timeout de verificaci\'on: 2 s.
- La estrategia de menor MTTR fue la ventana deslizante en los cuatro tipos de fallo.
- No se registraron falsos positivos en ninguna de las 10 corridas de control.
- Datos crudos (logs JSON individuales por corrida) no incluidos en el repositorio por tama\~no; el script `consolidate.py` los procesa desde `experimento/monitoreo/`.
