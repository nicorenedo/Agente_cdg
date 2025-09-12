// frontend/src/pages/GestorView.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Row,
  Col,
  Typography,
  Space,
  Card,
  Alert,
  FloatButton,
  Button,
  Avatar,
  Tag,
  notification,
  Badge
} from 'antd';
import {
  DashboardOutlined,
  ReloadOutlined,
  SettingOutlined,
  UserOutlined,
  HomeOutlined,
  TrophyOutlined,
  MessageOutlined,
  BarChartOutlined,
  TeamOutlined,
  RobotOutlined,
  ExpandOutlined,
  CompressOutlined,
  CloseOutlined
} from '@ant-design/icons';

import TopBar from '../components/common/TopBar';
import KPICards from '../components/Dashboard/KPICards';
import InteractiveCharts from '../components/Dashboard/InteractiveCharts';
import ConversationalPivot from '../components/Dashboard/ConversationalPivot';
import DrillDownView from '../components/Dashboard/DrillDownView';
import ChatInterface from '../components/Dashboard/ChatInterface';
import Loader from '../components/common/Loader';
import ErrorState from '../components/common/ErrorState';

import api from '../services/api';
import analyticsService from '../services/analyticsService';
import AdminService from '../services/adminService';
import theme from '../styles/theme';

const { Content } = Layout;
const { Title, Text } = Typography;

/**
 * ✅ ACTUALIZADO: GestorView con ConversationalPivot integrado
 * -----------------------------------------------------------
 * - Integración completa del nuevo ConversationalPivot.jsx
 * - Chat lateral funcional para pivoteo de gráficos
 * - Solo modifica el gráfico de análisis general
 * - Layout responsivo con chat visible/oculto
 */
const GestorView = () => {
  // ✅ URL params y navegación
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // ✅ Estados principales
  const [gestorId, setGestorId] = useState(null);
  const [gestorInfo, setGestorInfo] = useState(null);
  const [periodo, setPeriodo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshToken, setRefreshToken] = useState(0);

  // ✅ Estados de interacción de gráficos
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [currentChartConfig, setCurrentChartConfig] = useState(null);
  const [pivotHistory, setPivotHistory] = useState([]);

  // ✅ Estados de UI - NUEVO: gestión del chat conversacional
  const [showChat, setShowChat] = useState(false);
  const [showConversationalPivot, setShowConversationalPivot] = useState(true); // ✅ Visible por defecto
  const [chatExpanded, setChatExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);

  // ✅ Extraer gestor de URL params - estable
  const gestorFromUrl = useMemo(() => {
    const gestorParam = searchParams.get('gestor');
    
    if (!gestorParam) {
      console.warn('[GestorView] No gestor parameter in URL');
      return null;
    }
    
    const parsed = parseInt(gestorParam, 10);
    if (isNaN(parsed)) {
      console.warn('[GestorView] Invalid gestor ID:', gestorParam);
      return gestorParam;
    }
    
    return parsed;
  }, [searchParams]);

  // ✅ Normalizar período de forma estable
  const normalizedPeriodo = useMemo(() => {
    if (!periodo) return "2025-10";
    if (typeof periodo === 'string') return periodo;
    if (typeof periodo === 'object') {
      return periodo.periodo || periodo.value || periodo.latest || "2025-10";
    }
    return String(periodo);
  }, [periodo]);

  // ✅ Layout config responsivo mejorado
  const layoutConfig = useMemo(() => {
    if (showConversationalPivot) {
      return {
        chart: { xs: 24, sm: 24, md: 24, lg: 16, xl: 16, xxl: 16 },
        pivot: { xs: 24, sm: 24, md: 24, lg: 8, xl: 8, xxl: 8 }
      };
    }
    return {
      chart: { xs: 24, sm: 24, md: 24, lg: 24, xl: 24, xxl: 24 },
      pivot: { xs: 0, sm: 0, md: 0, lg: 0, xl: 0, xxl: 0 }
    };
  }, [showConversationalPivot]);

  // ✅ Cargar información del gestor MEJORADO
  const loadGestorInfo = useCallback(async (id) => {
    try {
      console.log('[GestorView] Loading gestor info for ID:', id);
      
      // Obtener información del segmento usando analyticsService
      let segmentInfo = null;
      try {
        const segmentData = await analyticsService.getSegmentForGestorSafe(id);
        if (segmentData) {
          segmentInfo = {
            nombre: segmentData.segmentoNombre,
            id: segmentData.segmentoId
          };
          console.log('[GestorView] ✅ Segment info loaded:', segmentData);
        }
      } catch (segErr) {
        console.warn('[GestorView] Could not load segment info:', segErr);
        segmentInfo = { nombre: 'Segmento no disponible', id: 'N/A' };
      }

      // Intentar obtener info completa del gestor
      const gestores = await api.basic.allGestores();
      const gestorData = Array.isArray(gestores) 
        ? gestores.find(g => 
            String(g.id || g.gestor_id || g.GESTOR_ID) === String(id)
          )
        : null;

      if (gestorData) {
        const processedInfo = {
          id: gestorData.id || gestorData.gestor_id || gestorData.GESTOR_ID,
          nombre: gestorData.nombre || gestorData.DESC_GESTOR || gestorData.name || `Gestor ${id}`,
          centro: gestorData.centro || gestorData.DESC_CENTRO || gestorData.CENTRO || 'Centro no especificado',
          segmento: segmentInfo ? `${segmentInfo.nombre} (${segmentInfo.id})` : gestorData.segmento || gestorData.DESC_SEGMENTO || 'No especificado',
          performance: gestorData.performance || 'Regular',
          email: gestorData.email || null,
          telefono: gestorData.telefono || null,
          fechaAlta: gestorData.fecha_alta || null,
          activo: gestorData.activo !== false,
          segmentInfo
        };
        
        console.log('[GestorView] ✅ Gestor info loaded:', processedInfo);
        return processedInfo;
      }

      // Fallback con información del segmento
      const fallbackInfo = {
        id,
        nombre: `Gestor ${id}`,
        centro: 'Centro no especificado',
        segmento: segmentInfo ? `${segmentInfo.nombre} (${segmentInfo.id})` : 'Segmento no especificado',
        performance: 'N/A',
        activo: true,
        segmentInfo
      };
      
      console.log('[GestorView] Using fallback info:', fallbackInfo);
      return fallbackInfo;
      
    } catch (err) {
      console.error('[GestorView] Error loading gestor info:', err);
      return {
        id,
        nombre: `Gestor ${id}`,
        centro: 'Centro no disponible',
        segmento: 'Segmento no disponible',
        performance: 'Error',
        activo: false,
        error: err.message
      };
    }
  }, []);

  // ✅ Handlers de navegación y cambios
  const handlePeriodChange = useCallback((newPeriodo) => {
    console.log('[GestorView] Period change requested:', newPeriodo);
    
    const normalizedNewPeriod = typeof newPeriodo === 'object' 
      ? newPeriodo.periodo || newPeriodo.value || newPeriodo.latest || String(newPeriodo)
      : String(newPeriodo);
    
    setPeriodo(normalizedNewPeriod);
    setRefreshToken(prev => prev + 1);
    
    // Limpiar cache al cambiar período
    if (analyticsService.clearAnalyticsCache) {
      analyticsService.clearAnalyticsCache();
    }
    
    notification.info({
      message: 'Período Actualizado',
      description: `Cambiado a ${normalizedNewPeriod}. Actualizando datos...`,
      duration: 2,
      placement: 'topRight'
    });
  }, []);

  const handleGestorChange = useCallback((newGestorId) => {
    console.log('[GestorView] Gestor change requested:', newGestorId);
    
    if (newGestorId) {
      // Limpiar cache al cambiar gestor
      if (analyticsService.clearAnalyticsCache) {
        analyticsService.clearAnalyticsCache();
      }
      
      // Actualizar URL y recargar
      navigate(`/gestor-dashboard?gestor=${encodeURIComponent(newGestorId)}`, { replace: true });
    }
  }, [navigate]);

  const handleBackToLanding = useCallback(() => {
    // Limpiar estados al salir
    if (analyticsService.clearAnalyticsCache) {
      analyticsService.clearAnalyticsCache();
    }
    navigate('/');
  }, [navigate]);

  // ✅ Handlers de interacción mejorados
  const handleEntitySelection = useCallback((entity, source) => {
    const enrichedEntity = { 
      ...entity, 
      source, 
      timestamp: new Date().toISOString(),
      mode: 'gestor',
      gestorId,
      periodo: normalizedPeriodo
    };
    
    setSelectedEntity(enrichedEntity);
    console.log(`[GestorView] Entity selected from ${source}:`, enrichedEntity);
  }, [gestorId, normalizedPeriodo]);

  const handleDrillDownLeafSelection = useCallback((leafEntity) => {
    console.log('[GestorView] Drill-down leaf selected:', leafEntity);
    
    const enrichedLeaf = {
      ...leafEntity,
      source: 'drill_down',
      timestamp: new Date().toISOString(),
      mode: 'gestor',
      gestorId,
      periodo: normalizedPeriodo
    };
    
    setSelectedEntity(enrichedLeaf);
    
    // Si es un contrato, mostrar el panel conversacional para análisis detallado
    if (leafEntity._level === 'contratos') {
      setShowConversationalPivot(true);
      
      notification.success({
        message: 'Contrato Seleccionado',
        description: `Contrato ${leafEntity.nombre} disponible para análisis detallado`,
        duration: 3,
        placement: 'topRight'
      });
    }
  }, [gestorId, normalizedPeriodo]);

  // ✅ NUEVO: Handlers del ConversationalPivot
  const handleConversationalChartUpdate = useCallback((newChartConfig) => {
    console.log('[GestorView] 🤖 Chart updated from ConversationalPivot:', newChartConfig);
    
    setCurrentChartConfig({
      ...newChartConfig,
      updatedAt: new Date().toISOString(),
      source: 'conversational_pivot',
      mode: 'gestor',
      gestorId
    });
    
    notification.success({
      message: 'Gráfico Actualizado',
      description: 'El gráfico se ha modificado mediante chat conversacional',
      duration: 2,
      placement: 'topRight'
    });
  }, [gestorId]);

  // ✅ Handlers del asistente conversacional MEJORADOS
  const handleChartUpdate = useCallback((chartConfig) => {
    console.log('[GestorView] Chart updated from InteractiveCharts:', chartConfig);
    
    setCurrentChartConfig({
      ...chartConfig,
      generatedAt: new Date().toISOString(),
      source: 'interactive_charts',
      mode: 'gestor',
      gestorId
    });
  }, [gestorId]);

  const handleChartPivot = useCallback((result, message) => {
    console.log('[GestorView] Chart pivot executed:', { result, message });
    
    // Actualizar historial de pivots
    const pivotEntry = {
      id: Date.now(),
      message,
      timestamp: new Date().toISOString(),
      success: !!result,
      chartType: result?.meta?.type || 'unknown',
      gestorId
    };
    
    setPivotHistory(prev => [pivotEntry, ...prev.slice(0, 9)]); // Mantener últimos 10
    
    // Actualizar configuración actual
    if (result) {
      setCurrentChartConfig({
        ...result,
        pivotedAt: new Date().toISOString(),
        source: 'pivot',
        mode: 'gestor',
        gestorId
      });
    }
  }, [gestorId]);

  const handleNewChart = useCallback((chartConfig) => {
    console.log('[GestorView] New chart generated:', chartConfig);
    
    const enrichedConfig = {
      ...chartConfig,
      generatedAt: new Date().toISOString(),
      source: 'chat_interface',
      mode: 'gestor',
      gestorId
    };
    
    setCurrentChartConfig(enrichedConfig);
    
    // Auto-abrir panel conversacional si está cerrado
    setShowConversationalPivot(true);
    
    notification.success({
      message: 'Gráfico Generado',
      description: 'Se ha creado un nuevo gráfico personalizado',
      duration: 3,
      placement: 'topRight'
    });
  }, [gestorId]);

  const handleChatCommand = useCallback((command, payload) => {
    console.log('[GestorView] Chat command received:', command, payload);
    
    switch (command) {
      case 'open_drill_down':
        if (payload?.entity) {
          handleDrillDownLeafSelection(payload.entity);
        }
        break;
      case 'pivot_chart':
        if (payload?.message && currentChartConfig) {
          console.log('[GestorView] Pivot request forwarded to ConversationalPivot');
        }
        break;
      case 'export_report':
        console.log('[GestorView] Export report requested:', payload);
        break;
      default:
        console.log(`[GestorView] Unknown command: ${command}`, payload);
    }
  }, [handleDrillDownLeafSelection, currentChartConfig]);

  // ✅ NUEVOS HANDLERS PARA CHATINTERFACE
  const handleChatModelChange = useCallback((model) => {
    console.log('[GestorView] 🔄 Chat model changed:', model);
  }, []);

  const handleChatSettingsChange = useCallback((settings) => {
    console.log('[GestorView] ⚙️ Chat settings changed:', settings);
  }, []);

  const handleChatClear = useCallback(() => {
    console.log('[GestorView] 🧹 Chat history cleared');
    setCurrentChartConfig(null);
  }, []);

  // ✅ Handlers de UI
  const handleChatToggleExpand = useCallback(() => {
    setChatExpanded(prev => !prev);
  }, []);

  const handleRefreshAll = useCallback(async () => {
    console.log('[GestorView] Refreshing all data...');
    
    setRefreshToken(prev => prev + 1);
    
    // Limpiar todos los caches
    if (analyticsService.clearAnalyticsCache) {
      analyticsService.clearAnalyticsCache();
    }
    
    try {
      await AdminService.ping();
      
      notification.success({
        message: 'Datos Actualizados',
        description: 'Todos los componentes han sido refrescados',
        duration: 2,
        placement: 'topRight'
      });
    } catch (err) {
      console.warn('[GestorView] Health check failed on refresh:', err);
      notification.warning({
        message: 'Refresh Parcial',
        description: 'Los datos se actualizaron pero hay problemas de conectividad',
        duration: 3,
        placement: 'topRight'
      });
    }
  }, []);

  // ✅ Configuración dinámica del chat
  const chatConfig = useMemo(() => {
    if (chatExpanded) {
      return {
        width: '80vw',
        height: '80vh',
        bottom: '10vh',
        right: '10vw',
        zIndex: 2000
      };
    }
    return {
      width: 420,
      height: 520,
      bottom: 80,
      right: theme.spacing?.lg || 24,
      zIndex: 1000
    };
  }, [chatExpanded]);

  // ✅ Inicialización MEJORADA
  useEffect(() => {
    const initializeGestorView = async () => {
      if (!gestorFromUrl) {
        setError('No se especificó un gestor válido en la URL. Redirigiendo al inicio...');
        setTimeout(() => navigate('/'), 3000);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        console.log('[GestorView] Initializing for gestor:', gestorFromUrl);

        // Inicialización paralela
        const [initResult, latestPeriod, gestorData] = await Promise.all([
          AdminService.init().catch(err => ({ ok: false, errors: [err.message] })),
          api.catalogs.latestPeriod().catch(() => "2025-10"),
          loadGestorInfo(gestorFromUrl)
        ]);

        // Validar estado del sistema
        if (!initResult.ok) {
          console.warn('[GestorView] System health issues:', initResult.errors);
          notification.warning({
            message: 'Estado del Sistema',
            description: 'Se detectaron problemas menores. Algunos datos pueden estar en caché.',
            duration: 5,
            placement: 'topRight'
          });
        }

        // Configurar estados finales
        setSystemHealth(initResult);
        
        // Normalizar período
        if (latestPeriod && typeof latestPeriod === 'object') {
          setPeriodo(latestPeriod.periodo || latestPeriod.value || latestPeriod.latest || "2025-10");
        } else {
          setPeriodo(latestPeriod || "2025-10");
        }
        
        setGestorId(gestorFromUrl);
        setGestorInfo(gestorData);

        // Mostrar notificación de bienvenida
        if (gestorData.nombre && !gestorData.error) {
          notification.success({
            message: '¡Bienvenido!',
            description: `Dashboard cargado para ${gestorData.nombre}`,
            duration: 3,
            placement: 'topRight'
          });
        }
        
      } catch (err) {
        console.error('[GestorView] Initialization error:', err);
        setError(err?.message || 'Error al inicializar el dashboard del gestor');
        
        notification.error({
          message: 'Error de Inicialización',
          description: 'No se pudo cargar el dashboard. Inténtalo de nuevo.',
          duration: 5,
          placement: 'topRight'
        });
      } finally {
        setLoading(false);
      }
    };

    initializeGestorView();
  }, [gestorFromUrl, navigate, loadGestorInfo]);

  // ✅ Estados de carga y error
  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh', backgroundColor: theme.colors?.background || '#fafafa' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          flexDirection: 'column'
        }}>
          <div style={{
            padding: '40px',
            backgroundColor: 'white',
            borderRadius: theme.token?.borderRadius || 8,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            textAlign: 'center'
          }}>
            <Avatar 
              size={64} 
              icon={<UserOutlined />} 
              style={{ 
                backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff',
                marginBottom: 24
              }}
            />
            <Loader 
              tip="Inicializando Dashboard Personal..."
              size="large"
            />
            <Text type="secondary" style={{ marginTop: 16, display: 'block' }}>
              Cargando datos del gestor {gestorFromUrl}...
            </Text>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout style={{ minHeight: '100vh', backgroundColor: theme.colors?.background || '#fafafa' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh' 
        }}>
          <ErrorState
            error={error}
            message="Error al cargar el Dashboard Personal"
            description="No se pudo inicializar la vista del gestor."
            onRetry={handleBackToLanding}
            size="large"
          />
        </div>
      </Layout>
    );
  }

  return (
    <Layout style={{ 
      minHeight: '100vh', 
      backgroundColor: theme.colors?.background || '#fafafa',
      overflow: 'hidden'
    }}>
      {/* ✅ TopBar */}
      <TopBar
        valuePeriod={normalizedPeriodo}
        onPeriodChange={handlePeriodChange}
        valueGestor={gestorId}
        onGestorChange={handleGestorChange}
        onRefresh={handleRefreshAll}
        compact={false}
        showHelp={true}
      />

      {/* Contenido principal */}
      <Content style={{
        marginTop: 64,
        padding: theme.spacing?.lg || 24,
        overflowY: 'auto',
        height: 'calc(100vh - 64px)'
      }}>
        {/* ✅ Header personalizado mejorado */}
        <div style={{ marginBottom: theme.spacing?.lg || 24 }}>
          <Card style={{
            background: `linear-gradient(135deg, ${theme.colors?.bmGreenPrimary || '#1890ff'}08, ${theme.colors?.bmGreenLight || '#52c41a'}15)`,
            border: `1px solid ${theme.colors?.bmGreenPrimary || '#1890ff'}40`,
            borderRadius: theme.token?.borderRadius || 8
          }}>
            <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                <Avatar 
                  size={60} 
                  icon={<UserOutlined />} 
                  style={{ 
                    backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff',
                    fontSize: 24
                  }}
                />
                <div>
                  <Title 
                    level={2} 
                    style={{ 
                      color: theme.colors?.bmGreenPrimary || '#1890ff', 
                      margin: 0,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12
                    }}
                  >
                    <DashboardOutlined />
                    Mi Panel Personal
                    <Badge count="Gestor" style={{ marginLeft: 8 }} />
                  </Title>
                  <div style={{ marginTop: 8 }}>
                    <Text style={{ fontSize: 15, fontWeight: 500 }}>
                      {gestorInfo?.nombre || `Gestor ${gestorId}`}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 13, marginLeft: 8 }}>
                      • {gestorInfo?.centro} • {gestorInfo?.segmento}
                    </Text>
                  </div>
                  <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 16 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Período: <strong>{normalizedPeriodo}</strong>
                    </Text>
                    {pivotHistory.length > 0 && (
                      <Badge 
                        count={`${pivotHistory.length} pivots`} 
                        size="small" 
                        style={{ backgroundColor: '#722ed1' }}
                      />
                    )}
                  </div>
                </div>
              </div>
              
              <Space direction="vertical" align="end">
                <div style={{ textAlign: 'right' }}>
                  <Tag color={
                    gestorInfo?.performance === 'Excelente' ? 'green' :
                    gestorInfo?.performance === 'Bueno' ? 'blue' :
                    gestorInfo?.performance === 'Regular' ? 'orange' : 'default'
                  }>
                    {gestorInfo?.performance || 'N/A'}
                  </Tag>
                </div>
                <Button 
                  type="text" 
                  icon={<HomeOutlined />} 
                  onClick={handleBackToLanding}
                >
                  Volver
                </Button>
              </Space>
            </Space>
          </Card>
        </div>

        {/* Alertas de sistema */}
        {systemHealth && !systemHealth.ok && (
          <Alert
            message="Estado del Sistema"
            description={`Se detectaron ${systemHealth.errors.length} problema${systemHealth.errors.length !== 1 ? 's' : ''} menor${systemHealth.errors.length !== 1 ? 'es' : ''}. El dashboard funciona con datos en caché.`}
            type="warning"
            showIcon
            closable
            style={{ marginBottom: theme.spacing?.md || 16 }}
          />
        )}

        {/* ✅ KPIs personalizados */}
        <div style={{ marginBottom: theme.spacing?.lg || 24 }}>
          <KPICards
            mode="gestor"
            periodo={normalizedPeriodo}
            gestorId={gestorId}
            onKpiClick={(kpi, data) => handleEntitySelection({ 
              type: 'kpi', 
              kpi, 
              data 
            }, 'kpi_cards')}
            refreshToken={refreshToken}
          />
        </div>

        {/* ✅ Grid principal con InteractiveCharts + ConversationalPivot */}
        <Row gutter={[24, 24]} style={{ marginBottom: theme.spacing?.lg || 24 }}>
          <Col {...layoutConfig.chart}>
            <InteractiveCharts
              mode="gestor"
              periodo={normalizedPeriodo}
              gestorId={gestorId}
              metric="MARGEN"
              height={480}
              onReload={handleRefreshAll}
              onSelectEntity={(entity) => handleEntitySelection(entity, 'interactive_charts')}
              externalChartConfig={currentChartConfig}
              onChartConfigChange={setCurrentChartConfig}
              onChartUpdate={handleChartUpdate}
              onChartPivot={handleChartPivot}
              key={`interactive-charts-${refreshToken}`}
            />
          </Col>

          {/* ✅ NUEVO: ConversationalPivot integrado */}
          {showConversationalPivot && (
            <Col {...layoutConfig.pivot}>
              <Card
                title={
                  <Space>
                    <RobotOutlined style={{ color: '#722ed1' }} />
                    <span>Chat Conversacional</span>
                    <Badge count="IA" style={{ backgroundColor: '#722ed1' }} />
                  </Space>
                }
                extra={
                  <Space>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Solo gráfico análisis general
                    </Text>
                    <Button 
                      type="text" 
                      size="small"
                      icon={<CloseOutlined />}
                      onClick={() => setShowConversationalPivot(false)}
                    />
                  </Space>
                }
                style={{ height: 600 }}
                styles={{ body: { height: 520, padding: 0 }}}
              >
                <ConversationalPivot
                  mode="gestor"
                  gestorId={gestorId}
                  periodo={normalizedPeriodo}
                  currentChartConfig={currentChartConfig}
                  onChartUpdate={handleConversationalChartUpdate}
                  style={{ height: '100%' }}
                />
              </Card>
            </Col>
          )}
        </Row>

        {/* ✅ Drill-down con props correctos */}
        <div style={{ marginBottom: theme.spacing?.lg || 24 }}>
          <Card
            title={
              <Space>
                <TeamOutlined style={{ color: theme.colors?.bmGreenPrimary }} />
                <span>Exploración de Mi Cartera</span>
                <Tag color="blue">Modo Personal</Tag>
              </Space>
            }
            extra={
              <Space>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Clientes → Contratos
                </Text>
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  size="small"
                  onClick={() => setRefreshToken(prev => prev + 1)}
                >
                  Actualizar
                </Button>
              </Space>
            }
          >
            <DrillDownView
              mode="gestor"
              periodo={normalizedPeriodo}
              gestorId={gestorId}
              onSelectLeaf={handleDrillDownLeafSelection}
              refreshToken={refreshToken}
              style={{ minHeight: 400 }}
            />
          </Card>
        </div>

        {/* ✅ Panel de información del elemento seleccionado */}
        {selectedEntity && (
          <div style={{ marginBottom: theme.spacing?.lg || 24 }}>
            <Card
              title="Elemento Seleccionado"
              size="small"
              style={{
                borderColor: theme.colors?.bmGreenPrimary,
                borderWidth: 2
              }}
              extra={
                <Button
                  type="text"
                  size="small"
                  onClick={() => setSelectedEntity(null)}
                >
                  ✕
                </Button>
              }
            >
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div>
                  <Text strong>Nombre:</Text> {selectedEntity.nombre || selectedEntity.name || 'N/A'}
                </div>
                {selectedEntity._level && (
                  <div>
                    <Text strong>Tipo:</Text> <Tag color="blue">{selectedEntity._level}</Tag>
                  </div>
                )}
                {selectedEntity.source && (
                  <div>
                    <Text strong>Origen:</Text> <Tag color="green">{selectedEntity.source}</Tag>
                  </div>
                )}
                {selectedEntity.ingresos && (
                  <div>
                    <Text strong>Ingresos:</Text> €{new Intl.NumberFormat('es-ES', { notation: 'compact' }).format(selectedEntity.ingresos)}
                  </div>
                )}
                {selectedEntity.margen_pct && (
                  <div>
                    <Text strong>Margen:</Text> {selectedEntity.margen_pct.toFixed(1)}%
                  </div>
                )}
              </Space>
            </Card>
          </div>
        )}
      </Content>

      {/* ✅ CHAT FLOTANTE ACTUALIZADO CON NUEVAS PROPS */}
      {showChat && (
        <div style={{
          position: 'fixed',
          ...chatConfig,
          borderRadius: chatExpanded ? 8 : theme.token?.borderRadius || 8,
          boxShadow: chatExpanded 
            ? '0 16px 48px rgba(0,0,0,0.25)' 
            : '0 8px 24px rgba(0,0,0,0.15)',
          border: `2px solid ${theme.colors?.bmGreenPrimary || '#1890ff'}40`,
          backgroundColor: 'white',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* Header del chat */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '12px 16px',
            borderBottom: '1px solid #f0f0f0',
            backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff',
            borderRadius: chatExpanded ? '6px 6px 0 0' : `${theme.token?.borderRadius || 8}px ${theme.token?.borderRadius || 8}px 0 0`
          }}>
            <Space>
              <Text strong style={{ color: 'white', fontSize: 14 }}>
                🤖 Asistente CDG Personal
              </Text>
              <Badge count="Dashboard Gestor" size="small" style={{ backgroundColor: 'rgba(255,255,255,0.3)' }} />
            </Space>
            <Space>
              <Button
                type="text"
                size="small"
                icon={chatExpanded ? <CompressOutlined /> : <ExpandOutlined />}
                onClick={handleChatToggleExpand}
                style={{ color: 'white' }}
              />
              <Button
                type="text"
                size="small"
                onClick={() => setShowChat(false)}
                style={{ color: 'white', padding: 0, minWidth: 'auto' }}
              >
                ✕
              </Button>
            </Space>
          </div>
          
          {/* ✅ CONTENIDO DEL CHAT CON NUEVAS PROPS PARA GESTOR */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <ChatInterface
              scope="gestor"
              periodo={normalizedPeriodo}
              gestorId={gestorId}
              currentChartConfig={currentChartConfig}
              onNewChart={handleNewChart}
              onCommand={handleChatCommand}
              onModelChange={handleChatModelChange}
              onSettingsChange={handleChatSettingsChange}
              onClear={handleChatClear}
              expanded={chatExpanded}
              allowModelSelection={false}
              showSystemInfo={false}
              maxTokens={1000}
              style={{ height: '100%' }}
            />
          </div>
        </div>
      )}

      {/* Overlay para chat expandido */}
      {showChat && chatExpanded && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 1999,
            backdropFilter: 'blur(2px)'
          }}
          onClick={handleChatToggleExpand}
        />
      )}

      {/* ✅ Botones flotantes actualizados */}
      <FloatButton.Group 
        trigger="hover" 
        type="primary" 
        style={{ right: 24, bottom: 24 }}
        icon={<SettingOutlined />}
      >
        <FloatButton 
          icon={<RobotOutlined />} 
          tooltip="Toggle Chat Conversacional"
          onClick={() => setShowConversationalPivot(!showConversationalPivot)}
          badge={{ count: showConversationalPivot ? 1 : 0, dot: true }}
        />
        <FloatButton 
          icon={<ReloadOutlined />} 
          tooltip="Refrescar Todo"
          onClick={handleRefreshAll} 
        />
        <FloatButton 
          icon={<HomeOutlined />} 
          tooltip="Volver al Inicio"
          onClick={handleBackToLanding} 
        />
      </FloatButton.Group>

      {/* Chat toggle mejorado */}
      <FloatButton
        icon={showChat ? <MessageOutlined /> : <RobotOutlined />}
        tooltip={showChat ? 'Cerrar Chat General' : 'Abrir Chat General'}
        onClick={() => setShowChat(!showChat)}
        badge={{ count: showChat ? 1 : 0, dot: true }}
        style={{ 
          right: 24, 
          bottom: showConversationalPivot ? 180 : 140,
          backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff'
        }}
      />

      <FloatButton.BackTop />
    </Layout>
  );
};

export default GestorView;
