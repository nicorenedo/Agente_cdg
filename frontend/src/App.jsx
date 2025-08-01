// src/App.jsx
// Aplicación principal con routing y configuración

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { ErrorBoundary } from 'react-error-boundary';
import theme from './styles/theme';

// Importar páginas principales
import LandingPage from './pages/LandingPage';
import GestorView from './pages/GestorView';
import DireccionView from './pages/DireccionView';

// Configuración de tema para Ant Design con colores corporativos Banca March
const antdThemeConfig = {
  token: theme.token,
  components: {
    Card: {
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    },
    Button: {
      borderRadius: 6,
      fontWeight: 600,
    },
    Table: {
      borderRadius: 8,
    },
    Input: {
      borderRadius: 6,
    },
  },
};

// Componente de error boundary corporativo
const ErrorFallback = ({ error, resetErrorBoundary }) => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh',
    backgroundColor: theme.colors.backgroundLight,
    padding: theme.spacing.xl,
    textAlign: 'center',
  }}>
    <h2 style={{ 
      color: theme.colors.error,
      fontSize: '24px',
      marginBottom: theme.spacing.md 
    }}>
      ¡Ops! Algo ha salido mal
    </h2>
    <p style={{ 
      color: theme.colors.textSecondary,
      marginBottom: theme.spacing.lg,
      maxWidth: '600px'
    }}>
      Ha ocurrido un error inesperado en la aplicación CDG. Por favor, intenta recargar la página.
    </p>
    <button
      onClick={resetErrorBoundary}
      style={{
        padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
        backgroundColor: theme.colors.bmGreenPrimary,
        color: 'white',
        border: 'none',
        borderRadius: 6,
        cursor: 'pointer',
        fontSize: '16px',
        fontWeight: 600,
      }}
    >
      Reintentar
    </button>
    
    {/* Información técnica del error (solo en desarrollo) */}
    <details style={{ 
      marginTop: theme.spacing.lg,
      maxWidth: '600px',
      textAlign: 'left'
    }}>
      <summary style={{ 
        color: theme.colors.textSecondary,
        cursor: 'pointer',
        marginBottom: theme.spacing.sm
      }}>
        Detalles técnicos
      </summary>
      <pre style={{
        backgroundColor: theme.colors.background,
        padding: theme.spacing.sm,
        borderRadius: 4,
        overflow: 'auto',
        fontSize: '12px',
        color: theme.colors.error
      }}>
        {error.message}
      </pre>
    </details>
  </div>
);

const App = () => {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <ConfigProvider theme={antdThemeConfig}>
        <Router>
          <div className="App" style={{ 
            fontFamily: theme.token.fontFamily,
            minHeight: '100vh'
          }}>
            <Routes>
              {/* Página de selección de roles */}
              <Route path="/" element={<LandingPage />} />
              
              {/* Dashboard de gestor comercial */}
              <Route path="/gestor-dashboard" element={<GestorView />} />
              <Route path="/gestor-dashboard/:gestorId" element={<GestorView />} />
              
              {/* Dashboard de dirección/control de gestión */}
              <Route path="/direccion-dashboard" element={<DireccionView />} />
              
              {/* Ruta catch-all - redirige a landing page */}
              <Route path="*" element={<LandingPage />} />
            </Routes>
          </div>
        </Router>
      </ConfigProvider>
    </ErrorBoundary>
  );
};

export default App;
