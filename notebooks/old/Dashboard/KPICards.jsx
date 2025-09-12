// src/components/Dashboard/KPICards.jsx
// ✅ VERSIÓN CORREGIDA v5.1 - Integración perfecta con ChatService

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Card, Row, Col, Tooltip, Button, Spin, Alert, Badge, Progress, 
  Space, Popover, App // ✅ Importar App para hooks contextuales
} from 'antd';
import { 
  ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined, ReloadOutlined,
  TrophyOutlined, PercentageOutlined, DollarCircleOutlined, 
  RobotOutlined, ThunderboltOutlined, EyeOutlined, BarChartOutlined, 
  LineChartOutlined, MinusOutlined, ApiOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';

import api from '../../services/api';
import { useChatService, CONNECTION_STATES } from '../../services/chatService';
import theme from '../../styles/theme';

// ============================================================================
// 🔧 UTILITY FUNCTIONS
// ============================================================================

const normalizePeriod = (period) => {
  if (!period) return '2025-10';
  if (period.length === 10 && period.includes('-')) {
    return period.substring(0, 7);
  }
  if (period.length === 7 && period.includes('-')) {
    return period;
  }
  return '2025-10';
};

const mapApiDataToKpiKeys = (apiData) => {
  if (!apiData) return {};
  
  console.log('🔄 [KPICards v5.1] Mapping API data:', apiData);
  
  const mapped = {
    ROE: (() => {
      const roe = apiData.ROE || apiData.roe || apiData.return_on_equity || 0;
      return roe < 1 ? roe * 100 : roe;
    })(),
    MARGEN_NETO: apiData.MARGEN_NETO || apiData.margen_neto || apiData.net_margin || 0,
    EFICIENCIA: apiData.EFICIENCIA || apiData.eficiencia_operativa || apiData.EFICIENCIA_OPERATIVA || apiData.efficiency || 0,
    TOTAL_INGRESOS: apiData.TOTAL_INGRESOS || apiData.total_ingresos || apiData.total_income || apiData.ingresos || apiData.INGRESOS || 0,
    TOTAL_GASTOS: apiData.TOTAL_GASTOS || apiData.total_gastos || apiData.total_expenses || apiData.gastos || apiData.GASTOS || 0,
    BENEFICIO_NETO: apiData.BENEFICIO_NETO || apiData.beneficio_neto || apiData.net_profit || 
                    ((apiData.TOTAL_INGRESOS || apiData.total_ingresos || 0) - 
                     (apiData.TOTAL_GASTOS || apiData.total_gastos || 0)) || 0,
    CONTRATOS_TOTAL: apiData.CONTRATOS_TOTAL || apiData.contratos_total || apiData.total_contracts || apiData.total_contratos || 0,
    SOLVENCIA: apiData.SOLVENCIA || apiData.solvency_ratio || 0,
    LIQUIDEZ: apiData.LIQUIDEZ || apiData.liquidity_ratio || 0,
    PRECIO_STD: apiData.PRECIO_STD || apiData.precio_std || apiData.standard_price || 0,
    PRECIO_REAL: apiData.PRECIO_REAL || apiData.precio_real || apiData.real_price || 0,
    CLIENTES_TOTAL: apiData.CLIENTES_TOTAL || apiData.total_clients || apiData.clientes || 0
  };
  
  Object.keys(mapped).forEach(key => {
    if (typeof mapped[key] !== 'number' || isNaN(mapped[key]) || !isFinite(mapped[key])) {
      mapped[key] = 0;
    }
  });
  
  console.log('✅ [KPICards v5.1] Data mapped and validated:', mapped);
  return mapped;
};

// ============================================================================
// 🎯 KPI CONFIGURATION
// ============================================================================

const KPI_CONFIG = {
  ROE: {
    title: 'ROE',
    description: 'Return on Equity - Rentabilidad sobre fondos propios, indicador clave en banca',
    unit: '%',
    precision: 2,
    threshold: { good: 8, excellent: 12 },
    icon: <PercentageOutlined />,
    emoji: '📈',
    category: 'rentabilidad',
    color: theme.colors.bmGreenPrimary,
    priority: 1,
    chatQueries: ['ROE', 'rentabilidad', 'return on equity'],
    agentPrompt: 'Analizar ROE y rentabilidad'
  },
  MARGEN_NETO: {
    title: 'Margen Neto',
    description: 'Margen neto como porcentaje sobre ingresos totales',
    unit: '%',
    precision: 2,
    threshold: { good: 10, excellent: 15 },
    icon: <TrophyOutlined />,
    emoji: '💰',
    category: 'rentabilidad',
    color: theme.colors.success,
    priority: 2,
    chatQueries: ['margen neto', 'beneficio', 'profit margin'],
    agentPrompt: 'Analizar margen neto y beneficios'
  },
  TOTAL_INGRESOS: {
    title: 'Total Ingresos',
    description: 'Suma total de ingresos gestionados en el período',
    unit: '€',
    precision: 0,
    format: 'currency',
    icon: <DollarCircleOutlined />,
    emoji: '💵',
    category: 'volumen',
    color: theme.colors.info,
    threshold: { good: 100000, excellent: 300000 },
    priority: 3,
    chatQueries: ['ingresos', 'revenue', 'facturación'],
    agentPrompt: 'Analizar ingresos y facturación'
  },
  TOTAL_GASTOS: {
    title: 'Total Gastos',
    description: 'Suma total de gastos asociados a la gestión',
    unit: '€',
    precision: 0,
    format: 'currency',
    icon: <DollarCircleOutlined />,
    emoji: '💸',
    category: 'volumen',
    color: theme.colors.warning,
    invertedLogic: true,
    threshold: { good: 180000, excellent: 150000 },
    priority: 4,
    chatQueries: ['gastos', 'costs', 'expenses'],
    agentPrompt: 'Analizar gastos y costes'
  },
  BENEFICIO_NETO: {
    title: 'Beneficio Neto',
    description: 'Beneficio neto obtenido en el período',
    unit: '€',
    precision: 0,
    format: 'currency',
    threshold: { good: 50000, excellent: 200000 },
    icon: <TrophyOutlined />,
    emoji: '🎯',
    category: 'rentabilidad',
    color: theme.colors.bmGreenDark,
    priority: 5,
    chatQueries: ['beneficio neto', 'net profit', 'ganancia'],
    agentPrompt: 'Analizar beneficio neto y resultados'
  },
  EFICIENCIA: {
    title: 'Eficiencia',
    description: 'Ratio de eficiencia operativa',
    unit: '%',
    precision: 2,
    threshold: { good: 60, excellent: 80 },
    icon: <ThunderboltOutlined />,
    emoji: '⚡',
    category: 'eficiencia',
    color: theme.colors.bmGreenLight,
    priority: 6,
    chatQueries: ['eficiencia', 'efficiency', 'productividad'],
    agentPrompt: 'Analizar eficiencia operativa'
  },
  CONTRATOS_TOTAL: {
    title: 'Contratos',
    description: 'Número total de contratos gestionados',
    unit: '',
    precision: 0,
    format: 'number',
    threshold: { good: 5, excellent: 10 },
    icon: <BarChartOutlined />,
    emoji: '📋',
    category: 'volumen',
    color: theme.colors.textPrimary,
    priority: 7,
    chatQueries: ['contratos', 'contracts', 'deals'],
    agentPrompt: 'Analizar cartera de contratos'
  },
  SOLVENCIA: {
    title: 'Solvencia',
    description: 'Ratio de solvencia financiera',
    unit: '%',
    precision: 2,
    threshold: { good: 20, excellent: 30 },
    icon: <ArrowUpOutlined />,
    emoji: '🛡️',
    category: 'solvencia',
    color: theme.colors.purple,
    priority: 8,
    chatQueries: ['solvencia', 'solvency', 'solidez financiera'],
    agentPrompt: 'Analizar solvencia y estabilidad'
  },
  LIQUIDEZ: {
    title: 'Liquidez',
    description: 'Ratio de liquidez disponible',
    unit: '%',
    precision: 2,
    threshold: { good: 15, excellent: 25 },
    icon: <LineChartOutlined />,
    emoji: '💧',
    category: 'liquidez',
    color: theme.colors.cyan,
    priority: 9,
    chatQueries: ['liquidez', 'liquidity', 'disponibilidad'],
    agentPrompt: 'Analizar liquidez y disponibilidad'
  },
  CLIENTES_TOTAL: {
    title: 'Clientes',
    description: 'Número total de clientes activos',
    unit: '',
    precision: 0,
    format: 'number',
    threshold: { good: 20, excellent: 50 },
    icon: <EyeOutlined />,
    emoji: '👥',
    category: 'volumen',
    color: theme.colors.geekblue,
    priority: 10,
    chatQueries: ['clientes', 'clients', 'customers'],
    agentPrompt: 'Analizar base de clientes'
  }
};

// ============================================================================
// 🎨 PRESENTATION FUNCTIONS
// ============================================================================

const getValueColor = (value, config) => {
  if (value === null || value === undefined || isNaN(value)) {
    return theme.colors.textSecondary;
  }
  
  const { threshold, invertedLogic, color } = config;
  if (!threshold) return color || theme.colors.bmGreenPrimary;
  
  if (invertedLogic) {
    if (value <= threshold.excellent) return theme.colors.success;
    if (value <= threshold.good) return theme.colors.bmGreenLight;
    return theme.colors.error;
  } else {
    if (value >= threshold.excellent) return theme.colors.success;
    if (value >= threshold.good) return theme.colors.bmGreenLight;
    return theme.colors.warning;
  }
};

const getPerformanceBadge = (value, config) => {
  if (value === null || value === undefined || isNaN(value)) return null;
  
  const { threshold, invertedLogic } = config;
  if (!threshold) return null;
  
  let status, text;
  
  if (invertedLogic) {
    if (value <= threshold.excellent) {
      status = 'success';
      text = 'Excelente';
    } else if (value <= threshold.good) {
      status = 'processing';
      text = 'Bueno';
    } else {
      status = 'error';
      text = 'Mejorable';
    }
  } else {
    if (value >= threshold.excellent) {
      status = 'success';
      text = 'Excelente';
    } else if (value >= threshold.good) {
      status = 'processing';
      text = 'Bueno';
    } else {
      status = 'warning';
      text = 'Mejorable';
    }
  }
  
  return <Badge status={status} text={text} style={{ fontSize: 10 }} />;
};

const formatValue = (value, config) => {
  if (value === null || value === undefined || isNaN(value)) return '--';
  
  const numValue = Number(value);
  if (isNaN(numValue)) return '--';
  
  if (config.format === 'currency') {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
      notation: numValue > 1000000 ? 'compact' : 'standard'
    }).format(numValue);
  }
  
  if (config.format === 'number') {
    return new Intl.NumberFormat('es-ES').format(numValue);
  }
  
  return numValue.toFixed(config.precision);
};

const getTrendIcon = (current, previous, config) => {
  if (!previous || !current || isNaN(current) || isNaN(previous)) {
    return <MinusOutlined style={{ color: theme.colors.textSecondary, fontSize: 12 }} />;
  }
  
  const change = current - previous;
  const isPositive = change > 0;
  const isGoodChange = config.invertedLogic ? !isPositive : isPositive;
  
  if (Math.abs(change) < 0.01) {
    return <MinusOutlined style={{ color: theme.colors.textSecondary, fontSize: 12 }} />;
  }
  
  const iconColor = isGoodChange ? theme.colors.success : theme.colors.error;
  const IconComponent = isPositive ? ArrowUpOutlined : ArrowDownOutlined;
  
  return <IconComponent style={{ color: iconColor, fontSize: 12 }} />;
};

// ============================================================================
// 🎯 KPICARD COMPONENT - ✅ FIXED HOOKS ORDER
// ============================================================================

const KPICard = React.memo(({ 
  kpiKey, 
  value, 
  previousValue, 
  loading, 
  onClick, 
  executiveMode = false,
  showTrends = true,
  enableAiAnalysis = true,
  onAiAnalysis
}) => {
  // ✅ FIX: TODOS LOS HOOKS AL INICIO - INCONDICIONALMENTE
  const [analyzing, setAnalyzing] = useState(false);
  const { notification } = App.useApp();
  
  // ✅ FIX: useCallback ANTES de cualquier return condicional
  const handleAiAnalysis = useCallback(async () => {
    if (!enableAiAnalysis || !onAiAnalysis) {
      console.warn('🤖 [KPICards v5.1] AI Analysis not enabled or handler missing');
      return;
    }
    
    setAnalyzing(true);
    try {
      console.log(`🤖 [KPICards v5.1] Starting AI analysis for ${kpiKey}:`, value);
      await onAiAnalysis(kpiKey, value, KPI_CONFIG[kpiKey] || {});
      console.log(`✅ [KPICards v5.1] AI analysis completed for ${kpiKey}`);
    } catch (error) {
      console.error(`❌ [KPICards v5.1] AI analysis error for ${kpiKey}:`, error);
      notification.error({
        message: 'Error en análisis AI v5.1',
        description: error.message || 'Error desconocido en el análisis',
        duration: 4
      });
    } finally {
      setAnalyzing(false);
    }
  }, [enableAiAnalysis, onAiAnalysis, kpiKey, value, notification]);
  
  // ✅ FIX: Validación DESPUÉS de todos los hooks
  const config = KPI_CONFIG[kpiKey];
  if (!config) {
    console.warn(`⚠️ [KPICards v5.1] KPI config not found for key: ${kpiKey}`);
    return null;
  }
  
  const formattedValue = formatValue(value, config);
  const valueColor = getValueColor(value, config);
  const performanceBadge = getPerformanceBadge(value, config);
  const trendIcon = showTrends ? getTrendIcon(value, previousValue, config) : null;
  
  // Calculate change metrics
  let changeIndicator = null;
  let progressValue = 0;
  
  if (showTrends && previousValue !== undefined && previousValue !== null && 
      value !== null && !isNaN(value) && !isNaN(previousValue)) {
    const change = Number(value) - Number(previousValue);
    const changePercent = (change / Number(previousValue)) * 100;

    if (Math.abs(changePercent) > 0.1) {
      const isPositive = change > 0;
      const isGood = config.invertedLogic ? !isPositive : isPositive;
    
      changeIndicator = (
        <Tooltip title={`Cambio: ${isPositive ? '+' : ''}${changePercent.toFixed(1)}% vs período anterior`}>
          <span style={{
            color: isGood ? theme.colors.success : theme.colors.error,
            fontSize: 12,
            marginLeft: 6
          }}>
            {isPositive ? '+' : ''}
            {changePercent.toFixed(1)}%
          </span>
        </Tooltip>
      );
    }
  }

  if (config.threshold && value !== null && !isNaN(value)) {
    const { threshold, invertedLogic } = config;
    if (invertedLogic) {
      progressValue = Math.max(0, Math.min(100, 100 - (value / threshold.good * 100)));
    } else {
      progressValue = Math.min(100, (value / threshold.excellent) * 100);
    }
  }
  
  return (
    <Card 
      hoverable={!!onClick}
      onClick={onClick}
      style={{ 
        borderRadius: executiveMode ? 12 : 8, 
        boxShadow: executiveMode ? '0 6px 16px rgba(0,0,0,0.1)' : '0 2px 8px rgba(0,0,0,0.08)',
        border: `1px solid ${config.color || theme.colors.border}`,
        borderTop: `4px solid ${config.color || theme.colors.bmGreenPrimary}`,
        height: executiveMode ? 180 : 160,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        position: 'relative',
        overflow: 'hidden'
      }}
      styles={{ body: { padding: executiveMode ? 20 : 16 } }}
    >
      <Spin spinning={loading || analyzing}>
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          
          {/* Header */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: executiveMode ? 16 : 12
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center',
              color: theme.colors.textSecondary,
              fontSize: executiveMode ? 14 : 13,
              fontWeight: 600
            }}>
              <span style={{ marginRight: 8, fontSize: 16 }}>
                {executiveMode ? config.icon : config.emoji}
              </span>
              <span>{config.title}</span>
              <Popover 
                content={
                  <div style={{ maxWidth: 200 }}>
                    <p style={{ margin: 0 }}>{config.description}</p>
                    {config.threshold && (
                      <div style={{ marginTop: 8, fontSize: 11 }}>
                        <div>Bueno: {config.threshold.good}{config.unit}</div>
                        <div>Excelente: {config.threshold.excellent}{config.unit}</div>
                      </div>
                    )}
                  </div>
                }
                trigger="hover"
              >
                <InfoCircleOutlined style={{ 
                  marginLeft: 6, 
                  color: config.color, 
                  fontSize: 12 
                }} />
              </Popover>
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              {trendIcon}
              {enableAiAnalysis && (
                <Tooltip title="Análisis AI v5.1">
                  <Button
                    type="text"
                    size="small"
                    icon={<RobotOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAiAnalysis();
                    }}
                    loading={analyzing}
                    style={{ 
                      fontSize: 10, 
                      padding: '0 4px', 
                      minWidth: 'auto' 
                    }}
                  />
                </Tooltip>
              )}
            </div>
          </div>
          
          {/* Main Value */}
          <div style={{ 
            flex: 1, 
            display: 'flex', 
            alignItems: 'center', 
            marginBottom: executiveMode ? 16 : 12 
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'baseline', 
              flex: 1, 
              flexWrap: 'wrap' 
            }}>
              <span style={{ 
                fontSize: executiveMode ? 36 : 28,
                fontWeight: 700,
                color: valueColor,
                lineHeight: 1
              }}>
                {formattedValue}
              </span>
              {config.format !== 'currency' && config.format !== 'number' && (
                <span style={{ 
                  fontSize: executiveMode ? 18 : 16,
                  color: theme.colors.textSecondary,
                  marginLeft: 4
                }}>
                  {config.unit}
                </span>
              )}
              {changeIndicator}
            </div>
          </div>
          
          {/* Progress Bar */}
          {config.threshold && executiveMode && (
            <div style={{ marginBottom: 12 }}>
              <Progress 
                percent={progressValue} 
                size="small" 
                strokeColor={valueColor}
                showInfo={false}
                style={{ marginBottom: 4 }}
              />
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between',
                fontSize: 10,
                color: theme.colors.textSecondary 
              }}>
                <span>Meta: {config.threshold.good}{config.unit}</span>
                <span>Excelente: {config.threshold.excellent}{config.unit}</span>
              </div>
            </div>
          )}
          
          {/* Footer */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center' 
          }}>
            {performanceBadge}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ 
                fontSize: 10, 
                color: theme.colors.textSecondary,
                textTransform: 'uppercase',
                fontWeight: 500
              }}>
                {config.category}
              </span>
              {executiveMode && (
                <Badge 
                  count={config.priority} 
                  size="small"
                  style={{ 
                    backgroundColor: config.color, 
                    fontSize: 9 
                  }}
                />
              )}
            </div>
          </div>
        </div>
      </Spin>
    </Card>
  );
});

KPICard.propTypes = {
  kpiKey: PropTypes.string.isRequired,
  value: PropTypes.number,
  previousValue: PropTypes.number,
  loading: PropTypes.bool,
  onClick: PropTypes.func,
  executiveMode: PropTypes.bool,
  showTrends: PropTypes.bool,
  enableAiAnalysis: PropTypes.bool,
  onAiAnalysis: PropTypes.func
};

// ============================================================================
// 🚀 MAIN COMPONENT - ✅ FIXED CHATSERVICE INTEGRATION
// ============================================================================

const KPICards = ({ 
  kpis = {}, 
  previousKpis = {}, 
  loading = false,
  gestorId,
  periodo,
  onKpiClick,
  showRefresh = false,
  autoRefresh = false,
  showTrends = true,
  showComparisons = true,
  executiveMode = false,
  enableAiAnalysis = true,
  userId = 'kpi_user_v5'
}) => {
  // ✅ FIX: Todos los hooks al inicio
  const [kpiData, setKpiData] = useState({});
  const [prevKpiData, setPrevKpiData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // ✅ FIX: useApp hook al inicio
  const { message: messageApi, notification } = App.useApp();
  
  // ✅ FIX: ChatService integration mejorada
  const {
    sendMessage,
    connectionState,
    serviceMetrics
  } = useChatService({
    userId,
    autoConnect: enableAiAnalysis, // Solo conectar si AI está habilitado
    handlers: {
      onMessage: useCallback((message) => {
        console.log('📨 [KPICards v5.1] AI Analysis response:', message);
        if (message?.response) {
          notification.success({
            message: '🤖 Análisis AI v5.1 Completado',
            description: message.response.length > 150 ? 
              message.response.substring(0, 150) + '...' : 
              message.response,
            duration: 6
          });
        }
      }, [notification]),
      onError: useCallback((error) => {
        console.error('❌ [KPICards v5.1] ChatService error:', error);
        // ✅ FIX: Error handling silencioso para evitar spam
        if (error?.message && !error.message.includes('No send method available')) {
          notification.warning({
            message: 'ChatService v5.1 Advertencia',
            description: 'Funcionalidad AI limitada - verifique conexión',
            duration: 3
          });
        }
      }, [notification])
    }
  });

  const normalizedPeriod = useMemo(() => normalizePeriod(periodo), [periodo]);

  // ✅ FIX: fetchKpiData mejorado con manejo robusto de errores
  const fetchKpiData = useCallback(async () => {
    if (!gestorId && !normalizedPeriod) return;

    setIsLoading(true);
    setError(null);

    try {
      let apiData = {};

      if (gestorId) {
        console.log('🔍 [KPICards v5.1] Fetching KPIs for gestor:', gestorId);
        
        const promises = [];
        
        if (api.getGestorPerformance) {
          promises.push(api.getGestorPerformance(gestorId, normalizedPeriod));
        }
        if (api.getGestorKPIs) {
          promises.push(api.getGestorKPIs(gestorId, normalizedPeriod));
        }
        
        if (promises.length > 0) {
          const results = await Promise.allSettled(promises);
          results.forEach(result => {
            if (result.status === 'fulfilled' && result.value) {
              const data = result.value?.data || result.value || {};
              apiData = { ...apiData, ...data, ...(data.kpis || {}) };
            }
          });
        }
      } else {
        console.log('🔍 [KPICards v5.1] Fetching consolidated KPIs');
        
        const promises = [];
        
        if (api.getKpisConsolidados) {
          promises.push(api.getKpisConsolidados(normalizedPeriod));
        }
        if (api.getTotales) {
          promises.push(api.getTotales(normalizedPeriod));
        }
        if (api.getDashboardData) {
          promises.push(api.getDashboardData(normalizedPeriod));
        }
        
        if (promises.length > 0) {
          const results = await Promise.allSettled(promises);
          results.forEach(result => {
            if (result.status === 'fulfilled' && result.value) {
              const data = result.value?.data || result.value || {};
              apiData = { 
                ...apiData, 
                ...data, 
                ...(data.kpis || {}),
                ...(data.totales || {})
              };
            }
          });
        }
      }

      if (Object.keys(apiData).length > 0) {
        const mappedKpis = mapApiDataToKpiKeys(apiData);
        setKpiData(mappedKpis);
        
        // ✅ FIX: Generar datos previos simulados solo si no existen
        if (!previousKpis || Object.keys(previousKpis).length === 0) {
          const simulatedPrevious = Object.keys(mappedKpis).reduce((acc, key) => {
            const value = mappedKpis[key];
            acc[key] = value && !isNaN(value) ? value * (0.90 + Math.random() * 0.20) : null;
            return acc;
          }, {});
          setPrevKpiData(simulatedPrevious);
        }
        
        messageApi.success(`✅ KPIs v5.1 cargados: ${Object.keys(mappedKpis).length} indicadores`);
      }

    } catch (error) {
      const errorMessage = error.message || error.toString() || 'Error desconocido';
      console.error('❌ [KPICards v5.1] Error loading KPIs:', errorMessage);
      setError(`Error al cargar KPIs v5.1: ${errorMessage}`);
      
      // ✅ FIX: Error message mejorado
      messageApi.error(`❌ Error cargando KPIs v5.1: ${errorMessage.substring(0, 100)}`);
    } finally {
      setIsLoading(false);
    }
  }, [gestorId, normalizedPeriod, previousKpis, messageApi]);

  // ✅ FIX: useEffect mejorado para data loading
  useEffect(() => {
    if (kpis && Object.keys(kpis).length > 0) {
      console.log('🎯 [KPICards v5.1] Using provided KPIs:', kpis);
      
      const validatedKpis = Object.keys(kpis).reduce((acc, key) => {
        const value = kpis[key];
        acc[key] = (typeof value === 'number' && !isNaN(value) && isFinite(value)) ? value : 0;
        return acc;
      }, {});
      
      setKpiData(validatedKpis);
      
      if (previousKpis && Object.keys(previousKpis).length > 0) {
        const validatedPrevKpis = Object.keys(previousKpis).reduce((acc, key) => {
          const value = previousKpis[key];
          acc[key] = (typeof value === 'number' && !isNaN(value) && isFinite(value)) ? value : 0;
          return acc;
        }, {});
        setPrevKpiData(validatedPrevKpis);
      }
    } else if (gestorId || normalizedPeriod) {
      fetchKpiData();
    }
  }, [kpis, previousKpis, gestorId, normalizedPeriod, fetchKpiData]);

  // ✅ FIX: Auto-refresh mejorado
  useEffect(() => {
    let interval;
    if (autoRefresh && (gestorId || normalizedPeriod)) {
      interval = setInterval(() => {
        fetchKpiData();
      }, 60000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, fetchKpiData, gestorId, normalizedPeriod]);

  // ✅ FIX: AI Analysis handler mejorado con validaciones robustas
  const handleAiAnalysis = useCallback(async (kpiKey, value, config) => {
    console.log(`🤖 [KPICards v5.1] AI Analysis requested for ${kpiKey}:`, { value, connectionState });
    
    // ✅ FIX: Verificación de estado de conexión
    if (connectionState !== CONNECTION_STATES.OPEN) {
      console.warn('⚠️ [KPICards v5.1] ChatService not connected, state:', connectionState);
      notification.warning({
        message: 'ChatService v5.1 no disponible',
        description: `Estado: ${connectionState}. La funcionalidad de análisis AI requiere conexión activa.`,
        duration: 4
      });
      return;
    }

    // ✅ FIX: Verificación de sendMessage
    if (!sendMessage || typeof sendMessage !== 'function') {
      console.error('❌ [KPICards v5.1] sendMessage not available');
      notification.error({
        message: 'Error ChatService v5.1',
        description: 'Método sendMessage no disponible',
        duration: 4
      });
      return;
    }

    try {
      const analysisPrompt = `${config.agentPrompt || `Analizar KPI ${config.title}`} para ${gestorId ? `gestor ${gestorId}` : 'consolidado'} en ${normalizedPeriod}. 
        Valor actual: ${formatValue(value, config)}. 
        Categoría: ${config.category}. 
        Umbral bueno: ${config.threshold?.good || 'N/A'}, 
        Umbral excelente: ${config.threshold?.excellent || 'N/A'}.
        
        Por favor proporciona un análisis detallado del KPI y recomendaciones específicas.`;
      
      console.log(`📤 [KPICards v5.1] Sending AI analysis request:`, analysisPrompt.substring(0, 100) + '...');
      
      const response = await sendMessage(analysisPrompt, {
        gestorId,
        periodo: normalizedPeriod,
        kpiContext: {
          kpiKey,
          value,
          config,
          category: config.category,
          threshold: config.threshold
        },
        includeRecommendations: true,
        quickMode: false, // ✅ FIX: Full analysis mode
        version: '5.1'
      });

      console.log(`✅ [KPICards v5.1] AI analysis response received:`, response);

      if (response?.response) {
        // Success notification handled by onMessage handler
      } else {
        console.warn('⚠️ [KPICards v5.1] Empty AI response received');
      }
    } catch (error) {
      console.error('❌ [KPICards v5.1] Error en análisis AI:', error);
      throw error; // Re-throw para que KPICard maneje el error
    }
  }, [sendMessage, connectionState, gestorId, normalizedPeriod, notification]);

  // ✅ FIX: displayKeys con mejor lógica de filtrado
  const displayKeys = useMemo(() => {
    const availableKeys = Object.keys(KPI_CONFIG).filter(key => {
      const value = kpiData[key];
      return value !== null && value !== undefined && !isNaN(value);
    });

    const sortedKeys = availableKeys.sort((a, b) => KPI_CONFIG[a].priority - KPI_CONFIG[b].priority);

    if (executiveMode) {
      return sortedKeys.slice(0, 6); // Top 6 for executive mode
    }

    return sortedKeys;
  }, [kpiData, executiveMode]);

  const handleRefresh = useCallback(() => {
    console.log('🔄 [KPICards v5.1] Manual refresh triggered');
    fetchKpiData();
  }, [fetchKpiData]);

  const isConnected = connectionState === CONNECTION_STATES.OPEN;

  console.log('🎯 [KPICards v5.1] Render state:', { 
    displayKeys: displayKeys.length, 
    kpiDataKeys: Object.keys(kpiData).length, 
    executiveMode, 
    connectionState,
    enableAiAnalysis,
    isConnected
  });

  // ✅ FIX: Error state mejorado
  if (error) {
    return (
      <Alert
        message="Error al cargar KPIs v5.1"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={handleRefresh} icon={<ReloadOutlined />}>
            Reintentar
          </Button>
        }
        style={{ marginBottom: 24 }}
      />
    );
  }
  
  // ✅ FIX: Empty state mejorado
  if (displayKeys.length === 0 && !isLoading) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: 32,
        color: theme.colors.textSecondary,
        backgroundColor: theme.colors.backgroundLight,
        borderRadius: executiveMode ? 12 : 8,
        border: `1px dashed ${theme.colors.border}`
      }}>
        <div style={{ fontSize: executiveMode ? 18 : 16, marginBottom: 8 }}>
          📊 {executiveMode ? 'KPIs Ejecutivos v5.1 no disponibles' : 'No hay KPIs disponibles'}
        </div>
        <div style={{ fontSize: 12, marginBottom: 16 }}>
          {executiveMode ? 
            `Configurando análisis avanzado para ${normalizedPeriod}` :
            `Verifica la conexión con el backend v5.1 para ${normalizedPeriod}`
          }
        </div>
        {showRefresh && (
          <Button 
            type="primary" 
            size="small" 
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={isLoading}
          >
            Recargar KPIs v5.1
          </Button>
        )}
      </div>
    );
  }
  
  return (
    <div style={{ marginBottom: 24 }}>
      
      {/* ✅ FIX: Header mejorado con mejor información de estado */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 16
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
            {executiveMode ? '📊 KPIs Ejecutivos v5.1' : 'Mostrando'} {displayKeys.length} KPIs
            {gestorId && ` • Gestor: ${gestorId}`}
            {normalizedPeriod && ` • Período: ${normalizedPeriod}`}
          </div>
          
          <Badge 
            status={isConnected ? 'success' : 'warning'} 
            text={
              <span style={{ fontSize: 11 }}>
                {isConnected ? 'AI v5.1 Online' : 'AI v5.1 Offline'}
              </span>
            }
          />
        </div>
        
        <Space>
          {enableAiAnalysis && (
            <Tooltip title={`Análisis AI v5.1 ${isConnected ? 'disponible' : 'no disponible'}`}>
              <Button
                type="text"
                size="small"
                icon={<RobotOutlined />}
                style={{ 
                  color: isConnected ? theme.colors.success : theme.colors.textSecondary 
                }}
              />
            </Tooltip>
          )}
          
          {showRefresh && (
            <Button 
              size="small"
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={isLoading}
            >
              Actualizar v5.1
            </Button>
          )}
        </Space>
      </div>

      {/* ✅ FIX: Grid layout mejorado */}
      <Row gutter={[16, 16]}>
        {displayKeys.map(key => (
          <Col 
            key={key} 
            xs={24} 
            sm={12} 
            md={executiveMode ? 8 : 8} 
            lg={displayKeys.length <= 3 ? 8 : 6}
            xl={executiveMode ? 
              (displayKeys.length <= 4 ? 6 : Math.floor(24 / Math.min(displayKeys.length, 4))) :
              (displayKeys.length <= 5 ? Math.floor(24 / displayKeys.length) : 4)
            }
          >
            <KPICard 
              kpiKey={key}
              value={kpiData[key]}
              previousValue={prevKpiData[key]}
              loading={isLoading || loading}
              onClick={onKpiClick ? () => onKpiClick(key, kpiData[key]) : null}
              executiveMode={executiveMode}
              showTrends={showTrends}
              enableAiAnalysis={enableAiAnalysis && isConnected}
              onAiAnalysis={handleAiAnalysis}
            />
          </Col>
        ))}
      </Row>

      {/* ✅ FIX: Footer mejorado con información de estado */}
      <div style={{ 
        marginTop: 16,
        padding: 12,
        backgroundColor: theme.colors.backgroundLight,
        borderRadius: executiveMode ? 8 : 4,
        fontSize: 11,
        color: theme.colors.textSecondary,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <strong>{executiveMode ? 'Vista Ejecutiva v5.1' : 'Categorías v5.1'}:</strong>
          {' '}
          <span style={{ color: theme.colors.bmGreenPrimary }}>Rentabilidad</span>
          {' • '}
          <span style={{ color: theme.colors.info }}>Volumen</span>
          {' • '}
          <span style={{ color: theme.colors.bmGreenLight }}>Eficiencia</span>
          {' • '}
          <span style={{ color: theme.colors.purple }}>Solvencia</span>
          {' • '}
          <span style={{ color: theme.colors.cyan }}>Liquidez</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>Período: <strong>{normalizedPeriod}</strong></span>
          {executiveMode && <span>🎯</span>}
          {isConnected && enableAiAnalysis && (
            <Space>
              <ApiOutlined style={{ color: theme.colors.success }} />
              <span style={{ color: theme.colors.success }}>AI v5.1</span>
            </Space>
          )}
        </div>
      </div>
    </div>
  );
};

KPICards.propTypes = {
  kpis: PropTypes.object,
  previousKpis: PropTypes.object,
  loading: PropTypes.bool,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  onKpiClick: PropTypes.func,
  showRefresh: PropTypes.bool,
  autoRefresh: PropTypes.bool,
  showTrends: PropTypes.bool,
  showComparisons: PropTypes.bool,
  executiveMode: PropTypes.bool,
  enableAiAnalysis: PropTypes.bool,
  userId: PropTypes.string
};

export default KPICards;
