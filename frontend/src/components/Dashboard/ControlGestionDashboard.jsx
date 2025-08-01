// src/components/Dashboard/ControlGestionDashboard.jsx
// Dashboard especializado para el área de Control de Gestión

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Spin, message, Button, Table, Tag } from 'antd';
import { ReloadOutlined, AlertOutlined, TrendingUpOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import KPICards from './KPICards';
import InteractiveCharts from './InteractiveCharts';
import ChatInterface from '../Chat/ChatInterface';
import api from '../../services/api';
import theme from '../../styles/theme';

const { Title, Text, Paragraph } = Typography;

const ControlGestionDashboard = ({ userId, periodo }) => {
  // Estados principales
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Estados de datos
  const [consolidatedKpis, setConsolidatedKpis] = useState({});
  const [previousKpis, setPreviousKpis] = useState({});
  const [rankingData, setRankingData] = useState([]);
  const [deviationAlerts, setDeviationAlerts] = useState([]);
  const [availableKpis, setAvailableKpis] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Configuración de columnas para tabla de ranking
  const rankingColumns = [
    {
      title: 'Ranking',
      key: 'ranking',
      render: (_, __, index) => (
        <Tag color={index < 3 ? 'green' : 'blue'}>
          #{index + 1}
        </Tag>
      ),
      width: 80,
    },
    {
      title: 'Gestor',
      dataKey: 'desc_gestor',
      key: 'desc_gestor',
      ellipsis: true,
    },
    {
      title: 'Centro',
      dataKey: 'desc_centro',
      key: 'desc_centro',
      ellipsis: true,
    },
    {
      title: 'Margen Neto (%)',
      dataKey: 'margen_neto',
      key: 'margen_neto',
      render: (value) => (
        <Text style={{ 
          color: value >= 12 ? theme.colors.bmGreenPrimary : theme.colors.warning,
          fontWeight: 600 
        }}>
          {value ? value.toFixed(2) : '--'}%
        </Text>
      ),
      sorter: (a, b) => (a.margen_neto || 0) - (b.margen_neto || 0),
    },
    {
      title: 'ROE (%)',
      dataKey: 'roe',
      key: 'roe',
      render: (value) => (
        <Text style={{ 
          color: value >= 8 ? theme.colors.bmGreenPrimary : theme.colors.warning,
          fontWeight: 600 
        }}>
          {value ? value.toFixed(2) : '--'}%
        </Text>
      ),
      sorter: (a, b) => (a.roe || 0) - (b.roe || 0),
    }
  ];

  // Cargar datos del dashboard
  useEffect(() => {
    fetchDashboardData();
  }, [periodo]);

  const fetchDashboardData = async (showRefreshing = false) => {
    if (showRefreshing) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const currentPeriod = periodo || new Date().toISOString().slice(0, 7);

      // Obtener ranking de gestores para datos consolidados
      const rankingResponse = await api.getComparativeRanking(currentPeriod, 'margen_neto');
      if (rankingResponse.data && rankingResponse.data.ranking) {
        const ranking = rankingResponse.data.ranking;
        setRankingData(ranking);

        // Calcular KPIs consolidados del ranking
        if (ranking.length > 0) {
          const consolidatedData = {
            roe: ranking.reduce((sum, item) => sum + (item.roe || 0), 0) / ranking.length,
            margen_neto: ranking.reduce((sum, item) => sum + (item.margen_neto || 0), 0) / ranking.length,
            eficiencia: ranking.reduce((sum, item) => sum + (item.eficiencia || 75), 0) / ranking.length,
            total_ingresos: ranking.reduce((sum, item) => sum + (item.total_ingresos || 0), 0),
            total_gastos: ranking.reduce((sum, item) => sum + (item.total_gastos || 0), 0)
          };

          setConsolidatedKpis(consolidatedData);
          setAvailableKpis(Object.keys(consolidatedData));

          // Simular datos del período anterior para comparación
          const previousData = Object.keys(consolidatedData).reduce((acc, key) => {
            acc[key] = consolidatedData[key] ? consolidatedData[key] * (0.95 + Math.random() * 0.1) : null;
            return acc;
          }, {});
          setPreviousKpis(previousData);
        }
      }

      // Obtener alertas de desviación
      try {
        const alertsResponse = await api.getDeviationAlerts(currentPeriod, 12.0);
        if (alertsResponse.data) {
          setDeviationAlerts([
            ...(alertsResponse.data.precio_alerts || []),
            ...(alertsResponse.data.margen_anomalies || []),
            ...(alertsResponse.data.volumen_outliers || [])
          ]);
        }
      } catch (alertError) {
        console.warn('Error obteniendo alertas:', alertError);
      }

      setLastUpdate(new Date());

    } catch (err) {
      console.error('Error cargando dashboard de Control de Gestión:', err);
      setError('Error al cargar datos consolidados. Por favor, intenta nuevamente.');
      message.error('Error al cargar datos consolidados');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    fetchDashboardData(true);
  };

  // Renderizar loading
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '60vh'
      }}>
        <Spin size="large" />
        <Paragraph style={{ marginTop: theme.spacing.lg, color: theme.colors.textSecondary }}>
          Cargando datos consolidados...
        </Paragraph>
      </div>
    );
  }

  return (
    <div style={{
      padding: theme.spacing.lg,
      minHeight: '100vh',
      backgroundColor: theme.colors.backgroundLight
    }}>
      
      {/* Header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: theme.spacing.lg }}>
        <Col>
          <Title level={2} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
            Panel de Control de Gestión
          </Title>
          <Text style={{ color: theme.colors.textSecondary, fontSize: '16px' }}>
            Vista consolidada y análisis estratégico - Período: {periodo || 'Actual'}
          </Text>
        </Col>
        
        <Col>
          <Button
            icon={<ReloadOutlined />}
            loading={refreshing}
            onClick={handleRefresh}
            style={{ borderColor: theme.colors.bmGreenLight }}
          >
            Actualizar Datos
          </Button>
        </Col>
      </Row>

      {/* Información de actualización */}
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

      {/* KPIs Consolidados */}
      <Card
        title={
          <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
            📊 KPIs Consolidados - Toda la Red
          </span>
        }
        bordered={false}
        style={{
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: theme.spacing.lg
        }}
      >
        <KPICards kpis={consolidatedKpis} previousKpis={previousKpis} />
      </Card>

      {/* Layout principal */}
      <Row gutter={[16, 16]}>
        {/* Columna principal con gráficos */}
        <Col xs={24} lg={16}>
          {/* Gráfico de ranking */}
          {availableKpis.length > 0 && rankingData.length > 0 && (
            <InteractiveCharts
              data={rankingData}
              availableKpis={availableKpis}
              title="Análisis Comparativo de Gestores"
              description="Visualización del performance de todos los gestores de la red"
              onChartChange={(config) => console.log('Chart config:', config)}
            />
          )}

          {/* Tabla de ranking */}
          <Card
            title={
              <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
                🏆 Ranking de Gestores por Performance
              </span>
            }
            bordered={false}
            style={{
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              marginTop: theme.spacing.md
            }}
          >
            <Table
              columns={rankingColumns}
              dataSource={rankingData}
              pagination={{ pageSize: 10, showSizeChanger: true }}
              scroll={{ x: 'max-content' }}
              size="small"
              rowKey={(record) => record.gestor_id || record.desc_gestor}
            />
          </Card>
        </Col>

        {/* Columna lateral */}
        <Col xs={24} lg={8}>
          {/* Alertas de desviación */}
          <Card
            title={
              <span style={{ color: theme.colors.bmGreenDark, fontSize: '16px', fontWeight: 600 }}>
                <AlertOutlined style={{ marginRight: 8, color: theme.colors.warning }} />
                Alertas de Desviación
              </span>
            }
            bordered={false}
            style={{
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              marginBottom: theme.spacing.md
            }}
          >
            {deviationAlerts.length === 0 ? (
              <Text style={{ color: theme.colors.textSecondary }}>
                ✅ No se detectaron desviaciones críticas
              </Text>
            ) : (
              <div>
                {deviationAlerts.slice(0, 5).map((alert, index) => (
                  <div
                    key={index}
                    style={{
                      padding: theme.spacing.sm,
                      backgroundColor: theme.colors.backgroundLight,
                      borderRadius: 4,
                      marginBottom: theme.spacing.sm,
                      borderLeft: `3px solid ${theme.colors.warning}`
                    }}
                  >
                    <Text style={{ fontSize: '13px' }}>
                      {alert.desc_gestor || 'Gestor'}: {alert.descripcion || 'Desviación detectada'}
                    </Text>
                  </div>
                ))}
                {deviationAlerts.length > 5 && (
                  <Text style={{ color: theme.colors.textSecondary, fontStyle: 'italic' }}>
                    ... y {deviationAlerts.length - 5} alertas más
                  </Text>
                )}
              </div>
            )}
          </Card>

          {/* Chat conversacional */}
          <Card
            title={
              <span style={{ color: theme.colors.bmGreenDark, fontSize: '16px', fontWeight: 600 }}>
                💬 Consulta Estratégica
              </span>
            }
            bordered={false}
            style={{
              borderRadius: 8,
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              height: '400px'
            }}
          >
            <ChatInterface
              userId={userId}
              periodo={periodo}
              initialMessages={[
                {
                  sender: 'agent',
                  text: `¡Hola! Soy tu asistente de Control de Gestión para análisis estratégico. 

Puedo ayudarte con:

• Análisis consolidado de toda la red
• Identificación de mejores prácticas
• Análisis de desviaciones críticas  
• Generación de informes ejecutivos
• Comparativas entre centros y segmentos

¿Qué análisis necesitas?`,
                  charts: [],
                  recommendations: []
                }
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

ControlGestionDashboard.propTypes = {
  userId: PropTypes.string.isRequired,
  periodo: PropTypes.string
};

export default ControlGestionDashboard;
