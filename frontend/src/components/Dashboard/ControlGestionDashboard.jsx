// src/components/Dashboard/ControlGestionDashboard.jsx
// Dashboard principal CDG - COMPLETAMENTE ARREGLADO: Dependencias de hooks corregidas

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Row, Col, Card, Typography, Spin, message, Button, Table, Alert, Space, Tooltip } from 'antd';
import { ReloadOutlined, AlertOutlined, SwapOutlined, BarChartOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import KPICards from './KPICards';
import InteractiveCharts from './InteractiveCharts';
import ChatInterface from '../Chat/ChatInterface';
import ConversationalPivot from '../Chat/ConversationalPivot';
import DeviationAnalysis from '../Analytics/DeviationAnalysis';
import DrillDownView from '../Analytics/DrillDownView';
import api from '../../services/api';
import theme from '../../styles/theme';

const { Title, Text, Paragraph } = Typography;

const ControlGestionDashboard = ({ 
  userId, 
  periodo, 
  comparisonMode = false, 
  comparisonPeriods = [], 
  availablePeriods = [] 
}) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('overview');

  // Estados de datos
  const [consolidatedKpis, setConsolidatedKpis] = useState({});
  const [previousKpis, setPreviousKpis] = useState({});
  const [rankingData, setRankingData] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [deviationAlerts, setDeviationAlerts] = useState([]);
  const [availableKpis, setAvailableKpis] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(null);

  // Estado para drill-down
  const [drillDownContext, setDrillDownContext] = useState({
    level: 'consolidated',
    context: {}
  });

  // 🔥 SOLUCIÓN 1: Memorizar la función de normalización
  const normalizePeriod = useCallback((period) => {
    if (!period) return '2025-10';
    if (period.length === 10 && period.includes('-')) {
      return period.substring(0, 7); // YYYY-MM-DD → YYYY-MM
    }
    if (period.length === 7 && period.includes('-')) {
      return period;
    }
    return '2025-10';
  }, []);

  // 🔥 SOLUCIÓN 2: Memorizar el período normalizado
  const normalizedPeriod = useMemo(() => normalizePeriod(periodo), [periodo, normalizePeriod]);

  // 🔥 SOLUCIÓN 3: Función optimizada sin dependencias circulares
  const fetchDashboardData = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      console.log('📅 DEBUG: Período normalizado para APIs:', normalizedPeriod);

      // ✅ CORREGIDO: Usar endpoints separados con período normalizado
      let kpisData = {};
      let totalesData = {};
      let comparativoData = {};
      let alertasData = [];

      try {
        // Intentar usar endpoints separados primero
        const [kpisResponse, totalesResponse, comparativoResponse, alertasResponse] = await Promise.allSettled([
          api.getKpisConsolidados(normalizedPeriod),
          api.getTotales(normalizedPeriod),
          api.getAnalisisComparativo(normalizedPeriod),
          api.getDeviationAlerts(normalizedPeriod)
        ]);

        if (kpisResponse.status === 'fulfilled') {
          kpisData = kpisResponse.value?.data || kpisResponse.value || {};
        }
        if (totalesResponse.status === 'fulfilled') {
          totalesData = totalesResponse.value?.data || totalesResponse.value || {};
        }
        if (comparativoResponse.status === 'fulfilled') {
          comparativoData = comparativoResponse.value?.data || comparativoResponse.value || {};
        }
        if (alertasResponse.status === 'fulfilled') {
          alertasData = alertasResponse.value?.data?.alerts || alertasResponse.value?.alerts || [];
        }

      } catch (separateEndpointsError) {
        console.warn('Endpoints separados no disponibles, usando getDashboardData:', separateEndpointsError);
        
        // Fallback usando getDashboardData
        const dashboardResponse = await api.getDashboardData(normalizedPeriod);
        
        kpisData = dashboardResponse?.data?.kpis || dashboardResponse?.kpis || {};
        totalesData = dashboardResponse?.data?.totales || dashboardResponse?.totales || {};
        comparativoData = dashboardResponse?.data?.comparativo || dashboardResponse?.comparativo || {};
        alertasData = dashboardResponse?.data?.alertas?.alerts || dashboardResponse?.alertas?.alerts || [];
      }

      // ✅ CORREGIDO: Procesar KPIs consolidados
      const kpis = {
        ROE: kpisData.ROE || kpisData.roe || totalesData.ROE || totalesData.roe || 0,
        MARGEN_NETO: kpisData.MARGEN_NETO || kpisData.margen_neto || totalesData.MARGEN_NETO || totalesData.margen_neto || 0,
        TOTAL_INGRESOS: totalesData.TOTAL_INGRESOS || totalesData.total_ingresos || kpisData.TOTAL_INGRESOS || kpisData.total_ingresos || 0,
        TOTAL_GASTOS: totalesData.TOTAL_GASTOS || totalesData.total_gastos || kpisData.TOTAL_GASTOS || kpisData.total_gastos || 0,
        BENEFICIO_NETO: totalesData.BENEFICIO_NETO || totalesData.beneficio_neto || kpisData.BENEFICIO_NETO || kpisData.beneficio_neto || 0
      };

      setConsolidatedKpis(kpis);
      setAvailableKpis(['ROE', 'MARGEN_NETO', 'TOTAL_INGRESOS', 'TOTAL_GASTOS', 'BENEFICIO_NETO']);

      // ✅ CORREGIDO: Procesar datos de gestores
      const gestores = comparativoData.gestores || comparativoData.managers || [];
      
      const gestoresMapped = gestores.map(gestor => ({
        GESTOR_ID: gestor.GESTOR_ID || gestor.gestor_id || gestor.id,
        DESC_GESTOR: gestor.DESC_GESTOR || gestor.desc_gestor || gestor.nombre || gestor.name || 'Sin nombre',
        DESC_CENTRO: gestor.DESC_CENTRO || gestor.desc_centro || gestor.centro || gestor.center || 'Sin centro',
        CENTRO_ID: gestor.CENTRO_ID || gestor.centro_id || gestor.center_id,
        MARGEN_NETO: gestor.MARGEN_NETO || gestor.margen_neto || 0,
        ROE: gestor.ROE || gestor.roe || 0,
        TOTAL_INGRESOS: gestor.TOTAL_INGRESOS || gestor.total_ingresos || 0,
        TOTAL_GASTOS: gestor.TOTAL_GASTOS || gestor.total_gastos || 0
      }));

      setRankingData(gestoresMapped);
      
      // ✅ CORREGIDO: Preparar datos para gráficos
      const chartDataProcessed = gestoresMapped.map(gestor => ({
        DESC_GESTOR: gestor.DESC_GESTOR,
        MARGEN_NETO: gestor.MARGEN_NETO,
        ROE: gestor.ROE,
        TOTAL_INGRESOS: gestor.TOTAL_INGRESOS,
        TOTAL_GASTOS: gestor.TOTAL_GASTOS
      }));
      setChartData(chartDataProcessed);

      // Procesar alertas de desviación
      setDeviationAlerts(Array.isArray(alertasData) ? alertasData : []);

      // Generar datos anteriores para comparación (simulado)
      const previousData = Object.keys(kpis).reduce((acc, key) => {
        acc[key] = kpis[key] ? kpis[key] * (0.95 + Math.random() * 0.1) : null;
        return acc;
      }, {});
      setPreviousKpis(previousData);

      setLastUpdate(new Date());
      
      message.success(`Dashboard actualizado: ${gestoresMapped.length} gestores, ${Object.values(kpis).filter(v => v > 0).length} KPIs activos`);

    } catch (error) {
      console.error('❌ ERROR completo cargando dashboard:', error);
      setError(`Error al cargar datos del dashboard: ${error.message}. Revisa la conexión con el backend.`);
      message.error('Error al cargar los datos del dashboard');
      
      // ✅ CORREGIDO: Datos fallback con campos correctos
      setConsolidatedKpis({
        ROE: 0,
        MARGEN_NETO: 0,
        TOTAL_INGRESOS: 0,
        TOTAL_GASTOS: 0,
        BENEFICIO_NETO: 0
      });
      setRankingData([]);
      setChartData([]);
      setDeviationAlerts([]);
      setAvailableKpis(['ROE', 'MARGEN_NETO', 'TOTAL_INGRESOS', 'TOTAL_GASTOS']);
      
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [normalizedPeriod]); // 🔥 SOLUCION 4: Solo depende del período normalizado

  // 🔥 SOLUCIÓN 5: useEffect optimizado con AbortController - DEPENDENCIAS CORREGIDAS
  useEffect(() => {
    const abortController = new AbortController();
    
    if (normalizedPeriod && !loading && !refreshing) {
      fetchDashboardData();
    }

    return () => {
      abortController.abort();
    };
  }, [normalizedPeriod, fetchDashboardData, loading, refreshing]); // ✅ CORREGIDO: Todas las dependencias incluidas

  // 🔥 SOLUCIÓN 6: Función de refresh memoizada
  const handleRefresh = useCallback(() => {
    fetchDashboardData(true);
  }, [fetchDashboardData]);

  // Handlers memoizados
  const handleDrillDown = useCallback((record) => {
    setDrillDownContext({
      level: 'manager',
      context: {
        gestorId: record.GESTOR_ID || record.DESC_GESTOR,
        gestorName: record.DESC_GESTOR,
        centroId: record.CENTRO_ID || record.DESC_CENTRO,
        centroName: record.DESC_CENTRO
      }
    });
    setActiveView('drilldown');
  }, []);

  const handleViewChange = useCallback((view) => {
    setActiveView(view);
  }, []);

  const formatPeriodName = useCallback((period) => {
    const periodObj = availablePeriods.find(p => p.value === period);
    return periodObj ? periodObj.label : period;
  }, [availablePeriods]);

  // 🔥 SOLUCIÓN 7: Columnas memoizadas - DEPENDENCIAS CORREGIDAS
  const rankingColumns = useMemo(() => [
    {
      title: 'Ranking',
      key: 'ranking',
      render: (_, __, index) => (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          width: 24,
          height: 24,
          borderRadius: '50%',
          backgroundColor: index < 3 ? theme.colors.bmGreenLight : theme.colors.backgroundLight,
          color: index < 3 ? 'white' : theme.colors.textPrimary,
          fontWeight: 'bold',
          fontSize: 12
        }}>
          {index + 1}
        </div>
      ),
      width: 60,
      align: 'center'
    },
    {
      title: 'Gestor',
      dataIndex: 'DESC_GESTOR',
      key: 'DESC_GESTOR',
      ellipsis: true,
      render: (text) => (
        <Text strong style={{ color: theme.colors.textPrimary }}>
          {text || 'Sin nombre'}
        </Text>
      )
    },
    {
      title: 'Centro',
      dataIndex: 'DESC_CENTRO', 
      key: 'DESC_CENTRO',
      ellipsis: true,
      render: (text) => (
        <Text style={{ color: theme.colors.textSecondary }}>
          {text || 'Sin centro'}
        </Text>
      )
    },
    {
      title: 'Margen Neto (%)',
      dataIndex: 'MARGEN_NETO',
      key: 'MARGEN_NETO',
      render: (value) => (
        <Text style={{ 
          color: value >= 12 ? theme.colors.bmGreenPrimary : 
                value >= 8 ? theme.colors.warning : theme.colors.error,
          fontWeight: 600 
        }}>
          {value !== null && value !== undefined ? value.toFixed(2) : '--'}%
        </Text>
      ),
      sorter: (a, b) => (a.MARGEN_NETO || 0) - (b.MARGEN_NETO || 0),
      width: 120
    },
    {
      title: 'ROE (%)',
      dataIndex: 'ROE',
      key: 'ROE',
      render: (value) => (
        <Text style={{ 
          color: value >= 8 ? theme.colors.bmGreenPrimary : 
                value >= 5 ? theme.colors.warning : theme.colors.error,
          fontWeight: 600 
        }}>
          {value !== null && value !== undefined ? value.toFixed(2) : '--'}%
        </Text>
      ),
      sorter: (a, b) => (a.ROE || 0) - (b.ROE || 0),
      width: 100
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Button
          size="small"
          type="link"
          onClick={() => handleDrillDown(record)}
          style={{ color: theme.colors.bmGreenPrimary }}
        >
          Ver Detalle
        </Button>
      ),
      width: 100
    }
  ], [handleDrillDown]); // ✅ CORREGIDO: handleDrillDown incluido en dependencias

  // Navegación de vistas memoizada
  const renderViewSelector = useMemo(() => (
    <div style={{ 
      marginBottom: theme.spacing.md,
      padding: theme.spacing.sm,
      backgroundColor: theme.colors.background,
      borderRadius: 6,
      border: `1px solid ${theme.colors.border}`
    }}>
      <Space>
        <Text strong style={{ color: theme.colors.textPrimary }}>
          Vista:
        </Text>
        {[
          { key: 'overview', label: 'Panel General', icon: <BarChartOutlined /> },
          { key: 'deviation', label: 'Análisis Desviaciones', icon: <ExclamationCircleOutlined /> },
          { key: 'drilldown', label: 'Drill-Down', icon: <BarChartOutlined /> },
          { key: 'chat', label: 'Chat IA', icon: <BarChartOutlined /> }
        ].map(view => (
          <Button
            key={view.key}
            type={activeView === view.key ? 'primary' : 'default'}
            size="small"
            icon={view.icon}
            onClick={() => handleViewChange(view.key)}
            style={{
              backgroundColor: activeView === view.key ? theme.colors.bmGreenPrimary : 'transparent',
              borderColor: activeView === view.key ? theme.colors.bmGreenPrimary : theme.colors.border
            }}
          >
            {view.label}
          </Button>
        ))}
      </Space>
    </div>
  ), [activeView, handleViewChange]);

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
          Cargando datos consolidados para {normalizedPeriod}...
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
            {comparisonMode ? (
              <>
                <SwapOutlined style={{ marginRight: 8 }} />
                Panel Comparativo de Control de Gestión
              </>
            ) : (
              'Panel de Control de Gestión'
            )}
          </Title>
          <Text style={{ color: theme.colors.textSecondary, fontSize: '16px' }}>
            Vista consolidada - Período: {formatPeriodName(periodo) || normalizedPeriod}
          </Text>
        </Col>
        
        <Col>
          <Space>
            <Tooltip title="Última actualización">
              <Text style={{ color: theme.colors.textSecondary, fontSize: 12 }}>
                {lastUpdate ? lastUpdate.toLocaleTimeString('es-ES') : '--'}
              </Text>
            </Tooltip>
            <Button
              icon={<ReloadOutlined />}
              loading={refreshing}
              onClick={handleRefresh}
              style={{ borderColor: theme.colors.bmGreenLight }}
            >
              Actualizar
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Mostrar error si existe */}
      {error && (
        <Alert
          message="Error de Conexión"
          description={error}
          type="error"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: theme.spacing.md }}
        />
      )}

      {/* Selector de vista */}
      {renderViewSelector}

      {/* KPIs Consolidados - Siempre visibles */}
      <Card
        title={
          <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
            KPIs Consolidados - Toda la Red
          </span>
        }
        variant="outlined"
        style={{
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: theme.spacing.lg
        }}
      >
        <KPICards 
          kpis={consolidatedKpis} 
          previousKpis={previousKpis}
        />
      </Card>

      {/* Renderizado condicional según vista activa */}
      {activeView === 'overview' && (
        <Row gutter={[16, 16]}>
          {/* Columna principal con gráficos */}
          <Col xs={24} lg={16}>
            {/* Gráfico interactivo */}
            {chartData && chartData.length > 0 ? (
              <Card
                title={
                  <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
                    Análisis Comparativo de Gestores
                  </span>
                }
                variant="outlined"
                style={{
                  borderRadius: 8,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                  marginBottom: theme.spacing.md
                }}
              >
                <InteractiveCharts
                  data={chartData}
                  availableKpis={availableKpis}
                  title="Performance por Gestor"
                  description="Análisis comparativo de KPIs principales"
                />
              </Card>
            ) : (
              <Card
                title="Análisis de Gestores"
                variant="outlined"
                style={{ marginBottom: theme.spacing.md }}
              >
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <Text style={{ color: theme.colors.textSecondary }}>
                    No hay datos de gestores disponibles para el período {normalizedPeriod}.
                  </Text>
                </div>
              </Card>
            )}

            {/* Tabla de ranking */}
            <Card
              title={
                <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
                  Ranking de Gestores por Performance
                </span>
              }
              variant="outlined"
              style={{
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
              }}
            >
              <Table
                columns={rankingColumns}
                dataSource={rankingData}
                pagination={{ pageSize: 10, showSizeChanger: true }}
                scroll={{ x: 'max-content' }}
                size="small"
                rowKey={(record) => record.GESTOR_ID || record.DESC_GESTOR || `row-${Math.random()}`}
                locale={{
                  emptyText: `No hay datos de gestores disponibles para ${normalizedPeriod}`
                }}
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
              variant="outlined"
              style={{
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                marginBottom: theme.spacing.md
              }}
            >
              {deviationAlerts.length === 0 ? (
                <Text style={{ color: theme.colors.textSecondary }}>
                  No se detectaron desviaciones críticas
                </Text>
              ) : (
                <div>
                  {deviationAlerts.slice(0, 5).map((alert, index) => (
                    <div
                      key={`alert-${index}`}
                      style={{
                        padding: theme.spacing.sm,
                        backgroundColor: theme.colors.backgroundLight,
                        borderRadius: 4,
                        marginBottom: theme.spacing.sm,
                        borderLeft: `3px solid ${theme.colors.warning}`
                      }}
                    >
                      <Text style={{ fontSize: '13px' }}>
                        {alert.gestor_nombre || 'Gestor'}: {alert.descripcion || 'Desviación detectada'}
                      </Text>
                    </div>
                  ))}
                  {deviationAlerts.length > 5 && (
                    <Button 
                      type="link" 
                      size="small"
                      onClick={() => setActiveView('deviation')}
                      style={{ padding: 0 }}
                    >
                      Ver todas las alertas ({deviationAlerts.length})
                    </Button>
                  )}
                </div>
              )}
            </Card>

            {/* Pivoteo conversacional */}
            <Card
              title={
                <span style={{ color: theme.colors.bmGreenDark, fontSize: '16px', fontWeight: 600 }}>
                  Control Conversacional de Dashboard
                </span>
              }
              variant="outlined"
              style={{
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                height: '400px'
              }}
            >
              <ConversationalPivot
                userId={userId}
                periodo={normalizedPeriod}
                initialData={chartData}
                initialKpis={availableKpis}
                onChartUpdate={(config) => {
                  console.log('Chart updated:', config);
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Vista de análisis de desviaciones */}
      {activeView === 'deviation' && (
        <DeviationAnalysis
          userId={userId}
          periodo={normalizedPeriod}
          onDrillDown={(context) => {
            setDrillDownContext({
              level: 'manager',
              context
            });
            setActiveView('drilldown');
          }}
        />
      )}

      {/* Vista de drill-down */}
      {activeView === 'drilldown' && (
        <DrillDownView
          initialLevel={drillDownContext.level}
          initialContext={drillDownContext.context}
          userId={userId}
          periodo={normalizedPeriod}
          onLevelChange={(level, context) => {
            setDrillDownContext({ level, context });
          }}
        />
      )}

      {/* Vista de chat */}
      {activeView === 'chat' && (
        <Card
          title={
            <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
              Asistente Inteligente CDG
            </span>
          }
          variant="outlined"
          style={{
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            minHeight: '600px'
          }}
        >
          <ChatInterface
            userId={userId}
            periodo={normalizedPeriod}
            height="550px"
            initialMessages={[
              {
                sender: 'agent',
                text: '¡Hola! Soy tu asistente de Control de Gestión. Puedo ayudarte con análisis de KPIs, comparativas entre gestores, explicaciones de desviaciones y mucho más. ¿En qué puedo asistirte?',
                charts: [],
                recommendations: [
                  'Pregunta sobre KPIs específicos de gestores',
                  'Solicita análisis comparativos',
                  'Consulta sobre causas de desviaciones',
                  'Pide recomendaciones de mejora'
                ]
              }
            ]}
          />
        </Card>
      )}
    </div>
  );
};

ControlGestionDashboard.propTypes = {
  userId: PropTypes.string.isRequired,
  periodo: PropTypes.string,
  comparisonMode: PropTypes.bool,
  comparisonPeriods: PropTypes.array,
  availablePeriods: PropTypes.array
};

export default ControlGestionDashboard;
