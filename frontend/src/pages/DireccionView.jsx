// src/pages/DireccionView.jsx
// Página principal para directivos y Control de Gestión - Vista ejecutiva consolidada

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spin, Alert, Button, Card, Row, Col, Typography, Space } from 'antd';
import { ArrowLeftOutlined, DashboardOutlined, FileTextOutlined } from '@ant-design/icons';
import ControlGestionDashboard from '../components/Dashboard/ControlGestionDashboard';
import theme from '../styles/theme';

// Importar assets corporativos
import BancaMarchLogo from '../assets/BancaMarchlogo.png';

const { Title, Text } = Typography;

const DireccionView = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [userId] = useState('direccion_user_001'); // En producción vendría del auth
  const [currentPeriodo] = useState(new Date().toISOString().slice(0, 7)); // YYYY-MM formato

  useEffect(() => {
    // Simular validación de permisos y carga inicial
    const timer = setTimeout(() => {
      setLoading(false);
    }, 800);

    return () => clearTimeout(timer);
  }, []);

  // Header corporativo para la vista de dirección
  const renderDirectionHeader = () => (
    <Card 
      bordered={false}
      style={{ 
        marginBottom: theme.spacing.lg,
        background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}, ${theme.colors.bmGreenPrimary})`,
        color: 'white'
      }}
    >
      <Row justify="space-between" align="middle">
        <Col>
          <Space align="center" size="large">
            <img 
              src={BancaMarchLogo} 
              alt="Banca March" 
              style={{ height: '40px', filter: 'brightness(0) invert(1)' }}
            />
            <div>
              <Title 
                level={2} 
                style={{ 
                  color: 'white', 
                  margin: 0,
                  fontWeight: 600 
                }}
              >
                Panel Ejecutivo de Dirección
              </Title>
              <Text style={{ 
                color: 'rgba(255,255,255,0.9)', 
                fontSize: '16px' 
              }}>
                Control de Gestión Consolidado | Vista Estratégica
              </Text>
            </div>
          </Space>
        </Col>
        
        <Col>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/')}
              style={{ 
                borderColor: 'white',
                color: 'white',
                background: 'transparent'
              }}
              onMouseEnter={(e) => {
                e.target.style.backgroundColor = 'rgba(255,255,255,0.1)';
              }}
              onMouseLeave={(e) => {
                e.target.style.backgroundColor = 'transparent';
              }}
            >
              Volver a Selección
            </Button>
            
            <Button
              type="primary"
              icon={<FileTextOutlined />}
              style={{
                backgroundColor: theme.colors.bmGreenLight,
                borderColor: theme.colors.bmGreenLight
              }}
              onClick={() => {
                // Funcionalidad futura: generar reporte ejecutivo
                console.log('Generar reporte ejecutivo consolidado');
              }}
            >
              Reporte Ejecutivo
            </Button>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  // Métricas ejecutivas destacadas
  const renderExecutiveMetrics = () => (
    <Row gutter={[16, 16]} style={{ marginBottom: theme.spacing.lg }}>
      <Col xs={24} sm={12} lg={6}>
        <Card 
          bordered={false}
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${theme.colors.bmGreenPrimary}`
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <DashboardOutlined 
              style={{ 
                fontSize: '32px', 
                color: theme.colors.bmGreenPrimary,
                marginBottom: theme.spacing.sm
              }} 
            />
            <Title level={4} style={{ margin: 0, color: theme.colors.textPrimary }}>
              Vista Consolidada
            </Title>
            <Text style={{ color: theme.colors.textSecondary }}>
              Análisis integral de toda la red comercial
            </Text>
          </div>
        </Card>
      </Col>
      
      <Col xs={24} sm={12} lg={6}>
        <Card 
          bordered={false}
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${theme.colors.bmGreenLight}`
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <Title level={3} style={{ 
              margin: 0, 
              color: theme.colors.bmGreenPrimary,
              fontSize: '28px'
            }}>
              Real Time
            </Title>
            <Text style={{ color: theme.colors.textSecondary }}>
              Datos actualizados en tiempo real
            </Text>
          </div>
        </Card>
      </Col>
      
      <Col xs={24} sm={12} lg={6}>
        <Card 
          bordered={false}
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${theme.colors.success}`
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <Title level={3} style={{ 
              margin: 0, 
              color: theme.colors.success,
              fontSize: '28px'
            }}>
              AI Insights
            </Title>
            <Text style={{ color: theme.colors.textSecondary }}>
              Análisis inteligente con Azure OpenAI
            </Text>
          </div>
        </Card>
      </Col>
      
      <Col xs={24} sm={12} lg={6}>
        <Card 
          bordered={false}
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${theme.colors.info}`
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <Title level={3} style={{ 
              margin: 0, 
              color: theme.colors.info,
              fontSize: '28px'
            }}>
              Strategic
            </Title>
            <Text style={{ color: theme.colors.textSecondary }}>
              Decisiones estratégicas informadas
            </Text>
          </div>
        </Card>
      </Col>
    </Row>
  );

  // Renderizar loading
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: theme.colors.backgroundLight,
        background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}15, ${theme.colors.bmGreenPrimary}10)`
      }}>
        <Space direction="vertical" align="center" size="large">
          <img 
            src={BancaMarchLogo} 
            alt="Banca March" 
            style={{ height: '60px', marginBottom: theme.spacing.lg }}
          />
          <Spin size="large" />
          <div style={{ textAlign: 'center' }}>
            <Title level={3} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
              Iniciando Panel Ejecutivo
            </Title>
            <Text style={{ 
              color: theme.colors.textSecondary,
              fontSize: '16px',
              marginTop: theme.spacing.sm
            }}>
              Cargando datos consolidados y métricas estratégicas...
            </Text>
          </div>
        </Space>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: theme.colors.backgroundLight,
      background: `linear-gradient(180deg, ${theme.colors.backgroundLight} 0%, ${theme.colors.background} 100%)`
    }}>
      
      {/* Header ejecutivo */}
      {renderDirectionHeader()}
      
      {/* Métricas ejecutivas destacadas */}
      <div style={{ padding: `0 ${theme.spacing.lg}` }}>
        {renderExecutiveMetrics()}
      </div>
      
      {/* Dashboard principal de Control de Gestión */}
      <ControlGestionDashboard 
        userId={userId} 
        periodo={currentPeriodo}
      />
      
      {/* Footer ejecutivo */}
      <div style={{ 
        padding: theme.spacing.lg,
        textAlign: 'center',
        borderTop: `1px solid ${theme.colors.border}`,
        backgroundColor: theme.colors.background,
        marginTop: theme.spacing.xl
      }}>
        <Space direction="vertical" size="small">
          <Text style={{ 
            color: theme.colors.textSecondary,
            fontSize: '14px'
          }}>
            Panel Ejecutivo CDG - Banca March
          </Text>
          <Text style={{ 
            color: theme.colors.textSecondary,
            fontSize: '12px'
          }}>
            Sistema de Control de Gestión Inteligente con IA | © 2025 Todos los derechos reservados
          </Text>
        </Space>
      </div>
    </div>
  );
};

export default DireccionView;
