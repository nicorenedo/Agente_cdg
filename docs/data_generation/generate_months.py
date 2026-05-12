"""
S60 — Historical data expansion script.
Generates data from sep-2024 to apr-2026.

Run from backend/ directory:
    python scripts/generate_months.py

IMPORTANT: Backup the DB before running!
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

random.seed(42)  # Reproducible

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'database', 'BM_CONTABILIDAD_CDG.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# ============================================================================
# CONSTANTS
# ============================================================================

PROD_HIP = '100100100100'
PROD_DEP = '400200100100'
PROD_FRV = '600100300300'

# Account ranges from S58 audit (avg values for contracts with movements)
# Ingresos
ACC_HIP_INGRESOS = [
    ('760001', 3878, 0.7),   # Intereses cobrados (main)
    ('760002', 669, 0.5),    # Comisiones apertura
    ('760003', 349, 0.4),    # Comisiones cancelación
    ('760004', 468, 0.5),    # Comisiones estudio
]
ACC_DEP_INGRESOS = [
    ('760011', 285, 0.5),    # Comisiones gestión
    ('760012', 213, 0.4),    # Comisiones cancelación anticipada
]
ACC_FRV_INGRESOS = [
    ('760021', 1028, 0.5),   # Comisiones gestión
    ('760022', 1190, 0.5),   # Comisiones suscripción
    ('760023', 1233, 0.4),   # Comisiones reembolso
    ('760026', 279, 0.3),    # Comisiones distribución
]
ACC_FRV_INTERNEG = [
    ('760024', 142, 1.0),    # Internegocio Banco (15%)
    ('760025', 771, 1.0),    # Internegocio Fábrica (85%)
]

# Gastos directos por contrato
ACC_HIP_GASTOS = [('620001', -452, 0.6)]
ACC_DEP_GASTOS = [
    ('640001', -2123, 1.0),  # Intereses pagados (siempre)
    ('691001', -32, 0.8),    # Impuesto depósitos
    ('691002', -22, 0.7),    # Fondo garantía
]
ACC_FRV_GASTOS = [('620001', -452, 0.3)]  # Menos frecuente para fondos

# Gastos centrales (CONTRATO_ID = NULL)
GASTOS_CENTRALES_BASE = {
    '620001': -29148,    # Personal central
    '621001': -6506,     # Tecnología
    '621002': -2175,     # Suministros
    '621003': -1028,     # Papelería
    '660001': -180000,   # Fondeo
    '669001': -574,      # Otros explotación
    '682001': -2745,     # Amortización SW
    '690001': -4075,     # Coste capital
    '690002': -45000,    # Provisión
}

# GASTOS_CENTRO conceptos base (from oct-2025)
GASTOS_CENTRO_CONCEPTOS = ['PERSONAL', 'TECNOLOGIA', 'INMUEBLES', 'SUMINISTROS', 'OTROS']

CENTROS = [1, 2, 3, 4, 5, 6, 7, 8]  # 5 finalistas + 3 soporte

# 30 gestores distributed across 5 centres
GESTORES_POR_CENTRO = {
    1: [1, 2, 3, 4, 5, 6, 7, 8],
    2: [9, 10, 11, 12, 13, 14, 15, 16],
    3: [17, 18, 19, 20, 21],
    4: [22, 23, 24, 25, 26],
    5: [27, 28, 29, 30],
}

ALL_GESTORES = list(range(1, 31))

# ============================================================================
# GLOBAL COUNTERS
# ============================================================================

_max_mov_id = conn.execute('SELECT MAX(MOVIMIENTO_ID) FROM MOVIMIENTOS_CONTRATOS').fetchone()[0] or 2800
_max_cliente_id = conn.execute('SELECT MAX(CLIENTE_ID) FROM MAESTRO_CLIENTES').fetchone()[0] or 85


def next_mov_id():
    global _max_mov_id
    _max_mov_id += 1
    return _max_mov_id


def next_cliente_id():
    global _max_cliente_id
    _max_cliente_id += 1
    return _max_cliente_id


def rand_day(year, month, lo=2, hi=28):
    d = random.randint(lo, hi)
    return f'{year}-{month:02d}-{d:02d}'


def gen_importe(base, variance=0.15):
    return round(base * random.uniform(1 - variance, 1 + variance), 2)


# ============================================================================
# BLOQUE 1.1 — Fix 8 orphan contracts
# ============================================================================

def fix_orphan_contracts():
    orphans = [1067, 1074, 1075, 2066, 3069, 3070, 3071, 3072]
    count = 0
    for cid in orphans:
        row = conn.execute('SELECT * FROM MAESTRO_CONTRATOS WHERE CONTRATO_ID=?', (cid,)).fetchone()
        if not row:
            continue
        pid = row['PRODUCTO_ID']
        centro = row['CENTRO_CONTABLE']

        for periodo_m, periodo_y in [(9, 2025), (10, 2025)]:
            fecha = rand_day(periodo_y, periodo_m, 5, 25)

            if pid == PROD_HIP:
                accs_ing, accs_gas = ACC_HIP_INGRESOS, ACC_HIP_GASTOS
            elif pid == PROD_DEP:
                accs_ing, accs_gas = ACC_DEP_INGRESOS, ACC_DEP_GASTOS
            else:
                accs_ing, accs_gas = ACC_FRV_INGRESOS, ACC_FRV_GASTOS

            for acc, base, prob in accs_ing:
                if random.random() < prob:
                    conn.execute(
                        'INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                        (next_mov_id(), fecha, cid, centro, acc, 'EUR',
                         gen_importe(base), 'CR0001', 'CDG'))
                    count += 1

            for acc, base, prob in accs_gas:
                if random.random() < prob:
                    conn.execute(
                        'INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                        (next_mov_id(), fecha, cid, centro, acc, 'EUR',
                         gen_importe(base), 'CR0003' if acc.startswith('64') else 'CR0014', 'CDG'))
                    count += 1

            # FRV internegocio
            if pid == PROD_FRV:
                for acc, base, _ in ACC_FRV_INTERNEG:
                    conn.execute(
                        'INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                        (next_mov_id(), fecha, cid, centro, acc, 'EUR',
                         gen_importe(base), 'CR001104', 'CDG'))
                    count += 1

    conn.commit()
    print(f'B1.1: Fixed {len(orphans)} orphan contracts, {count} movements inserted')


# ============================================================================
# BLOQUE 1.2 — Redistribute FECHA_ALTA to sep-2024 → aug-2025
# ============================================================================

REDISTRIB = [
    ('2024-09', 14, 5, 4, 5),
    ('2024-10', 16, 5, 5, 6),
    ('2024-11', 15, 5, 5, 5),
    ('2024-12', 10, 3, 4, 3),
    ('2025-01', 18, 6, 6, 6),
    ('2025-02', 20, 7, 7, 6),
    ('2025-03', 22, 8, 7, 7),
    ('2025-04', 19, 7, 6, 6),
    ('2025-05', 17, 6, 5, 6),
    ('2025-06', 16, 5, 6, 5),
    ('2025-07', 12, 4, 4, 4),
    ('2025-08', 8, 3, 3, 2),
]


def redistribute_fecha_alta():
    # Get IDs of contracts to redistribute (ene-may 2025 FECHA_ALTA)
    rows = conn.execute("""
        SELECT CONTRATO_ID, PRODUCTO_ID FROM MAESTRO_CONTRATOS
        WHERE strftime('%Y-%m', FECHA_ALTA) BETWEEN '2025-01' AND '2025-05'
        ORDER BY PRODUCTO_ID, CONTRATO_ID
    """).fetchall()

    hip_ids = [r['CONTRATO_ID'] for r in rows if r['PRODUCTO_ID'] == PROD_HIP]
    dep_ids = [r['CONTRATO_ID'] for r in rows if r['PRODUCTO_ID'] == PROD_DEP]
    frv_ids = [r['CONTRATO_ID'] for r in rows if r['PRODUCTO_ID'] == PROD_FRV]

    random.shuffle(hip_ids)
    random.shuffle(dep_ids)
    random.shuffle(frv_ids)

    hi, di, fi = 0, 0, 0
    updated = 0

    for mes_str, total, n_hip, n_dep, n_frv in REDISTRIB:
        year, month = int(mes_str[:4]), int(mes_str[5:7])

        for _ in range(n_hip):
            if hi < len(hip_ids):
                fecha = rand_day(year, month)
                conn.execute('UPDATE MAESTRO_CONTRATOS SET FECHA_ALTA=? WHERE CONTRATO_ID=?',
                             (fecha, hip_ids[hi]))
                hi += 1
                updated += 1

        for _ in range(n_dep):
            if di < len(dep_ids):
                fecha = rand_day(year, month)
                conn.execute('UPDATE MAESTRO_CONTRATOS SET FECHA_ALTA=? WHERE CONTRATO_ID=?',
                             (fecha, dep_ids[di]))
                di += 1
                updated += 1

        for _ in range(n_frv):
            if fi < len(frv_ids):
                fecha = rand_day(year, month)
                conn.execute('UPDATE MAESTRO_CONTRATOS SET FECHA_ALTA=? WHERE CONTRATO_ID=?',
                             (fecha, frv_ids[fi]))
                fi += 1
                updated += 1

    conn.commit()
    print(f'B1.2: Redistributed {updated} contracts (Hip:{hi} Dep:{di} FRV:{fi})')


# ============================================================================
# BLOQUE 1.3 — Add 10 contracts to oct-2025
# ============================================================================

OCT_NEW_CONTRACTS = [
    # (contrato_id, fecha_alta, cliente_id, gestor_id, producto_id, centro, is_new_client)
    (1077, '2025-10-08', 86, 3, PROD_HIP, 1, True),
    (1078, '2025-10-12', 87, 11, PROD_HIP, 2, True),
    (1079, '2025-10-20', 88, 17, PROD_HIP, 3, True),
    (2072, '2025-10-05', 15, 9, PROD_DEP, 2, False),
    (2073, '2025-10-18', 42, 23, PROD_DEP, 4, False),
    (2074, '2025-10-25', 89, 27, PROD_DEP, 5, True),
    (3074, '2025-10-10', 5, 2, PROD_FRV, 1, False),
    (3075, '2025-10-15', 60, 29, PROD_FRV, 5, False),
    (3076, '2025-10-22', 90, 19, PROD_FRV, 3, True),
    (3077, '2025-10-28', 28, 13, PROD_FRV, 2, False),
]

NOMBRES_NUEVOS = {
    86: 'Elena Navarro Ruiz',
    87: 'David Muñoz Blanco',
    88: 'Sergio Díaz Fernández',
    89: 'Laura Romero Sanz',
    90: 'Adrián Molina Torres',
}


def add_oct_contracts():
    count_c, count_cl, count_m = 0, 0, 0

    for cid, fecha, cli, gest, prod, centro, is_new in OCT_NEW_CONTRACTS:
        # New client if needed
        if is_new and cli in NOMBRES_NUEVOS:
            conn.execute('INSERT INTO MAESTRO_CLIENTES VALUES (?,?,?,1)',
                         (cli, NOMBRES_NUEVOS[cli], gest))
            count_cl += 1

        # New contract
        conn.execute('INSERT INTO MAESTRO_CONTRATOS VALUES (?,?,?,?,?,?,1)',
                     (cid, fecha, cli, gest, prod, centro))
        count_c += 1

        # Movements for oct-2025
        if prod == PROD_HIP:
            accs_ing, accs_gas = ACC_HIP_INGRESOS, ACC_HIP_GASTOS
        elif prod == PROD_DEP:
            accs_ing, accs_gas = ACC_DEP_INGRESOS, ACC_DEP_GASTOS
        else:
            accs_ing, accs_gas = ACC_FRV_INGRESOS, ACC_FRV_GASTOS

        mov_fecha = rand_day(2025, 10, 5, 28)
        for acc, base, prob in accs_ing:
            if random.random() < prob:
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                             (next_mov_id(), mov_fecha, cid, centro, acc, 'EUR',
                              gen_importe(base), 'CR0001', 'CDG'))
                count_m += 1

        for acc, base, prob in accs_gas:
            if random.random() < prob:
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                             (next_mov_id(), mov_fecha, cid, centro, acc, 'EUR',
                              gen_importe(base), 'CR0003' if acc.startswith('64') else 'CR0014', 'CDG'))
                count_m += 1

        if prod == PROD_FRV:
            for acc, base, _ in ACC_FRV_INTERNEG:
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                             (next_mov_id(), mov_fecha, cid, centro, acc, 'EUR',
                              gen_importe(base), 'CR001104', 'CDG'))
                count_m += 1

    # Update global counters after oct inserts
    global _max_cliente_id
    _max_cliente_id = conn.execute('SELECT MAX(CLIENTE_ID) FROM MAESTRO_CLIENTES').fetchone()[0]

    conn.commit()
    print(f'B1.3: Added {count_c} contracts, {count_cl} clients, {count_m} movements in oct-2025')


# ============================================================================
# BLOQUE 2 — Generate nov-2025 to apr-2026
# ============================================================================

MONTHS_CONFIG = [
    {'periodo': '2025-11', 'contratos_nuevos': 17, 'mix': {'Hip': 6, 'Dep': 6, 'FRV': 5},
     'ingresos_target': 610_000, 'gastos_central_factor': 1.00},
    {'periodo': '2025-12', 'contratos_nuevos': 11, 'mix': {'Hip': 4, 'Dep': 3, 'FRV': 4},
     'ingresos_target': 580_000, 'gastos_central_factor': 0.97},
    {'periodo': '2026-01', 'contratos_nuevos': 21, 'mix': {'Hip': 7, 'Dep': 7, 'FRV': 7},
     'ingresos_target': 595_000, 'gastos_central_factor': 1.03},
    {'periodo': '2026-02', 'contratos_nuevos': 24, 'mix': {'Hip': 8, 'Dep': 8, 'FRV': 8},
     'ingresos_target': 630_000, 'gastos_central_factor': 1.01},
    {'periodo': '2026-03', 'contratos_nuevos': 26, 'mix': {'Hip': 9, 'Dep': 8, 'FRV': 9},
     'ingresos_target': 648_000, 'gastos_central_factor': 1.01},
    {'periodo': '2026-04', 'contratos_nuevos': 22, 'mix': {'Hip': 7, 'Dep': 7, 'FRV': 8},
     'ingresos_target': 635_000, 'gastos_central_factor': 0.98},
]


def get_active_contracts(periodo_str):
    """Get all contracts active as of end of periodo (YYYY-MM)."""
    year, month = int(periodo_str[:4]), int(periodo_str[5:7])
    # Last day of month
    if month == 12:
        end = f'{year}-12-31'
    else:
        end = f'{year}-{month + 1:02d}-01'
        # Subtract 1 day
        from datetime import date
        d = date(year, month + 1, 1) - timedelta(days=1)
        end = d.isoformat()

    rows = conn.execute(
        'SELECT CONTRATO_ID, PRODUCTO_ID, GESTOR_ID, CENTRO_CONTABLE FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= ?',
        (end,)).fetchall()
    return [dict(r) for r in rows]


def generate_month(config):
    periodo = config['periodo']
    year, month = int(periodo[:4]), int(periodo[5:7])
    target_ingresos = config['ingresos_target']
    gc_factor = config['gastos_central_factor']

    # --- 1. New contracts + clients ---
    mix = config['mix']
    max_hip = conn.execute(f"SELECT MAX(CONTRATO_ID) FROM MAESTRO_CONTRATOS WHERE PRODUCTO_ID='{PROD_HIP}'").fetchone()[0]
    max_dep = conn.execute(f"SELECT MAX(CONTRATO_ID) FROM MAESTRO_CONTRATOS WHERE PRODUCTO_ID='{PROD_DEP}'").fetchone()[0]
    max_frv = conn.execute(f"SELECT MAX(CONTRATO_ID) FROM MAESTRO_CONTRATOS WHERE PRODUCTO_ID='{PROD_FRV}'").fetchone()[0]

    new_contracts = []
    new_client_count = 0

    for prod_label, n in mix.items():
        if prod_label == 'Hip':
            pid, base_id = PROD_HIP, max_hip
        elif prod_label == 'Dep':
            pid, base_id = PROD_DEP, max_dep
        else:
            pid, base_id = PROD_FRV, max_frv

        for i in range(n):
            cid = base_id + i + 1
            gestor = random.choice(ALL_GESTORES)
            centro = None
            for c, gs in GESTORES_POR_CENTRO.items():
                if gestor in gs:
                    centro = c
                    break
            fecha = rand_day(year, month)

            # ~40% new client, 60% existing
            if random.random() < 0.4:
                cli = next_cliente_id()
                conn.execute('INSERT INTO MAESTRO_CLIENTES VALUES (?,?,?,1)',
                             (cli, f'Cliente {cli}', gestor))
                new_client_count += 1
            else:
                # Pick existing client of this gestor
                existing = conn.execute(
                    'SELECT CLIENTE_ID FROM MAESTRO_CONTRATOS WHERE GESTOR_ID=? ORDER BY RANDOM() LIMIT 1',
                    (gestor,)).fetchone()
                cli = existing[0] if existing else next_cliente_id()
                if not existing:
                    conn.execute('INSERT INTO MAESTRO_CLIENTES VALUES (?,?,?,1)',
                                 (cli, f'Cliente {cli}', gestor))
                    new_client_count += 1

            conn.execute('INSERT INTO MAESTRO_CONTRATOS VALUES (?,?,?,?,?,?,1)',
                         (cid, fecha, cli, gestor, pid, centro))
            new_contracts.append({'cid': cid, 'pid': pid, 'gestor': gestor, 'centro': centro})

        # Update max for next product
        if prod_label == 'Hip':
            max_hip = base_id + n
        elif prod_label == 'Dep':
            max_dep = base_id + n
        else:
            max_frv = base_id + n

    # --- 2. Financial movements for ALL active contracts ---
    active = get_active_contracts(periodo)
    total_ingresos_generated = 0.0
    mov_count = 0

    # Calibrated avg ingresos per contract from oct-2025 real data:
    # Hip: €4,216/contract, Dep: €541/contract (low: captación), FRV: €4,382/contract
    AVG_ING = {PROD_HIP: 4216, PROD_DEP: 541, PROD_FRV: 4382}

    # Calculate how many of each product are active
    count_by_prod = {}
    for c in active:
        count_by_prod[c['PRODUCTO_ID']] = count_by_prod.get(c['PRODUCTO_ID'], 0) + 1

    # Expected raw ingresos from current cartera at oct-2025 rates
    expected_raw = sum(AVG_ING.get(p, 3000) * n for p, n in count_by_prod.items())
    scale = target_ingresos / expected_raw if expected_raw > 0 else 1.0

    for contract in active:
        cid = contract['CONTRATO_ID']
        pid = contract['PRODUCTO_ID']
        centro = contract['CENTRO_CONTABLE']
        gestor_var = random.uniform(0.85, 1.15)
        fecha = rand_day(year, month, 3, 27)

        # Target ingresos for this contract
        contract_ing_target = AVG_ING.get(pid, 3000) * scale * gestor_var

        if pid == PROD_HIP:
            # Split across 3-4 income accounts (760001 dominant)
            splits = [('760001', 0.60), ('760002', 0.15), ('760003', 0.10), ('760004', 0.15)]
            for acc, pct in splits:
                imp = round(contract_ing_target * pct * random.uniform(0.85, 1.15), 2)
                if imp > 5:
                    conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                                 (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0001', 'CDG'))
                    total_ingresos_generated += imp
                    mov_count += 1
            # Gastos: personal
            imp_gas = round(-452 * scale * gestor_var * random.uniform(0.8, 1.2), 2)
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                         (next_mov_id(), fecha, cid, centro, '620001', 'EUR', imp_gas, 'CR0014', 'CDG'))
            mov_count += 1

        elif pid == PROD_DEP:
            # 2 income accounts
            splits = [('760011', 0.55), ('760012', 0.45)]
            for acc, pct in splits:
                imp = round(contract_ing_target * pct * random.uniform(0.80, 1.20), 2)
                if imp > 5:
                    conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                                 (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0001', 'CDG'))
                    total_ingresos_generated += imp
                    mov_count += 1
            # Gastos: intereses pagados (big), impuesto, fondo garantía
            for acc, base in [('640001', -2123), ('691001', -32), ('691002', -22)]:
                imp = round(base * scale * gestor_var * random.uniform(0.9, 1.1), 2)
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                             (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0003', 'CDG'))
                mov_count += 1

        else:  # FRV
            # FRV income split: comisiones (20%) + internegocio (80%)
            # In real data, 760024+760025 ARE part of the total €4,382/contract
            comision_part = contract_ing_target * 0.20  # ~20% comisiones directas
            interneg_part = contract_ing_target * 0.80  # ~80% internegocio

            # Comisiones directas
            for acc, pct in [('760021', 0.30), ('760022', 0.30), ('760023', 0.25), ('760026', 0.15)]:
                imp = round(comision_part * pct * random.uniform(0.85, 1.15), 2)
                if imp > 5:
                    conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                                 (next_mov_id(), fecha, cid, centro, acc, 'EUR', imp, 'CR0001', 'CDG'))
                    total_ingresos_generated += imp
                    mov_count += 1

            # Internegocio 85/15 split (part of total, not additional)
            imp_fab = round(interneg_part * 0.85 * random.uniform(0.95, 1.05), 2)
            imp_ban = round(interneg_part * 0.15 * random.uniform(0.95, 1.05), 2)
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                         (next_mov_id(), fecha, cid, centro, '760025', 'EUR', imp_fab, 'CR001104', 'CDG'))
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                         (next_mov_id(), fecha, cid, centro, '760024', 'EUR', imp_ban, 'CR001104', 'CDG'))
            total_ingresos_generated += imp_fab + imp_ban
            mov_count += 2

            # Small operational expense
            if random.random() < 0.3:
                imp_gas = round(-452 * scale * gestor_var * random.uniform(0.5, 1.0), 2)
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,?,?,?,?,?,?,?)',
                             (next_mov_id(), fecha, cid, centro, '620001', 'EUR', imp_gas, 'CR0014', 'CDG'))
                mov_count += 1

    # --- 3. Central expenses (CONTRATO_ID = NULL, spread across centres) ---
    fecha_central = f'{year}-{month:02d}-01'
    for acc, base in GASTOS_CENTRALES_BASE.items():
        # Big items (fondeo/provisión) go as single entry with random centro
        if acc in ('660001', '690002'):
            imp = round(base * gc_factor * random.uniform(0.97, 1.03), 2)
            conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,NULL,?,?,?,?,?,?)',
                         (next_mov_id(), fecha_central, random.choice([6, 7, 8]), acc, 'EUR', imp,
                          'CR0003' if acc.startswith(('64', '66')) else 'CR0016', 'CDG'))
            mov_count += 1
        else:
            # Distribute across support + some finalist centres
            share_centres = random.sample(CENTROS, k=random.randint(3, 6))
            per_centro = base / len(share_centres)
            for c in share_centres:
                imp = round(per_centro * gc_factor * random.uniform(0.85, 1.15), 2)
                conn.execute('INSERT INTO MOVIMIENTOS_CONTRATOS VALUES (?,1,?,NULL,?,?,?,?,?,?)',
                             (next_mov_id(), fecha_central, c, acc, 'EUR', imp,
                              'CR0016', 'CDG'))
                mov_count += 1

    # --- 4. GASTOS_CENTRO ---
    gc_base_per_centro = 222718 / len(CENTROS)  # oct-2025 total / 8 centros
    for centro in CENTROS:
        for concepto in GASTOS_CENTRO_CONCEPTOS:
            imp = round(gc_base_per_centro / len(GASTOS_CENTRO_CONCEPTOS) * gc_factor
                        * random.uniform(0.90, 1.10), 2)
            try:
                conn.execute('INSERT INTO GASTOS_CENTRO VALUES (1,?,?,?,?)',
                             (centro, concepto, f'{year}-{month:02d}-01', imp))
            except sqlite3.IntegrityError:
                pass  # Skip if already exists

    # --- 5. PRECIO_POR_PRODUCTO_REAL ---
    segmentos = ['N10101', 'N10102', 'N10103', 'N10104', 'N20301']
    productos = [PROD_HIP, PROD_DEP, PROD_FRV]
    fecha_calc = f'{year}-{month:02d}-01'
    for seg in segmentos:
        for prod in productos:
            # Base from oct-2025 or estimate
            base_row = conn.execute(
                'SELECT * FROM PRECIO_POR_PRODUCTO_REAL WHERE SEGMENTO_ID=? AND PRODUCTO_ID=? AND FECHA_CALCULO=?',
                (seg, prod, '2025-10-01')).fetchone()
            if base_row:
                precio = round(base_row['PRECIO_MANTENIMIENTO_REAL'] * random.uniform(0.98, 1.02), 2)
                n_base = base_row['NUM_CONTRATOS_BASE'] + random.randint(-1, 2)
                gastos = round(base_row['GASTOS_TOTALES_ASIGNADOS'] * gc_factor * random.uniform(0.97, 1.03), 2)
                coste = round(gastos / n_base, 2) if n_base > 0 else 0
            else:
                precio = round(-1250 * random.uniform(0.95, 1.05), 2)
                n_base = random.randint(5, 15)
                gastos = round(n_base * abs(precio) * random.uniform(0.8, 1.2), 2)
                coste = round(gastos / n_base, 2)
            try:
                conn.execute('INSERT INTO PRECIO_POR_PRODUCTO_REAL VALUES (?,?,?,?,?,?,?)',
                             (seg, prod, precio, fecha_calc, n_base, gastos, coste))
            except sqlite3.IntegrityError:
                pass

    conn.commit()

    pct_diff = ((total_ingresos_generated - target_ingresos) / target_ingresos * 100)
    print(f'  {periodo}: {len(new_contracts)} contracts, {new_client_count} new clients, '
          f'{mov_count} movements, ingresos=€{total_ingresos_generated:,.0f} '
          f'(target €{target_ingresos:,.0f}, {pct_diff:+.1f}%), '
          f'{len(active)} active contracts')


def insert_precio_std_2026():
    """Update PRECIO_POR_PRODUCTO_STD to 2026 (+2.5% over 2025).
    PK is (SEGMENTO_ID, PRODUCTO_ID) without ANNO, so we UPDATE existing rows."""
    conn.execute('UPDATE PRECIO_POR_PRODUCTO_STD SET ANNO=2026, PRECIO_MANTENIMIENTO=ROUND(PRECIO_MANTENIMIENTO*1.025,2), FECHA_ACTUALIZACION=? WHERE ANNO=2025', ('2026-01-01',))
    count = conn.execute('SELECT changes()').fetchone()[0]
    conn.commit()
    print(f'PRECIO_STD: Updated {count} rows to ANNO=2026 (+2.5%)')


# ============================================================================
# VERIFICATION
# ============================================================================

def verify():
    print('\n' + '=' * 70)
    print('VERIFICATION')
    print('=' * 70)

    print('\n=== PERIODOS CON MOVIMIENTOS ===')
    rows = conn.execute("""
        SELECT strftime('%Y-%m', FECHA) as mes,
               COUNT(*) as movs,
               ROUND(SUM(CASE WHEN CUENTA_ID LIKE '76%' THEN IMPORTE ELSE 0 END)) as ingresos
        FROM MOVIMIENTOS_CONTRATOS
        GROUP BY mes ORDER BY mes
    """).fetchall()
    for r in rows:
        print(f'  {r[0]}: {r[1]:>5d} movs | €{r[2]:>10,.0f} ingresos')

    print('\n=== CONTRATOS POR MES ===')
    rows = conn.execute("""
        SELECT strftime('%Y-%m', FECHA_ALTA) as mes, COUNT(*) as n
        FROM MAESTRO_CONTRATOS GROUP BY mes ORDER BY mes
    """).fetchall()
    acum = 0
    for r in rows:
        acum += r[1]
        print(f'  {r[0]}: {r[1]:>3d} nuevos | acumulado: {acum}')

    print('\n=== CRECIMIENTO INTERANUAL (contratos nuevos) ===')
    pairs = [('2024-11', '2025-11'), ('2024-12', '2025-12'),
             ('2025-01', '2026-01'), ('2025-02', '2026-02'),
             ('2025-03', '2026-03'), ('2025-04', '2026-04')]
    for p_ant, p_act in pairs:
        n_ant = conn.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE strftime('%Y-%m',FECHA_ALTA)=?",
                             (p_ant,)).fetchone()[0]
        n_act = conn.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE strftime('%Y-%m',FECHA_ALTA)=?",
                             (p_act,)).fetchone()[0]
        pct = ((n_act - n_ant) / n_ant * 100) if n_ant else 0
        print(f'  {p_ant}->{p_act}: {n_ant:>2d}->{n_act:>2d} ({pct:+.0f}%)')

    print('\n=== TOTALES FINALES ===')
    n_c = conn.execute('SELECT COUNT(*) FROM MAESTRO_CONTRATOS').fetchone()[0]
    n_cl = conn.execute('SELECT COUNT(*) FROM MAESTRO_CLIENTES').fetchone()[0]
    n_m = conn.execute('SELECT COUNT(*) FROM MOVIMIENTOS_CONTRATOS').fetchone()[0]
    n_gc = conn.execute('SELECT COUNT(*) FROM GASTOS_CENTRO').fetchone()[0]
    n_pr = conn.execute('SELECT COUNT(*) FROM PRECIO_POR_PRODUCTO_REAL').fetchone()[0]
    n_ps = conn.execute('SELECT COUNT(*) FROM PRECIO_POR_PRODUCTO_STD').fetchone()[0]
    print(f'  Contratos: {n_c}')
    print(f'  Clientes: {n_cl}')
    print(f'  Movimientos: {n_m}')
    print(f'  GASTOS_CENTRO: {n_gc}')
    print(f'  PRECIO_REAL: {n_pr}')
    print(f'  PRECIO_STD: {n_ps}')

    # Orphan check
    n_orph = conn.execute("""
        SELECT COUNT(*) FROM MAESTRO_CONTRATOS
        WHERE CONTRATO_ID NOT IN (SELECT DISTINCT CONTRATO_ID FROM MOVIMIENTOS_CONTRATOS WHERE CONTRATO_ID IS NOT NULL)
    """).fetchone()[0]
    print(f'  Contratos sin movimientos: {n_orph} (should be 0 for sep+ contracts)')


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print('=' * 70)
    print('S60 — HISTORICAL DATA EXPANSION')
    print('=' * 70)

    print('\n--- BLOQUE 1: Corrections ---')
    fix_orphan_contracts()
    redistribute_fecha_alta()
    add_oct_contracts()

    # Checkpoint
    n_sep = conn.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= '2025-09-30'").fetchone()[0]
    n_oct = conn.execute("SELECT COUNT(*) FROM MAESTRO_CONTRATOS WHERE FECHA_ALTA <= '2025-10-31'").fetchone()[0]
    print(f'\nCHECKPOINT: sep-2025 active={n_sep} (expect 216), oct-2025 active={n_oct} (expect ~230)')

    print('\n--- BLOQUE 2: Generate nov-2025 to apr-2026 ---')
    for cfg in MONTHS_CONFIG:
        generate_month(cfg)

    insert_precio_std_2026()

    verify()
    conn.close()
    print('\nDone.')
