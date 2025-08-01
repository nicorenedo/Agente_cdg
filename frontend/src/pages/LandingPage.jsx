// src/pages/LandingPage.jsx
// Pantalla de selección entre Panel de Gestor y Panel de Dirección

import React from 'react';
import { Button, Row, Col } from 'antd';
import { useNavigate } from 'react-router-dom';
import theme from '../styles/theme';

// Importar assets corporativos
import BancaMarchLogo from '../assets/BancaMarchlogo.png';
import FondoInterfaz from '../assets/FondoInterfaz.png';

const LandingPage = () => {
  const navigate = useNavigate();

  const containerStyle = {
    height: '100vh',
    background: `linear-gradient(rgba(27, 94, 85, 0.7), rgba(18, 59, 54, 0.8)), url(${FondoInterfaz})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '2rem',
  };

  const logoStyle = {
    maxWidth: '280px',
    height: 'auto',
    marginBottom: '3rem',
    filter: 'brightness(1.1)',
  };

  const titleStyle = {
    color: '#FFFFFF',
    fontSize: '2.8rem',
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: '3rem',
    textShadow: '2px 2px 4px rgba(0, 0, 0, 0.3)',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  };

  const buttonStyle = {
    height: '70px',
    fontSize: '20px',
    fontWeight: '600',
    padding: '0 3rem',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    transition: 'all 0.3s ease',
  };

  const gestorButtonStyle = {
    ...buttonStyle,
    background: theme.colors.bmGreenLight,
    borderColor: theme.colors.bmGreenLight,
    color: '#FFFFFF',
  };

  const direccionButtonStyle = {
    ...buttonStyle,
    background: theme.colors.bmGreenPrimary,
    borderColor: theme.colors.bmGreenPrimary,
    color: '#FFFFFF',
  };

  return (
    <div style={containerStyle}>
      {/* Logo corporativo */}
      <img 
        src={BancaMarchLogo} 
        alt="Banca March" 
        style={logoStyle}
      />
      
      {/* Título principal */}
      <h1 style={titleStyle}>
        ¿Qué pantalla deseas ver?
      </h1>
      
      {/* Botones de selección */}
      <Row gutter={[32, 16]} justify="center">
        <Col>
          <Button
            size="large"
            type="primary"
            style={gestorButtonStyle}
            onClick={() => navigate('/gestor-dashboard')}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            }}
          >
            📊 PANEL DE GESTOR
          </Button>
        </Col>
        
        <Col>
          <Button
            size="large"
            type="primary"
            style={direccionButtonStyle}
            onClick={() => navigate('/direccion-dashboard')}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            }}
          >
            🏦 PANEL DE DIRECCIÓN
          </Button>
        </Col>
      </Row>
      
      {/* Información adicional */}
      <div style={{
        position: 'absolute',
        bottom: '2rem',
        color: 'rgba(255, 255, 255, 0.8)',
        fontSize: '14px',
        textAlign: 'center',
      }}>
        Agente CDG - Control de Gestión Inteligente<br />
        Banca March © 2025
      </div>
    </div>
  );
};

export default LandingPage;
