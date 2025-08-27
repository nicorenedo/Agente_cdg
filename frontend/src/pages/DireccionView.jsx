// src/pages/DireccionView.jsx
// Vista de dirección ANTI-BUCLE INFINITO - Completamente optimizada

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

  // 🔥 ANTI-BUCLE: Refs para controlar inicialización
  const isInitialized = useRef(false);
  const isFetchingPeriods = useRef(false);
  const isFetchingMetrics = useRef(false);

  // 🔥 SOLUCIÓN 1: Usuario ID constante
  const userId = useMemo(() => 'direccion_user_001', []);

  // 🔥 SOLUCIÓN 2: Función de formateo memoizada
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

  // 🔥 SOLUCIÓN 3: Fetch períodos PROTEGIDO CONTRA BUCLES
  const fetchAvailablePeriods = useCallback(async () => {
    if (isFetchingPeriods.current || periodsLoading) return;
    
    isFetchingPeriods.current = true;
    setPeriodsLoading(true);
    
    try {
      let periodsData = [];
      
      try {
        const response = await api.getAvailablePeriods();
        if (response.data && response.data.periods && response.data.periods.length > 0) {
          periodsData = response.data.periods.sort((a, b) => b.localeCompare(a));
        }
      } catch (error) {
        console.warn('Endpoint getAvailablePeriods no disponible, generando períodos automáticamente');
        
        const now = new Date();
        for (let i = 0; i < 12; i++) {
          const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = '01';
          periodsData.push(`${year}-${month}-${day}`);
        }
      }

      if (periodsData.length > 0) {
        const periodsWithLabels = periodsData.map(period => ({
          value: period,
          label: formatPeriodLabel(period)
        }));
        
        setAvailablePeriods(periodsWithLabels);
        
        // Solo establecer período por defecto si no existe y no está en proceso
        if (!currentPeriodo && periodsData.length > 0) {
          const defaultPeriod = periodsData[0];
          setCurrentPeriodo(defaultPeriod);
          
          // PROTECCIÓN: Solo actualizar URL si realmente cambió
          const currentUrlPeriod = searchParams.get('periodo');
          if (currentUrlPeriod !== defaultPeriod) {
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
      console.error('Error obteniendo periodos disponibles:', error);
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

  // 🔥 SOLUCIÓN 4: Fetch métricas PROTEGIDO CONTRA BUCLES
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
    } finally {
      isFetchingMetrics.current = false;
    }
  }, []);

  // 🔥 SOLUCIÓN ANTI-BUCLE PRINCIPAL: useEffect de inicialización UNA SOLA VEZ
  useEffect(() => {
    if (isInitialized.current) return;
    
    let isMounted = true;
    isInitialized.current = true;

    const initializeComponent = async () => {
      if (!isMounted) return;
      
      setLoading(true);
      
      try {
        // Cargar períodos solo una vez
        await fetchAvailablePeriods();
        
        // Solo cargar métricas si tenemos período
        const periodoToUse = currentPeriodo || searchParams.get('periodo');
        if (isMounted && periodoToUse) {
          await fetchDashboardMetrics(periodoToUse);
        }
        
        if (isMounted) {
          setLastUpdate(new Date());
        }
      } catch (error) {
        if (isMounted) {
          console.error('Error inicializando componente:', error);
        }
      } finally {
        if (isMounted) {
          setTimeout(() => setLoading(false), 500);
        }
      }
    };

    initializeComponent();

    return () => {
      isMounted = false;
    };
  }, []); // ✅ DEPENDENCIAS VACÍAS - Solo se ejecuta UNA vez

  // 🔥 useEffect PROTEGIDO para métricas cuando cambia período
  useEffect(() => {
    if (currentPeriodo && !loading && !isFetchingMetrics.current && isInitialized.current) {
      fetchDashboardMetrics(currentPeriodo);
    }
  }, [currentPeriodo, fetchDashboardMetrics, loading]);

  // 🔥 SOLUCIÓN 7: Handlers memoizados CON PROTECCIÓN
  const handlePeriodChange = useCallback((newPeriod) => {
    if (currentPeriodo === newPeriod) return; // ✅ Evitar cambios innecesarios
    
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
    if (refreshing) return; // ✅ Evitar múltiples refreshes
    
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

  // 🔥 SOLUCIÓN 8: Componentes memoizados
  const renderDirectionHeader = useMemo(() => (
    <Card 
      variant="outlined"
      style={{ 
        marginBottom: theme.spacing.lg,
        background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}, ${theme.colors.bmGreenPrimary})`,
        color: 'white',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
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
              {lastUpdate && (
                <div style={{ marginTop: 4 }}>
                  <Text style={{ 
                    color: 'rgba(255,255,255,0.7)', 
                    fontSize: '12px' 
                  }}>
                    Última actualización: {lastUpdate.toLocaleTimeString('es-ES')}
                  </Text>
                </div>
              )}
            </div>
          </Space>
        </Col>
        
        <Col>
          <Space size="middle" wrap>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CalendarOutlined style={{ color: 'white', fontSize: '16px' }} />
              <Text style={{ color: 'white', fontSize: '14px', fontWeight: 500 }}>
                Período:
              </Text>
              <Select
                value={currentPeriodo}
                onChange={handlePeriodChange}
                style={{ minWidth: '150px' }}
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
                style={{ 
                  borderColor: 'white',
                  color: 'white',
                  background: 'transparent'
                }}
              />
            </Tooltip>

            <Tooltip title={comparisonMode ? 'Desactivar comparación' : 'Comparar períodos'}>
              <Button
                icon={<SwapOutlined />}
                type={comparisonMode ? 'primary' : 'default'}
                size="default"
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
              style={{ 
                borderColor: 'white',
                color: 'white',
                background: 'transparent'
              }}
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
              Exportar Reporte
            </Button>
          </Space>
        </Col>
      </Row>

      {comparisonMode && comparisonPeriods.length >= 2 && (
        <Row style={{ marginTop: theme.spacing.md }}>
          <Col span={24}>
            <div style={{
              padding: theme.spacing.sm,
              backgroundColor: 'rgba(255,255,255,0.1)',
              borderRadius: 6,
              border: '1px solid rgba(255,255,255,0.2)'
            }}>
              <Text style={{ color: 'white', fontSize: '14px' }}>
                📊 <strong>Modo Comparación Activo:</strong> Comparando {comparisonPeriods.map(formatPeriodLabel).join(' vs ')}
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

  const renderExecutiveMetrics = useMemo(() => (
    <Row gutter={[16, 16]} style={{ marginBottom: theme.spacing.lg }}>
      <Col xs={24} sm={12} lg={6}>
        <Card 
          variant="outlined"
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${theme.colors.bmGreenPrimary}`,
            height: '120px'
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <Space direction="vertical" size="small">
              <DashboardOutlined 
                style={{ 
                  fontSize: '24px', 
                  color: theme.colors.bmGreenPrimary
                }} 
              />
              <Title level={4} style={{ margin: 0, color: theme.colors.textPrimary }}>
                Vista Consolidada
              </Title>
              <Text style={{ color: theme.colors.textSecondary, fontSize: '12px' }}>
                {dashboardMetrics.totalGestores} gestores en {dashboardMetrics.centros} centros
              </Text>
            </Space>
          </div>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card 
          variant="outlined"
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${theme.colors.bmGreenLight}`,
            height: '120px'
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <Space direction="vertical" size="small">
              <Title level={3} style={{ 
                margin: 0, 
                color: theme.colors.bmGreenPrimary,
                fontSize: '20px'
              }}>
                Real Time
              </Title>
              <Text style={{ color: theme.colors.textSecondary, fontSize: '12px' }}>
                Datos actualizados automáticamente
              </Text>
              <Badge 
                status="processing" 
                text="En línea" 
                style={{ fontSize: '10px' }}
              />
            </Space>
          </div>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card 
          variant="outlined"
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${theme.colors.success}`,
            height: '120px'
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <Space direction="vertical" size="small">
              <Title level={3} style={{ 
                margin: 0, 
                color: theme.colors.success,
                fontSize: '20px'
              }}>
                AI Insights
              </Title>
              <Text style={{ color: theme.colors.textSecondary, fontSize: '12px' }}>
                Performance: {dashboardMetrics.performance}
              </Text>
              <Badge 
                color={dashboardMetrics.performance === 'excelente' ? 'green' : 
                      dashboardMetrics.performance === 'buena' ? 'blue' : 'orange'}
                text={dashboardMetrics.performance.toUpperCase()}
                style={{ fontSize: '10px' }}
              />
            </Space>
          </div>
        </Card>
      </Col>

      <Col xs={24} sm={12} lg={6}>
        <Card 
          variant="outlined"
          style={{ 
            textAlign: 'center',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            borderTop: `4px solid ${dashboardMetrics.alertasActivas > 0 ? theme.colors.error : theme.colors.info}`,
            height: '120px'
          }}
        >
          <div style={{ padding: theme.spacing.sm }}>
            <Space direction="vertical" size="small">
              <Title level={3} style={{ 
                margin: 0, 
                color: dashboardMetrics.alertasActivas > 0 ? theme.colors.error : theme.colors.info,
                fontSize: '20px'
              }}>
                Alertas
              </Title>
              <Text style={{ color: theme.colors.textSecondary, fontSize: '12px' }}>
                {dashboardMetrics.alertasActivas} alertas activas
              </Text>
              <Badge 
                count={dashboardMetrics.alertasActivas} 
                overflowCount={99}
                style={{ fontSize: '10px' }}
              />
            </Space>
          </div>
        </Card>
      </Col>
    </Row>
  ), [dashboardMetrics]);

  // Props memoizadas para ControlGestionDashboard
  const dashboardProps = useMemo(() => ({
    userId,
    periodo: currentPeriodo,
    comparisonMode,
    comparisonPeriods,
    availablePeriods
  }), [userId, currentPeriodo, comparisonMode, comparisonPeriods, availablePeriods]);

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
              Cargando datos consolidados y períodos disponibles...
            </Text>
          </div>
        </Space>
      </div>
    );
  }

  // No renderizar dashboard hasta tener período seleccionado
  if (!currentPeriodo) {
    return (
      <div style={{ padding: theme.spacing.lg }}>
        <Card>
          <div style={{ textAlign: 'center', padding: theme.spacing.xl }}>
            <Spin size="large" />
            <Paragraph style={{ marginTop: theme.spacing.lg }}>
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
      backgroundColor: theme.colors.backgroundLight,
      background: `linear-gradient(180deg, ${theme.colors.backgroundLight} 0%, ${theme.colors.background} 100%)`
    }}>
      
      {/* Header ejecutivo */}
      {renderDirectionHeader}
      
      {/* Métricas ejecutivas destacadas */}
      <div style={{ padding: `0 ${theme.spacing.lg}` }}>
        {renderExecutiveMetrics}
      </div>
      
      {/* Dashboard principal con períodos dinámicos - PROPS MEMOIZADAS */}
      <ControlGestionDashboard {...dashboardProps} />
      
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
            fontSize: '14px',
            fontWeight: 500
          }}>
            Panel Ejecutivo CDG - Banca March
          </Text>
          <Text style={{ 
            color: theme.colors.textSecondary,
            fontSize: '12px'
          }}>
            Sistema de Control de Gestión Inteligente con IA | © 2025 Todos los derechos reservados
          </Text>
          {lastUpdate && (
            <Text style={{ 
              color: theme.colors.textSecondary,
              fontSize: '11px',
              fontStyle: 'italic'
            }}>
              Datos actualizados: {lastUpdate.toLocaleString('es-ES')}
            </Text>
          )}
        </Space>
      </div>
    </div>
  );
};

export default DireccionView;
