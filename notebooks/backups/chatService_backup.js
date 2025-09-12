// src/services/chatService.js
// Chat Service v3.0 - Integrado completamente con backend v3.0 y Chat Agent v7.0
// ✅ ACTUALIZADO: Basic Queries, Chart Generator avanzado, Reflection Pattern mejorado
// ✅ Compatible con: API v3.0, WebSocket mejorado, nuevos endpoints de personalización

import React, { useEffect, useCallback } from 'react';
import api, { chartAPI, basicAPI } from './api.js';

// ========================================
// 🌐 CONFIGURACIÓN Y CONSTANTES ACTUALIZADAS
// ========================================

const CHAT_CONFIG = {
  WEBSOCKET_URL: process.env.REACT_APP_CHAT_API_URL?.replace(/^http/, 'ws') || 'ws://localhost:8000',
  RECONNECT_ATTEMPTS: 6, // Aumentado para mayor resistencia
  RECONNECT_BASE_DELAY: 1000,
  HEARTBEAT_INTERVAL: 30000,
  REQUEST_TIMEOUT: 60000, // Aumentado para consultas complejas
  RETRY_ATTEMPTS: 3,
  // 🆕 NUEVAS CONFIGURACIONES
  BASIC_QUERIES_TIMEOUT: 5000, // Timeout específico para Basic Queries
  CHART_INTERACTION_TIMEOUT: 15000,
  MAX_CHART_SUGGESTIONS: 10
};

const CONNECTION_STATES = {
  CONNECTING: 'CONNECTING',
  OPEN: 'OPEN',
  CLOSING: 'CLOSING',
  CLOSED: 'CLOSED',
  RECONNECTING: 'RECONNECTING',
  // 🆕 NUEVO ESTADO
  OPTIMIZING: 'OPTIMIZING' // Para conexiones que se están optimizando
};

// ========================================
// 🎯 CLASE PRINCIPAL CHATSERVICE v3.0
// ========================================

class ChatService {
  constructor() {
    // WebSocket management
    this.wsConnection = null;
    this.connectionState = CONNECTION_STATES.CLOSED;
    this.reconnectAttempts = 0;
    this.heartbeatInterval = null;
    this.isConnecting = false;
    
    // Event handlers
    this.messageHandlers = [];
    this.stateChangeHandlers = [];
    this.errorHandlers = [];
    
    // 🆕 CHART GENERATOR v3.0 - Handlers especializados
    this.chartUpdateHandlers = [];
    this.pivotSuggestionHandlers = [];
    this.chartErrorHandlers = [];
    
    // 🆕 BASIC QUERIES - Handlers para respuestas rápidas
    this.quickResponseHandlers = [];
    this.basicQueryHandlers = [];
    
    // Chat features
    this.sessionId = this.getSessionId();
    this.currentUserId = 'frontend_user';
    
    // Performance tracking
    this.lastMessageTime = null;
    this.messageQueue = [];
    this.requestHistory = []; // 🆕 Para analytics
    
    // 🆕 FEATURES ACTUALIZADAS PARA v3.0
    this.features = {
      // Core features
      professionalPrompts: true,
      intentClassification: true,
      personalizedSuggestions: true,
      feedbackLearning: true,
      reflectionPattern: true,
      
      // Chart Generator features
      chartGeneration: true,
      chartPivoting: true,
      chartInteractionDetection: true,
      visualizationPreferences: true,
      
      // 🆕 NUEVAS FEATURES v3.0
      basicQueries: true,
      quickSummaries: true,
      fastRankings: true,
      drillDownNavigation: true,
      organizationalInsights: true,
      advancedPersonalization: true,
      multiAgentCoordination: true
    };

    // 🆕 CHART GENERATOR v3.0 - Estado avanzado
    this.currentChartConfig = null;
    this.chartHistory = []; // Historial de configuraciones
    this.chartPreferences = {
      preferred_chart_type: 'bar',
      chart_complexity: 'medium',
      interactive_mode: true,
      auto_pivot: false, // 🆕 Pivoteo automático
      smart_suggestions: true, // 🆕 Sugerencias inteligentes
      performance_mode: 'balanced' // 🆕 Modo de rendimiento
    };

    // 🆕 BASIC QUERIES - Configuración optimizada
    this.basicQueriesConfig = {
      enabled: true,
      cache_duration: 30000, // 30 segundos
      prefer_quick_responses: true,
      fallback_to_full_queries: true
    };

    // 🆕 PERSONALIZATION v3.0 - Estado avanzado
    this.userPreferences = {
      communication_style: 'professional',
      technical_level: 'intermediate',
      response_format: 'combined',
      chart_preferences: this.chartPreferences,
      basic_queries_enabled: true,
      quick_mode_default: false
    };

    // Auto-cleanup on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.cleanup());
    }
  }

  // ========================================
  // 🔧 CONFIGURACIÓN Y INICIALIZACIÓN v3.0
  // ========================================

  /**
   * Establece el ID del usuario actual con soporte mejorado
   * @param {string} userId - ID único del usuario
   */
  setCurrentUserId(userId) {
    this.currentUserId = userId;
    api.setCurrentUserId(userId);
    console.log(`👤 Usuario v3.0 establecido: ${userId}`);
    
    // 🆕 Cargar preferencias del usuario automáticamente
    this.loadUserPreferences(userId);
  }

  /**
   * 🆕 Carga preferencias del usuario desde el backend
   * @param {string} userId - ID del usuario
   */
  async loadUserPreferences(userId) {
    try {
      const preferences = await api.getUserPersonalization(userId);
      if (preferences && preferences.data) {
        this.userPreferences = { ...this.userPreferences, ...preferences.data };
        this.features = { ...this.features, ...preferences.features };
        console.log('⚙️ Preferencias de usuario cargadas:', this.userPreferences);
      }
    } catch (error) {
      console.warn('⚠️ No se pudieron cargar las preferencias del usuario:', error);
    }
  }

  getCurrentUserId() {
    return this.currentUserId;
  }

  /**
   * 🆕 Actualiza configuración del servicio con validación
   * @param {object} config - Nueva configuración
   */
  updateConfig(config) {
    const validKeys = Object.keys(CHAT_CONFIG);
    const filteredConfig = Object.keys(config)
      .filter(key => validKeys.includes(key))
      .reduce((obj, key) => {
        obj[key] = config[key];
        return obj;
      }, {});
    
    Object.assign(CHAT_CONFIG, filteredConfig);
    console.log('⚙️ Configuración v3.0 actualizada:', filteredConfig);
  }

  // ========================================
  // 💬 FUNCIONALIDADES DE CHAT v3.0 - MEJORADAS
  // ========================================

  /**
   * Envía un mensaje con procesamiento inteligente completo v3.0
   * @param {string} message - Mensaje del usuario
   * @param {object} options - Opciones avanzadas
   * @returns {Promise<Object>} Respuesta del agente
   */
  async sendMessage(message, options = {}) {
    if (!message?.trim()) {
      throw new Error('El mensaje no puede estar vacío');
    }

    // 🎯 DETECCIÓN INTELIGENTE v3.0
    const isChartInteraction = this.isChartCommand(message) && 
      (this.currentChartConfig || options.current_chart_config);
    const isBasicQuery = this.isBasicQuery(message);
    const isQuickRequest = options.quick_mode || this.shouldUseQuickMode(message);

    // 🎯 CONTEXTO ENRIQUECIDO v3.0
    const enhancedContext = {
      sessionId: this.sessionId,
      timestamp: new Date().toISOString(),
      features: this.features,
      source: 'frontend_react_v3',
      user_agent: 'chatservice_v3.0',
      interaction_type: this.classifyInteractionType(message, isChartInteraction, isBasicQuery),
      
      // Session context
      session_context: {
        previous_messages: this.messageQueue.length,
        user_id: this.currentUserId,
        connection_state: this.connectionState,
        user_preferences: this.userPreferences,
        request_history_length: this.requestHistory.length
      },
      
      // Chart context
      current_chart_config: this.currentChartConfig || options.current_chart_config,
      chart_interaction_type: isChartInteraction ? 'pivot' : options.chart_interaction_type,
      chart_preferences: this.chartPreferences,
      chart_interaction_detected: isChartInteraction,
      chart_history_count: this.chartHistory.length,
      
      // 🆕 BASIC QUERIES CONTEXT
      basic_query_detected: isBasicQuery,
      use_basic_queries: isBasicQuery || this.basicQueriesConfig.enabled,
      quick_mode: isQuickRequest,
      prefer_fast_response: isBasicQuery || isQuickRequest,
      
      // Enhanced context
      ...options.context
    };

    const enhancedOptions = {
      ...options,
      context: enhancedContext,
      includeCharts: options.includeCharts !== false,
      includeRecommendations: options.includeRecommendations !== false,
      
      // 🆕 v3.0 OPTIONS
      use_basic_queries: isBasicQuery || this.basicQueriesConfig.enabled,
      quick_mode: isQuickRequest,
      current_chart_config: this.currentChartConfig || options.current_chart_config,
      chart_interaction_type: isChartInteraction ? 'pivot' : options.chart_interaction_type,
      enhanced_processing: true,
      allow_auto_detection: true,
      allow_intent_enhancement: true
    };

    console.log('💬 Enviando mensaje v3.0 con contexto avanzado:', { 
      message: message.substring(0, 50) + '...', 
      isChartInteraction, 
      isBasicQuery,
      isQuickRequest,
      options: enhancedOptions 
    });

    try {
      const startTime = performance.now();
      let response;

      // 🎯 ROUTING INTELIGENTE v3.0
      if (isChartInteraction) {
        console.log('📊 Procesando interacción de gráfico...');
        response = await this.sendChartInteraction(message, this.currentChartConfig || options.current_chart_config);
      } else if (isBasicQuery && !options.force_full_processing) {
        console.log('🚀 Procesando con Basic Queries...');
        response = await this.sendBasicQuery(message, enhancedOptions);
      } else {
        // 🎯 PROCESAMIENTO COMPLETO CON FALLBACKS
        if (api.sendIntelligentMessage) {
          console.log('🧠 Intentando procesamiento inteligente...');
          try {
            response = await api.sendIntelligentMessage(message, enhancedContext);
          } catch (intelligentError) {
            console.warn('⚠️ Procesamiento inteligente falló, usando método estándar:', intelligentError.message);
            response = await api.sendChatMessage(message, enhancedOptions.gestorId, enhancedOptions);
          }
        } else {
          response = await api.sendChatMessage(message, enhancedOptions.gestorId, enhancedOptions);
        }
      }

      const processingTime = performance.now() - startTime;
      this.lastMessageTime = new Date();

      // 🆕 PROCESAMIENTO AVANZADO DE RESPUESTAS v3.0
      this.processAdvancedResponse(response);
      this.updateRequestHistory(message, response, processingTime);

      const processedResponse = {
        ...response,
        serviceMetadata: {
          userId: this.currentUserId,
          sessionId: this.sessionId,
          timestamp: new Date().toISOString(),
          processingTime: Math.round(processingTime),
          processingType: this.getProcessingType(isChartInteraction, isBasicQuery, isQuickRequest),
          features: this.features,
          chartInteraction: isChartInteraction,
          basicQueryUsed: isBasicQuery || response.basic_queries_used,
          quickMode: isQuickRequest,
          // 🆕 v3.0 METADATA
          apiVersion: '3.0',
          agentVersion: response.agent_version || 'v7.0',
          enhanced: true
        }
      };

      console.log('✅ Respuesta v3.0 procesada:', {
        processingTime: Math.round(processingTime),
        type: processedResponse.serviceMetadata.processingType,
        hasCharts: !!(response.chart_configs && response.chart_configs.length > 0),
        basicQueriesUsed: processedResponse.serviceMetadata.basicQueryUsed
      });

      return processedResponse;

    } catch (error) {
      console.error('❌ Error enviando mensaje v3.0:', error);
      return this.handleChatError(error);
    }
  }

  // ========================================
  // 🆕 MÉTODOS DE DETECCIÓN Y CLASIFICACIÓN v3.0
  // ========================================

  /**
   * 🆕 Detecta si un mensaje es una consulta básica
   * @param {string} message - Mensaje a analizar
   * @returns {boolean} True si es consulta básica
   */
  isBasicQuery(message) {
    const basicKeywords = [
      'resumen', 'summary', 'total', 'cuántos', 'cuantos', 'cantidad',
      'lista', 'listar', 'mostrar todos', 'ver todos', 'general',
      'rápido', 'quick', 'simple', 'básico', 'overview'
    ];
    
    const messageLower = message.toLowerCase();
    return basicKeywords.some(keyword => messageLower.includes(keyword)) ||
           message.length < 30; // Mensajes cortos probablemente son consultas básicas
  }

  /**
   * Detecta si un mensaje es un comando de gráfico (mejorado)
   * @param {string} message - Mensaje a analizar
   * @returns {boolean} True si es comando de gráfico
   */
  isChartCommand(message) {
    const chartKeywords = [
      'cambia', 'cambiar', 'modifica', 'modificar', 'convierte', 'convertir',
      'gráfico', 'chart', 'barras', 'línea', 'circular', 'pie', 'líneas',
      'mostrar', 'visualizar', 'ver en', 'como', 'tipo', 'formato',
      'pivotea', 'pivotear', 'transforma', 'transformar',
      // 🆕 NUEVAS PALABRAS CLAVE v3.0
      'representa', 'dibuja', 'genera gráfico', 'crear chart', 'plot', 'visualize'
    ];
    
    const messageLower = message.toLowerCase();
    return chartKeywords.some(keyword => messageLower.includes(keyword));
  }

  /**
   * 🆕 Determina si debería usar modo rápido
   * @param {string} message - Mensaje a analizar
   * @returns {boolean} True si debería usar modo rápido
   */
  shouldUseQuickMode(message) {
    return this.userPreferences.quick_mode_default || 
           message.includes('rápido') ||
           message.includes('quick') ||
           message.length < 20;
  }

  /**
   * 🆕 Clasifica el tipo de interacción
   * @param {string} message - Mensaje
   * @param {boolean} isChart - Es interacción de gráfico
   * @param {boolean} isBasic - Es consulta básica
   * @returns {string} Tipo de interacción
   */
  classifyInteractionType(message, isChart, isBasic) {
    if (isChart) return 'chart_interaction';
    if (isBasic) return 'basic_query';
    if (message.includes('ayuda')) return 'help_request';
    if (message.includes('configurar')) return 'configuration';
    return 'user_query';
  }

  /**
   * 🆕 Obtiene el tipo de procesamiento usado
   * @param {boolean} isChart - Fue interacción de gráfico
   * @param {boolean} isBasic - Fue consulta básica
   * @param {boolean} isQuick - Fue modo rápido
   * @returns {string} Tipo de procesamiento
   */
  getProcessingType(isChart, isBasic, isQuick) {
    if (isChart) return 'chart_interaction';
    if (isBasic) return 'basic_queries';
    if (isQuick) return 'quick_mode';
    return 'intelligent_standard';
  }

  // ========================================
  // 🆕 FUNCIONALIDADES BASIC QUERIES v3.0
  // ========================================

  /**
   * 🆕 Envía consulta básica optimizada
   * @param {string} message - Mensaje de consulta
   * @param {object} options - Opciones
   * @returns {Promise<Object>} Respuesta optimizada
   */
  async sendBasicQuery(message, options = {}) {
    try {
      console.log('🚀 Procesando consulta básica:', message);
      
      // Determinar tipo de consulta básica
      const queryType = this.classifyBasicQuery(message);
      
      let response;
      switch (queryType) {
        case 'summary':
          response = await basicAPI.getSummary();
          break;
        case 'ranking':
          const metric = this.extractMetricFromMessage(message);
          response = await basicAPI.getGestoresRanking(metric);
          break;
        case 'list_gestores':
          response = await basicAPI.getGestoresList();
          break;
        case 'list_centros':
          response = await basicAPI.getCentros();
          break;
        case 'list_productos':
          response = await basicAPI.getProductos();
          break;
        default:
          // Fallback a procesamiento estándar
          return await api.sendChatMessage(message, options.gestorId, options);
      }

      // Procesar respuesta de Basic Query
      const processedResponse = {
        ...response,
        response: this.formatBasicQueryResponse(response, queryType),
        basic_queries_used: true,
        processing_type: 'basic_queries',
        query_type: queryType,
        fast_response: true
      };

      // Notificar handlers
      this.notifyBasicQueryHandlers(processedResponse);

      return processedResponse;

    } catch (error) {
      console.warn('⚠️ Error en Basic Query, fallback a procesamiento estándar:', error);
      // Fallback automático
      return await api.sendChatMessage(message, options.gestorId, options);
    }
  }

  /**
   * 🆕 Clasifica el tipo de consulta básica
   * @param {string} message - Mensaje a clasificar
   * @returns {string} Tipo de consulta
   */
  classifyBasicQuery(message) {
    const lower = message.toLowerCase();
    
    if (lower.includes('resumen') || lower.includes('summary')) return 'summary';
    if (lower.includes('ranking') || lower.includes('mejor')) return 'ranking';
    if (lower.includes('gestores') && lower.includes('lista')) return 'list_gestores';
    if (lower.includes('centros')) return 'list_centros';
    if (lower.includes('productos')) return 'list_productos';
    
    return 'general';
  }

  /**
   * 🆕 Extrae métrica del mensaje para ranking
   * @param {string} message - Mensaje
   * @returns {string} Métrica extraída
   */
  extractMetricFromMessage(message) {
    const lower = message.toLowerCase();
    
    if (lower.includes('contratos')) return 'contratos';
    if (lower.includes('margen')) return 'margen';
    if (lower.includes('clientes')) return 'clientes';
    if (lower.includes('roe')) return 'roe';
    
    return 'contratos'; // Default
  }

  /**
   * 🆕 Formatea respuesta de Basic Query
   * @param {object} response - Respuesta raw
   * @param {string} queryType - Tipo de consulta
   * @returns {string} Respuesta formateada
   */
  formatBasicQueryResponse(response, queryType) {
    switch (queryType) {
      case 'summary':
        return `📊 **Resumen General del Sistema**\n\n` +
               `• **Gestores Activos:** ${response.summary?.total_gestores || 0}\n` +
               `• **Clientes Total:** ${response.summary?.total_clientes || 0}\n` +
               `• **Contratos Activos:** ${response.summary?.total_contratos || 0}\n\n` +
               `✅ Datos obtenidos con **Basic Queries** para mayor velocidad.`;
               
      case 'ranking':
        const ranking = response.ranking || [];
        if (ranking.length === 0) return 'No hay datos de ranking disponibles.';
        
        let rankingText = `🏆 **Top Gestores por ${response.metric || 'Performance'}**\n\n`;
        ranking.slice(0, 10).forEach((gestor, index) => {
          rankingText += `${index + 1}. **${gestor.nombre}** - ${gestor.valor}\n`;
        });
        return rankingText;
        
      default:
        return 'Información procesada con Basic Queries.';
    }
  }

  // ========================================
  // 🆕 CHART GENERATOR v3.0 - FUNCIONALIDADES AVANZADAS
  // ========================================

  /**
   * Envía interacción específica con gráficos (mejorado v3.0)
   * @param {string} message - Mensaje de interacción
   * @param {object} currentChartConfig - Configuración actual del gráfico
   * @returns {Promise<Object>} Respuesta de la interacción
   */
  async sendChartInteraction(message, currentChartConfig) {
    try {
      console.log('📊 Enviando interacción de gráfico v3.0:', { message, currentChartConfig });
      
      const response = await chartAPI.sendChartInteraction(message, this.currentUserId, currentChartConfig);
      
      // 🆕 Actualizar historial de gráficos
      if (response.chart_configs && response.chart_configs.length > 0) {
        this.currentChartConfig = response.chart_configs[0];
        this.updateChartHistory(this.currentChartConfig);
        this.notifyChartUpdateHandlers(response.chart_configs);
      }

      // 🆕 Procesar sugerencias automáticas si están habilitadas
      if (this.chartPreferences.smart_suggestions && response.pivot_suggestions) {
        this.notifyPivotSuggestionHandlers(response.pivot_suggestions);
      }

      return response;
    } catch (error) {
      console.error('❌ Error en interacción de gráfico v3.0:', error);
      this.notifyChartErrorHandlers(error);
      throw error;
    }
  }

  /**
   * Solicita generación de gráfico desde datos (mejorado v3.0)
   * @param {string} message - Mensaje descriptivo
   * @param {Array} data - Datos para el gráfico
   * @param {object} config - Configuración del gráfico
   * @returns {Promise<Object>} Gráfico generado
   */
  async requestChartGeneration(message, data, config) {
    try {
      console.log('🎨 Solicitando generación de gráfico v3.0:', { message, data, config });
      
      // 🆕 Aplicar preferencias del usuario automáticamente
      const enhancedConfig = {
        chart_type: this.chartPreferences.preferred_chart_type,
        interactive: this.chartPreferences.interactive_mode,
        complexity: this.chartPreferences.chart_complexity,
        ...config
      };
      
      const response = await chartAPI.requestChartGeneration(message, this.currentUserId, data, enhancedConfig);
      
      // Actualizar configuración local y historial
      if (response.chart_configs && response.chart_configs.length > 0) {
        this.currentChartConfig = response.chart_configs[0];
        this.updateChartHistory(this.currentChartConfig);
        this.notifyChartUpdateHandlers(response.chart_configs);
      }

      return response;
    } catch (error) {
      console.error('❌ Error generando gráfico v3.0:', error);
      this.notifyChartErrorHandlers(error);
      throw error;
    }
  }

  /**
   * 🆕 Actualiza historial de gráficos
   * @param {object} chartConfig - Configuración del gráfico
   */
  updateChartHistory(chartConfig) {
    this.chartHistory.push({
      config: chartConfig,
      timestamp: new Date().toISOString(),
      user_id: this.currentUserId
    });
    
    // Mantener solo los últimos 20 gráficos
    if (this.chartHistory.length > 20) {
      this.chartHistory = this.chartHistory.slice(-20);
    }
  }

  /**
   * Realiza pivoteo directo de gráfico (mejorado v3.0)
   * @param {string} pivotMessage - Mensaje de pivoteo
   * @param {object} currentConfig - Configuración actual
   * @returns {Promise<Object>} Resultado del pivoteo
   */
  async pivotChart(pivotMessage, currentConfig = null) {
    try {
      console.log('🔄 Pivoteando gráfico v3.0:', { pivotMessage, currentConfig });
      
      const config = currentConfig || this.currentChartConfig;
      if (!config) {
        throw new Error('No hay configuración de gráfico actual para pivotear');
      }

      const response = await chartAPI.pivotChart(this.currentUserId, {
        message: pivotMessage,
        current_chart_config: config,
        chart_interaction_type: 'pivot',
        // 🆕 Incluir preferencias del usuario
        user_preferences: this.chartPreferences
      });

      // Actualizar configuración si el pivoteo fue exitoso
      if (response.pivot_result?.status === 'success' && response.pivot_result.new_config) {
        this.currentChartConfig = response.pivot_result.new_config;
        this.updateChartHistory(this.currentChartConfig);
        this.notifyChartUpdateHandlers([this.currentChartConfig]);
      }

      return response;
    } catch (error) {
      console.error('❌ Error en pivoteo v3.0:', error);
      this.notifyChartErrorHandlers(error);
      throw error;
    }
  }

  /**
   * Obtiene sugerencias de pivoteo para el gráfico actual (mejorado v3.0)
   * @param {string} chartType - Tipo de gráfico (opcional)
   * @returns {Promise<Array>} Lista de sugerencias
   */
  async getChartSuggestions(chartType = null) {
    try {
      console.log('💡 Obteniendo sugerencias de gráfico v3.0...');
      
      const currentType = chartType || this.currentChartConfig?.chart_type;
      const response = await chartAPI.getChartSuggestions(this.currentUserId, currentType);
      
      if (response.suggestions && response.suggestions.length > 0) {
        // 🆕 Filtrar sugerencias basadas en preferencias
        const filteredSuggestions = this.filterSuggestionsByPreferences(response.suggestions);
        this.notifyPivotSuggestionHandlers(filteredSuggestions);
        
        return {
          ...response,
          suggestions: filteredSuggestions,
          filtered: true
        };
      }

      return response;
    } catch (error) {
      console.error('❌ Error obteniendo sugerencias v3.0:', error);
      return { 
        suggestions: [], 
        chart_generator_available: false,
        error: error.message 
      };
    }
  }

  /**
   * 🆕 Filtra sugerencias basadas en preferencias del usuario
   * @param {Array} suggestions - Lista de sugerencias
   * @returns {Array} Sugerencias filtradas
   */
  filterSuggestionsByPreferences(suggestions) {
    return suggestions
      .filter(suggestion => {
        // Filtrar por complejidad
        if (this.chartPreferences.chart_complexity === 'simple' && suggestion.complexity === 'complex') {
          return false;
        }
        return true;
      })
      .slice(0, CHAT_CONFIG.MAX_CHART_SUGGESTIONS);
  }

  /**
   * Genera gráfico desde endpoint de datos existente (mejorado v3.0)
   * @param {string} endpoint - Endpoint de datos
   * @param {object} chartConfig - Configuración del gráfico
   * @param {object} params - Parámetros del endpoint
   * @returns {Promise<Object>} Gráfico generado
   */
  async generateChartFromEndpoint(endpoint, chartConfig = {}, params = {}) {
    try {
      console.log('🔗 Generando gráfico desde endpoint v3.0:', endpoint);
      
      // 🆕 Aplicar configuración inteligente basada en endpoint
      const intelligentConfig = this.getIntelligentConfigForEndpoint(endpoint, chartConfig);
      
      const response = await chartAPI.generateChartFromEndpoint(endpoint, intelligentConfig, params);
      
      // Actualizar configuración local
      if (response.chart && response.chart.config) {
        this.currentChartConfig = response.chart.config;
        this.updateChartHistory(response.chart.config);
        this.notifyChartUpdateHandlers([response.chart]);
      }

      return response;
    } catch (error) {
      console.error('❌ Error generando gráfico desde endpoint v3.0:', error);
      this.notifyChartErrorHandlers(error);
      throw error;
    }
  }

  /**
   * 🆕 Obtiene configuración inteligente para un endpoint específico
   * @param {string} endpoint - Endpoint
   * @param {object} baseConfig - Configuración base
   * @returns {object} Configuración optimizada
   */
  getIntelligentConfigForEndpoint(endpoint, baseConfig) {
    const endpointConfigs = {
      '/analisis-comparativo': {
        chart_type: 'bar',
        dimension: 'gestor',
        metric: 'performance',
        interactive: true
      },
      '/kpis/consolidados': {
        chart_type: 'line',
        show_trend: true,
        interactive: true
      },
      '/deviations/alerts': {
        chart_type: 'scatter',
        color_by_deviation: true,
        interactive: true
      }
    };

    return {
      ...endpointConfigs[endpoint],
      ...baseConfig,
      user_preferences: this.chartPreferences
    };
  }

  /**
   * Actualiza preferencias de gráficos (mejorado v3.0)
   * @param {object} preferences - Nuevas preferencias
   */
  updateChartPreferences(preferences) {
    this.chartPreferences = { ...this.chartPreferences, ...preferences };
    console.log('🎨 Preferencias de gráficos v3.0 actualizadas:', this.chartPreferences);
    
    // 🆕 Sincronizar con el backend
    this.syncChartPreferencesWithBackend(preferences);
  }

  /**
   * 🆕 Sincroniza preferencias de gráficos con el backend
   * @param {object} preferences - Preferencias a sincronizar
   */
  async syncChartPreferencesWithBackend(preferences) {
    try {
      await api.updateUserPersonalization(this.currentUserId, {
        chart_preferences: preferences
      });
      console.log('✅ Preferencias de gráficos sincronizadas con backend');
    } catch (error) {
      console.warn('⚠️ No se pudieron sincronizar preferencias de gráficos:', error);
    }
  }

  // ========================================
  // 🆕 PROCESAMIENTO AVANZADO DE RESPUESTAS v3.0
  // ========================================

  /**
   * 🆕 Procesa respuesta avanzada con múltiples tipos de contenido
   * @param {object} response - Respuesta a procesar
   */
  processAdvancedResponse(response) {
    try {
      // Procesar gráficos
      this.processChartResponse(response);
      
      // 🆕 Procesar Basic Queries
      if (response.basic_queries_used) {
        this.notifyBasicQueryHandlers(response);
      }
      
      // 🆕 Procesar respuestas rápidas
      if (response.quick_response || response.fast_response) {
        this.notifyQuickResponseHandlers(response);
      }
      
      // 🆕 Procesar insights organizacionales
      if (response.organizational_insights) {
        console.log('🏢 Insights organizacionales recibidos:', response.organizational_insights);
      }
      
      // 🆕 Procesar recomendaciones personalizadas
      if (response.personalized_recommendations) {
        console.log('🎯 Recomendaciones personalizadas:', response.personalized_recommendations);
      }

    } catch (error) {
      console.error('❌ Error procesando respuesta avanzada:', error);
    }
  }

  /**
   * Procesa respuesta que puede contener información de gráficos (mejorado v3.0)
   * @param {object} response - Respuesta a procesar
   */
  processChartResponse(response) {
    try {
      // Procesar configuraciones de gráficos
      if (response.chart_configs && response.chart_configs.length > 0) {
        this.currentChartConfig = response.chart_configs[response.chart_configs.length - 1];
        this.updateChartHistory(this.currentChartConfig); // 🆕 Actualizar historial
        this.notifyChartUpdateHandlers(response.chart_configs);
        console.log('📊 Configuración de gráfico v3.0 actualizada:', this.currentChartConfig);
      }

      // Procesar sugerencias de pivoteo
      if (response.pivot_suggestions && response.pivot_suggestions.length > 0) {
        // 🆕 Filtrar por preferencias antes de notificar
        const filteredSuggestions = this.filterSuggestionsByPreferences(response.pivot_suggestions);
        this.notifyPivotSuggestionHandlers(filteredSuggestions);
        console.log('💡 Sugerencias de pivoteo v3.0 recibidas:', filteredSuggestions.length);
      }

      // Procesar gráficos directos
      if (response.charts && response.charts.length > 0) {
        response.charts.forEach(chart => {
          if (chart.config) {
            this.currentChartConfig = chart.config;
            this.updateChartHistory(chart.config); // 🆕 Actualizar historial
          }
        });
        this.notifyChartUpdateHandlers(response.charts);
      }

      // 🆕 Procesar errores de gráficos
      if (response.chart_errors && response.chart_errors.length > 0) {
        response.chart_errors.forEach(error => {
          this.notifyChartErrorHandlers(new Error(error.message || 'Error de gráfico desconocido'));
        });
      }

    } catch (error) {
      console.error('❌ Error procesando respuesta de gráfico v3.0:', error);
      this.notifyChartErrorHandlers(error);
    }
  }

  /**
   * 🆕 Actualiza historial de requests para analytics
   * @param {string} message - Mensaje enviado
   * @param {object} response - Respuesta recibida
   * @param {number} processingTime - Tiempo de procesamiento
   */
  updateRequestHistory(message, response, processingTime) {
    this.requestHistory.push({
      timestamp: new Date().toISOString(),
      message: message.substring(0, 100), // Solo primeros 100 caracteres
      processingTime,
      responseType: response.processing_type || 'standard',
      success: !response.error,
      userId: this.currentUserId,
      sessionId: this.sessionId
    });

    // Mantener solo los últimos 100 requests
    if (this.requestHistory.length > 100) {
      this.requestHistory = this.requestHistory.slice(-100);
    }
  }

  // ========================================
  // 🚀 FUNCIONALIDADES AVANZADAS v3.0
  // ========================================

  /**
   * 🆕 Envía feedback específico con soporte completo v3.0
   * @param {object} feedback - Datos del feedback
   * @returns {Promise<Object>} Resultado del procesamiento
   */
  async sendChatFeedback(feedback) {
    try {
      console.log('📝 Enviando feedback v3.0:', feedback);
      
      // 🆕 Feedback enriquecido
      const enhancedFeedback = {
        ...feedback,
        chart_rating: feedback.chart_rating,
        visualization_comments: feedback.visualization_comments,
        chart_interaction_satisfaction: feedback.chart_interaction_satisfaction,
        // 🆕 v3.0 FEEDBACK FIELDS
        basic_queries_rating: feedback.basic_queries_rating,
        quick_response_rating: feedback.quick_response_rating,
        overall_experience_rating: feedback.overall_experience_rating,
        feature_satisfaction: {
          chart_generation: feedback.chart_generation_satisfaction,
          basic_queries: feedback.basic_queries_satisfaction,
          personalization: feedback.personalization_satisfaction,
          response_speed: feedback.response_speed_satisfaction
        },
        user_preferences: this.userPreferences,
        session_context: {
          requests_count: this.requestHistory.length,
          charts_generated: this.chartHistory.length,
          session_duration: this.getSessionDuration()
        }
      };

      const response = await api.sendChatFeedback(this.currentUserId, enhancedFeedback);
      
      // 🆕 Actualizar features basado en feedback
      if (response.personalization_updated) {
        await this.refreshUserPreferences();
      }

      // 🆕 Actualizar configuración local si hay cambios sugeridos
      if (response.suggested_preferences) {
        this.applyFeedbackBasedPreferences(response.suggested_preferences);
      }
      
      return response;
    } catch (error) {
      console.error('❌ Error enviando feedback v3.0:', error);
      throw error;
    }
  }

  /**
   * 🆕 Aplica preferencias basadas en feedback
   * @param {object} suggestedPreferences - Preferencias sugeridas
   */
  applyFeedbackBasedPreferences(suggestedPreferences) {
    if (suggestedPreferences.chart_preferences) {
      this.updateChartPreferences(suggestedPreferences.chart_preferences);
    }
    
    if (suggestedPreferences.basic_queries_config) {
      this.basicQueriesConfig = {
        ...this.basicQueriesConfig,
        ...suggestedPreferences.basic_queries_config
      };
    }
    
    console.log('🎯 Preferencias aplicadas basadas en feedback');
  }

  /**
   * Obtiene sugerencias personalizadas dinámicas (mejorado v3.0)
   * @returns {Promise<Array>} Lista de sugerencias
   */
  async getChatSuggestions() {
    try {
      console.log('💡 Obteniendo sugerencias personalizadas v3.0...');
      const response = await api.getChatSuggestions(this.currentUserId);
      
      // 🆕 Enriquecer con contexto local
      const enrichedSuggestions = {
        suggestions: response.suggestions || [],
        personalized: response.personalized || false,
        total: response.total || 0,
        chart_generator_available: response.chart_generator_available || false,
        basic_queries_available: response.basic_queries_available || false,
        // 🆕 v3.0 FIELDS
        quick_suggestions: this.generateQuickSuggestions(),
        chart_suggestions: this.generateChartSuggestions(),
        context_aware: true,
        timestamp: response.timestamp
      };

      return enrichedSuggestions;
    } catch (error) {
      console.error('❌ Error obteniendo sugerencias v3.0:', error);
      // 🆕 Fallback mejorado con sugerencias contextuales
      return {
        suggestions: this.getFallbackSuggestions(),
        personalized: false,
        total: this.getFallbackSuggestions().length,
        source: 'fallback_v3'
      };
    }
  }

  /**
   * 🆕 Genera sugerencias rápidas basadas en contexto
   * @returns {Array} Sugerencias rápidas
   */
  generateQuickSuggestions() {
    const suggestions = [
      'Resumen general del sistema',
      'Top 5 gestores por contratos',
      'Lista de centros activos'
    ];

    // Añadir sugerencias basadas en historial
    if (this.chartHistory.length > 0) {
      suggestions.push('Recrear último gráfico');
    }

    if (this.requestHistory.length > 5) {
      suggestions.push('Análisis de mi actividad reciente');
    }

    return suggestions.slice(0, 5);
  }

  /**
   * 🆕 Genera sugerencias de gráficos basadas en contexto
   * @returns {Array} Sugerencias de gráficos
   */
  generateChartSuggestions() {
    const suggestions = [];

    if (this.currentChartConfig) {
      const currentType = this.currentChartConfig.chart_type;
      if (currentType === 'bar') {
        suggestions.push('Convertir a gráfico de líneas');
        suggestions.push('Mostrar como gráfico circular');
      } else if (currentType === 'line') {
        suggestions.push('Cambiar a gráfico de barras');
        suggestions.push('Ver como gráfico de área');
      }
    } else {
      suggestions.push('Crear gráfico comparativo de gestores');
      suggestions.push('Visualizar tendencias mensuales');
    }

    return suggestions.slice(0, 3);
  }

  /**
   * 🆕 Obtiene sugerencias de fallback mejoradas
   * @returns {Array} Sugerencias de fallback
   */
  getFallbackSuggestions() {
    return [
      "¿Cómo está mi rendimiento este mes?",
      "Comparar con otros gestores",
      "Detectar alertas automáticamente",
      "Análisis de desviaciones críticas",
      "Generar Business Review",
      // 🆕 SUGERENCIAS v3.0
      "Resumen rápido del sistema",
      "Mostrar datos en gráfico de barras",
      "Crear gráfico comparativo de gestores",
      "Ver evolución temporal en líneas",
      "Lista de gestores por performance",
      "Configurar mis preferencias",
      "Ayuda con comandos disponibles"
    ];
  }

  // ========================================
  // 📊 HANDLERS Y EVENTOS v3.0 - EXTENDIDOS
  // ========================================

  // Handlers existentes
  onMessage(handler) { this.messageHandlers.push(handler); }
  onStateChange(handler) { this.stateChangeHandlers.push(handler); }
  onError(handler) { this.errorHandlers.push(handler); }
  onChartUpdate(handler) { this.chartUpdateHandlers.push(handler); }
  onPivotSuggestion(handler) { this.pivotSuggestionHandlers.push(handler); }

  // 🆕 NUEVOS HANDLERS v3.0
  onQuickResponse(handler) { this.quickResponseHandlers.push(handler); }
  onBasicQuery(handler) { this.basicQueryHandlers.push(handler); }
  onChartError(handler) { this.chartErrorHandlers.push(handler); }

  // Notificadores
  notifyMessageHandlers(message) {
    this.messageHandlers.forEach(handler => {
      try { handler(message); } catch (error) { 
        console.error('❌ Error en message handler:', error); 
      }
    });
  }

  notifyStateChange(newState) {
    this.stateChangeHandlers.forEach(handler => {
      try { handler(newState, this.connectionState); } catch (error) { 
        console.error('❌ Error en state change handler:', error); 
      }
    });
  }

  notifyErrorHandlers(error) {
    this.errorHandlers.forEach(handler => {
      try { handler(error); } catch (e) { 
        console.error('❌ Error en error handler:', e); 
      }
    });
  }

  notifyChartUpdateHandlers(charts) {
    this.chartUpdateHandlers.forEach(handler => {
      try { handler(charts); } catch (error) { 
        console.error('❌ Error en chart update handler:', error); 
      }
    });
  }

  notifyPivotSuggestionHandlers(suggestions) {
    this.pivotSuggestionHandlers.forEach(handler => {
      try { handler(suggestions); } catch (error) { 
        console.error('❌ Error en pivot suggestion handler:', error); 
      }
    });
  }

  // 🆕 NUEVOS NOTIFICADORES v3.0
  notifyQuickResponseHandlers(response) {
    this.quickResponseHandlers.forEach(handler => {
      try { handler(response); } catch (error) { 
        console.error('❌ Error en quick response handler:', error); 
      }
    });
  }

  notifyBasicQueryHandlers(response) {
    this.basicQueryHandlers.forEach(handler => {
      try { handler(response); } catch (error) { 
        console.error('❌ Error en basic query handler:', error); 
      }
    });
  }

  notifyChartErrorHandlers(error) {
    this.chartErrorHandlers.forEach(handler => {
      try { handler(error); } catch (e) { 
        console.error('❌ Error en chart error handler:', e); 
      }
    });
  }

  // ========================================
  // 🌐 GESTIÓN WEBSOCKET v3.0 - MEJORADA
  // ========================================

  /**
   * Conecta WebSocket con manejo avanzado de estados v3.0
   * @param {Function} onMessage - Callback para mensajes
   * @param {Function} onError - Callback para errores
   * @param {Function} onClose - Callback para cierre
   * @param {Function} onChartUpdate - Callback para actualizaciones de gráficos
   * @param {Function} onQuickResponse - 🆕 Callback para respuestas rápidas
   * @returns {Promise<WebSocket>} Conexión WebSocket
   */
  async connectWebSocket(onMessage, onError = null, onClose = null, onChartUpdate = null, onQuickResponse = null) {
    if (this.isConnecting || this.connectionState === CONNECTION_STATES.OPEN) {
      console.log('🔗 WebSocket ya conectado o conectándose');
      return this.wsConnection;
    }

    return new Promise((resolve, reject) => {
      try {
        this.isConnecting = true;
        this.connectionState = CONNECTION_STATES.CONNECTING;
        this.notifyStateChange(CONNECTION_STATES.CONNECTING);

        const wsUrl = `${CHAT_CONFIG.WEBSOCKET_URL}/ws/${this.currentUserId}`;
        console.log(`🌐 Conectando WebSocket v3.0 con soporte avanzado: ${wsUrl}`);
        
        this.wsConnection = new WebSocket(wsUrl);

        this.wsConnection.onopen = () => {
          console.log('✅ WebSocket v3.0 conectado exitosamente');
          this.connectionState = CONNECTION_STATES.OPEN;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.notifyStateChange(CONNECTION_STATES.OPEN);
          this.processMessageQueue();
          
          // 🆕 Enviar información de capabilities al conectar
          this.sendCapabilityInfo();
          
          resolve(this.wsConnection);
        };

        this.wsConnection.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'heartbeat') {
              this.sendWebSocketMessage({ 
                type: 'heartbeat_response', 
                timestamp: new Date().toISOString(),
                client_version: '3.0' // 🆕 Incluir versión
              });
            } else {
              const processedMessage = {
                ...data,
                receivedAt: new Date().toISOString(),
                sessionId: this.sessionId,
                // 🆕 v3.0 METADATA
                client_version: '3.0',
                features_supported: Object.keys(this.features).filter(k => this.features[k])
              };
              
              // 🆕 PROCESAMIENTO AVANZADO DE MENSAJES WEBSOCKET
              this.processWebSocketMessage(processedMessage);
              
              // 🆕 ROUTING INTELIGENTE DE CALLBACKS
              if (data.chart_configs || data.charts || data.pivot_suggestions) {
                if (onChartUpdate) onChartUpdate(data);
              }
              
              if (data.quick_response || data.basic_queries_used) {
                if (onQuickResponse) onQuickResponse(data);
              }
              
              this.notifyMessageHandlers(processedMessage);
              if (onMessage) onMessage(processedMessage);
            }
          } catch (error) {
            console.error('❌ Error parseando mensaje WebSocket v3.0:', error);
            this.notifyErrorHandlers(error);
          }
        };

        this.wsConnection.onerror = (error) => {
          console.error('❌ Error WebSocket v3.0:', error);
          this.isConnecting = false;
          this.notifyErrorHandlers(error);
          if (onError) onError(error);
          reject(error);
        };

        this.wsConnection.onclose = (event) => {
          console.log(`🔌 WebSocket v3.0 cerrado: ${event.code} - ${event.reason}`);
          this.connectionState = CONNECTION_STATES.CLOSED;
          this.isConnecting = false;
          this.stopHeartbeat();
          this.notifyStateChange(CONNECTION_STATES.CLOSED);
          
          if (onClose) onClose(event);
          
          // Auto-reconexión mejorada
          if (event.code !== 1000 && this.reconnectAttempts < CHAT_CONFIG.RECONNECT_ATTEMPTS) {
            this.scheduleReconnect(onMessage, onError, onClose, onChartUpdate, onQuickResponse);
          }
        };

        // Timeout de conexión aumentado
        setTimeout(() => {
          if (this.connectionState === CONNECTION_STATES.CONNECTING) {
            console.error('⏰ Timeout de conexión WebSocket v3.0');
            this.wsConnection.close();
            reject(new Error('WebSocket connection timeout v3.0'));
          }
        }, 15000);

      } catch (error) {
        console.error('❌ Error creando WebSocket v3.0:', error);
        this.isConnecting = false;
        this.notifyErrorHandlers(error);
        reject(error);
      }
    });
  }

  /**
   * 🆕 Envía información de capabilities al servidor
   */
  sendCapabilityInfo() {
    this.sendWebSocketMessage({
      type: 'client_capabilities',
      version: '3.0',
      features: this.features,
      preferences: {
        chart: this.chartPreferences,
        basic_queries: this.basicQueriesConfig,
        user: this.userPreferences
      },
      timestamp: new Date().toISOString()
    });
  }

  /**
   * 🆕 Procesa mensajes WebSocket con lógica avanzada
   * @param {object} message - Mensaje a procesar
   */
  processWebSocketMessage(message) {
    // Procesar respuestas de gráficos
    if (message.chart_configs || message.charts) {
      this.processChartResponse(message);
    }
    
    // Procesar respuestas básicas
    if (message.basic_queries_used || message.quick_response) {
      this.notifyBasicQueryHandlers(message);
    }
    
    // Procesar actualizaciones de preferencias
    if (message.preferences_updated) {
      this.handlePreferencesUpdate(message.new_preferences);
    }
    
    // 🆕 Procesar notificaciones del servidor
    if (message.type === 'server_notification') {
      this.handleServerNotification(message);
    }
  }

  /**
   * 🆕 Maneja actualizaciones de preferencias desde el servidor
   * @param {object} newPreferences - Nuevas preferencias
   */
  handlePreferencesUpdate(newPreferences) {
    if (newPreferences.chart) {
      this.chartPreferences = { ...this.chartPreferences, ...newPreferences.chart };
    }
    if (newPreferences.user) {
      this.userPreferences = { ...this.userPreferences, ...newPreferences.user };
    }
    console.log('🔄 Preferencias actualizadas desde servidor');
  }

  /**
   * 🆕 Maneja notificaciones del servidor
   * @param {object} notification - Notificación
   */
  handleServerNotification(notification) {
    console.log('📢 Notificación del servidor:', notification);
    
    switch (notification.notification_type) {
      case 'system_update':
        console.log('🔄 Actualización del sistema disponible');
        break;
      case 'feature_announcement':
        console.log('🆕 Nueva funcionalidad:', notification.feature_name);
        break;
      case 'performance_alert':
        console.log('⚡ Alerta de rendimiento:', notification.message);
        break;
    }
  }

  /**
   * Programa reconexión automática con backoff exponencial (mejorado v3.0)
   */
  scheduleReconnect(onMessage, onError, onClose, onChartUpdate, onQuickResponse) {
    this.reconnectAttempts++;
    this.connectionState = CONNECTION_STATES.RECONNECTING;
    this.notifyStateChange(CONNECTION_STATES.RECONNECTING);
    
    // 🆕 Backoff exponencial mejorado con jitter
    const delay = Math.min(
      CHAT_CONFIG.RECONNECT_BASE_DELAY * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Máximo 30 segundos
    );
    const jitter = Math.random() * 1000; // Añadir jitter para evitar thundering herd
    const finalDelay = delay + jitter;
    
    console.log(`🔄 Reconectando WebSocket v3.0 en ${Math.round(finalDelay)}ms... (intento ${this.reconnectAttempts}/${CHAT_CONFIG.RECONNECT_ATTEMPTS})`);
    
    setTimeout(() => {
      this.connectWebSocket(onMessage, onError, onClose, onChartUpdate, onQuickResponse);
    }, finalDelay);
  }

  /**
   * Envía mensaje vía WebSocket con queue si no está conectado (mejorado v3.0)
   * @param {object} message - Mensaje a enviar
   * @returns {boolean} True si se envió exitosamente
   */
  sendWebSocketMessage(message) {
    const messageWithMetadata = {
      ...message,
      userId: this.currentUserId,
      sessionId: this.sessionId,
      timestamp: new Date().toISOString(),
      client_version: '3.0', // 🆕 Versión del cliente
      // 🆕 INCLUIR CONFIGURACIONES ACTUALES
      current_chart_config: this.currentChartConfig,
      user_preferences: this.userPreferences,
      features_enabled: Object.keys(this.features).filter(k => this.features[k])
    };

    if (this.wsConnection && this.connectionState === CONNECTION_STATES.OPEN) {
      try {
        this.wsConnection.send(JSON.stringify(messageWithMetadata));
        console.log('📤 Mensaje WebSocket v3.0 enviado:', messageWithMetadata.type || 'message');
        return true;
      } catch (error) {
        console.error('❌ Error enviando mensaje WebSocket v3.0:', error);
        this.messageQueue.push(messageWithMetadata);
        return false;
      }
    } else {
      console.warn('⚠️ WebSocket no conectado, añadiendo a cola v3.0');
      this.messageQueue.push(messageWithMetadata);
      return false;
    }
  }

  // ========================================
  // 🛠️ FUNCIONES DE UTILIDAD v3.0
  // ========================================

  /**
   * Obtiene historial de chat usando api.js (mejorado v3.0)
   * @param {number} limit - Límite de mensajes
   * @returns {Promise<Object>} Historial
   */
  async getChatHistory(limit = 50) {
    try {
      const history = await api.getChatHistory(this.currentUserId);
      
      // 🆕 Enriquecer historial con contexto local
      return {
        ...history,
        local_context: {
          charts_generated: this.chartHistory.length,
          requests_made: this.requestHistory.length,
          session_duration: this.getSessionDuration(),
          preferences_loaded: !!this.userPreferences,
          features_used: Object.keys(this.features).filter(k => this.features[k])
        }
      };
    } catch (error) {
      console.error('❌ Error obteniendo historial v3.0:', error);
      return { messages: [], local_context: { error: error.message } };
    }
  }

  /**
   * Resetea sesión de chat usando api.js (mejorado v3.0)
   * @returns {Promise<Object>} Resultado
   */
  async resetChatSession() {
    try {
      const result = await api.resetChatSession(this.currentUserId);
      
      // 🆕 Reset local completo
      this.sessionId = this.generateSessionId();
      this.currentChartConfig = null;
      this.chartHistory = [];
      this.requestHistory = [];
      this.messageQueue = [];
      
      console.log('🔄 Sesión de chat v3.0 reiniciada completamente');
      return {
        ...result,
        local_reset: true,
        new_session_id: this.sessionId
      };
    } catch (error) {
      console.error('❌ Error reiniciando sesión v3.0:', error);
      throw error;
    }
  }

  /**
   * Obtiene estado del servicio usando api.js (mejorado v3.0)
   * @returns {Promise<Object>} Estado
   */
  async getChatStatus() {
    try {
      const status = await api.getChatStatus();
      
      // 🆕 Enriquecer con estado local
      return {
        ...status,
        local_status: {
          websocket_state: this.connectionState,
          session_id: this.sessionId,
          charts_available: this.features.chartGeneration,
          basic_queries_available: this.features.basicQueries,
          last_message_time: this.lastMessageTime,
          reconnect_attempts: this.reconnectAttempts,
          message_queue_length: this.messageQueue.length,
          client_version: '3.0'
        }
      };
    } catch (error) {
      console.error('❌ Error obteniendo estado v3.0:', error);
      return { 
        status: 'unavailable', 
        message: 'Servicio no disponible v3.0',
        local_status: {
          websocket_state: this.connectionState,
          chart_generator_available: false,
          basic_queries_available: false,
          client_version: '3.0'
        }
      };
    }
  }

  /**
   * 🆕 Obtiene duración de la sesión
   * @returns {number} Duración en segundos
   */
  getSessionDuration() {
    const sessionStart = localStorage.getItem(`cdg_session_start_${this.sessionId}`);
    if (!sessionStart) {
      const now = Date.now();
      localStorage.setItem(`cdg_session_start_${this.sessionId}`, now.toString());
      return 0;
    }
    return Math.floor((Date.now() - parseInt(sessionStart)) / 1000);
  }

  // Resto de métodos de utilidad (sin cambios significativos)
  async isServiceAvailable() {
    try {
      const status = await this.getChatStatus();
      return status.status === 'active' || status.status === 'healthy';
    } catch {
      return false;
    }
  }

  getSessionId() {
    let sessionId = localStorage.getItem('cdg_chat_session_id_v3');
    if (!sessionId) {
      sessionId = this.generateSessionId();
      localStorage.setItem('cdg_chat_session_id_v3', sessionId);
    }
    return sessionId;
  }

  generateSessionId() {
    return `cdg_session_v3_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  getWebSocketState() {
    return this.connectionState;
  }

  getCurrentChartConfig() {
    return this.currentChartConfig;
  }

  setCurrentChartConfig(config) {
    this.currentChartConfig = config;
    this.updateChartHistory(config);
    console.log('📊 Configuración de gráfico v3.0 establecida:', config);
  }

  /**
   * 🆕 Obtiene analytics de la sesión
   * @returns {object} Analytics
   */
  getSessionAnalytics() {
    return {
      session_id: this.sessionId,
      duration: this.getSessionDuration(),
      requests_count: this.requestHistory.length,
      charts_generated: this.chartHistory.length,
      websocket_state: this.connectionState,
      reconnect_attempts: this.reconnectAttempts,
      features_used: Object.keys(this.features).filter(k => this.features[k]),
      avg_response_time: this.requestHistory.length > 0 
        ? this.requestHistory.reduce((sum, r) => sum + r.processingTime, 0) / this.requestHistory.length 
        : 0,
      success_rate: this.requestHistory.length > 0
        ? this.requestHistory.filter(r => r.success).length / this.requestHistory.length
        : 0,
      chart_types_used: [...new Set(this.chartHistory.map(h => h.config?.chart_type).filter(Boolean))],
      client_version: '3.0'
    };
  }

  /**
   * 🆕 Refresca preferencias del usuario desde el servidor
   */
  async refreshUserPreferences() {
    try {
      await this.loadUserPreferences(this.currentUserId);
    } catch (error) {
      console.warn('⚠️ No se pudieron actualizar las preferencias v3.0:', error);
    }
  }

  /**
   * Maneja errores de chat con respuestas inteligentes (mejorado v3.0)
   * @param {Error} error - Error capturado
   * @returns {Object} Respuesta de error formateada
   */
  handleChatError(error) {
    const errorResponses = {
      'ECONNREFUSED': {
        response: '🔌 El servicio de chat v3.0 no está disponible. Verificando conexión...',
        recommendations: [
          'Verifica tu conexión a internet',
          'El backend puede estar temporalmente caído',
          'Reintentando automáticamente...'
        ],
        error: 'CHAT_SERVICE_UNAVAILABLE'
      },
      'ERR_NETWORK': {
        response: '🌐 Problema de red detectado en v3.0. Reintentando conexión...',
        recommendations: [
          'Verifica tu conexión a internet',
          'Reintentando automáticamente...'
        ],
        error: 'NETWORK_ERROR'
      },
      'TIMEOUT': {
        response: '⏰ La respuesta está tomando más tiempo del esperado...',
        recommendations: [
          'El sistema está procesando tu consulta compleja',
          'Considera usar modo rápido para consultas simples',
          'Por favor espera un momento'
        ],
        error: 'REQUEST_TIMEOUT'
      }
    };

    const errorType = error.code || error.name || 'UNKNOWN';
    const errorResponse = errorResponses[errorType] || {
      response: '❌ Ha ocurrido un error inesperado en v3.0. Nuestro equipo ha sido notificado.',
      recommendations: [
        'Intenta nuevamente en unos momentos',
        'Considera usar Basic Queries para consultas simples',
        'Si el problema persiste, contacta al soporte'
      ],
      error: 'UNKNOWN_ERROR'
    };

    return {
      ...errorResponse,
      charts: [],
      chart_configs: [],
      pivot_suggestions: [],
      basic_queries_available: this.features.basicQueries,
      timestamp: new Date().toISOString(),
      serviceMetadata: {
        userId: this.currentUserId,
        sessionId: this.sessionId,
        errorDetails: error.message,
        chart_generator_available: false,
        basic_queries_available: this.features.basicQueries,
        client_version: '3.0'
      }
    };
  }

  // Resto de métodos de WebSocket (procesamiento de cola, heartbeat, etc.) - sin cambios significativos
  processMessageQueue() {
    while (this.messageQueue.length > 0 && this.connectionState === CONNECTION_STATES.OPEN) {
      const message = this.messageQueue.shift();
      this.sendWebSocketMessage(message);
    }
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.connectionState === CONNECTION_STATES.OPEN) {
        this.sendWebSocketMessage({ 
          type: 'heartbeat', 
          timestamp: new Date().toISOString(),
          client_version: '3.0'
        });
      }
    }, CHAT_CONFIG.HEARTBEAT_INTERVAL);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  disconnectWebSocket() {
    this.stopHeartbeat();
    if (this.wsConnection) {
      this.connectionState = CONNECTION_STATES.CLOSING;
      this.wsConnection.close(1000, 'Cliente v3.0 desconectando');
      this.wsConnection = null;
    }
    this.connectionState = CONNECTION_STATES.CLOSED;
    this.reconnectAttempts = 0;
    this.messageQueue = [];
  }

  /**
   * Limpia recursos del servicio (mejorado v3.0)
   */
  cleanup() {
    console.log('🧹 Limpiando recursos de ChatService v3.0...');
    this.disconnectWebSocket();
    
    // Limpiar handlers
    this.messageHandlers = [];
    this.stateChangeHandlers = [];
    this.errorHandlers = [];
    this.chartUpdateHandlers = [];
    this.pivotSuggestionHandlers = [];
    this.quickResponseHandlers = [];
    this.basicQueryHandlers = [];
    this.chartErrorHandlers = [];
    
    // Limpiar datos
    this.messageQueue = [];
    this.requestHistory = [];
    this.chartHistory = [];
    this.currentChartConfig = null;
    
    // Limpiar localStorage
    localStorage.removeItem('cdg_chat_session_id_v3');
    localStorage.removeItem(`cdg_session_start_${this.sessionId}`);
  }

  // ========================================
  // 📈 MÉTRICAS Y MONITOREO v3.0 - EXTENDIDAS
  // ========================================

  /**
   * Obtiene métricas de performance del servicio (mejorado v3.0)
   * @returns {Object} Métricas completas del servicio
   */
  getServiceMetrics() {
    const analytics = this.getSessionAnalytics();
    
    return {
      // Métricas básicas
      connectionState: this.connectionState,
      reconnectAttempts: this.reconnectAttempts,
      messageQueueLength: this.messageQueue.length,
      lastMessageTime: this.lastMessageTime,
      sessionId: this.sessionId,
      userId: this.currentUserId,
      
      // Features y capacidades
      features: this.features,
      preferences: {
        user: this.userPreferences,
        chart: this.chartPreferences,
        basic_queries: this.basicQueriesConfig
      },
      
      // Contadores de handlers
      handlersCount: {
        message: this.messageHandlers.length,
        stateChange: this.stateChangeHandlers.length,
        error: this.errorHandlers.length,
        chartUpdate: this.chartUpdateHandlers.length,
        pivotSuggestion: this.pivotSuggestionHandlers.length,
        // 🆕 v3.0 HANDLERS
        quickResponse: this.quickResponseHandlers.length,
        basicQuery: this.basicQueryHandlers.length,
        chartError: this.chartErrorHandlers.length
      },
      
      // 🆕 MÉTRICAS ESPECÍFICAS v3.0
      performance: {
        avgResponseTime: analytics.avg_response_time,
        successRate: analytics.success_rate,
        requestsCount: analytics.requests_count,
        sessionDuration: analytics.duration
      },
      
      // Métricas de gráficos
      chartMetrics: {
        hasCurrentChart: !!this.currentChartConfig,
        currentChartType: this.currentChartConfig?.chart_type || null,
        chartsGenerated: analytics.charts_generated,
        chartTypesUsed: analytics.chart_types_used,
        chartFeatures: {
          chartGeneration: this.features.chartGeneration,
          chartPivoting: this.features.chartPivoting,
          chartInteractionDetection: this.features.chartInteractionDetection,
          visualizationPreferences: this.features.visualizationPreferences
        }
      },
      
      // 🆕 MÉTRICAS DE BASIC QUERIES
      basicQueriesMetrics: {
        enabled: this.features.basicQueries,
        cacheEnabled: this.basicQueriesConfig.enabled,
        preferQuickResponses: this.basicQueriesConfig.prefer_quick_responses
      },
      
      // Información del cliente
      clientInfo: {
        version: '3.0',
        timestamp: new Date().toISOString(),
        capabilities: Object.keys(this.features).filter(k => this.features[k])
      }
    };
  }
}

// ========================================
// 📤 EXPORTACIONES v3.0
// ========================================

// Instancia singleton del servicio de chat
const chatService = new ChatService();

export default chatService;

// Exportaciones adicionales para flexibilidad
export { ChatService, CONNECTION_STATES, CHAT_CONFIG };

// ========================================
// 🎯 HOOK PERSONALIZADO PARA REACT v3.0 - ACTUALIZADO
// ========================================

/**
 * Hook personalizado para usar ChatService en componentes React v3.0
 * @param {object} options - Opciones del hook
 */
export const useChatService = (options = {}) => {
  const {
    autoConnect = false,
    userId = 'frontend_user',
    onMessage = null,
    onError = null,
    onStateChange = null,
    // Chart Generator callbacks
    onChartUpdate = null,
    onPivotSuggestion = null,
    onChartError = null,
    enableCharts = true,
    // 🆕 v3.0 CALLBACKS
    onQuickResponse = null,
    onBasicQuery = null,
    enableBasicQueries = true,
    enableQuickMode = false
  } = options;

  // Memoizar handlers para evitar re-renders innecesarios
  const memoizedOnMessage = useCallback(onMessage || (() => {}), [onMessage]);
  const memoizedOnError = useCallback(onError || (() => {}), [onError]);
  const memoizedOnStateChange = useCallback(onStateChange || (() => {}), [onStateChange]);
  const memoizedOnChartUpdate = useCallback(onChartUpdate || (() => {}), [onChartUpdate]);
  const memoizedOnPivotSuggestion = useCallback(onPivotSuggestion || (() => {}), [onPivotSuggestion]);
  const memoizedOnChartError = useCallback(onChartError || (() => {}), [onChartError]);
  // 🆕 v3.0 CALLBACKS
  const memoizedOnQuickResponse = useCallback(onQuickResponse || (() => {}), [onQuickResponse]);
  const memoizedOnBasicQuery = useCallback(onBasicQuery || (() => {}), [onBasicQuery]);

  // Configurar usuario
  useEffect(() => {
    if (userId) {
      chatService.setCurrentUserId(userId);
    }
  }, [userId]);

  // Configurar handlers de gráficos
  useEffect(() => {
    if (enableCharts) {
      if (onChartUpdate) chatService.onChartUpdate(memoizedOnChartUpdate);
      if (onPivotSuggestion) chatService.onPivotSuggestion(memoizedOnPivotSuggestion);
      if (onChartError) chatService.onChartError(memoizedOnChartError);
    }
  }, [enableCharts, memoizedOnChartUpdate, memoizedOnPivotSuggestion, memoizedOnChartError]);

  // 🆕 Configurar handlers de Basic Queries
  useEffect(() => {
    if (enableBasicQueries) {
      if (onQuickResponse) chatService.onQuickResponse(memoizedOnQuickResponse);
      if (onBasicQuery) chatService.onBasicQuery(memoizedOnBasicQuery);
    }
  }, [enableBasicQueries, memoizedOnQuickResponse, memoizedOnBasicQuery]);

  // 🆕 Configurar modo rápido por defecto
  useEffect(() => {
    if (enableQuickMode !== chatService.userPreferences.quick_mode_default) {
      chatService.userPreferences.quick_mode_default = enableQuickMode;
    }
  }, [enableQuickMode]);

  // Auto-conectar WebSocket si se solicita
  useEffect(() => {
    if (autoConnect) {
      chatService.connectWebSocket(
        memoizedOnMessage, 
        memoizedOnError, 
        memoizedOnStateChange,
        enableCharts ? memoizedOnChartUpdate : null,
        enableBasicQueries ? memoizedOnQuickResponse : null // 🆕 v3.0 callback
      );
    }
    
    return () => {
      if (autoConnect) {
        chatService.disconnectWebSocket();
      }
    };
  }, [autoConnect]); // Intencionalmente excluimos handlers para evitar reconexiones constantes

  return {
    // Servicio principal
    service: chatService,
    
    // Métodos básicos
    sendMessage: chatService.sendMessage.bind(chatService),
    sendFeedback: chatService.sendChatFeedback.bind(chatService),
    getSuggestions: chatService.getChatSuggestions.bind(chatService),
    getPreferences: chatService.getChatPreferences.bind(chatService),
    updatePreferences: chatService.updateChatPreferences.bind(chatService),
    classifyIntent: chatService.classifyIntent.bind(chatService),
    
    // WebSocket
    connectWebSocket: chatService.connectWebSocket.bind(chatService),
    disconnectWebSocket: chatService.disconnectWebSocket.bind(chatService),
    
    // Utilidades
    getMetrics: chatService.getServiceMetrics.bind(chatService),
    getAnalytics: chatService.getSessionAnalytics.bind(chatService),
    connectionState: chatService.connectionState,
    
    // Chart Generator
    sendChartInteraction: chatService.sendChartInteraction.bind(chatService),
    requestChartGeneration: chatService.requestChartGeneration.bind(chatService),
    pivotChart: chatService.pivotChart.bind(chatService),
    getChartSuggestions: chatService.getChartSuggestions.bind(chatService),
    generateChartFromEndpoint: chatService.generateChartFromEndpoint.bind(chatService),
    updateChartPreferences: chatService.updateChartPreferences.bind(chatService),
    getCurrentChartConfig: chatService.getCurrentChartConfig.bind(chatService),
    setCurrentChartConfig: chatService.setCurrentChartConfig.bind(chatService),
    isChartCommand: chatService.isChartCommand.bind(chatService),
    
    // 🆕 v3.0 METHODS
    sendBasicQuery: chatService.sendBasicQuery.bind(chatService),
    isBasicQuery: chatService.isBasicQuery.bind(chatService),
    shouldUseQuickMode: chatService.shouldUseQuickMode.bind(chatService),
    refreshUserPreferences: chatService.refreshUserPreferences.bind(chatService),
    
    // Estado y configuración
    features: chatService.features,
    preferences: {
      user: chatService.userPreferences,
      chart: chatService.chartPreferences,
      basicQueries: chatService.basicQueriesConfig
    }
  };
};

console.log('🎉 ChatService v3.0 inicializado con integración completa backend v3.0');
