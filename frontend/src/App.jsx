// src/App.jsx
// Aplicación principal con routing y configuración completa integrada

import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, message, notification } from 'antd';
import { ErrorBoundary } from 'react-error-boundary';
import esES from 'antd/locale/es_ES';
import theme from './styles/theme';
import api from './services/api';
import chatService from './services/chatService';

// Importar páginas principales
import LandingPage from './pages/LandingPage';
import GestorView from './pages/GestorView';
import DireccionView from './pages/DireccionView';

console.log('🔍 Environment Variables:', {
  API_URL: process.env.REACT_APP_API_URL,
  CHAT_URL: process.env.REACT_APP_CHAT_API_URL,
  NODE_ENV: process.env.NODE_ENV
});

// Configuración completa de tema para Ant Design
const antdThemeConfig = {
  token: {
    ...theme.token,
    // Colores específicos de Ant Design
    colorPrimary: theme.colors.bmGreenPrimary,
    colorSuccess: theme.colors.bmGreenLight,
    colorWarning: theme.colors.warning,
    colorError: theme.colors.error,
    colorInfo: theme.colors.info,
    
    // Configuración de componentes
    borderRadius: 6,
    borderRadiusLG: 8,
    borderRadiusSM: 4,
    controlHeight: 32,
    controlHeightLG: 40,
    controlHeightSM: 24,
    
    // Tipografía
    fontSize: 14,
    fontSizeLG: 16,
    fontSizeSM: 12,
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    lineHeight: 1.5,
    
    // Colores de fondo
    colorBgContainer: theme.colors.background,
    colorBgElevated: theme.colors.background,
    colorBgLayout: theme.colors.backgroundLight,
    
    // Bordes y texto
    colorBorder: theme.colors.border,
    colorText: theme.colors.textPrimary,
    colorTextSecondary: theme.colors.textSecondary,
    colorTextTertiary: theme.colors.textLight,
    
    // Sombras
    boxShadow: theme.token.boxShadow,
    boxShadowSecondary: theme.token.boxShadowSecondary,
  },
  components: {
    Card: {
      borderRadius: 8,
      boxShadowTertiary: '0 2px 8px rgba(0,0,0,0.1)',
    },
    Button: {
      borderRadius: 6,
      fontWeight: 600,
      controlHeight: 32,
      controlHeightLG: 40,
      controlHeightSM: 24,
    },
    Table: {
      borderRadius: 8,
      headerBg: theme.colors.backgroundLight,
      headerColor: theme.colors.textPrimary,
    },
    Input: {
      borderRadius: 6,
      controlHeight: 32,
    },
    Select: {
      borderRadius: 6,
      controlHeight: 32,
    },
    DatePicker: {
      borderRadius: 6,
    },
    Modal: {
      borderRadius: 8,
    },
    Drawer: {
      borderRadius: 8,
    },
    Menu: {
      itemBorderRadius: 6,
    },
    Tabs: {
      borderRadius: 6,
    }
  },
};

// Componente de error boundary mejorado
const ErrorFallback = ({ error, resetErrorBoundary }) => {
  const [showDetails, setShowDetails] = useState(false);
  
  useEffect(() => {
    // Log del error para debugging
    console.error('Application Error:', error);
    
    // Notificar error crítico
    notification.error({
      message: 'Error Crítico',
      description: 'Se ha producido un error en la aplicación CDG',
      duration: 0, // No auto-close
    });
  }, [error]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      backgroundColor: theme.colors.backgroundLight,
      background: theme.colors.gradients.light,
      padding: theme.spacing.xl,
      textAlign: 'center',
    }}>
      <div style={{
        backgroundColor: theme.colors.background,
        padding: theme.spacing.xxl,
        borderRadius: theme.token.borderRadiusLG,
        boxShadow: theme.token.boxShadowSecondary,
        maxWidth: '600px',
        width: '100%'
      }}>
        <h1 style={{ 
          color: theme.colors.error,
          fontSize: '28px',
          marginBottom: theme.spacing.md,
          fontWeight: theme.typography.fontWeights.bold
        }}>
          🚨 Error en la Aplicación
        </h1>
        
        <p style={{ 
          color: theme.colors.textSecondary,
          marginBottom: theme.spacing.lg,
          fontSize: '16px',
          lineHeight: theme.typography.lineHeights.relaxed
        }}>
          Ha ocurrido un error inesperado en el sistema de Control de Gestión de Banca March. 
          Por favor, intenta recargar la aplicación o contacta al soporte técnico si el problema persiste.
        </p>
        
        <div style={{
          display: 'flex',
          gap: theme.spacing.md,
          justifyContent: 'center',
          marginBottom: theme.spacing.lg
        }}>
          <button
            onClick={resetErrorBoundary}
            style={{
              padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
              backgroundColor: theme.colors.bmGreenPrimary,
              color: 'white',
              border: 'none',
              borderRadius: theme.token.borderRadius,
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: theme.typography.fontWeights.semibold,
              transition: theme.transitions.normal,
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = theme.colors.bmGreenDark;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = theme.colors.bmGreenPrimary;
            }}
          >
            🔄 Reintentar
          </button>
          
          <button
            onClick={() => window.location.href = '/'}
            style={{
              padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
              backgroundColor: 'transparent',
              color: theme.colors.textPrimary,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.token.borderRadius,
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: theme.typography.fontWeights.medium,
              transition: theme.transitions.normal,
            }}
          >
            🏠 Volver al Inicio
          </button>
        </div>
        
        <div style={{ borderTop: `1px solid ${theme.colors.border}`, paddingTop: theme.spacing.md }}>
          <button
            onClick={() => setShowDetails(!showDetails)}
            style={{
              background: 'none',
              border: 'none',
              color: theme.colors.textSecondary,
              cursor: 'pointer',
              fontSize: '14px',
              textDecoration: 'underline'
            }}
          >
            {showDetails ? '▼' : '▶'} Mostrar detalles técnicos
          </button>
          
          {showDetails && (
            <div style={{
              marginTop: theme.spacing.md,
              padding: theme.spacing.md,
              backgroundColor: theme.colors.backgroundDark,
              borderRadius: theme.token.borderRadiusSM,
              textAlign: 'left',
              maxHeight: '200px',
              overflow: 'auto'
            }}>
              <pre style={{
                fontSize: '12px',
                color: theme.colors.error,
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}>
                <strong>Error:</strong> {error.message}
                {error.stack && (
                  <>
                    <br/><br/>
                    <strong>Stack trace:</strong>
                    <br/>
                    {error.stack}
                  </>
                )}
              </pre>
            </div>
          )}
        </div>
      </div>
      
      {/* Footer con información de contacto */}
      <div style={{
        marginTop: theme.spacing.xl,
        color: theme.colors.textSecondary,
        fontSize: '12px'
      }}>
        <p>Sistema CDG - Banca March | Soporte Técnico: soporte-cdg@bancamarch.es</p>
        <p>© 2025 Todos los derechos reservados</p>
      </div>
    </div>
  );
};

// Componente de loading global
const GlobalLoading = () => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    backgroundColor: theme.colors.backgroundLight,
    background: theme.colors.gradients.primary
  }}>
    <div style={{
      animation: 'spin 1s linear infinite',
      width: '40px',
      height: '40px',
      border: `4px solid rgba(255,255,255,0.3)`,
      borderTop: `4px solid white`,
      borderRadius: '50%',
      marginBottom: theme.spacing.lg
    }} />
    <p style={{
      color: 'white',
      fontSize: '16px',
      fontWeight: theme.typography.fontWeights.medium
    }}>
      Inicializando Sistema CDG...
    </p>
  </div>
);

const App = () => {
  const [isInitializing, setIsInitializing] = useState(true);
  const [systemHealth, setSystemHealth] = useState({
    api: false,
    chat: false
  });

  // Inicialización de la aplicación
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Verificar estado de los servicios
        const [apiAvailable, chatAvailable] = await Promise.all([
          api.getHealth().then(() => true).catch(() => false), // 
          chatService.isServiceAvailable().catch(() => false)
        ]);

        setSystemHealth({
          api: apiAvailable,
          chat: chatAvailable
        });

        // Configurar notificaciones globales
        message.config({
          top: 100,
          duration: 3,
          maxCount: 3,
        });

        notification.config({
          placement: 'topRight',
          duration: 4.5,
          rtl: false,
        });

        // Mostrar estado de servicios si hay problemas
        if (!apiAvailable) {
          notification.warning({
            message: 'Servicio Principal',
            description: 'API principal no disponible. Algunas funcionalidades pueden estar limitadas.',
            duration: 6,
          });
        }

        if (!chatAvailable) {
          console.warn('Chat service not available');
        }

        // Log de inicialización exitosa
        console.log(`🚀 CDG App initialized successfully`, {
          api: apiAvailable,
          chat: chatAvailable,
          timestamp: new Date().toISOString()
        });

      } catch (error) {
        console.error('Error initializing app:', error);
        notification.error({
          message: 'Error de Inicialización',
          description: 'Error al inicializar la aplicación. Algunas funcionalidades pueden no estar disponibles.',
          duration: 0,
        });
      } finally {
        // Simular tiempo de carga mínimo para UX
        setTimeout(() => {
          setIsInitializing(false);
        }, 1500);
      }
    };

    initializeApp();

    // Cleanup al desmontar
    return () => {
      chatService.cleanup();
    };
  }, []);

  // Mostrar loading durante inicialización
  if (isInitializing) {
    return <GlobalLoading />;
  }

  return (
    <ErrorBoundary 
      FallbackComponent={ErrorFallback}
      onReset={() => {
        // Limpiar estado y recargar
        window.location.reload();
      }}
      onError={(error, errorInfo) => {
        // Log detallado para debugging
        console.error('ErrorBoundary caught an error:', error, errorInfo);
        
        // Aquí podrías enviar el error a un servicio de logging
        // logErrorToService(error, errorInfo);
      }}
    >
      <ConfigProvider 
        theme={antdThemeConfig}
        locale={esES}
      >
        <Router>
          <div 
            className="App" 
            style={{ 
              fontFamily: theme.token.fontFamily,
              minHeight: '100vh',
              backgroundColor: theme.colors.backgroundLight
            }}
          >
            <Routes>
              {/* Página de selección de roles */}
              <Route path="/" element={<LandingPage />} />
              
              {/* Dashboard de gestor comercial */}
              <Route path="/gestor-dashboard" element={<GestorView />} />
              <Route path="/gestor-dashboard/:gestorId" element={<GestorView />} />
              
              {/* Dashboard de dirección/control de gestión */}
              <Route path="/direccion-dashboard" element={<DireccionView />} />
              
              {/* Redirecciones de compatibilidad */}
              <Route path="/gestor" element={<Navigate to="/gestor-dashboard" replace />} />
              <Route path="/direccion" element={<Navigate to="/direccion-dashboard" replace />} />
              <Route path="/dashboard" element={<Navigate to="/" replace />} />
              
              {/* Ruta catch-all - redirige a landing page */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            
            {/* Indicador de estado de servicios en desarrollo */}
            {process.env.NODE_ENV === 'development' && (
              <div style={{
                position: 'fixed',
                bottom: theme.spacing.sm,
                right: theme.spacing.sm,
                padding: theme.spacing.xs,
                backgroundColor: theme.colors.background,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.token.borderRadiusSM,
                fontSize: '10px',
                color: theme.colors.textSecondary,
                zIndex: theme.zIndex.toast,
                boxShadow: theme.token.boxShadow
              }}>
                API: <span style={{ color: systemHealth.api ? theme.colors.success : theme.colors.error }}>
                  {systemHealth.api ? '🟢' : '🔴'}
                </span>
                {' '}
                Chat: <span style={{ color: systemHealth.chat ? theme.colors.success : theme.colors.warning }}>
                  {systemHealth.chat ? '🟢' : '🟡'}
                </span>
              </div>
            )}
          </div>
        </Router>
      </ConfigProvider>
    </ErrorBoundary>
  );
};

// Añadir estilos de animación
const style = document.createElement('style');
style.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  /* Scrollbar personalizado para Banca March */
  ::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  
  ::-webkit-scrollbar-track {
    background: ${theme.colors.backgroundLight};
  }
  
  ::-webkit-scrollbar-thumb {
    background: ${theme.colors.bmGreenLight};
    border-radius: 3px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: ${theme.colors.bmGreenPrimary};
  }
  
  /* Smooth scrolling */
  html {
    scroll-behavior: smooth;
  }
`;
document.head.appendChild(style);

export default App;
