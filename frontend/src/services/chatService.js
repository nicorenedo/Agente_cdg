// src/services/chatService.js
// Servicio de chat completamente integrado con backend CDG - CORREGIDO

import axios from 'axios';

// ✅ CORREGIDO: Chat usa puerto 8000
const CHAT_API_URL = process.env.REACT_APP_CHAT_API_URL || 'http://localhost:8000';

// Cliente HTTP específico para chat
const chatClient = axios.create({
  baseURL: CHAT_API_URL,
  timeout: 45000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptores para el cliente de chat
chatClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    if (process.env.NODE_ENV === 'development') {
      console.log(`💬 Chat Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

chatClient.interceptors.response.use(
  (response) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`✅ Chat Response: ${response.config.method?.toUpperCase()} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    console.error('❌ Chat API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

class ChatService {
  constructor() {
    this.wsConnection = null;
    this.messageHandlers = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.heartbeatInterval = null;
    this.isConnecting = false;
  }

  async sendMessage(userId, message, options = {}) {
    if (!userId || !message?.trim()) {
      throw new Error('UserId y mensaje son requeridos');
    }

    const payload = {
      user_id: userId,
      message: message.trim(),
      gestor_id: options.gestorId || null,
      periodo: options.periodo || null,
      include_charts: options.includeCharts !== false,
      include_recommendations: options.includeRecommendations !== false,
      context: options.context || {},
      user_feedback: options.feedback || null,
      conversation_id: options.conversationId || null,
      timestamp: new Date().toISOString(),
      ...(options.context?.conversationalPivot && {
        pivot_request: true,
        current_chart: options.context.currentChart,
        requested_updates: options.context.requestedUpdates
      }),
      ...(options.ping && { ping: true })
    };

    try {
      const response = await this.retryRequest(
        () => chatClient.post('/chat', payload),
        3
      );

      return {
        response: response.data.response || response.data.message || 'Respuesta procesada',
        charts: response.data.charts || [],
        recommendations: response.data.recommendations || [],
        conversation_id: response.data.conversation_id,
        timestamp: response.data.timestamp || new Date().toISOString(),
        ...(response.data.chart_updates && { chart_updates: response.data.chart_updates })
      };

    } catch (error) {
      console.error('Error enviando mensaje al chat:', error);
      
      if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        return {
          response: 'Lo siento, el servicio de chat no está disponible en este momento. Por favor, verifica tu conexión e intenta nuevamente.',
          charts: [],
          recommendations: [
            'Verifica tu conexión a internet',
            'El servicio de chat puede estar temporalmente no disponible',
            'Contacta al soporte técnico si el problema persiste'
          ],
          error: 'CHAT_SERVICE_UNAVAILABLE'
        };
      } else if (error.response?.status >= 500) {
        return {
          response: 'Ha ocurrido un error interno en el sistema de chat. Nuestro equipo técnico ha sido notificado.',
          charts: [],
          recommendations: [
            'Intenta realizar la consulta nuevamente en unos minutos',
            'Si el problema persiste, contacta al soporte técnico'
          ],
          error: 'INTERNAL_SERVER_ERROR'
        };
      } else if (error.response?.status === 400) {
        return {
          response: 'No he podido procesar tu consulta. Por favor, reformula tu pregunta de manera más específica.',
          charts: [],
          recommendations: [
            'Intenta ser más específico en tu consulta',
            'Usa términos relacionados con KPIs, gestores, o control de gestión',
            'Ejemplo: "Muestra el ROE del gestor X" o "Compara los ingresos por centro"'
          ],
          error: 'BAD_REQUEST'
        };
      } else {
        throw error;
      }
    }
  }

  async retryRequest(requestFn, maxRetries = 3, baseDelay = 1000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        if (attempt === maxRetries) {
          throw error;
        }
        
        const delay = baseDelay * Math.pow(2, attempt - 1);
        console.log(`Reintentando request en ${delay}ms... (intento ${attempt}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  connectWebSocket(userId, onMessage, onError = null, onClose = null) {
    if (this.isConnecting || (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN)) {
      console.log('WebSocket ya está conectado o conectándose');
      return this.wsConnection;
    }

    this.isConnecting = true;
    // ✅ CORREGIDO: WebSocket usa puerto 8000
    const wsUrl = `ws://localhost:8000/ws/${userId}`;
    
    try {
      this.wsConnection = new WebSocket(wsUrl);

      this.wsConnection.onopen = () => {
        console.log(`✅ WebSocket conectado para usuario ${userId}`);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };

      this.wsConnection.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'heartbeat') {
            this.sendWebSocketMessage({ type: 'heartbeat_response', timestamp: new Date().toISOString() });
          } else if (data.type === 'chat_response') {
            onMessage(data);
          } else {
            onMessage(data);
          }
        } catch (error) {
          console.error('Error parseando mensaje WebSocket:', error);
        }
      };

      this.wsConnection.onerror = (error) => {
        console.error('❌ Error WebSocket:', error);
        this.isConnecting = false;
        if (onError) onError(error);
      };

      this.wsConnection.onclose = (event) => {
        console.log('WebSocket desconectado:', event.code, event.reason);
        this.isConnecting = false;
        this.stopHeartbeat();
        
        if (onClose) onClose(event);
        
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect(userId, onMessage, onError, onClose);
        }
      };

    } catch (error) {
      console.error('Error creando WebSocket:', error);
      this.isConnecting = false;
      if (onError) onError(error);
    }

    return this.wsConnection;
  }

  scheduleReconnect(userId, onMessage, onError, onClose) {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reintentando conexión WebSocket en ${delay}ms... (intento ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connectWebSocket(userId, onMessage, onError, onClose);
    }, delay);
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
        this.sendWebSocketMessage({ 
          type: 'heartbeat', 
          timestamp: new Date().toISOString() 
        });
      }
    }, 30000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  sendWebSocketMessage(message) {
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify(message));
      return true;
    } else {
      console.warn('WebSocket no está conectado');
      return false;
    }
  }

  disconnectWebSocket() {
    this.stopHeartbeat();
    if (this.wsConnection) {
      this.wsConnection.close(1000, 'Cliente desconectando');
      this.wsConnection = null;
    }
    this.reconnectAttempts = 0;
  }

  getWebSocketState() {
    if (!this.wsConnection) return 'DISCONNECTED';
    
    switch (this.wsConnection.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING';
      case WebSocket.OPEN: return 'OPEN';
      case WebSocket.CLOSING: return 'CLOSING';
      case WebSocket.CLOSED: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  }

  async getChatHistory(userId, limit = 50) {
    try {
      const response = await chatClient.get(`/chat/history/${userId}?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Error obteniendo historial de chat:', error);
      return { messages: [] };
    }
  }

  async resetChatSession(userId) {
    try {
      const response = await chatClient.post(`/chat/reset/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error reiniciando sesión de chat:', error);
      throw error;
    }
  }

  async getChatStatus() {
    try {
      const response = await chatClient.get('/chat/status');
      return response.data;
    } catch (error) {
      console.error('Error obteniendo estado del chat:', error);
      return { 
        status: 'unavailable', 
        message: 'Servicio de chat no disponible' 
      };
    }
  }

  getSessionId() {
    let sessionId = localStorage.getItem('chat_session_id');
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('chat_session_id', sessionId);
    }
    return sessionId;
  }

  clearSession() {
    localStorage.removeItem('chat_session_id');
  }

  async isServiceAvailable() {
    try {
      await this.getChatStatus();
      return true;
    } catch {
      return false;
    }
  }

  async sendPivotCommand(userId, command, chartConfig, options = {}) {
    return this.sendMessage(userId, command, {
      ...options,
      context: {
        conversationalPivot: true,
        currentChart: chartConfig,
        command: command
      }
    });
  }

  cleanup() {
    this.disconnectWebSocket();
    this.clearSession();
  }
}

// Instancia singleton del servicio de chat
const chatService = new ChatService();

// Limpiar recursos cuando la página se cierra
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    chatService.cleanup();
  });
}

export default chatService;
