// src/services/api.js
// API Service para Agente Control de Gestión de Banca March - 100% integrado con main.py v2.0
// Versión: 2.1 - Con endpoints avanzados de Chat Agent v6.1 + System Prompts Profesionales

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE_URL;
    this._availablePeriods = null;
    this._defaultPeriod = null;
    this._currentUserId = 'frontend_user'; // Usuario por defecto para frontend
  }

  async _request(path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const config = {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options
    };

    try {
      console.log(`🔄 API Request: ${options.method || 'GET'} ${url}`);
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(`✅ API Response:`, data);
      return data;
    } catch (error) {
      console.error(`❌ API Error for ${path}:`, error);
      throw error;
    }
  }

  // ========================================
  // 🔧 UTILIDADES DE FORMATO
  // ========================================

  _formatPeriod(period) {
    if (!period) return null;
    if (typeof period === 'string' && period.length > 7) {
      return period.substring(0, 7);
    }
    return period;
  }

  setCurrentUserId(userId) {
    this._currentUserId = userId;
  }

  getCurrentUserId() {
    return this._currentUserId;
  }

  // ========================================
  // 📅 ENDPOINTS DE PERÍODOS
  // ========================================

  async getAvailablePeriods() {
    try {
      const response = await this._request('/periods/available');
      this._availablePeriods = response.periods || [];
      this._defaultPeriod = response.latest || this._availablePeriods[0] || '2025-10';
      
      return {
        data: {
          periods: this._availablePeriods,
          latest: this._defaultPeriod
        },
        success: true
      };
    } catch (error) {
      console.warn('Error obteniendo períodos, usando fallback');
      this._availablePeriods = ['2025-10', '2025-09'];
      this._defaultPeriod = '2025-10';
      
      return {
        data: {
          periods: this._availablePeriods,
          latest: this._defaultPeriod
        },
        success: false,
        source: 'fallback'
      };
    }
  }

  async getDefaultPeriod() {
    if (!this._defaultPeriod) {
      await this.getAvailablePeriods();
    }
    return this._defaultPeriod;
  }

  async isValidPeriod(period) {
    if (!this._availablePeriods) {
      await this.getAvailablePeriods();
    }
    return this._availablePeriods.includes(this._formatPeriod(period));
  }

  // ========================================
  // 📊 ENDPOINTS DE DASHBOARD
  // ========================================

  async getDashboardData(period) {
    const activePeriod = this._formatPeriod(period) || await this.getDefaultPeriod();
    return this._request(`/api/dashboard/${activePeriod}`);
  }

  async getKpisConsolidados(periodo = null) {
    const activePeriod = this._formatPeriod(periodo) || await this.getDefaultPeriod();
    return this._request(`/kpis/consolidados?periodo=${activePeriod}`);
  }

  async getTotales(periodo = null) {
    const activePeriod = this._formatPeriod(periodo) || await this.getDefaultPeriod();
    return this._request(`/totales?periodo=${activePeriod}`);
  }

  async getAnalisisComparativo(periodo = null) {
    const activePeriod = this._formatPeriod(periodo) || await this.getDefaultPeriod();
    return this._request(`/analisis-comparativo?periodo=${activePeriod}`);
  }

  // ========================================
  // 🚨 ENDPOINTS DE ALERTAS Y DESVIACIONES
  // ========================================

  async getDeviationAlerts(periodo = null, threshold = 15) {
    const activePeriod = this._formatPeriod(periodo) || await this.getDefaultPeriod();
    return this._request(`/deviations/alerts?periodo=${activePeriod}&threshold=${threshold}`);
  }

  // ========================================
  // 👥 ENDPOINTS DE GESTORES
  // ========================================

  async getGestores() {
    console.log('🎯 DEBUG: Obteniendo gestores...');
    try {
      const response = await this._request('/gestores');
      let gestoresData = [];
      
      if (response) {
        if (Array.isArray(response)) {
          gestoresData = response;
        } else if (response.gestores) {
          gestoresData = response.gestores;
        } else if (response.data) {
          gestoresData = response.data;
        }
      }

      const mapped = gestoresData.map(g => ({
        id: g.gestor_id || g.GESTOR_ID || g.id,
        nombre: g.nombre || g.desc_gestor || g.DESC_GESTOR,
        centro: g.centro || g.desc_centro || g.DESC_CENTRO,
        segmento: g.segmento || g.desc_segmento || g.DESC_SEGMENTO || 'No especificado'
      })).filter(g => g.id && g.nombre);

      console.log(`✅ Gestores procesados: ${mapped.length}`);
      return { data: { gestores: mapped, total: mapped.length }, success: true };
    } catch (error) {
      console.error('❌ Error en /gestores:', error);
      throw error;
    }
  }

  async getComparativeRanking(periodo = null, orderBy = 'margen_neto') {
    const activePeriod = this._formatPeriod(periodo) || await this.getDefaultPeriod();
    return this._request(`/comparative/ranking?periodo=${activePeriod}&metric=${orderBy}`);
  }

  async getGestorPerformance(gestorId, period) {
    const activePeriod = this._formatPeriod(period) || await this.getDefaultPeriod();
    return this._request(`/gestor/${gestorId}/performance?periodo=${activePeriod}`);
  }

  // ========================================
  // 💰 ENDPOINTS DE INCENTIVOS
  // ========================================

  async getIncentiveSummary(periodo = null, gestorId = null) {
    const activePeriod = this._formatPeriod(periodo) || await this.getDefaultPeriod();
    let params = `periodo=${activePeriod}`;
    if (gestorId) params += `&gestor_id=${gestorId}`;
    return this._request(`/incentives/summary?${params}`);
  }

  // ========================================
  // 📋 ENDPOINTS DE REPORTES
  // ========================================

  async generateBusinessReview(userId, gestorId, period) {
    return this._request('/reports/business_review', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        gestor_id: gestorId,
        periodo: this._formatPeriod(period)
      })
    });
  }

  async generateExecutiveSummary(userId, period) {
    return this._request('/reports/executive_summary', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        periodo: this._formatPeriod(period)
      })
    });
  }

  // ========================================
  // 💬 ENDPOINTS DE CHAT BÁSICO
  // ========================================

  async sendChatMessage(message, gestorId = null, context = {}) {
    const activePeriod = this._formatPeriod(context.periodo) || await this.getDefaultPeriod();
    return this._request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        user_id: this._currentUserId,
        message,
        gestor_id: gestorId,
        periodo: activePeriod,
        include_charts: true,
        include_recommendations: true,
        context,
        timestamp: new Date().toISOString()
      })
    });
  }

  /**
   * Procesa mensaje con análisis inteligente automático (completamente genérico)
   * @param {string} message - Mensaje del usuario
   * @param {object} context - Contexto adicional
   * @returns {Promise<Object>} Respuesta procesada
   */
  async sendIntelligentMessage(message, context = {}) {
    try {
      // 🎯 PREPARAR PAYLOAD ENRIQUECIDO GENÉRICO
      const intelligentPayload = {
        user_id: this._currentUserId,
        message: message.trim(),
        context: {
          ...context,
          // 🚀 METADATOS PARA MEJORAR CLASIFICACIÓN AUTOMÁTICA
          frontend_source: true,
          api_version: '2.1',
          request_timestamp: new Date().toISOString(),
          enhanced_processing: true,
          // Permitir que el backend haga toda la detección inteligente
          allow_auto_detection: true,
          allow_intent_enhancement: true
        },
        // 🎯 CONFIGURACIONES GENÉRICAS PARA MEJOR PROCESAMIENTO
        include_charts: true,
        include_recommendations: true,
        timestamp: new Date().toISOString()
      };
    
      console.log('🧠 Enviando para procesamiento inteligente:', intelligentPayload);
      
      return await this._request('/chat/intelligent', {
        method: 'POST',
        body: JSON.stringify(intelligentPayload)
      });
      
    } catch (error) {
      console.error('❌ Error en procesamiento inteligente:', error);
      
      // 🔄 FALLBACK AUTOMÁTICO AL MÉTODO ESTÁNDAR
      console.log('🔄 Fallback a método estándar...');
      return await this.sendChatMessage(message, null, { 
        context: {
          ...context,
          fallback_from_intelligent: true,
          fallback_reason: error.message
        }
      });
    }
  }


  async getChatStatus() {
    return this._request('/chat/status');
  }

  async getChatHistory(userId = null) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/chat/history/${activeUserId}`);
  }

  async resetChatSession(userId = null) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/chat/reset/${activeUserId}`, { method: 'POST' });
  }

  // ========================================
  // 🚀 ENDPOINTS DE CHAT AVANZADO v6.1
  // ========================================

  /**
   * Envía feedback específico del chat usando System Prompts Profesionales
   * @param {string} userId - ID del usuario
   * @param {Object} feedback - Datos del feedback (rating, comments, categories)
   */
  async sendChatFeedback(userId = null, feedback) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/chat/feedback/${activeUserId}`, {
      method: 'POST',
      body: JSON.stringify(feedback)
    });
  }

  /**
   * Obtiene sugerencias personalizadas dinámicas usando IA
   * @param {string} userId - ID del usuario
   */
  async getChatSuggestions(userId = null) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/chat/suggestions/${activeUserId}`);
  }

  /**
   * Obtiene preferencias de personalización del chat
   * @param {string} userId - ID del usuario
   */
  async getChatPreferences(userId = null) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/chat/preferences/${activeUserId}`);
  }

  /**
   * Actualiza preferencias de personalización del chat
   * @param {string} userId - ID del usuario
   * @param {Object} preferences - Nuevas preferencias
   */
  async updateChatPreferences(userId = null, preferences) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/chat/preferences/${activeUserId}`, {
      method: 'PUT',
      body: JSON.stringify(preferences)
    });
  }

  /**
   * Clasifica intención de mensaje usando System Prompts Profesionales
   * @param {string} message - Mensaje a clasificar
   * @param {string} userId - ID del usuario (opcional)
   */
  async classifyChatIntent(message, userId = null) {
    let url = `/chat/intent/classify?message=${encodeURIComponent(message)}`;
    if (userId) url += `&user_id=${userId}`;
    return this._request(url);
  }

  // ========================================
  // 🔧 ENDPOINTS DE PERSONALIZACIÓN BÁSICA
  // ========================================

  async getUserPersonalization(userId = null) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/personalization/${activeUserId}`);
  }

  async updateUserPersonalization(userId = null, preferences) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/personalization/${activeUserId}`, {
      method: 'POST',
      body: JSON.stringify(preferences)
    });
  }

  async sendFeedback(query, response, rating = null, comments = null) {
    return this._request('/feedback', {
      method: 'POST',
      body: JSON.stringify({
        user_id: this._currentUserId,
        query,
        response,
        rating,
        comments,
        categories: {},
        timestamp: new Date().toISOString()
      })
    });
  }

  // ========================================
  // 🧠 ENDPOINTS DE REFLECTION PATTERN
  // ========================================

  /**
   * Obtiene insights organizacionales del Reflection Pattern
   */
  async getOrganizationalInsights() {
    return this._request('/reflection/organizational-insights');
  }

  /**
   * Obtiene patrones de uso específicos de un usuario
   * @param {string} userId - ID del usuario
   */
  async getUserPatterns(userId = null) {
    const activeUserId = userId || this._currentUserId;
    return this._request(`/reflection/user-patterns/${activeUserId}`);
  }

  /**
   * Integra feedback del chat en el sistema de reflection
   * @param {Object} feedbackData - Datos de feedback para integración
   */
  async integrateFeedbackFromChat(feedbackData) {
    return this._request('/reflection/feedback-integration', {
      method: 'POST',
      body: JSON.stringify(feedbackData)
    });
  }

  // ========================================
  // 🏥 ENDPOINTS DE SISTEMA Y SALUD
  // ========================================

  async getHealth() {
    try {
      return await this._request('/health');
    } catch {
      return { status: 'ok', fallback: true };
    }
  }

  async getSystemStatus() {
    return this._request('/status');
  }

  async getDatabaseHealth() {
    return this._request('/database/health');
  }

  /**
   * Health check detallado de todos los componentes
   */
  async getDetailedHealth() {
    return this._request('/admin/health-detailed');
  }

  /**
   * Limpieza de sesiones del sistema
   */
  async cleanupSessions() {
    return this._request('/admin/session-cleanup');
  }

  // ========================================
  // 🌐 WEBSOCKET MEJORADO
  // ========================================

  createWebSocketConnection(userId = null) {
    const activeUserId = userId || this._currentUserId;
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + `/ws/${activeUserId}`;
    console.log(`🔗 Conectando WebSocket: ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);
    
    // Añadir manejo de errores mejorado
    ws.addEventListener('error', (error) => {
      console.error('❌ WebSocket Error:', error);
    });
    
    ws.addEventListener('open', () => {
      console.log('✅ WebSocket Connected');
    });
    
    ws.addEventListener('close', (event) => {
      console.log(`🔌 WebSocket Closed: ${event.code} - ${event.reason}`);
    });
    
    return ws;
  }

  // ========================================
  // 🚧 ENDPOINTS DRILL-DOWN (SIMULADOS)
  // ========================================

  async getClientesPorGestor(gestorId) {
    console.warn('Simulating getClientesPorGestor - endpoint not available in main.py');
    return { data: { clientes: [], total: 0 } };
  }

  async getContratosPorCliente(clienteId) {
    console.warn('Simulating getContratosPorCliente - endpoint not available in main.py');
    return { data: { contratos: [], total: 0 } };
  }

  async getMovimientosPorContrato(contratoId) {
    console.warn('Simulating getMovimientosPorContrato - endpoint not available in main.py');
    return { data: { movimientos: [], total: 0 } };
  }
}

// ========================================
// 📤 EXPORTACIONES
// ========================================

const api = new ApiService();

export default api;
export { api };

// ========================================
// 🛠️ UTILIDADES MEJORADAS
// ========================================

export const apiUtils = {
  formatPeriod: (period) => {
    if (!period) return null;
    if (typeof period === 'string' && period.length > 7) {
      return period.substring(0, 7);
    }
    return period;
  },
  
  formatGestorData: (gestor) => ({
    id: gestor.gestor_id || gestor.GESTOR_ID || gestor.id,
    nombre: gestor.nombre || gestor.desc_gestor || gestor.DESC_GESTOR,
    centro: gestor.centro || gestor.desc_centro || gestor.DESC_CENTRO,
    segmento: gestor.segmento || gestor.desc_segmento || gestor.DESC_SEGMENTO || 'No especificado'
  }),
  
  handleApiError: (error) => ({
    success: false,
    error: error.message || 'Error desconocido',
    timestamp: new Date().toISOString()
  }),

  // 🆕 Nuevas utilidades para endpoints avanzados
  formatChatPreferences: (prefs) => ({
    communication_style: prefs.communication_style || 'professional',
    technical_level: prefs.technical_level || 'intermediate',
    preferred_format: prefs.preferred_format || 'combined',
    response_length: prefs.response_length || 'medium'
  }),

  formatFeedbackData: (rating, comments, categories = {}) => ({
    rating,
    comments,
    categories,
    timestamp: new Date().toISOString()
  }),

  validateIntentResponse: (response) => {
    return {
      intent: response.intent_analysis?.intent || 'general_inquiry',
      confidence: response.intent_analysis?.confidence || 0.5,
      requires_cdg_agent: response.intent_analysis?.requires_cdg_agent || false,
      recommended_approach: response.intent_analysis?.recommended_approach || 'simple'
    };
  }
};

// ========================================
// 🎯 CONSTANTES PARA EL FRONTEND
// ========================================

export const API_CONSTANTS = {
  CHAT_INTENTS: {
    PERFORMANCE_ANALYSIS: 'performance_analysis',
    COMPARATIVE_ANALYSIS: 'comparative_analysis',
    DEVIATION_DETECTION: 'deviation_detection',
    INCENTIVE_ANALYSIS: 'incentive_analysis',
    BUSINESS_REVIEW: 'business_review',
    EXECUTIVE_SUMMARY: 'executive_summary',
    GENERAL_INQUIRY: 'general_inquiry'
  },
  
  PREFERENCE_OPTIONS: {
    COMMUNICATION_STYLE: ['professional', 'concise', 'detailed'],
    TECHNICAL_LEVEL: ['basic', 'intermediate', 'advanced'],
    PREFERRED_FORMAT: ['text', 'charts', 'combined'],
    RESPONSE_LENGTH: ['short', 'medium', 'detailed']
  },

  DEFAULT_PERIODO: '2025-10',
  DEFAULT_USER_ID: 'frontend_user'
};
