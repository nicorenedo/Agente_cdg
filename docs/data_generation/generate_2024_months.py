"""
S63 — Generate financial data for sep-2024 to aug-2025.
Adds MOVIMIENTOS_CONTRATOS, GASTOS_CENTRO, and PRECIO_POR_PRODUCTO_REAL
for the 12 months before the existing data (which starts at sep-2025).

Run from backend/: python scripts/generate_2024_months.py
IMPORTANT: Backup the DB before running!
"""

import sqlite3
import random
import os
import calendar

random.seed(99)  # Reproducible, different seed from S60

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'BM_CONTABILIDAD_CDG.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

PROD_HIP = '100100100100'
PROD_DEP = '400200100100'
PROD_FRV = '600100300300'

# Calibrated avg ingresos per contract (from oct-2025 real data)
AVG_ING = {PROD_HIP: 4216, PROD_DEP: 541, PROD_FRV: 4382}

# Central expenses baselines (from oct-2025, scale by cartera size)
GASTOS_CENTRALES_BASE = {
    '620001': -29148, '621001': -6506, '621002': -2175, '621003': -1028,
    '660001': -180000, '669001': -574, '682001': -2745, '690001': -4075, '690002': -45000,
}
GASTOS_CENTRO_CONCEPTOS = ['PERSONAL', 'TECNOLOGIA', 'INMUEBLES', 'SUMINISTROS', 'OTROS']
CENTROS = [1, 2, 3, 4, 5, 6, 7, 8]
OCT_2025_CONTRATOS = 230  # Reference cartera for scaling

# Configuration approved in S62
MONTHS_2024 = [
    {'periodo': '2024-09', 'ingresos_target':  39_894},
    {'periodo': '2024-10', 'ingresos_target':  88_565},
    {'periodo': '2024-11', 'ingresos_target': 127_129},
    {'periodo': '2024-12', 'ingresos_target': 141_356},
    {'periodo': '2025-01', 'ingresos_target': 203_897},
    {'periodo': '2025-02', 'ingresos_target': 268_747},
    {'periodo': '2025-03', 'ingresos_target': 343_238},
    {'periodo': '2025-04', 'ingresos_target': 389_651},
    {'periodo': '2025-05', 'ingresos_target': 431_341},
    {'periodo': '2025-06', 'ingresos_target': 463_818},
    {'periodo': '2025-07', 'ingresos_target': 455_084},
    {'periodo': '2025-08', 'ingresos_target': 453_887},
]

# Global counter
_max_mov_id = conn.execute('SELECT MAX(MOVIMIENTO_ID) FROM MOVIMIENTOS_CONTRATOS').fetchone()[0] or 0

def next_mov_id():
    global _max_mov_id
    _max_mov_id += 1
    return _max_mov_id

def rand_day(year, month, lo=3, hi=27):
    d = random.randint(lo, min(hi, calendar.monthrange(year, month)[1]))
    return f'{year}-{month:02d}-{d:02d}'


def generate_month(config):
    periodo = config['periodo']
    year, month = int(periodo[:4]), int(periodo[5:7])
    target_ingresos = config['ingresos_target']

    # Active contracts for this month
    ultimo_dia = f'{year}-{month:02d}-{calendar.monthrange(year, month)[1]}'
    active = [dict(r) for r in conn.execute(
        'SELECT CONTRATO_ID, PRODUCTO_ID, CENTRO_CONTABLE, GESTOR_ID FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= ?',
        (ultimo_dia,)).fetchall()]

    if not active:
        print(f'  {periodo}: 0 active contracts, skipping')
        return

    # Scale factor
    count_by_prod = {}
    for c in active:
        count_by_prod[c['PRODUCTO_ID']] = count_by_prod.get(c['PRODUCTO_ID'], 0) + 1
    expected_raw = sum(AVG_ING.get(p, 3000) * n for p, n in count_by_prod.items())
    scale = target_ingresos / expected_raw if expected_raw > 0 else 1.0

    total_ing = 0.0
    mov_count = 0

    for contract in active:
        cid = contract['CONTRATO_ID']
        pid = contract['PRODUCTO_ID']
        centro = contract['CENTRO_CONTABLE']
        gvar = random.uniform(0.85, 1.15)
        fecha = rand_day(year, month)
        ct = AVG_ING.get(pid, 3000) * scale * gvar

        if pid == PROD_HIP:
            for acc, pct in [('760001', 0.60), ('760002', 0.15), ('760003', 0.10), ('760004', 0.15)]:
                imp = round(ct * pct * random.uniform(0.85, 1.15), 2)
                if imp > 5:
                    conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                                 (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0001', 'CDG'))
                    total_ing += imp; mov_count += 1
            imp_g = round(-452 * scale * gvar * random.uniform(0.8, 1.2), 2)
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                         (next_mov_id(), fecha, cid, centro, '620001', 'EUR', imp_g, 'CR0014', 'CDG'))
            mov_count += 1

        elif pid == PROD_DEP:
            for acc, pct in [('760011', 0.55), ('760012', 0.45)]:
                imp = round(ct * pct * random.uniform(0.80, 1.20), 2)
                if imp > 5:
                    conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                                 (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0001', 'CDG'))
                    total_ing += imp; mov_count += 1
            for acc, base in [('640001', -2123), ('691001', -32), ('691002', -22)]:
                imp = round(base * scale * gvar * random.uniform(0.9, 1.1), 2)
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                             (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0003', 'CDG'))
                mov_count += 1

        else:  # FRV
            com_part = ct * 0.20
            int_part = ct * 0.80
            for acc, pct in [('760021', 0.30), ('760022', 0.30), ('760023', 0.25), ('760026', 0.15)]:
                imp = round(com_part * pct * random.uniform(0.85, 1.15), 2)
                if imp > 5:
                    conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                                 (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0001', 'CDG'))
                    total_ing += imp; mov_count += 1
            imp_fab = round(int_part * 0.85 * random.uniform(0.95, 1.05), 2)
            imp_ban = round(int_part * 0.15 * random.uniform(0.95, 1.05), 2)
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                         (next_mov_id(), fecha, cid, centro, '760025', 'EUR', imp_fab, 'CR001104', 'CDG'))
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                         (next_mov_id(), fecha, cid, centro, '760024', 'EUR', imp_ban, 'CR001104', 'CDG'))
            total_ing += imp_fab + imp_ban; mov_count += 2
            if random.random() < 0.3:
                imp_g = round(-452 * scale * gvar * random.uniform(0.5, 1.0), 2)
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                             (next_mov_id(), fecha, cid, centro, '620001', 'EUR', imp_g, 'CR0014', 'CDG'))
                mov_count += 1

    # Central expenses (CONTRATO_ID = NULL)
    cartera_ratio = len(active) / OCT_2025_CONTRATOS
    fecha_c = f'{year}-{month:02d}-01'
    for acc, base in GASTOS_CENTRALES_BASE.items():
        if acc in ('660001', '690002'):
            imp = round(base * cartera_ratio * random.uniform(0.97, 1.03), 2)
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,NULL,?,?,?,?,?,?)',
                         (next_mov_id(), fecha_c, random.choice([6, 7, 8]), acc, 'EUR', imp, 'CR0016', 'CDG'))
            mov_count += 1
        else:
            share = random.sample(CENTROS, k=random.randint(3, 6))
            per_c = base * cartera_ratio / len(share)
            for c in share:
                imp = round(per_c * random.uniform(0.85, 1.15), 2)
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,NULL,?,?,?,?,?,?)',
                             (next_mov_id(), fecha_c, c, acc, 'EUR', imp, 'CR0016', 'CDG'))
                mov_count += 1

    # GASTOS_CENTRO
    gc_base = 222718 * cartera_ratio / (len(CENTROS) * len(GASTOS_CENTRO_CONCEPTOS))
    for centro in CENTROS:
        for concepto in GASTOS_CENTRO_CONCEPTOS:
            imp = round(gc_base * random.uniform(0.90, 1.10), 2)
            try:
                conn.execute('INSERT INTO GASTOS_CENTRO VALUES (1,?,?,?,?)',
                             (centro, concepto, fecha_c, imp))
            except sqlite3.IntegrityError:
                pass

    # PRECIO_POR_PRODUCTO_REAL
    segmentos = ['N10101', 'N10102', 'N10103', 'N10104', 'N20301']
    productos = [PROD_HIP, PROD_DEP, PROD_FRV]
    for seg in segmentos:
        for prod in productos:
            base_row = conn.execute(
                'SELECT * FROM PRECIO_POR_PRODUCTO_REAL WHERE SEGMENTO_ID=? AND PRODUCTO_ID=? AND FECHA_CALCULO=?',
                (seg, prod, '2025-10-01')).fetchone()
            if base_row:
                precio = round(base_row['PRECIO_MANTENIMIENTO_REAL'] * 0.97 * random.uniform(0.98, 1.02), 2)
                n_base = max(1, int(base_row['NUM_CONTRATOS_BASE'] * cartera_ratio) + random.randint(-1, 1))
                gastos = round(base_row['GASTOS_TOTALES_ASIGNADOS'] * cartera_ratio * random.uniform(0.95, 1.05), 2)
                coste = round(gastos / n_base, 2) if n_base > 0 else 0
            else:
                precio = round(-1250 * random.uniform(0.93, 1.02), 2)
                n_base = max(1, random.randint(1, 10))
                gastos = round(n_base * abs(precio) * random.uniform(0.8, 1.2), 2)
                coste = round(gastos / n_base, 2)
            try:
                conn.execute('INSERT INTO PRECIO_POR_PRODUCTO_REAL VALUES (?,?,?,?,?,?,?)',
                             (seg, prod, precio, fecha_c, n_base, gastos, coste))
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    pct = ((total_ing - target_ingresos) / target_ingresos * 100)
    print(f'  {periodo}: {len(active):3d} contracts, {mov_count:5d} movs, '
          f'ingresos={total_ing:>10,.0f} (target {target_ingresos:>10,d}, {pct:+.1f}%)')


def verify():
    print('\n=== TODOS LOS PERIODOS ===')
    rows = conn.execute("""
        SELECT strftime('%Y-%m', FECHA) as mes, COUNT(*) as movs,
               ROUND(SUM(CASE WHEN CUENTA_ID LIKE '76%' THEN IMPORTE ELSE 0 END)) as ing
        FROM MOVIMIENTOS_CONTRATOS GROUP BY mes ORDER BY mes
    """).fetchall()
    for r in rows:
        print(f'  {r[0]}: {r[1]:>5d} movs | ingresos {r[2]:>10,.0f}')

    print('\n=== YoY CONTRATOS NUEVOS ===')
    pairs = [('2024-09','2025-09'), ('2024-10','2025-10'), ('2024-11','2025-11'),
             ('2024-12','2025-12'), ('2025-01','2026-01'), ('2025-02','2026-02'),
             ('2025-03','2026-03'), ('2025-04','2026-04')]
    for p_ant, p_act in pairs:
        n_ant = conn.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE strftime('%Y-%m',FECHA_ALTA)=?", (p_ant,)).fetchone()[0]
        n_act = conn.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE strftime('%Y-%m',FECHA_ALTA)=?", (p_act,)).fetchone()[0]
        pct = ((n_act - n_ant) / n_ant * 100) if n_ant else 0
        print(f'  {p_ant}->{p_act}: {n_ant:>2d}->{n_act:>2d} nuevos ({pct:+.0f}%)')

    print('\n=== YoY INGRESOS TOTALES ===')
    for p_ant, p_act in pairs:
        ia = conn.execute("SELECT COALESCE(SUM(IMPORTE),0) FROM MOVIMIENTOS_CONTRATOS WHERE strftime('%Y-%m',FECHA)=? AND CUENTA_ID LIKE '76%'", (p_ant,)).fetchone()[0]
        ib = conn.execute("SELECT COALESCE(SUM(IMPORTE),0) FROM MOVIMIENTOS_CONTRATOS WHERE strftime('%Y-%m',FECHA)=? AND CUENTA_ID LIKE '76%'", (p_act,)).fetchone()[0]
        pct = ((ib - ia) / ia * 100) if ia else 0
        print(f'  {p_ant}->{p_act}: {ia:>10,.0f} -> {ib:>10,.0f} ({pct:+.0f}%)')

    n_m = conn.execute('SELECT COUNT(*) FROM MOVIMIENTOS_CONTRATOS').fetchone()[0]
    n_gc = conn.execute('SELECT COUNT(*) FROM GASTOS_CENTRO').fetchone()[0]
    n_pr = conn.execute('SELECT COUNT(*) FROM PRECIO_POR_PRODUCTO_REAL').fetchone()[0]
    print(f'\n=== TOTALES: {n_m} movimientos, {n_gc} GASTOS_CENTRO, {n_pr} PRECIO_REAL ===')


if __name__ == '__main__':
    print('='*60)
    print('S63 - GENERATE FINANCIAL DATA SEP-2024 TO AUG-2025')
    print('='*60)

    for cfg in MONTHS_2024:
        generate_month(cfg)

    verify()
    conn.close()
    print('\nDone.')
