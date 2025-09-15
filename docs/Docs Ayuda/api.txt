// frontend/src/services/api.js
/* eslint-disable no-console */

/**
 * CDG Frontend API Client v11.0 (Chat Agent v10.0 + CDG Agent v6.0)
 * --------------------------------------------------------------------
 * - Perfect Integration con backend main.py v11.0
 * - Chat Agent v10.0: Clasificación inteligente + 6 catálogos
 * - CDG Agent v6.0: Análisis complejos especializados
 * - Desenvelope automático: devuelve { data, meta, ts } por defecto
 * - Retries con backoff para 429/502/503/504
 * - Cancelación de requests (AbortController)
 * - WebSocket optimizado para Chat Agent v10.0
 * - SDK completo con TODOS los endpoints del backend
 * - ✅ ACTUALIZADO: +40 nuevos endpoints añadidos
 */

import axios from "axios";

/* ============================
 * Configuración base
 * ============================ */

const BASE_URL =
  process.env.REACT_APP_API_BASE_URL?.replace(/\/+$/, "") ||
  `${window.location.protocol}//${window.location.hostname}:8000`;

const DEFAULT_TIMEOUT =
  Number(process.env.REACT_APP_API_TIMEOUT) > 0
    ? Number(process.env.REACT_APP_API_TIMEOUT)
    : 30000; // 30s para análisis complejos

const JSON_HEADERS = {
  "Content-Type": "application/json",
  Accept: "application/json",
};

// Helper: construir qs limpio
const buildQuery = (params = {}) => {
  const esc = encodeURIComponent;
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `${esc(k)}=${esc(v)}`)
    .join("&");
  return qs ? `?${qs}` : "";
};

// Error normalizado para el front
class ApiClientError extends Error {
  constructor(message, { status = 0, code = 0, detail = null } = {}) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code || status;
    this.detail = detail;
  }
}

/* ============================
 * Axios instance + interceptors
 * ============================ */

const instance = axios.create({
  baseURL: BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: JSON_HEADERS,
  withCredentials: false,
});

// Exponential backoff
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shouldRetry = (error) => {
  if (!error || !error.response) return false;
  const { status } = error.response;
  return [429, 502, 503, 504].includes(status);
};

// Interceptor de respuesta: desenvelope + retry
instance.interceptors.response.use(
  (res) => {
    const payload = res.data;
    if (payload && typeof payload === "object" && "status" in payload) {
      if (payload.status !== "success") {
        throw new ApiClientError(payload.message || "Error API", {
          status: res.status,
          code: payload.code || res.status,
          detail: payload,
        });
      }
      return {
        data: payload.data,
        meta: payload.meta || null,
        ts: payload.timestamp || null,
        raw: payload,
      };
    }
    return { data: payload, meta: null, ts: null, raw: payload };
  },
  async (error) => {
    const config = error.config || {};
    config.__retryCount = config.__retryCount || 0;

    if (shouldRetry(error) && config.__retryCount < 3) {
      config.__retryCount += 1;
      const backoff = 400 * 2 ** (config.__retryCount - 1);
      await sleep(backoff);
      return instance(config);
    }

    const status = error.response?.status || 0;
    const backend = error.response?.data;
    const messageFromBackend =
      backend?.message ||
      backend?.detail ||
      backend?.error ||
      error.message ||
      "Error de red";

    throw new ApiClientError(messageFromBackend, {
      status,
      code: backend?.code || status,
      detail: backend || null,
    });
  }
);

/* ============================
 * Core HTTP helpers
 * ============================ */

const withAbort = (config = {}) => {
  if (config.signal) return config;
  const controller = new AbortController();
  return { ...config, signal: controller.signal, __controller: controller };
};

const http = {
  get: (url, { params, ...cfg } = {}) =>
    instance.get(`${url}${buildQuery(params)}`, withAbort(cfg)),
  post: (url, body = {}, cfg = {}) =>
    instance.post(url, body, withAbort(cfg)),
  put: (url, body = {}, cfg = {}) => instance.put(url, body, withAbort(cfg)),
  del: (url, cfg = {}) => instance.delete(url, withAbort(cfg)),
  raw: instance,
  baseURL: BASE_URL,
};

/* ============================
 * Helpers utilitarios
 * ============================ */

const unwrap = async (promise, { returnMeta = false } = {}) => {
  const { data, meta } = await promise;
  return returnMeta ? { data, meta } : data;
};

const toQueryBody = (obj) =>
  Object.fromEntries(
    Object.entries(obj || {}).filter(
      ([, v]) => v !== undefined && v !== null && v !== ""
    )
  );

/* ============================
 * WebSocket optimizado para Chat Agent v10.0
 * ============================ */

const makeWsUrl = (path) => {
  const base = BASE_URL.replace(/^http/, 'ws').replace(/\/$/, '');
  return `${base}${path}`;
};

/**
 * ✅ WebSocket optimizado para Chat Agent v10.0 con Perfect Integration
 * Heartbeat compatible con configuración del servidor (30s ping, 15s timeout)
 */
const openChatSocket = (userId, { onMessage, onOpen, onClose, onError } = {}) => {
  if (!userId) throw new Error("userId requerido para WS");
  const url = makeWsUrl(`/ws/chat/${encodeURIComponent(userId)}`);
  
  console.log(`[WS] 🔌 Conectando a Chat Agent v10.0: ${url}`);
  const socket = new WebSocket(url);
  
  let heartbeatInterval;
  let isAlive = false;

  socket.onopen = (evt) => {
    console.log('[WS] ✅ Chat Agent v10.0 conectado exitosamente');
    isAlive = true;

    // ✅ Heartbeat cada 25s (más conservador que el servidor)
    heartbeatInterval = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        console.log('[WS] 💓 Enviando ping a Chat Agent v10.0');
        try {
          socket.send(JSON.stringify({ type: 'ping', ts: Date.now() }));
        } catch (error) {
          console.warn('[WS] ⚠️ Error sending ping:', error);
          clearInterval(heartbeatInterval);
        }

        // Timeout de 10s para recibir pong
        isAlive = false;
        setTimeout(() => {
          if (!isAlive && socket.readyState === WebSocket.OPEN) {
            console.log('[WS] ❌ Ping timeout, reconectando...');
            socket.close(1000, 'Ping timeout'); 
          }
        }, 10000);
      }
    }, 25000);

    onOpen && onOpen(evt);
  };

  socket.onmessage = (evt) => {
    try {
      const msg = JSON.parse(evt.data);
      
      // ✅ Manejar ready de Chat Agent v10.0 + CDG Agent v6.0
      if (msg.type === 'ready') {
        console.log(`[WS] 🎯 Ready: ${msg.chat_agent} + ${msg.cdg_agent} (${msg.integration})`);
        return;
      }
      
      // Manejar pong del servidor
      if (msg.type === 'pong') {
        console.log('[WS] 💚 Pong recibido de Chat Agent v10.0');
        isAlive = true;
        return;
      }
      
      onMessage && onMessage(msg);
    } catch (e) {
      console.warn('[WS] Parse error:', e);
    }
  };
  
  socket.onerror = (evt) => {
    console.error('[WS] ❌ Error en Chat Agent v10.0:', evt);
    onError && onError(evt);
  };
  
  socket.onclose = (evt) => {
    console.log(`[WS] 🔌 Chat Agent v10.0 cerrado: ${evt.code} - ${evt.reason || 'Sin razón'}`);
    
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
    
    onClose && onClose(evt);
  };

  const sendJson = (obj) => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(obj));
    } else {
      console.warn('[WS] ⚠️ Cannot send, socket not open:', socket.readyState);
    }
  };

  const close = () => {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
    socket.close();
  };

  return { socket, sendJson, close };
};

/* ============================
 * SDK por módulos - COMPLETAMENTE ACTUALIZADO
 * ============================ */

// ✅ System
const system = {
  root: (cfg) => unwrap(http.get("/", cfg), { returnMeta: true }),
  health: (cfg) => unwrap(http.get("/health", cfg)),
  version: (cfg) => unwrap(http.get("/version", cfg)),
};

// ✅ Catalogs / Periods - EXTENDIDO CON NUEVOS ENDPOINTS
const catalogs = {
  periods: (cfg) => unwrap(http.get("/periods", cfg)),
  latestPeriod: (cfg) => unwrap(http.get("/periods/latest", cfg)),
  catalogs: (cfg) => unwrap(http.get("/catalogs", cfg)),
  // ✅ NUEVOS: Períodos con métricas
  periodMetricas: (periodo, cfg) =>
    unwrap(http.get(`/periods/${encodeURIComponent(periodo)}/metricas`, cfg)),
  comparePeriods: (periodoActual, periodoAnterior, cfg) =>
    unwrap(http.get(`/periods/compare/${encodeURIComponent(periodoActual)}/${encodeURIComponent(periodoAnterior)}`, cfg)),
};

// ✅ Basic - COMPLETAMENTE EXTENDIDO (TODOS LOS ENDPOINTS MANTENIDOS)
const basic = {
  // Core básicos
  summary: (cfg) => unwrap(http.get("/basic/summary", cfg)),
  gestoresRanking: (metric = "contratos", cfg) =>
    unwrap(http.get("/basic/gestores-ranking", { params: { metric }, ...cfg })),
  // ✅ NUEVO: Todos los gestores
  allGestores: (cfg) => unwrap(http.get("/basic/gestores", cfg)),
  centros: (cfg) => unwrap(http.get("/basic/centros", cfg)),
  productos: (cfg) => unwrap(http.get("/basic/productos", cfg)),
  
  // ✅ NUEVOS: Gastos
  gastosByFecha: (fecha, cfg) =>
    unwrap(http.get("/basic/gastos/by-fecha", { params: { fecha }, ...cfg })),

  // ✅ NUEVOS: Contratos extendidos
  allContracts: (cfg) => unwrap(http.get("/basic/contracts", cfg)),
  contractsCount: (cfg) => unwrap(http.get("/basic/contracts/count", cfg)),
  contractsByGestor: (gestorId, cfg) =>
    unwrap(http.get(`/basic/contracts/by-gestor/${gestorId}`, cfg)),
  contractsByCliente: (clienteId, cfg) =>
    unwrap(http.get(`/basic/contracts/by-cliente/${clienteId}`, cfg)),
  contractsByProducto: (productoId, cfg) =>
    unwrap(http.get(`/basic/contracts/by-producto/${encodeURIComponent(productoId)}`, cfg)),
  contractsByCentro: (centroId, cfg) =>
    unwrap(http.get(`/basic/contracts/by-centro/${centroId}`, cfg)),

  // ✅ NUEVOS: Gestores extendidos
  gestoresByCentro: (centroId, cfg) =>
    unwrap(http.get(`/basic/gestores/by-centro/${centroId}`, cfg)),
  gestoresBySegmento: (segmentoId, cfg) =>
    unwrap(http.get(`/basic/gestores/by-segmento/${encodeURIComponent(segmentoId)}`, cfg)),
  gestorInfo: (gestorId, cfg) =>
    unwrap(http.get(`/basic/gestores/${gestorId}`, cfg)),
  gestorSegmento: (gestorId, cfg) =>
    unwrap(http.get(`/basic/gestores/${gestorId}/segmento`, cfg)),
  countGestoresByCentro: (cfg) =>
    unwrap(http.get("/basic/gestores/count-by-centro", cfg)),
  countGestoresBySegmento: (cfg) =>
    unwrap(http.get("/basic/gestores/count-by-segmento", cfg)),

  // ✅ NUEVOS: Clientes extendidos
  clientesByGestor: (gestorId, cfg) =>
    unwrap(http.get(`/basic/clientes/by-gestor/${gestorId}`, cfg)),
  clientesByCentro: (centroId, cfg) =>
    unwrap(http.get(`/basic/clientes/by-centro/${centroId}`, cfg)),
  clientMetricsByGestor: (gestorId, cfg) =>
    unwrap(http.get(`/basic/clientes/metrics/${gestorId}`, cfg)),

  // ✅ NUEVOS: Productos extendidos
  productosByGestor: (gestorId, cfg) =>
    unwrap(http.get(`/basic/productos/by-gestor/${gestorId}`, cfg)),
  productosTop: (cfg) => unwrap(http.get("/basic/productos/top", cfg)),

  // ✅ NUEVOS: Precios completos
  preciosStd: (cfg) => unwrap(http.get("/basic/precios/std", cfg)),
  preciosStdBySegmento: (segmentoId, cfg) =>
    unwrap(http.get(`/basic/precios/std/by-segmento/${encodeURIComponent(segmentoId)}`, cfg)),
  precioStdBySP: (segmentoId, productoId, cfg) =>
    unwrap(
      http.get(
        `/basic/precios/std/by-sp/${encodeURIComponent(segmentoId)}/${encodeURIComponent(productoId)}`,
        cfg
      )
    ),
  preciosReal: (cfg) => unwrap(http.get("/basic/precios/real", cfg)),
  preciosRealByFecha: (fechaCalculo, cfg) =>
    unwrap(
      http.get("/basic/precios/real/by-fecha", {
        params: { fecha_calculo: fechaCalculo },
        ...cfg,
      })
    ),
  preciosRealBySP: (segmentoId, productoId, cfg) =>
    unwrap(
      http.get(
        `/basic/precios/real/by-sp/${encodeURIComponent(segmentoId)}/${encodeURIComponent(productoId)}`,
        cfg
      )
    ),
  preciosCompare: (fechaCalculo, cfg) =>
    unwrap(
      http.get("/basic/precios/compare", {
        params: { fecha_calculo: fechaCalculo || undefined },
        ...cfg,
      })
    ),

  // ✅ NUEVOS: CDR y cuentas
  cdrLineas: (cfg) => unwrap(http.get("/basic/cdr/lineas", cfg)),
  cdrLineasCount: (cfg) => unwrap(http.get("/basic/cdr/lineas/count", cfg)),
  cuentas: (cfg) => unwrap(http.get("/basic/cuentas", cfg)),
  cuentasByLinea: (lineaCdr, cfg) =>
    unwrap(http.get(`/basic/cuentas/by-linea/${encodeURIComponent(lineaCdr)}`, cfg)),

  // ✅ NUEVOS: Conteos adicionales
  countContractsByCentro: (cfg) =>
    unwrap(http.get("/basic/contracts/count-by-centro", cfg)),
  countContractsByProducto: (cfg) =>
    unwrap(http.get("/basic/contracts/count-by-producto", cfg)),
  countContractsByGestor: (cfg) =>
    unwrap(http.get("/basic/contracts/count-by-gestor", cfg)),
};

// ✅ Analytics - COMPLETAMENTE NUEVO MÓDULO CON MÉTRICAS FINANCIERAS
const analytics = {
  // ✅ Varianza (existente)
  variance: ({ scope, id, periodo, vs = "budget" }, cfg) =>
    unwrap(
      http.get("/analytics/variance", {
        params: { scope, id: id || undefined, periodo, vs },
        ...cfg,
      })
    ),
  
  // ✅ NUEVOS: Métricas por Centro
  centroMetricas: (centroId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/analytics/centro/${centroId}/metricas`, { params: { periodo }, ...cfg })),
  centroGestoresMetricas: (centroId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/analytics/centro/${centroId}/gestores-con-metricas`, { params: { periodo }, ...cfg })),
  
  // ✅ NUEVOS: Métricas por Segmento
  segmentoMetricas: (segmentoId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/analytics/segmento/${encodeURIComponent(segmentoId)}/metricas`, { params: { periodo }, ...cfg })),
  
  // ✅ NUEVOS: Métricas por Gestor
  gestorMetricasCompletas: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/analytics/gestor/${gestorId}/metricas-completas`, { params: { periodo }, ...cfg })),
  gestorClientesMetricas: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/analytics/gestor/${gestorId}/clientes-con-metricas`, { params: { periodo }, ...cfg })),
  
  // ✅ NUEVOS: Métricas por Cliente
  clienteMetricas: (clienteId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/analytics/cliente/${clienteId}/metricas`, { params: { periodo }, ...cfg })),
  clienteContratosMetricas: (clienteId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/analytics/cliente/${clienteId}/contratos-con-metricas`, { params: { periodo }, ...cfg })),
  
  // ✅ NUEVOS: Métricas por Contrato
  contratoDetalleCompleto: (contratoId, cfg) =>
    unwrap(http.get(`/analytics/contrato/${contratoId}/detalle-completo`, cfg)),
};

// ✅ Data Queries - ACTUALIZADO
const dataQueries = {
  pricesComparison: ({ gestorId, productoId, periodo } = {}, cfg) =>
    unwrap(
      http.get("/prices/comparison", {
        params: {
          gestor_id: gestorId || undefined,
          producto_id: productoId || undefined,
          periodo: periodo || undefined,
        },
        ...cfg,
      })
    ),
  pricesComparisonBySegment: (segmentoId, periodo, cfg) =>
    unwrap(
      http.get("/prices/comparison-by-segment", {
        params: { segmento_id: segmentoId, periodo },
        ...cfg,
      })
    ),
};

// ✅ Comparatives - EXTENDIDO
const comparatives = {
  gestoresMargen: (periodo, cfg) =>
    unwrap(http.get("/comparatives/gestores/margen", { params: { periodo }, ...cfg })),
  centrosMargen: (periodo, cfg) =>
    unwrap(http.get("/comparatives/centros/margen", { params: { periodo }, ...cfg })),
  segmentosMargen: (periodo, cfg) =>
    unwrap(http.get("/comparatives/segmentos/margen", { params: { periodo }, ...cfg })),
  custom: (payload, cfg) => unwrap(http.post("/comparatives/custom", toQueryBody(payload), cfg)),
  // ✅ NUEVO: Ranking extendido
  gestoresRanking: (periodo = "2025-10", cfg) =>
    unwrap(http.get("/comparatives/gestores-ranking", { params: { periodo }, ...cfg })),
};

// ✅ Deviations - COMPLETAMENTE EXTENDIDO
const deviations = {
  pricing: (periodo, umbral = 15.0, cfg) =>
    unwrap(
      http.get("/deviations/pricing", { params: { periodo, umbral }, ...cfg }),
      { returnMeta: true }
    ),
  summary: (periodo, cfg) =>
    unwrap(http.get("/deviations/summary", { params: { periodo }, ...cfg })),
  // ✅ NUEVOS: Margen y volumen
  margen: (periodo, { z = 2.0, enhanced = true } = {}, cfg) =>
    unwrap(http.get("/deviations/margen", { params: { periodo, z, enhanced }, ...cfg })),
  volumen: (periodo, { factor = 3.0, enhanced = true } = {}, cfg) =>
    unwrap(http.get("/deviations/volumen", { params: { periodo, factor, enhanced }, ...cfg })),
  // ✅ NUEVO: Critical
  critical: (periodo, umbral = 15.0, cfg) =>
    unwrap(http.get("/deviations/critical", { params: { periodo, umbral }, ...cfg })),
};

// ✅ Incentives - COMPLETAMENTE EXTENDIDO
const incentives = {
  scorecard: (gestorId, periodo, cfg) =>
    unwrap(http.get(`/incentives/gestor/${encodeURIComponent(gestorId)}`, { params: { periodo }, ...cfg })),
  bonusMargen: (periodo, umbral = 15.0, cfg) =>
    unwrap(http.get("/incentives/bonus-margen", { params: { periodo, umbral_margen: umbral }, ...cfg })),
  bonusPool: (periodo, pool = 50000.0, cfg) =>
    unwrap(http.get("/incentives/bonus-pool", { params: { periodo, pool }, ...cfg })),
  simulate: (payload, cfg) =>
    unwrap(http.post("/incentives/simulate", toQueryBody(payload), cfg)),
  // ✅ NUEVO: Calculate
  calculate: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get("/incentives/calculate", { 
      params: { gestor_id: gestorId || undefined, periodo }, 
      ...cfg 
    })),
  
  // ✅ NUEVOS: Incentivos detallados por entidad
  centroTotal: (centroId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/incentives/centro/${centroId}/total`, { params: { periodo }, ...cfg })),
  gestorDetalle: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/incentives/gestor/${encodeURIComponent(gestorId)}/detalle`, { params: { periodo }, ...cfg })),
};

// ✅ KPIs - COMPLETAMENTE EXTENDIDO CON NUEVOS ENDPOINTS
const kpis = {
  // Existentes
  gestor: (gestorId, periodo, cfg) =>
    unwrap(
      http.get(`/kpis/gestor/${encodeURIComponent(gestorId)}`, {
        params: { periodo },
        ...cfg,
      })
    ),
  evolution: (gestorId, fromPeriod, toPeriod, cfg) =>
    unwrap(
      http.get(`/kpis/gestor/${encodeURIComponent(gestorId)}/evolution`, {
        params: { from_period: fromPeriod, to_period: toPeriod },
        ...cfg,
      })
    ),
  
  // ✅ NUEVOS: KPIs financieros específicos por entidad
  centroFinancieros: (centroId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/kpis/centro/${centroId}/financieros`, { params: { periodo }, ...cfg })),
  gestorFinancieros: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/kpis/gestor/${gestorId}/financieros`, { params: { periodo }, ...cfg })),
  gestorROE: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/kpis/gestor/${gestorId}/roe`, { params: { periodo }, ...cfg })),
  gestorEficiencia: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/kpis/gestor/${gestorId}/eficiencia`, { params: { periodo }, ...cfg })),
  centroMargen: (centroId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/kpis/centro/${centroId}/margen`, { params: { periodo }, ...cfg })),
  centroBonusTotal: (centroId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/kpis/centro/${centroId}/bonus-total`, { params: { periodo }, ...cfg })),
};

// ✅ Charts - ACTUALIZADO CON NUEVOS MÉTODOS
const charts = {
  fromData: (data, config = {}, cfg) =>
    unwrap(http.post("/charts/from-data", { data, config }, cfg)),
  pivot: ({ userId, message, currentChartConfig, chartInteractionType = "pivot" }, cfg) =>
    unwrap(
      http.post("/charts/pivot", {
        user_id: userId,
        message,
        current_chart_config: currentChartConfig || {},
        chart_interaction_type: chartInteractionType,
      }, cfg)
    ),
  quick: ({ queryMethod, chartType = "bar", kwargs = {} }, cfg) =>
    unwrap(http.post("/charts/quick", { query_method: queryMethod, chart_type: chartType, kwargs }, cfg)),
  supportedTypes: (cfg) => unwrap(http.get("/charts/supported-types", cfg)),
  validate: (cfg) => unwrap(http.get("/charts/validate", cfg)),
  availableQueries: (cfg) => unwrap(http.get("/charts/available-queries", cfg)),
  availableTypes: (cfg) => unwrap(http.get("/charts/available-types", cfg)),
  meta: (cfg) => unwrap(http.get("/charts/meta", cfg)),
  summaryDashboard: (cfg) => unwrap(http.get("/charts/summary-dashboard", cfg)),
  gestoresRanking: ({ metric = "CONTRATOS", chartType = "horizontal_bar" } = {}, cfg) =>
    unwrap(http.get("/charts/gestores-ranking", { params: { metric, chart_type: chartType }, ...cfg })),
  centrosDistribution: ({ chartType = "donut" } = {}, cfg) =>
    unwrap(http.get("/charts/centros-distribution", { params: { chart_type: chartType }, ...cfg })),
  productosPopularity: ({ chartType = "horizontal_bar" } = {}, cfg) =>
    unwrap(http.get("/charts/productos-popularity", { params: { chart_type: chartType }, ...cfg })),
  preciosComparison: ({ fechaCalculo = null, chartType = "bar" } = {}, cfg) =>
    unwrap(
      http.get("/charts/precios-comparison", {
        params: { fecha_calculo: fechaCalculo || undefined, chart_type: chartType },
        ...cfg,
      })
    ),
  gastosByCentro: ({ fecha, chartType = "stacked_bar" }, cfg) =>
    unwrap(http.get("/charts/gastos-by-centro", { params: { fecha, chart_type: chartType }, ...cfg })),
};

// ✅ Dashboards - COMPLETAMENTE EXTENDIDO CON NUEVOS ENDPOINTS
const dashboards = {
  // Existentes
  templates: (cfg) => unwrap(http.get("/dashboards/templates", cfg)),
  build: (payload, cfg) => unwrap(http.post("/dashboards/build", toQueryBody(payload), cfg)),
  generate: (payload, cfg) => unwrap(http.post("/dashboards/generate", toQueryBody(payload), cfg)),
  
  // ✅ NUEVOS: Dashboards específicos para componentes frontend
  gestorSummary: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/dashboards/gestor/${encodeURIComponent(gestorId)}/summary`, { params: { periodo }, ...cfg })),
  gestorEvolution: (gestorId, cfg) =>
    unwrap(http.get(`/dashboards/gestor/${encodeURIComponent(gestorId)}/evolution`, cfg)),
  gestorProductos: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/dashboards/gestor/${encodeURIComponent(gestorId)}/productos`, { params: { periodo }, ...cfg })),
  gestorAlertas: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/dashboards/gestor/${encodeURIComponent(gestorId)}/alertas`, { params: { periodo }, ...cfg })),
  gestorComparative: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/dashboards/gestor/${encodeURIComponent(gestorId)}/comparative`, { params: { periodo }, ...cfg })),
  
  // ✅ NUEVOS: Dashboards de incentivos
  incentivosSummary: (periodo = "2025-10", cfg) =>
    unwrap(http.get("/dashboards/incentivos/summary", { params: { periodo }, ...cfg })),
  incentivosTendencia: (cfg) =>
    unwrap(http.get("/dashboards/incentivos/tendencia", cfg)),
  
  // ✅ NUEVOS: Dashboards comparativos
  comparativeSummary: (periodo = "2025-10", cfg) =>
    unwrap(http.get("/dashboards/comparative/summary", { params: { periodo }, ...cfg })),
  matrizSegmentos: (periodo = "2025-10", cfg) =>
    unwrap(http.get("/dashboards/matriz-segmentos", { params: { periodo }, ...cfg })),
};

// ✅ Reports - EXTENDIDO
const reports = {
  businessReview: ({ userId, gestorId, periodo, options, reportType = "business_review" }, cfg) =>
    unwrap(
      http.post("/reports/business-review", {
        user_id: userId,
        gestor_id: gestorId || undefined,
        periodo,
        report_type: reportType,
        options: options || {},
      }, cfg)
    ),
  executiveSummary: ({ userId, periodo, options }, cfg) =>
    unwrap(
      http.post("/reports/executive-summary", {
        user_id: userId,
        periodo,
        options: options || {},
      }, cfg)
    ),
  deviationAnalysis: (periodo, cfg) =>
    unwrap(http.post("/reports/deviation-analysis", null, { params: { periodo }, ...cfg })),
  export: ({ format = "pdf", ...rest } = {}, cfg) =>
    unwrap(http.post("/reports/export", { format, ...rest }, cfg)),
  meta: (cfg) => unwrap(http.get("/reports/meta", cfg)),
};

// ✅ KPI Calculator - ACTUALIZADO
const kpiCalc = {
  margen: ({ ingresos, gastos }, cfg) =>
    unwrap(http.post("/kpi/margen", { ingresos, gastos }, cfg)),
  roe: ({ beneficioNeto, patrimonio }, cfg) =>
    unwrap(http.post("/kpi/roe", { beneficio_neto: beneficioNeto, patrimonio }, cfg)),
  // ✅ CORREGIDO: from-data → calculate
  calculate: (row, cfg) => unwrap(http.post("/kpi/calculate", { row }, cfg)),
};

// ✅ Security - MANTENIDO
const security = {
  validateSQL: (sql, context = "general", cfg) =>
    unwrap(http.post("/security/sql/validate", { sql, context }, cfg)),
};

// ✅ SQL - NUEVO MÓDULO
const sql = {
  dynamic: (sql, context = "general", cfg) =>
    unwrap(http.post("/sql/dynamic", { sql, context }, cfg)),
  validate: (sql, context = "general", cfg) =>
    unwrap(http.post("/sql/validate", { sql, context }, cfg)),
};

// ✅ Gestor Analysis - NUEVO MÓDULO  
const gestorAnalysis = {
  performance: (gestorId, periodo = "2025-10", cfg) =>
    unwrap(http.get(`/gestor/${encodeURIComponent(gestorId)}/performance`, { 
      params: { periodo }, 
      ...cfg 
    })),
};

// ✅ Reflection - NUEVO MÓDULO
const reflection = {
  insights: (cfg) => unwrap(http.get("/reflection/insights", cfg)),
};

// ✅ Feedback - NUEVO MÓDULO
const feedback = {
  process: (payload, cfg) => unwrap(http.post("/feedback/process", toQueryBody(payload), cfg)),
};

// ✅ Chat Agent v10.0 - COMPLETAMENTE ACTUALIZADO
const chat = {
  message: (payload, cfg) => unwrap(http.post("/chat/message", toQueryBody(payload), cfg)),
  status: (cfg) => unwrap(http.get("/chat/status", cfg)),
  // ✅ NUEVO: Capabilities
  capabilities: (cfg) => unwrap(http.get("/chat/capabilities", cfg)),
  history: (userId, cfg) => unwrap(http.get(`/chat/history/${encodeURIComponent(userId)}`, cfg)),
  suggestions: (userId, cfg) =>
    unwrap(http.get(`/chat/suggestions/${encodeURIComponent(userId)}`, cfg)),
  // ✅ CORREGIDO: reset como POST
  reset: (userId, cfg) =>
    unwrap(http.post(`/chat/reset/${encodeURIComponent(userId)}`, {}, cfg)),
  // WebSocket optimizado
  openSocket: openChatSocket,
};

// ✅ CDG Agent v6.0 - COMPLETAMENTE ACTUALIZADO  
const agent = {
  process: (payload, cfg) =>
    unwrap(http.post("/agent/process", toQueryBody(payload), cfg)),
  // ✅ NUEVO: Complex Analysis
  complexAnalysis: (payload, cfg) =>
    unwrap(http.post("/agent/complex-analysis", toQueryBody(payload), cfg)),
  status: (cfg) => unwrap(http.get("/agent/status", cfg)),
  // ✅ NUEVO: Specializations
  specializations: (cfg) => unwrap(http.get("/agent/specializations", cfg)),
  suggestQuestions: (userId, cfg) =>
    unwrap(http.get("/agent/suggest-questions", { params: { user_id: userId || undefined }, ...cfg })),
};

// ✅ Integration - MÓDULO COMPLETAMENTE NUEVO
const integration = {
  classifyAndRoute: (payload, cfg) =>
    unwrap(http.post("/integration/classify-and-route", toQueryBody(payload), cfg)),
  executePredefined: (payload, cfg) =>
    unwrap(http.post("/integration/execute-predefined", toQueryBody(payload), cfg)),
  queryCatalogs: (cfg) => unwrap(http.get("/integration/query-catalogs", cfg)),
  agentCoordination: (cfg) => unwrap(http.get("/integration/agent-coordination", cfg)),
};

// ✅ User - MANTENIDO
const user = {
  personalization: (userId, cfg) =>
    unwrap(http.get(`/user/${encodeURIComponent(userId)}/personalization`, cfg)),
  feedback: (userId, payload, cfg) =>
    unwrap(http.post(`/user/${encodeURIComponent(userId)}/feedback`, toQueryBody(payload), cfg)),
};

/* ============================
 * Export público - COMPLETAMENTE ACTUALIZADO
 * ============================ */

const api = {
  // low-level
  http,
  buildQuery,
  ApiClientError,

  // módulos actualizados
  system,
  catalogs,               // ✅ +2 nuevos endpoints
  basic,                  // ✅ 35+ endpoints (todos mantenidos)
  analytics,              // ✅ +9 nuevos endpoints de métricas financieras
  kpis,                   // ✅ +6 nuevos endpoints financieros específicos
  comparatives,           // ✅ +1 endpoint
  deviations,             // ✅ +3 endpoints  
  incentives,             // ✅ +3 nuevos endpoints detallados
  dataQueries,
  charts,                 // ✅ +1 endpoint
  dashboards,             // ✅ +9 nuevos endpoints específicos
  reports,
  kpiCalc,                // ✅ corregido
  security,
  
  // ✅ NUEVOS MÓDULOS
  sql,                    // ✅ 2 endpoints
  gestorAnalysis,         // ✅ 1 endpoint
  reflection,             // ✅ 1 endpoint  
  feedback,               // ✅ 1 endpoint
  integration,            // ✅ 4 endpoints
  
  // agentes actualizados
  chat,                   // ✅ Chat Agent v10.0
  agent,                  // ✅ CDG Agent v6.0
  user,
};

export default api;

// Exports individuales
export {
  api,
  http,
  system,
  catalogs,
  basic,
  analytics,
  kpis,
  comparatives,
  deviations,
  incentives,
  dataQueries,
  charts,
  dashboards,
  reports,
  kpiCalc,
  security,
  sql,
  gestorAnalysis,
  reflection,
  feedback,
  integration,
  chat,
  agent,
  user,
  ApiClientError,
};
