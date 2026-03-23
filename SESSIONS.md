# SESSIONS.md — Historial de sesiones CDG Agent

> Historial completo de sesiones, valores de referencia, próximos pasos y pendientes.
> Ver CLAUDE.md para la parte operativa del proyecto.

---

## ✅ Completado (sesiones 1-17)

**S1 — Limpieza repo:** Eliminados archivos basura (DB duplicada, 23 scripts, tests frontend). `chore: limpieza pre-refactor`

**S2 — Reescritura `basic_queries.py`:** 4 bugs corregidos (PRECIO_STD como coste operativo, cuentas gasto incompletas, redistribución oct de GASTOS_CENTRO €0, bloque duplicado). Validado G1 oct: ingresos €32,560, beneficio €26,944, margen 82.75%.

**S3-S4 — Queries backend + agentes:** `period_queries.py`, `gestor_queries.py`, `comparative_queries.py`, `incentive_queries.py` reescritas con patrón correcto (MOVIMIENTOS, no PRECIO_STD como coste). `auth.py` + `gestor_agent.py` creados. Commits: `7fb5e0f`, `83d8db3`.

**S5-S6 — Integración + POC end-to-end:** `main.py` + `api.js` con endpoints chat gestor. Deployment corregido `gpt-5.4`→`gpt-4o`. LangChain migrado a LangGraph `create_react_agent`. POC validado con datos reales en ~7s.

**S7 — Ambos agentes validados:** GestorAgent 3/3, CDGAgent 2/2. Fixes routing `user_role` en `chat_agent.py`/`main.py`, keywords español en `cdg_agent.py`. Commit: `2590270`.

**S8 — Dashboard Gestor funcional:** 6 bugs en `analyticsService.js` (datos mock→reales, pivot dos pasos, endpoints 404). Wiring `GestorView.jsx` corregido (`externalChartData`). Commits: `50f92c2`→`41f37ef`. Bugs React posteriores: loop infinito (`filtersRef`), pivot fallback `success:true`, `chart_prompts.py` fix metric/dimensión CLIENTES. Commits: `74cdb71`, `7000c99`.

**S9 — Dashboard Dirección funcional:** `gestores-ranking` reescrito para INGRESOS/MARGEN_NETO/ROE. Pivot wiring fix. `PIVOTABLE_CONFIG` ampliada. Commit: `9911aa5`.

**S10 — Chat CDG:** Routing expandido (`cdg_intents` + REGLA 2b catch-all CDG), `format_response()` kwargs fix. Commit: `a96db0e`.

**S11-S12 — UI completa + Rebrand:** Fix chart type snake_case. Rediseño UI (theme 8px, index.css). Rebrand "CDG Intelligence", paleta Accenture (#A100FF). Precios REAL ocultos para Gestor. Prompts reescritos (business focus). KPIs iconos, Skeleton loading, Chat header #1A0033. Commits: `fd328a3`, `d3c2969`, `b0baa97`, `9c44f31`, `15f1366`, `cb7b222`, `618348e`.

**S13-S14 — Animaciones + Fix CDG pivot:** framer-motion (stagger cards, fade charts). Botón Volver DireccionView. Fix pivot DireccionView: derivar `userRole` de `options.mode` → `CONTROL_GESTION`. Commits: `1d8e8bf`, `930e54c`, `f7d1925`, `4c90fc3`.

**S15-S16 — Auditoría + corrección BD:** 4 bugs críticos corregidos (gastos sep 12×oct, Bilbao €0, Privada<Minorista, Javier Fernández -201%). 220 contratos, ~2,900 mov. Backup: `BM_CONTABILIDAD_CDG_backup_20260315.db`. Commit: `25ba3c5`.

**S17 — Calidad + ROE grupo:** Hardcoded 216→220 en `cdg_agent.py` + `system_prompts.py`. ROE grupo 75%→36.77% (fondeo €180k + provisión €45k insertados). Commits: `cd63e7e`, `97fcaf8`.

**S18 — Compactación CLAUDE.md + tests + 2 fixes en main.py:**
- CLAUDE.md reducido 40.4k→12.8k chars (commit `73156c8`)
- Fix 1: `/charts/gestores-ranking` `rows[:15]` movido a post-sort → Privada gestores (Javier Fernández €42,995) lideran correctamente rankings INGRESOS/MARGEN_NETO
- Fix 2: `/chat/message` ignoraba `req.user_role` → CDG users ya no bloqueados por guardia de gestor (effective_context merge). Commit `bd8fab9`

**S19 — completada (commit `c857da7`):**
- FIX1 ✅ CDG ROE: `GET /kpis/consolidado` + GLOBAL_KPI type → responde 36.77% correctamente
- FIX2 ✅ CDG evolucion: `get_evolucion_gestores_sep_oct()` + EVOLUCION_GESTORES type → identifica 12 retrocesos
- FIX3 ✅ Margen unificado: `abs(gastos)` en `gestor_queries` y `comparative_queries` → margen consistente
- FILTER ✅ Añadido `'66'` al filtro gastos centrales en 4 archivos → ROE correcto 36.77% (sin él era 67%)
- NEW ✅ `GET /analytics/fabrica` + `FabricaModelSection.jsx` en DireccionView

**S20 — completada (commit `d3788f9` + `.env`):**
- CLAUDE.md: filtro 66 corregido en secciones 5.5 y 9
- Diagnóstico 404: puerto 8000 tiene procesos zombie con código pre-S19. Se creó `frontend/.env` apuntando a puerto 8004 (código S19 correcto)
- Verificados todos los endpoints DireccionView en 8004: 9/9 OK ✅
- Valores de referencia confirmados: gestor 1 margen 44.55% ✅, ROE grupo 36.77% ✅, fábrica cedida 83.98% ✅

**S21 — completada (commit `fe77403`):**
- FIX1: `total_contratos_activos` filtra por FECHA_ALTA≤último día del período. BD: 29 contratos con FECHA_ALTA incorrecto en oct → movidos a `2025-09-01`. Resultado: sep=216 ✓, oct=220 ✓.
- FIX3: `FabricaModelSection.jsx` compactado a banda ~140px. Eliminado gráfico de barras. Variación oct vs sep como texto ▲/▼.
- FIX4: `DeviationAnalysis.jsx` sin `height:'100vh'` ni `minHeight:'95vh'`. Altura adaptativa.

**S22 — YTD implementado y luego revertido:**
- YTD backend implementado en commit `510bb0a`, luego revertido con `git revert 510bb0a` (commit `36ac179`) — decisión: MoM es el modelo correcto.
- Bug fix ✅: `PercentageOutlined` → `EuroCircleOutlined` en FabricaModelSection (commit `d66933c`, NO revertido).

**S23 — completada (commits `36ac179`, `e7dbf08`, `4d8b534`):**
- REVERT ✅: `git revert 510bb0a` → MoM restaurado en los 6 archivos de queries + main.py
- DB scaling ✅: 825 rows `76%` oct-2025 × 1.052806 → oct €624k (+4.04% vs sep €599k ✓)
- Fábrica oct ✅: cedido €123,278 (84.01%), variación +4.54% vs sep
- Labels ✅: `ROE Grupo`, `Ingresos del Mes`, `Cartera Activa`, TopBar "Mes seleccionado"
- Prompts ✅: MoM model note en `gestor_agent._build_system_prompt` + `FINANCIAL_ANALYST_SYSTEM_PROMPT`

**S24 — completada (commits `5036b23`, `d5f8521`, `1e05f63`):**
- FIX ✅: `get_centro_metricas_financieras` aplica FECHA_ALTA. Sep 5 centros: 68+62+30+27+29=**216** ✓
- FIX ✅: `FabricaModelSection` usa período dinámico — sep muestra sep_2025, oct muestra oct_2025, títulos dinámicos
- FIX ✅: CDG agente: `get_contratos_nuevos_periodo` añadido. Agente responde "4 contratos nuevos en oct"

**S25 — completada:**
- Split CLAUDE.md → CLAUDE.md (operativo, <6k chars) + SESSIONS.md (historial completo)

**S26 — completada (commits `48465bc`, `13e1e89`, `229eee1`, `04b7a28`):**
- B1 ✅ App.jsx ConfigProvider: `colorLink:'#A100FF'`, Tabs tokens (inkBarColor/itemSelectedColor), Button colorPrimary explicit
- B2 ✅ KPICards: variation display as Tag (green #52c41a / red #E5002B), Tooltip per card with business descriptions, descriptions updated to spec
- B3 ✅ GestoresTable.jsx: new component with 7 cols, expandable drill-down (productos/by-gestor), seg/centro filters, sort, variation sep→oct Tag; added as "Tabla Detallada" tab in DireccionView
- B4 ✅ @ant-design/x@1.0.6 installed (antd 5.26.7 compatible); ChatInterface: Bubble.List (user #A100FF / assistant #F3E8FF+border) + Sender; markdown bold rendering; backend wiring unchanged

**S27 — completada (WOW Visual Redesign):**
- FIX ✅ Tooltip Recharts/ChartJS: `context.parsed.y||context.parsed.x` → discriminación correcta por `chartType === 'horizontal_bar'` → `context.parsed.x`; valores reales en tooltips
- B1 ✅ Dark mode global: `theme.darkTheme` palette (#0A0014/#120020/#1A0033), `index.css` body dark + scrollbar + selection, `App.jsx` ConfigProvider tokens dark (colorBgContainer, colorBgLayout, colorBgElevated, colorBorder, colorText, Select/Table/Input/DatePicker/Dropdown/Tooltip/Tabs dark)
- B2 ✅ LandingPage v6: Three.js CDN neural-network canvas (80 nodos, r134), CSS fallback `@keyframes`, `framer-motion` fade-in estalonado, glassmorphism cards (rgba(161,0,255,0.08) + backdrop-filter), glow title `text-shadow`, botones glassmorphism
- B3 ✅ KPICards: `useCountUp` hook (rAF, ease-out cúbico), `IntersectionObserver` por card, dark glow style (rgba(18,0,32,0.85) + backdrop-filter, border rgba(161,0,255,0.25→0.5) hover, box-shadow glow), tags variación MoM en neón (#00FF88 positivo / #FF3366 negativo)
- B4 ✅ InteractiveCharts: tooltip dark (rgba(26,0,51,0.95)), grid rgba(161,0,255,0.08), ejes #A87BC8, leyenda #A87BC8, cards dark #120020
- B5 ✅ ChatInterface: pulsing green dot "Activo", typing dots CSS animation (3 spans bounce escalonado), mensajes asistente fondo #1A0033, área mensajes #0A0014, Sender dark border rgba(161,0,255,0.3), accessDenied banner dark red
- B6 ✅ Animaciones: DireccionView+GestorView layout #0A0014 + `motion.div` fade-in Content (opacity 0→1, 0.4s), GestoresTable `motion.tr` row stagger (opacity/x -20→0, delay index×0.04), TopBar `border-bottom: 1px solid rgba(161,0,255,0.5)` glow

---

## 📊 Valores de referencia definitivos (post-sesión-24)

| Métrica | Valor |
|---|---|
| Total contratos | 220 oct / 216 sep (cartera acumulada FECHA_ALTA) |
| Total movimientos | ~2,900+ |
| **Modelo temporal** | **MoM** ingresos/gastos/ROE + **cartera acumulada** contratos |
| Sep MoM ingresos | €599,759 / ROE 35.94% / 216 contratos |
| Oct MoM ingresos | **€624,000** / ROE **39.96%** / 220 contratos (+4.04% oct>sep ✓) |
| Gastos centrales MoM | sep -€278,410 / oct -€271,251 (incluye fondeo 660001 -€180k) |
| Modelo fábrica oct | cedido €123,278 (84.01%), retenido €23,471, desv -0.99% vs 85% |
| Fábrica oct vs sep | +4.54% variación cedido gestora (sep €117,926) |
| Margen por segmento oct | Privada 91.8% > Minorista 85.7% > Empresas 80.9% > Personal 72.4% > Fondos 66.0% |
| Evolucion gestores oct | 10 mejora / 8 estable / 12 retroceso (umbral ±5%) |
| Outlier aceptado | G8 Pablo Moreno (-57.4% sep): fondos lumpy |
| Gestor 1 oct margen | 44.55% (ingresos €32,238 / gastos directos -€3,079 / redistribuidos -€14,795) |
| Avg Privada oct | €37,656 (2.01× Minorista €19,697) |

---

## ⏭️ Próximo paso al retomar (post-S27)

**Para iniciar el sistema:**
```bash
cd backend && python main.py
# o: python -m uvicorn main:app --host 127.0.0.1 --port 8000
cd frontend && npm start
```

⚠️ Puerto: el backend arranca siempre en 8000 (definido en `.env` raíz y `main.py`).
`frontend/.env` debe apuntar a `http://localhost:8000`.

**Pendiente menor (no bloquea demo):**
- ROE KPICards = promedio aritmético de 5 centros (~32.6% sep) vs ROE grupo (35.94%). Diferencia por fórmula, no un error crítico
- `kpis_financieros.margen_neto_pct` en endpoint centro = 159% (bug fórmula, campo no usado en UI)
- Distribución contratos inconsistente entre `/kpis/centro/{id}/financieros` y `count_contratos_by_centro`

---

## ⚠️ Pendiente de decisión

- `MAESTRO_CONTRATOS_BACKUP_20250922_002703` — tabla basura en la BD, pendiente de `DROP TABLE`
- `backend/src/utils/initial_agent.py` — usa `openai` SDK directo en lugar de LangChain, pendiente de reescribir (no bloquea la POC)
- `GET /basic/precios-std` y `GET /prices/comparison` — devuelven 404; no se usan en ningún flujo activo
- `analyticsService.js:2857` — `.replace('Fondo Banca March', 'Fondos CDG')` mantiene el string del nombre real en BD (no es UI-visible, no se toca)
- `BM_CONTABILIDAD_CDG_backup_20260315.db` — backup de la BD pre-corrección, mantener hasta confirmar que el sistema arranca correctamente
