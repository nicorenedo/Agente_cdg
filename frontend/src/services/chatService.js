// src/services/chatService.js
// Servicio de chat profesional v2.1 - Totalmente integrado con main.py v2.0 y api.js v2.1
// Compatible con Chat Agent v6.1 con System Prompts Profesionales + Reflection Pattern

import React, { useEffect, useCallback } from 'react';
import api from './api.js';

// ========================================
// 🌐 CONFIGURACIÓN Y CONSTANTES
// ========================================

const CHAT_CONFIG = {
  WEBSOCKET_URL: process.env.REACT_APP_CHAT_API_URL?.replace(/^http/, 'ws') || 'ws://localhost:8000',
  RECONNECT_ATTEMPTS: 5,
  RECONNECT_BASE_DELAY: 1000,
  HEARTBEAT_INTERVAL: 30000,
  REQUEST_TIMEOUT: 45000,
  RETRY_ATTEMPTS: 3
};

const CONNECTION_STATES = {
  CONNECTING: 'CONNECTING',
  OPEN: 'OPEN',
  CLOSING: 'CLOSING',
  CLOSED: 'CLOSED',
  RECONNECTING: 'RECONNECTING'
};

// ========================================
// 🎯 CLASE PRINCIPAL CHATSERVICE
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
    
    // Chat features
    this.sessionId = this.getSessionId();
    this.currentUserId = 'frontend_user';
    
    // Performance tracking
    this.lastMessageTime = null;
    this.messageQueue = [];
    
    // Advanced features flags
    this.features = {
      professionalPrompts: true,
      intentClassification: true,
      personalizedSuggestions: true,
      feedbackLearning: true,
      reflectionPattern: true
    };

    // Auto-cleanup on page unload
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => this.cleanup());
    }
  }

  // ========================================
  // 🔧 CONFIGURACIÓN Y INICIALIZACIÓN
  // ========================================

  /**
   * Establece el ID del usuario actual
   * @param {string} userId - ID único del usuario
   */
  setCurrentUserId(userId) {
    this.currentUserId = userId;
    api.setCurrentUserId(userId);
    console.log(`🆔 Usuario actual establecido: ${userId}`);
  }

  /**
   * Obtiene el ID del usuario actual
   * @returns {string} ID del usuario
   */
  getCurrentUserId() {
    return this.currentUserId;
  }

  /**
   * Actualiza configuración del servicio
   * @param {object} config - Nueva configuración
   */
  updateConfig(config) {
    Object.assign(CHAT_CONFIG, config);
    console.log('⚙️ Configuración actualizada:', config);
  }

  // ========================================
  // 💬 FUNCIONALIDADES DE CHAT BÁSICO
  // ========================================

  /**
   * Envía un mensaje de forma inteligente y escalable
   * @param {string} message - Mensaje del usuario
   * @param {object} options - Opciones adicionales
   * @returns {Promise<Object>} Respuesta del agente
   */
  async sendMessage(message, options = {}) {
    if (!message?.trim()) {
      throw new Error('El mensaje no puede estar vacío');
    }
  
    // 🎯 CONSTRUIR CONTEXTO ENRIQUECIDO SIN HARDCODEAR
    const enhancedOptions = {
      ...options,
      gestorId: options.gestorId || options.gestor_id,
      includeCharts: options.includeCharts !== false,
      includeRecommendations: options.includeRecommendations !== false,
      context: {
        sessionId: this.sessionId,
        timestamp: new Date().toISOString(),
        features: this.features,
        // 🚀 METADATOS GENÉRICOS PARA MEJORAR CLASIFICACIÓN
        source: 'frontend_react',
        user_agent: 'chatservice_v2.1',
        interaction_type: 'user_query',
        session_context: {
          previous_messages: this.messageQueue.length,
          user_id: this.currentUserId,
          connection_state: this.connectionState
        },
        ...options.context
      }
    };
  
    console.log('💬 Enviando mensaje:', { message, options: enhancedOptions });
  
    try {
      // 🎯 INTENTAR SIEMPRE CON PROCESAMIENTO INTELIGENTE PRIMERO
      // Si falla, automáticamente caerá al método estándar
      if (api.sendIntelligentMessage) {
        console.log('🧠 Intentando procesamiento inteligente...');
        try {
          const response = await api.sendIntelligentMessage(message, enhancedOptions.context);
          
          // ✅ Si el procesamiento inteligente funciona, usarlo
          return {
            ...response,
            serviceMetadata: {
              userId: this.currentUserId,
              sessionId: this.sessionId,
              timestamp: new Date().toISOString(),
              processingType: 'intelligent_success',
              features: this.features
            }
          };
        } catch (intelligentError) {
          console.warn('⚠️ Procesamiento inteligente falló, usando método estándar:', intelligentError.message);
          // Continúa al método estándar como fallback
        }
      }
    
      // 🔄 MÉTODO ESTÁNDAR COMO FALLBACK
      const response = await api.sendChatMessage(message, enhancedOptions.gestorId, enhancedOptions);
      
      this.lastMessageTime = new Date();
      
      const processedResponse = {
        ...response,
        serviceMetadata: {
          userId: this.currentUserId,
          sessionId: this.sessionId,
          timestamp: new Date().toISOString(),
          processingType: 'standard_fallback',
          features: this.features
        }
      };
    
      console.log('✅ Respuesta procesada:', processedResponse);
      return processedResponse;
    
    } catch (error) {
      console.error('❌ Error enviando mensaje:', error);
      return this.handleChatError(error);
    }
  }

  // ========================================
  // 🚀 FUNCIONALIDADES AVANZADAS v6.1
  // ========================================

  /**
   * Envía feedback específico usando System Prompts Profesionales
   * @param {object} feedback - Datos del feedback
   * @returns {Promise<Object>} Resultado del procesamiento
   */
  async sendChatFeedback(feedback) {
    try {
      console.log('📝 Enviando feedback de chat:', feedback);
      const response = await api.sendChatFeedback(this.currentUserId, feedback);
      
      // Actualizar features basado en feedback
      if (response.personalization_updated) {
        await this.refreshUserPreferences();
      }
      
      return response;
    } catch (error) {
      console.error('❌ Error enviando feedback:', error);
      throw error;
    }
  }

  /**
   * Obtiene sugerencias personalizadas dinámicas
   * @returns {Promise<Array>} Lista de sugerencias
   */
  async getChatSuggestions() {
    try {
      console.log('💡 Obteniendo sugerencias personalizadas...');
      const response = await api.getChatSuggestions(this.currentUserId);
      
      return {
        suggestions: response.suggestions || [],
        personalized: response.personalized || false,
        total: response.total || 0,
        timestamp: response.timestamp
      };
    } catch (error) {
      console.error('❌ Error obteniendo sugerencias:', error);
      // Fallback con sugerencias genéricas
      return {
        suggestions: [
          "¿Cómo está mi rendimiento este mes?",
          "Comparar con otros gestores",
          "Detectar alertas automáticamente",
          "Análisis de desviaciones",
          "Generar Business Review"
        ],
        personalized: false,
        total: 5,
        source: 'fallback'
      };
    }
  }

  /**
   * Obtiene preferencias de personalización
   * @returns {Promise<Object>} Preferencias del usuario
   */
  async getChatPreferences() {
    try {
      console.log('⚙️ Obteniendo preferencias de chat...');
      return await api.getChatPreferences(this.currentUserId);
    } catch (error) {
      console.error('❌ Error obteniendo preferencias:', error);
      throw error;
    }
  }

  /**
   * Actualiza preferencias de personalización
   * @param {object} preferences - Nuevas preferencias
   * @returns {Promise<Object>} Confirmación de actualización
   */
  async updateChatPreferences(preferences) {
    try {
      console.log('🔧 Actualizando preferencias:', preferences);
      const response = await api.updateChatPreferences(this.currentUserId, preferences);
      
      // Actualizar features locales
      if (response.current_preferences) {
        this.features = { ...this.features, ...response.current_preferences };
      }
      
      return response;
    } catch (error) {
      console.error('❌ Error actualizando preferencias:', error);
      throw error;
    }
  }

  /**
   * Clasifica intención de mensaje usando IA
   * @param {string} message - Mensaje a clasificar
   * @returns {Promise<Object>} Análisis de intención
   */
  async classifyIntent(message) {
    try {
      console.log('🧠 Clasificando intención:', message);
      const response = await api.classifyChatIntent(message, this.currentUserId);
      
      return {
        intent: response.intent_analysis?.intent || 'general_inquiry',
        confidence: response.intent_analysis?.confidence || 0.5,
        requiresCdgAgent: response.intent_analysis?.requires_cdg_agent || false,
        recommendedApproach: response.intent_analysis?.recommended_approach || 'simple',
        timestamp: response.timestamp
      };
    } catch (error) {
      console.error('❌ Error clasificando intención:', error);
      return {
        intent: 'general_inquiry',
        confidence: 0.5,
        requiresCdgAgent: false,
        recommendedApproach: 'simple',
        source: 'fallback'
      };
    }
  }

  /**
   * Refresca preferencias del usuario desde el servidor
   */
  async refreshUserPreferences() {
    try {
      const preferences = await this.getChatPreferences();
      this.features = { ...this.features, ...preferences.preferences };
      console.log('🔄 Preferencias actualizadas:', this.features);
    } catch (error) {
      console.warn('⚠️ No se pudieron actualizar las preferencias:', error);
    }
  }

  // ========================================
  // 🌐 GESTIÓN WEBSOCKET MEJORADA
  // ========================================

  /**
   * Conecta WebSocket con manejo avanzado de estados
   * @param {Function} onMessage - Callback para mensajes
   * @param {Function} onError - Callback para errores
   * @param {Function} onClose - Callback para cierre
   * @returns {Promise<WebSocket>} Conexión WebSocket
   */
  async connectWebSocket(onMessage, onError = null, onClose = null) {
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
        console.log(`🌐 Conectando WebSocket: ${wsUrl}`);
        
        this.wsConnection = new WebSocket(wsUrl);

        this.wsConnection.onopen = () => {
          console.log('✅ WebSocket conectado exitosamente');
          this.connectionState = CONNECTION_STATES.OPEN;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.notifyStateChange(CONNECTION_STATES.OPEN);
          this.processMessageQueue();
          resolve(this.wsConnection);
        };

        this.wsConnection.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'heartbeat') {
              this.sendWebSocketMessage({ 
                type: 'heartbeat_response', 
                timestamp: new Date().toISOString() 
              });
            } else {
              // Procesar mensaje y notificar handlers
              const processedMessage = {
                ...data,
                receivedAt: new Date().toISOString(),
                sessionId: this.sessionId
              };
              
              this.notifyMessageHandlers(processedMessage);
              if (onMessage) onMessage(processedMessage);
            }
          } catch (error) {
            console.error('❌ Error parseando mensaje WebSocket:', error);
            this.notifyErrorHandlers(error);
          }
        };

        this.wsConnection.onerror = (error) => {
          console.error('❌ Error WebSocket:', error);
          this.isConnecting = false;
          this.notifyErrorHandlers(error);
          if (onError) onError(error);
          reject(error);
        };

        this.wsConnection.onclose = (event) => {
          console.log(`🔌 WebSocket cerrado: ${event.code} - ${event.reason}`);
          this.connectionState = CONNECTION_STATES.CLOSED;
          this.isConnecting = false;
          this.stopHeartbeat();
          this.notifyStateChange(CONNECTION_STATES.CLOSED);
          
          if (onClose) onClose(event);
          
          // Auto-reconexión si no fue cierre limpio
          if (event.code !== 1000 && this.reconnectAttempts < CHAT_CONFIG.RECONNECT_ATTEMPTS) {
            this.scheduleReconnect(onMessage, onError, onClose);
          }
        };

        // Timeout de conexión
        setTimeout(() => {
          if (this.connectionState === CONNECTION_STATES.CONNECTING) {
            console.error('⏰ Timeout de conexión WebSocket');
            this.wsConnection.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);

      } catch (error) {
        console.error('❌ Error creando WebSocket:', error);
        this.isConnecting = false;
        this.notifyErrorHandlers(error);
        reject(error);
      }
    });
  }

  /**
   * Programa reconexión automática con backoff exponencial
   */
  scheduleReconnect(onMessage, onError, onClose) {
    this.reconnectAttempts++;
    this.connectionState = CONNECTION_STATES.RECONNECTING;
    this.notifyStateChange(CONNECTION_STATES.RECONNECTING);
    
    const delay = CHAT_CONFIG.RECONNECT_BASE_DELAY * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`🔄 Reconectando WebSocket en ${delay}ms... (intento ${this.reconnectAttempts}/${CHAT_CONFIG.RECONNECT_ATTEMPTS})`);
    
    setTimeout(() => {
      this.connectWebSocket(onMessage, onError, onClose);
    }, delay);
  }

  /**
   * Envía mensaje vía WebSocket con queue si no está conectado
   * @param {object} message - Mensaje a enviar
   * @returns {boolean} True si se envió exitosamente
   */
  sendWebSocketMessage(message) {
    const messageWithMetadata = {
      ...message,
      userId: this.currentUserId,
      sessionId: this.sessionId,
      timestamp: new Date().toISOString()
    };

    if (this.wsConnection && this.connectionState === CONNECTION_STATES.OPEN) {
      try {
        this.wsConnection.send(JSON.stringify(messageWithMetadata));
        console.log('📤 Mensaje WebSocket enviado:', messageWithMetadata);
        return true;
      } catch (error) {
        console.error('❌ Error enviando mensaje WebSocket:', error);
        this.messageQueue.push(messageWithMetadata);
        return false;
      }
    } else {
      console.warn('⚠️ WebSocket no conectado, añadiendo a cola');
      this.messageQueue.push(messageWithMetadata);
      return false;
    }
  }

  /**
   * Procesa cola de mensajes pendientes
   */
  processMessageQueue() {
    while (this.messageQueue.length > 0 && this.connectionState === CONNECTION_STATES.OPEN) {
      const message = this.messageQueue.shift();
      this.sendWebSocketMessage(message);
    }
  }

  /**
   * Inicia heartbeat para mantener WebSocket vivo
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.connectionState === CONNECTION_STATES.OPEN) {
        this.sendWebSocketMessage({ 
          type: 'heartbeat', 
          timestamp: new Date().toISOString() 
        });
      }
    }, CHAT_CONFIG.HEARTBEAT_INTERVAL);
  }

  /**
   * Detiene heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Desconecta WebSocket limpiamente
   */
  disconnectWebSocket() {
    this.stopHeartbeat();
    if (this.wsConnection) {
      this.connectionState = CONNECTION_STATES.CLOSING;
      this.wsConnection.close(1000, 'Cliente desconectando');
      this.wsConnection = null;
    }
    this.connectionState = CONNECTION_STATES.CLOSED;
    this.reconnectAttempts = 0;
    this.messageQueue = [];
  }

  // ========================================
  // 📊 HANDLERS Y EVENTOS
  // ========================================

  /**
   * Registra handler para mensajes WebSocket
   * @param {Function} handler - Función handler
   */
  onMessage(handler) {
    this.messageHandlers.push(handler);
  }

  /**
   * Registra handler para cambios de estado
   * @param {Function} handler - Función handler
   */
  onStateChange(handler) {
    this.stateChangeHandlers.push(handler);
  }

  /**
   * Registra handler para errores
   * @param {Function} handler - Función handler
   */
  onError(handler) {
    this.errorHandlers.push(handler);
  }

  /**
   * Notifica handlers de mensajes
   */
  notifyMessageHandlers(message) {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('❌ Error en message handler:', error);
      }
    });
  }

  /**
   * Notifica handlers de cambio de estado
   */
  notifyStateChange(newState) {
    this.stateChangeHandlers.forEach(handler => {
      try {
        handler(newState, this.connectionState);
      } catch (error) {
        console.error('❌ Error en state change handler:', error);
      }
    });
  }

  /**
   * Notifica handlers de errores
   */
  notifyErrorHandlers(error) {
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (error) {
        console.error('❌ Error en error handler:', error);
      }
    });
  }

  // ========================================
  // 🛠️ FUNCIONES DE UTILIDAD
  // ========================================

  /**
   * Obtiene historial de chat usando api.js
   * @param {number} limit - Límite de mensajes
   * @returns {Promise<Object>} Historial
   */
  async getChatHistory(limit = 50) {
    try {
      return await api.getChatHistory(this.currentUserId);
    } catch (error) {
      console.error('❌ Error obteniendo historial:', error);
      return { messages: [] };
    }
  }

  /**
   * Resetea sesión de chat usando api.js
   * @returns {Promise<Object>} Resultado
   */
  async resetChatSession() {
    try {
      const result = await api.resetChatSession(this.currentUserId);
      this.sessionId = this.generateSessionId();
      console.log('🔄 Sesión de chat reiniciada');
      return result;
    } catch (error) {
      console.error('❌ Error reiniciando sesión:', error);
      throw error;
    }
  }

  /**
   * Obtiene estado del servicio usando api.js
   * @returns {Promise<Object>} Estado
   */
  async getChatStatus() {
    try {
      return await api.getChatStatus();
    } catch (error) {
      console.error('❌ Error obteniendo estado:', error);
      return { 
        status: 'unavailable', 
        message: 'Servicio no disponible',
        websocket_state: this.connectionState
      };
    }
  }

  /**
   * Verifica si el servicio está disponible
   * @returns {Promise<boolean>} Disponibilidad
   */
  async isServiceAvailable() {
    try {
      const status = await this.getChatStatus();
      return status.status === 'active' || status.status === 'healthy';
    } catch {
      return false;
    }
  }

  /**
   * Obtiene ID de sesión
   * @returns {string} Session ID
   */
  getSessionId() {
    let sessionId = localStorage.getItem('cdg_chat_session_id');
    if (!sessionId) {
      sessionId = this.generateSessionId();
      localStorage.setItem('cdg_chat_session_id', sessionId);
    }
    return sessionId;
  }

  /**
   * Genera nuevo ID de sesión
   * @returns {string} Nuevo session ID
   */
  generateSessionId() {
    return `cdg_session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Obtiene estado actual de WebSocket
   * @returns {string} Estado de conexión
   */
  getWebSocketState() {
    return this.connectionState;
  }

  /**
   * Maneja errores de chat con respuestas inteligentes
   * @param {Error} error - Error capturado
   * @returns {Object} Respuesta de error formateada
   */
  handleChatError(error) {
    const errorResponses = {
      'ECONNREFUSED': {
        response: '🔌 El servicio de chat no está disponible. Verificando conexión...',
        recommendations: [
          'Verifica tu conexión a internet',
          'El backend puede estar temporalmente caído',
          'Reintentando automáticamente...'
        ],
        error: 'CHAT_SERVICE_UNAVAILABLE'
      },
      'ERR_NETWORK': {
        response: '🌐 Problema de red detectado. Reintentando conexión...',
        recommendations: [
          'Verifica tu conexión a internet',
          'Reintentando automáticamente...'
        ],
        error: 'NETWORK_ERROR'
      },
      'TIMEOUT': {
        response: '⏰ La respuesta está tomando más tiempo del esperado...',
        recommendations: [
          'El sistema está procesando tu consulta',
          'Por favor espera un momento'
        ],
        error: 'REQUEST_TIMEOUT'
      }
    };

    const errorType = error.code || error.name || 'UNKNOWN';
    const errorResponse = errorResponses[errorType] || {
      response: '❌ Ha ocurrido un error inesperado. Nuestro equipo ha sido notificado.',
      recommendations: [
        'Intenta nuevamente en unos momentos',
        'Si el problema persiste, contacta al soporte'
      ],
      error: 'UNKNOWN_ERROR'
    };

    return {
      ...errorResponse,
      charts: [],
      timestamp: new Date().toISOString(),
      serviceMetadata: {
        userId: this.currentUserId,
        sessionId: this.sessionId,
        errorDetails: error.message
      }
    };
  }

  /**
   * Limpia recursos del servicio
   */
  cleanup() {
    console.log('🧹 Limpiando recursos de ChatService...');
    this.disconnectWebSocket();
    this.messageHandlers = [];
    this.stateChangeHandlers = [];
    this.errorHandlers = [];
    this.messageQueue = [];
    localStorage.removeItem('cdg_chat_session_id');
  }

  // ========================================
  // 📈 MÉTRICAS Y MONITOREO
  // ========================================

  /**
   * Obtiene métricas de performance del servicio
   * @returns {Object} Métricas del servicio
   */
  getServiceMetrics() {
    return {
      connectionState: this.connectionState,
      reconnectAttempts: this.reconnectAttempts,
      messageQueueLength: this.messageQueue.length,
      lastMessageTime: this.lastMessageTime,
      sessionId: this.sessionId,
      userId: this.currentUserId,
      features: this.features,
      handlersCount: {
        message: this.messageHandlers.length,
        stateChange: this.stateChangeHandlers.length,
        error: this.errorHandlers.length
      }
    };
  }
}

// ========================================
// 📤 EXPORTACIONES
// ========================================

// Instancia singleton del servicio de chat
const chatService = new ChatService();

export default chatService;

// Exportaciones adicionales para flexibilidad
export { ChatService, CONNECTION_STATES, CHAT_CONFIG };

// ========================================
// 🎯 UTILIDADES PARA COMPONENTES REACT - SIN ERRORES ESLINT
// ========================================

/**
 * Hook personalizado para usar ChatService en componentes React
 * @param {object} options - Opciones del hook
 */
export const useChatService = (options = {}) => {
  const {
    autoConnect = false,
    userId = 'frontend_user',
    onMessage = null,
    onError = null,
    onStateChange = null
  } = options;

  // Memoizar handlers para evitar re-renders innecesarios
  const memoizedOnMessage = useCallback(onMessage || (() => {}), [onMessage]);
  const memoizedOnError = useCallback(onError || (() => {}), [onError]);
  const memoizedOnStateChange = useCallback(onStateChange || (() => {}), [onStateChange]);

  // Configurar usuario
  useEffect(() => {
    if (userId) {
      chatService.setCurrentUserId(userId);
    }
  }, [userId]);

  // Auto-conectar WebSocket si se solicita
  useEffect(() => {
    if (autoConnect) {
      chatService.connectWebSocket(memoizedOnMessage, memoizedOnError, memoizedOnStateChange);
    }
    
    return () => {
      if (autoConnect) {
        chatService.disconnectWebSocket();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]); // Intencionalmente excluimos handlers para evitar reconexiones constantes

  return {
    service: chatService,
    sendMessage: chatService.sendMessage.bind(chatService),
    sendFeedback: chatService.sendChatFeedback.bind(chatService),
    getSuggestions: chatService.getChatSuggestions.bind(chatService),
    getPreferences: chatService.getChatPreferences.bind(chatService),
    updatePreferences: chatService.updateChatPreferences.bind(chatService),
    classifyIntent: chatService.classifyIntent.bind(chatService),
    connectWebSocket: chatService.connectWebSocket.bind(chatService),
    disconnectWebSocket: chatService.disconnectWebSocket.bind(chatService),
    getMetrics: chatService.getServiceMetrics.bind(chatService),
    connectionState: chatService.connectionState
  };
};

console.log('🎉 ChatService v2.1 inicializado - ESLint errors corregidos');
