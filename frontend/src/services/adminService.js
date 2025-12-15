// frontend/src/services/adminService.js
/* eslint-disable no-console */

/**
 * AdminService v11.0 — Perfect Integration (Chat Agent v10.0 + CDG Agent v6.0)
 * --------------------------------------------------------------------------
 * Capa de alto nivel para endpoints "administrativos" y de metadatos
 * expuestos por la CDG API v11.0:
 *   - System (/, /health, /version) 
 *   - Catálogos (/periods, /catalogs)
 *   - Chat Agent v10.0 (status, capabilities, suggestions)
 *   - CDG Agent v6.0 (status, specializations, complex analysis)
 *   - Integration (Perfect Integration - 4 nuevos endpoints)
 *   - Charts (meta, tipos, validate, queries disponibles)
 *   - Dashboards (templates, generate)
 *   - Reports (meta, export)
 *   - Security & SQL (validate, dynamic)
 *   - Nuevos módulos: gestorAnalysis, reflection, feedback
 *   - Utilidades (warmup/init, buildInfo, WS helper)
 */

import api, { ApiClientError } from "./api";

/* =================================================================================
 * Cache in-memory con TTL optimizado para v11.0
 * ================================================================================= */
const _cache = new Map();

/**
 * getCached: Cache con TTL mejorado para Perfect Integration
 * - key: string única del recurso  
 * - ttlMs: milisegundos de validez
 * - fetcher: () => Promise<any>
 */
const getCached = async (key, ttlMs, fetcher) => {
  const now = Date.now();
  const hit = _cache.get(key);
  if (hit && now - hit.ts < ttlMs) {
    console.log(`[AdminService] 💾 Cache hit: ${key}`);
    return hit.value;
  }
  
  console.log(`[AdminService] 🔄 Cache miss: ${key}`);
  const value = await fetcher();
  _cache.set(key, { ts: now, value });
  return value;
};

/**
 * clearCache: Limpia cache específico o completo
 */
const clearCache = (pattern) => {
  if (!pattern) {
    _cache.clear();
    console.log(`[AdminService] 🧹 Cache completamente limpiado`);
    return;
  }
  
  const keysToDelete = Array.from(_cache.keys()).filter(key => key.includes(pattern));
  keysToDelete.forEach(key => _cache.delete(key));
  console.log(`[AdminService] 🧹 Cache limpiado para patrón: ${pattern} (${keysToDelete.length} items)`);
};

/* =================================================================================
 * AdminService v11.0: API Completa
 * ================================================================================= */
const TTL_FAST = 30 * 1000;      // 30s (health/ping/status)
const TTL_META = 5 * 60 * 1000;  // 5m (metadatos estables)
const TTL_SLOW = 15 * 60 * 1000; // 15m (datos muy estables)

const AdminService = {
  /* -----------------------
   * System (actualizado)
   * ----------------------- */
  /**
   * ✅ Root: devuelve info completa con Perfect Integration
   */
  getRoot: (cfg) =>
    getCached("system:root", TTL_META, async () => {
      return api.system.root(cfg);
    }),

  /** ✅ Health: estado del sistema */
  ping: (cfg) =>
    getCached("system:health", TTL_FAST, async () => api.system.health(cfg)),

  /** ✅ Version: información de versión completa */
  getVersion: (cfg) =>
    getCached("system:version", TTL_META, async () => api.system.version(cfg)),

  /**
   * ✅ buildInfo: resumen completo para panel "About"
   * Incluye validaciones de todos los módulos nuevos
   */
  getBuildInfo: async (cfg) => {
    const [
      root, 
      version, 
      chartsValidate, 
      chatStatus, 
      agentStatus,
      integrationCoordination,
      adminValidation
    ] = await Promise.allSettled([
      AdminService.getRoot(cfg),
      AdminService.getVersion(cfg),
      AdminService.validateCharts(cfg),
      AdminService.getChatStatus(cfg),
      AdminService.getAgentStatus(cfg),
      AdminService.getIntegrationCoordination(cfg),
      AdminService.validateChartGenerator(cfg)
    ]);


    return {
      apiBaseUrl: api.http.baseURL,
      system: root.status === 'fulfilled' ? (root.value?.data || root.value) : { error: root.reason?.message },
      version: version.status === 'fulfilled' ? version.value : { error: version.reason?.message },
      chartsValidate: chartsValidate.status === 'fulfilled' ? chartsValidate.value : { error: chartsValidate.reason?.message },
      chatAgent: chatStatus.status === 'fulfilled' ? chatStatus.value : { error: chatStatus.reason?.message },
      cdgAgent: agentStatus.status === 'fulfilled' ? agentStatus.value : { error: agentStatus.reason?.message },
      integration: integrationCoordination.status === 'fulfilled' ? integrationCoordination.value : { error: integrationCoordination.reason?.message },
      admin: adminValidation.status === 'fulfilled' ? adminValidation.value : { error: adminValidation.reason?.message },
      buildTime: new Date().toISOString(),
    };
  },

  /* -----------------------
   * Catálogos / Períodos (mantenidos)
   * ----------------------- */
  getCatalogs: (cfg) =>
    getCached("catalogs:all", TTL_META, async () => api.catalogs.catalogs(cfg)),

  getPeriods: (cfg) =>
    getCached("catalogs:periods", TTL_META, async () => api.catalogs.periods(cfg)),

  getLatestPeriod: (cfg) =>
    getCached("catalogs:periods:latest", TTL_FAST, async () =>
      api.catalogs.latestPeriod(cfg)
    ),

  /* -----------------------
   * ✅ Chat Agent v10.0 (ACTUALIZADO)
   * ----------------------- */
  getChatStatus: (cfg) =>
    getCached("chat:status", TTL_FAST, async () => api.chat.status(cfg)),

  /** ✅ NUEVO: Capacidades del Chat Agent v10.0 */
  getChatCapabilities: (cfg) =>
    getCached("chat:capabilities", TTL_META, async () => api.chat.capabilities(cfg)),

  getChatSuggestions: (userId, cfg) =>
    api.chat.suggestions(userId, cfg),

  getChatHistory: (userId, cfg) =>
    api.chat.history(userId, cfg),

  resetChatSession: (userId, cfg) =>
    api.chat.reset(userId, cfg),

  /* -----------------------
   * ✅ CDG Agent v6.0 (ACTUALIZADO)
   * ----------------------- */
  getAgentStatus: (cfg) =>
    getCached("agent:status", TTL_FAST, async () => api.agent.status(cfg)),

  /** ✅ NUEVO: Especializaciones del CDG Agent v6.0 */
  getAgentSpecializations: (cfg) =>
    getCached("agent:specializations", TTL_META, async () => api.agent.specializations(cfg)),

  getAgentSuggestedQuestions: (userId, cfg) =>
    api.agent.suggestQuestions(userId, cfg),

  /** ✅ NUEVO: Análisis complejo directo */
  requestComplexAnalysis: (payload, cfg) =>
    api.agent.complexAnalysis(payload, cfg),

  /* -----------------------
   * ✅ Integration (MÓDULO COMPLETAMENTE NUEVO)
   * ----------------------- */
  /** ✅ NUEVO: Clasificación y enrutamiento inteligente */
  classifyAndRoute: (payload, cfg) =>
    api.integration.classifyAndRoute(payload, cfg),

  /** ✅ NUEVO: Ejecución de query predefinida */
  executePredefined: (payload, cfg) =>
    api.integration.executePredefined(payload, cfg),

  /** ✅ NUEVO: Catálogos de queries disponibles */
  getQueryCatalogs: (cfg) =>
    getCached("integration:query-catalogs", TTL_META, async () => 
      api.integration.queryCatalogs(cfg)
    ),

  /** ✅ NUEVO: Estado de coordinación entre agentes */
  getIntegrationCoordination: (cfg) =>
    getCached("integration:coordination", TTL_FAST, async () => 
      api.integration.agentCoordination(cfg)
    ),

  /* -----------------------
   * Charts (mejorado con nuevos endpoints)
   * ----------------------- */
  getChartsMeta: (cfg) =>
    getCached("charts:meta", TTL_META, async () => api.charts.meta(cfg)),

  getSupportedChartTypes: (cfg) =>
    getCached("charts:supported-types", TTL_META, async () =>
      api.charts.supportedTypes(cfg)
    ),

  /** ✅ NUEVO: Tipos disponibles (diferente de supportedTypes) */
  getAvailableChartTypes: (cfg) =>
    getCached("charts:available-types", TTL_META, async () =>
      api.charts.availableTypes(cfg)
    ),

  getAvailableChartQueries: (cfg) =>
    getCached("charts:available-queries", TTL_META, async () =>
      api.charts.availableQueries(cfg)
    ),

  validateCharts: (cfg) => api.charts.validate(cfg),

  /** ✅ NUEVO: Dashboard resumen predefinido */
  getSummaryDashboard: (cfg) =>
    api.charts.summaryDashboard(cfg),

  /** ✅ NUEVO: Opciones de gráficos por rol */
  getChartOptions: (userRole, cfg) =>
    getCached(`charts:options:${userRole}`, TTL_META, async () => 
      api.charts.options(userRole, cfg)
    ),

  /** ✅ NUEVO: Validar configuración de gráfico */
  validateChartConfig: (config, cfg) =>
    api.charts.validateConfig(config, cfg),

  /** ✅ NUEVO: Crear gráfico con seguridad */
  createSecureChart: (payload, cfg) =>
    api.charts.createSecure(payload, cfg),

  /* -----------------------
   * Dashboards / Reports (extendido)
   * ----------------------- */
  getDashboardTemplates: (cfg) =>
    getCached("dashboards:templates", TTL_META, async () =>
      api.dashboards.templates(cfg)
    ),

  /** ✅ NUEVO: Generar dashboard */
  generateDashboard: (payload, cfg) =>
    api.dashboards.generate(payload, cfg),

  getReportsMeta: (cfg) =>
    getCached("reports:meta", TTL_META, async () => api.reports.meta(cfg)),

  /** ✅ NUEVO: Análisis de desviaciones */
  generateDeviationAnalysis: (periodo, cfg) =>
    api.reports.deviationAnalysis(periodo, cfg),

  /* -----------------------
   * ✅ Security & SQL (EXPANDIDO)
   * ----------------------- */
  /** Validación SQL (Security) */
  validateSQL: (sql, context = "general", cfg) =>
    api.security.validateSQL(sql, context, cfg),

  /** ✅ NUEVO: SQL dinámico */
  executeDynamicSQL: (sql, context = "general", cfg) =>
    api.sql.dynamic(sql, context, cfg),

  /** ✅ NUEVO: Validación SQL (SQL module) */
  validateSQLAdvanced: (sql, context = "general", cfg) =>
    api.sql.validate(sql, context, cfg),

  /* -----------------------
   * ✅ NUEVOS MÓDULOS
   * ----------------------- */
  /** ✅ Gestor Analysis */
  getGestorPerformance: (gestorId, periodo, cfg) =>
    api.gestorAnalysis.performance(gestorId, periodo, cfg),

  /** ✅ Reflection */
  getReflectionInsights: (cfg) =>
    getCached("reflection:insights", TTL_META, async () => api.reflection.insights(cfg)),

  /** ✅ Feedback */
  processFeedback: (payload, cfg) =>
    api.feedback.process(payload, cfg),

  /* -----------------------
   * ✅ Admin V4.4 (COMPLETAMENTE NUEVO)
   * ----------------------- */
  /** ✅ NUEVO: Validar Chart Generator */
  validateChartGenerator: (cfg) =>
    getCached("admin:chart-generator", TTL_FAST, async () => 
      api.admin.validateChartGenerator(cfg)
    ),

  /* -----------------------
   * Utilidades expandidas
   * ----------------------- */
  /**
   * ✅ init: warm-up completo para v11.0
   * Pre-carga TODOS los metadatos críticos
   */
  init: async (cfg) => {
    console.log(`[AdminService] 🚀 Iniciando warm-up v11.0...`);
    
    const tasks = [
      // ✅ System básico
      ["health", () => AdminService.ping(cfg)],
      ["root", () => AdminService.getRoot(cfg)],
      ["version", () => AdminService.getVersion(cfg)],
      
      // ✅ Catálogos
      ["periods", () => AdminService.getPeriods(cfg)],
      ["latestPeriod", () => AdminService.getLatestPeriod(cfg)],
      ["catalogs", () => AdminService.getCatalogs(cfg)],
      
      // ✅ Chat Agent v10.0
      ["chatStatus", () => AdminService.getChatStatus(cfg)],
      ["chatCapabilities", () => AdminService.getChatCapabilities(cfg)],
      
      // ✅ CDG Agent v6.0
      ["agentStatus", () => AdminService.getAgentStatus(cfg)],
      ["agentSpecializations", () => AdminService.getAgentSpecializations(cfg)],
      
      // ✅ Integration
      ["queryCatalogs", () => AdminService.getQueryCatalogs(cfg)],
      ["integrationCoordination", () => AdminService.getIntegrationCoordination(cfg)],
      
      // ✅ Charts
      ["chartsMeta", () => AdminService.getChartsMeta(cfg)],
      ["supportedChartTypes", () => AdminService.getSupportedChartTypes(cfg)],
      ["availableChartTypes", () => AdminService.getAvailableChartTypes(cfg)],
      ["availableChartQueries", () => AdminService.getAvailableChartQueries(cfg)],
      
      // ✅ Dashboards y Reports
      ["dashTemplates", () => AdminService.getDashboardTemplates(cfg)],
      ["reportsMeta", () => AdminService.getReportsMeta(cfg)],
      
      // ✅ Reflection
      ["reflectionInsights", () => AdminService.getReflectionInsights(cfg)],

      // ✅ Charts V4.4
      ["chartOptions", () => AdminService.getChartOptions("CONTROL_GESTION", cfg)],
          
      // ✅ Admin V4.4
      ["adminValidation", () => AdminService.validateChartGenerator(cfg)],

    ];

    const startTime = Date.now();
    const results = await Promise.allSettled(tasks.map(([, fn]) => fn()));
    const endTime = Date.now();
    
    const summary = {};
    const errors = [];

    results.forEach((res, i) => {
      const key = tasks[i][0];
      if (res.status === "fulfilled") {
        summary[key] = res.value;
      } else {
        summary[key] = null;
        errors.push({ 
          key, 
          error: res.reason instanceof Error ? res.reason.message : String(res.reason) 
        });
      }
    });

    const totalTime = endTime - startTime;
    const successCount = tasks.length - errors.length;
    
    console.log(`[AdminService] ✅ Warm-up completado: ${successCount}/${tasks.length} exitosos en ${totalTime}ms`);
    
    if (errors.length > 0) {
      console.warn(`[AdminService] ⚠️ Errores en warm-up:`, errors);
    }

    return { 
      ok: errors.length === 0, 
      summary, 
      errors,
      stats: {
        totalTasks: tasks.length,
        successful: successCount,
        failed: errors.length,
        executionTimeMs: totalTime
      }
    };
  },

  /**
   * ✅ NUEVO: healthCheck completo de todos los módulos
   */
  healthCheck: async (cfg) => {
    console.log(`[AdminService] 🏥 Ejecutando health check completo...`);
    
    const checks = [
      ["system", () => AdminService.ping(cfg)],
      ["chatAgent", () => AdminService.getChatStatus(cfg)],
      ["cdgAgent", () => AdminService.getAgentStatus(cfg)],
      ["integration", () => AdminService.getIntegrationCoordination(cfg)],
      ["charts", () => AdminService.validateCharts(cfg)],
      ["admin", () => AdminService.validateChartGenerator(cfg)],
    ];

    const results = await Promise.allSettled(checks.map(([, fn]) => fn()));
    const status = {};
    let overallHealthy = true;

    results.forEach((res, i) => {
      const key = checks[i][0];
      if (res.status === "fulfilled") {
        status[key] = { healthy: true, data: res.value };
      } else {
        status[key] = { healthy: false, error: res.reason?.message || String(res.reason) };
        overallHealthy = false;
      }
    });

    return {
      healthy: overallHealthy,
      timestamp: new Date().toISOString(),
      checks: status
    };
  },

  /**
   * openChatSocket: proxy optimizado para Chat Agent v10.0
   */
  openChatSocket: (userId, handlers) => api.chat.openSocket(userId, handlers),

  /* -----------------------
   * Cache management
   * ----------------------- */
  clearCache,
  
  getCacheStats: () => ({
    size: _cache.size,
    keys: Array.from(_cache.keys()),
    memory: _cache.size * 100 // estimación básica en bytes
  }),

  /* -----------------------
   * Passthrough de bajo nivel
   * ----------------------- */
  get apiBaseUrl() {
    return api.http.baseURL;
  },
  
  get rawClient() {
    return api.http.raw;
  },

  /* -----------------------
   * Utilidades de error mejoradas
   * ----------------------- */
  isApiError: (e) => e instanceof ApiClientError,
  
  /** ✅ NUEVO: Manejo de errores específicos por módulo */
  handleModuleError: (moduleName, error) => {
    console.error(`[AdminService] ❌ Error en módulo ${moduleName}:`, error);
    
    if (error instanceof ApiClientError) {
      return {
        module: moduleName,
        type: "api_error",
        status: error.status,
        message: error.message,
        detail: error.detail
      };
    }
    
    return {
      module: moduleName,
      type: "unknown_error", 
      message: error?.message || String(error)
    };
  },

  /* -----------------------
   * ✅ NUEVOS: Utilidades de monitoreo
   * ----------------------- */
  /** Monitor de estado en tiempo real */
  createStatusMonitor: (intervalMs = 30000) => {
    let isRunning = false;
    let intervalId = null;
    const listeners = new Set();

    const monitor = {
      start: () => {
        if (isRunning) return;
        isRunning = true;
        
        intervalId = setInterval(async () => {
          try {
            const status = await AdminService.healthCheck();
            listeners.forEach(listener => {
              try {
                listener(status);
              } catch (e) {
                console.error('[AdminService] Monitor listener error:', e);
              }
            });
          } catch (e) {
            console.error('[AdminService] Monitor check error:', e);
          }
        }, intervalMs);
        
        console.log(`[AdminService] 📊 Monitor iniciado (${intervalMs}ms)`);
      },
      
      stop: () => {
        if (!isRunning) return;
        isRunning = false;
        
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
        
        console.log(`[AdminService] 📊 Monitor detenido`);
      },
      
      onStatus: (listener) => {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
      
      get isRunning() { return isRunning; },
      get listenerCount() { return listeners.size; }
    };

    return monitor;
  },
};

export default AdminService;
