// frontend/src/pages/DireccionView.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  Badge,
  notification  // ✅ AÑADIR ESTA LÍNEA
} from 'antd';

import {
  DashboardOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  SettingOutlined,
  ExpandOutlined,
  CompressOutlined,
  MessageOutlined,
  RobotOutlined,
  CloseOutlined
} from '@ant-design/icons';
import TopBar from '../components/common/TopBar';
import KPICards from '../components/Dashboard/KPICards';
import InteractiveCharts from '../components/Dashboard/InteractiveCharts';
import DeviationAnalysis from '../components/Dashboard/DeviationAnalysis';
import DrillDownView from '../components/Dashboard/DrillDownView';
import ConversationalPivot from '../components/Dashboard/ConversationalPivot';
import ChatInterface from '../components/Dashboard/ChatInterface';
import Loader from '../components/common/Loader';
import ErrorState from '../components/common/ErrorState';
import api from '../services/api';
import AdminService from '../services/adminService';
import theme from '../styles/theme';

const { Content } = Layout;
const { Title, Text } = Typography;

/**
 * ✅ COMPLETAMENTE ACTUALIZADO: DireccionView con ConversationalPivot integrado
 * --------------------------------------------------------------------------
 * NUEVAS FUNCIONALIDADES:
 * 1. Integración completa del nuevo ConversationalPivot.jsx
 * 2. Chat lateral funcional para pivoteo de gráficos corporativos
 * 3. Solo modifica el gráfico de análisis general, no el de precios
 * 4. Layout responsivo con panel conversacional
 * 5. Comunicación bidireccional entre InteractiveCharts y ConversationalPivot
 * 6. Historial de pivots y estadísticas de interacción
 */
const DireccionView = () => {
  // ✅ ESTADOS PRINCIPALES
  const [periodo, setPeriodo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshToken, setRefreshToken] = useState(0);

  // ✅ ESTADOS DE INTERACCIÓN DE GRÁFICOS
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [currentChartConfig, setCurrentChartConfig] = useState(null);
  const [pivotHistory, setPivotHistory] = useState([]);

  // ✅ ESTADOS DE UI - NUEVO: gestión del chat conversacional
  const [showChat, setShowChat] = useState(false);
  const [showConversationalPivot, setShowConversationalPivot] = useState(true); // ✅ Visible por defecto
  const [chatExpanded, setChatExpanded] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);

  // ✅ Layout config responsivo mejorado para incluir chat
  const layoutConfig = useMemo(() => {
    if (showConversationalPivot) {
      return {
        chart: { xs: 24, sm: 24, md: 24, lg: 14, xl: 14, xxl: 14 },
        analysis: { xs: 24, sm: 24, md: 24, lg: 10, xl: 10, xxl: 10 },
        pivot: { xs: 24, sm: 24, md: 24, lg: 24, xl: 24, xxl: 24 }
      };
    }
    return {
      chart: { xs: 24, sm: 24, md: 12, lg: 12, xl: 12, xxl: 12 },
      analysis: { xs: 24, sm: 24, md: 12, lg: 12, xl: 12, xxl: 12 },
      pivot: { xs: 0, sm: 0, md: 0, lg: 0, xl: 0, xxl: 0 }
    };
  }, [showConversationalPivot]);

  // ✅ INICIALIZACIÓN MEJORADA
  useEffect(() => {
    const initializeView = async () => {
      try {
        setLoading(true);
        setError(null);

        console.log('[DireccionView] 🚀 Inicializando dashboard corporativo...');

        // Inicializar servicios y obtener período
        const [initResult, latestPeriod] = await Promise.all([
          AdminService.init(),
          api.catalogs.latestPeriod()
        ]);

        console.log('[DireccionView] 📊 Latest period response:', latestPeriod);

        // Validar estado del sistema
        if (!initResult.ok) {
          console.warn('[DireccionView] System health issues:', initResult.errors);
        }

        setSystemHealth(initResult);

        // ✅ NORMALIZACIÓN DE PERÍODO
        const periodoStr = typeof latestPeriod === 'object' 
          ? latestPeriod.latest || latestPeriod.period || '2025-10'
          : latestPeriod || '2025-10';
        
        console.log('[DireccionView] ✅ Período establecido:', periodoStr);
        setPeriodo(periodoStr);
        
      } catch (err) {
        console.error('[DireccionView] ❌ Initialization error:', err);
        setError(err?.message || 'Error al inicializar el dashboard');
        // Fallback en caso de error
        setPeriodo('2025-10');
      } finally {
        setLoading(false);
      }
    };

    initializeView();
  }, []);

  // ✅ HANDLERS DE PERÍODO
  const handlePeriodChange = useCallback((newPeriodo) => {
    console.log('[DireccionView] 📅 Period change requested:', newPeriodo);
    
    const periodoStr = typeof newPeriodo === 'object' 
      ? newPeriodo.latest || newPeriodo.period || newPeriodo
      : newPeriodo;
    
    console.log('[DireccionView] ✅ Period normalized:', periodoStr);
    setPeriodo(periodoStr);
    setRefreshToken(prev => prev + 1); // Forzar recarga de componentes
  }, []);

  // ✅ HANDLERS DE INTERACCIÓN MEJORADOS
  const handleEntitySelection = useCallback((entity, source) => {
    setSelectedEntity({ 
      ...entity,
      source,
      timestamp: new Date().toISOString(),
      mode: 'direccion',
      periodo
    });
    
    console.log(`[DireccionView] Entity selected from ${source}:`, entity);
  }, [periodo]);

  const handleDrillDownOpen = useCallback((entity) => {
    setSelectedEntity(entity);
    
    if (entity.type === 'gestor' && entity.id) {
      console.log(`[DireccionView] Opening gestor drill-down for:`, entity.id);
    }
  }, []);

  const handleDrillDownSelection = useCallback((record) => {
    console.log('[DireccionView] 📊 DrillDown selection:', record);
    
    setSelectedEntity({
      ...record,
      source: 'drill_down',
      timestamp: new Date().toISOString(),
      mode: 'direccion',
      periodo
    });

    if (record.tipo === 'contrato' || record._originalData?.CONTRATO_ID) {
      console.log('[DireccionView] Contract selected for detailed view:', record.id);
    }
  }, [periodo]);

  // ✅ NUEVO: Handlers del ConversationalPivot
  const handleConversationalChartUpdate = useCallback((newChartConfig) => {
    console.log('[DireccionView] 🤖 Chart updated from ConversationalPivot:', newChartConfig);
    
    setCurrentChartConfig({
      ...newChartConfig,
      updatedAt: new Date().toISOString(),
      source: 'conversational_pivot',
      mode: 'direccion'
    });
    
    notification.success({
      message: 'Gráfico Actualizado',
      description: 'El gráfico corporativo se ha modificado mediante chat conversacional',
      duration: 2,
      placement: 'topRight'
    });
  }, []);

  // ✅ HANDLERS DEL ASISTENTE CONVERSACIONAL MEJORADOS
  const handleChartUpdate = useCallback((chartConfig) => {
    console.log('[DireccionView] 📈 Chart updated from InteractiveCharts:', chartConfig);
    
    setCurrentChartConfig({
      ...chartConfig,
      generatedAt: new Date().toISOString(),
      source: 'interactive_charts',
      mode: 'direccion'
    });
  }, []);

  const handleChartPivot = useCallback((result, message) => {
    console.log('[DireccionView] 🔄 Pivot executed:', { result, message });

    const pivotEntry = {
      id: Date.now(),
      message,
      timestamp: new Date().toISOString(),
      success: !!result,
      chartType: result?.meta?.type || 'unknown'
    };

    setPivotHistory(prev => [pivotEntry, ...prev.slice(0, 9)]);

    if (result) {
      setCurrentChartConfig({
        ...result,
        pivotedAt: new Date().toISOString(),
        source: 'pivot',
        mode: 'direccion'
      });
    }
  }, []);

  const handleNewChart = useCallback((chartConfig) => {
    console.log('[DireccionView] 📈 New chart generated:', chartConfig);

    setCurrentChartConfig({
      ...chartConfig,
      generatedAt: new Date().toISOString(),
      source: 'chat_interface',
      mode: 'direccion'
    });

    if (!showChat) {
      setShowChat(true);
    }
  }, [showChat]);

  const handleChatCommand = useCallback((command, payload) => {
    console.log('[DireccionView] 🤖 Chat command:', command, payload);

    switch (command) {
      case 'open_drill_down':
        if (payload?.entity) {
          handleDrillDownOpen(payload.entity);
        }
        break;
      case 'pivot_chart':
        if (payload?.message && currentChartConfig) {
          console.log('[DireccionView] Pivot command forwarded');
        }
        break;
      case 'export_report':
        console.log('[DireccionView] Export report requested:', payload);
        break;
      default:
        console.log('[DireccionView] Unknown command:', command, payload);
    }
  }, [handleDrillDownOpen, currentChartConfig]);

  // ✅ NUEVOS HANDLERS PARA CHATINTERFACE
  const handleChatModelChange = useCallback((model) => {
    console.log('[DireccionView] 🔄 Chat model changed:', model);
  }, []);

  const handleChatSettingsChange = useCallback((settings) => {
    console.log('[DireccionView] ⚙️ Chat settings changed:', settings);
  }, []);

  const handleChatClear = useCallback(() => {
    console.log('[DireccionView] 🧹 Chat history cleared');
    setCurrentChartConfig(null);
  }, []);

  const handleRefreshAll = useCallback(async () => {
    console.log('[DireccionView] 🔄 Refreshing all components...');
    setRefreshToken(prev => prev + 1);
    
    try {
      await AdminService.ping();
      console.log('[DireccionView] ✅ Health check passed');
    } catch (err) {
      console.warn('[DireccionView] ⚠️ Health check failed:', err);
    }
  }, []);

  const handleToggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullscreen(true);
      });
    } else {
      document.exitFullscreen().then(() => {
        setIsFullscreen(false);
      });
    }
  }, []);

  // ✅ CONFIGURACIONES MEMOIZADAS
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

  // ✅ ESTADOS DE CARGA Y ERROR
  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh', backgroundColor: theme.colors?.background || '#fafafa' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <Loader tip="Inicializando Dashboard de Dirección..." size="large" />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout style={{ minHeight: '100vh', backgroundColor: theme.colors?.background || '#fafafa' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
          <ErrorState
            error={error}
            message="Error al cargar el Dashboard"
            description="No se pudo inicializar la vista de Dirección. Por favor, revisa tu conexión e inténtalo de nuevo."
            onRetry={() => window.location.reload()}
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
        valuePeriod={periodo}
        onPeriodChange={handlePeriodChange}
        onRefresh={handleRefreshAll}
        compact={false}
        showHelp={true}
      />

      {/* Contenido principal */}
      <Content style={{
        marginTop: 64, // Altura del TopBar
        padding: theme.spacing?.lg || 24,
        overflowY: 'auto',
        height: 'calc(100vh - 64px)'
      }}>
        {/* ✅ Header de la vista mejorado */}
        <div style={{ marginBottom: theme.spacing?.lg || 24 }}>
          <Space align="center" style={{ width: '100%', justifyContent: 'space-between' }}>
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
                Panel Ejecutivo de Dirección
                <Badge count="Corporativo" style={{ marginLeft: 8 }} />
              </Title>
              <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 16 }}>
                <Text type="secondary" style={{ fontSize: 14 }}>
                  Visión corporativa consolidada • Período: <strong>{periodo}</strong>
                </Text>
                {pivotHistory.length > 0 && (
                  <Badge 
                    count={`${pivotHistory.length} pivots`} 
                    size="small" 
                    style={{ backgroundColor: '#722ed1' }}
                  />
                )}
                {selectedEntity && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    • Selección: {selectedEntity.source}
                  </Text>
                )}
              </div>
            </div>
            
            <Space>
              <Text 
                type="secondary" 
                style={{ fontSize: 12 }}
                title="Última actualización"
              >
                Actualizado: {new Date().toLocaleTimeString()}
              </Text>
            </Space>
          </Space>
        </div>

        {/* Alertas de estado del sistema */}
        {systemHealth && !systemHealth.ok && (
          <Alert
            message="Estado del Sistema"
            description={`Se detectaron ${systemHealth.errors.length} problemas menores en la conectividad. El dashboard funciona con datos en caché.`}
            type="warning"
            showIcon
            closable
            style={{ marginBottom: theme.spacing?.md || 16 }}
          />
        )}

        {/* ✅ KPIs CORPORATIVOS */}
        <KPICards
          mode="direccion"
          periodo={periodo}
          onKpiClick={(kpi, data) => handleEntitySelection({ 
            type: 'kpi', 
            kpi, 
            data 
          }, 'kpi_cards')}
          style={{ marginBottom: theme.spacing?.lg || 24 }}
        />

        {/* ✅ Grid principal con InteractiveCharts y DeviationAnalysis */}
        <Row gutter={[24, 24]} style={{ marginTop: theme.spacing?.lg || 24 }}>
          {/* ✅ INTERACTIVECHARTS CON FILTROS EMBEBIDOS */}
          <Col {...layoutConfig.chart}>
            <InteractiveCharts
              mode="direccion"
              periodo={periodo}
              metric="CONTRATOS"
              chartType="horizontal_bar"
              filters={{}}
              height={460}
              onReload={handleRefreshAll}
              onSelectEntity={(entity) => handleEntitySelection(entity, 'interactive_charts')}
              externalChartConfig={currentChartConfig}
              onChartConfigChange={(config) => setCurrentChartConfig(config)}
              onChartUpdate={handleChartUpdate}
              onChartPivot={handleChartPivot}
              style={{ height: '100%' }}
              key={`interactive-charts-${refreshToken}`}
            />
          </Col>

          {/* Análisis de desviaciones */}
          <Col {...layoutConfig.analysis}>
            <DeviationAnalysis
              mode="direccion"
              periodo={periodo}
              bonusPool={50000}
              filters={{}}
              onReload={handleRefreshAll}
              onSelectRow={(entity) => handleEntitySelection(entity, 'deviation_analysis')}
              onOpenDrillDown={handleDrillDownOpen}
              style={{ height: 460 }}
            />
          </Col>
        </Row>

        {/* ✅ NUEVO: ConversationalPivot integrado */}
        {showConversationalPivot && (
          <Row gutter={[24, 24]} style={{ marginTop: theme.spacing?.lg || 24 }}>
            <Col {...layoutConfig.pivot}>
              <Card
                title={
                  <Space>
                    <RobotOutlined style={{ color: '#722ed1' }} />
                    <span>Asistente Conversacional Corporativo</span>
                    <Badge count="IA" style={{ backgroundColor: '#722ed1' }} />
                    {pivotHistory.length > 0 && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        • {pivotHistory.length} pivots
                      </Text>
                    )}
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
                style={{ 
                  height: 500,
                  borderRadius: theme.token?.borderRadius || 8,
                  border: `2px solid ${theme.colors?.bmGreenPrimary || '#1890ff'}40`
                }}
                styles={{ body: { height: 420, padding: 0 }}}
              >
                <ConversationalPivot
                  mode="direccion"
                  periodo={periodo}
                  currentChartConfig={currentChartConfig}
                  onChartUpdate={handleConversationalChartUpdate}
                  style={{ height: '100%' }}
                />
              </Card>
            </Col>
          </Row>
        )}

        {/* Drill-down navegable */}
        <Card
          title={
            <Space>
              <DashboardOutlined style={{ color: theme.colors?.bmGreenPrimary || '#1890ff' }} />
              <span>Análisis Navegable - Vista Corporativa</span>
              {selectedEntity?.source === 'drill_down' && (
                <Badge count="Activo" size="small" />
              )}
            </Space>
          }
          style={{ 
            marginTop: theme.spacing?.lg || 24,
            borderRadius: theme.token?.borderRadius || 8,
            boxShadow: theme.shadows?.card || '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <DrillDownView
            mode="direccion"
            periodo={periodo}
            onSelectLeaf={handleDrillDownSelection}
            refreshToken={refreshToken}
            style={{ minHeight: 400 }}
          />
        </Card>
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
          {/* Header del chat mejorado */}
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
                🤖 Asistente CDG Dirección
              </Text>
              <Badge count="Dashboard Corporativo" size="small" style={{ backgroundColor: 'rgba(255,255,255,0.3)' }} />
            </Space>
            <Space>
              <Button
                type="text"
                size="small"
                icon={chatExpanded ? <CompressOutlined /> : <ExpandOutlined />}
                onClick={() => setChatExpanded(prev => !prev)}
                style={{ color: 'white' }}
                title={chatExpanded ? 'Contraer chat' : 'Expandir chat'}
              />
              <Button
                type="text"
                size="small"
                onClick={() => setShowChat(false)}
                style={{ color: 'white', padding: 0, minWidth: 'auto' }}
                title="Cerrar chat"
              >
                ✕
              </Button>
            </Space>
          </div>
          
          {/* ✅ CONTENIDO DEL CHAT CON NUEVAS PROPS */}
          <div style={{ flex: 1, overflow: 'hidden' }}>
            <ChatInterface
              scope="direccion"
              periodo={periodo}
              currentChartConfig={currentChartConfig}
              onNewChart={handleNewChart}
              onCommand={handleChatCommand}
              onModelChange={handleChatModelChange}
              onSettingsChange={handleChatSettingsChange}
              onClear={handleChatClear}
              expanded={chatExpanded}
              allowModelSelection={true}
              showSystemInfo={true}
              maxTokens={2000}
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
          onClick={() => setChatExpanded(prev => !prev)}
        />
      )}

      {/* ✅ BOTONES FLOTANTES ACTUALIZADOS */}
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
          icon={<FullscreenOutlined />} 
          tooltip="Pantalla Completa"
          onClick={handleToggleFullscreen} 
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

      {/* Scroll to top */}
      <FloatButton.BackTop />
    </Layout>
  );
};

export default DireccionView;
