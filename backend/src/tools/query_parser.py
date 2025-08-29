from typing import Dict, List, Optional, Tuple
import re
from enum import Enum
from difflib import SequenceMatcher

# ✅ CORRECCIÓN CRÍTICA: Usar las funciones que SÍ existen en tu db_connection.py
from database.db_connection import db_manager, execute_query

class QueryIntent(Enum):
    PERFORMANCE_ANALYSIS = "performance_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    RANKING_ANALYSIS = "ranking_analysis"
    CAUSAL_ANALYSIS = "causal_analysis"
    SCENARIO_ANALYSIS = "scenario_analysis"
    TEMPORAL_ANALYSIS = "temporal_analysis"

class QueryParser:
    """
    🚀 VERSIÓN MEJORADA: Extracción múltiple y flexible de entidades
    Parsea consultas complejas detectando múltiples gestores, centros, segmentos, etc.
    """
    
    def __init__(self):
        self._centros_cache = None
        self._segmentos_cache = None  
        self._gestores_cache = None
        
        # Patrones de regex para detectar intenciones
        self.ranking_patterns = [
            r"(?:quién|cual|cuales)\s+(?:es|son|está|están)\s+(?:el|los|la|las)\s+(?:mejor|mejores|peor|peores)",
            r"(?:top|ranking|clasificación|posición)",
            r"(?:primero|segundo|tercero|\d+)\s+(?:mejor|peor)",
            r"(?:líder|líderes)"
        ]
        
        self.causal_patterns = [
            r"(?:por qué|porque|motivo|causa|razón)",
            r"(?:qué explica|qué factores|qué causas)",
            r"(?:debido a|a causa de|origen de)"
        ]
        
        self.comparative_patterns = [
            r"(?:comparar|comparado|versus|vs|frente a)",
            r"(?:mejor que|peor que|superior a|inferior a)",
            r"(?:diferencia entre|contraste|confrontar)",
            r"(?:entre|y)\s+(?:el|la|los|las)?\s*(?:gestor|centro|segmento)"  # 🆕 NUEVO
        ]
        
        self.temporal_patterns = [
            r"(?:evolución|tendencia|histórico|temporal|evolutivo)",
            r"(?:durante|a lo largo|en el tiempo|evoluciona)"
        ]

    def _load_centros(self) -> Dict[str, Tuple[int, str]]:
        """✅ CORRECCIÓN: Usa nombres exactos de tu esquema"""
        if self._centros_cache is not None:
            return self._centros_cache
            
        try:
            rows = execute_query("""
                SELECT CENTRO_ID, DESC_CENTRO 
                FROM MAESTRO_CENTROS 
                WHERE IND_CENTRO_FINALISTA = 1
            """)
            
            centros = {}
            for row in rows:
                centro_id = row['CENTRO_ID']
                desc_centro = row['DESC_CENTRO']
                
                # Crear múltiples formas de buscar cada centro
                nombre_clean = desc_centro.lower()
                centros[nombre_clean] = (centro_id, desc_centro)
                
                # Añadir variaciones sin guiones, espacios, etc.
                nombre_simple = re.sub(r'[-\s]+', '', nombre_clean)
                if nombre_simple != nombre_clean:
                    centros[nombre_simple] = (centro_id, desc_centro)
                
                # Añadir solo la primera palabra (ej: "barcelona")
                primera_palabra = nombre_clean.split('-')[0].split()[0]
                if len(primera_palabra) > 3:  # Evitar palabras muy cortas
                    centros[primera_palabra] = (centro_id, desc_centro)
            
            self._centros_cache = centros
            return centros
                
        except Exception as e:
            print(f"⚠️ Error cargando centros: {e}")
            return {}

    def _load_segmentos(self) -> Dict[str, Tuple[str, str]]:
        """✅ CORRECCIÓN: Usa nombres exactos de tu esquema"""
        if self._segmentos_cache is not None:
            return self._segmentos_cache
            
        try:
            rows = execute_query("""
                SELECT SEGMENTO_ID, DESC_SEGMENTO 
                FROM MAESTRO_SEGMENTOS
            """)
            
            segmentos = {}
            for row in rows:
                segmento_id = row['SEGMENTO_ID']
                desc_segmento = row['DESC_SEGMENTO']
                
                # Crear múltiples formas de buscar cada segmento
                nombre_clean = desc_segmento.lower()
                segmentos[nombre_clean] = (segmento_id, desc_segmento)
                
                # Variaciones comunes
                nombre_sin_banca = nombre_clean.replace('banca ', '').replace('banca', '')
                if nombre_sin_banca and nombre_sin_banca != nombre_clean:
                    segmentos[nombre_sin_banca.strip()] = (segmento_id, desc_segmento)
                
                # Palabras clave individuales
                palabras = nombre_clean.split()
                for palabra in palabras:
                    if len(palabra) > 4 and palabra not in ['banca']:
                        segmentos[palabra] = (segmento_id, desc_segmento)
            
            self._segmentos_cache = segmentos
            return segmentos
                
        except Exception as e:
            print(f"⚠️ Error cargando segmentos: {e}")
            return {}

    def _load_gestores(self) -> Dict[str, Tuple[int, str, int, str]]:
        """✅ CORRECCIÓN CRÍTICA: Usa nombres exactos de tu esquema"""
        if self._gestores_cache is not None:
            return self._gestores_cache
            
        try:
            rows = execute_query("""
                SELECT GESTOR_ID, DESC_GESTOR, CENTRO, SEGMENTO_ID
                FROM MAESTRO_GESTORES
            """)
            
            gestores = {}
            for row in rows:
                gestor_id = row['GESTOR_ID']
                desc_gestor = row['DESC_GESTOR'] 
                centro = row['CENTRO']
                segmento_id = row['SEGMENTO_ID']
                
                nombre_clean = desc_gestor.lower()
                gestores[nombre_clean] = (gestor_id, desc_gestor, centro, segmento_id)
                
                # Solo nombre (primera palabra)
                nombre_parts = nombre_clean.split()
                if len(nombre_parts) > 1:
                    primer_nombre = nombre_parts[0]
                    # Evitar duplicados usando un ID único como clave secundaria
                    gestores[f"{primer_nombre}_{gestor_id}"] = (gestor_id, desc_gestor, centro, segmento_id)
                
                # Solo apellido (última palabra)
                if len(nombre_parts) > 1:
                    apellido = nombre_parts[-1]
                    gestores[f"{apellido}_{gestor_id}"] = (gestor_id, desc_gestor, centro, segmento_id)
            
            self._gestores_cache = gestores
            return gestores
                
        except Exception as e:
            print(f"⚠️ Error cargando gestores: {e}")
            return {}

    def _find_best_match(self, text: str, options_dict: Dict[str, any], 
                        similarity_threshold: float = 0.6) -> Optional[any]:
        """Encuentra la mejor coincidencia usando similaridad de texto"""
        text_lower = text.lower()
        
        # Coincidencia exacta primero
        if text_lower in options_dict:
            return options_dict[text_lower]
        
        # Buscar contenido parcial
        for key, value in options_dict.items():
            if text_lower in key or key in text_lower:
                return value
        
        # Búsqueda por similaridad
        best_match = None
        best_similarity = 0
        
        for key, value in options_dict.items():
            similarity = SequenceMatcher(None, text_lower, key).ratio()
            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = value
        
        return best_match

    def _find_multiple_matches(self, text: str, options_dict: Dict[str, any], 
                             similarity_threshold: float = 0.6) -> List[any]:
        """🆕 NUEVO: Encuentra múltiples coincidencias en el texto"""
        text_lower = text.lower()
        matches = []
        
        # Buscar todas las coincidencias exactas y parciales
        for key, value in options_dict.items():
            if key in text_lower:
                if value not in matches:  # Evitar duplicados
                    matches.append(value)
        
        # Si no encontró coincidencias exactas, buscar por similaridad
        if not matches:
            for key, value in options_dict.items():
                similarity = SequenceMatcher(None, text_lower, key).ratio()
                if similarity >= similarity_threshold:
                    if value not in matches:
                        matches.append(value)
        
        return matches

    def parse_query(self, message: str, gestor_id: Optional[str] = None, 
                   periodo: Optional[str] = None) -> Dict:
        """Parsea una consulta y extrae intención, entidades y filtros"""
        message_lower = message.lower()
        
        # 1. Detectar intención principal
        intent = self._detect_intent(message_lower)
        
        # 2. Extraer entidades del dominio bancario (dinámicamente y múltiples)
        entities = self._extract_entities_dynamic_multiple(message_lower)
        
        # 3. Construir filtros combinando contexto y entidades
        filters = {
            'gestor_id': gestor_id,
            'periodo': periodo,
            **entities
        }
        
        # 4. Generar consulta estructurada
        structured_query = {
            'intent': intent,
            'entities': entities,
            'filters': filters,
            'complexity': self._assess_complexity(message_lower),
            'requires_ranking': self._requires_ranking(message_lower),
            'requires_comparison': self._requires_comparison(message_lower),
            'original_message': message
        }
        
        return structured_query

    def _extract_entities_dynamic_multiple(self, message: str) -> Dict:
        """🚀 NUEVA FUNCIÓN: Extrae múltiples entidades consultando dinámicamente la base de datos"""
        entities = {}
        
        # 1. 🆕 NUEVO: Buscar múltiples segmentos dinámicamente
        segmentos = self._load_segmentos()
        segmentos_found = self._find_multiple_matches(message, segmentos)
        if segmentos_found:
            if len(segmentos_found) == 1:
                segmento_id, segmento_desc = segmentos_found[0]
                entities['segmento_id'] = segmento_id
                entities['segmento_name'] = segmento_desc
            else:
                # Múltiples segmentos
                entities['segmentos_ids'] = [s[0] for s in segmentos_found]
                entities['segmentos_names'] = [s[1] for s in segmentos_found]
                entities['segmento_id'] = segmentos_found[0][0]  # Primer segmento como principal
                entities['segmento_name'] = segmentos_found[0][1]
        
        # 2. 🆕 NUEVO: Buscar múltiples centros dinámicamente  
        centros = self._load_centros()
        centros_found = self._find_multiple_matches(message, centros)
        if centros_found:
            if len(centros_found) == 1:
                centro_id, centro_desc = centros_found[0]
                entities['centro_id'] = centro_id
                entities['centro_name'] = centro_desc
            else:
                # Múltiples centros
                entities['centros_ids'] = [c[0] for c in centros_found]
                entities['centros_names'] = [c[1] for c in centros_found]
                entities['centro_id'] = centros_found[0][0]  # Primer centro como principal
                entities['centro_name'] = centros_found[0][1]
        
        # 3. 🚀 MEJORADO: Buscar múltiples gestores dinámicamente
        gestores = self._load_gestores()
        gestores_found = self._find_multiple_matches(message, gestores)
        
        # 🆕 NUEVO: Patrones mejorados para múltiples gestores
        gestores_ids_patterns = [
            r'gestores?\s+(\d+)\s+y\s+(\d+)',                    # "gestores 18 y 21"
            r'gestor\s+(\d+).*?(?:y|vs|versus).*?gestor\s+(\d+)', # "gestor 18 vs gestor 21"
            r'(?:entre|compara).*?gestor.*?(\d+).*?gestor.*?(\d+)', # "compara gestor 18 gestor 21"
            r'gestores?\s+(\d+),?\s*(\d+)',                      # "gestores 18, 21"
            r'(?:del|de)\s+gestor\s+(\d+).*?(?:y|con)\s+(?:del\s+)?gestor\s+(\d+)', # "del gestor 18 y gestor 21"
        ]
        
        gestores_ids_extraidos = []
        
        # Buscar patrones de múltiples gestores
        for pattern in gestores_ids_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        gestores_ids_extraidos.extend(match)
                    else:
                        gestores_ids_extraidos.append(match)
                break
        
        # Si no encontró múltiples, buscar individual
        if not gestores_ids_extraidos:
            single_patterns = [
                r'gestor\s+(?:con\s+)?(?:id\s+)?(\d+)',           # "gestor 18", "gestor con id 18"
                r'gestor\s+(?:número\s+|nº\s+|#)?(\d+)',          # "gestor número 18"  
                r'(?:del\s+|de\s+)?gestor\s+(\d+)',               # "del gestor 18"
                r'(?:ROE|rendimiento|análisis).*?(?:del\s+)?gestor\s+(\d+)', # "ROE del gestor 18"
                r'(?:gestor|ID)\s*[:=]?\s*(\d+)',                 # "gestor: 18"
            ]
            
            for pattern in single_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    gestores_ids_extraidos.append(match.group(1))
                    break
        
        # Procesar gestores encontrados
        if gestores_ids_extraidos:
            # Limpiar y convertir a enteros únicos
            gestores_ids_unicos = list(set([int(gid) for gid in gestores_ids_extraidos if gid.isdigit()]))
            
            if len(gestores_ids_unicos) == 1:
                entities['gestor_id_extracted'] = str(gestores_ids_unicos[0])
                print(f"🎯 Gestor ID extraído: {gestores_ids_unicos[0]}")
            elif len(gestores_ids_unicos) > 1:
                entities['gestores_ids'] = [str(gid) for gid in gestores_ids_unicos]
                entities['gestor_id_extracted'] = str(gestores_ids_unicos[0])  # Primer gestor como principal
                entities['comparison_targets'] = [str(gid) for gid in gestores_ids_unicos[1:]]  # Resto para comparar
                print(f"🎯 Múltiples Gestores extraídos: {gestores_ids_unicos}")
        
        elif gestores_found:
            # Usar gestores encontrados por nombre
            if len(gestores_found) == 1:
                gestor_id, gestor_desc, centro, segmento = gestores_found[0]
                entities['gestor_id_extracted'] = str(gestor_id)
                entities['gestor_name'] = gestor_desc
            else:
                # Múltiples gestores por nombre
                entities['gestores_ids'] = [str(g[0]) for g in gestores_found]
                entities['gestores_names'] = [g[1] for g in gestores_found]
                entities['gestor_id_extracted'] = str(gestores_found[0][0])
                entities['gestor_name'] = gestores_found[0][1]
        
        # 4. KPIs financieros (genéricos) - mejorado
        kpis = {
            'roe': ['roe', 'rentabilidad', 'return on equity', 'retorno', 'rendimiento'],
            'margen': ['margen', 'margen neto', 'beneficio neto', 'margen bruto'],
            'eficiencia': ['eficiencia', 'ratio eficiencia', 'gastos', 'coste', 'costes'],
            'ingresos': ['ingresos', 'revenue', 'facturación', 'ventas', 'facturacion']
        }
        
        kpis_encontrados = []
        for kpi_key, kpi_terms in kpis.items():
            if any(term in message for term in kpi_terms):
                kpis_encontrados.append(kpi_key)
        
        if kpis_encontrados:
            if len(kpis_encontrados) == 1:
                entities['kpi'] = kpis_encontrados[0]
            else:
                entities['kpis'] = kpis_encontrados
                entities['kpi'] = kpis_encontrados[0]  # Primer KPI como principal
        
        # 5. 🆕 NUEVO: Extraer productos si se mencionan
        productos_patterns = [
            r'producto\s+(\w+)',
            r'préstamo|prestamo|hipoteca|hipotecario',
            r'depósito|deposito|plazo\s+fijo',
            r'fondo|fondos',
        ]
        
        for pattern in productos_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                entities['tiene_productos'] = True
                break
        
        return entities

    def _detect_intent(self, message: str) -> QueryIntent:
        """Detecta la intención principal de la consulta"""
        if any(re.search(pattern, message, re.IGNORECASE) for pattern in self.ranking_patterns):
            return QueryIntent.RANKING_ANALYSIS
        elif any(re.search(pattern, message, re.IGNORECASE) for pattern in self.causal_patterns):
            return QueryIntent.CAUSAL_ANALYSIS
        elif any(re.search(pattern, message, re.IGNORECASE) for pattern in self.comparative_patterns):
            return QueryIntent.COMPARATIVE_ANALYSIS
        elif any(re.search(pattern, message, re.IGNORECASE) for pattern in self.temporal_patterns):
            return QueryIntent.TEMPORAL_ANALYSIS
        elif re.search(r"(?:si|que pasaría|escenario|simulación|proyección)", message, re.IGNORECASE):
            return QueryIntent.SCENARIO_ANALYSIS
        else:
            return QueryIntent.PERFORMANCE_ANALYSIS

    def _assess_complexity(self, message: str) -> str:
        """Evalúa la complejidad de la consulta mejorada"""
        complexity_indicators = [
            (r'(?:comparar|versus|vs)', 'medium'),
            (r'(?:mejor|peor|ranking|top)', 'medium'),
            (r'(?:múltiples|varios|entre.*y)', 'medium'),  # 🆕 NUEVO
            (r'(?:por qué|causa|motivo)', 'high'),
            (r'(?:evolución|tendencia|histórico)', 'high'),
            (r'(?:simulación|escenario|proyección)', 'high'),
            (r'(?:\d+.*y.*\d+)', 'high'),  # 🆕 NUEVO: Detectar múltiples IDs
        ]
        
        for pattern, level in complexity_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                return level
        
        return 'low'

    def _requires_ranking(self, message: str) -> bool:
        """Determina si la consulta requiere un ranking"""
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in self.ranking_patterns)

    def _requires_comparison(self, message: str) -> bool:
        """Determina si la consulta requiere comparaciones"""
        comparison_indicators = self.comparative_patterns + self.ranking_patterns
        return any(re.search(pattern, message, re.IGNORECASE) for pattern in comparison_indicators)

    def get_suggested_queries(self, gestor_id: Optional[str] = None) -> List[str]:
        """Genera consultas sugeridas basadas en datos reales de la BD"""
        base_queries = [
            "¿Quién es el mejor gestor?",
            "¿Cómo se comparan los diferentes centros?", 
            "Comparar gestores 18 y 21 en ROE",  # 🆕 NUEVO
            "¿Por qué algunos gestores tienen mejores resultados?",
            "Mostrar evolución del ROE en los últimos meses",
            "Comparar Madrid vs Barcelona en eficiencia",  # 🆕 NUEVO
            "¿Cuáles son los factores de éxito de los top performers?"
        ]
        
        # Añadir consultas específicas usando datos reales
        try:
            segmentos = self._load_segmentos()
            if segmentos:
                primer_segmento = list(segmentos.values())[0][1]
                base_queries.insert(0, f"¿Quién es el mejor gestor de {primer_segmento}?")
            
            centros = self._load_centros()  
            if len(centros) >= 2:
                centro_names = [v[1].split('-')[0] for v in list(centros.values())[:2]]
                base_queries.insert(1, f"¿Cómo se compara {centro_names[0]} vs {centro_names[1]}?")
        except:
            pass
        
        if gestor_id:
            personalized_queries = [
                f"¿Cómo está el gestor {gestor_id} respecto a su centro?",
                f"Comparar gestor {gestor_id} con otros del mismo segmento",  # 🆕 MEJORADO
                f"¿Por qué el gestor {gestor_id} tiene estos resultados?",
                f"Evolución histórica del gestor {gestor_id}",
            ]
            return personalized_queries + base_queries[:3]
        
        return base_queries

    def clear_cache(self):
        """Limpia el cache para forzar recarga de datos"""
        self._centros_cache = None
        self._segmentos_cache = None
        self._gestores_cache = None

# Funciones de utilidad mejoradas
def is_complex_query(message: str) -> bool:
    """Determina rápidamente si una consulta es compleja"""
    parser = QueryParser()
    parsed = parser.parse_query(message)
    return parsed['complexity'] in ['medium', 'high']

def extract_query_intent(message: str) -> str:
    """Extrae rápidamente la intención de una consulta"""
    parser = QueryParser()
    parsed = parser.parse_query(message)
    return parsed['intent'].value

def extract_multiple_entities(message: str) -> Dict:
    """🆕 NUEVA: Extrae múltiples entidades de una consulta"""
    parser = QueryParser()
    parsed = parser.parse_query(message)
    return parsed['entities']
