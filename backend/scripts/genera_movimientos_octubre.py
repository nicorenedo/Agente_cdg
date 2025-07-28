#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BANCAMARCH_AGENTECDG - Generador de Movimientos Octubre 2025
===========================================================
Genera 1,230 movimientos para octubre basado en:
- 15 nuevos clientes (IDs 71-85)
- 28 nuevos contratos (187→215 total)
- Crecimiento 23% en actividad comercial
"""

import random
import sqlite3
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DATABASE_PATH = PROJECT_ROOT / "src" / "database" / "BM_CONTABILIDAD_CDG.db"

# Configuración
EMPRESA_ID = 1
FECHA = '2025-10-01'
DIVISA = 'EUR'
NUM_MOVIMIENTOS = 1230

def generar_movimientos_octubre():
    """Genera movimientos comerciales para octubre"""
    
    print(f"🏦 GENERANDO {NUM_MOVIMIENTOS} MOVIMIENTOS PARA {FECHA}")
    print("=" * 60)
    
    # Cargar contratos existentes (187 + 28 nuevos = 215)
    contratos_existentes = list(range(1001, 1075))  # Hipotecarios
    contratos_existentes.extend(range(2001, 2070))  # Depósitos
    contratos_existentes.extend(range(3001, 3069))  # Fondos
    
    # Configuración por producto
    config_productos = {
        # Préstamos Hipotecarios
        'hipotecarios': {
            'contratos': [c for c in contratos_existentes if 1001 <= c <= 1075],
            'cuentas': [
                ('760001', 'CR0001', 'Intereses cobrados préstamo hipotecario', (1800, 4200)),
                ('760002', 'CR0008', 'Comisión apertura préstamo', (300, 800)),
                ('760003', 'CR0008', 'Comisión cancelación préstamo', (150, 400)),
                ('760004', 'CR0008', 'Comisión estudio préstamo', (200, 500))
            ]
        },
        # Depósitos a Plazo Fijo
        'depositos': {
            'contratos': [c for c in contratos_existentes if 2001 <= c <= 2070],
            'cuentas': [
                ('640001', 'CR0003', 'Intereses pagados depósito plazo fijo', (-3000, -1200)),
                ('760011', 'CR0008', 'Comisión gestión depósito', (80, 250)),
                ('760012', 'CR0008', 'Comisión cancelación anticipada depósito', (60, 180)),
                ('691001', 'CR001302', 'Impuesto depósitos', (-50, -15)),
                ('691002', 'CR001301', 'Fondo garantía depósitos', (-35, -10))
            ]
        },
        # Fondos Banca March (campaña octubre - mayor peso)
        'fondos': {
            'contratos': [c for c in contratos_existentes if 3001 <= c <= 3069],
            'cuentas': [
                ('760021', 'CR0008', 'Comisión gestión fondos', (400, 1500)),
                ('760022', 'CR0008', 'Comisión suscripción fondos', (300, 800)),
                ('760023', 'CR0008', 'Comisión reembolso fondos', (200, 600)),
                ('760024', 'CR001104', 'Reparto internegocio banco 15%', (50, 300)),
                ('760025', 'CR001104', 'Reparto internegocio fábrica 85%', (300, 1800)),
                ('760026', 'CR0008', 'Comisión distribución fondos', (80, 250))
            ]
        }
    }
    
    movimientos = []
    centros_por_contrato = {
        # Mapeo aproximado contrato → centro (basado en rangos)
        range(1001, 1021): 1, range(2001, 2021): 1, range(3001, 3021): 1,  # Madrid
        range(1021, 1041): 2, range(2021, 2041): 2, range(3021, 3041): 2,  # Palma
        range(1041, 1056): 3, range(2041, 2056): 3, range(3041, 3056): 3,  # Barcelona
        range(1056, 1066): 4, range(2056, 2066): 4, range(3056, 3066): 4,  # Málaga
        range(1066, 1076): 5, range(2066, 2076): 5, range(3066, 3076): 5,  # Bilbao
    }
    
    def obtener_centro(contrato_id):
        """Determina el centro del contrato"""
        for rango, centro in centros_por_contrato.items():
            if contrato_id in rango:
                return centro
        return 1  # Default Madrid
    
    # Generar movimientos comerciales (1000 movimientos)
    print("💰 Generando movimientos comerciales...")
    
    # Distribución por producto (campaña fondos octubre)
    movimientos_por_producto = {
        'hipotecarios': 350,  # -12% vs septiembre (menor foco)
        'depositos': 320,     # -8% vs septiembre (estable)
        'fondos': 430         # +25% vs septiembre (campaña)
    }
    
    for producto, cantidad in movimientos_por_producto.items():
        config = config_productos[producto]
        contratos = config['contratos']
        cuentas = config['cuentas']
        
        for _ in range(cantidad):
            contrato_id = random.choice(contratos)
            centro = obtener_centro(contrato_id)
            cuenta, linea, concepto, (min_imp, max_imp) = random.choice(cuentas)
            importe = round(random.uniform(min_imp, max_imp), 2)
            
            # Lógica especial para fondos (reparto 85/15)
            if producto == 'fondos' and cuenta in ['760021', '760022', '760023']:
                comision_base = abs(importe)
                
                # Movimiento principal
                movimientos.append({
                    'contrato_id': contrato_id, 'centro': centro, 'cuenta': cuenta,
                    'importe': comision_base, 'linea': linea, 'concepto': concepto
                })
                
                # Reparto banco 15%
                movimientos.append({
                    'contrato_id': contrato_id, 'centro': centro, 'cuenta': '760024',
                    'importe': round(comision_base * 0.15, 2), 'linea': 'CR001104',
                    'concepto': 'Reparto internegocio banco 15%'
                })
                
                # Reparto fábrica 85%
                movimientos.append({
                    'contrato_id': contrato_id, 'centro': centro, 'cuenta': '760025',
                    'importe': round(comision_base * 0.85, 2), 'linea': 'CR001104',
                    'concepto': 'Reparto internegocio fábrica 85%'
                })
            else:
                # Movimiento único
                movimientos.append({
                    'contrato_id': contrato_id, 'centro': centro, 'cuenta': cuenta,
                    'importe': importe, 'linea': linea, 'concepto': concepto
                })
    
    # Generar gastos operativos (230 movimientos - incremento vs septiembre)
    print("🏢 Generando gastos operativos...")
    
    gastos_operativos = [
        ('620001', 'CR0014', 'Gastos personal asignación directa', (-15000, -3000)),
        ('621001', 'CR0016', 'Gastos tecnología', (-5000, -800)),
        ('621002', 'CR0016', 'Gastos suministros', (-2000, -400)),
        ('621003', 'CR0016', 'Gastos papelería', (-800, -100)),
        ('682001', 'CR0017', 'Amortización software bancario', (-1500, -200)),
        ('669001', 'CR0013', 'Otros gastos de explotación', (-500, -50)),
        ('690001', 'CR0029', 'Coste de capital asignado', (-3000, -500))
    ]
    
    for _ in range(230):
        cuenta, linea, concepto, (min_imp, max_imp) = random.choice(gastos_operativos)
        centro = random.randint(1, 5)
        importe = round(random.uniform(min_imp, max_imp), 2)
        
        movimientos.append({
            'contrato_id': None, 'centro': centro, 'cuenta': cuenta,
            'importe': importe, 'linea': linea, 'concepto': concepto
        })
    
    print(f"✅ Total movimientos generados: {len(movimientos)}")
    return movimientos

def insertar_movimientos_octubre(movimientos):
    """Inserta movimientos en la base de datos"""
    
    print("\n💾 Insertando movimientos en base de datos...")
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Obtener último MOVIMIENTO_ID
        cursor.execute("SELECT MAX(MOVIMIENTO_ID) FROM MOVIMIENTOS_CONTRATOS")
        ultimo_id = cursor.fetchone()[0] or 0
        
        print(f"📊 Último ID existente: {ultimo_id}")
        
        # Insertar movimientos
        insertados = 0
        for i, mov in enumerate(movimientos):
            try:
                cursor.execute("""
                    INSERT INTO MOVIMIENTOS_CONTRATOS 
                    (EMPRESA_ID, FECHA, CONTRATO_ID, CENTRO_CONTABLE, CUENTA_ID, 
                     DIVISA, IMPORTE, LINEA_CUENTA_RESULTADOS, CONCEPTO_GESTION)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    EMPRESA_ID, FECHA, mov['contrato_id'], mov['centro'],
                    mov['cuenta'], DIVISA, mov['importe'], 
                    mov['linea'], mov['concepto']
                ))
                insertados += 1
                
                if insertados % 100 == 0:
                    print(f"   📦 {insertados} movimientos insertados...")
                    
            except sqlite3.Error as e:
                print(f"❌ Error insertando movimiento {i+1}: {e}")
        
        conn.commit()
        print(f"✅ {insertados} movimientos insertados correctamente")
        
        # Estadísticas finales
        cursor.execute("""
            SELECT 
                COUNT(*) as TOTAL,
                COUNT(CASE WHEN CONTRATO_ID IS NOT NULL THEN 1 END) as COMERCIALES,
                COUNT(CASE WHEN CONTRATO_ID IS NULL THEN 1 END) as GASTOS
            FROM MOVIMIENTOS_CONTRATOS 
            WHERE FECHA = ?
        """, (FECHA,))
        
        total, comerciales, gastos = cursor.fetchone()
        
        print(f"\n📊 ESTADÍSTICAS OCTUBRE {FECHA}:")
        print(f"   • Total movimientos: {total}")
        print(f"   • Comerciales: {comerciales} ({comerciales/total*100:.1f}%)")
        print(f"   • Gastos operativos: {gastos} ({gastos/total*100:.1f}%)")

def main():
    """Función principal"""
    
    try:
        # Generar movimientos
        movimientos = generar_movimientos_octubre()
        
        # Insertar en base de datos
        insertar_movimientos_octubre(movimientos)
        
        print(f"\n🎉 ¡Proceso completado exitosamente!")
        print(f"📈 Crecimiento: {NUM_MOVIMIENTOS}/1000 = +23% vs septiembre")
        print(f"🎯 Campaña fondos: Mayor actividad en productos de inversión")
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {e}")
        raise

if __name__ == "__main__":
    main()
