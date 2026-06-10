# Evaluaciones — CDG Intelligence v2

## Propósito

Estos datasets son la **referencia objetiva** contra la que se mide la reconstrucción v2.
Extraídos con SQL directo de `BM_CONTABILIDAD_CDG.db` y definidos con criterios
independientes del código de los agentes. Si hay conflicto entre el dataset y el agente,
el dataset tiene razón.

---

## Datasets

### `datasets/ground_truth.json`

Valores factuales extraídos con SQL puro de `BM_CONTABILIDAD_CDG.db` (post-S84).
**Son invariables entre v1 y v2.** Si el agente cita un número diferente, falla.

| Categoría | Descripción |
|-----------|-------------|
| `entidad_abr_2026` | Ingresos €644.589, margen 48.6%, contratos 351, gestores 30, clientes 142 |
| `productos_abr_2026` | FRV €313.789 (97.5%), Hip €297.104 (89.0%), Dep €33.696 (36.0%) |
| `centros_abr_2026` | Madrid €197.311 > Palma €174.042 > Bilbao €111.046 > Málaga €81.434 > Barcelona €80.756 |
| `gestores_abr_2026` | Ranking completo 30 gestores por ingresos. Top: Antonio Rodríguez García €36.847 |
| `gestor_1_kpis` | G1 Antonio Rodríguez García: ing €36.847, gas €3.032, margen 91.8%, 18 contratos |
| `gestor_1_clientes` | Clientes del gestor 1 con ingresos por cliente |
| `mom_entidad` | Mar→Abr 2026: €655.501 → €644.589 = **-1.66%** |
| `mom_gestor_1` | Mar→Abr 2026: €39.626 → €36.847 = **-7.01%** |
| `serie_historica` | 20 períodos (sep-2024 a abr-2026) con ingresos mensuales |

Script de extracción: `evals/extract_ground_truth.py`

---

### `datasets/s88_battery.json`

**21 preguntas cualitativas** con criterios de evaluación por LLM judge.
Ejecutadas originalmente en S88 con `gpt-5.4` (score global 4.4/5).

**5 dimensiones por pregunta** (pesos suman 1.0):
- `precision_datos` — cita cifras correctas de la BD
- `contextualizacion` — da contexto, no solo el dato
- `accionabilidad` — propone acción concreta
- `tono` — ejecutivo bancario en español
- `fluidez` — bien estructurado y fluido

**Grupos:**
- CDG (A1–A8): 8 preguntas al rol `control_gestion`
- Gestor (B1–B6): 6 preguntas al rol `gestor` (gestor_id=1)
- Forecast (C1–C7): 7 preguntas al `ForecastAgent`

**Tests con historial de fallos v1 (marcados con `s88_resultado_v1`):**
- `A6_estrategia` — respuesta vacía en v1, fix S89-F2
- `B3_evolucion` — margen 103% en v1, fix S89-F1
- `C4_crisis_frv` — shock mal mapeado en v1, fix S89-F3

**Objetivo v2:** score ≥ 4.5/5 en todas las dimensiones.

---

### `datasets/s77_battery.json`

**48 preguntas funcionales** con ground truth verificable (must_contain_values, must_mention,
must_not_contain).

Batería original ejecutada en S77 con resultado 48/48 (100%) tras fix S78a.
Las preguntas no se conservaron — reconstruidas desde los resultados documentados en
`SESSIONS_V1.md`. Los tests con campo `nota` son:
- Tests con historial documentado de fallo (A10, C11)
- Tests de no-regresión (A15, B07, C12, D07, E03, E04)

**Grupos:**
| Grupo | Tests | Descripción |
|-------|-------|-------------|
| CDG | 15 | CDGAgent rol dirección — KPIs, rankings, centros, gestores |
| Gestor | 8 | GestorAgent rol gestor (gestor_id=1) — personal, clientes, evolución |
| Forecast | 12 | ForecastAgent dirección — escenarios, what-if, macro |
| ForecastGestor | 8 | ForecastAgent gestor personal — proyecciones, objetivos |
| CalidadDato | 5 | Verificación calidad BD — no genéricos, márgenes correctos |

**Objetivo v2:** 48/48 (100%).

---

## Cómo evaluar

Los scripts de evaluación se construyen en fases:

```
Fase 1: evals/s77_functional.py   — ejecuta batería funcional contra backend v2
Fase 2: evals/s88_qualitative.py  — ejecuta batería cualitativa con LangSmith judge
```

Ambos leen los datasets de esta carpeta como fuente de verdad.

**Ejecución típica:**
```bash
# Fase 1 — funcional (pasa/falla por must_contain_values)
cd backend && python -m evals.s77_functional --endpoint http://localhost:8000

# Fase 2 — cualitativo (score 0-5 por LLM judge)
cd backend && python -m evals.s88_qualitative --endpoint http://localhost:8000
```

---

## Referencia rápida: valores clave

```
Entidad abr-2026:
  Ingresos:    €644.589
  Margen:      48.6%
  Contratos:   351
  Gestores:    30
  Clientes:    142

MoM entidad (mar→abr):   -1.66%
MoM gestor 1 (mar→abr):  -7.01%

Gestor 1 (Antonio Rodríguez García, Madrid):
  Ingresos:    €36.847
  Contratos:   18
  Margen directo: 91.8%

Top producto por ingresos: FRV €313.789 (97.5% margen directo)
Top centro por ingresos:   Madrid €197.311
```
