// src/services/chatService.js
// Servicio de chat integrado con el agente CDG

import api from './api';

class ChatService {
  constructor() {
    this.wsConnection = null;
    this.messageHandlers = [];
  }

  // ============================================================================
  // COMUNICACIÓN REST CON CHAT AGENT
  // ============================================================================

  async sendMessage(userId, message, options = {}) {
    const payload = {
      user_id: userId,
      message: message,
      gestor_id: options.gestorId || null,
      periodo: options.periodo || null,
      include_charts: options.includeCharts !== false,
      include_recommendations: options.includeRecommendations !== false,
      context: options.context || {},
      user_feedback: options.feedback || null,
    };

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error enviando mensaje al chat:', error);
      throw error;
    }
  }

  // ============================================================================
  // COMUNICACIÓN WEBSOCKET PARA TIEMPO REAL
  // ============================================================================

  connectWebSocket(userId, onMessage, onError = null, onClose = null) {
    const wsUrl = `ws://localhost:8000/ws/${userId}`;
    
    this.wsConnection = new WebSocket(wsUrl);

    this.wsConnection.onopen = () => {
      console.log(`WebSocket conectado para usuario ${userId}`);
    };

    this.wsConnection.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parseando mensaje WebSocket:', error);
      }
    };

    this.wsConnection.onerror = (error) => {
      console.error('Error WebSocket:', error);
      if (onError) onError(error);
    };

    this.wsConnection.onclose = () => {
      console.log('WebSocket desconectado');
      if (onClose) onClose();
    };

    return this.wsConnection;
  }

  sendWebSocketMessage(message) {
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket no está conectado');
    }
  }

  disconnectWebSocket() {
    if (this.wsConnection) {
      this.wsConnection.close();
      this.wsConnection = null;
    }
  }

  // ============================================================================
  // SERVICIOS ADICIONALES DE CHAT
  // ============================================================================

  async getChatHistory(userId) {
    try {
      const response = await fetch(`http://localhost:8000/chat/history/${userId}`);
      return await response.json();
    } catch (error) {
      console.error('Error obteniendo historial de chat:', error);
      throw error;
    }
  }

  async resetChatSession(userId) {
    try {
      const response = await fetch(`http://localhost:8000/chat/reset/${userId}`, {
        method: 'POST',
      });
      return await response.json();
    } catch (error) {
      console.error('Error reiniciando sesión de chat:', error);
      throw error;
    }
  }

  // Función para enviar feedback del usuario al sistema de reflection
  async sendUserFeedback(userId, query, response, rating, comments = '') {
    const feedbackData = {
      user_id: userId,
      query: query,
      response: response,
      rating: rating,
      comments: comments,
    };

    return this.sendFeedback(feedbackData);
  }
}

// Instancia singleton del servicio de chat
const chatService = new ChatService();

export default chatService;
