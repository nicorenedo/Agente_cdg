// frontend/src/components/Dashboard/InteractiveCharts.jsx
/* eslint-disable no-console */

/**
 * InteractiveCharts v2.0.7 — FINAL FIX: Usa analyticsService correctamente
 * -----------------------------------------------------------------------
 * ✅ DIRECCIÓN: getDirectionChartData() ya devuelve {labels, datasets}
 * ✅ GESTOR: Usa funciones específicas de analyticsService
 * ✅ NO hay doble transformación
 * ✅ Código limpio y mantenible
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import PropTypes from 'prop-types';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Badge,
  Select,
  Tabs,
  Alert,
  Empty,
  Spin,
  App
} from 'antd';
import {
  ReloadOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  DollarCircleOutlined,
  TrophyOutlined,
  TeamOutlined,
  FundOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend
} from 'chart.js';
import { Bar, Doughnut, Line, Pie } from 'react-chartjs-2';

import analyticsService from '../../services/analyticsService';
import ErrorState from '../common/ErrorState';
import theme from '../../styles/theme';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

const { Text } = Typography;
const { Option } = Select;

/* =========================================
 * ✅ CONFIGURACIÓN DE GRÁFICOS POR ROL
 * ========================================= */

const DIRECTION_PRESET_CHARTS = {
  'gestores-ranking': {
    key: 'gestores-ranking',
    title: 'Top 10 Gestores',
    subtitle: 'Ranking por métrica seleccionada',
    icon: <TrophyOutlined />,
    defaultMetric: 'CONTRATOS',
    defaultChartType: 'horizontal_bar',
    availableMetrics: ['CONTRATOS', 'CLIENTES', 'INGRESOS', 'MARGEN_NETO', 'ROE'],
    availableChartTypes: ['horizontal_bar', 'bar', 'donut']
  },
  'centros-distribution': {
    key: 'centros-distribution',
    title: 'Distribución por Centros',
    subtitle: 'Análisis por centro operativo',
    icon: <FundOutlined />,
    defaultMetric: 'CONTRATOS',
    defaultChartType: 'donut',
    availableMetrics: ['CONTRATOS', 'CLIENTES', 'INGRESOS'],
    availableChartTypes: ['donut', 'pie', 'horizontal_bar']
  },
  'productos-popularity': {
    key: 'productos-popularity',
    title: 'Popularidad de Productos',
    subtitle: 'Contratos por tipo de producto',
    icon: <DollarCircleOutlined />,
    defaultMetric: 'CONTRATOS',
    defaultChartType: 'horizontal_bar',
    availableMetrics: ['CONTRATOS', 'INGRESOS'],
    availableChartTypes: ['horizontal_bar', 'bar', 'pie']
  }
};

const GESTOR_PRESET_CHARTS = {
  'margen-clientes': {
    key: 'margen-clientes',
    title: 'Top Clientes por Margen',
    subtitle: 'Mejores clientes del gestor',
    icon: <TeamOutlined />,
    defaultMetric: 'MARGEN_NETO',
    defaultChartType: 'horizontal_bar',
    availableMetrics: ['MARGEN_NETO'],
    availableChartTypes: ['horizontal_bar', 'bar', 'donut'],
    hasFilters: true,
    filterOptions: { limit: [5, 10, 15] }
  },
  'productos-clientes': {
    key: 'productos-clientes',
    title: 'Mix de Productos',
    subtitle: 'Distribución de productos contratados',
    icon: <PieChartOutlined />,
    defaultMetric: 'CONTRATOS',
    defaultChartType: 'donut',
    availableMetrics: ['CONTRATOS'],
    availableChartTypes: ['donut', 'pie', 'horizontal_bar'],
    hasFilters: true
  },
  'precios-comparison': {
    key: 'precios-comparison',
    title: 'Comparativa de Precios',
    subtitle: 'Precio estándar vs precio real',
    icon: <DollarCircleOutlined />,
    defaultMetric: 'PRECIO',
    defaultChartType: 'bar',
    availableMetrics: ['PRECIO'],
    availableChartTypes: ['bar', 'horizontal_bar'],
    hasFilters: true
  }
};

/* =========================================
 * ✅ UTILIDADES DE FORMATO
 * ========================================= */

const formatBankingValue = (value, metric) => {
  if (typeof value !== 'number' || isNaN(value)) return '0';

  const abs = Math.abs(value);
  const isCount = ['CONTRATOS', 'CLIENTES'].includes(metric);

  if (isCount) {
    return Math.round(abs).toLocaleString();
  }

  if (abs >= 1000000) {
    return `${(abs / 1000000).toFixed(1)}M€`;
  } else if (abs >= 1000) {
    return `${(abs / 1000).toFixed(1)}K€`;
  }
  return `${abs.toFixed(0)}€`;
};

const getMetricIcon = (metric) => {
  const icons = {
    CONTRATOS: <FundOutlined />,
    CLIENTES: <TeamOutlined />,
    INGRESOS: <DollarCircleOutlined />,
    GASTOS: <BarChartOutlined />,
    MARGEN_NETO: <LineChartOutlined />,
    ROE: <TrophyOutlined />,
    PRECIO: <DollarCircleOutlined />
  };
  return icons[metric] || <BarChartOutlined />;
};

/* =========================================
 * ✅ COMPONENTE PRINCIPAL
 * ========================================= */

const InteractiveCharts = ({
  mode = 'direccion',
  periodo = '2025-10',
  gestorId = null,
  filters = {},
  height = 400,
  onReload = () => {},
  onSelectEntity = () => {},
  externalChartData = null,
  onChartConfigChange = () => {},
  className = '',
  style = {}
}) => {
  
  const { notification } = App.useApp();

  /* Estados */
  const [activeTab, setActiveTab] = useState('preset1');
  const [chartsData, setChartsData] = useState({});
  const [loadingStates, setLoadingStates] = useState({});
  const [errorStates, setErrorStates] = useState({});
  const [chartConfigs, setChartConfigs] = useState({});
  const [dynamicChartData, setDynamicChartData] = useState(null);
  const [dynamicChartConfig, setDynamicChartConfig] = useState(null);

  const abortControllers = useRef({});
  const loadedCharts = useRef(new Set());

  /* Configuración según rol */
  const presetCharts = useMemo(() => {
    return mode === 'direccion' ? DIRECTION_PRESET_CHARTS : GESTOR_PRESET_CHARTS;
  }, [mode]);

  const presetKeys = useMemo(() => Object.keys(presetCharts), [presetCharts]);

  /* Inicializar configuraciones */
  useEffect(() => {
    const initialConfigs = {};
    Object.entries(presetCharts).forEach(([key, chart]) => {
      initialConfigs[key] = {
        metric: chart.defaultMetric || 'CONTRATOS',
        chartType: chart.defaultChartType || 'horizontal_bar',
        filters: { limit: 10 }
      };
    });
    setChartConfigs(initialConfigs);
  }, [presetCharts]);

  /* =========================================
   * ✅ CARGA DE DATOS v2.0.7 - SIN DOBLE TRANSFORMACIÓN
   * ========================================= */

  const loadChartData = useCallback(async (chartKey) => {
    const chart = presetCharts[chartKey];
    if (!chart) return;

    const config = chartConfigs[chartKey];
    if (!config) return;

    if (loadingStates[chartKey]) {
      console.log(`[InteractiveCharts] ⏭️ Skipping ${chartKey} - already loading`);
      return;
    }

    if (abortControllers.current[chartKey]) {
      abortControllers.current[chartKey].abort();
    }
    abortControllers.current[chartKey] = new AbortController();

    setLoadingStates(prev => ({ ...prev, [chartKey]: true }));
    setErrorStates(prev => ({ ...prev, [chartKey]: null }));

    try {
      console.log(`[InteractiveCharts] 🚀 Loading ${chartKey} with config:`, config);

      let chartData;

      // ✅ DIRECCIÓN: Usa getDirectionChartData() (YA DEVUELVE {labels, datasets})
      if (mode === 'direccion') {
        console.log(`[InteractiveCharts] 📊 Loading dirección chart: ${chartKey}`);
        
        chartData = await analyticsService.getDirectionChartData(chartKey, {
          metric: config.metric,
          chart_type: config.chartType,
          periodo,
          ...filters
        });
        
        // ✅ analyticsService YA devuelve {labels, datasets, meta}
        // NO necesitamos transformar
        console.log(`[InteractiveCharts] ✅ Received transformed data:`, {
          labels: chartData.labels?.length,
          datasets: chartData.datasets?.length
        });
      }
      // ✅ GESTOR: Usa funciones específicas de analyticsService
      else {
        console.log(`[InteractiveCharts] 📊 Loading gestor chart: ${chartKey}`);
        
        if (chartKey === 'margen-clientes') {
          // ✅ Usa función existente de analyticsService
          chartData = await analyticsService.getTopClientsChartData(gestorId, {
            periodo,
            limit: config.filters.limit || 10,
            ...filters
          });
          
        } else if (chartKey === 'productos-clientes') {
          // ✅ Usa función existente de analyticsService
          chartData = await analyticsService.getProductMixChartData(gestorId, {
            periodo,
            ...filters
          });
          
        } else if (chartKey === 'precios-comparison') {
          // ✅ Usa función existente de analyticsService
          chartData = await analyticsService.getPriceComparisonChartData({
            gestorId,
            periodo
          }, filters);
        }
      }

      // ✅ Validar que tenemos datos válidos
      if (!chartData || !chartData.labels || !chartData.datasets) {
        console.warn(`[InteractiveCharts] ⚠️ ${chartKey}: Invalid data format`);
        chartData = {
          labels: ['Sin datos'],
          datasets: [{
            label: 'N/A',
            data: [0],
            backgroundColor: ['#cccccc']
          }],
          meta: { error: 'No data available' }
        };
      }

      setChartsData(prev => ({ ...prev, [chartKey]: chartData }));
      loadedCharts.current.add(chartKey);
      console.log(`[InteractiveCharts] ✅ ${chartKey} loaded:`, chartData.labels?.length, 'items');

    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error(`[InteractiveCharts] ❌ Error loading ${chartKey}:`, error);
        setErrorStates(prev => ({ ...prev, [chartKey]: error }));
        
        notification.error({
          message: `Error cargando ${chart.title}`,
          description: error.message,
          duration: 3
        });
      }
    } finally {
      setLoadingStates(prev => ({ ...prev, [chartKey]: false }));
    }
  }, [
    presetCharts,
    chartConfigs,
    mode,
    gestorId,
    periodo,
    filters,
    notification,
    loadingStates
  ]);

  /* Cargar todos los gráficos */
  const loadAllCharts = useCallback(() => {
    if (!periodo) return;
    if (mode === 'gestor' && !gestorId) return;

    console.log('[InteractiveCharts] 🔄 Loading all preset charts');

    presetKeys.forEach(key => {
      if (!loadedCharts.current.has(key)) {
        loadChartData(key);
      } else {
        console.log(`[InteractiveCharts] ✅ ${key} already loaded`);
      }
    });
  }, [periodo, mode, gestorId, presetKeys, loadChartData]);

  useEffect(() => {
    let mounted = true;
    
    const loadTimeout = setTimeout(() => {
      if (mounted) {
        loadAllCharts();
      }
    }, 100);

    return () => {
      mounted = false;
      clearTimeout(loadTimeout);
      
      Object.values(abortControllers.current).forEach(controller => {
        try {
          controller.abort();
        } catch (e) {}
      });
      abortControllers.current = {};
    };
  }, [periodo, mode, gestorId]);

  /* Manejo de datos externos */
  useEffect(() => {
    if (externalChartData) {
      console.log('[InteractiveCharts] 📥 Received external chart data:', externalChartData);

      setDynamicChartData(externalChartData);
      setDynamicChartConfig({
        metric: externalChartData.meta?.metric,
        dimension: externalChartData.meta?.dimension,
        chartType: externalChartData.meta?.chartType || 'horizontal_bar'
      });

      setActiveTab('dynamic');
    }
  }, [externalChartData]);

  /* Handlers */
  const handleConfigChange = useCallback((chartKey, configType, value) => {
    setChartConfigs(prev => ({
      ...prev,
      [chartKey]: {
        ...prev[chartKey],
        [configType]: value
      }
    }));

    loadedCharts.current.delete(chartKey);
    setTimeout(() => loadChartData(chartKey), 100);
  }, [loadChartData]);

  const handleRefreshAll = useCallback(() => {
    console.log('[InteractiveCharts] 🔄 Refreshing all charts');
    analyticsService.clearAnalyticsCache();
    loadedCharts.current.clear();
    
    presetKeys.forEach(key => {
      loadChartData(key);
    });

    onReload();
  }, [presetKeys, loadChartData, onReload]);

  const handleDataPointClick = useCallback((data, chartKey) => {
    console.log('[InteractiveCharts] 🖱️ Data point clicked:', data);
    onSelectEntity({ ...data, chartKey, mode });
  }, [onSelectEntity, mode]);

  /* Renderizado de gráficos */
  const renderChart = (data, config, chartKey) => {
    if (!data || !data.labels || !data.datasets) {
      return (
        <Empty
          description="No hay datos disponibles"
          image={<BarChartOutlined style={{ fontSize: 48, opacity: 0.3 }} />}
        />
      );
    }

    const commonOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            usePointStyle: true,
            color: theme.colors?.textPrimary || '#333',
            font: { size: 12, family: 'Inter, sans-serif' }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: theme.colors?.bmGreenPrimary || '#1b5e55',
          borderWidth: 1,
          callbacks: {
            label: (context) => {
              const value = context.parsed.y || context.parsed.x || context.parsed;
              return ` ${context.dataset.label}: ${formatBankingValue(value, config.metric)}`;
            }
          }
        }
      },
      onClick: (event, elements) => {
        if (elements.length > 0 && onSelectEntity) {
          const index = elements[0].index;
          handleDataPointClick({
            label: data.labels[index],
            value: data.datasets[0].data[index],
            index
          }, chartKey);
        }
      }
    };

    const scaleOptions = {
      grid: { color: 'rgba(0,0,0,0.1)' },
      ticks: {
        color: theme.colors?.textSecondary || '#666',
        font: { size: 11 },
        callback: function(value) {
          return formatBankingValue(value, config.metric);
        }
      }
    };

    switch (config.chartType) {
      case 'horizontal_bar':
        return (
          <Bar
            data={data}
            options={{
              ...commonOptions,
              indexAxis: 'y',
              scales: {
                x: { ...scaleOptions, beginAtZero: true },
                y: { 
                  grid: { display: false }, 
                  ticks: { 
                    color: '#333',
                    font: { size: 11 }
                  } 
                }
              }
            }}
            height={height}
          />
        );

      case 'bar':
        return (
          <Bar
            data={data}
            options={{
              ...commonOptions,
              scales: {
                y: { ...scaleOptions, beginAtZero: true },
                x: { 
                  grid: { display: false }, 
                  ticks: { 
                    ...scaleOptions.ticks, 
                    maxRotation: 45
                  } 
                }
              }
            }}
            height={height}
          />
        );

      case 'donut':
        return (
          <Doughnut
            data={data}
            options={{
              ...commonOptions,
              cutout: '60%',
              plugins: {
                ...commonOptions.plugins,
                legend: { ...commonOptions.plugins.legend, position: 'right' },
                tooltip: {
                  ...commonOptions.plugins.tooltip,
                  callbacks: {
                    label: (context) => {
                      const value = context.parsed;
                      const total = context.dataset.data.reduce((a, b) => a + b, 0);
                      const pct = ((value / total) * 100).toFixed(1);
                      return ` ${context.label}: ${pct}% (${formatBankingValue(value, config.metric)})`;
                    }
                  }
                }
              }
            }}
            height={height}
          />
        );

      case 'pie':
        return (
          <Pie
            data={data}
            options={{
              ...commonOptions,
              plugins: {
                ...commonOptions.plugins,
                legend: { ...commonOptions.plugins.legend, position: 'right' }
              }
            }}
            height={height}
          />
        );

      case 'line':
        return (
          <Line
            data={data}
            options={{
              ...commonOptions,
              scales: {
                y: { ...scaleOptions, beginAtZero: true },
                x: { grid: { display: false }, ticks: { ...scaleOptions.ticks } }
              }
            }}
            height={height}
          />
        );

      default:
        return (
          <Bar data={data} options={commonOptions} height={height} />
        );
    }
  };

  const renderChartCard = (chartKey) => {
    const chart = presetCharts[chartKey];
    const config = chartConfigs[chartKey] || {};
    const data = chartsData[chartKey];
    const loading = loadingStates[chartKey];
    const error = errorStates[chartKey];

    return (
      <Card
        key={chartKey}
        title={
          <Space>
            {chart.icon}
            <div>
              <div style={{ fontWeight: 600 }}>{chart.title}</div>
              <Text type="secondary" style={{ fontSize: 12 }}>{chart.subtitle}</Text>
            </div>
          </Space>
        }
        extra={
          <Space>
            {chart.availableMetrics && chart.availableMetrics.length > 1 && (
              <Select
                size="small"
                value={config.metric}
                onChange={(value) => handleConfigChange(chartKey, 'metric', value)}
                style={{ width: 120 }}
              >
                {chart.availableMetrics.map(metric => (
                  <Option key={metric} value={metric}>
                    <Space>{getMetricIcon(metric)} {metric}</Space>
                  </Option>
                ))}
              </Select>
            )}

            {chart.availableChartTypes && chart.availableChartTypes.length > 1 && (
              <Select
                size="small"
                value={config.chartType}
                onChange={(value) => handleConfigChange(chartKey, 'chartType', value)}
                style={{ width: 100 }}
              >
                {chart.availableChartTypes.map(type => (
                  <Option key={type} value={type}>{type}</Option>
                ))}
              </Select>
            )}

            <Button
              size="small"
              icon={<ReloadOutlined />}
              loading={loading}
              onClick={() => {
                loadedCharts.current.delete(chartKey);
                loadChartData(chartKey);
              }}
            />
          </Space>
        }
        style={{
          height: height + 80,
          boxShadow: '0 2px 8px rgba(27, 94, 85, 0.1)',
          borderRadius: 8
        }}
        styles={{ body: { height, padding: 16 } }}
      >
        {loading && (
          <div style={{ height, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Spin size="large" tip="Cargando datos..." />
          </div>
        )}

        {error && !loading && (
          <ErrorState
            error={error}
            onRetry={() => {
              loadedCharts.current.delete(chartKey);
              loadChartData(chartKey);
            }}
            style={{ height }}
          />
        )}

        {!loading && !error && renderChart(data, config, chartKey)}
      </Card>
    );
  };

  /* Tabs */
  const tabItems = [
    ...presetKeys.slice(0, 3).map((key, idx) => ({
      key: `preset${idx + 1}`,
      label: presetCharts[key].title,
      children: renderChartCard(key)
    })),
    {
      key: 'dynamic',
      label: (
        <Space>
          <LineChartOutlined />
          Gráfico Dinámico
          {dynamicChartData && <Badge count="Nuevo" size="small" />}
        </Space>
      ),
      children: dynamicChartData ? (
        <Card
          title={
            <Space>
              <LineChartOutlined />
              Gráfico generado por lenguaje natural
            </Space>
          }
          extra={
            <Button
              size="small"
              onClick={() => {
                setDynamicChartData(null);
                setDynamicChartConfig(null);
                setActiveTab('preset1');
              }}
            >
              Limpiar
            </Button>
          }
          style={{ height: height + 80 }}
          styles={{ body: { height, padding: 16 } }}
        >
          {renderChart(dynamicChartData, dynamicChartConfig, 'dynamic')}
        </Card>
      ) : (
        <Card style={{ height: height + 80 }}>
          <Empty
            description="No hay gráfico dinámico. Usa ConversationalPivot para generar uno."
            image={<InfoCircleOutlined style={{ fontSize: 48, opacity: 0.3 }} />}
          />
        </Card>
      )
    }
  ];

  /* Render principal */
  return (
    <div className={`interactive-charts ${className}`} style={style}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space>
            <BarChartOutlined style={{ fontSize: 24, color: theme.colors?.bmGreenPrimary }} />
            <div>
              <Text style={{ fontSize: 18, fontWeight: 600 }}>
                Dashboard {mode === 'direccion' ? 'de Dirección' : 'del Gestor'}
              </Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>
                Perfect Integration v11.0 • Período: {periodo}
                {mode === 'gestor' && gestorId && ` • Gestor: ${gestorId}`}
              </Text>
            </div>
          </Space>
        </Col>
        <Col>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefreshAll}
            loading={Object.values(loadingStates).some(Boolean)}
          >
            Actualizar Todo
          </Button>
        </Col>
      </Row>

      <Alert
        message={
          mode === 'direccion'
            ? '✅ Acceso Completo: Puedes ver todos los gestores, centros y segmentos'
            : '🔒 Acceso Limitado: Solo puedes ver tus clientes, productos y precios'
        }
        type={mode === 'direccion' ? 'success' : 'info'}
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        items={tabItems}
      />
    </div>
  );
};

InteractiveCharts.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.string.isRequired,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  filters: PropTypes.object,
  height: PropTypes.number,
  onReload: PropTypes.func,
  onSelectEntity: PropTypes.func,
  externalChartData: PropTypes.object,
  onChartConfigChange: PropTypes.func,
  className: PropTypes.string,
  style: PropTypes.object
};

const InteractiveChartsWithApp = (props) => (
  <App>
    <InteractiveCharts {...props} />
  </App>
);

export default React.memo(InteractiveChartsWithApp);
