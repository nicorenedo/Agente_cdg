# CDG Intelligence v2 — Kutxa-CdG

> Contexto maestro operativo. Léelo completo antes de escribir código.
> Historial de sesiones en SESSIONS.md.
> Documentos de planificación en docs/.

---

## ⚠️ ADVERTENCIAS CRÍTICAS

1. **LLM: Azure OpenAI — NO Anthropic API.** Usa `langchain-openai` con credenciales del `.env`. No uses `anthropic` SDK.
2. **El código v1 existente puede contener errores.** Validar antes de reutilizar. Ante la duda: reescribir.
3. **Reconstrucción de dentro hacia fuera.** Infraestructura → agentes → knowledge base → frontend → QA.
4. **El frontend visual no se toca.** La calidad visual del frontend v1 está consolidada. Solo se añaden componentes nuevos AI Act y se limpia `analyticsService.js`.
5. **Tres patas en paralelo en cada fase**, no en serie:
   - Pata agéntica (LangGraph + agentes)
   - Pata de observabilidad (LangSmith + DecisionLogger)
   - Pata AI Act (linaje, descomposición, confidence, HITL, doc Art. 11)
6. **Cada sesión actualiza `AI_ACT_MAPPING.md` §6** con el grado de cumplimiento alcanzado.

---

## 1. Contexto del proyecto

**CDG Intelligence** es un copiloto de Control de Gestión bancario basado en IA agéntica.

La **v1 es una POC** que demuestra el caso. La **v2 se reconstruye desde cero** con tres objetivos:

1. **Arquitectura modular y observable** — LangGraph + agentes especializados + LangSmith trazado end-to-end.
2. **Mejora de calidad y funcionalidad** — Query Rewriter, mejor calidad de output, descomposición de efectos, exportación HTML/email.
3. **AI Act ready by design** — linaje del dato, registro auditable de decisiones, confidence scoring, HITL, documentación Art. 11. No como parche al final: integrado en cada fase desde el origen.

El frontend mantiene el diseño Accenture (paleta #A100FF), es temable para futuros clientes y se respeta su calidad visual actual.

- **Tres perfiles:** `control_gestion`, `gestor`, `validator` (nuevo, para HITL)
- **Datos:** BD SQLite con 20 meses de histórico bancario sintético (sep-2024 a abr-2026)
- **LLM:** Azure OpenAI — configurar credenciales en `.env` según `.env.example`

## 2. Estado actual

**Fase 0 completada.** Repo limpio y listo para la reconstrucción v2.

Leer en este orden antes de empezar cualquier sesión:

1. `docs/RECONSTRUCTION_AUDIT.md` — qué hay en v1, qué conservar, qué reconstruir
2. `docs/ARCHITECTURE_V2.md` — arquitectura objetivo con LangGraph + capa AI Act
3. `docs/RECONSTRUCTION_PLAN.md` — 6 fases, criterios de paso, riesgos
4. `docs/AGENT_CONTRACTS.md` — contratos de cada agente
5. `docs/AI_ACT_MAPPING.md` — **mapeo AI Act → componentes técnicos**. Imprescindible para entender qué satisface cada componente AI Act y qué evidencias debe producir.

## 3. Stack técnico v2

| Capa | Tecnología |
|------|-----------|
| Orquestación agéntica | LangGraph + LangChain |
| LLM | Azure OpenAI (gpt-4o) |
| Observabilidad técnica | LangSmith (tracing + evals) |
| **Observabilidad regulatoria** | **`DecisionLogger` + BD** |
| Backend | FastAPI + Python 3.11+ |
| Templating prompts | Jinja2 (NO hardcoding en código) |
| Datos | SQLite + Pandas |
| Forecast | Prophet (heredado v1, no tocar) |
| Knowledge base | ChromaDB + sentence-transformers |
| Validación | Pydantic v2 |
| Frontend | React 18 + Ant Design 5 + Recharts (heredado v1, no se reformatea) |

## 4. Estructura de directorios v2

```
backend/
├── core/
│   ├── graph/
│   │   ├── orchestrator.py
│   │   ├── nodes/                  # un archivo por agente, incluye:
│   │   │   ├── query_rewriter.py   # 🆕 pre-procesador del Orchestrator
│   │   │   ├── hitl_validator.py   # 🆕 decide activación de HITL
│   │   │   └── ...
│   │   └── edges.py
│   ├── agents/                     # base_agent.py, react_agent.py
│   ├── tools/                      # tools atómicas, incluye:
│   │   ├── effect_decomposer.py    # 🆕 descomposición fija de efectos
│   │   └── ...
│   ├── prompts/                    # plantillas *.j2 (Jinja2)
│   └── state.py                    # CDGState TypedDict extendido AI Act
├── compliance/                     # 🆕 capa de gobernanza AI Act
│   ├── decision_logger.py          # persistencia decision_logs
│   ├── lineage_tracker.py          # middleware anotación source
│   ├── confidence_scorer.py        # scoring 0.0-1.0
│   ├── policy_enforcer.py          # políticas configurables banco
│   ├── art11_doc_generator.py      # generador doc técnica
│   └── schemas.py                  # Pydantic schemas compliance
├── data/
│   ├── queries/                    # SQL puro
│   ├── calculator.py               # cálculos centralizados
│   ├── database.py
│   └── seed/
├── forecast/                       # heredado v1, MANTENER intacto
├── knowledge/                      # ChromaDB + loaders + citator unificado lineage
├── observability/                  # LangSmith + tags compliance
├── evals/                          # batería tests
│   ├── s77_functional.py
│   ├── s88_qualitative.py
│   ├── compliance_eval.py          # 🆕
│   ├── robustness_eval.py          # 🆕
│   ├── risk_register.json          # 🆕
│   └── datasets/
├── api/
│   ├── routes/                     # endpoints, incluye:
│   │   ├── feedback.py             # 🆕
│   │   ├── hitl.py                 # 🆕
│   │   ├── decision_log.py         # 🆕
│   │   └── compliance.py           # 🆕
│   └── schemas.py
├── config/
│   ├── data_config.py
│   ├── business_rules.py
│   ├── brand_config.py
│   ├── compliance_config.py        # 🆕 umbrales HITL, retención, políticas
│   └── settings.py
└── main.py

frontend/
└── src/
    ├── theme/                      # heredado intacto
    ├── components/
    │   ├── Chat/                   # heredado intacto
    │   ├── Dashboard/              # heredado intacto (calidad visual)
    │   ├── compliance/             # 🆕 componentes AI Act
    │   │   ├── FeedbackWidget.jsx
    │   │   ├── DataLineagePopover.jsx
    │   │   ├── ConfidenceBadge.jsx
    │   │   ├── EffectBreakdown.jsx
    │   │   └── HITLConsole.jsx
    │   └── export/
    ├── pages/                      # heredado intacto
    └── services/
        ├── analyticsService.js     # único reescrito: cliente HTTP fino
        ├── feedbackService.js      # 🆕
        ├── hitlService.js          # 🆕
        └── lineageService.js       # 🆕

docs/
├── RECONSTRUCTION_AUDIT.md
├── ARCHITECTURE_V2.md
├── RECONSTRUCTION_PLAN.md
├── AGENT_CONTRACTS.md
├── AI_ACT_MAPPING.md               # 🆕 documento fundacional AI Act
├── ART11_TECHNICAL_DOC.md          # 🆕 generado en F5
├── USER_MANUAL.md                  # 🆕 manual del desplegador
├── QMS.md                          # 🆕 sistema de gestión de calidad
├── RISK_REGISTER.md                # 🆕 registro de riesgos vivo
└── data_generation/
```

## 5. Los 11 agentes / componentes (LangGraph + capa AI Act)

| Agente / componente | Tipo | LLM calls | Activación |
|--------|-----------|-----------|-----------|
| `QueryRewriter` 🆕 | Agente | 1 (small) | Siempre primero |
| `Orchestrator` | Agente | 1 (clasifica) | Siempre tras Rewriter |
| `PermissionAgent` (+ `PolicyEnforcer`) | Agente + servicio | 0 | Siempre — transversal |
| `ContextEnricher` | Agente | 0 (determinista) | Compleja / forecast |
| `DataAgent` (+ `LineageTracker`) | Agente + middleware | 1 (selecciona query) | Consultas con datos |
| `CalculationAgent` (+ `EffectDecomposer`) | Agente + tool | 0 (determinista) | Consultas con datos |
| `ForecastAgent` | Agente | 1 (selecciona tool) | Consultas forecast |
| `InsightAgent` | Agente | 1 | Consultas con interpretación |
| `KnowledgeAgent` | Agente | 1 (síntesis RAG) | Consultas knowledge |
| `HITLValidator` 🆕 | Agente | 0 (reglas) | Siempre tras Confidence, antes Narrator |
| `NarratorAgent` (+ `ConfidenceScorer`) | Agente + hook | 1 | Siempre penúltimo |
| `DecisionLogger` 🆕 | Servicio | 0 | Siempre al cierre del grafo |

**Principio clave:** el Orchestrator activa solo los agentes necesarios. Consulta simple = 4 LLM calls. Compleja = 5. Forecast = 4. Knowledge = 4.

## 6. Reglas de desarrollo (anti-patrones prohibidos)

- ❌ **Sin hardcoding** de valores de negocio en agentes o queries. Todo en `config/`.
- ❌ **Sin god-strings en prompts.** Solo plantillas Jinja2 con `{{ variables }}`.
- ❌ **Sin S46-retry manual.** Tool-calling obligatorio en system prompt.
- ❌ **Sin lógica de negocio en queries SQL.** SQL puro en `data/queries/`.
- ❌ **Sin lógica de negocio en frontend.** `analyticsService.js` es cliente HTTP fino.
- ❌ **Sin tocar la calidad visual del frontend.** Solo añadir componentes nuevos AI Act y limpiar lógica de negocio.
- ❌ **Sin saltarse `LineageTracker` en DataAgent / KnowledgeAgent / ForecastAgent** — toda cifra del output debe traer source.
- ❌ **Sin saltarse `DecisionLogger`** — cada request del agente debe producir un decision_log persistido.
- ✅ **LangSmith tracing activo** desde Fase 1 — cada request trazado end-to-end con tags compliance.
- ✅ **Prompt caching Azure OpenAI** activo desde Fase 2 (system prompt ≥1024 tokens).
- ✅ **Cada agente con contrato** definido en `docs/AGENT_CONTRACTS.md` y mapeo en `docs/AI_ACT_MAPPING.md` §3.
- ✅ **Toda tool es atómica** y testeable de forma independiente.
- ✅ **Documentar cada sesión** en SESSIONS.md y actualizar este CLAUDE.md si cambia la estructura.
- ✅ **Actualizar AI_ACT_MAPPING.md §6** al cierre de cada fase con grado de cumplimiento real.

## 7. Datos de referencia (BD post-S84)

- **Rango temporal:** sep-2024 a abr-2026 (20 meses)
- **Período por defecto:** 2026-04
- **Contratos activos:** 351 acumulados · **Gestores:** 30 · **Clientes:** 142
- **Centros:** 5 finalistas (Madrid, Palma, Barcelona, Málaga, Bilbao)
- **Productos:** Hipotecario (margen ~29%), Depósito (~36%), Fondo RV (~97%)
- **Margen entidad:** 48.6% · **Dispersión gestores:** 45.1pp

## 8. Tablas AI Act en BD (Alembic)

Creadas en F0:

- `decision_logs` — registro de cada request del agente (Art. 12)
- `user_feedback` — feedback de usuario por respuesta
- `hitl_overrides` — eventos de validación/rechazo/override por humano (Art. 14)
- `data_sources` — registro vivo de fuentes de datos (Art. 10)

Schema detallado en `ARCHITECTURE_V2.md` §3.bis.

## 9. Arranque

```bash
# Backend
cd backend && python main.py
# o: python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Frontend
cd frontend && npm start
# frontend/.env: REACT_APP_API_BASE_URL=http://localhost:8000
```

## 10. Criterios de calidad por fase

- **Fase 1:** 48/48 tests funcionales (batería S77) + trazas LangSmith visibles + `compliance_eval.py` v0 (decision_logs persistidos con lineage)
- **Fase 2:** score cualitativo ≥4.5/5 (batería S88, 21 preguntas) + `compliance_eval.py` v1 (confidence + effect_decomposition + policy_violations + hitl_status correctos)
- **Fase 3:** KnowledgeAgent cita fuentes en cada respuesta + lineage unificado data/knowledge
- **Fase 4:** UI completa con `<FeedbackWidget>`, `<DataLineagePopover>`, `<ConfidenceBadge>`, `<EffectBreakdown>`, `<HITLConsole>` · cero regresión visual vs v1
- **Fase 5:** latencia consulta simple <2.5s, compleja <5.5s · `Art11DocGenerator` funcional · `robustness_eval.py` passing · documentos del proveedor redactados

## 11. Modelo de trabajo con Claude Code

**Sesión típica:**

1. Claude Code abre `CLAUDE.md` (este documento) + `RECONSTRUCTION_PLAN.md` (fase actual) + `AI_ACT_MAPPING.md` + `AGENT_CONTRACTS.md`.
2. Ejecuta los pasos planificados de la fase.
3. Al cerrar, actualiza:
   - `SESSIONS.md` con bitácora de la sesión.
   - `AGENT_CONTRACTS.md` si se implementó algún agente.
   - `AI_ACT_MAPPING.md` §6 con grado de cumplimiento alcanzado.
   - Este `CLAUDE.md` si cambió la estructura.
4. Commit + tag si corresponde.

**Validación humana (chat de contexto paralelo):** antes de aceptar el commit de una sesión, el chat de contexto verifica que los criterios de paso se cumplen y que la actualización del mapeo AI Act es coherente.

---

**Documento maestro. Actualizado en cada sesión que altere la estructura.**
