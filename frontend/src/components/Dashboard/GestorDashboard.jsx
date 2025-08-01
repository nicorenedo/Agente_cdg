// src/components/Dashboard/GestorDashboard.jsx
// Dashboard principal para gestores comerciales - Integra KPIs, gráficos y chat conversacional

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Spin, message, Button, Divider, Alert } from 'antd';
import { ReloadOutlined, DownloadOutlined, FileTextOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import KPICards from './KPICards';
import InteractiveCharts from './InteractiveCharts';
import ChatInterface from '../Chat/ChatInterface';
import api from '../../services/api';
import theme from '../../styles/theme';

const { Title, Paragraph, Text } = Typography;

const GestorDashboard = ({ userId, gestorId, periodo }) => {
  // Estados principales del dashboard
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Estados de datos
  const [gestorInfo, setGestorInfo] = useState({});
  const [kpis, setKpis] = useState({});
  const [previousKpis, setPreviousKpis] = useState({});
  const [chartData, setChartData] = useState([]);
  const [availableKpis, setAvailableKpis] = useState([]);
  const [comparativeData, setComparativeData] = useState([]);
  
  // Estados de UI
  const [selectedView, setSelectedView] = useState('performance');
  const [lastUpdate, setLastUpdate] = useState(null);

  // Cargar datos iniciales
  useEffect(() => {
    if (!gestorId) {
      setError('ID de gestor es requerido para mostrar el dashboard');
      setLoading(false);
      return;
    }

    fetchDashboardData();
  }, [gestorId, periodo]);

  // Función principal para cargar datos
  const fetchDashboardData = async (showRefreshing = false) => {
    if (showRefreshing) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      // Obtener performance del gestor
      const performanceResponse = await api.getGestorPerformance(gestorId, periodo);
      
      if (performanceResponse.data) {
        setGestorInfo(performanceResponse.data.gestor || {});
        setKpis(performanceResponse.data.kpis || {});
        
        // Preparar datos para gráficos (convirtiendo KPIs individuales a array para charting)
        const gestorForChart = {
          desc_gestor: performanceResponse.data.gestor?.desc_gestor || `Gestor ${gestorId}`,
          ...performanceResponse.data.kpis
        };
        setChartData([gestorForChart]);
        
        // Obtener KPIs disponibles
        const kpiKeys = Object.keys(performanceResponse.data.kpis || {});
        setAvailableKpis(kpiKeys);
      }

      // Obtener datos comparativos para contexto
      try {
        const comparativeResponse = await api.getComparativeRanking(periodo || '2025-07', 'margen_neto');
        if (comparativeResponse.data) {
          setComparativeData(comparativeResponse.data.ranking || []);
        }
      } catch (comparativeError) {
        console.warn('Error obteniendo datos comparativos:', comparativeError);
      }

      // Simular datos del período anterior para indicadores de tendencia
      // En producción, esto vendría del backend
      const simulatedPreviousKpis = Object.keys(kpis).reduce((acc, key) => {
        acc[key] = kpis[key] ? kpis[key] * (0.95 + Math.random() * 0.1) : null;
        return acc;
      }, {});
      setPreviousKpis(simulatedPreviousKpis);

      setLastUpdate(new Date());

    } catch (err) {
      console.error('Error cargando datos del dashboard:', err);
      setError('Error al cargar datos del gestor. Por favor, intenta nuevamente.');
      message.error('Error al cargar datos del gestor');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Manejar refresh manual
  const handleRefresh = () => {
    fetchDashboardData(true);
  };

  // Generar Business Review
  const handleGenerateReport = async () => {
    try {
      message.loading('Generando Business Review...', 2.5);
      
      const reportData = {
        user_id: userId,
        gestor_id: gestorId,
        periodo: periodo || '2025-07',
        include_charts: true,
        include_recommendations: true
      };

      const response = await api.generateBusinessReview(reportData);
      message.success('Business Review generado exitosamente');
      
      // Aquí podrías abrir el reporte en una nueva ventana o descargar
      console.log('Business Review generado:', response.data);
      
    } catch (error) {
      console.error('Error generando reporte:', error);
      message.error('Error al generar Business Review');
    }
  };

  // Renderizar estado de carga
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column',
        justifyContent: 'center', 
        alignItems: 'center',
        height: '60vh',
        backgroundColor: theme.colors.background 
      }}>
        <Spin size="large" />
        <Paragraph style={{ 
          marginTop: theme.spacing.lg, 
          color: theme.colors.textSecondary,
          fontSize: '16px'
        }}>
          Cargando datos del gestor...
        </Paragraph>
      </div>
    );
  }

  // Renderizar estado de error
  if (error) {
    return (
      <div style={{ padding: theme.spacing.xl }}>
        <Alert
          message="Error al cargar el dashboard"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => fetchDashboardData()}>
              Reintentar
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ 
      padding: theme.spacing.lg,
      minHeight: '100vh',
      backgroundColor: theme.colors.backgroundLight 
    }}>
      
      {/* Header del dashboard */}
      <Row justify="space-between" align="middle" style={{ marginBottom: theme.spacing.lg }}>
        <Col>
          <Title level={2} style={{ 
            color: theme.colors.bmGreenDark, 
            margin: 0,
            fontWeight: 600 
          }}>
            Dashboard del Gestor
          </Title>
          <Text style={{ 
            color: theme.colors.textSecondary,
            fontSize: '16px'
          }}>
            {gestorInfo.desc_gestor || `Gestor ${gestorId}`} - {gestorInfo.desc_centro || 'Centro'} 
            {periodo && ` | Período: ${periodo}`}
          </Text>
        </Col>
        
        <Col>
          <div style={{ display: 'flex', gap: theme.spacing.sm }}>
            <Button 
              icon={<ReloadOutlined />}
              loading={refreshing}
              onClick={handleRefresh}
              style={{ borderColor: theme.colors.bmGreenLight }}
            >
              Actualizar
            </Button>
            <Button 
              type="primary"
              icon={<FileTextOutlined />}
              onClick={handleGenerateReport}
              style={{ 
                backgroundColor: theme.colors.bmGreenPrimary,
                borderColor: theme.colors.bmGreenPrimary
              }}
            >
              Business Review
            </Button>
          </div>
        </Col>
      </Row>

      {/* Información de última actualización */}
      {lastUpdate && (
        <div style={{ 
          marginBottom: theme.spacing.md,
          padding: theme.spacing.sm,
          backgroundColor: theme.colors.background,
          borderRadius: 6,
          borderLeft: `4px solid ${theme.colors.bmGreenLight}`
        }}>
          <Text style={{ color: theme.colors.textSecondary, fontSize: '14px' }}>
            Última actualización: {lastUpdate.toLocaleString('es-ES')}
          </Text>
        </div>
      )}

      {/* Sección de KPIs principales */}
      <Card 
        title={
          <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
            📊 Indicadores Clave de Performance
          </span>
        }
        bordered={false}
        style={{ 
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: theme.spacing.lg
        }}
      >
        <KPICards kpis={kpis} previousKpis={previousKpis} />
      </Card>

      {/* Gráficos interactivos */}
      {availableKpis.length > 0 && (
        <InteractiveCharts 
          data={chartData} 
          availableKpis={availableKpis} 
          title="Análisis Visual de KPIs" 
          description="Visualización interactiva de tu performance vs otros gestores"
          onChartChange={(config) => console.log('Chart config changed:', config)}
        />
      )}

      {/* Sección de chat conversacional */}
      <Row gutter={[16, 16]} style={{ marginTop: theme.spacing.lg }}>
        <Col xs={24} lg={16}>
          <Card
            title={
              <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
                💬 Consulta Conversacional
              </span>
            }
            bordered={false}
            style={{ 
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              height: '500px'
            }}
          >
            <ChatInterface 
              userId={userId} 
              gestorId={gestorId} 
              periodo={periodo}
              initialMessages={[
                {
                  sender: 'agent',
                  text: `¡Hola! Soy tu asistente de Control de Gestión. Puedo ayudarte con:

• Análisis de tus KPIs y performance
• Comparativas con otros gestores
• Explicación de variaciones en comisiones
• Generación de reportes personalizados
• Modificación de visualizaciones

¿En qué puedo ayudarte hoy?`,
                  charts: [],
                  recommendations: []
                }
              ]}
            />
          </Card>
        </Col>

        {/* Panel lateral con información adicional */}
        <Col xs={24} lg={8}>
          <Card
            title="Información del Gestor"
            bordered={false}
            style={{ 
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              marginBottom: theme.spacing.md
            }}
          >
            <div style={{ lineHeight: 1.8 }}>
              <Text strong>Centro:</Text> <Text>{gestorInfo.desc_centro || 'No disponible'}</Text><br/>
              <Text strong>Segmento:</Text> <Text>{gestorInfo.desc_segmento || 'No disponible'}</Text><br/>
              <Text strong>ID Gestor:</Text> <Text>{gestorId}</Text><br/>
              <Text strong>Período Activo:</Text> <Text>{periodo || 'Actual'}</Text>
            </div>
          </Card>

          {/* Acciones rápidas */}
          <Card
            title="Acciones Rápidas"
            bordered={false}
            style={{ 
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
              <Button 
                block 
                onClick={handleGenerateReport}
                style={{ borderColor: theme.colors.bmGreenLight }}
              >
                📋 Generar Business Review
              </Button>
              <Button 
                block
                style={{ borderColor: theme.colors.bmGreenLight }}
                onClick={() => message.info('Funcionalidad próximamente disponible')}
              >
                📊 Ver Comparativa Detallada
              </Button>
              <Button 
                block
                style={{ borderColor: theme.colors.bmGreenLight }}
                onClick={() => message.info('Funcionalidad próximamente disponible')}
              >
                💰 Detalle de Incentivos
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Footer del dashboard */}
      <Divider />
      <div style={{ 
        textAlign: 'center', 
        color: theme.colors.textSecondary,
        fontSize: '14px'
      }}>
        Agente CDG - Control de Gestión Inteligente | Banca March © 2025
      </div>
    </div>
  );
};

GestorDashboard.propTypes = {
  userId: PropTypes.string.isRequired,
  gestorId: PropTypes.string.isRequired,
  periodo: PropTypes.string
};

export default GestorDashboard;
