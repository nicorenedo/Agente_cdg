// src/services/api.js
// Cliente API para conexión con backend CDG

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Configuración del cliente axios
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para manejo de errores
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

// ============================================================================
// SERVICIOS ESPECÍFICOS PARA ENDPOINTS CDG
// ============================================================================

const api = {
  // Servicios generales
  health: () => apiClient.get('/health'),
  status: () => apiClient.get('/status'),

  // Servicios de gestor
  getGestorPerformance: (gestorId, periodo = null) => {
    const params = periodo ? `?periodo=${periodo}` : '';
    return apiClient.get(`/gestor/${gestorId}/performance${params}`);
  },

  // Servicios comparativos
  getComparativeRanking: (periodo, metric = 'margen_neto') => 
    apiClient.get(`/comparative/ranking?periodo=${periodo}&metric=${metric}`),

  // Servicios de desviaciones
  getDeviationAlerts: (periodo, threshold = 15.0) =>
    apiClient.get(`/deviations/alerts?periodo=${periodo}&threshold=${threshold}`),

  // Servicios de incentivos
  getIncentiveSummary: (periodo, gestorId = null) => {
    const params = gestorId ? `?gestor_id=${gestorId}` : '';
    return apiClient.get(`/incentives/summary?periodo=${periodo}${params}`);
  },

  // Servicios de reportes
  generateBusinessReview: (data) =>
    apiClient.post('/reports/business_review', data),

  generateExecutiveSummary: (data) =>
    apiClient.post('/reports/executive_summary', data),

  // Servicios de personalización
  getPersonalization: (userId) =>
    apiClient.get(`/personalization/${userId}`),

  updatePersonalization: (userId, preferences) =>
    apiClient.post(`/personalization/${userId}`, preferences),

  // Servicios de feedback
  sendFeedback: (feedbackData) =>
    apiClient.post('/feedback', feedbackData),
};

export default api;
