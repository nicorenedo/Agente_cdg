# AI_ACT_MAPPING.md — Mapeo AI Act → Componentes CDG Intelligence v2

> Fecha: 2026-06-08 · Documento 4 de 4
> Acompaña a `RECONSTRUCTION_AUDIT.md`, `ARCHITECTURE_V2.md` y `RECONSTRUCTION_PLAN.md`.
> Se actualiza al cierre de cada fase de la reconstrucción.

---

## 0. Propósito

Este documento traduce las obligaciones del **Reglamento (UE) 2024/1689 (AI Act)** a componentes técnicos concretos de CDG Intelligence v2 y a evidencias auditables.

Tres usos:

1. **Guía de diseño** — antes de codificar un agente, se consulta qué artículos satisface y qué campos del estado debe escribir.
2. **Evidencia de conformidad** — al cierre de cada fase, se actualiza con el grado de cumplimiento por artículo y los artefactos entregables al supervisor.
3. **Argumento comercial** — Accenture entrega este documento al cliente como prueba de que el sistema está diseñado AI Act-ready desde el origen, no parcheado a posteriori.

---

## 1. Clasificación del sistema bajo AI Act

### 1.1 ¿Es CDG Intelligence un sistema de alto riesgo?

CDG Intelligence v2 es un sistema de IA generativa con orquestación agéntica que apoya decisiones de gestión en una entidad financiera. La clasificación bajo AI Act depende de su uso:

| Escenario de uso | Clasificación AI Act | Justificación |
|---|---|---|
| Análisis descriptivo de KPIs y desviaciones | Riesgo limitado (Art. 50) | Sistema de IA que interactúa con personas físicas |
| Apoyo a decisiones de gestión sin impacto directo en clientes finales | Riesgo limitado | No cae en Anexo III literal |
| Forecast usado para decisiones de pricing o de cartera | **Alto riesgo** (Anexo III) | Apoya decisiones que afectan condiciones contractuales |
| Outputs usados en informes regulatorios al supervisor | **Alto riesgo** *de facto* | Aunque no esté en Anexo III, exigencias sectoriales (DORA, EBA) lo equiparan |

**Decisión de diseño:** tratamos el sistema **como si fuera de alto riesgo** desde el origen. Tres motivos:

- Es más caro elevar un sistema de bajo riesgo a alto riesgo después que construirlo así.
- El cliente (entidad financiera) tiene su propia gobernanza de IA que probablemente lo exija aunque AI Act no lo obligue.
- Es argumento de venta diferencial: pocos competidores entregan agentes con readiness completo.

### 1.2 Roles bajo AI Act

| Rol | Quién | Obligaciones principales |
|---|---|---|
| **Proveedor (provider)** | Accenture | Art. 16 — diseño conforme · Art. 11 doc técnica · Art. 17 sistema de gestión de calidad · Art. 19 conservación de logs · Art. 21-22 cooperación con autoridades |
| **Desplegador (deployer)** | Entidad financiera (Banca March / Kutxabank / etc.) | Art. 26 — uso conforme · supervisión humana · monitorización de funcionamiento · información a personas afectadas |
| **Importador / Distribuidor** | N/A (entrega directa) | — |

Accenture vende el agente y su servicio recurrente; el banco lo opera. La línea de obligaciones está clara y el modelo de ingresos doble (build + run) se alinea con esta separación.

### 1.3 Marcos regulatorios complementarios

AI Act no vive solo en servicios financieros. Componentes específicos del CDG deben tener en cuenta:

- **DORA (Reglamento 2022/2554)** — resiliencia operativa digital. Aplica a todo software crítico en entidades financieras desde enero 2025.
- **EBA Guidelines on ICT and security risk management** — gobernanza de riesgos tecnológicos.
- **EBA Guidelines on outsourcing arrangements** — si Accenture opera la capa de servicio, aplica.
- **Guías del Banco de España / DGSyFP** — supervisor nacional, expectativas sectoriales.
- **GDPR** — datos personales si aparecen en KPIs por gestor o cliente.

Este documento se centra en AI Act. Los marcos complementarios se referencian donde aplica.

---

## 2. Mapeo Artículo → Componente

Para cada artículo relevante, se documenta: **qué exige**, **qué componente de v2 lo satisface** y **qué evidencia se entrega**.

### Art. 9 — Sistema de gestión de riesgos

**Qué exige:** sistema documentado para identificar, analizar, evaluar y mitigar riesgos previsibles del sistema de IA a lo largo de todo su ciclo de vida. Revisión periódica.

**Componentes que lo satisfacen:**

- `evals/risk_register.json` — registro vivo de riesgos identificados (alucinación, prompt injection, deriva, sesgo, sobreconfianza, etc.) con probabilidad, impacto y mitigación.
- `evals/s77_functional.py` + `evals/s88_qualitative.py` + `evals/latency_eval.py` — baterías de evaluación que se ejecutan en cada release.
- `evals/compliance_eval.py` *(nuevo)* — evaluador específico que mide conformidad: ¿el output tiene linaje? ¿hay confidence score? ¿se aplica HITL cuando corresponde?
- LangSmith Datasets — versionado de baterías de evaluación.

**Evidencia entregable:**

- Registro de riesgos actualizado por release.
- Informe trimestral con resultados de evaluación + decisiones de mitigación.

### Art. 10 — Datos y gobernanza del dato

**Qué exige:** los datos de entrenamiento, validación y prueba deben ser pertinentes, representativos, libres de errores y con propiedades estadísticas apropiadas. Trazabilidad del origen del dato.

**Componentes que lo satisfacen:**

- `DataLineageTracker` *(nuevo)* — middleware entre `DataAgent` y `CalculationAgent`. Anota cada cifra del output con su origen: `tabla`, `campo`, `período`, `validador`, `timestamp`, `query_id`.
- `data_lineage` en `CDGState` *(nuevo campo)* — estructura que viaja con cada cifra hasta el `NarratorAgent`.
- `knowledge/citator.py` — para outputs de RAG, ya implementado, comparte infraestructura de linaje.
- `data/queries/*.py` — SQL puro, versionado, sin lógica de negocio mezclada (auditable).
- `docs/data_generation/*` — documentación del origen de los datos sintéticos (relevante porque la POC usa datos sintéticos).

**Evidencia entregable:**

- Documento de origen del dato (data lineage report) por release.
- Cada respuesta del agente lleva linaje granular consultable vía endpoint `/decision-log/{id}/lineage`.

### Art. 11 — Documentación técnica

**Qué exige:** el proveedor mantiene documentación técnica completa del sistema antes de ponerlo en el mercado y la actualiza durante todo su ciclo de vida. Anexo IV detalla contenido mínimo.

**Componentes que lo satisfacen:**

- `Art11DocGenerator` *(nuevo)* — meta-tool que ensambla la documentación técnica a partir de `AGENT_CONTRACTS.md`, `ARCHITECTURE_V2.md`, datasets de evaluación y trazas LangSmith. Se ejecuta en cada release.
- `docs/ART11_TECHNICAL_DOC.md` *(nuevo, generado)* — documento vivo que cubre:
  - Descripción general del sistema y su propósito previsto
  - Elementos del sistema y proceso de desarrollo
  - Datos de entrenamiento / fine-tuning (si aplica)
  - Información sobre supervisión humana
  - Métricas de precisión y robustez
  - Cambios introducidos en cada release

**Evidencia entregable:**

- `ART11_TECHNICAL_DOC.md` actualizado por release.
- Histórico de versiones del documento (git tags).

### Art. 12 — Conservación de registros (logs)

**Qué exige:** registro automático de eventos durante la operación del sistema. Los logs deben permitir el seguimiento del funcionamiento, identificar situaciones de riesgo y facilitar la vigilancia post-comercialización.

**Componentes que lo satisfacen:**

- `DecisionLogger` *(nuevo)* — persistencia en BD de cada respuesta del agente con: `user_id`, `user_role`, `timestamp`, `original_query`, `rewritten_query`, `intent`, `agents_invoked`, `tools_called`, `final_response`, `model_version`, `confidence_score`, `data_lineage_ref`, `policy_violations`, `hitl_status`.
- Tabla `decision_logs` *(Alembic)* — schema versionado.
- LangSmith — trazabilidad técnica granular (prompts, tool calls, latency, tokens) que complementa el log de negocio.
- Endpoint `GET /decision-log/{id}` y `GET /decision-log/search` — recuperación para auditoría.

**Evidencia entregable:**

- Logs estructurados consultables por cualquier criterio (usuario, período, intención).
- Política de retención documentada (cuánto tiempo se conservan, cómo se anonimizan o purgan).

### Art. 13 — Transparencia e información a los usuarios

**Qué exige:** los sistemas de IA de alto riesgo deben diseñarse de forma que su funcionamiento sea suficientemente transparente para que los desplegadores puedan interpretar el output y usarlo apropiadamente.

**Componentes que lo satisfacen:**

- `EffectDecomposer` *(nuevo)* — método fijo de descomposición de efectos (precio · volumen · mix · riesgo). El output no es opaco: explica de dónde vienen los puntos básicos.
- `ConfidenceScorer` *(nuevo)* — hook al final del `NarratorAgent`. Cada output lleva un score 0.0–1.0 con breakdown por dimensión (calidad del dato · cobertura del histórico · ajuste a precedentes).
- Plantillas `narrator_*.j2` enriquecidas — el output incluye explícitamente: qué fuente, qué confianza, qué supuesto.
- Frontend: `<DataLineagePopover>`, `<ConfidenceBadge>`, `<EffectBreakdown>` — superficie de transparencia en UI.
- `docs/USER_MANUAL.md` *(nuevo)* — manual del desplegador con propósito previsto, limitaciones, ejemplos de uso correcto / incorrecto.

**Evidencia entregable:**

- Manual del desplegador entregado por release.
- Cada output muestra confidence + lineage clickeable en UI.

### Art. 14 — Supervisión humana

**Qué exige:** los sistemas de alto riesgo deben diseñarse para que las personas físicas puedan supervisar su funcionamiento de forma efectiva. Debe ser posible: entender capacidades y limitaciones, monitorizar funcionamiento, interpretar correctamente el output, decidir no usar el output, intervenir o anular.

**Componentes que lo satisfacen:**

- `HITLValidator` *(nuevo)* — agente que decide cuándo un output requiere validación humana (basado en `confidence_score`, `policy_violations`, política configurable por cliente).
- Flujo HITL en `CDGState`:
  - `hitl_status`: `"not_required" | "pending" | "validated" | "rejected" | "overridden"`
  - `hitl_metadata`: `validator_id`, `motivo`, `timestamp`
- Endpoints `POST /hitl/validate`, `POST /hitl/reject`, `POST /hitl/override` con persistencia.
- Frontend: `<HITLConsole>` — consola para validadores designados (no para todos los usuarios).
- Override registrado: si un humano anula el output, se persiste el motivo con valor legal.

**Evidencia entregable:**

- Documentación del flujo HITL: cuándo se activa, quién valida, qué se registra.
- Logs de override consultables por auditoría.

### Art. 15 — Precisión, robustez y ciberseguridad

**Qué exige:** los sistemas de alto riesgo deben alcanzar un nivel apropiado de precisión, robustez y ciberseguridad. Resistencia a errores, fallos e inconsistencias. Protección frente a intentos de explotar vulnerabilidades.

**Componentes que lo satisfacen:**

- `core/tools/sql_guard.py` — protección contra SQL injection (heredado v1, mantenido).
- `core/tools/query_parser.py` — validación de queries.
- `QueryRewriter` *(nuevo)* — sanitización y normalización de input antes del Orchestrator. Mitiga prompt injection.
- `PolicyEnforcer` *(nuevo, extensión de `PermissionAgent`)* — aplica políticas del banco (rangos permitidos, datos accesibles, acciones permitidas).
- `evals/robustness_eval.py` *(nuevo)* — batería de tests adversariales (prompt injection, prompts ambiguos, datos faltantes).
- `evals/latency_eval.py` — robustez de tiempo de respuesta.
- LangSmith metrics — tasa de error, latencia, tokens, agentes invocados.

**Evidencia entregable:**

- Reporte de tests adversariales por release.
- SLA de disponibilidad y precisión documentado.

### Art. 16 — Obligaciones del proveedor (transversal)

Accenture, como proveedor:

- Demuestra conformidad con Art. 9-15 (todo lo anterior).
- Mantiene `ART11_TECHNICAL_DOC.md` actualizado.
- Establece sistema de gestión de calidad (`docs/QMS.md` *nuevo*).
- Mantiene logs del sistema operados durante 6 meses como mínimo (configurable por contrato).
- Coopera con autoridades competentes.

### Art. 26 — Obligaciones del desplegador (cliente)

Información que Accenture provee al cliente para que cumpla SUS obligaciones:

- Manual del desplegador.
- Configuración recomendada de supervisión humana.
- Plan de monitorización post-despliegue.
- Plantilla de comunicación a personas afectadas (si aplica).

### Art. 50 — Transparencia de sistemas que interactúan con personas

Aplica como mínimo siempre (no solo alto riesgo):

- El frontend muestra explícitamente que el usuario interactúa con un sistema de IA.
- Contenido generado por IA está marcado como tal (los outputs del `NarratorAgent` se identifican como generados por IA).

---

## 3. Mapeo Componente → Artículos

Vista inversa: para cada componente nuevo o modificado, qué artículos satisface y qué fase de la reconstrucción lo introduce.

| Componente | Tipo | Fase | Art. 9 | Art. 10 | Art. 11 | Art. 12 | Art. 13 | Art. 14 | Art. 15 |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `QueryRewriter` | Nuevo agente | F1 | | | | ✓ | | | ✓ |
| `DataLineageTracker` | Nuevo middleware | F1 | | ✓ | | ✓ | ✓ | | |
| `EffectDecomposer` | Nueva tool / sub-agente | F2 | | | | | ✓ | | |
| `ConfidenceScorer` | Nuevo hook | F2 | ✓ | | | ✓ | ✓ | ✓ | ✓ |
| `PolicyEnforcer` | Extensión PermissionAgent | F2 | ✓ | | | ✓ | | ✓ | ✓ |
| `DecisionLogger` | Nuevo servicio + BD | F1-F2 | ✓ | | | ✓ | | | |
| `HITLValidator` | Nuevo agente + flujo | F2-F4 | ✓ | | | ✓ | | ✓ | |
| `Art11DocGenerator` | Meta-tool | F5 | | | ✓ | | | | |
| `FeedbackCollector` | API + UI | F4 | ✓ | | | ✓ | | ✓ | |
| `<DataLineagePopover>` | Componente UI | F4 | | | | | ✓ | | |
| `<ConfidenceBadge>` | Componente UI | F4 | | | | | ✓ | | |
| `<HITLConsole>` | Componente UI | F4 | | | | | | ✓ | |
| `<FeedbackWidget>` | Componente UI | F4 | ✓ | | | ✓ | | | |
| `<EffectBreakdown>` | Componente UI | F4 | | | | | ✓ | | |
| `evals/compliance_eval.py` | Eval suite | F5 | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ |
| `evals/robustness_eval.py` | Eval suite | F5 | ✓ | | | | | | ✓ |

---

## 4. Evidencias entregables al supervisor

Inventario de los artefactos que Accenture genera y mantiene como prueba de conformidad. Estos son los entregables del servicio recurrente (run) además de los del proyecto (build).

| Artefacto | Frecuencia | Generado por | Entregable a |
|---|---|---|---|
| `ART11_TECHNICAL_DOC.md` | Cada release | `Art11DocGenerator` | Supervisor a demanda · Cliente cada release |
| `evals/risk_register.json` actualizado | Trimestral | Manual + LangSmith | Cliente · Supervisor a demanda |
| Decision logs export | Bajo demanda | `DecisionLogger` | Auditoría interna · Supervisor en investigación |
| Informe de evaluación cualitativa (S88 + compliance) | Trimestral | LangSmith Evals | Cliente |
| Informe de tests adversariales | Cada release | `evals/robustness_eval` | Cliente |
| Manual del desplegador (`USER_MANUAL.md`) | Cada release | Manual + generación | Cliente · Usuarios finales |
| Política de retención de logs | Una vez · revisión anual | Documento legal | Cliente |
| Plan de monitorización post-deployment | Una vez · revisión anual | Documento técnico | Cliente |
| Sistema de gestión de calidad (`QMS.md`) | Una vez · revisión anual | Documento de Accenture | Auditoría · Supervisor |

---

## 5. Riesgos residuales conocidos

Riesgos que el sistema no elimina y que el desplegador debe asumir o mitigar:

| Riesgo residual | Mitigación recomendada al desplegador |
|---|---|
| Alucinaciones en outputs cualitativos | HITL obligatorio para decisiones materiales · Confidence score por debajo de umbral activa revisión |
| Deriva del modelo Azure OpenAI entre versiones | Monitorización mensual de score S88 · Retest al actualizar versión |
| Datos de entrada con errores no detectados | Doble validación con fuente alternativa para decisiones de >X € |
| Sesgo histórico en los datos (gestores con perfil X subrepresentados) | Análisis de sesgo trimestral · Documentado en `evals/bias_eval.py` |
| Prompt injection sofisticado vía documentos cargados a Knowledge Base | Filtrado de documentos en carga · Restricción de fuentes por área |

---

## 6. Roadmap de readiness por fase

Estado esperado al cierre de cada fase. Esto se cruza con `RECONSTRUCTION_PLAN.md` §9 (criterios de paso por fase).

### Cierre Fase 0
- ✅ `AI_ACT_MAPPING.md` creado (este documento).
- ✅ Tablas `decision_logs`, `user_feedback`, `hitl_overrides`, `data_sources` definidas en Alembic.
- ⏳ Cero implementación todavía.

### Cierre Fase 1
- ✅ `CDGState` extendido con campos AI Act (`data_lineage`, `decision_log_id`, `confidence_score`, `original_query`, `rewritten_query`, `hitl_status`, `user_feedback`, `policy_violations`, `model_version`, `effect_decomposition`, `hitl_metadata`, `confidence_breakdown`, `query_rewriter_metadata`).
- ✅ `QueryRewriter` operativo.
- ✅ `DataLineageTracker` middleware funcionando (cada query produce metadata de linaje).
- ✅ `DecisionLogger` persistiendo cada request en BD.
- ✅ LangSmith tags incluyen dimensión compliance.

### Cierre Fase 2
- ✅ `EffectDecomposer` funcionando (método fijo aplicado a outputs cuantitativos).
- ✅ `ConfidenceScorer` puntuando cada output.
- ✅ `PolicyEnforcer` aplicando políticas configurables.
- ✅ `HITLValidator` decide cuándo activar HITL (backend completo; UI llega en F4).
- ✅ `evals/compliance_eval.py` ejecutable.

### Cierre Fase 3
- ✅ `KnowledgeAgent` cita fuentes vía infraestructura compartida con `DataLineageTracker` (un solo modelo de linaje para datos y conocimiento).

### Cierre Fase 4
- ✅ UI completa: `<FeedbackWidget>`, `<DataLineagePopover>`, `<ConfidenceBadge>`, `<HITLConsole>`, `<EffectBreakdown>`.
- ✅ Endpoints `/chat/feedback`, `/hitl/*`, `/decision-log/*` expuestos.
- ✅ Loop de feedback usuario → LangSmith Datasets activo.

### Cierre Fase 5
- ✅ `Art11DocGenerator` ejecutable; primer `ART11_TECHNICAL_DOC.md` generado.
- ✅ `evals/robustness_eval.py` con batería adversarial.
- ✅ `USER_MANUAL.md` redactado.
- ✅ `QMS.md` redactado.
- ✅ Compliance dashboard `/compliance/metrics` operativo.
- ✅ Política de retención de logs documentada.
- ✅ Tag `v2.0.0` con readiness completa.

---

## 7. Glosario de términos AI Act

| Término | Definición operativa |
|---|---|
| **Sistema de IA de alto riesgo** | Sistema clasificado bajo Anexo III del AI Act o tratado como tal por decisión del proveedor |
| **Proveedor (provider)** | Persona física o jurídica que desarrolla un sistema de IA con vistas a su comercialización |
| **Desplegador (deployer)** | Persona física o jurídica que utiliza un sistema de IA bajo su autoridad |
| **Sistema de gestión de riesgos** | Proceso documentado para identificar, evaluar y mitigar riesgos del sistema |
| **Documentación técnica** | Documento del Art. 11 con contenido mínimo del Anexo IV |
| **Supervisión humana (HITL)** | Capacidad de personas físicas para entender, monitorizar e intervenir en el funcionamiento |
| **Registro automático** | Logs persistentes generados por el sistema durante operación (Art. 12) |
| **Linaje del dato** | Trazabilidad del origen, transformaciones y validaciones aplicadas a cada cifra |
| **Effect decomposition** | Descomposición estructurada de una variación financiera en sus efectos componentes (precio · volumen · mix · riesgo) |

---

**Próxima actualización:** al cierre de cada fase, actualizar §6 con el grado de cumplimiento real alcanzado.
