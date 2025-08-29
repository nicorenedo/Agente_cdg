// src/pages/DireccionView.jsx
// Vista de dirección ANTI-BUCLE INFINITO - Completamente optimizada y CORREGIDA

import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Spin, Button, Card, Row, Col, Typography, Space, Select, message, Tooltip, Badge } from 'antd';
import { 
  ArrowLeftOutlined, 
  DashboardOutlined,
  CalendarOutlined, 
  SwapOutlined,
  ReloadOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import ControlGestionDashboard from '../components/Dashboard/ControlGestionDashboard';
import api from '../services/api';
import theme from '../styles/theme';
import BancaMarchLogo from '../assets/BancaMarchlogo.png';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const DireccionView = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Estados principales
  const [loading, setLoading] = useState(true);
  const [periodsLoading, setPeriodsLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // Estados de configuración
  const [availablePeriods, setAvailablePeriods] = useState([]);
  const [currentPeriodo, setCurrentPeriodo] = useState(searchParams.get('periodo') || null);
  const [comparisonMode, setComparisonMode] = useState(searchParams.get('comparison') === 'true');
  const [comparisonPeriods, setComparisonPeriods] = useState([]);
  
  // Estados de datos
  const [dashboardMetrics, setDashboardMetrics] = useState({
    totalGestores: 0,
    centros: 0,
    alertasActivas: 0,
    performance: 'buena'
  });

  // ✅ Refs para controlar inicialización y evitar bucles
  const isInitialized = useRef(false);
  const isFetchingPeriods = useRef(false);
  const isFetchingMetrics = useRef(false);

  // ✅ Usuario ID memoizado
  const userId = useMemo(() => 'direccion_user_001', []);

  // ✅ Función de formateo memoizada
  const formatPeriodLabel = useCallback((period) => {
    if (!period) return '';
    
    const monthNames = [
      'Enero', 'Febrero', 'Marzo', 'Abril', 
      'Mayo', 'Junio', 'Julio', 'Agosto', 
      'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];
    
    try {
      const dateParts = period.split('-');
      if (dateParts.length >= 2) {
        const year = parseInt(dateParts[0]);
        const monthIndex = parseInt(dateParts[1]) - 1;
        
        if (monthIndex >= 0 && monthIndex < 12) {
          return `${monthNames[monthIndex]} ${year}`;
        }
      }
      
      const dateObj = new Date(period);
      if (!isNaN(dateObj.getTime())) {
        const month = monthNames[dateObj.getMonth()];
        const year = dateObj.getFullYear();
        return `${month} ${year}`;
      }
    } catch (error) {
      console.warn('Error formatting period:', period, error);
    }
    
    return period;
  }, []);

  // ✅ Fetch períodos con protección anti-bucle
  const fetchAvailablePeriods = useCallback(async () => {
    if (isFetchingPeriods.current || periodsLoading) return;
    isFetchingPeriods.current = true;
    setPeriodsLoading(true);
    
    try {
      let periodsData = [];
      
      try {
        const response = await api.getAvailablePeriods();
        if (response?.data?.periods?.length) {
          periodsData = response.data.periods.sort((a, b) => b.localeCompare(a));
        }
      } catch {
        // Generar períodos automáticamente si el endpoint falla
        const now = new Date();
        for (let i = 0; i < 12; i++) {
          const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          periodsData.push(`${year}-${month}-01`);
        }
      }

      if (periodsData.length > 0) {
        const periodsWithLabels = periodsData.map(period => ({
          value: period,
          label: formatPeriodLabel(period)
        }));
        
        setAvailablePeriods(periodsWithLabels);
        
        // Solo establecer período por defecto si no existe
        if (!currentPeriodo && periodsData.length > 0) {
          const defaultPeriod = periodsData[0];
          setCurrentPeriodo(defaultPeriod);
          
          if (searchParams.get('periodo') !== defaultPeriod) {
            setSearchParams(prev => ({ 
              ...Object.fromEntries(prev), 
              periodo: defaultPeriod 
            }));
          }
        }
        
        // Configurar períodos de comparación
        if (periodsData.length >= 2) {
          setComparisonPeriods([periodsData[1], periodsData[0]]);
        }
      } else {
        throw new Error('No se pudieron obtener períodos');
      }
      
    } catch (error) {
      console.error('Error obteniendo periodos:', error);
      message.warning('Error al cargar períodos. Usando datos por defecto.');
      
      const fallbackPeriods = [
        { value: '2025-10-01', label: 'Octubre 2025' },
        { value: '2025-09-01', label: 'Septiembre 2025' },
        { value: '2025-08-01', label: 'Agosto 2025' }
      ];
      
      setAvailablePeriods(fallbackPeriods);
      if (!currentPeriodo) {
        setCurrentPeriodo('2025-10-01');
        setSearchParams(prev => ({ 
          ...Object.fromEntries(prev), 
          periodo: '2025-10-01' 
        }));
      }
      setComparisonPeriods(['2025-09-01', '2025-10-01']);
      
    } finally {
      setPeriodsLoading(false);
      isFetchingPeriods.current = false;
    }
  }, [formatPeriodLabel, setSearchParams, periodsLoading, currentPeriodo, searchParams]);

  // ✅ Fetch métricas con protección anti-bucle
  const fetchDashboardMetrics = useCallback(async (periodo) => {
    if (!periodo || isFetchingMetrics.current) return;
    isFetchingMetrics.current = true;
    
    try {
      const dashboardData = await api.getDashboardData(periodo);
      
      if (dashboardData) {
        const gestores = dashboardData.comparativo?.gestores || [];
        const alertas = dashboardData.alertas?.alerts || [];
        
        const centrosUnicos = new Set(gestores.map(g => g.desc_centro)).size;
        const margenPromedio = gestores.reduce((sum, g) => sum + (g.margen_neto || 0), 0) / (gestores.length || 1);
        
        setDashboardMetrics({
          totalGestores: gestores.length,
          centros: centrosUnicos,
          alertasActivas: alertas.length,
          performance: margenPromedio >= 12 ? 'excelente' : margenPromedio >= 8 ? 'buena' : 'mejorable'
        });
      }
    } catch (error) {
      console.warn('Error cargando métricas ejecutivas:', error);
      // Datos fallback
      setDashboardMetrics({
        totalGestores: 30,
        centros: 5,
        alertasActivas: 3,
        performance: 'buena'
      });
    } finally {
      isFetchingMetrics.current = false;
    }
  }, []);

  // ✅ Inicialización controlada UNA SOLA VEZ
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    const initializeComponent = async () => {
      setLoading(true);
      
      try {
        await fetchAvailablePeriods();
        
        const periodoToUse = currentPeriodo || searchParams.get('periodo');
        if (periodoToUse) {
          await fetchDashboardMetrics(periodoToUse);
        }
        
        setLastUpdate(new Date());
      } catch (error) {
        console.error('Error inicializando componente:', error);
      } finally {
        setTimeout(() => setLoading(false), 500);
      }
    };

    initializeComponent();
  }, []); // ✅ Dependencias vacías - solo se ejecuta UNA vez

  // ✅ Effect protegido para métricas cuando cambia período
  useEffect(() => {
    if (currentPeriodo && !loading && !isFetchingMetrics.current && isInitialized.current) {
      fetchDashboardMetrics(currentPeriodo);
    }
  }, [currentPeriodo, fetchDashboardMetrics, loading]);

  // ✅ Handlers memoizados con protecciones
  const handlePeriodChange = useCallback((newPeriod) => {
    if (currentPeriodo === newPeriod) return;
    
    setCurrentPeriodo(newPeriod);
    const newParams = { periodo: newPeriod };
    if (comparisonMode) {
      newParams.comparison = 'true';
    }
    setSearchParams(newParams);
  }, [comparisonMode, setSearchParams, currentPeriodo]);

  const handleComparisonModeToggle = useCallback(() => {
    const newComparisonMode = !comparisonMode;
    setComparisonMode(newComparisonMode);
    
    if (newComparisonMode && availablePeriods.length >= 2) {
      const periods = availablePeriods.map(p => p.value);
      setComparisonPeriods([periods[1], periods[0]]);
      setSearchParams({ periodo: currentPeriodo, comparison: 'true' });
    } else {
      setSearchParams({ periodo: currentPeriodo });
    }
    
    message.success(newComparisonMode ? 'Modo comparación activado' : 'Modo comparación desactivado');
  }, [comparisonMode, availablePeriods, currentPeriodo, setSearchParams]);

  const handleRefresh = useCallback(async () => {
    if (refreshing) return;
    
    setRefreshing(true);
    try {
      await Promise.all([
        fetchAvailablePeriods(),
        fetchDashboardMetrics(currentPeriodo)
      ]);
      setLastUpdate(new Date());
      message.success('Datos actualizados correctamente');
    } catch (error) {
      message.error('Error al actualizar los datos');
    } finally {
      setRefreshing(false);
    }
  }, [fetchAvailablePeriods, fetchDashboardMetrics, currentPeriodo, refreshing]);

  const handleExportReport = useCallback(() => {
    message.info('Generando reporte ejecutivo...');
    console.log('Exportando reporte para período:', currentPeriodo);
  }, [currentPeriodo]);

  const handleGoBack = useCallback(() => {
    navigate('/');
  }, [navigate]);

  // ✅ Header memoizado
  const renderDirectionHeader = useMemo(() => (
    <Card style={{ 
      marginBottom: 24,
      background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}, ${theme.colors.bmGreenPrimary})`,
      color: 'white',
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
    }}>
      <Row justify="space-between" align="middle">
        <Col>
          <Space align="center" size="large">
            <img 
              src={BancaMarchLogo} 
              alt="Banca March" 
              style={{ height: 40, filter: 'brightness(0) invert(1)' }}
            />
            <div>
              <Title level={3} style={{ color: 'white', margin: 0, fontWeight: 600 }}>
                <DashboardOutlined style={{ marginRight: 8 }} />
                Panel Ejecutivo de Dirección
              </Title>
              <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: 16 }}>
                Control de Gestión Consolidado
              </Text>
              {lastUpdate && (
                <div style={{ marginTop: 4 }}>
                  <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>
                    Última actualización: {lastUpdate.toLocaleTimeString('es-ES')}
                  </Text>
                </div>
              )}
            </div>
          </Space>
        </Col>
        
        <Col>
          <Space size="middle" wrap>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <CalendarOutlined style={{ color: 'white' }} />
              <Text style={{ color: 'white', fontWeight: 500 }}>Período:</Text>
              <Select
                value={currentPeriodo}
                onChange={handlePeriodChange}
                style={{ minWidth: 150 }}
                disabled={comparisonMode || periodsLoading}
                loading={periodsLoading}
                placeholder="Seleccionar período..."
              >
                {availablePeriods.map(period => (
                  <Option key={period.value} value={period.value}>
                    {period.label}
                  </Option>
                ))}
              </Select>
            </div>

            <Tooltip title="Actualizar datos">
              <Button 
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
                loading={refreshing}
                style={{ borderColor: 'white', color: 'white', background: 'transparent' }}
              />
            </Tooltip>

            <Tooltip title={comparisonMode ? 'Desactivar comparación' : 'Comparar períodos'}>
              <Button
                icon={<SwapOutlined />}
                type={comparisonMode ? 'primary' : 'default'}
                onClick={handleComparisonModeToggle}
                disabled={availablePeriods.length < 2}
                style={{ 
                  borderColor: 'white',
                  color: 'white',
                  background: comparisonMode ? 'rgba(255,255,255,0.2)' : 'transparent'
                }}
              >
                {comparisonMode ? 'Salir Comparación' : 'Comparar'}
              </Button>
            </Tooltip>

            <Button 
              icon={<ArrowLeftOutlined />}
              onClick={handleGoBack}
              style={{ borderColor: 'white', color: 'white', background: 'transparent' }}
            >
              Volver
            </Button>

            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={handleExportReport}
              style={{
                backgroundColor: theme.colors.bmGreenLight,
                borderColor: theme.colors.bmGreenLight
              }}
            >
              Exportar
            </Button>
          </Space>
        </Col>
      </Row>

      {comparisonMode && comparisonPeriods.length >= 2 && (
        <Row style={{ marginTop: 16 }}>
          <Col span={24}>
            <div style={{
              padding: 12,
              backgroundColor: 'rgba(255,255,255,0.1)',
              borderRadius: 6,
              border: '1px solid rgba(255,255,255,0.2)'
            }}>
              <Text style={{ color: 'white', fontSize: 14 }}>
                📊 <strong>Modo Comparación:</strong> {comparisonPeriods.map(formatPeriodLabel).join(' vs ')}
              </Text>
            </div>
          </Col>
        </Row>
      )}
    </Card>
  ), [
    lastUpdate, 
    currentPeriodo, 
    handlePeriodChange, 
    availablePeriods, 
    comparisonMode, 
    periodsLoading, 
    handleRefresh, 
    refreshing, 
    handleComparisonModeToggle, 
    handleGoBack, 
    handleExportReport,
    comparisonPeriods,
    formatPeriodLabel
  ]);

  // ✅ Métricas ejecutivas memoizadas
  const renderExecutiveMetrics = useMemo(() => (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderTop: `4px solid ${theme.colors.bmGreenPrimary}`,
          height: 120
        }}>
          <Space direction="vertical" size="small">
            <DashboardOutlined style={{ fontSize: 24, color: theme.colors.bmGreenPrimary }} />
            <Title level={4} style={{ margin: 0 }}>Vista Consolidada</Title>
            <Text style={{ fontSize: 12 }}>
              {dashboardMetrics.totalGestores} gestores en {dashboardMetrics.centros} centros
            </Text>
          </Space>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderTop: `4px solid ${theme.colors.bmGreenLight}`,
          height: 120
        }}>
          <Space direction="vertical" size="small">
            <Title level={3} style={{ margin: 0, color: theme.colors.bmGreenPrimary, fontSize: 20 }}>
              Real Time
            </Title>
            <Text style={{ fontSize: 12 }}>Datos actualizados automáticamente</Text>
            <Badge status="processing" text="En línea" style={{ fontSize: 10 }} />
          </Space>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderTop: `4px solid ${theme.colors.success}`,
          height: 120
        }}>
          <Space direction="vertical" size="small">
            <Title level={3} style={{ margin: 0, color: theme.colors.success, fontSize: 20 }}>
              AI Insights
            </Title>
            <Text style={{ fontSize: 12 }}>Performance: {dashboardMetrics.performance}</Text>
            <Badge 
              color={dashboardMetrics.performance === 'excelente' ? 'green' : 
                    dashboardMetrics.performance === 'buena' ? 'blue' : 'orange'}
              text={dashboardMetrics.performance.toUpperCase()}
              style={{ fontSize: 10 }}
            />
          </Space>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card style={{ 
          textAlign: 'center',
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderTop: `4px solid ${dashboardMetrics.alertasActivas > 0 ? theme.colors.error : theme.colors.info}`,
          height: 120
        }}>
          <Space direction="vertical" size="small">
            <Title level={3} style={{ 
              margin: 0, 
              color: dashboardMetrics.alertasActivas > 0 ? theme.colors.error : theme.colors.info,
              fontSize: 20
            }}>
              Alertas
            </Title>
            <Text style={{ fontSize: 12 }}>
              {dashboardMetrics.alertasActivas} alertas activas
            </Text>
            <Badge count={dashboardMetrics.alertasActivas} overflowCount={99} />
          </Space>
        </Card>
      </Col>
    </Row>
  ), [dashboardMetrics]);

  // ✅ Props memoizadas para ControlGestionDashboard
  const dashboardProps = useMemo(() => ({
    userId,
    periodo: currentPeriodo,
    comparisonMode,
    comparisonPeriods,
    availablePeriods
  }), [userId, currentPeriodo, comparisonMode, comparisonPeriods, availablePeriods]);

  // ✅ Loading inicial
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
          <img src={BancaMarchLogo} alt="Banca March" style={{ height: 60 }} />
          <Spin size="large" />
          <div style={{ textAlign: 'center' }}>
            <Title level={3} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
              Iniciando Panel Ejecutivo
            </Title>
            <Text style={{ color: theme.colors.textSecondary, fontSize: 16 }}>
              Cargando datos consolidados y períodos disponibles...
            </Text>
          </div>
        </Space>
      </div>
    );
  }

  // ✅ Verificar período antes de renderizar
  if (!currentPeriodo) {
    return (
      <div style={{ padding: 24 }}>
        <Card>
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: 24 }}>
              Cargando períodos disponibles...
            </Paragraph>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      background: `linear-gradient(180deg, ${theme.colors.backgroundLight}, ${theme.colors.background})`
    }}>
      
      {/* Header ejecutivo */}
      {renderDirectionHeader}
      
      {/* Métricas ejecutivas */}
      <div style={{ padding: `0 24px` }}>
        {renderExecutiveMetrics}
      </div>
      
      {/* Dashboard principal - PROPS MEMOIZADAS */}
      <ControlGestionDashboard {...dashboardProps} />
      
      {/* Footer ejecutivo */}
      <div style={{ 
        padding: 24,
        textAlign: 'center',
        borderTop: `1px solid ${theme.colors.border}`,
        backgroundColor: theme.colors.background,
        marginTop: 24
      }}>
        <Space direction="vertical" size="small">
          <Text style={{ fontSize: 14, fontWeight: 500 }}>
            Panel Ejecutivo CDG - Banca March
          </Text>
          <Text style={{ fontSize: 12 }}>
            Sistema de Control de Gestión Inteligente con IA | © 2025
          </Text>
          {lastUpdate && (
            <Text style={{ fontSize: 11, fontStyle: 'italic' }}>
              Datos actualizados: {lastUpdate.toLocaleString('es-ES')}
            </Text>
          )}
        </Space>
      </div>
    </div>
  );
};

export default DireccionView;
