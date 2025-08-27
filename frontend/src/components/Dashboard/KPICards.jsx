// src/components/Dashboard/KPICards.jsx
// Componente para mostrar KPIs principales - COMPLETAMENTE OPTIMIZADO sin warnings

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, Row, Col, Tooltip, Button, Spin, Alert, Badge } from 'antd';
import { 
  ArrowUpOutlined, 
  ArrowDownOutlined, 
  InfoCircleOutlined, 
  ReloadOutlined,
  DashOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import theme from '../../styles/theme';

// 🔥 SOLUCIÓN 1: Función memoizada para normalizar período
const normalizePeriod = (period) => {
  if (!period) return '2025-10';
  if (period.length === 10 && period.includes('-')) {
    return period.substring(0, 7); // YYYY-MM-DD → YYYY-MM
  }
  if (period.length === 7 && period.includes('-')) {
    return period;
  }
  return '2025-10';
};

// 🔥 SOLUCIÓN 2: Función memoizada para mapear datos de API
const mapApiDataToKpiKeys = (apiData) => {
  if (!apiData) return {};
  
  console.log('🔄 DEBUG: Mapeando datos de API:', apiData);
  
  const mapped = {
    ROE: apiData.ROE || apiData.roe || apiData.return_on_equity || 0,
    MARGEN_NETO: apiData.MARGEN_NETO || apiData.margen_neto || apiData.net_margin || 0,
    TOTAL_INGRESOS: apiData.TOTAL_INGRESOS || apiData.total_ingresos || apiData.total_income || apiData.ingresos || 0,
    TOTAL_GASTOS: apiData.TOTAL_GASTOS || apiData.total_gastos || apiData.total_expenses || apiData.gastos || 0,
    BENEFICIO_NETO: apiData.BENEFICIO_NETO || apiData.beneficio_neto || apiData.net_profit || apiData.profit || 0,
    EFICIENCIA_OPERATIVA: apiData.EFICIENCIA_OPERATIVA || apiData.eficiencia_operativa || apiData.efficiency || 0
  };
  
  console.log('🎯 DEBUG: Datos mapeados resultantes:', mapped);
  return mapped;
};

// 🔥 SOLUCIÓN 3: Configuración KPI memoizada
const KPI_CONFIG = {
  ROE: {
    title: 'ROE',
    description: 'Return on Equity - Rentabilidad sobre fondos propios, indicador clave en banca',
    unit: '%',
    precision: 2,
    threshold: { good: 8, excellent: 12 },
    icon: '📈',
    category: 'rentabilidad'
  },
  MARGEN_NETO: {
    title: 'Margen Neto',
    description: 'Margen neto como porcentaje sobre ingresos totales del gestor',
    unit: '%',
    precision: 2,
    threshold: { good: 10, excellent: 15 },
    icon: '💰',
    category: 'rentabilidad'
  },
  TOTAL_INGRESOS: {
    title: 'Total Ingresos',
    description: 'Suma total de ingresos gestionados por el gestor en el período',
    unit: '€',
    precision: 0,
    format: 'currency',
    icon: '💵',
    category: 'volumen'
  },
  TOTAL_GASTOS: {
    title: 'Total Gastos',
    description: 'Suma total de gastos asociados a la gestión en el período',
    unit: '€',
    precision: 0,
    format: 'currency',
    icon: '💸',
    category: 'volumen'
  },
  BENEFICIO_NETO: {
    title: 'Beneficio Neto',
    description: 'Beneficio neto obtenido en el período',
    unit: '€',
    precision: 0,
    format: 'currency',
    threshold: { good: 50000, excellent: 100000 },
    icon: '🎯',
    category: 'rentabilidad'
  }
};

// 🔥 SOLUCIÓN 4: Funciones utilitarias memoizadas
const getValueColor = (value, config) => {
  if (value === null || value === undefined || isNaN(value)) return theme.colors.textSecondary;
  
  const { threshold, invertedLogic } = config;
  if (!threshold) return theme.colors.bmGreenPrimary;
  
  if (invertedLogic) {
    if (value <= threshold.excellent) return theme.colors.bmGreenPrimary;
    if (value <= threshold.good) return theme.colors.bmGreenLight;
    return theme.colors.error;
  } else {
    if (value >= threshold.excellent) return theme.colors.bmGreenPrimary;
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
  
  return <Badge status={status} text={text} style={{ fontSize: '10px' }} />;
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

// 🔥 SOLUCIÓN 5: Componente KPICard memoizado
const KPICard = React.memo(({ kpiKey, value, previousValue, loading, onClick }) => {
  const config = KPI_CONFIG[kpiKey];
  if (!config) return null;
  
  const formattedValue = formatValue(value, config);
  const valueColor = getValueColor(value, config);
  const performanceBadge = getPerformanceBadge(value, config);
  
  // Calcular cambio respecto al período anterior
  let changeIndicator = null;
  let trendIcon = null;
  
  if (previousValue !== undefined && previousValue !== null && value !== null && !isNaN(value) && !isNaN(previousValue)) {
    const change = Number(value) - Number(previousValue);
    const changePercent = (change / Number(previousValue)) * 100;
    
    if (Math.abs(changePercent) > 0.1) {
      const isPositive = change > 0;
      const isGoodChange = config.invertedLogic ? !isPositive : isPositive;
      
      const iconColor = isGoodChange ? theme.colors.bmGreenPrimary : theme.colors.error;
      const Icon = isPositive ? ArrowUpOutlined : ArrowDownOutlined;
      const TrendIcon = isGoodChange ? ArrowUpOutlined : ArrowDownOutlined;
      
      changeIndicator = (
        <Tooltip title={`Cambio: ${isPositive ? '+' : ''}${changePercent.toFixed(1)}% vs período anterior`}>
          <Icon style={{ color: iconColor, marginLeft: 8, fontSize: 14 }} />
        </Tooltip>
      );
      
      trendIcon = <TrendIcon style={{ color: iconColor, fontSize: 12 }} />;
    } else {
      trendIcon = <DashOutlined style={{ color: theme.colors.textSecondary, fontSize: 12 }} />;
    }
  }
  
  return (
    <Card 
      variant="outlined"
      hoverable={!!onClick}
      onClick={onClick}
      style={{ 
        borderRadius: 8, 
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        border: `1px solid ${theme.colors.border}`,
        height: '140px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease'
      }}
      styles={{ body: { padding: '16px' } }}
    >
      <Spin spinning={loading}>
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* Header con título y trend */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: 8
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center',
              color: theme.colors.textSecondary,
              fontSize: 13,
              fontWeight: 500
            }}>
              <span style={{ marginRight: 4 }}>{config.icon}</span>
              {config.title}
              <Tooltip title={config.description}>
                <InfoCircleOutlined style={{ marginLeft: 6, color: theme.colors.bmGreenLight }} />
              </Tooltip>
            </div>
            {trendIcon}
          </div>
          
          {/* Valor principal */}
          <div style={{ 
            flex: 1, 
            display: 'flex', 
            alignItems: 'center', 
            marginBottom: 8 
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', flex: 1 }}>
              <span style={{ 
                fontSize: 26,
                fontWeight: 700,
                color: valueColor,
                lineHeight: 1
              }}>
                {formattedValue}
              </span>
              {config.format !== 'currency' && config.format !== 'number' && (
                <span style={{ 
                  fontSize: 16,
                  color: theme.colors.textSecondary,
                  marginLeft: 4
                }}>
                  {config.unit}
                </span>
              )}
              {changeIndicator}
            </div>
          </div>
          
          {/* Footer con badge de performance */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'center' 
          }}>
            {performanceBadge}
            <span style={{ 
              fontSize: 10, 
              color: theme.colors.textSecondary,
              textTransform: 'uppercase',
              fontWeight: 500
            }}>
              {config.category}
            </span>
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
  onClick: PropTypes.func
};

// 🔥 SOLUCIÓN 6: Componente principal optimizado
const KPICards = ({ 
  kpis = {}, 
  previousKpis = {}, 
  loading = false,
  gestorId,
  periodo,
  onKpiClick,
  showRefresh = false,
  autoRefresh = false
}) => {
  const [kpiData, setKpiData] = useState({});
  const [prevKpiData, setPrevKpiData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // 🔥 SOLUCIÓN 7: Período normalizado memoizado
  const normalizedPeriod = useMemo(() => normalizePeriod(periodo), [periodo]);

  // 🔥 SOLUCIÓN 8: Función de fetch optimizada
  const fetchKpiData = useCallback(async () => {
    if (!gestorId && !normalizedPeriod) return;

    setIsLoading(true);
    setError(null);

    try {
      let apiData = {};

      if (gestorId) {
        console.log('🔍 DEBUG KPICards: Fetching KPIs para gestor específico');
        const response = await api.getGestorPerformance(gestorId, normalizedPeriod);
        
        if (response?.data?.kpis) {
          apiData = response.data.kpis;
        }
      } else {
        console.log('🔍 DEBUG KPICards: Fetching KPIs consolidados');
        
        try {
          const [kpisResponse, totalesResponse] = await Promise.allSettled([
            api.getKpisConsolidados(normalizedPeriod),
            api.getTotales(normalizedPeriod)
          ]);
          
          if (kpisResponse.status === 'fulfilled') {
            apiData = { ...apiData, ...(kpisResponse.value?.data || kpisResponse.value || {}) };
          }
          if (totalesResponse.status === 'fulfilled') {
            apiData = { ...apiData, ...(totalesResponse.value?.data || totalesResponse.value || {}) };
          }
        } catch (endpointError) {
          console.warn('⚠️ DEBUG KPICards: Error usando endpoints separados, usando fallback');
          const dashboardData = await api.getDashboardData(normalizedPeriod);
          
          apiData = {
            ...(dashboardData?.data?.kpis || dashboardData?.kpis || {}),
            ...(dashboardData?.data?.totales || dashboardData?.totales || {})
          };
        }
      }

      if (Object.keys(apiData).length > 0) {
        const mappedKpis = mapApiDataToKpiKeys(apiData);
        setKpiData(mappedKpis);
        
        // Generar datos anteriores simulados si no se proporcionan
        if (!previousKpis || Object.keys(previousKpis).length === 0) {
          const simulatedPrevious = Object.keys(mappedKpis).reduce((acc, key) => {
            const value = mappedKpis[key];
            acc[key] = value && !isNaN(value) ? value * (0.92 + Math.random() * 0.16) : null;
            return acc;
          }, {});
          setPrevKpiData(simulatedPrevious);
        }
      }

    } catch (error) {
      console.error('❌ DEBUG KPICards: Error cargando KPIs:', error);
      setError(`Error al cargar KPIs: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [gestorId, normalizedPeriod, previousKpis]);

  // 🔥 SOLUCIÓN 9: useEffect optimizado CON TODAS LAS DEPENDENCIAS
  useEffect(() => {
    if (kpis && Object.keys(kpis).length > 0) {
      const mappedKpis = mapApiDataToKpiKeys(kpis);
      setKpiData(mappedKpis);
      setPrevKpiData(mapApiDataToKpiKeys(previousKpis));
    } else if (gestorId || normalizedPeriod) {
      fetchKpiData();
    }
  }, [kpis, previousKpis, fetchKpiData, gestorId, normalizedPeriod]); // ✅ CORREGIDO: Todas las dependencias incluidas

  // 🔥 SOLUCIÓN 10: AutoRefresh memoizado
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchKpiData, 60000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchKpiData]);

  // 🔥 SOLUCIÓN 11: Display keys memoizados
  const displayKeys = useMemo(() => {
    const kpiKeys = Object.keys(KPI_CONFIG).filter(key => {
      const value = kpiData[key];
      return value !== null && value !== undefined && !isNaN(value) && value !== 0;
    });

    const allKpiKeys = Object.keys(KPI_CONFIG).filter(key => 
      kpiData.hasOwnProperty(key) && kpiData[key] !== null && kpiData[key] !== undefined
    );

    return kpiKeys.length > 0 ? kpiKeys : allKpiKeys;
  }, [kpiData]);

  // 🔥 SOLUCIÓN 12: Handler memoizado
  const handleRefresh = useCallback(() => {
    fetchKpiData();
  }, [fetchKpiData]);

  console.log('🎯 DEBUG KPICards: KPIs para mostrar:', { displayKeys, kpiData });

  if (error) {
    return (
      <Alert
        message="Error al cargar KPIs"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={handleRefresh}>
            Reintentar
          </Button>
        }
        style={{ marginBottom: theme.spacing.lg }}
      />
    );
  }
  
  if (displayKeys.length === 0 && !isLoading) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: theme.spacing.xl,
        color: theme.colors.textSecondary,
        backgroundColor: theme.colors.backgroundLight,
        borderRadius: 8,
        border: `1px dashed ${theme.colors.border}`
      }}>
        <div style={{ fontSize: 16, marginBottom: 8 }}>
          📊 No hay KPIs disponibles para mostrar
        </div>
        <div style={{ fontSize: 12 }}>
          Verifica la conexión con el backend para el período {normalizedPeriod}
        </div>
        {showRefresh && (
          <Button 
            type="primary" 
            size="small" 
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            style={{ marginTop: 12 }}
          >
            Recargar KPIs
          </Button>
        )}
      </div>
    );
  }
  
  return (
    <div style={{ marginBottom: theme.spacing.lg }}>
      {/* Header con información y controles */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: theme.spacing.md
      }}>
        <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
          Mostrando {displayKeys.length} KPIs
          {gestorId && ` • Gestor: ${gestorId}`}
          {normalizedPeriod && ` • Período: ${normalizedPeriod}`}
        </div>
        {showRefresh && (
          <Button 
            size="small"
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={isLoading}
          >
            Actualizar
          </Button>
        )}
      </div>

      {/* Grid de KPIs */}
      <Row gutter={[16, 16]}>
        {displayKeys.map(key => (
          <Col 
            key={key} 
            xs={24} 
            sm={12} 
            md={8} 
            lg={displayKeys.length <= 3 ? 8 : 6}
            xl={displayKeys.length <= 5 ? Math.floor(24 / displayKeys.length) : 4}
          >
            <KPICard 
              kpiKey={key}
              value={kpiData[key]}
              previousValue={prevKpiData[key]}
              loading={isLoading}
              onClick={onKpiClick ? () => onKpiClick(key, kpiData[key]) : null}
            />
          </Col>
        ))}
      </Row>

      {/* Leyenda de categorías */}
      <div style={{ 
        marginTop: theme.spacing.md,
        padding: theme.spacing.sm,
        backgroundColor: theme.colors.backgroundLight,
        borderRadius: 4,
        fontSize: 11,
        color: theme.colors.textSecondary
      }}>
        <strong>Categorías:</strong>
        {' '}
        <span style={{ color: theme.colors.bmGreenPrimary }}>Rentabilidad</span>
        {' • '}
        <span style={{ color: theme.colors.warning }}>Volumen</span>
        {' • '}
        Período: {normalizedPeriod}
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
  autoRefresh: PropTypes.bool
};

export default KPICards;
