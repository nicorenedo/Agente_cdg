"""
gestor_prompts.py — Prompts del GestorAgent
============================================
S43: gestor_agent.py construye su system prompt con _build_system_prompt()
internamente y NO importa desde system_prompts.py.

Este archivo centraliza los prompts SQL para consultas de gestor.
Actualmente no son importados activamente (clasificación/generación SQL
fue reemplazada por el DeterministicQueryRouter en S40).

Schema SQL real (BM_CONTABILIDAD_CDG.db) — referencia corregida:
  Ingresos  : SUM(IMPORTE) WHERE CUENTA_ID LIKE '76%'
  Gastos dir: ABS(SUM(IMPORTE)) WHERE SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69') AND CONTRATO_ID IS NOT NULL
  Gastos cen: ABS(SUM(IMPORTE)) WHERE SUBSTR(CUENTA_ID,1,2) IN ('62','64','66','68','69') AND CONTRATO_ID IS NULL
  Redistrib : fondeo(660001) × (hip_gestor/total_hip) + otros_centrales × (ctos_gestor/total_fin)
  Período   : strftime('%Y-%m', FECHA) = '{periodo}'  -- formato YYYY-MM
  Tabla base: MOVIMIENTOS_CONTRATOS
  NO existe : LINEA_CDR como filtro de ingresos/gastos operativos
"""

# Placeholder — prompts de clasificación/generación de SQL para gestor.
# Si se reutiliza el flujo DYNAMIC_SQL para gestores, mover aquí los prompts
# de GESTOR_QUERIES_GENERATION_PROMPT desde system_prompts.py con el schema correcto.
