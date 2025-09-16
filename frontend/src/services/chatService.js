// frontend/src/services/chatService.js
/* eslint-disable no-console */

/**
 * ChatService v11.0 — Perfect Integration + Chart Pivoting (Chat Agent v10.0 + CDG Agent v6.0)
 * -------------------------------------------------------------------------------------------
 * - Integración completa con Chat Agent v10.0: clasificación inteligente + 6 catálogos
 * - Soporte para CDG Agent v6.0: análisis complejos especializados  
 * - Cliente WebSocket optimizado con heartbeat compatible
 * - Cola de salida inteligente y auto-reconexión exponencial
 * - API de eventos completa: 'open'|'ready'|'message'|'error'|'close'|'reconnect'|'typing'
 * - Atajos directos a Integration endpoints para perfect workflow
 * - Soporte completo para capabilities y specializations de ambos agentes
 * - ✅ NUEVO: Funciones específicas para pivoteo conversacional de gráficos
 * - ✅ NUEVO: Parser local de intenciones de pivoteo
 * - ✅ NUEVO: Separación clara entre chat general y pivoteo de gráficos
 */

import api, { 
  chat as chatApi, 
  agent as agentApi, 
  integration as integrationApi,
  charts as chartsApi,
  ApiClientError 
} from "./api";

/* =========================================
 * ✅ NUEVA CONFIGURACIÓN PARA PIVOTEO DE GRÁFICOS
 * ========================================= */

/**
 * ✅ Configuración centralizada para pivoteo de gráficos
 */
const PIVOT_CONFIG = {
  // Métricas disponibles para pivoteo
  metrics: {
    'CONTRATOS': { 
      label: 'Contratos',
      aliases: ['contratos', 'contrato'],
      apiEndpoint: 'charts.gestoresRanking',
      defaultParams: { metric: 'CONTRATOS' }
    },
    'CLIENTES': { 
      label: 'Clientes',
      aliases: ['clientes', 'cliente'],
      apiEndpoint: 'basic.clientesByGestor', 
      defaultParams: { metric: 'CLIENTES' }
    },
    'ROE': { 
      label: 'ROE (%)',
      aliases: ['roe', 'rentabilidad', 'rendimiento'],
      apiEndpoint: 'kpis.gestorROE',
      defaultParams: {}
    },
    'MARGEN_NETO': { 
      label: 'Margen Neto (%)',
      aliases: ['margen', 'margen neto', 'margenes'],
      apiEndpoint: 'comparatives.gestoresMargen',
      defaultParams: {}
    },
    'INGRESOS': { 
      label: 'Ingresos (€)',
      aliases: ['ingresos', 'ingresos totales', 'facturación'],
      apiEndpoint: 'analytics.gestorMetricasCompletas',
      defaultParams: {}
    },
    'INCENTIVOS': {
      label: 'Incentivos (€)',
      aliases: ['incentivos', 'bonus', 'bonificaciones'],
      apiEndpoint: 'incentives.bonusPool',
      defaultParams: {}
    }
  },

  // Dimensiones disponibles para pivoteo
  dimensions: {
    'gestor': { 
      label: 'Gestores',
      aliases: ['gestor', 'gestores', 'comercial', 'comerciales'],
      defaultChartType: 'horizontal_bar'
    },
    'centro': { 
      label: 'Centros',
      aliases: ['centro', 'centros', 'oficina', 'oficinas'],
      defaultChartType: 'donut'
    },
    'producto': { 
      label: 'Productos',
      aliases: ['producto', 'productos', 'servicio', 'servicios'],
      defaultChartType: 'horizontal_bar'
    },
    'cliente': { 
      label: 'Clientes',
      aliases: ['cliente', 'clientes'],
      defaultChartType: 'bar'
    },
    'segmento': { 
      label: 'Segmentos',
      aliases: ['segmento', 'segmentos'],
      defaultChartType: 'pie'
    }
  },

  // Tipos de gráfico disponibles
  chartTypes: {
    'bar': { 
      label: 'Barras',
      aliases: ['barras', 'barra', 'columnas']
    },
    'horizontal_bar': { 
      label: 'Barras Horizontales',
      aliases: ['horizontal', 'horizontales', 'barras horizontales']
    },
    'pie': { 
      label: 'Circular',
      aliases: ['circular', 'pie', 'tarta', 'quesito']
    },
    'donut': { 
      label: 'Donut',
      aliases: ['donut', 'anillo', 'rosquilla']
    },
    'line': { 
      label: 'Líneas',
      aliases: ['líneas', 'linea', 'temporal', 'evolución']
    },
    'area': { 
      label: 'Área',
      aliases: ['área', 'area', 'relleno']
    }
  }
};

/**
 * ✅ Parser local de intenciones de pivoteo
 */
function parsePivotIntent(message, currentConfig = {}) {
  const msg = message.toLowerCase().trim();
  
  console.log(`[ChatService] 🔍 Parsing pivot intent: "${msg}"`);
  console.log(`[ChatService] Current config:`, currentConfig);

  let newMetric = currentConfig.metric;
  let newDimension = currentConfig.dimension;
  let newChartType = currentConfig.chartType || currentConfig.chart_type;

  // Detectar cambios de métrica
  for (const [metricKey, metricConfig] of Object.entries(PIVOT_CONFIG.metrics)) {
    if (metricConfig.aliases.some(alias => msg.includes(alias))) {
      newMetric = metricKey;
      console.log(`[ChatService] ✅ Detected metric change: ${metricKey}`);
      break;
    }
  }

  // Detectar cambios de dimensión
  for (const [dimensionKey, dimensionConfig] of Object.entries(PIVOT_CONFIG.dimensions)) {
    if (dimensionConfig.aliases.some(alias => msg.includes(alias))) {
      newDimension = dimensionKey;
      console.log(`[ChatService] ✅ Detected dimension change: ${dimensionKey}`);
      break;
    }
  }

  // Detectar cambios de tipo de gráfico
  for (const [chartKey, chartConfig] of Object.entries(PIVOT_CONFIG.chartTypes)) {
    if (chartConfig.aliases.some(alias => msg.includes(alias))) {
      newChartType = chartKey;
      console.log(`[ChatService] ✅ Detected chart type change: ${chartKey}`);
      break;
    }
  }

  // Detectar palabras de comando de cambio
  const isChangeCommand = [
    'cambia', 'cambiar', 'muestra', 'mostrar', 'pon', 'poner', 
    'ver', 'visualiza', 'convierte', 'transforma'
  ].some(cmd => msg.includes(cmd));

  const hasChanges = (
    newMetric !== currentConfig.metric ||
    newDimension !== currentConfig.dimension ||
    newChartType !== (currentConfig.chartType || currentConfig.chart_type)
  );

  console.log(`[ChatService] Parse result:`, {
    isChangeCommand,
    hasChanges,
    newMetric,
    newDimension, 
    newChartType
  });

  if (isChangeCommand && hasChanges) {
    return {
      metric: newMetric,
      dimension: newDimension,
      chartType: newChartType,
      intent: 'pivot',
      confidence: 0.8
    };
  }

  return null;
}

/**
 * ✅ Valida si una combinación métrica/dimensión es soportada
 */
function validatePivotCombination(metric, dimension, chartType) {
  const metricConfig = PIVOT_CONFIG.metrics[metric];
  const dimensionConfig = PIVOT_CONFIG.dimensions[dimension];
  const chartTypeConfig = PIVOT_CONFIG.chartTypes[chartType];

  if (!metricConfig || !dimensionConfig || !chartTypeConfig) {
    return {
      valid: false,
      reason: `Combinación no soportada: ${metric} por ${dimension} como ${chartType}`
    };
  }

  return { valid: true };
}

/* =========================================
 * Utilidades actualizadas (MANTENIDAS)
 * ========================================= */

// Generador id pseudo-único mejorado
const uid = () =>
  `cdg_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 12)}`;

// ✅ Validación actualizada para Chat Agent v10.0
const buildChatPayload = ({
  user_id,
  message,
  gestor_id = undefined,
  periodo = undefined,
  include_charts = true,
  include_recommendations = true,
  context = {},
  current_chart_config = undefined,
  chart_interaction_type = undefined,
  use_basic_queries = true,
  quick_mode = false,
} = {}) => {
  if (!user_id) throw new Error("user_id es obligatorio en ChatRequest");
  if (!message || !String(message).trim()) {
    throw new Error("message no puede estar vacío");
  }
  return {
    user_id,
    message: String(message).trim(),
    gestor_id,
    periodo,
    include_charts,
    include_recommendations,
    context: context || {},
    current_chart_config,
    chart_interaction_type,
    use_basic_queries,
    quick_mode,
  };
};

// ✅ Normalización mejorada para Chat Agent v10.0
const normalizeChatData = (raw = {}) => {
  // Compatibilidad con diferentes formatos de respuesta
  const text =
    raw.text ||
    raw.response ||
    raw.content ||
    (typeof raw === "string" ? raw : raw?.data?.response) ||
    "";
  
  const charts = raw.charts || raw?.data?.charts || [];
  const recommendations = raw.recommendations || raw?.data?.recommendations || [];
  const metadata = raw.metadata || raw?.data?.metadata || {};
  
  // ✅ NUEVOS: Campos específicos del Chat Agent v10.0
  const responseType = raw.response_type || raw?.data?.response_type || "chat";
  const executionTime = raw.execution_time || raw?.data?.execution_time || 0;
  const confidenceScore = raw.confidence_score || raw?.data?.confidence_score || 0;
  
  return { 
    text, 
    charts, 
    recommendations, 
    metadata, 
    responseType,
    executionTime,
    confidenceScore,
    raw 
  };
};

/* =========================================
 * Cliente HTTP actualizado para v10.0 + v6.0 + PIVOTEO
 * ========================================= */

const httpChat = {
  /**
   * ✅ Envía mensaje al Chat Agent v10.0 con clasificación inteligente
   */
  async sendMessage(req) {
    const payload = buildChatPayload(req);
    const data = await chatApi.message(payload);
    return normalizeChatData(data);
  },

  /** ✅ Estado del Chat Agent v10.0 */
  status(cfg) {
    return chatApi.status(cfg);
  },

  /** ✅ NUEVO: Capacidades del Chat Agent v10.0 */
  capabilities(cfg) {
    return chatApi.capabilities(cfg);
  },

  /** Historial por usuario */
  history(userId, cfg) {
    if (!userId) throw new Error("userId requerido");
    return chatApi.history(userId, cfg);
  },

  /** Sugerencias dinámicas personalizadas */
  suggestions(userId, cfg) {
    if (!userId) throw new Error("userId requerido");
    return chatApi.suggestions(userId, cfg);
  },

  /** Reset de sesión */
  reset(userId, cfg) {
    if (!userId) throw new Error("userId requerido");
    return chatApi.reset(userId, cfg);
  },

  /* ===== ATAJOS PARA CDG AGENT v6.0 ===== */

  /** ✅ Análisis complejo especializado (CDG Agent v6.0) */
  async askComplexAnalysis(payload, cfg) {
    const data = await agentApi.complexAnalysis(payload, cfg);
    return data;
  },

  /** ✅ Procesamiento principal CDG Agent v6.0 */
  async askAgentProcess(payload, cfg) {
    const data = await agentApi.process(payload, cfg);
    return data;
  },

  /** ✅ Estado del CDG Agent v6.0 */
  agentStatus(cfg) {
    return agentApi.status(cfg);
  },

  /** ✅ NUEVO: Especializaciones del CDG Agent v6.0 */
  agentSpecializations(cfg) {
    return agentApi.specializations(cfg);
  },

  /** Sugerencias de preguntas especializadas */
  agentSuggestQuestions(userId, cfg) {
    return agentApi.suggestQuestions(userId, cfg);
  },

  /* ===== ATAJOS PARA INTEGRATION (Perfect Integration) ===== */

  /** ✅ NUEVO: Clasificación y enrutamiento inteligente */
  async classifyAndRoute(payload, cfg) {
    const data = await integrationApi.classifyAndRoute(payload, cfg);
    return data;
  },

  /** ✅ NUEVO: Ejecución directa de query predefinida */
  async executePredefined(payload, cfg) {
    const data = await integrationApi.executePredefined(payload, cfg);
    return data;
  },

  /** ✅ NUEVO: Catálogos de queries disponibles */
  queryCatalogs(cfg) {
    return integrationApi.queryCatalogs(cfg);
  },

  /** ✅ NUEVO: Estado de coordinación entre agentes */
  agentCoordination(cfg) {
    return integrationApi.agentCoordination(cfg);
  },

  /* ===== ✅ NUEVAS FUNCIONES PARA PIVOTEO DE GRÁFICOS ===== */

  /**
   * ✅ NUEVO: Pivoteo de gráfico mediante conversación
   */
  async pivotChart(userId, message, currentChartConfig = {}, options = {}) {
    console.log(`[ChatService] 🔄 Pivoting chart via conversation`);
    console.log(`[ChatService] Message: "${message}"`);
    console.log(`[ChatService] Current config:`, currentChartConfig);

    try {
      // 1. Intentar usar el backend para pivoteo
      const result = await chartsApi.pivot({
        userId,
        message,
        currentChartConfig,
        chartInteractionType: 'pivot'
      });

      console.log(`[ChatService] ✅ Backend pivot successful`);
      return {
        success: true,
        data: result,
        source: 'backend',
        newConfig: result.new_config || result.newConfig,
        changesMade: result.changes_made || result.changesMade
      };

    } catch (backendError) {
      console.warn(`[ChatService] ⚠️ Backend pivot failed, trying local parsing:`, backendError.message);

      // 2. Fallback: usar parser local
      const parsedIntent = parsePivotIntent(message, currentChartConfig);

      if (!parsedIntent) {
        throw new Error(`No se pudo interpretar la intención de pivoteo: "${message}"`);
      }

      // 3. Validar la combinación
      const validation = validatePivotCombination(
        parsedIntent.metric, 
        parsedIntent.dimension, 
        parsedIntent.chartType
      );

      if (!validation.valid) {
        throw new Error(validation.reason);
      }

      console.log(`[ChatService] ✅ Local parsing successful:`, parsedIntent);

      return {
        success: true,
        data: parsedIntent,
        source: 'local_parser',
        newConfig: {
          metric: parsedIntent.metric,
          dimension: parsedIntent.dimension,
          chartType: parsedIntent.chartType
        },
        changesMade: [`Pivoteo local: ${parsedIntent.metric} por ${parsedIntent.dimension} como ${parsedIntent.chartType}`]
      };
    }
  },

  /**
   * ✅ NUEVO: Obtener configuración de pivoteo disponible
   */
  getPivotConfig() {
    return {
      metrics: Object.keys(PIVOT_CONFIG.metrics),
      dimensions: Object.keys(PIVOT_CONFIG.dimensions),
      chartTypes: Object.keys(PIVOT_CONFIG.chartTypes),
      combinations: this.getValidCombinations()
    };
  },

  /**
   * ✅ NUEVO: Obtener combinaciones válidas
   */
  getValidCombinations() {
    const combinations = [];
    
    for (const metric of Object.keys(PIVOT_CONFIG.metrics)) {
      for (const dimension of Object.keys(PIVOT_CONFIG.dimensions)) {
        for (const chartType of Object.keys(PIVOT_CONFIG.chartTypes)) {
          const validation = validatePivotCombination(metric, dimension, chartType);
          if (validation.valid) {
            combinations.push({
              metric,
              dimension,
              chartType,
              label: `${PIVOT_CONFIG.metrics[metric].label} por ${PIVOT_CONFIG.dimensions[dimension].label} (${PIVOT_CONFIG.chartTypes[chartType].label})`
            });
          }
        }
      }
    }
    
    return combinations;
  },

  /**
   * ✅ NUEVO: Sugerencias de pivoteo basadas en configuración actual
   */
  getPivotSuggestions(currentConfig = {}) {
    const suggestions = [];
    
    // Sugerir cambios de métrica
    if (currentConfig.metric) {
      const otherMetrics = Object.keys(PIVOT_CONFIG.metrics).filter(m => m !== currentConfig.metric);
      otherMetrics.slice(0, 2).forEach(metric => {
        suggestions.push(`Cambia a ${PIVOT_CONFIG.metrics[metric].label.toLowerCase()}`);
      });
    }
    
    // Sugerir cambios de dimensión
    if (currentConfig.dimension) {
      const otherDimensions = Object.keys(PIVOT_CONFIG.dimensions).filter(d => d !== currentConfig.dimension);
      otherDimensions.slice(0, 2).forEach(dimension => {
        suggestions.push(`Muestra por ${PIVOT_CONFIG.dimensions[dimension].label.toLowerCase()}`);
      });
    }
    
    // Sugerir cambios de tipo de gráfico
    if (currentConfig.chartType) {
      const otherChartTypes = Object.keys(PIVOT_CONFIG.chartTypes).filter(c => c !== currentConfig.chartType);
      otherChartTypes.slice(0, 2).forEach(chartType => {
        suggestions.push(`Ponlo en ${PIVOT_CONFIG.chartTypes[chartType].label.toLowerCase()}`);
      });
    }
    
    return suggestions;
  }
};

/* =========================================
 * Cliente WebSocket optimizado para v10.0 (MANTENIDO)
 * ========================================= */

/**
 * ✅ Opciones optimizadas para Chat Agent v10.0 + CDG Agent v6.0
 */
const DEFAULT_WS_OPTS = {
  // Reconexión optimizada para Perfect Integration
  reconnect: true,
  maxRetries: 8, // ✅ Más reintentos para análisis largos
  backoffBaseMs: 800, // ✅ Más conservador
  heartbeatIntervalMs: 25000, // ✅ Compatible con servidor
  typingTimeoutMs: 2000, // ✅ Más tiempo para análisis complejos
  
  // ✅ NUEVO: Configuración específica para CDG Agent v6.0
  complexAnalysisTimeout: 45000, // 45s para análisis complejos
  enableIntegrationFlow: true,    // Habilitar flujo de integración
};

/**
 * ✅ ChatSocketClient optimizado para Chat Agent v10.0 + CDG Agent v6.0
 * 
 * Eventos actualizados:
 *   - 'integration-ready' : Perfect Integration establecida
 *   - 'complex-analysis'  : Análisis complejo iniciado/completado  
 *   - 'classification'    : Resultado de clasificación inteligente
 *   - 'chart-pivot'       : ✅ NUEVO: Resultado de pivoteo de gráfico
 */
class ChatSocketClient {
  constructor(userId, opts = {}) {
    if (!userId) throw new Error("userId requerido para ChatSocketClient");

    this.userId = userId;
    this.opts = { ...DEFAULT_WS_OPTS, ...opts };

    // ✅ Event listeners expandidos
    this.listeners = new Map();
    [
      "open", "ready", "message", "error", "close", "reconnect", "typing",
      "integration-ready", "complex-analysis", "classification", "chart-pivot" // ✅ NUEVO
    ].forEach((e) => this.listeners.set(e, new Set()));

    // Estado WS
    this.socket = null;
    this.connected = false;
    this.integrationReady = false; // ✅ NUEVO
    this.retries = 0;
    this.heartbeat = null;
    this.typingTimer = null;

    // Cola de mensajes mejorada
    this.outbox = [];

    // Callbacks opcionales
    if (opts.onMessage) this.on("message", opts.onMessage);
    if (opts.onOpen) this.on("open", opts.onOpen);
    if (opts.onClose) this.on("close", opts.onClose);
    if (opts.onError) this.on("error", opts.onError);
    
    // ✅ NUEVOS callbacks
    if (opts.onIntegrationReady) this.on("integration-ready", opts.onIntegrationReady);
    if (opts.onComplexAnalysis) this.on("complex-analysis", opts.onComplexAnalysis);
    if (opts.onChartPivot) this.on("chart-pivot", opts.onChartPivot); // ✅ NUEVO
  }

  /* ====== Pub/Sub mejorado ====== */

  on(event, fn) {
    const set = this.listeners.get(event);
    if (!set) throw new Error(`Evento desconocido: ${event}`);
    set.add(fn);
    return () => this.off(event, fn);
  }

  off(event, fn) {
    const set = this.listeners.get(event);
    if (set) set.delete(fn);
  }

  emit(event, payload) {
    const set = this.listeners.get(event);
    if (set && set.size) {
      set.forEach((fn) => {
        try {
          fn(payload);
        } catch (e) {
          console.error(`[ChatSocketClient] listener error (${event})`, e);
        }
      });
    }
  }

  /* ====== Conexión optimizada ====== */

  connect() {
    if (this.socket && this.connected) return this.socket;

    const { socket, sendJson, close } = chatApi.openSocket(this.userId, {
      onOpen: () => {
        console.log('[ChatService] ✅ Chat Agent v10.0 conectado');
        this.socket = socket;
        this.connected = true;
        this.retries = 0;

        this._startHeartbeat();
        this._flushOutbox();
        this.emit("open");
      },
      
      onMessage: (msg) => {
        // ✅ Manejo mejorado para Chat Agent v10.0 + CDG Agent v6.0
        if (msg?.type === "ready") {
          console.log(`[ChatService] 🎯 Perfect Integration: ${msg.chat_agent} + ${msg.cdg_agent}`);
          this.integrationReady = true;
          this.emit("ready", { 
            userId: this.userId, 
            chatAgent: msg.chat_agent,
            cdgAgent: msg.cdg_agent,
            integration: msg.integration,
            ts: msg.ts 
          });
          this.emit("integration-ready", { integration: msg.integration });
          return;
        }

        // ✅ NUEVO: Manejo de clasificación inteligente
        if (msg?.type === "classification") {
          this.emit("classification", {
            flowType: msg.flow_type,
            confidence: msg.confidence,
            routing: msg.routing
          });
          return;
        }

        // ✅ NUEVO: Manejo de análisis complejo
        if (msg?.type === "complex-analysis") {
          this.emit("complex-analysis", {
            status: msg.status,
            analysisType: msg.analysis_type,
            progress: msg.progress
          });
          return;
        }

        // ✅ NUEVO: Manejo de pivoteo de gráficos
        if (msg?.type === "chart-pivot") {
          this.emit("chart-pivot", {
            success: msg.success,
            newConfig: msg.new_config,
            changesMade: msg.changes_made,
            data: msg.data
          });
          return;
        }

        if (msg?.type === "pong") {
          console.log('[ChatService] 💚 Pong de Chat Agent v10.0');
          return;
        }

        if (msg?.type === "message") {
          this._toggleTyping(false);
          const normalized = normalizeChatData(msg.data);
          this.emit("message", normalized);
          return;
        }

        if (msg?.type === "fallback") {
          this._toggleTyping(false);
          this.emit("error", new ApiClientError(msg?.message || "fallback", { status: 200 }));
          return;
        }

        if (msg?.type === "error") {
          this._toggleTyping(false);
          this.emit("error", new ApiClientError(msg?.message || "error WS", { status: 400 }));
          return;
        }

        console.warn('[ChatService] ⚠️ Mensaje desconocido:', msg?.type);
      },
      
      onError: (evt) => {
        console.error('[ChatService] ❌ Error WebSocket:', evt);
        this.emit("error", evt instanceof Error ? evt : new Error("WS error"));
      },
      
      onClose: (evt) => {
        console.log(`[ChatService] 🔌 Desconectado: ${evt?.code}`);
        this.connected = false;
        this.integrationReady = false;
        this._stopHeartbeat();
        
        this.emit("close", {
          code: evt?.code,
          reason: evt?.reason,
          wasClean: evt?.wasClean,
        });

        if (this.opts.reconnect && this.retries < this.opts.maxRetries) {
          this._scheduleReconnect();
        }
      },
    });

    this.socket = socket;
    this._sendJson = sendJson;
    this._closeWs = close;
    return this.socket;
  }

  close() {
    this.opts.reconnect = false;
    this._stopHeartbeat();
    if (this.socket) {
      try {
        this._closeWs?.();
      } catch (_) {}
    }
    this.socket = null;
    this.connected = false;
    this.integrationReady = false;
  }

  /* ====== Mensajería mejorada ====== */

  /**
   * ✅ Envío optimizado para Chat Agent v10.0
   * Soporta contexto extendido para Perfect Integration
   */
  send(input) {
    const message = typeof input === "string" ? input : String(input?.message || "").trim();
    if (!message) throw new Error("message vacío");

    // ✅ Contexto extendido para Perfect Integration
    const context = typeof input === "object" ? {
      gestor_id: input.gestor_id,
      periodo: input.periodo,
      include_charts: input.include_charts !== false,
      include_recommendations: input.include_recommendations !== false,
      ...(input.context || {})
    } : {};

    const packet = { message, context };

    console.log('[ChatService] 📤 Enviando a Chat Agent v10.0:', packet);
    this._toggleTyping(true);

    if (this.connected && this.socket?.readyState === 1) {
      this._sendJson(packet);
    } else {
      console.log('[ChatService] 📦 Encolando mensaje...');
      this.outbox.push(packet);
      this.connect();
    }
  }

  /**
   * ✅ NUEVO: Envío de análisis complejo directo
   */
  sendComplexAnalysis(analysisType, params = {}) {
    const packet = {
      type: "complex-analysis",
      analysis_type: analysisType,
      params,
      context: { timestamp: Date.now() }
    };

    console.log('[ChatService] 🔬 Solicitando análisis complejo:', analysisType);
    
    if (this.connected && this.socket?.readyState === 1) {
      this._sendJson(packet);
    } else {
      this.outbox.push(packet);
      this.connect();
    }
  }

  /**
   * ✅ NUEVO: Envío de pivoteo de gráfico via WebSocket
   */
  sendChartPivot(message, currentConfig = {}) {
    const packet = {
      type: "chart-pivot",
      message,
      current_config: currentConfig,
      context: { timestamp: Date.now() }
    };

    console.log('[ChatService] 🔄 Solicitando pivoteo via WebSocket:', message);
    
    if (this.connected && this.socket?.readyState === 1) {
      this._sendJson(packet);
    } else {
      this.outbox.push(packet);
      this.connect();
    }
  }

  _flushOutbox() {
    if (!this.outbox.length || !this.connected || this.socket?.readyState !== 1) return;

    console.log(`[ChatService] 📦 Vaciando ${this.outbox.length} mensajes encolados`);
    const queued = [...this.outbox];
    this.outbox = [];
    queued.forEach((pkt) => this._sendJson(pkt));
  }

  /* ====== Reconexión exponencial mejorada (MANTENIDA) ====== */

  _scheduleReconnect() {
    if (!this.opts.reconnect || this.retries >= this.opts.maxRetries) {
      console.log('[ChatService] ❌ Máximos reintentos alcanzados');
      return;
    }
    
    const attempt = this.retries + 1;
    this.retries = attempt;

    const base = this.opts.backoffBaseMs || 800;
    const delay = Math.floor(base * Math.pow(1.5, attempt - 1)) + Math.floor(Math.random() * 300);

    console.log(`[ChatService] 🔄 Reintento ${attempt}/${this.opts.maxRetries} en ${delay}ms`);
    this.emit("reconnect", { attempt, delayMs: delay, maxRetries: this.opts.maxRetries });

    setTimeout(() => {
      if (this.opts.reconnect) {
        console.log(`[ChatService] 🔄 Ejecutando reintento ${attempt}`);
        this.connect();
      }
    }, delay);
  }

  /* ====== Heartbeat optimizado (MANTENIDO) ====== */

  _startHeartbeat() {
    this._stopHeartbeat();
    const interval = this.opts.heartbeatIntervalMs || 25000;
    
    this.heartbeat = setInterval(() => {
      if (this.socket?.readyState === 1) {
        this._sendJson({ type: "ping", ts: Date.now(), agent: "chat_v10" });
      }
    }, interval);
  }

  _stopHeartbeat() {
    if (this.heartbeat) {
      clearInterval(this.heartbeat);
      this.heartbeat = null;
    }
  }

  /* ====== Typing UX mejorado (MANTENIDO) ====== */

  _toggleTyping(active) {
    this.emit("typing", { active, integration: this.integrationReady });

    if (active) {
      if (this.typingTimer) clearTimeout(this.typingTimer);
      // ✅ Timeout extendido para análisis complejos
      const timeout = this.opts.complexAnalysisTimeout || 45000;
      this.typingTimer = setTimeout(() => {
        this.emit("typing", { active: false });
      }, timeout);
    } else if (this.typingTimer) {
      clearTimeout(this.typingTimer);
      this.typingTimer = null;
    }
  }
}

/* =========================================
 * API de alto nivel mejorada para v10.0 + v6.0 + PIVOTEO
 * ========================================= */

/**
 * ✅ Crea sesión de chat con Perfect Integration + Pivoteo
 */
function createChatSession(userId = uid(), options = {}) {
  const wsClient = new ChatSocketClient(userId, options);

  return {
    userId,

    // ✅ HTTP Chat Agent v10.0
    sendHttp: (req) => httpChat.sendMessage({ user_id: userId, ...req }),
    status: (cfg) => httpChat.status(cfg),
    capabilities: (cfg) => httpChat.capabilities(cfg), // ✅ NUEVO
    history: (cfg) => httpChat.history(userId, cfg),
    suggestions: (cfg) => httpChat.suggestions(userId, cfg),
    reset: (cfg) => httpChat.reset(userId, cfg),

    // ✅ HTTP CDG Agent v6.0
    askComplexAnalysis: (payload = {}, cfg) => 
      httpChat.askComplexAnalysis({ user_id: userId, ...payload }, cfg),
    askAgentProcess: (payload = {}, cfg) =>
      httpChat.askAgentProcess({ user_id: userId, ...payload }, cfg),
    agentStatus: (cfg) => httpChat.agentStatus(cfg),
    agentSpecializations: (cfg) => httpChat.agentSpecializations(cfg), // ✅ NUEVO
    agentSuggestQuestions: (cfg) => httpChat.agentSuggestQuestions(userId, cfg),

    // ✅ HTTP Integration (Perfect Integration)
    classifyAndRoute: (message, context = {}, cfg) =>
      httpChat.classifyAndRoute({ user_id: userId, message, ...context }, cfg),
    executePredefined: (payload = {}, cfg) =>
      httpChat.executePredefined({ user_id: userId, ...payload }, cfg),
    queryCatalogs: (cfg) => httpChat.queryCatalogs(cfg),
    agentCoordination: (cfg) => httpChat.agentCoordination(cfg),

    // ✅ NUEVAS funciones de pivoteo de gráficos
    pivotChart: (message, currentConfig = {}, options = {}) =>
      httpChat.pivotChart(userId, message, currentConfig, options),
    getPivotConfig: () => httpChat.getPivotConfig(),
    getValidCombinations: () => httpChat.getValidCombinations(),
    getPivotSuggestions: (currentConfig) => httpChat.getPivotSuggestions(currentConfig),

    // ✅ WebSocket mejorado
    ws: wsClient,
    connect: () => wsClient.connect(),
    send: (messageOrObj) => wsClient.send(messageOrObj),
    sendComplexAnalysis: (type, params) => wsClient.sendComplexAnalysis(type, params), // ✅ NUEVO
    sendChartPivot: (message, config) => wsClient.sendChartPivot(message, config), // ✅ NUEVO
    close: () => wsClient.close(),

    // Pub/Sub extendido
    on: (event, fn) => wsClient.on(event, fn),
    off: (event, fn) => wsClient.off(event, fn),

    // ✅ Propiedades de estado
    get connected() { return wsClient.connected; },
    get integrationReady() { return wsClient.integrationReady; }, // ✅ NUEVO
  };
}

/* =========================================
 * Exports actualizados con PIVOTEO
 * ========================================= */

const chatService = {
  http: httpChat,
  ChatSocketClient,
  createChatSession,
  normalizeChatData,
  buildChatPayload,
  
  // ✅ NUEVAS utilidades
  DEFAULT_WS_OPTS,
  uid,
  
  // ✅ NUEVAS funciones de pivoteo
  PIVOT_CONFIG,
  parsePivotIntent,
  validatePivotCombination,
};

export default chatService;

export {
  chatService,
  httpChat,
  ChatSocketClient,
  createChatSession,
  normalizeChatData,
  buildChatPayload,
  DEFAULT_WS_OPTS,
  uid,
  
  // ✅ NUEVAS exportaciones para pivoteo
  PIVOT_CONFIG,
  parsePivotIntent,
  validatePivotCombination,
};
