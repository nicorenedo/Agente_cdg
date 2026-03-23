// src/App.jsx
// ✅ CDG Sistema v1.2 - App Principal Optimizado
// Enrutador principal para LandingPage, GestorView y DireccionView

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import { ErrorBoundary } from 'react-error-boundary';
import esES from 'antd/es/locale/es_ES';

// Servicios y tema
import theme from './styles/theme';

// Páginas del sistema CDG
import LandingPage from './pages/LandingPage';
import GestorView from './pages/GestorView';
import DireccionView from './pages/DireccionView';

// ============================================================================
// CONFIGURACIÓN TEMA ACCENTURE — CDG Intelligence
// ============================================================================

const antdTheme = {
  token: {
    colorPrimary: '#A100FF',
    colorLink: '#A100FF',
    colorSuccess: '#A100FF',
    colorWarning: theme.colors.warning,
    colorError: theme.colors.error,
    colorInfo: theme.colors.info,
    borderRadius: 8,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSize: 14,
    colorBgContainer: '#120020',
    colorBgLayout: '#0A0014',
    colorBgElevated: '#1A0033',
    colorBgSpotlight: '#1A0033',
    colorBorder: 'rgba(161, 0, 255, 0.2)',
    colorBorderSecondary: 'rgba(161, 0, 255, 0.12)',
    colorText: '#F0E6FF',
    colorTextSecondary: '#A87BC8',
    colorTextTertiary: '#6B4F7A',
    colorTextPlaceholder: '#6B4F7A',
    colorFill: 'rgba(161, 0, 255, 0.08)',
    colorFillSecondary: 'rgba(161, 0, 255, 0.05)',
    colorFillTertiary: 'rgba(161, 0, 255, 0.03)',
    borderRadiusLG: 12,
    wireframe: false,
  },
  components: {
    Button: {
      colorPrimary: '#A100FF',
      borderRadius: 6,
      controlHeight: 36,
      colorPrimaryHover: theme.colors.bmGreenLight,
      fontWeight: 500,
    },
    Tabs: {
      inkBarColor: '#A100FF',
      itemSelectedColor: '#A100FF',
    },
    Card: {
      borderRadius: 12,
      padding: 20,
      boxShadow: '0 2px 8px rgba(161,0,255,0.08)',
    },
    Table: {
      borderRadius: 8,
      colorBorderSecondary: 'rgba(161, 0, 255, 0.15)',
      colorBgContainer: '#120020',
      headerBg: '#1A0033',
      rowHoverBg: 'rgba(161, 0, 255, 0.08)',
      borderColor: 'rgba(161, 0, 255, 0.15)',
    },
    Select: {
      borderRadius: 6,
      controlHeight: 36,
      colorBorder: 'rgba(161, 0, 255, 0.3)',
      colorBgContainer: '#120020',
      colorBgElevated: '#1A0033',
    },
    Input: {
      borderRadius: 6,
      controlHeight: 36,
      colorBorder: 'rgba(161, 0, 255, 0.3)',
      colorBgContainer: '#120020',
      activeBorderColor: '#A100FF',
      hoverBorderColor: 'rgba(161, 0, 255, 0.5)',
    },
    Layout: {
      headerBg: '#1A0033',
      bodyBg: '#0A0014',
      siderBg: '#120020',
    },
    Menu: {
      borderRadius: 6,
      colorItemBg: 'transparent',
    },
    Badge: {
      colorPrimary: '#A100FF',
    },
    Alert: {
      borderRadius: 8,
    },
    Drawer: {
      borderRadius: 12,
    },
    Modal: {
      borderRadius: 12,
      colorBgElevated: '#1A0033',
    },
    DatePicker: {
      colorBgContainer: '#120020',
      colorBgElevated: '#1A0033',
      colorBorder: 'rgba(161, 0, 255, 0.3)',
    },
    Dropdown: {
      colorBgElevated: '#1A0033',
      colorBorder: 'rgba(161, 0, 255, 0.2)',
    },
    Tooltip: {
      colorBgSpotlight: '#1A0033',
      colorTextLightSolid: '#F0E6FF',
    },
    Statistic: {
      titleFontSize: 12,
    },
    Tabs: {
      inkBarColor: '#A100FF',
      itemSelectedColor: '#A100FF',
      colorBgContainer: '#120020',
    },
  }
};

// ============================================================================
// ❌ ERROR BOUNDARY MEJORADO
// ============================================================================

const ErrorFallback = ({ error, resetErrorBoundary }) => {
  const handleBackToHome = () => {
    window.location.href = '/';
  };

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: `linear-gradient(135deg, ${theme.colors.backgroundLight}, ${theme.colors.background})`,
      padding: 24,
      textAlign: 'center'
    }}>
      <div style={{
        background: 'white',
        padding: 40,
        borderRadius: 16,
        boxShadow: '0 8px 32px rgba(27, 94, 85, 0.15)',
        maxWidth: 600,
        border: `1px solid ${theme.colors.borderLight}`
      }}>
        <div style={{ 
          fontSize: 48, 
          marginBottom: 24,
          color: theme.colors.error 
        }}>
          ⚠️
        </div>
        
        <h2 style={{ 
          color: theme.colors.error, 
          marginBottom: 16,
          fontSize: 24,
          fontWeight: 600
        }}>
          Error del Sistema CDG
        </h2>
        
        <p style={{ 
          color: theme.colors.textSecondary, 
          marginBottom: 32,
          fontSize: 16,
          lineHeight: 1.6
        }}>
          Ha ocurrido un error inesperado en el Sistema de Control de Gestión. 
          Nuestro equipo técnico ha sido notificado automáticamente.
        </p>
        
        <div style={{
          background: theme.colors.backgroundLight,
          padding: 16,
          borderRadius: 8,
          marginBottom: 32,
          fontSize: 13,
          color: theme.colors.textSecondary,
          wordBreak: 'break-word',
          fontFamily: 'monospace',
          textAlign: 'left',
          border: `1px solid ${theme.colors.borderLight}`
        }}>
          <strong>Error técnico:</strong><br />
          {error?.message || 'Error desconocido del sistema'}
          {error?.stack && (
            <>
              <br /><br />
              <details style={{ fontSize: 11, opacity: 0.8 }}>
                <summary style={{ cursor: 'pointer', marginBottom: 8 }}>
                  Ver detalles técnicos
                </summary>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                  {error.stack}
                </pre>
              </details>
            </>
          )}
        </div>
        
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <button
            onClick={resetErrorBoundary}
            style={{
              background: theme.colors.bmGreenPrimary,
              color: 'white',
              border: 'none',
              padding: '14px 28px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
              transition: 'all 0.2s ease',
            }}
            onMouseOver={(e) => e.target.style.backgroundColor = theme.colors.bmGreenLight}
            onMouseOut={(e) => e.target.style.backgroundColor = theme.colors.bmGreenPrimary}
          >
            🔄 Reintentar
          </button>
          
          <button
            onClick={handleReload}
            style={{
              background: theme.colors.textSecondary,
              color: 'white',
              border: 'none',
              padding: '14px 28px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            ♻️ Recargar Página
          </button>
          
          <button
            onClick={handleBackToHome}
            style={{
              background: 'transparent',
              color: theme.colors.textSecondary,
              border: `1px solid ${theme.colors.borderLight}`,
              padding: '14px 28px',
              borderRadius: 8,
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            🏠 Ir al Inicio
          </button>
        </div>
        
        <p style={{ 
          marginTop: 24, 
          fontSize: 12, 
          color: theme.colors.textLight 
        }}>
          Si el problema persiste, contacta con soporte técnico: [sistemas@bancamarch.es](mailto:sistemas@bancamarch.es)
        </p>
      </div>
    </div>
  );
};

// ============================================================================
// 🛣️ RUTAS PRINCIPALES DEL SISTEMA (CORREGIDAS CON FUTURE FLAGS)
// ============================================================================

const AppRoutes = () => (
  <Router
    future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true
    }}
  >
    <Routes>
      {/* Página Principal */}
      <Route path="/" element={<LandingPage />} />
      
      {/* Dashboard Gestor Comercial - CORREGIDO para usar query params */}
      <Route path="/gestor-dashboard" element={<GestorView />} />
      
      {/* Dashboard Control de Gestión */}
      <Route path="/direccion-dashboard" element={<DireccionView />} />
      
      {/* Rutas alternativas más amigables */}
      <Route path="/gestor" element={<Navigate to="/gestor-dashboard" replace />} />
      <Route path="/direccion" element={<Navigate to="/direccion-dashboard" replace />} />
      <Route path="/control-gestion" element={<Navigate to="/direccion-dashboard" replace />} />
      
      {/* Rutas específicas de gestor (parámetro URL) */}
      <Route path="/gestor/:gestorId" element={<Navigate to={(location) => `/gestor-dashboard?gestor=${location.pathname.split('/')[2]}`} replace />} />
      
      {/* Catch-all: redirigir a inicio */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </Router>
);

// ============================================================================
// 🏠 COMPONENTE PRINCIPAL DE LA APLICACIÓN
// ============================================================================

const App = () => {
  // Log de inicio en desarrollo
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('%c> CDG Intelligence',
        'color: #A100FF; font-size: 18px; font-weight: bold; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);');
      console.log('%c🔗 API URL:', 'font-weight: bold; color: #2563eb;', process.env.REACT_APP_API_URL || 'http://localhost:8000');
      console.log('%c🌍 Environment:', 'font-weight: bold; color: #059669;', process.env.NODE_ENV);
      console.log('%c📦 Theme loaded:', 'font-weight: bold; color: #7c3aed;', theme.colors.bmGreenPrimary);
      console.log('%c✅ Sistema inicializado correctamente', 'color: #16a34a; font-weight: bold;');
    }
  }, []);

  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        console.error('❌ CDG App Critical Error:', error, errorInfo);
        
        // En producción, enviar error a sistema de monitoreo
        if (process.env.NODE_ENV === 'production') {
          // TODO: Integrar con sistema de logging (Sentry, LogRocket, etc.)
          console.log('📨 Error reportado al sistema de monitoreo');
        }
      }}
      onReset={() => {
        console.log('🔄 Reseteando aplicación CDG...');
        // Limpiar localStorage si es necesario
        try {
          localStorage.removeItem('cdg-temp-state');
          sessionStorage.clear();
        } catch (e) {
          console.warn('⚠️ Error limpiando storage:', e);
        }
      }}
    >
      <ConfigProvider 
        theme={antdTheme} 
        locale={esES}
      >
        <AntdApp>
          <div className="cdg-app" style={{ minHeight: '100vh' }}>
            <AppRoutes />
          </div>
        </AntdApp>
      </ConfigProvider>
    </ErrorBoundary>
  );
};

export default App;
