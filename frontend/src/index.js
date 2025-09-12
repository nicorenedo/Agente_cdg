// src/index.js
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import 'antd/dist/reset.css';
import reportWebVitals from './reportWebVitals';

// ✅ AGREGAR ESTO: Suprimir error de extensiones del navegador
if (process.env.NODE_ENV === 'development') {
  const originalConsoleError = console.error;
  console.error = function(...args) {
    // Filtrar el error específico de extensiones
    if (typeof args[0] === 'string' && 
        args[0].includes('Attempting to use a disconnected port object')) {
      return; // No mostrar este error
    }
    // Mostrar todos los demás errores normalmente
    originalConsoleError.apply(console, args);
  };
}

// ✅ CORREGIDO: Variables globales con puerto 8000 para chat
window.CDG_CONFIG = {
  appVersion: '1.0.0',
  buildTime: new Date().toISOString(),
  environment: process.env.NODE_ENV,
  apiUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  chatUrl: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'
};

// Obtener el elemento root del DOM
const container = document.getElementById('root');

// Verificar que el elemento root existe
if (!container) {
  throw new Error('Failed to find the root element. Make sure your public/index.html has a div with id="root"');
}

// Crear el root de React 18
const root = createRoot(container);

// Configuración para desarrollo
if (process.env.NODE_ENV === 'development') {
  console.log('%cCDG - Sistema de Control de Gestión Banca March', 
    'color: #1B5E55; font-size: 16px; font-weight: bold;'
  );
  console.log('%cIniciando aplicación...', 'color: #229B8B; font-size: 12px;');
  console.log('Configuración:', window.CDG_CONFIG);

  // Habilitar React DevTools
  if (typeof window !== 'undefined') {
    window.React = React;
  }
}

// Renderizar la aplicación
root.render(
  <App />
);

// Configuración de Web Vitals para monitoreo de rendimiento
const sendToAnalytics = ({ name, delta, value, id }) => {
  // Enviar métricas a servicio de analytics si está configurado
  if (process.env.REACT_APP_ANALYTICS_ENDPOINT) {
    fetch(process.env.REACT_APP_ANALYTICS_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        metric: name,
        value,
        delta,
        id,
        timestamp: Date.now(),
        page: window.location.pathname,
        userAgent: navigator.userAgent,
        app: 'cdg-frontend'
      })
    }).catch(error => {
      console.warn('Failed to send analytics:', error);
    });
  }

  // Log en desarrollo
  if (process.env.NODE_ENV === 'development') {
    console.log(`Web Vital - ${name}:`, { value, delta });
  }
};

// Medir rendimiento de la aplicación
reportWebVitals(sendToAnalytics);

// Manejo de errores no capturados
window.addEventListener('unhandledrejection', event => {
  console.error('Unhandled promise rejection:', event.reason);
  
  // En producción, enviar error a servicio de logging
  if (process.env.NODE_ENV === 'production' && process.env.REACT_APP_ERROR_LOGGING_ENDPOINT) {
    fetch(process.env.REACT_APP_ERROR_LOGGING_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'unhandledrejection',
        error: event.reason?.toString?.() || 'Unknown error',
        stack: event.reason?.stack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        app: 'cdg-frontend'
      })
    }).catch(() => {
      // Silently fail if logging service is unavailable
    });
  }
});

window.addEventListener('error', event => {
  console.error('Global error:', event.error);
  
  // En producción, enviar error a servicio de logging
  if (process.env.NODE_ENV === 'production' && process.env.REACT_APP_ERROR_LOGGING_ENDPOINT) {
    fetch(process.env.REACT_APP_ERROR_LOGGING_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'javascript_error',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        app: 'cdg-frontend'
      })
    }).catch(() => {
      // Silently fail if logging service is unavailable
    });
  }
});

// Detectar si el usuario está offline/online
window.addEventListener('online', () => {
  console.log('Conexión restaurada');
  window.dispatchEvent(new CustomEvent('cdg:online'));
});

window.addEventListener('offline', () => {
  console.log('Conexión perdida');
  window.dispatchEvent(new CustomEvent('cdg:offline'));
});

// Log de información de build en producción
if (process.env.NODE_ENV === 'production') {
  console.log(
    '%cCDG Banca March', 
    'color: #1B5E55; font-size: 14px; font-weight: bold;'
  );
  console.log(
    `%cVersión: ${window.CDG_CONFIG.appVersion} | Build: ${window.CDG_CONFIG.buildTime}`, 
    'color: #666; font-size: 11px;'
  );
}
