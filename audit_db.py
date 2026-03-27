import sqlite3
import json

db_path = r"C:\Users\nicolas.renedo\Documents\GEN AI\BancaMarch_CdG\backend\src\database\BM_CONTABILIDAD_CDG.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

results = {}

# 1. MAESTROS
cur.execute("SELECT GESTOR_ID, DESC_GESTOR, CENTRO, SEGMENTO_ID FROM MAESTRO_GESTORES ORDER BY GESTOR_ID")
results["gestores"] = [dict(r) for r in cur.fetchall()]

cur.execute("SELECT CLIENTE_ID, NOMBRE_CLIENTE FROM MAESTRO_CLIENTES ORDER BY CLIENTE_ID")
results["clientes"] = [dict(r) for r in cur.fetchall()]

cur.execute("SELECT * FROM MAESTRO_CENTROS ORDER BY CENTRO_ID")
results["centros"] = [dict(r) for r in cur.fetchall()]

cur.execute("SELECT * FROM MAESTRO_SEGMENTOS ORDER BY SEGMENTO_ID")
results["segmentos"] = [dict(r) for r in cur.fetchall()]

cur.execute("SELECT * FROM MAESTRO_PRODUCTOS ORDER BY PRODUCTO_ID")
results["productos"] = [dict(r) for r in cur.fetchall()]

# 2. DISTRIBUCIÓN CONTRATOS
cur.execute("""
SELECT mg.GESTOR_ID, mg.DESC_GESTOR, mg.SEGMENTO_ID, COUNT(mc.CONTRATO_ID) as num_contratos
FROM MAESTRO_GESTORES mg
LEFT JOIN MAESTRO_CONTRATOS mc ON mg.GESTOR_ID = mc.GESTOR_ID
GROUP BY mg.GESTOR_ID ORDER BY mg.GESTOR_ID
""")
results["contratos_por_gestor"] = [dict(r) for r in cur.fetchall()]

cur.execute("""
SELECT mp.PRODUCTO_ID, mp.DESC_PRODUCTO, COUNT(mc.CONTRATO_ID) as num_contratos
FROM MAESTRO_PRODUCTOS mp
LEFT JOIN MAESTRO_CONTRATOS mc ON mp.PRODUCTO_ID = mc.PRODUCTO_ID
GROUP BY mp.PRODUCTO_ID
""")
results["contratos_por_producto"] = [dict(r) for r in cur.fetchall()]

cur.execute("""
SELECT cl.CLIENTE_ID, cl.NOMBRE_CLIENTE, COUNT(mc.CONTRATO_ID) as num_contratos
FROM MAESTRO_CLIENTES cl
LEFT JOIN MAESTRO_CONTRATOS mc ON cl.CLIENTE_ID = mc.CLIENTE_ID
GROUP BY cl.CLIENTE_ID ORDER BY num_contratos DESC
""")
results["contratos_por_cliente"] = [dict(r) for r in cur.fetchall()]

# Clientes sin contratos
cur.execute("""
SELECT cl.CLIENTE_ID, cl.NOMBRE_CLIENTE
FROM MAESTRO_CLIENTES cl
LEFT JOIN MAESTRO_CONTRATOS mc ON cl.CLIENTE_ID = mc.CLIENTE_ID
WHERE mc.CONTRATO_ID IS NULL
""")
results["clientes_sin_contratos"] = [dict(r) for r in cur.fetchall()]

# 3. MÉTRICAS FINANCIERAS POR GESTOR (octubre)
cur.execute("""
SELECT
    mg.GESTOR_ID, mg.DESC_GESTOR, mg.SEGMENTO_ID,
    COUNT(DISTINCT mct.CONTRATO_ID) as contratos,
    ROUND(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 2) as ingresos,
    ROUND(SUM(CASE WHEN mov.IMPORTE < 0 AND mct.CONTRATO_ID IS NOT NULL THEN mov.IMPORTE ELSE 0 END), 2) as gastos_directos,
    ROUND(SUM(mov.IMPORTE), 2) as margen_bruto
FROM MAESTRO_GESTORES mg
JOIN MAESTRO_CONTRATOS mct ON mg.GESTOR_ID = mct.GESTOR_ID
JOIN MOVIMIENTOS_CONTRATOS mov ON mct.CONTRATO_ID = mov.CONTRATO_ID
WHERE mov.FECHA = '2025-10-01'
GROUP BY mg.GESTOR_ID ORDER BY ingresos DESC
""")
results["metricas_oct_por_gestor"] = [dict(r) for r in cur.fetchall()]

# Ingresos por segmento
cur.execute("""
SELECT
    mg.SEGMENTO_ID,
    COUNT(DISTINCT mg.GESTOR_ID) as num_gestores,
    ROUND(AVG(sub.ingresos), 2) as avg_ingresos,
    ROUND(MIN(sub.ingresos), 2) as min_ingresos,
    ROUND(MAX(sub.ingresos), 2) as max_ingresos
FROM MAESTRO_GESTORES mg
JOIN (
    SELECT mct.GESTOR_ID, SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END) as ingresos
    FROM MAESTRO_CONTRATOS mct
    JOIN MOVIMIENTOS_CONTRATOS mov ON mct.CONTRATO_ID = mov.CONTRATO_ID
    WHERE mov.FECHA = '2025-10-01'
    GROUP BY mct.GESTOR_ID
) sub ON mg.GESTOR_ID = sub.GESTOR_ID
GROUP BY mg.SEGMENTO_ID
""")
results["ingresos_por_segmento"] = [dict(r) for r in cur.fetchall()]

# 4. MOVIMIENTOS - estadísticas
cur.execute("""
SELECT
    SUBSTR(CUENTA_ID, 1, 2) as tipo_cuenta,
    COUNT(*) as num_mov,
    ROUND(MIN(IMPORTE), 2) as min_importe,
    ROUND(MAX(IMPORTE), 2) as max_importe,
    ROUND(AVG(IMPORTE), 2) as avg_importe,
    SUM(CASE WHEN IMPORTE = 0 THEN 1 ELSE 0 END) as mov_cero
FROM MOVIMIENTOS_CONTRATOS
GROUP BY tipo_cuenta ORDER BY tipo_cuenta
""")
results["movimientos_por_tipo_cuenta"] = [dict(r) for r in cur.fetchall()]

# Movimientos extremos (outliers)
cur.execute("""
SELECT mov.MOVIMIENTO_ID, mov.CONTRATO_ID, mov.CUENTA_ID, mov.IMPORTE, mov.FECHA,
       mp.PRODUCTO_ID, mp.DESC_PRODUCTO
FROM MOVIMIENTOS_CONTRATOS mov
LEFT JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
LEFT JOIN MAESTRO_PRODUCTOS mp ON mc.PRODUCTO_ID = mp.PRODUCTO_ID
WHERE ABS(mov.IMPORTE) > 5000 OR mov.IMPORTE = 0
ORDER BY ABS(mov.IMPORTE) DESC
LIMIT 30
""")
results["movimientos_extremos"] = [dict(r) for r in cur.fetchall()]

# 5. FECHAS
cur.execute("""
SELECT FECHA, COUNT(*) as num_movimientos
FROM MOVIMIENTOS_CONTRATOS
GROUP BY FECHA ORDER BY FECHA
""")
results["fechas_movimientos"] = [dict(r) for r in cur.fetchall()]

cur.execute("""
SELECT MIN(FECHA_ALTA) as min_fecha, MAX(FECHA_ALTA) as max_fecha,
       SUM(CASE WHEN FECHA_ALTA > '2025-10-31' THEN 1 ELSE 0 END) as futura,
       SUM(CASE WHEN FECHA_ALTA < '2000-01-01' THEN 1 ELSE 0 END) as muy_antigua
FROM MAESTRO_CONTRATOS
""")
results["fechas_contratos"] = [dict(r) for r in cur.fetchall()]

cur.execute("""
SELECT FECHA_ALTA, COUNT(*) as cantidad
FROM MAESTRO_CONTRATOS
GROUP BY FECHA_ALTA ORDER BY cantidad DESC LIMIT 20
""")
results["distribucion_fechas_alta"] = [dict(r) for r in cur.fetchall()]

# 6. PRECIOS STD
cur.execute("SELECT * FROM PRECIO_POR_PRODUCTO_STD ORDER BY SEGMENTO_ID, PRODUCTO_ID")
results["precios_std"] = [dict(r) for r in cur.fetchall()]

# 7. PRECIOS REAL
cur.execute("SELECT * FROM PRECIO_POR_PRODUCTO_REAL ORDER BY SEGMENTO_ID, PRODUCTO_ID, FECHA_CALCULO")
results["precios_real"] = [dict(r) for r in cur.fetchall()]

# Desviaciones precio real vs std
cur.execute("""
SELECT r.SEGMENTO_ID, r.PRODUCTO_ID, r.FECHA_CALCULO,
    ROUND(r.PRECIO_MANTENIMIENTO_REAL, 2) as precio_real,
    ROUND(s.PRECIO_MANTENIMIENTO, 2) as precio_std,
    ROUND((r.PRECIO_MANTENIMIENTO_REAL - s.PRECIO_MANTENIMIENTO) / s.PRECIO_MANTENIMIENTO * 100, 2) as desviacion_pct
FROM PRECIO_POR_PRODUCTO_REAL r
JOIN PRECIO_POR_PRODUCTO_STD s ON r.SEGMENTO_ID = s.SEGMENTO_ID AND r.PRODUCTO_ID = s.PRODUCTO_ID
ORDER BY ABS(desviacion_pct) DESC
""")
results["desviaciones_precio"] = [dict(r) for r in cur.fetchall()]

# 8. INTEGRIDAD REFERENCIAL
cur.execute("""
SELECT COUNT(*) as mov_sin_contrato_valido
FROM MOVIMIENTOS_CONTRATOS mov
WHERE mov.CONTRATO_ID IS NOT NULL
AND mov.CONTRATO_ID NOT IN (SELECT CONTRATO_ID FROM MAESTRO_CONTRATOS)
""")
results["integridad_mov_contratos"] = [dict(r) for r in cur.fetchall()]

cur.execute("""
SELECT COUNT(*) as contratos_sin_gestor_valido
FROM MAESTRO_CONTRATOS mc
WHERE mc.GESTOR_ID NOT IN (SELECT GESTOR_ID FROM MAESTRO_GESTORES)
""")
results["integridad_contratos_gestores"] = [dict(r) for r in cur.fetchall()]

cur.execute("""
SELECT COUNT(*) as contratos_sin_cliente_valido
FROM MAESTRO_CONTRATOS mc
WHERE mc.CLIENTE_ID NOT IN (SELECT CLIENTE_ID FROM MAESTRO_CLIENTES)
""")
results["integridad_contratos_clientes"] = [dict(r) for r in cur.fetchall()]

cur.execute("""
SELECT COUNT(*) as contratos_sin_producto_valido
FROM MAESTRO_CONTRATOS mc
WHERE mc.PRODUCTO_ID NOT IN (SELECT PRODUCTO_ID FROM MAESTRO_PRODUCTOS)
""")
results["integridad_contratos_productos"] = [dict(r) for r in cur.fetchall()]

# 9. MODELO FABRICA FONDOS
cur.execute("""
SELECT
    mc.PRODUCTO_ID,
    mov.CUENTA_ID,
    COUNT(*) as num_movimientos,
    ROUND(SUM(mov.IMPORTE), 2) as total_importe,
    ROUND(AVG(mov.IMPORTE), 2) as avg_importe
FROM MOVIMIENTOS_CONTRATOS mov
JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
WHERE mc.PRODUCTO_ID = '600100300300'
AND mov.CUENTA_ID IN ('760024', '760025')
GROUP BY mc.PRODUCTO_ID, mov.CUENTA_ID
""")
results["modelo_fabrica"] = [dict(r) for r in cur.fetchall()]

# Verificar ratio 85/15
cur.execute("""
SELECT
    ROUND(SUM(CASE WHEN CUENTA_ID = '760025' THEN IMPORTE ELSE 0 END), 2) as gestora_85,
    ROUND(SUM(CASE WHEN CUENTA_ID = '760024' THEN IMPORTE ELSE 0 END), 2) as banco_15,
    ROUND(SUM(CASE WHEN CUENTA_ID = '760025' THEN IMPORTE ELSE 0 END) /
          NULLIF(SUM(CASE WHEN CUENTA_ID = '760024' THEN IMPORTE ELSE 0 END), 0), 4) as ratio_gestora_banco
FROM MOVIMIENTOS_CONTRATOS mov
JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
WHERE mc.PRODUCTO_ID = '600100300300'
""")
results["ratio_fabrica"] = [dict(r) for r in cur.fetchall()]

# 10. EVOLUCION SEP vs OCT
cur.execute("""
SELECT
    mg.GESTOR_ID, mg.DESC_GESTOR,
    ROUND(SUM(CASE WHEN mov.FECHA = '2025-09-01' AND mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 2) as ingresos_sep,
    ROUND(SUM(CASE WHEN mov.FECHA = '2025-10-01' AND mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 2) as ingresos_oct,
    ROUND((SUM(CASE WHEN mov.FECHA = '2025-10-01' AND mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END) -
           SUM(CASE WHEN mov.FECHA = '2025-09-01' AND mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END)) /
          NULLIF(SUM(CASE WHEN mov.FECHA = '2025-09-01' AND mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) * 100, 2) as variacion_pct
FROM MAESTRO_GESTORES mg
JOIN MAESTRO_CONTRATOS mct ON mg.GESTOR_ID = mct.GESTOR_ID
JOIN MOVIMIENTOS_CONTRATOS mov ON mct.CONTRATO_ID = mov.CONTRATO_ID
GROUP BY mg.GESTOR_ID ORDER BY mg.GESTOR_ID
""")
results["evolucion_sep_oct"] = [dict(r) for r in cur.fetchall()]

# 11. GASTOS CENTRALES
cur.execute("""
SELECT FECHA, SUBSTR(CUENTA_ID,1,2) as tipo, COUNT(*) as mov, ROUND(SUM(IMPORTE), 2) as total
FROM MOVIMIENTOS_CONTRATOS
WHERE CONTRATO_ID IS NULL
GROUP BY FECHA, tipo
""")
results["gastos_centrales"] = [dict(r) for r in cur.fetchall()]

# 12. Lineas CDR
cur.execute("SELECT * FROM MAESTRO_LINEA_CDR ORDER BY COD_LINEA_CDR")
results["lineas_cdr"] = [dict(r) for r in cur.fetchall()]

# 13. ROE por gestor (oct) - calculo simplificado
cur.execute("""
SELECT
    mg.GESTOR_ID, mg.DESC_GESTOR, mg.SEGMENTO_ID,
    ROUND(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 2) as ingresos,
    ROUND(ABS(SUM(CASE WHEN mov.IMPORTE < 0 THEN mov.IMPORTE ELSE 0 END)), 2) as gastos_totales,
    ROUND(SUM(mov.IMPORTE), 2) as beneficio,
    ROUND(SUM(mov.IMPORTE) / NULLIF(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) * 100, 1) as margen_pct
FROM MAESTRO_GESTORES mg
JOIN MAESTRO_CONTRATOS mct ON mg.GESTOR_ID = mct.GESTOR_ID
JOIN MOVIMIENTOS_CONTRATOS mov ON mct.CONTRATO_ID = mov.CONTRATO_ID
WHERE mov.FECHA = '2025-10-01'
GROUP BY mg.GESTOR_ID ORDER BY margen_pct DESC
""")
results["margen_por_gestor_oct"] = [dict(r) for r in cur.fetchall()]

# 14. Distribucion de importes por producto
cur.execute("""
SELECT
    mp.DESC_PRODUCTO,
    mov.CUENTA_ID,
    COUNT(*) as num_mov,
    ROUND(MIN(ABS(mov.IMPORTE)), 2) as min_abs,
    ROUND(MAX(ABS(mov.IMPORTE)), 2) as max_abs,
    ROUND(AVG(ABS(mov.IMPORTE)), 2) as avg_abs,
    ROUND(SUM(mov.IMPORTE), 2) as total
FROM MOVIMIENTOS_CONTRATOS mov
JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
JOIN MAESTRO_PRODUCTOS mp ON mc.PRODUCTO_ID = mp.PRODUCTO_ID
GROUP BY mp.DESC_PRODUCTO, mov.CUENTA_ID
ORDER BY mp.DESC_PRODUCTO, mov.CUENTA_ID
""")
results["importes_por_producto_cuenta"] = [dict(r) for r in cur.fetchall()]

# 15. Ratio gastos/ingresos por gestor
cur.execute("""
SELECT
    mg.DESC_GESTOR, mg.SEGMENTO_ID,
    ROUND(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 2) as ingresos,
    ROUND(ABS(SUM(CASE WHEN mov.IMPORTE < 0 AND mct.CONTRATO_ID IS NOT NULL THEN mov.IMPORTE ELSE 0 END)), 2) as gastos_directos,
    ROUND(ABS(SUM(CASE WHEN mov.IMPORTE < 0 AND mct.CONTRATO_ID IS NOT NULL THEN mov.IMPORTE ELSE 0 END)) /
          NULLIF(SUM(CASE WHEN mov.IMPORTE > 0 THEN mov.IMPORTE ELSE 0 END), 0) * 100, 1) as ratio_gasto_ingreso_pct
FROM MAESTRO_GESTORES mg
JOIN MAESTRO_CONTRATOS mct ON mg.GESTOR_ID = mct.GESTOR_ID
JOIN MOVIMIENTOS_CONTRATOS mov ON mct.CONTRATO_ID = mov.CONTRATO_ID
WHERE mov.FECHA = '2025-10-01'
GROUP BY mg.GESTOR_ID ORDER BY ratio_gasto_ingreso_pct
""")
results["ratio_gastos_ingresos"] = [dict(r) for r in cur.fetchall()]

conn.close()
print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
