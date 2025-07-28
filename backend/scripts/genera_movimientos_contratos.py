#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BANCAMARCH_AGENTECDG - Generador de Movimientos Contratos
=======================================================
Genera 1,000 movimientos para MOVIMIENTOS_CONTRATOS basado en MAESTRO_CONTRATOS
Ubicación: backend/scripts/genera_movimientos_contratos.py
Base de datos: backend/src/database/BM_CONTABILIDAD_CDG.db
"""

import sqlite3
import random
import os
from datetime import datetime
from pathlib import Path

# Configuración del proyecto
PROJECT_ROOT = Path(__file__).parent.parent  # BANCAMARCH_AGENTECDG/backend/
DATABASE_PATH = PROJECT_ROOT / "src" / "database" / "BM_CONTABILIDAD_CDG.db"
LOGS_DIR = PROJECT_ROOT / "logs"

# Configuración global
EMPRESA_ID = 1
FECHA = '2025-09-01'
DIVISA = 'EUR'
NUM_MOVIMIENTOS = 1000

class GeneradorMovimientos:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.movimientos_generados = []
        
        # Verificar que existe la base de datos
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")
        
        print(f"🏦 AGENTE CDG - Generador de Movimientos Contratos")
        print(f"📍 Base de datos: {self.db_path}")
        print(f"📅 Fecha movimientos: {FECHA}")
    
    def conectar_db(self):
        """Establece conexión con la base de datos"""
        return sqlite3.connect(self.db_path)
    
    def verificar_estructura(self):
        """Verifica que existan las tablas necesarias"""
        with self.conectar_db() as conn:
            cursor = conn.cursor()
            
            # Verificar tablas requeridas
            tablas_requeridas = [
                'MAESTRO_CONTRATOS', 'MAESTRO_CENTROS', 
                'MAESTRO_CUENTAS', 'MAESTRO_LINEA_CDR'
            ]
            
            for tabla in tablas_requeridas:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
                    (tabla,)
                )
                if not cursor.fetchone():
                    raise Exception(f"❌ Tabla {tabla} no encontrada en la base de datos")
            
            print("✅ Estructura de base de datos verificada")
    
    def cargar_contratos_existentes(self):
        """Carga contratos desde MAESTRO_CONTRATOS"""
        with self.conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT CONTRATO_ID, PRODUCTO_ID, CENTRO_CONTABLE 
                FROM MAESTRO_CONTRATOS
            """)
            contratos = cursor.fetchall()
            
            print(f"📋 Contratos cargados: {len(contratos)}")
            return contratos
    
    def configurar_cuentas_productos(self):
        """Configuración de cuentas por producto"""
        return {
            '100100100100': {  # Préstamos Hipotecarios
                'cuentas': ['760001', '760002', '760003', '760004'],
                'lineas': {
                    '760001': 'CR0001',  # Intereses cobrados
                    '760002': 'CR0008',  # Comisión apertura
                    '760003': 'CR0008',  # Comisión cancelación
                    '760004': 'CR0008'   # Comisión estudio
                },
                'conceptos': {
                    '760001': 'Intereses cobrados préstamo hipotecario',
                    '760002': 'Comisión apertura préstamo',
                    '760003': 'Comisión cancelación préstamo',
                    '760004': 'Comisión estudio préstamo'
                },
                'rangos_importe': {
                    '760001': (1800, 4200),
                    '760002': (300, 800),
                    '760003': (150, 400),
                    '760004': (200, 500)
                }
            },
            '400200100100': {  # Depósitos a Plazo Fijo
                'cuentas': ['640001', '760011', '760012', '691001', '691002'],
                'lineas': {
                    '640001': 'CR0003',
                    '760011': 'CR0008',
                    '760012': 'CR0008',
                    '691001': 'CR001302',
                    '691002': 'CR001301'
                },
                'conceptos': {
                    '640001': 'Intereses pagados depósito plazo fijo',
                    '760011': 'Comisión gestión depósito',
                    '760012': 'Comisión cancelación anticipada depósito',
                    '691001': 'Impuesto depósitos',
                    '691002': 'Fondo garantía depósitos'
                },
                'rangos_importe': {
                    '640001': (-3000, -1200),
                    '760011': (80, 250),
                    '760012': (60, 180),
                    '691001': (-50, -15),
                    '691002': (-35, -10)
                }
            },
            '600100300300': {  # Fondos Banca March
                'cuentas': ['760021', '760022', '760023', '760024', '760025', '760026'],
                'lineas': {
                    '760021': 'CR0008',
                    '760022': 'CR0008',
                    '760023': 'CR0008',
                    '760024': 'CR001104',
                    '760025': 'CR001104',
                    '760026': 'CR0008'
                },
                'conceptos': {
                    '760021': 'Comisión gestión fondos',
                    '760022': 'Comisión suscripción fondos',
                    '760023': 'Comisión reembolso fondos',
                    '760024': 'Reparto internegocio banco 15%',
                    '760025': 'Reparto internegocio fábrica 85%',
                    '760026': 'Comisión distribución fondos'
                },
                'rangos_importe': {
                    '760021': (400, 1500),
                    '760022': (300, 800),
                    '760023': (200, 600),
                    '760024': (50, 300),
                    '760025': (300, 1800),
                    '760026': (80, 250)
                }
            }
        }
    
    def generar_movimiento_comercial(self, contratos, config_productos):
        """Genera movimiento comercial basado en contrato real"""
        # Seleccionar contrato aleatorio
        contrato_id, producto_id, centro = random.choice(contratos)
        config = config_productos.get(producto_id)
        
        if not config:
            return []
        
        cuenta = random.choice(config['cuentas'])
        
        # Lógica especial para Fondos (reparto 85/15)
        if producto_id == '600100300300' and cuenta in ['760021', '760022', '760023']:
            comision_base = random.uniform(400, 1500)
            
            return [
                {
                    'contrato_id': contrato_id,
                    'centro': centro,
                    'cuenta': cuenta,
                    'importe': round(comision_base, 2),
                    'linea': config['lineas'][cuenta],
                    'concepto': config['conceptos'][cuenta]
                },
                {
                    'contrato_id': contrato_id,
                    'centro': centro,
                    'cuenta': '760024',
                    'importe': round(comision_base * 0.15, 2),
                    'linea': 'CR001104',
                    'concepto': 'Reparto internegocio banco 15%'
                },
                {
                    'contrato_id': contrato_id,
                    'centro': centro,
                    'cuenta': '760025',
                    'importe': round(comision_base * 0.85, 2),
                    'linea': 'CR001104',
                    'concepto': 'Reparto internegocio fábrica 85%'
                }
            ]
        else:
            # Movimiento único
            rango_min, rango_max = config['rangos_importe'][cuenta]
            importe = round(random.uniform(rango_min, rango_max), 2)
            
            return [{
                'contrato_id': contrato_id,
                'centro': centro,
                'cuenta': cuenta,
                'importe': importe,
                'linea': config['lineas'][cuenta],
                'concepto': config['conceptos'][cuenta]
            }]
    
    def generar_movimiento_gastos(self):
        """Genera movimiento de gastos operativos"""
        cuentas_gastos = {
            '620001': ('CR0014', 'Gastos personal asignación directa', (-15000, -3000)),
            '621001': ('CR0016', 'Gastos tecnología', (-5000, -800)),
            '621002': ('CR0016', 'Gastos suministros', (-2000, -400)),
            '621003': ('CR0016', 'Gastos papelería', (-800, -100)),
            '682001': ('CR0017', 'Amortización software bancario', (-1500, -200)),
            '669001': ('CR0013', 'Otros gastos de explotación', (-500, -50)),
            '690001': ('CR0029', 'Coste de capital asignado', (-3000, -500))
        }
        
        cuenta = random.choice(list(cuentas_gastos.keys()))
        linea, concepto, (rango_min, rango_max) = cuentas_gastos[cuenta]
        centro = random.randint(1, 5)  # Centros finalistas
        importe = round(random.uniform(rango_min, rango_max), 2)
        
        return [{
            'contrato_id': None,
            'centro': centro,
            'cuenta': cuenta,
            'importe': importe,
            'linea': linea,
            'concepto': concepto
        }]
    
    def generar_todos_movimientos(self):
        """Genera los 1,000 movimientos"""
        print("🔄 Generando movimientos...")
        
        # Cargar datos base
        contratos = self.cargar_contratos_existentes()
        config_productos = self.configurar_cuentas_productos()
        
        movimientos = []
        
        # 800 movimientos comerciales (80%)
        movimientos_comerciales = 0
        while movimientos_comerciales < 800:
            movs = self.generar_movimiento_comercial(contratos, config_productos)
            movimientos.extend(movs)
            movimientos_comerciales += len(movs)
        
        # 200 movimientos de gastos (20%)
        for _ in range(200):
            movs = self.generar_movimiento_gastos()
            movimientos.extend(movs)
        
        # Truncar a exactamente 1,000
        self.movimientos_generados = movimientos[:NUM_MOVIMIENTOS]
        
        print(f"✅ Generados {len(self.movimientos_generados)} movimientos")
        return self.movimientos_generados
    
    def insertar_en_db(self):
        """Inserta los movimientos en la base de datos"""
        print("💾 Insertando movimientos en base de datos...")
        
        with self.conectar_db() as conn:
            cursor = conn.cursor()
            
            # Limpiar tabla si existe
            try:
                cursor.execute("DELETE FROM MOVIMIENTOS_CONTRATOS")
                print("🗑️ Tabla MOVIMIENTOS_CONTRATOS limpiada")
            except sqlite3.Error as e:
                print(f"⚠️ Error al limpiar tabla: {e}")
            
            # Insertar movimientos
            for mov in self.movimientos_generados:
                cursor.execute("""
                    INSERT INTO MOVIMIENTOS_CONTRATOS 
                    (EMPRESA_ID, FECHA, CONTRATO_ID, CENTRO_CONTABLE, CUENTA_ID, 
                     DIVISA, IMPORTE, LINEA_CUENTA_RESULTADOS, CONCEPTO_GESTION)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    EMPRESA_ID,
                    FECHA,
                    mov['contrato_id'],
                    mov['centro'],
                    mov['cuenta'],
                    DIVISA,
                    mov['importe'],
                    mov['linea'],
                    mov['concepto']
                ))
            
            conn.commit()
            print(f"✅ {len(self.movimientos_generados)} movimientos insertados correctamente")
    
    def generar_estadisticas(self):
        """Genera estadísticas de los movimientos creados"""
        if not self.movimientos_generados:
            return
        
        comerciales = len([m for m in self.movimientos_generados if m['contrato_id']])
        gastos = len([m for m in self.movimientos_generados if not m['contrato_id']])
        contratos_unicos = len(set(m['contrato_id'] for m in self.movimientos_generados if m['contrato_id']))
        
        print("\n📊 ESTADÍSTICAS GENERADAS:")
        print(f"   • Total movimientos: {len(self.movimientos_generados)}")
        print(f"   • Comerciales: {comerciales} ({comerciales/len(self.movimientos_generados)*100:.1f}%)")
        print(f"   • Gastos operativos: {gastos} ({gastos/len(self.movimientos_generados)*100:.1f}%)")
        print(f"   • Contratos únicos: {contratos_unicos}")
        
        # Crear log
        self.crear_log_ejecucion(comerciales, gastos, contratos_unicos)
    
    def crear_log_ejecucion(self, comerciales, gastos, contratos_unicos):
        """Crea log de la ejecución"""
        LOGS_DIR.mkdir(exist_ok=True)
        log_file = LOGS_DIR / f"generacion_movimientos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        with open(log_file, 'w') as f:
            f.write(f"AGENTE CDG - Generación Movimientos Contratos\n")
            f.write(f"============================================\n")
            f.write(f"Fecha ejecución: {datetime.now()}\n")
            f.write(f"Base de datos: {self.db_path}\n")
            f.write(f"Fecha movimientos: {FECHA}\n\n")
            f.write(f"RESULTADOS:\n")
            f.write(f"- Total movimientos: {len(self.movimientos_generados)}\n")
            f.write(f"- Comerciales: {comerciales}\n")
            f.write(f"- Gastos: {gastos}\n")
            f.write(f"- Contratos únicos: {contratos_unicos}\n")
        
        print(f"📝 Log creado: {log_file}")
    
    def ejecutar(self):
        """Ejecuta el proceso completo"""
        try:
            self.verificar_estructura()
            self.generar_todos_movimientos()
            self.insertar_en_db()
            self.generar_estadisticas()
            print("\n🎉 ¡Proceso completado exitosamente!")
            
        except Exception as e:
            print(f"\n❌ Error durante la ejecución: {e}")
            raise

def main():
    """Función principal"""
    generador = GeneradorMovimientos()
    generador.ejecutar()

if __name__ == "__main__":
    main()
