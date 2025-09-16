// frontend/src/services/analyticsService.js
/* eslint-disable no-console */

/**
 * Analytics Service v11.0 — Perfect Integration (Chat Agent v10.0 + CDG Agent v6.0)
 * ---------------------------------------------------------------------------------
 * ✅ INTEGRADO: Todos los endpoints v11.0 con Perfect Integration
 * ✅ NUEVO: Soporte para gestorAnalysis, reflection, feedback, integration
 * ✅ ACTUALIZADO: Charts con pivot corregido y nuevos endpoints
 * ✅ AMPLIADO: Deviations con margen, volumen y critical
 * ✅ OPTIMIZADO: Cache inteligente y manejo de errores mejorado
 * ✅ CORREGIDO: Funciones async para manejo de segmentos dinámicos
 * ✅ AÑADIDO: Soporte completo para Dashboard de Dirección usando endpoints reales
 * ✅ ACTUALIZADO: +40 nuevos endpoints de analytics, kpis, incentives, dashboards
 */

import api, {
  analytics as analyticsAPI,
  dataQueries as dataQueriesAPI,
  charts as chartsAPI,
  basic as basicAPI,
  kpis as kpisAPI,
  comparatives as comparativesAPI,
  deviations as deviationsAPI,
  incentives as incentivesAPI,
  dashboards as dashboardsAPI,
  catalogs as catalogsAPI,
  gestorAnalysis as gestorAnalysisAPI,
  reflection as reflectionAPI,
  feedback as feedbackAPI,
  integration as integrationAPI,
  sql as sqlAPI,
  ApiClientError,
} from "./api";

/* =========================================
 * Constantes y utilidades de validación actualizadas
 * ========================================= */

const SCOPE = /** @type {const} */ ({
  GESTOR: "gestor",
  CENTRO: "centro",
  SEGMENTO: "segmento",
});

const VS = /** @type {const} */ ({
  BUDGET: "budget",
  LAST_YEAR: "last_year",
  LAST_PERIOD: "last_period",
});

const DEFAULTS = Object.freeze({
  scope: SCOPE.GESTOR,
  vs: VS.BUDGET,
});

/** Drivers admitidos típicamente en la variance bridge */
const KNOWN_DRIVERS = ["precio", "volumen", "mix", "fx", "one_offs"];

/** Paleta por semáforo (backend devuelve Verde/Amarillo/Rojo) */
const SEMAPHORE_COLORS = Object.freeze({
  Verde: "#22c55e",
  Amarillo: "#f59e0b",
  Rojo: "#ef4444",
  Gris: "#6b7280",
});

/** ✅ COLORES consistentes para visualizaciones */
const PRODUCT_COLORS = ["#022e16ff","#214239ff", "#224b3cff", "#267a65ff", "#2f8365ff",  "#339276ff", "#49a175ff"];
const CLIENT_COLORS = ["#214239ff", "#2a634fff", "#1a9072ff", "#46d2a1ff", "#022e16ff", "#34a382ff", "#49a175ff"];

/** ✅ COLORES ESPECÍFICOS PARA DASHBOARD DIRECCIÓN */
const DIRECTION_COLORS = Object.freeze({
  gestores: ["#022e16ff","#214239ff", "#224b3cff", "#267a65ff", "#2f8365ff",  "#339276ff", "#49a175ff", "#354d43ff"],
  centros: ["#022e16ff","#214239ff", "#224b3cff", "#267a65ff", "#2f8365ff"],
  productos: ["#214239ff", "#2a634fff", "#1a9072ff"],
  gastos: ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6"], // ✅ NUEVO para gastos
  general: ["#022e16ff","#214239ff", "#224b3cff", "#267a65ff", "#2f8365ff"]
});

/* =========================================
 * ✅ CONFIGURACIÓN PARA PIVOTEO DINÁMICO v11.0
 * ========================================= */

/**
 * ✅ CONFIGURACIÓN CENTRALIZADA: Métricas, dimensiones y tipos de gráfico pivoteables
 */
const PIVOTABLE_CONFIG = Object.freeze({
  // Métricas disponibles para pivoteo
  metrics: {
    'CONTRATOS': {
      label: 'Contratos',
      defaultValue: 0,
      format: '0,0',
      color: '#22c55e',
      endpoints: {
        gestor: 'basic.contractsByGestor',
        centro: 'basic.contractsByCentro', 
        producto: 'basic.contractsByProducto',
        cliente: 'basic.contractsByCliente',
        ranking: 'charts.gestoresRanking'
      }
    },
    'CLIENTES': {
      label: 'Clientes',
      defaultValue: 0,
      format: '0,0',
      color: '#3b82f6',
      endpoints: {
        gestor: 'basic.clientesByGestor',
        centro: 'basic.clientesByCentro',
        ranking: 'basic.gestoresRanking'
      }
    },
    'ROE': {
      label: 'ROE (%)',
      defaultValue: 0,
      format: '0.00%',
      color: '#f59e0b',
      endpoints: {
        gestor: 'kpis.gestorROE',
        centro: 'kpis.centroFinancieros',
        ranking: 'comparatives.gestoresRanking'
      }
    },
    'MARGEN_NETO': {
      label: 'Margen Neto (%)',
      defaultValue: 0,
      format: '0.00%', 
      color: '#ef4444',
      endpoints: {
        gestor: 'comparatives.gestoresMargen',
        centro: 'comparatives.centrosMargen',
        segmento: 'comparatives.segmentosMargen',
        ranking: 'comparatives.gestoresRanking'
      }
    },
    'INGRESOS': {
      label: 'Ingresos (€)',
      defaultValue: 0,
      format: '€0,0',
      color: '#10b981',
      endpoints: {
        gestor: 'analytics.gestorMetricasCompletas',
        centro: 'analytics.centroMetricas',
        segmento: 'analytics.segmentoMetricas'
      }
    },
    'INCENTIVOS': {
      label: 'Incentivos (€)',
      defaultValue: 0,
      format: '€0,0',
      color: '#8b5cf6',
      endpoints: {
        gestor: 'incentives.gestorDetalle',
        centro: 'incentives.centroTotal',
        pool: 'incentives.bonusPool'
      }
    }
  },

  // Dimensiones disponibles para pivoteo
  dimensions: {
    'gestor': {
      label: 'Gestores',
      idField: 'gestor_id',
      nameField: 'nombre_gestor',
      defaultChartType: 'horizontal_bar',
      supportedChartTypes: ['horizontal_bar', 'bar', 'pie', 'donut']
    },
    'centro': {
      label: 'Centros', 
      idField: 'centro_id',
      nameField: 'nombre_centro',
      defaultChartType: 'donut',
      supportedChartTypes: ['donut', 'pie', 'bar', 'horizontal_bar']
    },
    'producto': {
      label: 'Productos',
      idField: 'producto_id', 
      nameField: 'nombre_producto',
      defaultChartType: 'horizontal_bar',
      supportedChartTypes: ['horizontal_bar', 'bar', 'pie']
    },
    'cliente': {
      label: 'Clientes',
      idField: 'cliente_id',
      nameField: 'nombre_cliente', 
      defaultChartType: 'bar',
      supportedChartTypes: ['bar', 'horizontal_bar']
    },
    'segmento': {
      label: 'Segmentos',
      idField: 'segmento_id',
      nameField: 'nombre_segmento',
      defaultChartType: 'pie',
      supportedChartTypes: ['pie', 'donut', 'bar']
    }
  },

  // Tipos de gráfico soportados
  chartTypes: {
    'bar': { label: 'Barras', icon: '📊' },
    'horizontal_bar': { label: 'Barras Horizontales', icon: '📈' },
    'pie': { label: 'Circular', icon: '🥧' },
    'donut': { label: 'Donut', icon: '🍩' },
    'line': { label: 'Líneas', icon: '📉' },
    'area': { label: 'Área', icon: '🏔️' }
  }
});

/**
 * ✅ Valida si una combinación métrica/dimensión/tipo es soportada
 */
function validatePivotCombination(metric, dimension, chartType) {
  const metricConfig = PIVOTABLE_CONFIG.metrics[metric];
  const dimensionConfig = PIVOTABLE_CONFIG.dimensions[dimension];
  const chartTypeConfig = PIVOTABLE_CONFIG.chartTypes[chartType];

  if (!metricConfig) {
    return { valid: false, reason: `Métrica '${metric}' no soportada` };
  }

  if (!dimensionConfig) {
    return { valid: false, reason: `Dimensión '${dimension}' no soportada` };
  }

  if (!chartTypeConfig) {
    return { valid: false, reason: `Tipo de gráfico '${chartType}' no soportado` };
  }

  // Verificar si la métrica tiene endpoint para esta dimensión
  if (!metricConfig.endpoints[dimension] && !metricConfig.endpoints.ranking) {
    return { 
      valid: false, 
      reason: `Métrica '${metric}' no soporta dimensión '${dimension}'` 
    };
  }

  // Verificar si la dimensión soporta este tipo de gráfico
  if (!dimensionConfig.supportedChartTypes.includes(chartType)) {
    return { 
      valid: false, 
      reason: `Dimensión '${dimension}' no soporta gráfico '${chartType}'` 
    };
  }

  return { valid: true };
}

/** ✅ OBTENCIÓN DINÁMICA DE SEGMENTOS desde /catalogs */
let SEGMENT_INFO_CACHE = null;
let SEGMENT_CACHE_EXPIRY = 0;
const SEGMENT_CACHE_TTL = 5 * 60 * 1000; // 5 minutos

/**
 * ✅ FUNCIÓN DINÁMICA: Obtiene información de segmentos desde el backend
 */
async function getSegmentInfo() {
  const now = Date.now();
  
  if (SEGMENT_INFO_CACHE && now < SEGMENT_CACHE_EXPIRY) {
    return SEGMENT_INFO_CACHE;
  }

  try {
    console.log('[Analytics] 🔄 Fetching segment info from backend...');
    
    // Intentar obtener catálogos desde el backend
    const catalogsData = await api.catalogs.catalogs();
    
    if (catalogsData?.segmentos && Array.isArray(catalogsData.segmentos)) {
      const segmentMap = {};
      const colors = ['#1890ff', '#722ed1', '#13c2c2', '#52c41a', '#faad14'];
      
      catalogsData.segmentos.forEach((segment, index) => {
        const segmentId = segment.SEGMENTO_ID || segment.segmento_id;
        const segmentName = segment.DESC_SEGMENTO || segment.desc_segmento || segment.nombre;
        
        if (segmentId) {
          segmentMap[segmentId] = {
            nombre: segmentName || 'Segmento Desconocido',
            color: colors[index % colors.length]
          };
        }
      });
      
      SEGMENT_INFO_CACHE = segmentMap;
      SEGMENT_CACHE_EXPIRY = now + SEGMENT_CACHE_TTL;
      
      console.log('[Analytics] ✅ Segment info loaded dynamically:', Object.keys(segmentMap).length, 'segments');
      return segmentMap;
    }
    
  } catch (error) {
    console.warn('[Analytics] ⚠️ Error fetching dynamic segments, using fallback:', error.message);
  }

  // Fallback estático solo si falla la obtención dinámica
  const fallbackSegments = {
    'N10101': { nombre: 'Banca Minorista', color: '#1890ff' },
    'N10102': { nombre: 'Banca Privada', color: '#722ed1' },
    'N10103': { nombre: 'Banca de Empresas', color: '#13c2c2' },
    'N10104': { nombre: 'Banca Personal', color: '#52c41a' },
    'N20301': { nombre: 'Fondos', color: '#faad14' }
  };
  
  SEGMENT_INFO_CACHE = fallbackSegments;
  SEGMENT_CACHE_EXPIRY = now + SEGMENT_CACHE_TTL;
  
  console.log('[Analytics] 📋 Using fallback segment info');
  return fallbackSegments;
}

/** Valida y sanea parámetros de variance */
function validateVarianceParams({ scope, id, periodo, vs } = {}) {
  const _scope = [SCOPE.GESTOR, SCOPE.CENTRO, SCOPE.SEGMENTO].includes(scope)
    ? scope
    : DEFAULTS.scope;
  const _vs = [VS.BUDGET, VS.LAST_YEAR, VS.LAST_PERIOD].includes(vs)
    ? vs
    : DEFAULTS.vs;

  if (!periodo || typeof periodo !== "string") {
    throw new ApiClientError("Parametro 'periodo' es requerido (YYYY-MM)", {
      status: 400,
      code: 400,
    });
  }
  return { scope: _scope, id: id || null, periodo, vs: _vs };
}

/* =========================================
 * Cache in-memory (TTL) - MEJORADO para v11.0
 * ========================================= */

const _cache = new Map();
const DEFAULT_TTL_MS = 60 * 1000; // 60s

const _now = () => Date.now();
const _key = (name, params) => `${name}:${JSON.stringify(params || {})}`;

function _getCached(name, params) {
  const k = _key(name, params);
  const hit = _cache.get(k);
  if (!hit) return null;
  if (hit.expireAt && hit.expireAt < _now()) {
    _cache.delete(k);
    return null;
  }
  return hit.value;
}

function _setCached(name, params, value, ttlMs = DEFAULT_TTL_MS) {
  const k = _key(name, params);
  _cache.set(k, { value, expireAt: ttlMs ? _now() + ttlMs : 0 });
}

/**
 * ✅ OPTIMIZACIÓN: Limpia cache por período para asegurar frescura de datos
 */
function _clearCacheForPeriod(periodo) {
  const keysToDelete = [];
  for (let [key] of _cache) {
    if (key.includes(`"periodo":"${periodo}"`)) {
      keysToDelete.push(key);
    }
  }
  keysToDelete.forEach(key => _cache.delete(key));
  console.log(`[Analytics] ✅ Cleared cache for period ${periodo}: ${keysToDelete.length} entries`);
}

/**
 * ✅ NUEVA FUNCIÓN: Limpia cache específico de un gestor
 */
function _clearCacheForGestor(gestorId) {
  const keysToDelete = [];
  for (let [key] of _cache) {
    if (key.includes(`"gestorId":"${gestorId}"`) || key.includes(`"gestorId":${gestorId}`)) {
      keysToDelete.push(key);
    }
  }
  keysToDelete.forEach(key => _cache.delete(key));
  console.log(`[Analytics] ✅ Cleared cache for gestor ${gestorId}: ${keysToDelete.length} entries`);
}

function clearAnalyticsCache() {
  _cache.clear();
  SEGMENT_INFO_CACHE = null;
  SEGMENT_CACHE_EXPIRY = 0;
  console.log('[Analytics] ✅ Cache cleared completely including segment info');
}

/* =========================================
 * ✅ FUNCIONES DINÁMICAS PARA SEGMENTOS (mantenidas)
 * ========================================= */

/**
 * ✅ FUNCIÓN CORREGIDA - Obtiene el segmento de un gestor desde el backend
 */
async function getSegmentForGestor(gestorId) {
  try {
    if (!gestorId) return null;
    
    const numericId = parseInt(gestorId, 10);
    if (isNaN(numericId)) return null;

    console.log(`[Analytics] 🔍 Buscando segmento para gestor ${numericId}`);

    const segmentInfo = await getSegmentInfo();

    // Buscar el gestor en todos los segmentos
    for (const segmentoId of Object.keys(segmentInfo)) {
      try {
        const gestoresEnSegmento = await basicAPI.gestoresBySegmento(segmentoId);
        
        if (Array.isArray(gestoresEnSegmento)) {
          console.log(`[Analytics] Segment ${segmentoId}: ${gestoresEnSegmento.length} gestores`);
          
          // ✅ CORRECCIÓN CRÍTICA: Comparación robusta de claves
          const gestorEncontrado = gestoresEnSegmento.find(g => {
            // Probar múltiples variantes de clave (mayúsculas/minúsculas)
            const candidateId = g.GESTORID || g.gestorid || g.GESTOR_ID || g.gestor_id || g.id;
            
            if (candidateId == null) return false;
            
            // Comparación numérica robusta
            return parseInt(candidateId, 10) === numericId;
          });
          
          if (gestorEncontrado) {
            console.log(`[Analytics] ✅ Gestor ${numericId} encontrado en segmento ${segmentoId}`);
            return {
              id: segmentoId,
              nombre: segmentInfo[segmentoId]?.nombre || 'Segmento Desconocido'
            };
          }
        }
      } catch (segmentError) {
        console.warn(`[Analytics] Error checking segment ${segmentoId}:`, segmentError.message);
      }
    }

    console.warn(`[Analytics] ❌ Gestor ${numericId} no encontrado en ningún segmento`);
    return null;
    
  } catch (error) {
    console.error(`[Analytics] Error general fetching segmento for gestorId=${gestorId}:`, error);
    return null;
  }
}

/**
 * Función segura para obtener el segmento de un gestor con fallback
 */
async function getSegmentForGestorSafe(gestorId) {
  const segmento = await getSegmentForGestor(gestorId);
  
  if (segmento) {
    return { 
      segmentoId: segmento.id, 
      segmentoNombre: segmento.nombre 
    };
  }
  
  // Fallback en caso de error
  console.warn(`[Analytics] Using fallback segment for gestorId=${gestorId}`);
  return { 
    segmentoId: 'N10101', 
    segmentoNombre: 'Banca Minorista' 
  };
}

/**
 * ✅ FUNCIÓN COMPLETAMENTE REESCRITA: Filtra datos por segmento de forma robusta
 */
function filterDataBySegment(data, targetSegmentId) {
  if (!data || !targetSegmentId) {
    console.warn('[Analytics] No data or targetSegmentId provided for filtering');
    return data;
  }
  
  console.log(`[Analytics] Filtering data for segment: ${targetSegmentId}`);
  
  const filtered = {
    standard: [],
    real: []
  };
  
  // Filtrar standard
  if (Array.isArray(data.standard)) {
    const beforeCount = data.standard.length;
    filtered.standard = data.standard.filter(item => {
      const itemSegmentId = item.SEGMENTO_ID || item.segmento_id;
      return itemSegmentId === targetSegmentId;
    });
    console.log(`[Analytics] Standard: ${beforeCount} -> ${filtered.standard.length} items`);
  }
  
  // Filtrar real
  if (Array.isArray(data.real)) {
    const beforeCount = data.real.length;
    filtered.real = data.real.filter(item => {
      const itemSegmentId = item.SEGMENTO_ID || item.segmento_id;
      return itemSegmentId === targetSegmentId;
    });
    console.log(`[Analytics] Real: ${beforeCount} -> ${filtered.real.length} items`);
  }
  
  // ✅ VALIDACIÓN: Verificar que el filtrado funciona
  if (filtered.standard.length === 0 && filtered.real.length === 0) {
    console.error(`[Analytics] FILTRO FALLÓ: No hay datos para segmento ${targetSegmentId}`);
    console.log('[Analytics] Available segments in data:', 
      [...new Set([
        ...(data.standard || []).map(i => i.SEGMENTO_ID || i.segmento_id),
        ...(data.real || []).map(i => i.SEGMENTO_ID || i.segmento_id)
      ])]
    );
  }
  
  return filtered;
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA ANALYTICS v11.0 - MÉTRICAS FINANCIERAS
 * ========================================= */

/**
 * ✅ NUEVO: Métricas financieras por centro
 */
async function getCentroMetricas(centroId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🏢 Fetching metrics for centro ${centroId}, period ${periodo}`);
  
  const cacheKey = { centroId, periodo, type: 'centro_metricas' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached centro metrics`);
    return cached;
  }

  try {
    const result = await analyticsAPI.centroMetricas(centroId, periodo, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Centro metrics loaded for ${centroId}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching centro metrics:`, error.message);
    return {
      centro_id: centroId,
      periodo,
      error: error.message,
      metricas: {}
    };
  }
}

/**
 * ✅ NUEVO: Gestores con métricas por centro
 */
async function getCentroGestoresMetricas(centroId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 👥 Fetching gestores metrics for centro ${centroId}`);
  
  const cacheKey = { centroId, periodo, type: 'centro_gestores_metricas' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached centro gestores metrics`);
    return cached;
  }

  try {
    const result = await analyticsAPI.centroGestoresMetricas(centroId, periodo, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Centro gestores metrics loaded: ${result.length} gestores`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching centro gestores metrics:`, error.message);
    return [];
  }
}

/**
 * ✅ NUEVO: Métricas financieras por segmento
 */
async function getSegmentoMetricas(segmentoId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🎯 Fetching metrics for segmento ${segmentoId}, period ${periodo}`);
  
  const cacheKey = { segmentoId, periodo, type: 'segmento_metricas' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached segmento metrics`);
    return cached;
  }

  try {
    const result = await analyticsAPI.segmentoMetricas(segmentoId, periodo, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Segmento metrics loaded for ${segmentoId}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching segmento metrics:`, error.message);
    return {
      segmento_id: segmentoId,
      periodo,
      error: error.message,
      metricas: {}
    };
  }
}

/**
 * ✅ NUEVO: Métricas completas por gestor
 */
async function getGestorMetricasCompletas(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 👤 Fetching complete metrics for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'gestor_metricas_completas' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor complete metrics`);
    return cached;
  }

  try {
    const result = await analyticsAPI.gestorMetricasCompletas(gestorId, periodo, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor complete metrics loaded for ${gestorId}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor complete metrics:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      error: error.message,
      metricas: {}
    };
  }
}

/**
 * ✅ NUEVO: Clientes con métricas por gestor
 */
async function getGestorClientesMetricas(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🤝 Fetching client metrics for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'gestor_clientes_metricas' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor client metrics`);
    return cached;
  }

  try {
    const result = await analyticsAPI.gestorClientesMetricas(gestorId, periodo, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor client metrics loaded: ${result.length} clients`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor client metrics:`, error.message);
    return [];
  }
}

/**
 * ✅ NUEVO: Métricas por cliente
 */
async function getClienteMetricas(clienteId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🤝 Fetching metrics for cliente ${clienteId}`);
  
  const cacheKey = { clienteId, periodo, type: 'cliente_metricas' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached cliente metrics`);
    return cached;
  }

  try {
    const result = await analyticsAPI.clienteMetricas(clienteId, periodo, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Cliente metrics loaded for ${clienteId}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching cliente metrics:`, error.message);
    return {
      cliente_id: clienteId,
      periodo,
      error: error.message,
      metricas: {}
    };
  }
}

/**
 * ✅ NUEVO: Contratos con métricas por cliente
 */
async function getClienteContratosMetricas(clienteId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 📋 Fetching contract metrics for cliente ${clienteId}`);
  
  const cacheKey = { clienteId, periodo, type: 'cliente_contratos_metricas' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached cliente contract metrics`);
    return cached;
  }

  try {
    const result = await analyticsAPI.clienteContratosMetricas(clienteId, periodo, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Cliente contract metrics loaded: ${result.length} contracts`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching cliente contract metrics:`, error.message);
    return [];
  }
}

/**
 * ✅ NUEVO: Detalle completo por contrato
 */
async function getContratoDetalleCompleto(contratoId, options = {}) {
  console.log(`[Analytics] 📄 Fetching complete detail for contrato ${contratoId}`);
  
  const cacheKey = { contratoId, type: 'contrato_detalle_completo' };
  const cached = _getCached("analytics", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached contrato complete detail`);
    return cached;
  }

  try {
    const result = await analyticsAPI.contratoDetalleCompleto(contratoId, options);
    
    _setCached("analytics", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Contrato complete detail loaded for ${contratoId}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching contrato complete detail:`, error.message);
    return {
      contrato_id: contratoId,
      error: error.message,
      detalle: {}
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA KPIs v11.0 - FINANCIEROS ESPECÍFICOS
 * ========================================= */

/**
 * ✅ NUEVO: KPIs financieros por centro
 */
async function getCentroKPIsFinancieros(centroId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 📊 Fetching financial KPIs for centro ${centroId}`);
  
  const cacheKey = { centroId, periodo, type: 'centro_kpis_financieros' };
  const cached = _getCached("kpis", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached centro financial KPIs`);
    return cached;
  }

  try {
    const result = await kpisAPI.centroFinancieros(centroId, periodo, options);
    
    _setCached("kpis", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Centro financial KPIs loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching centro financial KPIs:`, error.message);
    return {
      centro_id: centroId,
      periodo,
      error: error.message,
      kpis_financieros: {}
    };
  }
}

/**
 * ✅ NUEVO: KPIs financieros por gestor
 */
async function getGestorKPIsFinancieros(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 📊 Fetching financial KPIs for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'gestor_kpis_financieros' };
  const cached = _getCached("kpis", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor financial KPIs`);
    return cached;
  }

  try {
    const result = await kpisAPI.gestorFinancieros(gestorId, periodo, options);
    
    _setCached("kpis", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor financial KPIs loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor financial KPIs:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      error: error.message,
      kpis_financieros: {}
    };
  }
}

/**
 * ✅ NUEVO: ROE específico por gestor
 */
async function getGestorROE(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 📈 Fetching ROE for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'gestor_roe' };
  const cached = _getCached("kpis", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor ROE`);
    return cached;
  }

  try {
    const result = await kpisAPI.gestorROE(gestorId, periodo, options);
    
    _setCached("kpis", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor ROE loaded: ${result.roe_pct}%`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor ROE:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      roe_pct: 0,
      clasificacion: 'ERROR',
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Eficiencia específica por gestor
 */
async function getGestorEficiencia(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] ⚡ Fetching efficiency for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'gestor_eficiencia' };
  const cached = _getCached("kpis", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor efficiency`);
    return cached;
  }

  try {
    const result = await kpisAPI.gestorEficiencia(gestorId, periodo, options);
    
    _setCached("kpis", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor efficiency loaded: ${result.ratio_eficiencia}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor efficiency:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      ratio_eficiencia: 0,
      clasificacion: 'ERROR',
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Margen específico por centro
 */
async function getCentroMargen(centroId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 💰 Fetching margin for centro ${centroId}`);
  
  const cacheKey = { centroId, periodo, type: 'centro_margen' };
  const cached = _getCached("kpis", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached centro margin`);
    return cached;
  }

  try {
    const result = await kpisAPI.centroMargen(centroId, periodo, options);
    
    _setCached("kpis", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Centro margin loaded: ${result.margen_neto_pct}%`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching centro margin:`, error.message);
    return {
      centro_id: centroId,
      periodo,
      margen_neto_pct: 0,
      clasificacion: 'ERROR',
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Total bonus por centro
 */
async function getCentroBonusTotal(centroId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🎁 Fetching total bonus for centro ${centroId}`);
  
  const cacheKey = { centroId, periodo, type: 'centro_bonus_total' };
  const cached = _getCached("kpis", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached centro total bonus`);
    return cached;
  }

  try {
    const result = await kpisAPI.centroBonusTotal(centroId, periodo, options);
    
    _setCached("kpis", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Centro total bonus loaded: €${result.bonus_total}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching centro total bonus:`, error.message);
    return {
      centro_id: centroId,
      periodo,
      bonus_total: 0,
      gestores_con_bonus: 0,
      error: error.message
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA INCENTIVES v11.0 - DETALLADOS
 * ========================================= */

/**
 * ✅ NUEVO: Total incentivos por centro
 */
async function getIncentivesCentroTotal(centroId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🏆 Fetching total incentives for centro ${centroId}`);
  
  const cacheKey = { centroId, periodo, type: 'incentives_centro_total' };
  const cached = _getCached("incentives", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached centro total incentives`);
    return cached;
  }

  try {
    const result = await incentivesAPI.centroTotal(centroId, periodo, options);
    
    _setCached("incentives", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Centro total incentives loaded: €${result.total_incentivos}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching centro total incentives:`, error.message);
    return {
      centro_id: centroId,
      periodo,
      total_incentivos: 0,
      gestores_elegibles: 0,
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Detalle completo incentivos por gestor
 */
async function getIncentivesGestorDetalle(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🎯 Fetching detailed incentives for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'incentives_gestor_detalle' };
  const cached = _getCached("incentives", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor detailed incentives`);
    return cached;
  }

  try {
    const result = await incentivesAPI.gestorDetalle(gestorId, periodo, options);
    
    _setCached("incentives", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor detailed incentives loaded: €${result.total_incentivos}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor detailed incentives:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      total_incentivos: 0,
      detalle_incentivos: {},
      error: error.message
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA DASHBOARDS v11.0 - ESPECÍFICOS
 * ========================================= */

/**
 * ✅ NUEVO: Dashboard resumen por gestor
 */
async function getDashboardGestorSummary(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 📊 Fetching dashboard summary for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'dashboard_gestor_summary' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor summary dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.gestorSummary(gestorId, periodo, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor summary dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor summary dashboard:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      charts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Dashboard evolución por gestor
 */
async function getDashboardGestorEvolution(gestorId, options = {}) {
  console.log(`[Analytics] 📈 Fetching evolution dashboard for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, type: 'dashboard_gestor_evolution' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor evolution dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.gestorEvolution(gestorId, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor evolution dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor evolution dashboard:`, error.message);
    return {
      gestor_id: gestorId,
      charts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Dashboard productos por gestor
 */
async function getDashboardGestorProductos(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🛍️ Fetching products dashboard for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'dashboard_gestor_productos' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor products dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.gestorProductos(gestorId, periodo, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor products dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor products dashboard:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      charts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Dashboard alertas por gestor
 */
async function getDashboardGestorAlertas(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🚨 Fetching alerts dashboard for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'dashboard_gestor_alertas' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor alerts dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.gestorAlertas(gestorId, periodo, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor alerts dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor alerts dashboard:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      alerts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Dashboard comparativo por gestor
 */
async function getDashboardGestorComparative(gestorId, periodo = "2025-10", options = {}) {
  console.log(`[Analytics] ⚖️ Fetching comparative dashboard for gestor ${gestorId}`);
  
  const cacheKey = { gestorId, periodo, type: 'dashboard_gestor_comparative' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gestor comparative dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.gestorComparative(gestorId, periodo, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Gestor comparative dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gestor comparative dashboard:`, error.message);
    return {
      gestor_id: gestorId,
      periodo,
      charts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Dashboard resumen incentivos
 */
async function getDashboardIncentivosSummary(periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🏆 Fetching incentives summary dashboard`);
  
  const cacheKey = { periodo, type: 'dashboard_incentivos_summary' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached incentives summary dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.incentivosSummary(periodo, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Incentives summary dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching incentives summary dashboard:`, error.message);
    return {
      periodo,
      charts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Dashboard tendencia incentivos
 */
async function getDashboardIncentivosTendencia(options = {}) {
  console.log(`[Analytics] 📊 Fetching incentives trend dashboard`);
  
  const cacheKey = { type: 'dashboard_incentivos_tendencia' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached incentives trend dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.incentivosTendencia(options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Incentives trend dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching incentives trend dashboard:`, error.message);
    return {
      charts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Dashboard comparativo summary
 */
async function getDashboardComparativeSummary(periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 📊 Fetching comparative summary dashboard`);
  
  const cacheKey = { periodo, type: 'dashboard_comparative_summary' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached comparative summary dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.comparativeSummary(periodo, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Comparative summary dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching comparative summary dashboard:`, error.message);
    return {
      periodo,
      charts: [],
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Matriz comparativa segmentos
 */
async function getDashboardMatrizSegmentos(periodo = "2025-10", options = {}) {
  console.log(`[Analytics] 🎯 Fetching segments matrix dashboard`);
  
  const cacheKey = { periodo, type: 'dashboard_matriz_segmentos' };
  const cached = _getCached("dashboards", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached segments matrix dashboard`);
    return cached;
  }

  try {
    const result = await dashboardsAPI.matrizSegmentos(periodo, options);
    
    _setCached("dashboards", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Segments matrix dashboard loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching segments matrix dashboard:`, error.message);
    return {
      periodo,
      matriz: [],
      error: error.message
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA CATALOGS v11.0 - PERÍODOS CON MÉTRICAS
 * ========================================= */

/**
 * ✅ NUEVO: Métricas financieras por período
 */
async function getPeriodMetricas(periodo, options = {}) {
  console.log(`[Analytics] 📅 Fetching period metrics for ${periodo}`);
  
  const cacheKey = { periodo, type: 'period_metricas' };
  const cached = _getCached("catalogs", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached period metrics`);
    return cached;
  }

  try {
    const result = await catalogsAPI.periodMetricas(periodo, options);
    
    _setCached("catalogs", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Period metrics loaded for ${periodo}`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching period metrics:`, error.message);
    return {
      periodo,
      error: error.message,
      metricas: {}
    };
  }
}

/**
 * ✅ NUEVO: Comparación entre períodos
 */
async function getComparePeriods(periodoActual, periodoAnterior, options = {}) {
  console.log(`[Analytics] 📊 Comparing periods ${periodoAnterior} vs ${periodoActual}`);
  
  const cacheKey = { periodoActual, periodoAnterior, type: 'compare_periods' };
  const cached = _getCached("catalogs", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached period comparison`);
    return cached;
  }

  try {
    const result = await catalogsAPI.comparePeriods(periodoActual, periodoAnterior, options);
    
    _setCached("catalogs", cacheKey, result, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Period comparison loaded`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error comparing periods:`, error.message);
    return {
      periodo_actual: periodoActual,
      periodo_anterior: periodoAnterior,
      error: error.message,
      comparacion: {}
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA SQL v11.0
 * ========================================= */

/**
 * ✅ NUEVO: Ejecutar SQL dinámico validado
 */
async function executeDynamicSQL(sql, context = "general", options = {}) {
  console.log(`[Analytics] 🔍 Executing dynamic SQL (${context})`);
  
  try {
    const result = await sqlAPI.dynamic(sql, context, options);
    
    console.log(`[Analytics] ✅ Dynamic SQL executed successfully`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error executing dynamic SQL:`, error.message);
    return {
      error: error.message,
      sql: sql.substring(0, 100) + (sql.length > 100 ? '...' : ''),
      context,
      rows: []
    };
  }
}

/**
 * ✅ NUEVO: Validar SQL
 */
async function validateSQL(sql, context = "general", options = {}) {
  console.log(`[Analytics] ✅ Validating SQL (${context})`);
  
  try {
    const result = await sqlAPI.validate(sql, context, options);
    
    console.log(`[Analytics] ✅ SQL validation completed`);
    return result;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error validating SQL:`, error.message);
    return {
      is_safe: false,
      error: error.message,
      sql: sql.substring(0, 100) + (sql.length > 100 ? '...' : ''),
      context
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA DASHBOARD DIRECCIÓN v11.0
 * ========================================= */

/**
 * ✅ FUNCIÓN PRINCIPAL ACTUALIZADA: Obtiene datos para gráficos del dashboard de dirección
 */
async function getDirectionChartData(chartType = 'gestores-ranking', options = {}) {
  const { metric = 'CONTRATOS', chart_type = 'horizontal_bar', periodo, fecha } = options;
  
  console.log(`[Analytics] 🎯 getDirectionChartData: ${chartType}, metric: ${metric}, chart_type: ${chart_type}`);
  
  const cacheKey = { chartType, metric, chart_type, periodo, fecha };
  const cached = _getCached("direction_chart", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached direction chart: ${chartType}`);
    return cached;
  }

  try {
    let result;
    
    switch (chartType) {
      case 'gestores-ranking':
        console.log(`[Analytics] 📊 Calling chartsAPI.gestoresRanking with metric: ${metric}`);
        result = await chartsAPI.gestoresRanking({ metric, chartType: chart_type });
        break;
      case 'centros-distribution':
        console.log(`[Analytics] 📊 Calling chartsAPI.centrosDistribution`);
        result = await chartsAPI.centrosDistribution({ chartType: chart_type });
        break;
      case 'productos-popularity':
        console.log(`[Analytics] 📊 Calling chartsAPI.productosPopularity`);
        result = await chartsAPI.productosPopularity({ chartType: chart_type });
        break;
      case 'precios-comparison':
        console.log(`[Analytics] 📊 Calling chartsAPI.preciosComparison`);
        result = await chartsAPI.preciosComparison({ fechaCalculo: fecha, chartType: chart_type });
        break;
      case 'gastos-by-centro':
        // ✅ NUEVO: Endpoint de gastos por centro
        console.log(`[Analytics] 📊 Calling chartsAPI.gastosByCentro`);
        result = await chartsAPI.gastosByCentro({ fecha, chartType: chart_type });
        break;
      case 'summary-dashboard':
        console.log(`[Analytics] 📊 Calling chartsAPI.summaryDashboard`);
        result = await chartsAPI.summaryDashboard();
        break;
      default:
        throw new Error(`Chart type ${chartType} not supported`);
    }

    console.log(`[Analytics] ✅ Backend response received for ${chartType}:`, {
      hasChart: !!result.chart,
      dataLength: result.chart?.data?.length || 0,
      chartId: result.chart?.id
    });

    // Transformar a formato uniforme para InteractiveCharts
    const transformed = transformBackendChartData(result, chartType);
    
    _setCached("direction_chart", cacheKey, transformed, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] 🎉 Direction chart data ready:`, {
      type: chartType,
      labelsCount: transformed.labels?.length || 0,
      hasData: transformed.datasets?.length > 0
    });
    
    return transformed;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching direction chart ${chartType}:`, error.message);
    return generateMockDirectionChart(chartType, options);
  }
}

/**
 * ✅ OPTIMIZACIÓN: Nueva función para obtener datos KPIs unificados usando endpoints reales
 */
async function getUnifiedKPIData(gestorId, periodo, options = {}) {
  console.log(`[Analytics] 🎯 getUnifiedKPIData: gestor ${gestorId}, period ${periodo}`);
  
  const cacheKey = { gestorId, periodo, type: 'unified_kpi' };
  const cached = _getCached("kpi_data", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached KPI data for gestor ${gestorId}`);
    return cached;
  }

  try {
    // ✅ USAR ENDPOINT REAL /kpis/gestor/{id}
    const kpiData = await kpisAPI.gestor(gestorId, periodo);
    
    // ✅ USAR ENDPOINT REAL /comparatives/gestores/margen
    const comparativeData = await comparativesAPI.gestoresMargen(periodo);
    
    // ✅ NUEVO: Usar endpoint /gestor/{id}/performance si está disponible
    let performanceData = null;
    try {
      performanceData = await gestorAnalysisAPI.performance(gestorId, periodo);
      console.log(`[Analytics] ✅ Performance data loaded for gestor ${gestorId}`);
    } catch (perfError) {
      console.warn(`[Analytics] Performance data not available:`, perfError.message);
    }
    
    // Encontrar datos específicos del gestor en las comparativas
    const gestorComparative = comparativeData?.find(item => {
      const itemGestorId = item.GESTOR_ID || item.gestor_id;
      return parseInt(itemGestorId, 10) === parseInt(gestorId, 10);
    });

    const unified = {
      // Datos básicos del gestor
      gestorId,
      periodo,
      nombreGestor: kpiData?.kpis?.desc_gestor || performanceData?.nombre_gestor || 'Gestor Desconocido',
      centro: kpiData?.kpis?.desc_centro || performanceData?.centro || 'Centro Desconocido',
      segmento: kpiData?.kpis?.desc_segmento || performanceData?.segmento || 'Segmento Desconocido',
      
      // KPIs principales
      totalContratos: kpiData?.kpis?.total_contratos || performanceData?.total_contratos || 0,
      totalClientes: kpiData?.kpis?.total_clientes || performanceData?.total_clientes || 0,
      totalIngresos: kpiData?.kpis?.total_ingresos || performanceData?.total_ingresos || 0,
      patrimonioTotal: kpiData?.kpis?.patrimonio_total || performanceData?.patrimonio_total || 0,
      margenNeto: kpiData?.kpis?.margen_neto || performanceData?.margen_neto || 0,
      beneficioNeto: kpiData?.kpis?.beneficio_neto || performanceData?.beneficio_neto || 0,
      roe: kpiData?.kpis?.roe_pct || performanceData?.roe_pct || 0,
      
      // Clasificaciones cualitativas
      clasificacionMargen: kpiData?.kpis?.clasificacion_margen || 'DESCONOCIDO',
      clasificacionROE: kpiData?.kpis?.clasificacion_roe || 'DESCONOCIDO',
      clasificacionEficiencia: kpiData?.kpis?.clasificacion_eficiencia || 'DESCONOCIDO',
      
      // Datos comparativos
      ranking: gestorComparative?.ranking || performanceData?.ranking || null,
      mediaMargen: gestorComparative?.media_margen || null,
      desviacionVsMedia: gestorComparative?.desviacion_vs_media || null,
      categoriaPerformance: gestorComparative?.categoria_performance || performanceData?.categoria_performance || 'DESCONOCIDO',
      
      // Metadatos
      raw: {
        kpiData,
        gestorComparative,
        performanceData,
        hasRealData: true
      }
    };

    _setCached("kpi_data", cacheKey, unified, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Unified KPI data ready for gestor ${gestorId}:`, {
      contratos: unified.totalContratos,
      margen: unified.margenNeto,
      ranking: unified.ranking
    });
    
    return unified;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching unified KPI data:`, error.message);
    
    // Fallback con datos mock básicos
    return {
      gestorId,
      periodo,
      nombreGestor: 'Gestor Desconocido',
      centro: 'Centro Desconocido',
      segmento: 'Segmento Desconocido',
      totalContratos: Math.floor(Math.random() * 50) + 10,
      totalClientes: Math.floor(Math.random() * 30) + 5,
      totalIngresos: Math.floor(Math.random() * 50000) + 10000,
      patrimonioTotal: Math.floor(Math.random() * 100000) + 20000,
      margenNeto: Math.floor(Math.random() * 80) + 20,
      beneficioNeto: Math.floor(Math.random() * 40000) + 5000,
      roe: Math.floor(Math.random() * 60) + 20,
      clasificacionMargen: 'EXCELENTE',
      clasificacionROE: 'SOBRESALIENTE',
      clasificacionEficiencia: 'MUY_EFICIENTE',
      ranking: Math.floor(Math.random() * 30) + 1,
      mediaMargen: 65.92,
      desviacionVsMedia: Math.floor(Math.random() * 20) - 10,
      categoriaPerformance: 'GOOD_PERFORMER',
      raw: { hasRealData: false, mockData: true }
    };
  }
}

/**
 * ✅ FUNCIÓN DE TRANSFORMACIÓN: Convierte datos del backend al formato esperado por InteractiveCharts
 */
function transformBackendChartData(backendData, chartType) {
  console.log(`[Analytics] 🔄 Transforming backend data for ${chartType}`);
  
  const chart = backendData.chart || backendData;
  
  if (!chart || !chart.data || !Array.isArray(chart.data)) {
    console.error('[Analytics] Invalid chart data from backend:', { chart: !!chart, data: !!chart?.data });
    throw new Error('Invalid chart data from backend');
  }

  console.log(`[Analytics] Chart data items: ${chart.data.length}`);

  // Extraer labels y values
  const labels = chart.data.map(item => item.label || 'Sin Etiqueta');
  const values = chart.data.map(item => item.value || 0);
  
  // Colores basados en el tipo de gráfico
  const colors = getColorsForChartType(chartType, chart.data.length);
  
  const transformed = {
    labels,
    datasets: [{
      label: getDatasetLabel(chart.metric || chartType),
      data: values,
      backgroundColor: colors,
      borderRadius: 4,
    }],
    raw: chart.data,
    meta: {
      type: chartType,
      title: chart.title,
      total: chart.data.length,
      showing: chart.data.length,
      dimension: chart.dimension,
      metric: chart.metric,
      interactive: chart.interactive || false,
      pivot_enabled: chart.pivot_enabled || false,
      created_at: chart.created_at,
      chart_id: chart.id,
      data_source: chart.data_source || 'backend'
    }
  };
  
  console.log(`[Analytics] ✅ Transform complete:`, {
    labels: labels.length,
    values: values.length,
    colors: colors.length
  });
  
  return transformed;
}

/**
 * ✅ FUNCIÓN MEJORADA: Pivoteo conversacional que integra con getPivotableChartData
 */
async function pivotChart(userId, message, currentChartConfig = {}, chartInteractionType = "pivot", options = {}) {
  if (!userId || !message) {
    throw new Error('userId and message are required for pivot');
  }
  
  console.log(`[Analytics] 🔄 Enhanced pivot with message: "${message}"`);
  console.log(`[Analytics] Current config:`, currentChartConfig);

  try {
    // 1. Intentar usar backend para pivoteo
    const result = await chartsAPI.pivot({ 
      userId, 
      message, 
      currentChartConfig, 
      chartInteractionType 
    }, options);
    
    console.log(`[Analytics] ✅ Backend pivot successful`);
    return transformBackendChartData(result, 'pivot_result');
    
  } catch (backendError) {
    console.warn(`[Analytics] ⚠️ Backend pivot failed, trying local parsing:`, backendError.message);

    // 2. Fallback: usar parser local desde chatService si está disponible
    const chatService = await import('./chatService.js');
    const parsedIntent = chatService.parsePivotIntent?.(message, currentChartConfig);

    if (parsedIntent && parsedIntent.intent === 'pivot') {
      console.log(`[Analytics] ✅ Local parsing successful:`, parsedIntent);
      
      // 3. Usar función unificada para obtener datos
      const pivotedData = await getPivotableChartData(
        parsedIntent.metric || currentChartConfig.metric || 'CONTRATOS',
        parsedIntent.dimension || currentChartConfig.dimension || 'gestor', 
        parsedIntent.chartType || currentChartConfig.chartType || 'bar',
        { ...options, userId }
      );

      // Añadir metadatos de pivoteo
      pivotedData.meta = {
        ...pivotedData.meta,
        pivot_source: 'local_parser',
        original_message: message,
        changes_made: [
          `Pivoteo: ${pivotedData.meta.metricLabel} por ${pivotedData.meta.dimensionLabel} como ${pivotedData.meta.chartType}`
        ]
      };

      return pivotedData;
    }

    // 4. Si todo falla, mantener configuración actual pero mostrar error
    throw new Error(`No se pudo interpretar la intención de pivoteo: "${message}"`);
  }
}


/**
 * ✅ FUNCIÓN PARA OBTENER METADATOS DE CHARTS: Obtiene tipos de gráfico soportados y configuraciones
 */
async function getChartMeta() {
  const cacheKey = 'chart_meta';
  const cached = _getCached(cacheKey, {});
  if (cached) {
    console.log('[Analytics] Using cached chart meta');
    return cached;
  }

  try {
    console.log('[Analytics] 🔍 Fetching chart meta from backend');
    const meta = await chartsAPI.meta();
    
    _setCached(cacheKey, {}, meta, 5 * 60 * 1000); // 5 minutos cache
    
    console.log('[Analytics] ✅ Chart meta loaded:', {
      chartTypes: meta.charttypes?.length || 0,
      dimensions: Object.keys(meta.dimensions || {}).length,
      metrics: Object.keys(meta.metrics || {}).length
    });
    
    return meta;
  } catch (error) {
    console.error('[Analytics] ❌ Error fetching chart meta:', error.message);
    
    // Fallback meta basado en los endpoints disponibles
    return {
      charttypes: ['bar', 'line', 'pie', 'donut', 'horizontal_bar', 'stacked_bar'],
      dimensions: {
        gestor: 'Gestor',
        centro: 'Centro',
        producto: 'Producto',
        segmento: 'Segmento'
      },
      metrics: {
        CONTRATOS: 'Contratos',
        CLIENTES: 'Clientes',
        INGRESOS: 'Ingresos',
        MARGEN: 'Margen'
      },
      supportspivot: true
    };
  }
}

/* =========================================
 * ✅ FUNCIÓN UNIFICADA PARA PIVOTEO DINÁMICO v11.0
 * ========================================= */

/**
 * ✅ FUNCIÓN PRINCIPAL: Obtiene datos para cualquier combinación métrica/dimensión/tipo
 */
async function getPivotableChartData(metric, dimension, chartType = 'bar', options = {}) {
  const { periodo = '2025-10', gestorId, centroId, limit = 10 } = options;
  
  console.log(`[Analytics] 🎯 getPivotableChartData: ${metric} by ${dimension} as ${chartType}`);
  
 const validation = validatePivotCombination(metric, dimension, chartType);
  if (!validation.valid) {
    throw new Error(`❌ ${validation.reason}`);
  }

  const cacheKey = { metric, dimension, chartType, periodo, gestorId, centroId, type: 'pivotable' };
  const cached = _getCached("pivotable_chart", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached pivotable data`);
    return cached;
  }

  try {
    const metricConfig = PIVOTABLE_CONFIG.metrics[metric];
    const dimensionConfig = PIVOTABLE_CONFIG.dimensions[dimension];
    
    // Determinar qué endpoint usar
    const endpointKey = metricConfig.endpoints[dimension] || metricConfig.endpoints.ranking;
    if (!endpointKey) {
      throw new Error(`No endpoint available for ${metric} by ${dimension}`);
    }

    console.log(`[Analytics] Using endpoint: ${endpointKey}`);

    // Llamar al endpoint correspondiente
    let rawData;
    const endpointParts = endpointKey.split('.');
    const apiModule = endpointParts[0]; // 'basic', 'kpis', etc.
    const apiMethod = endpointParts[1]; // 'gestoresRanking', etc.

    // Construir parámetros dinámicamente
    const params = { periodo };
    if (gestorId) params.gestorId = gestorId;
    if (centroId) params.centroId = centroId;
    if (metric === 'CONTRATOS') params.metric = 'CONTRATOS';

    // Ejecutar llamada dinámica al API
    switch (apiModule) {
      case 'basic':
        rawData = await basicAPI[apiMethod](gestorId || centroId, { ...params });
        break;
      case 'kpis':
        rawData = await kpisAPI[apiMethod](gestorId || centroId, periodo, { ...params });
        break;
      case 'comparatives':
        rawData = await comparativesAPI[apiMethod](periodo, { ...params });
        break;
      case 'charts':
        rawData = await chartsAPI[apiMethod]({ ...params, chartType });
        break;
      case 'analytics':
        rawData = await analyticsAPI[apiMethod](gestorId || centroId, periodo, { ...params });
        break;
      case 'incentives':
        rawData = await incentivesAPI[apiMethod](gestorId || centroId, periodo, { ...params });
        break;
      default:
        throw new Error(`API module '${apiModule}' not supported`);
    }

    console.log(`[Analytics] Raw data received:`, { 
      type: typeof rawData, 
      length: Array.isArray(rawData) ? rawData.length : 'N/A',
      hasChart: !!rawData?.chart
    });

    // Transformar datos usando la función existente o crear nueva estructura
    const transformed = transformPivotableData(rawData, {
      metric,
      dimension,
      chartType,
      metricConfig,
      dimensionConfig,
      limit
    });

    _setCached("pivotable_chart", cacheKey, transformed, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Pivotable chart data ready:`, {
      labels: transformed.labels?.length || 0,
      datasets: transformed.datasets?.length || 0
    });

    return transformed;

  } catch (error) {
    console.error(`[Analytics] ❌ Error in getPivotableChartData:`, error.message);
    
    // Fallback con datos mock
    return generateMockPivotableChart(metric, dimension, chartType, options);
  }
}

/**
 * ✅ Transforma datos del backend al formato pivoteable unificado
 */
function transformPivotableData(rawData, context) {
  const { metric, dimension, chartType, metricConfig, dimensionConfig, limit = 10 } = context;
  
  console.log(`[Analytics] 🔄 Transforming pivotable data: ${metric} by ${dimension}`);

  let items = [];
  let labels = [];
  let values = [];

  // Manejar diferentes formatos de respuesta del backend
  if (rawData?.chart?.data) {
    // Respuesta de charts API (formato estándar)
    items = rawData.chart.data.slice(0, limit);
    labels = items.map(item => item.label || 'Sin Etiqueta');
    values = items.map(item => item.value || metricConfig.defaultValue);
    
  } else if (Array.isArray(rawData)) {
    // Respuesta directa de array
    items = rawData.slice(0, limit);
    
    labels = items.map(item => {
      // Extraer nombre usando configuración de dimensión
      const nameField = dimensionConfig.nameField;
      return item[nameField] || 
             item.DESC_GESTOR || item.DESC_CENTRO || item.DESC_PRODUCTO ||
             item.nombre_gestor || item.nombre_centro || item.nombre_producto ||
             item.nombre || item.label || 
             `${dimensionConfig.label} ${item.id || '?'}`;
    });
    
    values = items.map(item => {
      // Extraer valor usando configuración de métrica
      const value = item[metric.toLowerCase()] || 
                   item[`${metric.toLowerCase()}_pct`] ||
                   item.total_contratos || item.margen_neto || item.roe_pct ||
                   item.value || metricConfig.defaultValue;
      return Number(value) || metricConfig.defaultValue;
    });
    
  } else if (rawData && typeof rawData === 'object') {
    // Respuesta de objeto único
    items = [rawData];
    labels = [rawData[dimensionConfig.nameField] || dimensionConfig.label];
    values = [rawData[metric.toLowerCase()] || metricConfig.defaultValue];
    
  } else {
    console.warn('[Analytics] Unexpected data format, using empty data');
    items = [];
    labels = ['No hay datos'];
    values = [0];
  }

  // Generar colores basados en la métrica
  const colors = values.map((_, index) => {
    const baseColor = metricConfig.color;
    // Variaciones de opacity para múltiples elementos
    const opacity = 1 - (index * 0.1);
    return `${baseColor}${Math.floor(opacity * 255).toString(16).padStart(2, '0')}`;
  });

  const transformed = {
    labels,
    datasets: [{
      label: metricConfig.label,
      data: values,
      backgroundColor: colors,
      borderRadius: 4,
      borderWidth: chartType.includes('bar') ? 0 : 2,
      borderColor: metricConfig.color,
    }],
    raw: items,
    meta: {
      type: 'pivotable_chart',
      metric,
      dimension,
      chartType,
      metricLabel: metricConfig.label,
      dimensionLabel: dimensionConfig.label,
      total: items.length,
      showing: Math.min(items.length, limit),
      format: metricConfig.format,
      pivot_enabled: true,
      interactive: true,
      generated_at: new Date().toISOString()
    }
  };

  console.log(`[Analytics] ✅ Pivotable transform complete:`, {
    metric: transformed.meta.metricLabel,
    dimension: transformed.meta.dimensionLabel,
    items: transformed.meta.showing
  });

  return transformed;
}

/**
 * ✅ Genera datos mock para pivoteo cuando falla el backend
 */
function generateMockPivotableChart(metric, dimension, chartType, options = {}) {
  console.log(`[Analytics] 🎭 Generating mock pivotable data: ${metric} by ${dimension}`);
  
  const metricConfig = PIVOTABLE_CONFIG.metrics[metric];
  const dimensionConfig = PIVOTABLE_CONFIG.dimensions[dimension];
  
  // Datos mock basados en la dimensión
  const mockData = {
    gestor: {
      labels: ['Gestor A', 'Gestor B', 'Gestor C', 'Gestor D', 'Gestor E'],
      values: [45, 38, 32, 28, 22]
    },
    centro: {
      labels: ['Madrid', 'Barcelona', 'Valencia', 'Sevilla'],
      values: [35, 25, 18, 12]
    },
    producto: {
      labels: ['Hipotecas', 'Depósitos', 'Fondos'],
      values: [50, 30, 20]
    },
    cliente: {
      labels: ['Cliente Premium', 'Cliente Gold', 'Cliente Silver'],
      values: [65, 45, 25]
    },
    segmento: {
      labels: ['Banca Minorista', 'Banca Privada', 'Empresas'],
      values: [40, 35, 25]
    }
  };

  const mock = mockData[dimension] || mockData.gestor;
  
  // Ajustar valores según la métrica
  const adjustedValues = mock.values.map(v => {
    switch (metric) {
      case 'ROE':
      case 'MARGEN_NETO':
        return v; // Ya son porcentajes
      case 'CONTRATOS':
        return v;
      case 'CLIENTES':
        return Math.floor(v * 0.7);
      case 'INGRESOS':
        return v * 1000;
      case 'INCENTIVOS':
        return v * 500;
      default:
        return v;
    }
  });

  return {
    labels: mock.labels,
    datasets: [{
      label: metricConfig?.label || metric,
      data: adjustedValues,
      backgroundColor: metricConfig?.color || '#22c55e',
      borderRadius: 4,
    }],
    raw: mock.labels.map((label, idx) => ({
      label,
      value: adjustedValues[idx],
      mock: true
    })),
    meta: {
      type: 'pivotable_chart',
      metric,
      dimension,
      chartType,
      metricLabel: metricConfig?.label || metric,
      dimensionLabel: dimensionConfig?.label || dimension,
      total: mock.labels.length,
      showing: mock.labels.length,
      mockData: true,
      note: 'Datos de demostración - Error al cargar datos reales',
      ...options
    }
  };
}


/* =========================================
 * ✅ NUEVAS FUNCIONES PARA DEVIATIONS v11.0
 * ========================================= */

/**
 * ✅ NUEVO: Análisis de desviaciones de margen
 */
async function getMargenDeviations(periodo, options = {}) {
  const { z = 2.0, enhanced = true } = options;
  
  console.log(`[Analytics] 🔍 Fetching margen deviations for period ${periodo}`);
  
  const cacheKey = { periodo, z, enhanced, type: 'margen_deviations' };
  const cached = _getCached("deviations", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached margen deviations`);
    return cached;
  }

  try {
    const result = await deviationsAPI.margen(periodo, { z, enhanced });
    
    const normalized = {
      periodo,
      z,
      enhanced,
      deviations: result.deviations || [],
      stats: result.stats || {},
      threshold: result.threshold || z,
      meta: {
        total: result.deviations?.length || 0,
        source: 'deviations_api',
        type: 'margen'
      }
    };

    _setCached("deviations", cacheKey, normalized, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Margen deviations loaded: ${normalized.deviations.length} items`);
    return normalized;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching margen deviations:`, error.message);
    return {
      periodo,
      z,
      deviations: [],
      meta: { total: 0, error: error.message, type: 'margen' }
    };
  }
}

/**
 * ✅ NUEVO: Análisis de desviaciones de volumen
 */
async function getVolumenDeviations(periodo, options = {}) {
  const { factor = 3.0, enhanced = true } = options;
  
  console.log(`[Analytics] 🔍 Fetching volumen deviations for period ${periodo}`);
  
  const cacheKey = { periodo, factor, enhanced, type: 'volumen_deviations' };
  const cached = _getCached("deviations", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached volumen deviations`);
    return cached;
  }

  try {
    const result = await deviationsAPI.volumen(periodo, { factor, enhanced });
    
    const normalized = {
      periodo,
      factor,
      enhanced,
      deviations: result.deviations || [],
      stats: result.stats || {},
      threshold: result.threshold || factor,
      meta: {
        total: result.deviations?.length || 0,
        source: 'deviations_api',
        type: 'volumen'
      }
    };

    _setCached("deviations", cacheKey, normalized, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Volumen deviations loaded: ${normalized.deviations.length} items`);
    return normalized;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching volumen deviations:`, error.message);
    return {
      periodo,
      factor,
      deviations: [],
      meta: { total: 0, error: error.message, type: 'volumen' }
    };
  }
}

/**
 * ✅ NUEVO: Desviaciones críticas
 */
async function getCriticalDeviations(periodo, umbral = 15.0, options = {}) {
  console.log(`[Analytics] 🔍 Fetching critical deviations for period ${periodo}`);
  
  const cacheKey = { periodo, umbral, type: 'critical_deviations' };
  const cached = _getCached("deviations", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached critical deviations`);
    return cached;
  }

  try {
    const result = await deviationsAPI.critical(periodo, umbral);
    
    const normalized = {
      periodo,
      umbral,
      deviations: result.deviations || [],
      severity: result.severity || 'medium',
      priority: result.priority || [],
      meta: {
        total: result.deviations?.length || 0,
        critical_count: result.critical_count || 0,
        source: 'deviations_api',
        type: 'critical'
      }
    };

    _setCached("deviations", cacheKey, normalized, DEFAULT_TTL_MS);
    
    console.log(`[Analytics] ✅ Critical deviations loaded: ${normalized.deviations.length} items`);
    return normalized;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching critical deviations:`, error.message);
    return {
      periodo,
      umbral,
      deviations: [],
      meta: { total: 0, error: error.message, type: 'critical' }
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA INTEGRATION v11.0
 * ========================================= */

/**
 * ✅ NUEVO: Clasificación y enrutamiento inteligente
 */
async function classifyAndRoute(userMessage, context = {}) {
  console.log(`[Analytics] 🧠 Classifying message: "${userMessage}"`);
  
  try {
    const result = await integrationAPI.classifyAndRoute({
      user_message: userMessage,
      context
    });
    
    console.log(`[Analytics] ✅ Message classified:`, {
      flowType: result.flow_type,
      confidence: result.confidence
    });
    
    return result;
  } catch (error) {
    console.error(`[Analytics] ❌ Error classifying message:`, error.message);
    return {
      flow_type: 'FALLBACK',
      confidence: 0.0,
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Obtener catálogos de queries disponibles
 */
async function getQueryCatalogs() {
  const cacheKey = 'query_catalogs';
  const cached = _getCached(cacheKey, {});
  if (cached) {
    console.log('[Analytics] Using cached query catalogs');
    return cached;
  }

  try {
    const result = await integrationAPI.queryCatalogs();
    
    _setCached(cacheKey, {}, result, 5 * 60 * 1000); // 5 minutos cache
    
    console.log('[Analytics] ✅ Query catalogs loaded:', {
      catalogs: result.available_catalogs?.length || 0,
      engines: result.query_engines?.length || 0
    });
    
    return result;
  } catch (error) {
    console.error('[Analytics] ❌ Error fetching query catalogs:', error.message);
    return {
      available_catalogs: ['basic', 'comparative', 'deviation', 'gestor'],
      query_engines: ['basic', 'comparative', 'deviation', 'gestor'],
      error: error.message
    };
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA REFLECTION/FEEDBACK v11.0
 * ========================================= */

/**
 * ✅ NUEVO: Obtener insights de reflexión
 */
async function getReflectionInsights() {
  const cacheKey = 'reflection_insights';
  const cached = _getCached(cacheKey, {});
  if (cached) {
    console.log('[Analytics] Using cached reflection insights');
    return cached;
  }

  try {
    const result = await reflectionAPI.insights();
    
    _setCached(cacheKey, {}, result, 10 * 60 * 1000); // 10 minutos cache
    
    console.log('[Analytics] ✅ Reflection insights loaded');
    return result;
  } catch (error) {
    console.error('[Analytics] ❌ Error fetching reflection insights:', error.message);
    return {
      insights: [],
      total_users: 0,
      error: error.message
    };
  }
}

/**
 * ✅ NUEVO: Procesar feedback del usuario
 */
async function processFeedback(feedbackData) {
  console.log(`[Analytics] 📝 Processing user feedback`);
  
  try {
    const result = await feedbackAPI.process(feedbackData);
    
    console.log(`[Analytics] ✅ Feedback processed successfully`);
    return result;
  } catch (error) {
    console.error(`[Analytics] ❌ Error processing feedback:`, error.message);
    return {
      status: 'error',
      message: error.message
    };
  }
}

/* =========================================
 * ✅ FUNCIONES AUXILIARES ACTUALIZADAS PARA v11.0
 * ========================================= */

function getColorsForChartType(chartType, dataLength) {
  let colorPalette;
  
  switch (chartType) {
    case 'gestores-ranking':
      colorPalette = DIRECTION_COLORS.gestores;
      break;
    case 'centros-distribution':
      colorPalette = DIRECTION_COLORS.centros;
      break;
    case 'productos-popularity':
      colorPalette = DIRECTION_COLORS.productos;
      break;
    case 'precios-comparison':
      colorPalette = PRODUCT_COLORS;
      break;
    case 'gastos-by-centro':
      // ✅ NUEVO: Colores para gastos
      colorPalette = DIRECTION_COLORS.gastos;
      break;
    case 'summary-dashboard':
      colorPalette = DIRECTION_COLORS.general;
      break;
    default:
      colorPalette = DIRECTION_COLORS.general;
  }
  
  // Extender la paleta si necesitamos más colores
  const colors = [];
  for (let i = 0; i < dataLength; i++) {
    colors.push(colorPalette[i % colorPalette.length]);
  }
  
  return colors;
}

function getDatasetLabel(metric) {
  const labels = {
    'CONTRATOS': 'Contratos',
    'CLIENTES': 'Clientes', 
    'INGRESOS': 'Ingresos (€)',
    'MARGEN': 'Margen (%)',
    'VOLUMEN': 'Volumen',
    'GASTOS': 'Gastos (€)' // ✅ NUEVO
  };
  return labels[metric] || metric;
}

function generateMockDirectionChart(chartType, options = {}) {
  console.log(`[Analytics] 🎭 Generating mock data for ${chartType}`);
  
  const mockData = {
    'gestores-ranking': {
      labels: ['Gestor A', 'Gestor B', 'Gestor C', 'Gestor D', 'Gestor E'],
      data: [45, 38, 32, 28, 22],
      label: 'Contratos'
    },
    'centros-distribution': {
      labels: ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao'],
      data: [35, 25, 18, 12, 10],
      label: 'Distribución'
    },
    'productos-popularity': {
      labels: ['Hipotecas', 'Depósitos', 'Fondos'],
      data: [50, 30, 20],
      label: 'Popularidad'
    },
    'gastos-by-centro': {
      // ✅ NUEVO: Mock para gastos por centro
      labels: ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao'],
      data: [85000, 65000, 45000, 35000, 25000],
      label: 'Gastos (€)'
    },
    'summary-dashboard': {
      labels: ['Gestores', 'Clientes', 'Contratos', 'Productos'],
      data: [30, 85, 216, 3],
      label: 'Resumen'
    }
  };

  const mock = mockData[chartType] || mockData['gestores-ranking'];
  
  return {
    labels: mock.labels,
    datasets: [{
      label: mock.label,
      data: mock.data,
      backgroundColor: getColorsForChartType(chartType, mock.data.length),
      borderRadius: 4,
    }],
    raw: mock.labels.map((label, idx) => ({
      label,
      value: mock.data[idx],
      mock: true
    })),
    meta: {
      type: chartType,
      mockData: true,
      total: mock.data.length,
      showing: mock.data.length,
      note: 'Error loading data - showing mock',
      ...options
    }
  };
}

/* =========================================
 * ✅ GENERADORES DE DATOS MOCK (MANTENIDOS)
 * ========================================= */

function generateMockTopClients(gestorId = null) {
  const mockNames = [
    'CLIENTE PREMIUM SA',
    'INVERSIONES MADRID SL', 
    'GRUPO FINANCIERO BCN',
    'CAPITAL VENTURES SL',
    'CONSULTORA ESTRATÉGICA'
  ];
  
  const mockValues = [45000, 38000, 32000, 28000, 22000];
  
  return {
    labels: mockNames,
    datasets: [{
      label: "Margen (€)",
      data: mockValues,
      backgroundColor: CLIENT_COLORS.slice(0, 5),
      borderRadius: 4,
    }],
    raw: mockNames.map((name, idx) => ({
      NOMBRE_CLIENTE: name,
      margen: mockValues[idx],
      contratos: Math.floor(Math.random() * 5) + 2
    })),
    meta: {
      type: 'top_clients',
      total: 5,
      showing: 5,
      mockData: true,
      gestorId,
      note: 'Datos de demostración - Backend sin datos reales'
    }
  };
}

function generateMockProductMix(gestorId = null) {
  const mockProducts = [
    'Préstamo Hipotecario',
    'Depósito a Plazo Fijo', 
    'Fondo de Inversión',
    'Cuenta Corriente Plus'
  ];
  
  const mockValues = [25, 20, 15, 10];
  const total = mockValues.reduce((sum, v) => sum + v, 0);
  
  return {
    labels: mockProducts,
    datasets: [{
      label: "Contratos",
      data: mockValues,
      backgroundColor: PRODUCT_COLORS.slice(0, 4),
      borderWidth: 2,
      borderColor: '#ffffff',
    }],
    raw: mockProducts.map((product, idx) => ({
      DESC_PRODUCTO: product,
      num_contratos: mockValues[idx]
    })),
    meta: {
      type: 'product_mix',
      total,
      showing: 4,
      percentages: mockValues.map(v => ((v / total) * 100).toFixed(1)),
      mockData: true,
      gestorId,
      note: 'Datos de demostración - Backend sin datos reales'
    }
  };
}

/**
 * ✅ MEJORADO: Genera mock con segmento correcto
 */
function generateMockPriceComparison(gestorId = null, segmentoInfo = null) {
  const mockProducts = ['Préstamo Hipotecario', 'Depósito a Plazo', 'Fondo Inversión'];
  const stdPrices = [1200, 1160, 1180];
  const realPrices = [1185, 1190, 1165];
  
  const tableData = mockProducts.map((product, idx) => {
    const std = stdPrices[idx];
    const real = realPrices[idx];
    const delta_abs = real - std;
    const delta_pct = ((delta_abs / std) * 100);
    const absPct = Math.abs(delta_pct);
    
    return {
      DESC_PRODUCTO: product,
      precio_std: std,
      precio_real: real,
      delta_abs: Number(delta_abs.toFixed(2)),
      delta_pct: Number(delta_pct.toFixed(2)),
      semaforo: absPct <= 2 ? 'Verde' : absPct <= 15 ? 'Amarillo' : 'Rojo'
    };
  });
  
  return {
    labels: mockProducts,
    datasets: [
      {
        label: "Precio Estándar",
        data: stdPrices,
        backgroundColor: "#94a3b8",
        borderRadius: 4,
      },
      {
        label: "Precio Real",
        data: realPrices,
        backgroundColor: tableData.map(r => SEMAPHORE_COLORS[r.semaforo] || SEMAPHORE_COLORS.Gris),
        borderRadius: 4,
      }
    ],
    table: tableData,
    raw: { standard: [], real: [] },
    meta: {
      type: 'price_comparison',
      gestorId,
      showing: 3,
      total: 3,
      mockData: true,
      segmentoId: segmentoInfo?.segmentoId,
      segmentoNombre: segmentoInfo?.segmentoNombre,
      periodo: '2025-10',
      semaforos: { Verde: 2, Amarillo: 1, Rojo: 0 },
      note: `Datos de demostración para ${segmentoInfo?.segmentoNombre || 'Segmento Desconocido'}`
    }
  };
}

/* =========================================
 * ✅ TRANSFORMACIONES ESPECÍFICAS MANTENIDAS
 * ========================================= */

function transformTopClients(clientsData = [], options = {}) {
  const { limit = 5, mockMetric = true, gestorId = null } = options;
  
  if (!Array.isArray(clientsData) || clientsData.length === 0) {
    console.warn('[Analytics] No clients data available, using mock data');
    return generateMockTopClients(gestorId);
  }
  
  const withMetrics = clientsData.map((client, index) => ({
    ...client,
    margen: mockMetric ? Math.floor(Math.random() * 40000) + 15000 : (client.margen || 0),
    contratos: mockMetric ? Math.floor(Math.random() * 8) + 2 : (client.contratos || 0),
  }));

  const sorted = withMetrics
    .sort((a, b) => (b.margen || 0) - (a.margen || 0))
    .slice(0, limit);

  if (sorted.length === 0 || sorted.every(c => (c.margen || 0) === 0)) {
    console.warn('[Analytics] No meaningful client data after processing, using mock data');
    return generateMockTopClients(gestorId);
  }

  return {
    labels: sorted.map(c => {
      const name = c.NOMBRE_CLIENTE || c.nombre || c.name || 'Cliente';
      return name.split(' ').slice(0, 2).join(' ');
    }),
    datasets: [{
      label: "Margen (€)",
      data: sorted.map(c => c.margen || 0),
      backgroundColor: CLIENT_COLORS.slice(0, sorted.length),
      borderRadius: 4,
    }],
    raw: sorted,
    meta: {
      type: 'top_clients',
      total: clientsData.length,
      showing: sorted.length,
      gestorId,
      mockData: mockMetric
    }
  };
}

function transformProductMix(productsData = [], options = {}) {
  const { gestorId = null } = options;
  
  if (!Array.isArray(productsData) || productsData.length === 0) {
    console.warn('[Analytics] No products data available, using mock data');
    return generateMockProductMix(gestorId);
  }

  const sorted = productsData.sort((a, b) => (b.num_contratos || 0) - (a.num_contratos || 0));
  const total = sorted.reduce((sum, p) => sum + (p.num_contratos || 0), 0);

  if (total === 0) {
    console.warn('[Analytics] No contracts found in products data, using mock data');
    return generateMockProductMix(gestorId);
  }

  return {
    labels: sorted.map(p => p.DESC_PRODUCTO || p.producto || p.name || 'Producto'),
    datasets: [{
      label: "Contratos",
      data: sorted.map(p => p.num_contratos || 0),
      backgroundColor: PRODUCT_COLORS.slice(0, sorted.length),
      borderWidth: 2,
      borderColor: '#ffffff',
    }],
    raw: sorted,
    meta: {
      type: 'product_mix',
      total,
      showing: sorted.length,
      percentages: sorted.map(p => total > 0 ? ((p.num_contratos || 0) / total * 100).toFixed(1) : '0'),
      gestorId
    }
  };
}

/**
 * ✅ FUNCIÓN COMPLETAMENTE REESCRITA: transformPriceComparison (mantenida)
 */
function transformPriceComparison(data = {}, options = {}) {
  const { gestorId, segmentoInfo, periodo = '2025-10' } = options;
  
  console.log(`[Analytics] transformPriceComparison called for gestor ${gestorId}`);
  console.log(`[Analytics] Segment info:`, segmentoInfo);
  console.log(`[Analytics] Raw data lengths - standard: ${data.standard?.length || 0}, real: ${data.real?.length || 0}`);
  
  if (!data.standard && !data.real) {
    console.warn('[Analytics] No price data available, using mock data');
    return generateMockPriceComparison(gestorId, segmentoInfo);
  }
  
  const standard = Array.isArray(data.standard) ? data.standard : [];
  const real = Array.isArray(data.real) ? data.real : [];

  if (standard.length === 0 && real.length === 0) {
    console.warn('[Analytics] No valid price data arrays, using mock data');
    return generateMockPriceComparison(gestorId, segmentoInfo);
  }

  // ✅ FILTRAR DATOS POR SEGMENTO
  let filteredStandard = standard;
  let filteredReal = real;
  
  if (segmentoInfo?.segmentoId) {
    filteredStandard = standard.filter(item => {
      const itemSegmentId = item.SEGMENTO_ID || item.segmento_id;
      return itemSegmentId === segmentoInfo.segmentoId;
    });
    
    filteredReal = real.filter(item => {
      const itemSegmentId = item.SEGMENTO_ID || item.segmento_id;
      return itemSegmentId === segmentoInfo.segmentoId;
    });
    
    console.log(`[Analytics] After segment filtering (${segmentoInfo.segmentoId}):`, {
      standard: filteredStandard.length,
      real: filteredReal.length
    });
  }

  // Filtrar precios reales por período más reciente
  const realByProduct = {};
  filteredReal.forEach(item => {
    const productId = item.PRODUCTO_ID;
    const currentPeriod = item.FECHA_CALCULO || '';
    
    if (!realByProduct[productId] || currentPeriod >= (realByProduct[productId].FECHA_CALCULO || '')) {
      realByProduct[productId] = item;
    }
  });

  // Crear estructura de datos combinando standard y real
  const productData = [];
  
  filteredStandard.forEach(stdItem => {
    const productId = stdItem.PRODUCTO_ID;
    const realItem = realByProduct[productId];
    
    if (realItem) {
      const stdPrice = Math.abs(stdItem.PRECIO_MANTENIMIENTO || 0);
      const realPrice = Math.abs(realItem.PRECIO_MANTENIMIENTO_REAL || 0);
      
      if (stdPrice > 0 && realPrice > 0) {
        const deltaAbs = realPrice - stdPrice;
        const deltaPct = (deltaAbs / stdPrice) * 100;
        const absPct = Math.abs(deltaPct);
        
        productData.push({
          PRODUCTO_ID: productId,
          DESC_PRODUCTO: stdItem.DESC_PRODUCTO || realItem.DESC_PRODUCTO || 'Producto',
          SEGMENTO_ID: stdItem.SEGMENTO_ID,
          DESC_SEGMENTO: stdItem.DESC_SEGMENTO,
          precio_std: stdPrice,
          precio_real: realPrice,
          delta_abs: Number(deltaAbs.toFixed(2)),
          delta_pct: Number(deltaPct.toFixed(2)),
          semaforo: absPct <= 2 ? 'Verde' : absPct <= 15 ? 'Amarillo' : 'Rojo',
          contratos_base: realItem.NUM_CONTRATOS_BASE || 0,
          fecha_calculo: realItem.FECHA_CALCULO
        });
      }
    }
  });

  console.log(`[Analytics] Final product data length: ${productData.length}`);

  // ✅ VALIDACIÓN: Si no hay productos después del filtrado, usar mock
  if (productData.length === 0) {
    console.warn('[Analytics] No complete product data after processing, using mock data');
    return generateMockPriceComparison(gestorId, segmentoInfo);
  }

  // Ordenar por desviación absoluta (más críticos primero)
  const sortedData = productData.sort((a, b) => Math.abs(b.delta_pct) - Math.abs(a.delta_pct));

  // Preparar labels más cortos
  const labels = sortedData.map(item => {
    let label = item.DESC_PRODUCTO;
    return label
      .replace('Préstamo Hipotecario', 'Hipotecario')
      .replace('Depósito a Plazo Fijo en Euros', 'Depósito PF')
      .replace('Fondo Banca March', 'Fondos BM');
  });

  return {
    labels,
    datasets: [
      {
        label: "Precio Estándar",
        data: sortedData.map(item => item.precio_std),
        backgroundColor: "rgba(25, 124, 99, 1)",
        borderColor: "rgba(25, 124, 99, 1)",
        borderWidth: 2,
        borderRadius: 4,
      },
      {
        label: "Precio Real",
        data: sortedData.map(item => item.precio_real),
        backgroundColor: "rgba(20, 70, 50, 1)",
        borderColor: "rgba(20, 70, 50, 1)",
        borderWidth: 2,
        borderRadius: 4,
      }
    ],
    table: sortedData,
    raw: data,
    meta: {
      type: 'price_comparison',
      gestorId,
      showing: sortedData.length,
      total: productData.length,
      segmentoId: segmentoInfo?.segmentoId,
      segmentoNombre: segmentoInfo?.segmentoNombre,
      periodo,
      semaforos: sortedData.reduce((acc, item) => {
        acc[item.semaforo] = (acc[item.semaforo] || 0) + 1;
        return acc;
      }, { Verde: 0, Amarillo: 0, Rojo: 0, Gris: 0 }),
      note: `Comparativa de precios para segmento ${segmentoInfo?.segmentoNombre || 'Desconocido'}`
    }
  };
}

/* =========================================
 * Normalizaciones EXISTENTES - MANTENIDAS
 * ========================================= */

function normalizeVarianceBridge(apiData = {}) {
  const scope = apiData.scope || DEFAULTS.scope;
  const id = apiData.id ?? null;
  const periodo = apiData.periodo || "";
  const vs = apiData.vs || DEFAULTS.vs;
  const rows = Array.isArray(apiData.bridge) ? apiData.bridge : [];

  const ordered = [
    ...KNOWN_DRIVERS
      .map((d) => rows.find((r) => (r.driver || "").toLowerCase() === d))
      .filter(Boolean),
    ...rows.filter(
      (r) => !KNOWN_DRIVERS.includes((r.driver || "").toLowerCase())
    ),
  ];

  const positives = [];
  const negatives = [];
  let totalImpact = 0;

  const byDriver = ordered.map((r) => {
    const driver = String(r.driver || "").toLowerCase();
    const impacto = Number(r.impacto || 0);
    const semaforo = r.semaforo || (impacto === 0 ? "Verde" : impacto > 0 ? "Rojo" : "Amarillo");
    totalImpact += impacto;
    if (impacto >= 0) positives.push({ driver, impacto, semaforo });
    else negatives.push({ driver, impacto, semaforo });
    return { driver, impacto, semaforo };
  });

  const countBySemaphore = byDriver.reduce(
    (acc, { semaforo }) => {
      acc[semaforo] = (acc[semaforo] || 0) + 1;
      return acc;
    },
    { Verde: 0, Amarillo: 0, Rojo: 0 }
  );

  const absSum = byDriver.reduce((acc, { impacto }) => acc + Math.abs(impacto), 0) || 1;
  const withContribution = byDriver.map((r) => ({
    ...r,
    pct_contrib: Number(((Math.abs(r.impacto) / absSum) * 100).toFixed(2)),
  }));

  return {
    scope,
    id,
    periodo,
    vs,
    totalImpact,
    drivers: withContribution,
    positives,
    negatives,
    semaphores: countBySemaphore,
    raw: apiData,
  };
}

/* =========================================
 * Transformaciones para gráficos EXISTENTES
 * ========================================= */

function toBarChartDataset(nb) {
  const labels = nb.drivers.map((d) => d.driver);
  const values = nb.drivers.map((d) => d.impacto);
  const colors = nb.drivers.map((d) => SEMAPHORE_COLORS[d.semaforo] || SEMAPHORE_COLORS.Gris);

  return {
    labels,
    datasets: [
      {
        label: "Impacto",
        data: values,
        backgroundColor: colors,
      },
    ],
    meta: {
      totalImpact: nb.totalImpact,
      periodo: nb.periodo,
      vs: nb.vs,
      scope: nb.scope,
      id: nb.id,
    },
  };
}

function toSemaphoreDonutDataset(nb) {
  const labels = ["Verde", "Amarillo", "Rojo"];
  const data = labels.map((l) => nb.semaphores[l] || 0);
  const backgroundColor = labels.map((l) => SEMAPHORE_COLORS[l] || SEMAPHORE_COLORS.Gris);
  return {
    labels,
    datasets: [
      {
        label: "Alertas",
        data,
        backgroundColor,
      },
    ],
  };
}

function toTableRows(nb) {
  return nb.drivers.map((d, idx) => ({
    id: idx + 1,
    driver: d.driver,
    impacto: d.impacto,
    semaforo: d.semaforo,
    pct_contrib: d.pct_contrib,
    color: SEMAPHORE_COLORS[d.semaforo] || SEMAPHORE_COLORS.Gris,
  }));
}

/* =========================================
 * Llamadas de alto nivel EXISTENTES
 * ========================================= */

async function fetchVariance(params, cfg) {
  const clean = validateVarianceParams(params || {});
  return analyticsAPI.variance(clean, cfg);
}

async function getVarianceBridge(params, { ttlMs = DEFAULT_TTL_MS, cfg } = {}) {
  const clean = validateVarianceParams(params || {});
  const cached = _getCached("variance", clean);
  if (cached) return cached;

  const data = await analyticsAPI.variance(clean, cfg);
  const normalized = normalizeVarianceBridge(data);
  _setCached("variance", clean, normalized, ttlMs);
  return normalized;
}

async function getVarianceChartData(params, opts = {}) {
  const nb = await getVarianceBridge(params, opts);
  return {
    bar: toBarChartDataset(nb),
    donut: toSemaphoreDonutDataset(nb),
    table: toTableRows(nb),
    meta: {
      periodo: nb.periodo,
      vs: nb.vs,
      totalImpact: nb.totalImpact,
      scope: nb.scope,
      id: nb.id,
    },
  };
}

async function createServerChartFromBridge(params, { chartType = "horizontal_bar", cfg } = {}) {
  const nb = await getVarianceBridge(params, { cfg });
  const data = nb.drivers.map((d) => ({
    driver: d.driver,
    impacto: d.impacto,
    semaforo: d.semaforo,
    pct_contrib: d.pct_contrib,
  }));

  const config = {
    type: chartType,
    x: "impacto",
    y: "driver",
    colorBy: "semaforo",
    palette: SEMAPHORE_COLORS,
    title: `Variance (${nb.scope}${nb.id ? `:${nb.id}` : ""}) — ${nb.periodo} vs ${nb.vs}`,
    valueFormat: "0,0.00",
  };

  const res = await chartsAPI.fromData(data, config, cfg);
  return res;
}

/* =========================================
 * ✅ FUNCIONES DE ALTO NIVEL COMPLETAMENTE REESCRITAS
 * ========================================= */

async function getTopClientsChartData(gestorId, options = {}) {
  const cacheKey = { gestorId, options };
  const cached = _getCached("top_clients", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached top clients data for gestor ${gestorId}`);
    return cached;
  }

  try {
    console.log(`[Analytics] Fetching top clients for gestor ${gestorId}`);
    
    const numericGestorId = parseInt(gestorId, 10);
    if (isNaN(numericGestorId)) {
      console.warn(`[Analytics] Invalid gestorId: ${gestorId}, using mock data`);
      return generateMockTopClients(gestorId);
    }

    const clientsData = await basicAPI.clientesByGestor(numericGestorId);
    console.log(`[Analytics] Retrieved ${clientsData?.length || 0} clients from API`);
    
    const result = transformTopClients(clientsData, { ...options, gestorId });
    
    if (!result.meta?.mockData) {
      _setCached("top_clients", cacheKey, result, DEFAULT_TTL_MS);
    }
    
    return result;
  } catch (error) {
    console.warn('[Analytics] Error fetching top clients:', error.message);
    return generateMockTopClients(gestorId);
  }
}

async function getProductMixChartData(gestorId, options = {}) {
  const cacheKey = { gestorId, options };
  const cached = _getCached("product_mix", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached product mix data for gestor ${gestorId}`);
    return cached;
  }

  try {
    console.log(`[Analytics] Fetching product mix for gestor ${gestorId}`);
    
    const numericGestorId = parseInt(gestorId, 10);
    if (isNaN(numericGestorId)) {
      console.warn(`[Analytics] Invalid gestorId: ${gestorId}, using mock data`);
      return generateMockProductMix(gestorId);
    }

    const productsData = await basicAPI.productosByGestor(numericGestorId);
    console.log(`[Analytics] Retrieved ${productsData?.length || 0} products from API`);
    
    const result = transformProductMix(productsData, { ...options, gestorId });
    
    if (!result.meta?.mockData) {
      _setCached("product_mix", cacheKey, result, DEFAULT_TTL_MS);
    }
    
    return result;
  } catch (error) {
    console.warn('[Analytics] Error fetching product mix:', error.message);
    return generateMockProductMix(gestorId);
  }
}

/**
 * ✅ FUNCIÓN COMPLETAMENTE REESCRITA: getPriceComparisonChartData (AHORA ASYNC) - MANTENIDA
 */
async function getPriceComparisonChartData(params = {}, options = {}) {
  const { gestorId, periodo, productoId } = params;
  
  console.log(`[Analytics] === getPriceComparisonChartData START ===`);
  console.log(`[Analytics] Params:`, { gestorId, periodo, productoId });
  
  // ✅ PASO 2: Obtener segmento del gestor de forma ASYNC
  const segmentoInfo = await getSegmentForGestorSafe(gestorId);
  console.log(`[Analytics] Segment info for gestor ${gestorId}:`, segmentoInfo);
  
  try {
    // ✅ PASO 3: Preparar parámetros para la API
    const cleanParams = {};
    
    if (gestorId) {
      const numericGestorId = parseInt(gestorId, 10);
      if (!isNaN(numericGestorId)) {
        cleanParams.gestorId = numericGestorId;
      }
    }
    
    if (periodo) {
      cleanParams.periodo = String(periodo);
    }
    
    if (productoId) {
      cleanParams.productoId = productoId;
    }

    if (Object.keys(cleanParams).length === 0) {
      console.warn('[Analytics] No valid parameters for price comparison, using mock data');
      return generateMockPriceComparison(gestorId, segmentoInfo);
    }

    console.log(`[Analytics] API call params:`, cleanParams);

    // ✅ PASO 4: Llamada al API
    const priceData = await dataQueriesAPI.pricesComparison(cleanParams);
    console.log('[Analytics] Raw API response:', {
      standard: priceData?.standard?.length || 0,
      real: priceData?.real?.length || 0
    });

    // ✅ PASO 5: Transformar datos (incluye filtrado automático)
    const result = transformPriceComparison(priceData, { 
      gestorId, 
      segmentoInfo,
      periodo,
      ...options 
    });
    
    console.log(`[Analytics] === getPriceComparisonChartData END ===`);
    console.log(`[Analytics] Final result meta:`, result.meta);
    
    return result;
    
  } catch (error) {
    console.error('[Analytics] Error fetching price comparison:', error.message);
    return generateMockPriceComparison(gestorId, segmentoInfo);
  }
}

/**
 * ✅ FUNCIÓN COMPLETAMENTE REESCRITA: getPriceComparisonBySegment (AHORA ASYNC) - MANTENIDA
 */
async function getPriceComparisonBySegment(params = {}, options = {}) {
  const { gestorId, periodo } = params;
  
  console.log(`[Analytics] === getPriceComparisonBySegment START ===`);
  console.log(`[Analytics] Params:`, { gestorId, periodo });
  
  // ✅ Obtener segmento del gestor de forma ASYNC
  const segmentoInfo = await getSegmentForGestorSafe(gestorId);
  console.log(`[Analytics] Segment info for gestor ${gestorId}:`, segmentoInfo);
  
  // ✅ Validación de parámetros
  if (!periodo) {
    throw new Error('Parametro "periodo" es requerido');
  }

  try {
    // ✅ Preparar parámetros para la API
    const apiParams = {
      segmento_id: segmentoInfo.segmentoId,
      periodo
    };

    console.log(`[Analytics] API call params:`, apiParams);

    // ✅ Llamada al nuevo endpoint específico
    const rawData = await dataQueriesAPI.pricesComparisonBySegment(apiParams.segmento_id, apiParams.periodo, options);
    console.log('[Analytics] Raw API response:', {
      standard: rawData?.standard?.length || 0,
      real: rawData?.real?.length || 0
    });

    // ✅ Transformar datos (reutiliza la función existente)
    const result = transformPriceComparison(rawData, { 
      gestorId, 
      segmentoInfo,
      periodo,
      ...options 
    });
    
    console.log(`[Analytics] === getPriceComparisonBySegment END ===`);
    console.log(`[Analytics] Final result meta:`, result.meta);
    
    return result;
    
  } catch (error) {
    console.error('[Analytics] Error fetching price comparison by segment:', error.message);
    return generateMockPriceComparison(gestorId, segmentoInfo);
  }
}

/* =========================================
 * Analítica auxiliar EXISTENTE - MANTENIDA
 * ========================================= */

async function getPricesComparison({ gestor_id, producto_id, periodo } = {}, cfg) {
  const payload = {};
  
  if (gestor_id) {
    const numericId = parseInt(gestor_id, 10);
    if (!isNaN(numericId)) {
      payload.gestorId = numericId;
    }
  }
  
  if (producto_id) {
    payload.productoId = producto_id;
  }
  
  if (periodo) {
    payload.periodo = String(periodo);
  }

  const data = await dataQueriesAPI.pricesComparison(payload, cfg);
  const transformed = transformPriceComparison(data, { gestorId: gestor_id });
  
  return {
    table: transformed.table || [],
    bar: {
      labels: transformed.labels || [],
      datasets: [{
        label: "Δ Precio (real - std)",
        data: (transformed.table || []).map(r => r.delta_abs || 0),
        backgroundColor: (transformed.table || []).map(r => {
          const delta = r.delta_abs || 0;
          return delta >= 0 ? SEMAPHORE_COLORS.Rojo : SEMAPHORE_COLORS.Verde;
        }),
      }],
    },
    raw: data,
    meta: transformed.meta || {},
  };
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA GASTOS BY CENTRO v11.0
 * ========================================= */

/**
 * ✅ NUEVO: Obtener gastos por centro usando endpoint real
 */
async function getGastosByCentroChartData(fecha, options = {}) {
  const { chart_type = 'stacked_bar' } = options;
  
  console.log(`[Analytics] 📊 Fetching gastos by centro for fecha: ${fecha}`);
  
  const cacheKey = { fecha, chart_type, type: 'gastos_by_centro' };
  const cached = _getCached("gastos_chart", cacheKey);
  if (cached) {
    console.log(`[Analytics] Using cached gastos by centro data`);
    return cached;
  }

  try {
    // ✅ Usar endpoint real de gastos
    const result = await chartsAPI.gastosByCentro({ fecha, chartType: chart_type });
    
    console.log(`[Analytics] ✅ Gastos by centro data received:`, {
      hasChart: !!result.chart,
      dataLength: result.chart?.data?.length || 0
    });

    // Transformar a formato uniforme
    const transformed = transformBackendChartData(result, 'gastos-by-centro');
    
    _setCached("gastos_chart", cacheKey, transformed, DEFAULT_TTL_MS);
    
    return transformed;
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error fetching gastos by centro:`, error.message);
    
    // Fallback con datos mock
    return generateMockDirectionChart('gastos-by-centro', { fecha, chart_type });
  }
}

/* =========================================
 * ✅ NUEVAS FUNCIONES PARA QUICK CHARTS v11.0
 * ========================================= */

/**
 * ✅ NUEVO: Crear gráfico rápido predefinido
 */
async function createQuickChart(queryMethod, options = {}) {
  const { chartType = 'bar', kwargs = {} } = options;
  
  console.log(`[Analytics] ⚡ Creating quick chart: ${queryMethod}`);
  
  try {
    const result = await chartsAPI.quick({ 
      queryMethod, 
      chartType, 
      kwargs 
    });
    
    console.log(`[Analytics] ✅ Quick chart created successfully`);
    
    return transformBackendChartData(result, 'quick_chart');
    
  } catch (error) {
    console.error(`[Analytics] ❌ Error creating quick chart:`, error.message);
    throw error;
  }
}

/**
 * ✅ NUEVO: Obtener queries disponibles para gráficos rápidos
 */
async function getAvailableQuickQueries() {
  const cacheKey = 'available_quick_queries';
  const cached = _getCached(cacheKey, {});
  if (cached) {
    console.log('[Analytics] Using cached available quick queries');
    return cached;
  }

  try {
    const result = await chartsAPI.availableQueries();
    
    _setCached(cacheKey, {}, result, 5 * 60 * 1000); // 5 minutos cache
    
    console.log('[Analytics] ✅ Available quick queries loaded:', result.length || 0);
    return result;
    
  } catch (error) {
    console.error('[Analytics] ❌ Error fetching available quick queries:', error.message);
    
    // Fallback queries
    return [
      'gestores-ranking',
      'centros-distribution', 
      'productos-popularity',
      'precios-comparison',
      'gastos-by-centro'
    ];
  }
}

/* =========================================
 * ✅ EXPORTS COMPLETOS Y ACTUALIZADOS v11.0
 * ========================================= */

const analyticsService = {
  // ✅ FUNCIONES PRINCIPALES PARA DASHBOARD DIRECCIÓN v11.0
  getDirectionChartData,
  transformBackendChartData,
  pivotChart,
  getChartMeta,

  // ✅ NUEVA FUNCIÓN OPTIMIZADA
  getUnifiedKPIData,

  // ✅ NUEVAS FUNCIONES ANALYTICS v11.0 - MÉTRICAS FINANCIERAS
  getCentroMetricas,
  getCentroGestoresMetricas,
  getSegmentoMetricas,
  getGestorMetricasCompletas,
  getGestorClientesMetricas,
  getClienteMetricas,
  getClienteContratosMetricas,
  getContratoDetalleCompleto,

  // ✅ NUEVAS FUNCIONES KPIs v11.0 - FINANCIEROS ESPECÍFICOS
  getCentroKPIsFinancieros,
  getGestorKPIsFinancieros,
  getGestorROE,
  getGestorEficiencia,
  getCentroMargen,
  getCentroBonusTotal,

  // ✅ NUEVAS FUNCIONES INCENTIVES v11.0 - DETALLADOS
  getIncentivesCentroTotal,
  getIncentivesGestorDetalle,

  // ✅ NUEVAS FUNCIONES DASHBOARDS v11.0 - ESPECÍFICOS
  getDashboardGestorSummary,
  getDashboardGestorEvolution,
  getDashboardGestorProductos,
  getDashboardGestorAlertas,
  getDashboardGestorComparative,
  getDashboardIncentivosSummary,
  getDashboardIncentivosTendencia,
  getDashboardComparativeSummary,
  getDashboardMatrizSegmentos,

  // ✅ NUEVAS FUNCIONES CATALOGS v11.0 - PERÍODOS CON MÉTRICAS
  getPeriodMetricas,
  getComparePeriods,

  // ✅ NUEVAS FUNCIONES SQL v11.0
  executeDynamicSQL,
  validateSQL,

  // ✅ NUEVAS FUNCIONES DEVIATIONS v11.0
  getMargenDeviations,
  getVolumenDeviations,
  getCriticalDeviations,

  // ✅ NUEVAS FUNCIONES INTEGRATION v11.0
  classifyAndRoute,
  getQueryCatalogs,

  // ✅ NUEVAS FUNCIONES REFLECTION/FEEDBACK v11.0
  getReflectionInsights,
  processFeedback,

  // ✅ NUEVAS FUNCIONES GASTOS v11.0
  getGastosByCentroChartData,

  // ✅ NUEVAS FUNCIONES QUICK CHARTS v11.0
  createQuickChart,
  getAvailableQuickQueries,

  // llamadas crudas / normalizadas EXISTENTES
  fetchVariance,
  getVarianceBridge,
  getVarianceChartData,
  createServerChartFromBridge,

  // ✅ FUNCIONES PRINCIPALES CORREGIDAS (ASYNC)
  getTopClientsChartData,
  getProductMixChartData,
  getPriceComparisonChartData,
  getPriceComparisonBySegment,

  // ✅ FUNCIONES DE SEGMENTACIÓN DINÁMICAS
  getSegmentInfo,
  getSegmentForGestor,
  getSegmentForGestorSafe,
  filterDataBySegment,

  // auxiliares mantenidas
  getPricesComparison,

  // transformaciones
  transformTopClients,
  transformProductMix,
  transformPriceComparison,

  // generadores mock
  generateMockTopClients,
  generateMockProductMix,
  generateMockPriceComparison,
  generateMockDirectionChart,

  // normalizaciones
  normalizeVarianceBridge,
  toBarChartDataset,
  toSemaphoreDonutDataset,
  toTableRows,

  // ✅ CACHE OPTIMIZADO
  clearAnalyticsCache,
  _clearCacheForPeriod,
  _clearCacheForGestor,

  // ✅ NUEVAS FUNCIONES PARA PIVOTEO DINÁMICO v11.0
  getPivotableChartData,
  transformPivotableData,
  generateMockPivotableChart,
  validatePivotCombination,
  
  // configuración de pivoteo
  PIVOTABLE_CONFIG,


  // constantes
  SCOPE,
  VS,
  SEMAPHORE_COLORS,
  PRODUCT_COLORS,
  CLIENT_COLORS,
  DIRECTION_COLORS,
};

export default analyticsService;
export {
  analyticsService,
  
  // ✅ NUEVAS EXPORTACIONES v11.0 PARA DASHBOARD DIRECCIÓN
  getDirectionChartData,
  transformBackendChartData,
  pivotChart,
  getChartMeta,

  // ✅ NUEVAS EXPORTACIONES ANALYTICS v11.0 - MÉTRICAS FINANCIERAS
  getCentroMetricas,
  getCentroGestoresMetricas,
  getSegmentoMetricas,
  getGestorMetricasCompletas,
  getGestorClientesMetricas,
  getClienteMetricas,
  getClienteContratosMetricas,
  getContratoDetalleCompleto,

  // ✅ NUEVAS EXPORTACIONES KPIs v11.0 - FINANCIEROS ESPECÍFICOS
  getCentroKPIsFinancieros,
  getGestorKPIsFinancieros,
  getGestorROE,
  getGestorEficiencia,
  getCentroMargen,
  getCentroBonusTotal,

  // ✅ NUEVAS EXPORTACIONES INCENTIVES v11.0 - DETALLADOS
  getIncentivesCentroTotal,
  getIncentivesGestorDetalle,

  // ✅ NUEVAS EXPORTACIONES DASHBOARDS v11.0 - ESPECÍFICOS
  getDashboardGestorSummary,
  getDashboardGestorEvolution,
  getDashboardGestorProductos,
  getDashboardGestorAlertas,
  getDashboardGestorComparative,
  getDashboardIncentivosSummary,
  getDashboardIncentivosTendencia,
  getDashboardComparativeSummary,
  getDashboardMatrizSegmentos,

  // ✅ NUEVAS EXPORTACIONES CATALOGS v11.0 - PERÍODOS CON MÉTRICAS
  getPeriodMetricas,
  getComparePeriods,

  // ✅ NUEVAS EXPORTACIONES SQL v11.0
  executeDynamicSQL,
  validateSQL,
  
  // ✅ NUEVAS EXPORTACIONES DEVIATIONS v11.0
  getMargenDeviations,
  getVolumenDeviations,
  getCriticalDeviations,

  // ✅ NUEVAS EXPORTACIONES INTEGRATION v11.0
  classifyAndRoute,
  getQueryCatalogs,

  // ✅ NUEVAS EXPORTACIONES REFLECTION/FEEDBACK v11.0
  getReflectionInsights,
  processFeedback,

  // ✅ NUEVAS EXPORTACIONES GASTOS v11.0
  getGastosByCentroChartData,

  // ✅ NUEVAS EXPORTACIONES QUICK CHARTS v11.0
  createQuickChart,
  getAvailableQuickQueries,

  // ✅ NUEVAS EXPORTACIONES PARA PIVOTEO DINÁMICO v11.0
  getPivotableChartData,
  transformPivotableData,
  generateMockPivotableChart,
  validatePivotCombination,
  PIVOTABLE_CONFIG,

  
  // ✅ OPTIMIZACIÓN NUEVA
  getUnifiedKPIData,
  
  // EXISTENTES MANTENIDAS
  fetchVariance,
  getVarianceBridge,
  getVarianceChartData,
  createServerChartFromBridge,
  getPricesComparison,
  getTopClientsChartData,
  getProductMixChartData,
  getPriceComparisonChartData,
  getPriceComparisonBySegment,
  getSegmentInfo,
  getSegmentForGestor,
  getSegmentForGestorSafe,
  filterDataBySegment,
  transformTopClients,
  transformProductMix,
  transformPriceComparison,
  normalizeVarianceBridge,
  toBarChartDataset,
  toSemaphoreDonutDataset,
  toTableRows,
  clearAnalyticsCache,
  generateMockDirectionChart,
  SCOPE,
  VS,
  SEMAPHORE_COLORS,
  PRODUCT_COLORS,
  CLIENT_COLORS,
  DIRECTION_COLORS,
};
