import sqlite3, json, os

conn = sqlite3.connect('backend/src/database/BM_CONTABILIDAD_CDG.db')
gt = {}

# 1. ENTIDAD ABR-2026
cur = conn.execute("""
    SELECT
        SUM(CASE WHEN CUENTA_ID LIKE '76%' THEN IMPORTE ELSE 0 END),
        ABS(SUM(CASE WHEN SUBSTR(CUENTA_ID,1,2) IN ('62','64','68','69') AND CONTRATO_ID IS NOT NULL THEN IMPORTE ELSE 0 END)),
        ABS(SUM(CASE WHEN SUBSTR(CUENTA_ID,1,2) IN ('62','64','66','68','69') AND CONTRATO_ID IS NULL THEN IMPORTE ELSE 0 END))
    FROM MOVIMIENTOS_CONTRATOS WHERE strftime('%Y-%m', FECHA) = '2026-04'
""")
ingresos, gastos_dir, gastos_cen = cur.fetchone()
beneficio = ingresos - gastos_dir - gastos_cen
margen = (beneficio / ingresos * 100) if ingresos > 0 else 0

contratos = conn.execute("SELECT COUNT(DISTINCT CONTRATO_ID) FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= '2026-04-30'").fetchone()[0]
n_gestores = conn.execute("""
    SELECT COUNT(DISTINCT mg.GESTOR_ID) FROM MAESTRO_GESTORES mg
    JOIN MAESTRO_CENTROS mce ON mg.CENTRO = mce.CENTRO_ID WHERE mce.IND_CENTRO_FINALISTA = 1
""").fetchone()[0]
n_clientes = conn.execute("""
    SELECT COUNT(DISTINCT mc.CLIENTE_ID) FROM MAESTRO_CONTRATOS mc
    JOIN MAESTRO_GESTORES mg ON mc.GESTOR_ID = mg.GESTOR_ID
    JOIN MAESTRO_CENTROS mce ON mg.CENTRO = mce.CENTRO_ID WHERE mce.IND_CENTRO_FINALISTA = 1
""").fetchone()[0]

print(f"ENTIDAD: ingresos={ingresos:,.2f}, gastos_dir={gastos_dir:,.2f}, gastos_cen={gastos_cen:,.2f}, beneficio={beneficio:,.2f}, margen={margen:.1f}%, contratos={contratos}, gestores={n_gestores}, clientes={n_clientes}")
gt['entidad_abr_2026'] = {
    'ingresos': round(ingresos,2), 'gastos_directos': round(gastos_dir,2),
    'gastos_centrales': round(gastos_cen,2), 'beneficio': round(beneficio,2),
    'margen_neto_pct': round(margen,1), 'contratos_activos': contratos,
    'n_gestores': n_gestores, 'n_clientes': n_clientes
}

# 2. POR PRODUCTO
cur = conn.execute("""
    SELECT mp.DESC_PRODUCTO, mp.PRODUCTO_ID,
        SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as ing,
        ABS(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID,1,2) IN ('62','64','68','69') AND mov.CONTRATO_ID IS NOT NULL THEN mov.IMPORTE ELSE 0 END)) as gas,
        COUNT(DISTINCT mc.CONTRATO_ID) as ctos
    FROM MOVIMIENTOS_CONTRATOS mov
    JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
    JOIN MAESTRO_PRODUCTOS mp ON mc.PRODUCTO_ID = mp.PRODUCTO_ID
    WHERE strftime('%Y-%m', mov.FECHA) = '2026-04'
    GROUP BY mp.DESC_PRODUCTO ORDER BY ing DESC
""")
productos = {}
for nombre, pid, ing, gas, ctos in cur.fetchall():
    mar_p = ((ing - gas) / ing * 100) if ing > 0 else 0
    print(f"  PROD {nombre}: ing={ing:,.2f}, gas={gas:,.2f}, margen={mar_p:.1f}%, ctos={ctos}")
    productos[nombre] = {'producto_id': pid, 'ingresos': round(ing,2), 'gastos_directos': round(gas,2),
                         'margen_directo_pct': round(mar_p,1), 'contratos': ctos}
gt['productos_abr_2026'] = productos

# 3. POR CENTRO
cur = conn.execute("""
    SELECT mce.DESC_CENTRO, mce.CENTRO_ID,
        SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as ing,
        COUNT(DISTINCT mc.CONTRATO_ID) as ctos, COUNT(DISTINCT mc.GESTOR_ID) as gest
    FROM MOVIMIENTOS_CONTRATOS mov
    JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
    JOIN MAESTRO_GESTORES mg ON mc.GESTOR_ID = mg.GESTOR_ID
    JOIN MAESTRO_CENTROS mce ON mg.CENTRO = mce.CENTRO_ID
    WHERE strftime('%Y-%m', mov.FECHA) = '2026-04' AND mce.IND_CENTRO_FINALISTA = 1
    GROUP BY mce.DESC_CENTRO ORDER BY ing DESC
""")
centros = {}
for nombre, cid, ing, ctos, gest in cur.fetchall():
    print(f"  CENTRO {nombre}: ing={ing:,.2f}, ctos={ctos}, gest={gest}")
    centros[nombre] = {'centro_id': cid, 'ingresos': round(ing,2), 'contratos': ctos, 'gestores': gest}
gt['centros_abr_2026'] = centros

# 4. RANKING GESTORES
cur = conn.execute("""
    SELECT mg.GESTOR_ID, mg.DESC_GESTOR, mce.DESC_CENTRO,
        SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as ing,
        ABS(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID,1,2) IN ('62','64','68','69') AND mov.CONTRATO_ID IS NOT NULL THEN mov.IMPORTE ELSE 0 END)) as gas,
        COUNT(DISTINCT mc.CONTRATO_ID) as ctos
    FROM MOVIMIENTOS_CONTRATOS mov
    JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
    JOIN MAESTRO_GESTORES mg ON mc.GESTOR_ID = mg.GESTOR_ID
    JOIN MAESTRO_CENTROS mce ON mg.CENTRO = mce.CENTRO_ID
    WHERE strftime('%Y-%m', mov.FECHA) = '2026-04' AND mce.IND_CENTRO_FINALISTA = 1
    GROUP BY mg.GESTOR_ID ORDER BY ing DESC
""")
gestores = []
for gid, nom, cen, ing, gas, ctos in cur.fetchall():
    mar_g = ((ing - gas) / ing * 100) if ing > 0 else 0
    g = {'gestor_id': gid, 'nombre': nom, 'centro': cen,
         'ingresos': round(ing,2), 'gastos_directos': round(gas,2),
         'margen_directo_pct': round(mar_g,1), 'contratos': ctos}
    gestores.append(g)
    print(f"  G{gid:>2} {nom:<30} ({cen:<10}): {ing:>10,.0f} | margen {mar_g:>5.1f}% | {ctos} ctos")
gt['gestores_abr_2026'] = gestores

# 5. GESTOR 1 CLIENTES + KPIs
g1_nom = g1_cen = "?"
cur = conn.execute("""
    SELECT mcl.NOMBRE_CLIENTE, mcl.CLIENTE_ID,
        SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as ing,
        COUNT(DISTINCT mc.CONTRATO_ID) as ctos
    FROM MOVIMIENTOS_CONTRATOS mov
    JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
    JOIN MAESTRO_CLIENTES mcl ON mc.CLIENTE_ID = mcl.CLIENTE_ID
    WHERE mc.GESTOR_ID = 1 AND strftime('%Y-%m', mov.FECHA) = '2026-04'
    GROUP BY mcl.NOMBRE_CLIENTE ORDER BY ing DESC
""")
clientes_g1 = [{'nombre': r[0], 'cliente_id': r[1], 'ingresos': round(r[2],2), 'contratos': r[3]} for r in cur.fetchall()]
gt['gestor_1_clientes'] = clientes_g1

cur = conn.execute("""
    SELECT
        SUM(CASE WHEN mov.CUENTA_ID LIKE '76%' THEN mov.IMPORTE ELSE 0 END) as ing,
        ABS(SUM(CASE WHEN SUBSTR(mov.CUENTA_ID,1,2) IN ('62','64','68','69') AND mov.CONTRATO_ID IS NOT NULL THEN mov.IMPORTE ELSE 0 END)) as gas,
        COUNT(DISTINCT mc.CONTRATO_ID) as ctos, mg.DESC_GESTOR, mce.DESC_CENTRO
    FROM MOVIMIENTOS_CONTRATOS mov
    JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
    JOIN MAESTRO_GESTORES mg ON mc.GESTOR_ID = mg.GESTOR_ID
    JOIN MAESTRO_CENTROS mce ON mg.CENTRO = mce.CENTRO_ID
    WHERE mc.GESTOR_ID = 1 AND strftime('%Y-%m', mov.FECHA) = '2026-04'
    GROUP BY mc.GESTOR_ID
""")
r = cur.fetchone()
if r:
    g1_ing, g1_gas, g1_ctos, g1_nom, g1_cen = r
    g1_mar = ((g1_ing - g1_gas) / g1_ing * 100) if g1_ing > 0 else 0
    print(f"\nGESTOR 1: {g1_nom} ({g1_cen}): ing={g1_ing:,.2f}, gas={g1_gas:,.2f}, mar={g1_mar:.1f}%, ctos={g1_ctos}")
    gt['gestor_1_kpis'] = {
        'nombre': g1_nom, 'centro': g1_cen, 'ingresos': round(g1_ing,2),
        'gastos_directos': round(g1_gas,2), 'contratos': g1_ctos, 'margen_directo_pct': round(g1_mar,1)
    }

# 6. MoM MAR->ABR
for scope, filtro in [("entidad", "1=1"), ("gestor_1", "mc.GESTOR_ID = 1")]:
    cur = conn.execute(f"""
        SELECT
            SUM(CASE WHEN CUENTA_ID LIKE '76%' AND strftime('%Y-%m', FECHA) = '2026-03' THEN IMPORTE ELSE 0 END),
            SUM(CASE WHEN CUENTA_ID LIKE '76%' AND strftime('%Y-%m', FECHA) = '2026-04' THEN IMPORTE ELSE 0 END)
        FROM MOVIMIENTOS_CONTRATOS mov LEFT JOIN MAESTRO_CONTRATOS mc ON mov.CONTRATO_ID = mc.CONTRATO_ID
        WHERE ({filtro}) AND strftime('%Y-%m', FECHA) IN ('2026-03','2026-04')
    """)
    mar_v, abr_v = cur.fetchone()
    var = ((abr_v - mar_v) / mar_v * 100) if mar_v and mar_v > 0 else 0
    print(f"MoM {scope}: mar={mar_v:,.0f}, abr={abr_v:,.0f}, var={var:+.2f}%")
    gt[f'mom_{scope}'] = {'marzo': round(mar_v,2), 'abril': round(abr_v,2), 'variacion_pct': round(var,2)}

# 7. SERIE HISTORICA
cur = conn.execute("""
    SELECT strftime('%Y-%m', FECHA), SUM(CASE WHEN CUENTA_ID LIKE '76%' THEN IMPORTE ELSE 0 END)
    FROM MOVIMIENTOS_CONTRATOS GROUP BY 1 ORDER BY 1
""")
serie = [{'periodo': row[0], 'ingresos': round(row[1],2)} for row in cur.fetchall()]
gt['serie_historica'] = serie
print(f"\nSerie: {len(serie)} periodos ({serie[0]['periodo']} a {serie[-1]['periodo']})")

conn.close()
os.makedirs('evals/datasets', exist_ok=True)
with open('evals/datasets/ground_truth.json', 'w', encoding='utf-8') as f:
    json.dump(gt, f, indent=2, ensure_ascii=False)
print(f"\nTOTAL: {len(gt)} categorias")
print("evals/datasets/ground_truth.json guardado OK")
