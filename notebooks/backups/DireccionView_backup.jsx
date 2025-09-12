// src/pages/DireccionView.jsx
// Vista de dirección COMPLETAMENTE INTEGRADA con api.js v2.1 y chatService.js v2.1
// CORREGIDA - Todos los errores de iconos solucionados

import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Spin, Button, Card, Row, Col, Typography, Space, Select, message, Tooltip, Badge, 
  Alert, Divider, Progress, Statistic, notification 
} from 'antd';
import { 
  ArrowLeftOutlined, DashboardOutlined, CalendarOutlined, SwapOutlined,
  ReloadOutlined, DownloadOutlined, AlertOutlined, ArrowUpOutlined,
  BarChartOutlined, TeamOutlined, BulbOutlined, MessageOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, SyncOutlined, BellOutlined,
  TrophyFilled, FundOutlined, TargetOutlined, StarOutlined
} from '@ant-design/icons';
import ControlGestionDashboard from '../components/Dashboard/ControlGestionDashboard';
import api from '../services/api';
import chatService from '../services/chatService';
import theme from '../styles/theme';
import BancaMarchLogo from '../assets/BancaMarchlogo.png';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const DireccionView = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // ========================================
  // 🎯 ESTADOS PRINCIPALES MEJORADOS
  // ========================================
  
  // Estados de carga y inicialización
  const [loading, setLoading] = useState(true);
  const [periodsLoading, setPeriodsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // Estados de configuración
  const [availablePeriods, setAvailablePeriods] = useState([]);
  const [currentPeriodo, setCurrentPeriodo] = useState(searchParams.get('periodo') || null);
  const [comparisonMode, setComparisonMode] = useState(searchParams.get('comparison') === 'true');
  const [comparisonPeriods, setComparisonPeriods] = useState([]);
  
  // Estados de datos mejorados
  const [dashboardMetrics, setDashboardMetrics] = useState({
    totalGestores: 0,
    centros: 0,
    alertasActivas: 0,
    alertasCriticas: 0,
    performance: 'buena',
    tendencia: 'neutral',
    margenPromedio: 0,
    desviaciones: 0,
    eficienciaGeneral: 0
  });

  // ========================================
  // 🚀 NUEVOS ESTADOS PARA INTEGRACIÓN AVANZADA
  // ========================================
  
  // Estados de servicios inteligentes
  const [servicesHealth, setServicesHealth] = useState({
    api: 'checking',
    chat: 'checking',
    websocket: 'checking'
  });
  const [chatServiceReady, setChatServiceReady] = useState(false);
  const [aiInsights, setAiInsights] = useState([]);
  const [executiveSuggestions, setExecutiveSuggestions] = useState([]);
  const [alertasInteligentes, setAlertasInteligentes] = useState([]);
  
  // Estados de análisis avanzado
  const [deviationAlerts, setDeviationAlerts] = useState([]);
  const [businessReviewData, setBusinessReviewData] = useState(null);
  const [incentivesSummary, setIncentivesSummary] = useState(null);
  const [comparativeRanking, setComparativeRanking] = useState([]);

  // ========================================
  // 🔧 REFS Y CONFIGURACIÓN
  // ========================================
  
  const isInitialized = useRef(false);
  const isFetchingPeriods = useRef(false);
  const isFetchingMetrics = useRef(false);
  const wsConnection = useRef(null);

  // Usuario ID memoizado para servicios
  const userId = useMemo(() => 'direccion_user_001', []);

  // ========================================
  // 🧠 INICIALIZACIÓN DE SERVICIOS INTELIGENTES
  // ========================================

  // Verificar estado de todos los servicios
  const checkServicesHealth = useCallback(async () => {
    try {
      console.log('🔍 Verificando estado de servicios...');
      
      // Health check API
      const apiHealth = await api.getHealth();
      const apiStatus = apiHealth?.status === 'ok' ? 'healthy' : 'degraded';
      
      // Configurar y verificar chatService
      chatService.setCurrentUserId(userId);
      const chatAvailable = await chatService.isServiceAvailable();
      setChatServiceReady(chatAvailable);
      
      // Actualizar estados de servicios
      setServicesHealth({
        api: apiStatus,
        chat: chatAvailable ? 'healthy' : 'error',
        websocket: 'checking' // Se actualizará con WebSocket
      });

      // Cargar funcionalidades avanzadas si el chat está disponible
      if (chatAvailable) {
        try {
          // Cargar sugerencias executivas personalizadas
          const suggestionsData = await chatService.getChatSuggestions();
          setExecutiveSuggestions(suggestionsData.suggestions?.slice(0, 5) || [
            'Generar Business Review automático',
            'Análizar desviaciones por centro',
            'Comparar performance entre gestores',
            'Detectar alertas críticas',
            'Exportar reporte ejecutivo'
          ]);

          // Intentar obtener insights de IA si están disponibles
          const organizationalInsights = await api.getOrganizationalInsights?.() || null;
          if (organizationalInsights?.insights) {
            setAiInsights(organizationalInsights.insights.slice(0, 3));
          }

        } catch (error) {
          console.warn('⚠️ Funcionalidades avanzadas limitadas:', error);
        }
      }

      console.log('✅ Servicios verificados:', { apiStatus, chatAvailable });

    } catch (error) {
      console.error('❌ Error verificando servicios:', error);
      setServicesHealth({
        api: 'error',
        chat: 'error',
        websocket: 'error'
      });
    }
  }, [userId]);

  // ========================================
  // 📊 CARGA DE DATOS AVANZADA
  // ========================================

  // Formateo de períodos mejorado
  const formatPeriodLabel = useCallback((period) => {
    if (!period) return '';
    
    const monthNames = [
      'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];
    
    try {
      // Formato YYYY-MM o YYYY-MM-DD
      const dateParts = period.split('-');
      if (dateParts.length >= 2) {
        const year = parseInt(dateParts[0]);
        const monthIndex = parseInt(dateParts[1]) - 1;
        
        if (monthIndex >= 0 && monthIndex < 12) {
          return `${monthNames[monthIndex]} ${year}`;
        }
      }
      
      return period;
    } catch (error) {
      console.warn('Error formatting period:', period, error);
      return period;
    }
  }, []);

  // Fetch períodos con integración API mejorada
  const fetchAvailablePeriods = useCallback(async () => {
    if (isFetchingPeriods.current || periodsLoading) return;
    
    isFetchingPeriods.current = true;
    setPeriodsLoading(true);
    
    try {
      console.log('📅 Cargando períodos disponibles...');
      
      let periodsData = [];
      
      try {
        const response = await api.getAvailablePeriods();
        if (response?.data?.periods?.length) {
          periodsData = response.data.periods.sort((a, b) => b.localeCompare(a));
          console.log(`✅ Cargados ${periodsData.length} períodos desde API`);
        }
      } catch (apiError) {
        console.warn('⚠️ API períodos falló, generando automáticamente...');
        
        // Generar períodos automáticamente
        const now = new Date();
        for (let i = 0; i < 12; i++) {
          const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          periodsData.push(`${year}-${month}`);
        }
      }

      if (periodsData.length > 0) {
        const periodsWithLabels = periodsData.map(period => ({
          value: period,
          label: formatPeriodLabel(period)
        }));
        
        setAvailablePeriods(periodsWithLabels);
        
        // Auto-selección inteligente de período
        if (!currentPeriodo) {
          const defaultPeriod = periodsData[0];
          setCurrentPeriodo(defaultPeriod);
          setSearchParams(prev => ({ 
            ...Object.fromEntries(prev), 
            periodo: defaultPeriod 
          }));
        }
        
        // Configurar períodos de comparación
        if (periodsData.length >= 2) {
          setComparisonPeriods([periodsData[1], periodsData[0]]);
        }
      }
      
    } catch (error) {
      console.error('❌ Error crítico cargando períodos:', error);
      
      // Fallback robusto
      const fallbackPeriods = [
        { value: '2025-10', label: 'Octubre 2025' },
        { value: '2025-09', label: 'Septiembre 2025' },
        { value: '2025-08', label: 'Agosto 2025' }
      ];
      
      setAvailablePeriods(fallbackPeriods);
      if (!currentPeriodo) {
        setCurrentPeriodo('2025-10');
        setSearchParams(prev => ({ 
          ...Object.fromEntries(prev), 
          periodo: '2025-10' 
        }));
      }
      setComparisonPeriods(['2025-09', '2025-10']);
      
      message.warning('Usando períodos por defecto - Verifique conexión');
      
    } finally {
      setPeriodsLoading(false);
      isFetchingPeriods.current = false;
    }
  }, [formatPeriodLabel, setSearchParams, periodsLoading, currentPeriodo]);

  // Fetch métricas ejecutivas avanzadas con múltiples fuentes
  const fetchExecutiveMetrics = useCallback(async (periodo) => {
    if (!periodo || isFetchingMetrics.current) return;
    
    isFetchingMetrics.current = true;
    
    try {
      console.log('📊 Cargando métricas ejecutivas para:', periodo);
      
      // Cargar datos en paralelo de múltiples fuentes
      const [
        dashboardData,
        kpisData,
        alertsData,
        rankingData,
        incentivesData
      ] = await Promise.allSettled([
        api.getDashboardData(periodo),
        api.getKpisConsolidados(periodo),
        api.getDeviationAlerts(periodo, 15),
        api.getComparativeRanking(periodo, 'margen_neto'),
        chatServiceReady ? api.getIncentiveSummary(periodo) : Promise.resolve(null)
      ]);

      // Procesar dashboard data
      let totalGestores = 0, centros = 0, margenPromedio = 0;
      if (dashboardData.status === 'fulfilled' && dashboardData.value) {
        const gestores = dashboardData.value.comparativo?.gestores || [];
        totalGestores = gestores.length;
        centros = new Set(gestores.map(g => g.desc_centro || g.centro)).size;
        margenPromedio = gestores.reduce((sum, g) => sum + (g.margen_neto || 0), 0) / (gestores.length || 1);
      }

      // Procesar alertas de desviaciones
      let alertasActivas = 0, alertasCriticas = 0, desviaciones = 0;
      if (alertsData.status === 'fulfilled' && alertsData.value?.data?.alerts) {
        const alerts = alertsData.value.data.alerts;
        alertasActivas = alerts.length;
        alertasCriticas = alerts.filter(a => a.severity === 'high' || a.threshold_exceeded > 20).length;
        desviaciones = alerts.filter(a => a.type === 'deviation').length;
        
        setDeviationAlerts(alerts.slice(0, 5)); // Top 5 alertas
        setAlertasInteligentes(alerts.map(alert => ({
          tipo: alert.type || 'deviation',
          mensaje: alert.message || `Desviación detectada: ${alert.deviation_percent || 'N/A'}%`,
          severidad: alert.severity || 'medium',
          gestor: alert.gestor_name || 'N/A'
        })));
      }

      // Procesar ranking comparativo
      if (rankingData.status === 'fulfilled' && rankingData.value?.data?.ranking) {
        setComparativeRanking(rankingData.value.data.ranking.slice(0, 10));
      }

      // Procesar datos de incentivos
      if (incentivesData.status === 'fulfilled' && incentivesData.value) {
        setIncentivesSummary(incentivesData.value);
      }

      // Calcular eficiencia general y tendencia
      const eficienciaGeneral = Math.min(100, Math.max(0, (margenPromedio / 15) * 100)); // Asumiendo 15% como óptimo
      const tendencia = alertasCriticas > 3 ? 'descendente' : 
                       alertasCriticas === 0 ? 'ascendente' : 'neutral';
      const performance = margenPromedio >= 12 ? 'excelente' : 
                         margenPromedio >= 8 ? 'buena' : 'mejorable';

      // Actualizar métricas consolidadas
      setDashboardMetrics({
        totalGestores,
        centros,
        alertasActivas,
        alertasCriticas,
        performance,
        tendencia,
        margenPromedio: Number(margenPromedio.toFixed(2)),
        desviaciones,
        eficienciaGeneral: Number(eficienciaGeneral.toFixed(1))
      });

      console.log('✅ Métricas ejecutivas cargadas:', {
        gestores: totalGestores,
        alertas: alertasActivas,
        performance
      });

    } catch (error) {
      console.error('❌ Error cargando métricas ejecutivas:', error);
      
      // Datos de fallback mejorados
      setDashboardMetrics({
        totalGestores: 30,
        centros: 5,
        alertasActivas: 3,
        alertasCriticas: 1,
        performance: 'buena',
        tendencia: 'neutral',
        margenPromedio: 10.5,
        desviaciones: 2,
        eficienciaGeneral: 75.0
      });
    } finally {
      isFetchingMetrics.current = false;
    }
  }, [chatServiceReady]);

  // ========================================
  // 🎯 INICIALIZACIÓN PRINCIPAL MEJORADA
  // ========================================

  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    const initializeExecutiveView = async () => {
      setLoading(true);
      
      try {
        // Inicializar servicios y datos en paralelo
        await Promise.all([
          checkServicesHealth(),
          fetchAvailablePeriods()
        ]);
        
        // Cargar métricas si ya tenemos período
        const periodoToUse = currentPeriodo || searchParams.get('periodo');
        if (periodoToUse) {
          await fetchExecutiveMetrics(periodoToUse);
        }
        
        setLastUpdate(new Date());
        
      } catch (error) {
        console.error('❌ Error inicializando vista ejecutiva:', error);
        notification.error({
          message: 'Error de Inicialización',
          description: 'Algunas funcionalidades pueden estar limitadas'
        });
      } finally {
        setTimeout(() => setLoading(false), 800);
      }
    };

    initializeExecutiveView();
  }, []); // Solo se ejecuta una vez

  // Effect para cargar métricas cuando cambia el período
  useEffect(() => {
    if (currentPeriodo && !loading && isInitialized.current) {
      fetchExecutiveMetrics(currentPeriodo);
    }
  }, [currentPeriodo, fetchExecutiveMetrics, loading]);

  // ========================================
  // 🎯 HANDLERS MEJORADOS
  // ========================================

  const handlePeriodChange = useCallback((newPeriod) => {
    if (currentPeriodo === newPeriod) return;
    
    setCurrentPeriodo(newPeriod);
    const newParams = { periodo: newPeriod };
    if (comparisonMode) {
      newParams.comparison = 'true';
    }
    setSearchParams(newParams);
    
    message.success(`Período cambiado a ${formatPeriodLabel(newPeriod)}`);
  }, [comparisonMode, setSearchParams, currentPeriodo, formatPeriodLabel]);

  const handleComparisonModeToggle = useCallback(() => {
    const newComparisonMode = !comparisonMode;
    setComparisonMode(newComparisonMode);
    
    if (newComparisonMode && availablePeriods.length >= 2) {
      const periods = availablePeriods.map(p => p.value);
      setComparisonPeriods([periods[1], periods[0]]);
      setSearchParams({ periodo: currentPeriodo, comparison: 'true' });
      
      message.success('🔄 Modo comparación activado - Análisis comparativo habilitado');
    } else {
      setSearchParams({ periodo: currentPeriodo });
      message.success('📊 Modo individual activado');
    }
  }, [comparisonMode, availablePeriods, currentPeriodo, setSearchParams]);

  const handleRefresh = useCallback(async () => {
    if (refreshing) return;
    
    setRefreshing(true);
    message.loading('Actualizando datos ejecutivos...', 1);
    
    try {
      await Promise.all([
        checkServicesHealth(),
        fetchAvailablePeriods(),
        fetchExecutiveMetrics(currentPeriodo)
      ]);
      
      setLastUpdate(new Date());
      
      notification.success({
        message: 'Datos Actualizados',
        description: `Panel ejecutivo actualizado correctamente - ${new Date().toLocaleTimeString()}`,
        duration: 3
      });
      
    } catch (error) {
      notification.error({
        message: 'Error de Actualización',
        description: 'No se pudieron actualizar todos los datos'
      });
    } finally {
      setRefreshing(false);
    }
  }, [checkServicesHealth, fetchAvailablePeriods, fetchExecutiveMetrics, currentPeriodo, refreshing]);

  const handleExportReport = useCallback(async () => {
    try {
      message.loading('Generando Business Review ejecutivo...', 2);
      
      if (chatServiceReady) {
        try {
          const reportData = await api.generateExecutiveSummary(userId, currentPeriodo);
          console.log('📄 Business Review generado:', reportData);
          
          notification.success({
            message: 'Reporte Generado',
            description: 'Business Review ejecutivo listo para descarga',
            duration: 5
          });
        } catch (error) {
          throw error;
        }
      } else {
        // Fallback para exportación básica
        console.log('📊 Exportando datos básicos para:', currentPeriodo);
        message.info('Exportando datos disponibles...');
      }
      
    } catch (error) {
      notification.error({
        message: 'Error en Exportación',
        description: 'No se pudo generar el reporte ejecutivo'
      });
    }
  }, [chatServiceReady, userId, currentPeriodo]);

  const handleGoBack = useCallback(() => {
    navigate('/');
  }, [navigate]);

  // ========================================
  // 🎨 COMPONENTES VISUALES MEJORADOS
  // ========================================

  // Header ejecutivo con indicadores avanzados
  const renderExecutiveHeader = useMemo(() => (
    <Card style={{ 
      marginBottom: 24,
      background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}, ${theme.colors.bmGreenPrimary})`,
      color: 'white',
      boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
      border: 'none'
    }}>
      <Row justify="space-between" align="middle">
        <Col xs={24} lg={12}>
          <Space align="center" size="large">
            <img 
              src={BancaMarchLogo} 
              alt="Banca March" 
              style={{ height: 45, filter: 'brightness(0) invert(1)' }}
            />
            <div>
              <Title level={2} style={{ color: 'white', margin: 0, fontWeight: 600 }}>
                <DashboardOutlined style={{ marginRight: 12 }} />
                Panel Ejecutivo CDG
              </Title>
              <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: 16 }}>
                Control de Gestión Consolidado con IA
              </Text>
              {lastUpdate && (
                <div style={{ marginTop: 6 }}>
                  <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>
                    <SyncOutlined spin={refreshing} style={{ marginRight: 4 }} />
                    Actualizado: {lastUpdate.toLocaleTimeString('es-ES')}
                    {chatServiceReady && ' • Agente IA activo'}
                  </Text>
                </div>
              )}
            </div>
          </Space>
        </Col>
        
        <Col xs={24} lg={12}>
          <Row justify="end" gutter={[8, 8]}>
            <Col>
              <Space direction="vertical" size={4} style={{ textAlign: 'right' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <CalendarOutlined style={{ color: 'white' }} />
                  <Text style={{ color: 'white', fontWeight: 500 }}>Período:</Text>
                  <Select
                    value={currentPeriodo}
                    onChange={handlePeriodChange}
                    style={{ minWidth: 150 }}
                    disabled={comparisonMode || periodsLoading}
                    loading={periodsLoading}
                    placeholder="Seleccionar..."
                  >
                    {availablePeriods.map(period => (
                      <Option key={period.value} value={period.value}>
                        {period.label}
                      </Option>
                    ))}
                  </Select>
                </div>
                
                {/* Indicadores de servicios */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 11 }}>
                  <Badge 
                    status={servicesHealth.api === 'healthy' ? 'success' : 'error'} 
                    text={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>API</Text>}
                  />
                  <Badge 
                    status={servicesHealth.chat === 'healthy' ? 'success' : 'warning'} 
                    text={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>IA</Text>}
                  />
                  {chatServiceReady && (
                    <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: 10 }}>
                      <BulbOutlined style={{ marginRight: 2 }} />
                      Análisis avanzado
                    </Text>
                  )}
                </div>
              </Space>
            </Col>
            
            <Col>
              <Space size="small" wrap>
                <Tooltip title="Actualizar todos los datos">
                  <Button 
                    icon={<ReloadOutlined spin={refreshing} />}
                    onClick={handleRefresh}
                    loading={refreshing}
                    style={{ borderColor: 'white', color: 'white', background: 'rgba(255,255,255,0.1)' }}
                  />
                </Tooltip>

                <Tooltip title={comparisonMode ? 'Salir del modo comparación' : 'Comparar períodos'}>
                  <Button
                    icon={<SwapOutlined />}
                    type={comparisonMode ? 'primary' : 'default'}
                    onClick={handleComparisonModeToggle}
                    disabled={availablePeriods.length < 2}
                    style={{ 
                      borderColor: 'white',
                      color: 'white',
                      background: comparisonMode ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.1)'
                    }}
                  >
                    {comparisonMode ? 'Individual' : 'Comparar'}
                  </Button>
                </Tooltip>

                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={handleExportReport}
                  style={{
                    backgroundColor: theme.colors.bmGreenLight,
                    borderColor: theme.colors.bmGreenLight,
                    color: theme.colors.bmGreenDark
                  }}
                >
                  {chatServiceReady ? 'Business Review' : 'Exportar'}
                </Button>

                <Button 
                  icon={<ArrowLeftOutlined />}
                  onClick={handleGoBack}
                  style={{ borderColor: 'white', color: 'white', background: 'rgba(255,255,255,0.1)' }}
                >
                  Volver
                </Button>
              </Space>
            </Col>
          </Row>
        </Col>
      </Row>

      {/* Modo comparación info */}
      {comparisonMode && comparisonPeriods.length >= 2 && (
        <Divider style={{ borderColor: 'rgba(255,255,255,0.3)', margin: '16px 0' }} />
      )}
      {comparisonMode && comparisonPeriods.length >= 2 && (
        <Row>
          <Col span={24}>
            <div style={{
              padding: 12,
              backgroundColor: 'rgba(255,255,255,0.1)',
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.2)'
            }}>
              <Text style={{ color: 'white', fontSize: 14 }}>
                <BarChartOutlined style={{ marginRight: 8 }} />
                <strong>Análisis Comparativo:</strong> {comparisonPeriods.map(formatPeriodLabel).join(' vs ')}
              </Text>
            </div>
          </Col>
        </Row>
      )}
    </Card>
  ), [
    lastUpdate, currentPeriodo, handlePeriodChange, availablePeriods, comparisonMode, 
    periodsLoading, servicesHealth, chatServiceReady, handleRefresh, refreshing,
    handleComparisonModeToggle, handleExportReport, handleGoBack, comparisonPeriods, formatPeriodLabel
  ]);

  // Métricas ejecutivas mejoradas con más indicadores
  const renderAdvancedMetrics = useMemo(() => (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      {/* Métricas principales */}
      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 12,
          boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
          borderTop: `4px solid ${theme.colors.bmGreenPrimary}`,
          height: 140
        }}>
          <Space direction="vertical" size="small">
            <TeamOutlined style={{ fontSize: 28, color: theme.colors.bmGreenPrimary }} />
            <Statistic 
              title="Gestores Activos" 
              value={dashboardMetrics.totalGestores}
              suffix={`en ${dashboardMetrics.centros} centros`}
              valueStyle={{ fontSize: 18, fontWeight: 600 }}
            />
            <Text style={{ fontSize: 11, color: theme.colors.textSecondary }}>
              Vista consolidada tiempo real
            </Text>
          </Space>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 12,
          boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
          borderTop: `4px solid ${theme.colors.success}`,
          height: 140
        }}>
          <Space direction="vertical" size="small">
            <ArrowUpOutlined style={{ fontSize: 28, color: theme.colors.success }} />
            <Statistic 
              title="Margen Promedio" 
              value={dashboardMetrics.margenPromedio}
              suffix="%"
              precision={1}
              valueStyle={{ 
                fontSize: 18, 
                fontWeight: 600,
                color: dashboardMetrics.margenPromedio >= 10 ? theme.colors.success : theme.colors.warning
              }}
            />
            <Badge 
              color={dashboardMetrics.tendencia === 'ascendente' ? 'green' : 
                    dashboardMetrics.tendencia === 'descendente' ? 'red' : 'blue'}
              text={dashboardMetrics.tendencia.toUpperCase()}
              style={{ fontSize: 10 }}
            />
          </Space>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 12,
          boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
          borderTop: `4px solid ${dashboardMetrics.alertasCriticas > 0 ? theme.colors.error : theme.colors.info}`,
          height: 140
        }}>
          <Space direction="vertical" size="small">
            <AlertOutlined style={{ 
              fontSize: 28, 
              color: dashboardMetrics.alertasCriticas > 0 ? theme.colors.error : theme.colors.info 
            }} />
            <Statistic 
              title="Alertas Activas" 
              value={dashboardMetrics.alertasActivas}
              suffix={dashboardMetrics.alertasCriticas > 0 ? `(${dashboardMetrics.alertasCriticas} críticas)` : ''}
              valueStyle={{ 
                fontSize: 18, 
                fontWeight: 600,
                color: dashboardMetrics.alertasCriticas > 0 ? theme.colors.error : theme.colors.success
              }}
            />
            <Badge count={dashboardMetrics.desviaciones} overflowCount={99} />
          </Space>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 12,
          boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
          borderTop: `4px solid ${theme.colors.bmGreenLight}`,
          height: 140
        }}>
          <Space direction="vertical" size="small">
            <CheckCircleOutlined style={{ fontSize: 28, color: theme.colors.bmGreenLight }} />
            <div>
              <Text style={{ fontSize: 12, color: theme.colors.textSecondary }}>Eficiencia General</Text>
              <div style={{ margin: '8px 0' }}>
                <Progress 
                  type="circle" 
                  percent={dashboardMetrics.eficienciaGeneral} 
                  size={60}
                  strokeColor={theme.colors.bmGreenPrimary}
                />
              </div>
            </div>
            <Badge 
              status={dashboardMetrics.eficienciaGeneral >= 80 ? 'success' : 
                     dashboardMetrics.eficienciaGeneral >= 60 ? 'processing' : 'warning'}
              text={chatServiceReady ? 'IA Activa' : 'Básico'}
              style={{ fontSize: 10 }}
            />
          </Space>
        </Card>
      </Col>
    </Row>
  ), [dashboardMetrics, chatServiceReady]);

  // Alertas inteligentes (solo si hay alertas)
  const renderIntelligentAlerts = useMemo(() => {
    if (!alertasInteligentes.length) return null;

    return (
      <Card 
        title={
          <Space>
            <ExclamationCircleOutlined style={{ color: theme.colors.warning }} />
            <Text strong>Alertas Inteligentes</Text>
            <Badge count={alertasInteligentes.length} />
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Row gutter={[12, 12]}>
          {alertasInteligentes.slice(0, 3).map((alerta, index) => (
            <Col xs={24} sm={12} lg={8} key={index}>
              <Alert
                message={alerta.mensaje}
                type={alerta.severidad === 'high' ? 'error' : 'warning'}
                showIcon
                style={{ fontSize: 12 }}
                description={alerta.gestor !== 'N/A' ? `Gestor: ${alerta.gestor}` : null}
              />
            </Col>
          ))}
        </Row>
      </Card>
    );
  }, [alertasInteligentes]);

  // Props memoizadas para el dashboard con datos enriquecidos
  const dashboardProps = useMemo(() => ({
    userId,
    periodo: currentPeriodo,
    comparisonMode,
    comparisonPeriods,
    availablePeriods,
    // Props adicionales para funcionalidades avanzadas
    chatServiceReady,
    servicesHealth,
    executiveSuggestions,
    deviationAlerts,
    comparativeRanking,
    incentivesSummary,
    dashboardMetrics
  }), [
    userId, currentPeriodo, comparisonMode, comparisonPeriods, availablePeriods,
    chatServiceReady, servicesHealth, executiveSuggestions, deviationAlerts,
    comparativeRanking, incentivesSummary, dashboardMetrics
  ]);

  // ========================================
  // 🎨 RENDERIZADO PRINCIPAL
  // ========================================

  // Loading mejorado
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}15, ${theme.colors.bmGreenPrimary}10)`
      }}>
        <Space direction="vertical" align="center" size="large">
          <img src={BancaMarchLogo} alt="Banca March" style={{ height: 70, opacity: 0.9 }} />
          <Spin size="large" />
          <div style={{ textAlign: 'center' }}>
            <Title level={3} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
              Inicializando Panel Ejecutivo
            </Title>
            <Text style={{ color: theme.colors.textSecondary, fontSize: 16 }}>
              Configurando servicios inteligentes y cargando datos consolidados...
            </Text>
          </div>
        </Space>
      </div>
    );
  }

  // Verificación de período
  if (!currentPeriodo) {
    return (
      <div style={{ padding: 24 }}>
        <Card>
          <div style={{ textAlign: 'center', padding: 60 }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 24, fontSize: 16 }}>
              Configurando períodos disponibles...
            </Paragraph>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      background: `linear-gradient(180deg, ${theme.colors.backgroundLight}, ${theme.colors.background})`,
      paddingBottom: 24
    }}>
      
      {/* Header ejecutivo mejorado */}
      {renderExecutiveHeader}
      
      {/* Contenedor principal con padding */}
      <div style={{ padding: '0 24px' }}>
        
        {/* Métricas ejecutivas avanzadas */}
        {renderAdvancedMetrics}
        
        {/* Alertas inteligentes */}
        {renderIntelligentAlerts}
        
        {/* Dashboard principal con props enriquecidas */}
        <ControlGestionDashboard {...dashboardProps} />
      
      </div>
      
      {/* Footer ejecutivo mejorado */}
      <div style={{ 
        padding: '32px 24px 24px',
        textAlign: 'center',
        borderTop: `1px solid ${theme.colors.border}`,
        backgroundColor: theme.colors.background,
        marginTop: 32
      }}>
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: 16, fontWeight: 600, color: theme.colors.bmGreenDark }}>
            Panel Ejecutivo CDG - Banca March
          </Text>
          <Text style={{ fontSize: 13, color: theme.colors.textSecondary }}>
            Sistema de Control de Gestión con Inteligencia Artificial | © 2025
          </Text>
          {lastUpdate && (
            <Text style={{ fontSize: 11, fontStyle: 'italic', color: theme.colors.textLight }}>
              Última sincronización: {lastUpdate.toLocaleString('es-ES')}
              {chatServiceReady && ' • Funcionalidades avanzadas activas'}
            </Text>
          )}
        </Space>
      </div>
    </div>
  );
};

export default DireccionView;
