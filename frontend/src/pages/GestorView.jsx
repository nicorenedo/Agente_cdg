// src/pages/GestorView.jsx
// Página principal para gestores comerciales - Wrapper del GestorDashboard

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Spin, Alert, Button } from 'antd';
import GestorDashboard from '../components/Dashboard/GestorDashboard';
import theme from '../styles/theme';

const GestorView = () => {
  const { gestorId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [userId] = useState('gestor_user_001'); // En producción vendría del auth

  useEffect(() => {
    // Simular validación inicial y establecer período actual
    const timer = setTimeout(() => {
      setLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: theme.colors.backgroundLight
      }}>
        <Spin size="large" />
        <p style={{ 
          marginTop: theme.spacing.lg,
          color: theme.colors.textSecondary,
          fontSize: '16px'
        }}>
          Inicializando dashboard del gestor...
        </p>
      </div>
    );
  }

  if (!gestorId) {
    return (
      <div style={{ 
        padding: theme.spacing.xl,
        backgroundColor: theme.colors.backgroundLight,
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <Alert
          message="Error de Acceso"
          description="No se ha especificado un ID de gestor válido para acceder al dashboard."
          type="error"
          showIcon
          action={
            <Button 
              type="primary" 
              onClick={() => navigate('/')}
              style={{
                backgroundColor: theme.colors.bmGreenPrimary,
                borderColor: theme.colors.bmGreenPrimary
              }}
            >
              Volver a Inicio
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <GestorDashboard 
      userId={userId} 
      gestorId={gestorId} 
      periodo={new Date().toISOString().slice(0, 7)} // YYYY-MM formato actual
    />
  );
};

export default GestorView;
