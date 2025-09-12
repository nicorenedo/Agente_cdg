// frontend/src/components/Dashboard/InteractiveCharts.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Tooltip, 
  Space, 
  Typography, 
  Badge,
  FloatButton,
  Empty,
  Select,
  Flex,
  Tabs,
  Alert
} from 'antd';
import {
  ReloadOutlined, 
  BarChartOutlined, 
  TrophyOutlined, 
  PieChartOutlined,
  DollarCircleOutlined,
  SettingOutlined,
  FilterOutlined,
  LineChartOutlined,
  FundOutlined,
  TeamOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import analyticsService from '../../services/analyticsService';
import ErrorState from '../common/ErrorState';
import Loader from '../common/Loader';
import theme from '../../styles/theme';

// Chart.js imports
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
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, ChartTooltip, Legend);

const { Text } = Typography;
const { Option } = Select;

// Mantener todas las constantes y validaciones existentes
const VALID_COMBINATIONS_DIRECCION = {
  CONTRATOS: ['productos', 'gestores', 'centros', 'segmentos'],
  CLIENTES: ['productos', 'gestores', 'centros', 'segmentos'], 
  MARGEN: ['productos', 'gestores', 'centros', 'segmentos'],
  INGRESOS: ['productos', 'gestores', 'centros', 'segmentos'],
  GASTOS: ['productos', 'gestores', 'centros', 'segmentos']
};

const VALID_COMBINATIONS_GESTOR = {
  CONTRATOS: ['clientes', 'productos'],
  CLIENTES: ['productos'],
  MARGEN: ['productos', 'clientes'],
  INGRESOS: ['productos', 'clientes'],
  GASTOS: ['productos', 'clientes']
};

const COUNT_METRICS = ['CONTRATOS', 'CLIENTES'];
const CURRENCY_METRICS = ['MARGEN', 'INGRESOS', 'GASTOS'];

const formatBankingValue = (value, options = {}) => {
  const { showCurrency = true, decimals = 0, isPrice = false, metric = '' } = options;
  if (typeof value !== 'number') return { displayValue: '0', isNegative: false };
  
  const abs = Math.abs(value);
  const isCount = COUNT_METRICS.includes(metric?.toUpperCase());
  
  let display = '';
  
  if (isCount) {
    display = Math.round(abs).toString();
  } else if (isPrice) {
    display = abs.toFixed(decimals);
  } else if (abs >= 1000000) {
    display = (abs / 1000000).toFixed(decimals) + 'M';
  } else if (abs >= 1000) {
    display = (abs / 1000).toFixed(decimals) + 'K';
  } else {
    display = abs.toFixed(decimals);
  }
  
  return { 
    displayValue: (showCurrency && !isCount) ? display + '€' : display, 
    isNegative: value < 0, 
    originalValue: value, 
    numericValue: abs 
  };
};

const isValidCombination = (metric, dimension, mode) => {
  if (!metric || !dimension) return false;
  
  const validCombinations = mode === 'gestor' 
    ? VALID_COMBINATIONS_GESTOR 
    : VALID_COMBINATIONS_DIRECCION;
  
  return validCombinations[metric]?.includes(dimension) || false;
};

const getSemaphoreColor = (semaforo) => {
  const colors = {
    'Verde': '#22c55e',
    'Amarillo': '#f59e0b', 
    'Rojo': '#ef4444',
    'Gris': '#6b7280'
  };
  return colors[semaforo] || colors.Gris;
};

const validateDataset = (dataset, context = '') => {
  if (!dataset) {
    return { valid: false, isEmpty: false, isLoading: true };
  }
  
  if (dataset.labels && Array.isArray(dataset.labels) && dataset.datasets && Array.isArray(dataset.datasets)) {
    const hasData = dataset.labels.length > 0 && 
                   dataset.datasets.some(ds => ds.data && ds.data.some(val => val !== null && val !== undefined && val !== 0));
    
    if (!hasData) {
      return { valid: true, isEmpty: true, isLoading: false };
    }
    return { valid: true, isEmpty: false, isLoading: false };
  }
  
  return { valid: false, isEmpty: true, isLoading: false };
};

/**
 * ChartFilter - Filtros dinámicos embebidos FUNCIONANDO CORRECTAMENTE
 */
const ChartFilter = ({ 
  chartKey, 
  mode, 
  currentMetric, 
  currentChartType, 
  currentDimension,
  onMetricChange, 
  onChartTypeChange, 
  onDimensionChange,
  style = {},
  availableMetrics = []
}) => {
  
  const metricOptions = useMemo(() => {
    if (chartKey === 'unified') {
      if (mode === 'direccion') {
        return [
          { value: 'CONTRATOS', label: 'Contratos', icon: <FundOutlined /> },
          { value: 'CLIENTES', label: 'Clientes', icon: <TeamOutlined /> },
          { value: 'INGRESOS', label: 'Ingresos', icon: <DollarCircleOutlined /> },
          { value: 'MARGEN', label: 'Margen', icon: <LineChartOutlined /> }
        ];
      } else {
        return [
          { value: 'CONTRATOS', label: 'Contratos', icon: <FundOutlined /> },
          { value: 'MARGEN', label: 'Margen', icon: <LineChartOutlined /> },
          { value: 'CLIENTES', label: 'Clientes', icon: <TeamOutlined /> }
        ];
      }
    }
    return availableMetrics.length > 0 ? availableMetrics : [
      { value: currentMetric, label: currentMetric }
    ];
  }, [mode, chartKey, availableMetrics, currentMetric]);

  const chartTypeOptions = useMemo(() => {
    if (chartKey === 'priceComparison') {
      return [
        { value: 'comparison', label: 'Comparación', icon: <BarChartOutlined /> },
        { value: 'horizontal_bar', label: 'Barras H.', icon: <BarChartOutlined /> },
        { value: 'line', label: 'Líneas', icon: <LineChartOutlined /> }
      ];
    } else if (chartKey === 'unified') {
      return [
        { value: 'horizontal_bar', label: 'Barras H.', icon: <BarChartOutlined /> },
        { value: 'bar', label: 'Barras V.', icon: <BarChartOutlined /> },
        { value: 'donut', label: 'Donut', icon: <PieChartOutlined /> },
        { value: 'line', label: 'Líneas', icon: <LineChartOutlined /> }
      ];
    }
    return [
      { value: 'horizontal_bar', label: 'Barras H.' },
      { value: 'bar', label: 'Barras V.' },
      { value: 'donut', label: 'Donut' }
    ];
  }, [chartKey]);

  const dimensionOptions = useMemo(() => {
    let baseDimensions = [];
    
    if (chartKey === 'unified') {
      if (mode === 'direccion') {
        baseDimensions = [
          { value: 'gestores', label: 'Gestores', icon: <TeamOutlined /> },
          { value: 'centros', label: 'Centros', icon: <FundOutlined /> },
          { value: 'productos', label: 'Productos', icon: <DollarCircleOutlined /> },
          { value: 'segmentos', label: 'Segmentos', icon: <FundOutlined /> }
        ];
      } else if (mode === 'gestor') {
        baseDimensions = [
          { value: 'clientes', label: 'Clientes', icon: <TeamOutlined /> },
          { value: 'productos', label: 'Productos', icon: <FundOutlined /> }
        ];
      }
    }
    
    return baseDimensions.filter(dim => 
      isValidCombination(currentMetric, dim.value, mode)
    );
  }, [mode, chartKey, currentMetric]);

  const effectiveDimension = useMemo(() => {
    if (dimensionOptions.some(opt => opt.value === currentDimension)) {
      return currentDimension;
    }
    return dimensionOptions[0]?.value || '';
  }, [currentDimension, dimensionOptions]);

  React.useEffect(() => {
    if (currentDimension !== effectiveDimension && effectiveDimension && onDimensionChange) {
      console.log(`[ChartFilter] Auto-adjusting dimension from ${currentDimension} to ${effectiveDimension} for metric ${currentMetric}`);
      onDimensionChange(effectiveDimension);
    }
  }, [currentDimension, effectiveDimension, currentMetric, onDimensionChange]);

  return (
    <Flex gap={8} wrap="wrap" style={{ marginBottom: 12, ...style }}>
      {metricOptions.length > 1 && (
        <Select
          size="small"
          value={currentMetric}
          onChange={onMetricChange}
          style={{ minWidth: 120 }}
          placeholder="Métrica"
        >
          {metricOptions.map(opt => (
            <Option key={opt.value} value={opt.value}>
              <Space>
                {opt.icon}
                {opt.label}
              </Space>
            </Option>
          ))}
        </Select>
      )}

      {dimensionOptions.length > 0 && (
        <Select
          size="small"
          value={effectiveDimension}
          onChange={onDimensionChange}
          style={{ minWidth: 110 }}
          placeholder="Dimensión"
        >
          {dimensionOptions.map(opt => (
            <Option key={opt.value} value={opt.value}>
              <Space>
                {opt.icon}
                {opt.label}
              </Space>
            </Option>
          ))}
        </Select>
      )}
      
      <Select
        size="small"
        value={currentChartType}
        onChange={onChartTypeChange}
        style={{ minWidth: 110 }}
        placeholder="Tipo"
      >
        {chartTypeOptions.map(opt => (
          <Option key={opt.value} value={opt.value}>
            <Space>
              {opt.icon}
              {opt.label}
            </Space>
          </Option>
        ))}
      </Select>
    </Flex>
  );
};

/**
 * PriceComparisonChart - Componente especializado para precios ACTUALIZADO
 */
const PriceComparisonChart = ({ data, height = 280, onDataClick }) => {
  const validation = validateDataset(data, 'priceComparison');
  
  if (validation.isLoading) {
    return (
      <div style={{ height, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Loader size="large" />
      </div>
    );
  }
  
  if (!validation.valid || validation.isEmpty || !data.table) {
    return (
      <div style={{ height, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Empty 
          image={<DollarCircleOutlined style={{ fontSize: 48, color: '#999', opacity: 0.3 }} />}
          description="No hay datos de precios disponibles"
        />
      </div>
    );
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        display: true,
        labels: {
          usePointStyle: true,
          padding: 20,
          color: theme.colors?.textPrimary || '#333',
          font: { size: 12 }
        }
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0,0,0,0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: theme.colors?.bmGreenPrimary || '#1890ff',
        borderWidth: 1,
        cornerRadius: 6,
        callbacks: {
          title: (context) => context[0].label || '',
          label: (context) => {
            const value = context.parsed.y || context.parsed;
            const formatted = formatBankingValue(Math.abs(value), { 
              decimals: 0, 
              isPrice: true,
              showCurrency: true
            });
            return ` ${context.dataset.label}: ${formatted.displayValue}`;
          },
          afterBody: (context) => {
            if (data.table && context[0]) {
              const item = data.table[context[0].dataIndex];
              if (item) {
                const delta = item.delta_pct || 0;
                const semaforo = item.semaforo || 'Gris';
                return [`Δ: ${delta.toFixed(2)}%`, `Estado: ${semaforo}`];
              }
            }
            return [];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false },
        ticks: {
          color: theme.colors?.textSecondary || '#666',
          font: { size: 11 },
          callback: function(value) {
            return formatBankingValue(Math.abs(value), { 
              decimals: 0, 
              isPrice: true,
              showCurrency: true
            }).displayValue;
          }
        }
      },
      x: {
        grid: { display: false },
        ticks: {
          color: theme.colors?.textPrimary || '#333',
          font: { size: 11, weight: '500' },
          maxRotation: 45,
          callback: function(value, index) {
            const label = this.getLabelForValue(value);
            // TRUNCAR etiquetas largas para evitar cortes
            return label.length > 15 ? label.substring(0, 12) + '...' : label;
          }
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0 && onDataClick && data.table) {
        const clickedElement = elements[0];
        const dataIndex = clickedElement.dataIndex;
        const item = data.table[dataIndex];
        onDataClick({
          index: dataIndex,
          item,
          chartKey: 'priceComparison'
        });
      }
    }
  };

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      <Bar data={data} options={chartOptions} height={height} />
      
      {data.meta?.semaforos && (
        <div style={{ 
          marginTop: 12, 
          padding: '8px 12px', 
          backgroundColor: '#f8f9fa', 
          borderRadius: 6,
          fontSize: 12
        }}>
          <Space split={<span style={{ color: '#d9d9d9' }}>•</span>}>
            <span style={{ color: getSemaphoreColor('Verde') }}>
              ✓ Verde: {data.meta.semaforos.Verde || 0}
            </span>
            <span style={{ color: getSemaphoreColor('Amarillo') }}>
              ⚠ Amarillo: {data.meta.semaforos.Amarillo || 0}
            </span>
            <span style={{ color: getSemaphoreColor('Rojo') }}>
              ✗ Rojo: {data.meta.semaforos.Rojo || 0}
            </span>
          </Space>
        </div>
      )}
    </div>
  );
};

/**
 * UnifiedChart - Gráfico principal unificado y dinámico
 */
const UnifiedChart = ({ data, config = {}, height = 280, onDataClick }) => {
  const { chartType = 'horizontal_bar', metric = 'CONTRATOS' } = config;
  
  const validation = validateDataset(data, 'unified');
  
  if (validation.isLoading) {
    return (
      <div style={{ height, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Loader size="large" />
        <Text type="secondary" style={{ marginTop: 16 }}>
          Cargando datos dinámicos...
        </Text>
      </div>
    );
  }
  
  if (!validation.valid || validation.isEmpty) {
    return (
      <div style={{ height, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Empty 
          image={<BarChartOutlined style={{ fontSize: 48, color: '#999', opacity: 0.3 }} />}
          description={
            <div style={{ textAlign: 'center' }}>
              <Text type="secondary">No hay datos para la métrica seleccionada</Text>
              <br />
              <Text type="secondary" style={{ fontSize: 11 }}>
                Prueba cambiar la métrica o dimensión
              </Text>
            </div>
          }
        />
      </div>
    );
  }

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        display: true,
        labels: {
          usePointStyle: true,
          padding: 20,
          color: theme.colors?.textPrimary || '#333',
          font: { size: 12 }
        }
      },
      tooltip: {
        enabled: true,
        backgroundColor: 'rgba(0,0,0,0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: theme.colors?.bmGreenPrimary || '#1890ff',
        borderWidth: 1,
        cornerRadius: 6,
        callbacks: {
          title: (context) => context[0].label || '',
          label: (context) => {
            const value = context.parsed.y || context.parsed;
            const formatted = formatBankingValue(Math.abs(value), { 
              decimals: COUNT_METRICS.includes(metric) ? 0 : 2,
              metric: metric
            });
            return ` ${context.dataset.label || metric}: ${formatted.displayValue}`;
          }
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0 && onDataClick) {
        const clickedElement = elements[0];
        const dataIndex = clickedElement.index;
        onDataClick({
          index: dataIndex,
          value: data.datasets[0].data[dataIndex],
          label: data.labels[dataIndex],
          chartKey: 'unified',
          metric,
          chartType
        });
      }
    }
  };

  const renderChart = () => {
    switch (chartType) {
      case 'horizontal_bar':
        return (
          <Bar 
            data={data} 
            options={{
              ...commonOptions,
              indexAxis: 'y',
              scales: {
                x: {
                  beginAtZero: true,
                  grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false },
                  ticks: {
                    color: theme.colors?.textSecondary || '#666',
                    font: { size: 11 },
                    callback: function(value) {
                      return formatBankingValue(value, { 
                        decimals: 0, 
                        metric: metric
                      }).displayValue;
                    }
                  }
                },
                y: {
                  grid: { display: false },
                  ticks: {
                    color: theme.colors?.textPrimary || '#333',
                    font: { size: 12, weight: '500' },
                    maxRotation: 0,
                    callback: function(value, index) {
                      const label = this.getLabelForValue(value);
                      return label.length > 15 ? label.substring(0, 12) + '...' : label;
                    }
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
                y: {
                  beginAtZero: true,
                  grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false },
                  ticks: {
                    color: theme.colors?.textSecondary || '#666',
                    font: { size: 11 },
                    callback: function(value) {
                      return formatBankingValue(Math.abs(value), { 
                        decimals: 0, 
                        metric: metric
                      }).displayValue;
                    }
                  }
                },
                x: {
                  grid: { display: false },
                  ticks: {
                    color: theme.colors?.textPrimary || '#333',
                    font: { size: 12, weight: '500' },
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
                legend: {
                  ...commonOptions.plugins.legend,
                  position: 'right',
                  align: 'center'
                },
                tooltip: {
                  ...commonOptions.plugins.tooltip,
                  callbacks: {
                    ...commonOptions.plugins.tooltip.callbacks,
                    label: (context) => {
                      const value = context.parsed;
                      const total = context.dataset.data.reduce((a, b) => a + b, 0);
                      const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                      const formatted = formatBankingValue(value, { 
                        decimals: 0,
                        metric: metric
                      });
                      return ` ${context.label}: ${percentage}% (${formatted.displayValue})`;
                    }
                  }
                }
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
                y: {
                  beginAtZero: true,
                  grid: { color: 'rgba(0,0,0,0.1)', drawBorder: false },
                  ticks: {
                    color: theme.colors?.textSecondary || '#666',
                    font: { size: 11 },
                    callback: function(value) {
                      return formatBankingValue(Math.abs(value), { 
                        decimals: 0, 
                        metric: metric
                      }).displayValue;
                    }
                  }
                },
                x: {
                  grid: { display: false },
                  ticks: {
                    color: theme.colors?.textPrimary || '#333',
                    font: { size: 12, weight: '500' },
                    maxRotation: 45
                  }
                }
              }
            }}
            height={height}
          />
        );
        
      default:
        return (
          <Bar 
            data={data} 
            options={commonOptions}
            height={height}
          />
        );
    }
  };

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      {renderChart()}
      
      {data.meta && (
        <div style={{ 
          position: 'absolute',
          top: 8,
          right: 8,
          padding: '4px 8px',
          backgroundColor: 'rgba(255,255,255,0.9)',
          borderRadius: 4,
          fontSize: 11,
          color: theme.colors?.textSecondary || '#666',
          border: `1px solid ${theme.colors?.borderLight || '#e8e8e8'}`
        }}>
          {data.meta.mockData ? 'Datos de prueba' : `${data.meta.showing || 0} elementos`}
        </div>
      )}
    </div>
  );
};

/**
 * InteractiveCharts - Componente principal CON GRÁFICO DE PRECIOS PARA DIRECCIÓN
 */
const InteractiveCharts = ({
  mode = 'direccion',
  periodo,
  gestorId = null,
  metric = 'CONTRATOS',
  chartType = null,
  filters = {},
  height = 380,
  onReload = () => {},
  onSelectEntity = () => {},
  externalChartConfig = null,
  onChartConfigChange = null,
  onChartUpdate = () => {},
  onChartPivot = () => {},
  className = '',
  style = {}
}) => {
  
  const normalizedPeriodo = useMemo(() => {
    if (!periodo) return '2025-10';
    if (typeof periodo === 'string') return periodo;
    if (typeof periodo === 'object') {
      return periodo.latest || periodo.value || periodo.periodo || '2025-10';
    }
    return String(periodo);
  }, [periodo]);

  const normalizedGestorId = useMemo(() => {
    if (!gestorId) return null;
    return parseInt(gestorId, 10);
  }, [gestorId]);

  const normalizedMetric = useMemo(() => metric ? metric.toUpperCase() : 'CONTRATOS', [metric]);

  const [unifiedConfig, setUnifiedConfig] = useState({
    metric: normalizedMetric,
    chartType: chartType || 'horizontal_bar',
    dimension: mode === 'direccion' ? 'gestores' : 'clientes'
  });

  const [priceConfig, setPriceConfig] = useState({
    chartType: 'comparison',
    showTable: true
  });

  // NUEVO: Estado para selector de segmentos en dashboard dirección
  const [selectedSegment, setSelectedSegment] = useState('N10101');
  const segmentos = [
    { id: 'N10101', nombre: 'Banca Minorista' },
    { id: 'N10102', nombre: 'Banca Privada' },
    { id: 'N10103', nombre: 'Banca de Empresas' },
    { id: 'N10104', nombre: 'Banca Personal' },
    { id: 'N20301', nombre: 'Fondos' }
  ];

  const [chartsData, setChartsData] = useState({});
  const [loadingStates, setLoadingStates] = useState({});
  const [errorStates, setErrorStates] = useState({});
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [activeTab, setActiveTab] = useState('unified');

  const abortControllers = useRef({});
  const lastLoadKey = useRef(null);

  const cleanupAbortController = useCallback((key) => {
    if (abortControllers.current[key]) {
      try {
        abortControllers.current[key].abort();
      } catch (e) {
        console.warn(`[${key}] Error aborting controller:`, e);
      }
      delete abortControllers.current[key];
    }
  }, []);

  const loadChartData = useCallback(async (chartKey, loaderFn, shouldLoad = true) => {
    if (!shouldLoad) return;

    if (chartKey === 'unified' && !isValidCombination(unifiedConfig.metric, unifiedConfig.dimension, mode)) {
      console.warn(`[${chartKey}] Invalid combination: ${unifiedConfig.metric}-${unifiedConfig.dimension} for mode ${mode}`);
      setErrorStates(prev => ({ 
        ...prev, 
        [chartKey]: new Error(`Combinación no válida: ${unifiedConfig.metric} por ${unifiedConfig.dimension}`)
      }));
      setLoadingStates(prev => ({ ...prev, [chartKey]: false }));
      return;
    }

    cleanupAbortController(chartKey);
    abortControllers.current[chartKey] = new AbortController();
    
    console.log(`[${chartKey}] 🚀 Loading data...`);
    setLoadingStates(prev => ({ ...prev, [chartKey]: true }));
    setErrorStates(prev => ({ ...prev, [chartKey]: null }));
    
    try {
      const result = await loaderFn();
      
      if (!abortControllers.current[chartKey]?.signal.aborted) {
        console.log(`[${chartKey}] ✅ Data loaded successfully`);
        setChartsData(prev => ({ ...prev, [chartKey]: result }));
      }
      
    } catch (error) {
      if (error.name !== 'AbortError' && !abortControllers.current[chartKey]?.signal.aborted) {
        console.error(`[${chartKey}] ❌ Error loading data:`, error);
        setErrorStates(prev => ({ ...prev, [chartKey]: error }));
      }
    } finally {
      if (!abortControllers.current[chartKey]?.signal.aborted) {
        setLoadingStates(prev => ({ ...prev, [chartKey]: false }));
      }
    }
  }, [cleanupAbortController, unifiedConfig, mode]);

  const loadUnifiedData = useCallback(async () => {
    const config = unifiedConfig;
    
    if (mode === 'direccion') {
      const chartTypeMap = {
        'gestores': 'gestores-ranking',
        'centros': 'centros-distribution', 
        'productos': 'productos-popularity',
        'segmentos': 'segmentos-overview'
      };
      
      const chartType = chartTypeMap[config.dimension] || 'gestores-ranking';
      
      return await analyticsService.getDirectionChartData(chartType, {
        metric: config.metric,
        chart_type: config.chartType,
        periodo: normalizedPeriodo,
        dimension: config.dimension,
        ...filters
      });
    } else if (normalizedGestorId) {
      if (config.dimension === 'clientes') {
        return await analyticsService.getTopClientsChartData(normalizedGestorId, { 
          limit: 10,
          ...filters
        });
      } else if (config.dimension === 'productos') {
        return await analyticsService.getProductMixChartData(normalizedGestorId, {
          ...filters
        });
      }
    }
    return null;
  }, [mode, normalizedGestorId, normalizedPeriodo, filters, unifiedConfig]);

  // FUNCIÓN CORREGIDA: loadPriceData para dirección CON FILTRO DE SEGMENTO y gestor CON FILTROS
  const loadPriceData = useCallback(async () => {
    if (mode === 'direccion') {
      // Dashboard de dirección: CON FILTRO DE SEGMENTO SELECCIONADO
      console.log(`[InteractiveCharts] 🎯 Loading price data for DIRECTION mode (segment: ${selectedSegment})`);
      return await analyticsService.getPriceComparisonChartData({
        periodo: normalizedPeriodo,
        segment_id: selectedSegment, // NUEVO: Filtrar por segmento seleccionado
        ...filters
      });
    } else if (normalizedGestorId) {
      // Dashboard de gestor: CON FILTROS (su segmento específico)
      console.log(`[InteractiveCharts] 🎯 Loading price data for GESTOR mode (gestor ${normalizedGestorId})`);
      return await analyticsService.getPriceComparisonChartData({
        gestor_id: normalizedGestorId,
        periodo: normalizedPeriodo,
        ...filters
      });
    }
    return null;
  }, [mode, normalizedGestorId, normalizedPeriodo, filters, selectedSegment]);

  // ✅ EFECTO PRINCIPAL PARA RECARGAR PRECIOS AL CAMBIAR SEGMENTO (SIN EL HOOK DENTRO DE RENDER)
  useEffect(() => {
    if (mode === 'direccion' && selectedSegment) {
      loadChartData('priceComparison', loadPriceData, true);
    }
  }, [mode, selectedSegment, loadChartData, loadPriceData]);

  const dependencyKey = useMemo(() => 
    JSON.stringify({
      mode,
      gestorId: normalizedGestorId,
      periodo: normalizedPeriodo,
      unifiedConfig,
      priceConfig,
      filters
    }), 
    [mode, normalizedGestorId, normalizedPeriodo, unifiedConfig, priceConfig, filters]
  );

  useEffect(() => {
    if (lastLoadKey.current === dependencyKey) {
      console.log('[InteractiveCharts] 🔄 Dependencies unchanged, skipping reload');
      return;
    }

    if (!normalizedPeriodo) {
      console.log('[InteractiveCharts] ⚠️ No periodo provided');
      return;
    }

    if (mode === 'gestor' && !normalizedGestorId) {
      console.log('[InteractiveCharts] ⚠️ Gestor mode requires gestorId');
      return;
    }

    lastLoadKey.current = dependencyKey;
    console.log('[InteractiveCharts] 🚀 Loading all charts with new dependencies');

    setChartsData({});
    setErrorStates({});

    // Cargar ambos gráficos en paralelo - INCLUIR PRECIOS EN AMBOS MODOS
    const loadPromises = [
      loadChartData('unified', loadUnifiedData, true),
      loadChartData('priceComparison', loadPriceData, true) // SIEMPRE cargar precios
    ];

    Promise.allSettled(loadPromises).then(() => {
      console.log('[InteractiveCharts] ✅ All charts loading completed');
    });

    return () => {
      console.log('[InteractiveCharts] 🧹 Cleanup: Aborting all requests');
      Object.keys(abortControllers.current).forEach(key => {
        cleanupAbortController(key);
      });
    };

  }, [
    dependencyKey,
    normalizedPeriodo,
    mode,
    normalizedGestorId,
    loadChartData,
    loadUnifiedData,
    loadPriceData,
    cleanupAbortController
  ]);

  const handleUnifiedConfigChange = useCallback((configType, value) => {
    console.log(`[InteractiveCharts] 🔧 Unified config change: ${configType} = ${value}`);
    
    setUnifiedConfig(prev => {
      const newConfig = { ...prev, [configType]: value };
      
      if (configType === 'metric') {
        if (!isValidCombination(value, newConfig.dimension, mode)) {
          const validCombinations = mode === 'gestor' 
            ? VALID_COMBINATIONS_GESTOR 
            : VALID_COMBINATIONS_DIRECCION;
          const validDimensions = validCombinations[value] || [];
          
          if (validDimensions.length > 0) {
            const fallbackDimension = mode === 'direccion' 
              ? (validDimensions.includes('gestores') ? 'gestores' : validDimensions[0])
              : (validDimensions.includes('clientes') ? 'clientes' : validDimensions[0]);
            newConfig.dimension = fallbackDimension;
            console.log(`[InteractiveCharts] Auto-adjusted dimension to ${fallbackDimension} for metric ${value} in mode ${mode}`);
          }
        }
      }
      
      return newConfig;
    });

    if (onChartConfigChange) {
      onChartConfigChange({ chartKey: 'unified', configType, value });
    }
  }, [onChartConfigChange, mode]);

  const handlePriceConfigChange = useCallback((configType, value) => {
    console.log(`[InteractiveCharts] 🔧 Price config change: ${configType} = ${value}`);
    
    setPriceConfig(prev => ({
      ...prev,
      [configType]: value
    }));

    if (onChartConfigChange) {
      onChartConfigChange({ chartKey: 'priceComparison', configType, value });
    }
  }, [onChartConfigChange]);

  const handleDataPointClick = useCallback((entity, chartKey) => {
    setSelectedEntity({ ...entity, chartKey });
    if (onSelectEntity) {
      onSelectEntity({ ...entity, chartKey, mode, periodo: normalizedPeriodo });
    }
  }, [onSelectEntity, mode, normalizedPeriodo]);

  const handleRefreshChart = useCallback((chartKey) => {
    console.log(`[InteractiveCharts] 🔄 Refreshing chart: ${chartKey}`);
    
    const loaderMap = {
      'unified': loadUnifiedData,
      'priceComparison': loadPriceData
    };

    const loader = loaderMap[chartKey];
    if (loader) {
      loadChartData(chartKey, loader, true);
    }
    
    if (onReload) onReload();
  }, [loadUnifiedData, loadPriceData, loadChartData, onReload]);

  const handleRefreshAll = useCallback(() => {
    console.log('[InteractiveCharts] 🔄 Refreshing all charts');
    
    lastLoadKey.current = null;
    
    if (analyticsService.clearAnalyticsCache) {
      analyticsService.clearAnalyticsCache();
    }
    
    setChartsData({});
    setErrorStates({});
    
    if (onReload) onReload();
  }, [onReload]);

  const renderUnifiedTab = () => {
    const data = chartsData.unified;
    const loading = loadingStates.unified;
    const error = errorStates.unified;

    return (
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <BarChartOutlined style={{ 
              backgroundColor: `${theme.colors?.bmGreenPrimary || '#1890ff'}15`, 
              color: theme.colors?.bmGreenPrimary || '#1890ff', 
              fontSize: 18, 
              padding: 8, 
              borderRadius: 6 
            }} />
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontWeight: 600, 
                fontSize: 16, 
                color: theme.colors?.textPrimary || '#333',
                marginBottom: 2
              }}>
                Análisis General Dinámico
                {loading && (
                  <Badge 
                    count="Cargando..." 
                    style={{ 
                      backgroundColor: theme.colors?.info || '#13c2c2',
                      marginLeft: 8,
                      fontSize: 10
                    }} 
                  />
                )}
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {mode === 'direccion' 
                  ? `Vista corporativa • ${unifiedConfig.metric} por ${unifiedConfig.dimension}`
                  : `Vista personal • ${unifiedConfig.metric} por ${unifiedConfig.dimension}`}
                <span style={{ marginLeft: 8, fontWeight: 500 }}>
                  ({COUNT_METRICS.includes(unifiedConfig.metric) ? 'Unidades' : 'Euros'})
                </span>
              </Text>
            </div>
          </div>
        }
        extra={
          <Space>
            <Tooltip title="Actualizar datos">
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={loading}
                onClick={() => handleRefreshChart('unified')}
                style={{
                  borderColor: theme.colors?.bmGreenPrimary || '#1890ff',
                  color: theme.colors?.bmGreenPrimary || '#1890ff'
                }}
              />
            </Tooltip>
          </Space>
        }
        style={{
          height: height + 100,
          borderRadius: theme.token?.borderRadius || 8,
          boxShadow: '0 4px 12px rgba(27, 94, 85, 0.12)',
          border: `1px solid ${theme.colors?.borderLight || '#e8e8e8'}`
        }}
        styles={{
          body: {
            height: height,
            padding: '16px 20px',
            overflow: 'hidden'
          }
        }}
      >
        <ChartFilter
          chartKey="unified"
          mode={mode}
          currentMetric={unifiedConfig.metric}
          currentChartType={unifiedConfig.chartType}
          currentDimension={unifiedConfig.dimension}
          onMetricChange={(value) => handleUnifiedConfigChange('metric', value)}
          onChartTypeChange={(value) => handleUnifiedConfigChange('chartType', value)}
          onDimensionChange={(value) => handleUnifiedConfigChange('dimension', value)}
        />
        
        {error && !loading && (
          <ErrorState
            error={error}
            onRetry={() => handleRefreshChart('unified')}
            style={{ height: height - 80 }}
          />
        )}
        
        {!error && (
          <UnifiedChart
            key={`unified-${normalizedGestorId || 'default'}-${unifiedConfig.chartType}-${unifiedConfig.metric}-${unifiedConfig.dimension}`}
            data={data}
            config={unifiedConfig}
            height={height - 80}
            onDataClick={(entity) => handleDataPointClick(entity, 'unified')}
          />
        )}
      </Card>
    );
  };

  // ✅ RENDERIZADO DE TAB DE PRECIOS CON SELECTOR DE SEGMENTOS Y ETIQUETAS CORREGIDAS (SIN useEffect DENTRO)
  const renderPriceTab = () => {
    const data = chartsData.priceComparison;
    const loading = loadingStates.priceComparison;
    const error = errorStates.priceComparison;

    const handleSegmentChange = (value) => {
      setSelectedSegment(value);
    };

    return (
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <DollarCircleOutlined style={{ 
              backgroundColor: `${theme.colors?.warning || '#faad14'}15`, 
              color: theme.colors?.warning || '#faad14', 
              fontSize: 18, 
              padding: 8, 
              borderRadius: 6 
            }} />
            <div style={{ flex: 1 }}>
              <div style={{ 
                fontWeight: 600, 
                fontSize: 16, 
                color: theme.colors?.textPrimary || '#333',
                marginBottom: 2
              }}>
                Precios: Real vs Estándar
                {loading && (
                  <Badge 
                    count="Cargando..." 
                    style={{ 
                      backgroundColor: theme.colors?.info || '#13c2c2',
                      marginLeft: 8,
                      fontSize: 10
                    }} 
                  />
                )}
              </div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {mode === 'direccion' 
                  ? `✅ Filtrado por segmento: ${segmentos.find(s => s.id === selectedSegment)?.nombre || 'Desconocido'}`
                  : `Segmento específico • Gestor ${normalizedGestorId} • Semáforo automático`}
                {data?.meta?.segmentoNombre && ` • ${data.meta.segmentoNombre}`}
              </Text>
                
              {/* ✅ SELECTOR DE SEGMENTOS SOLO PARA DIRECCIÓN */}
              {mode === 'direccion' && (
                <div style={{ marginTop: 8 }}>
                  <Select
                    size="small"
                    value={selectedSegment}
                    onChange={handleSegmentChange}
                    style={{ minWidth: 180 }}
                    placeholder="Seleccionar segmento"
                  >
                    {segmentos.map(segmento => (
                      <Option key={segmento.id} value={segmento.id}>
                        {segmento.nombre}
                      </Option>
                    ))}
                  </Select>
                </div>
              )}
            </div>
          </div>
        }
        extra={
          <Space>
            <Tooltip title="Actualizar precios">
              <Button
                size="small"
                icon={<ReloadOutlined />}
                loading={loading}
                onClick={() => handleRefreshChart('priceComparison')}
                style={{
                  borderColor: theme.colors?.warning || '#faad14',
                  color: theme.colors?.warning || '#faad14'
                }}
              />
            </Tooltip>
          </Space>
        }
        style={{
          height: height + 100,
          borderRadius: theme.token?.borderRadius || 8,
          boxShadow: '0 4px 12px rgba(27, 94, 85, 0.12)',
          border: `1px solid ${theme.colors?.borderLight || '#e8e8e8'}`
        }}
        styles={{
          body: {
            height: height,
            padding: '16px 20px',
            overflow: 'hidden'
          }
        }}
      >
        {/* SOLO mostrar filtros en modo GESTOR */}
        {mode === 'gestor' && (
          <ChartFilter
            chartKey="priceComparison"
            mode={mode}
            currentChartType={priceConfig.chartType}
            onChartTypeChange={(value) => handlePriceConfigChange('chartType', value)}
            style={{ marginBottom: 16 }}
          />
        )}

        {mode === 'direccion' && (
          <Alert
            message="Vista por Segmento"
            description={`Mostrando precios del segmento ${segmentos.find(s => s.id === selectedSegment)?.nombre}. Usa el selector arriba para cambiar de segmento.`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {error && !loading && (
          <ErrorState
            error={error}
            onRetry={() => handleRefreshChart('priceComparison')}
            style={{ height: height - 80 }}
          />
        )}

        {!error && (
          <PriceComparisonChart
            key={`price-${normalizedGestorId || selectedSegment}-${priceConfig.chartType}`}
            data={data}
            height={height - 80}
            onDataClick={(entity) => handleDataPointClick(entity, 'priceComparison')}
          />
        )}
      </Card>
    );
  };

  const tabItems = [
    {
      key: 'unified',
      label: (
        <Space>
          <BarChartOutlined />
          Análisis General
        </Space>
      ),
      children: renderUnifiedTab()
    },
    {
      key: 'prices', 
      label: (
        <Space>
          <DollarCircleOutlined />
          Precios por Productos
        </Space>
      ),
      children: renderPriceTab()
    }
  ];

  return (
    <div className={`interactive-charts ${className}`} style={{ ...style, width: '100%' }}>
      {/* Header mejorado */}
      <div style={{ marginBottom: theme.spacing?.lg || 24 }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'flex-start', 
          marginBottom: theme.spacing?.md || 16
        }}>
          <div>
            <Text style={{ 
              fontWeight: 600, 
              fontSize: 20, 
              color: theme.colors?.bmGreenPrimary || '#1890ff', 
              display: 'flex', 
              alignItems: 'center', 
              gap: 12 
            }}>
              <BarChartOutlined style={{ 
                padding: 10, 
                backgroundColor: `${theme.colors?.bmGreenPrimary || '#1890ff'}15`, 
                borderRadius: 8, 
                fontSize: 20 
              }} />
              Dashboard Interactivo Unificado
              <Badge 
                count={mode === 'gestor' ? 'Gestor' : 'Dirección'} 
                style={{ 
                  backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff',
                  marginLeft: 4
                }} 
              />
            </Text>
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 13 }}>
                {mode === 'direccion' 
                  ? `Dashboard corporativo • Período: ${normalizedPeriodo} • ✅ SELECTOR DE SEGMENTOS`
                  : `Panel personalizado • Período: ${normalizedPeriodo} • Precios filtrados por segmento`}
                {mode === 'gestor' && normalizedGestorId && ` • Gestor: ${normalizedGestorId}`}
                {Object.keys(filters).length > 0 && ' • Con filtros aplicados'}
              </Text>
            </div>
          </div>
          
          <Space>
            <Button 
              icon={<SettingOutlined />}
              style={{ 
                borderColor: theme.colors?.bmGreenPrimary || '#1890ff',
                color: theme.colors?.bmGreenPrimary || '#1890ff'
              }}
            >
              Configurar
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={handleRefreshAll}
              loading={Object.values(loadingStates).some(Boolean)}
              style={{ 
                borderColor: theme.colors?.bmGreenPrimary || '#1890ff',
                color: theme.colors?.bmGreenPrimary || '#1890ff'
              }}
            >
              Actualizar Todo
            </Button>
          </Space>
        </div>

        <Alert
          message="✅ Gráfico de Precios con Selector de Segmentos"
          description={`Los gráficos muestran unidades apropiadas (contratos en números, margen en euros). ${mode === 'gestor' ? 'El gráfico de precios muestra tu segmento específico con filtros.' : 'El gráfico de precios tiene SELECTOR DE SEGMENTOS para análisis detallado por segmento.'} Las etiquetas de productos se muestran correctamente sin cortes.`}
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        size="large"
        items={tabItems}
      />

      <FloatButton
        icon={<ReloadOutlined />}
        type="primary"
        style={{
          right: 24,
          bottom: 24,
          backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff'
        }}
        onClick={handleRefreshAll}
        tooltip={`Actualizar dashboard - Modo: ${mode === 'direccion' ? 'Dirección' : 'Gestor'}`}
      />

      {selectedEntity && (
        <div style={{
          position: 'fixed',
          bottom: 80,
          right: 24,
          padding: '12px 16px',
          backgroundColor: 'rgba(0,0,0,0.8)',
          color: 'white',
          borderRadius: 8,
          fontSize: 12,
          maxWidth: 300,
          zIndex: 1000
        }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>
            Seleccionado: {selectedEntity.label}
          </div>
          <div>
            Valor: {formatBankingValue(selectedEntity.value, { 
              decimals: 2,
              metric: selectedEntity.metric || unifiedConfig.metric
            }).displayValue}
          </div>
          <div>
            Gráfico: {selectedEntity.chartKey} • Métrica: {selectedEntity.metric || unifiedConfig.metric}
          </div>
        </div>
      )}
    </div>
  );
};

InteractiveCharts.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.oneOfType([PropTypes.string, PropTypes.object]).isRequired,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  metric: PropTypes.oneOf(['CONTRATOS', 'CLIENTES', 'MARGEN', 'INGRESOS', 'GASTOS']),
  chartType: PropTypes.oneOf(['horizontal_bar', 'bar', 'line', 'donut', 'stacked_bar']),
  filters: PropTypes.object,
  height: PropTypes.number,
  onReload: PropTypes.func,
  onSelectEntity: PropTypes.func,
  externalChartConfig: PropTypes.object,
  onChartConfigChange: PropTypes.func,
  onChartUpdate: PropTypes.func,
  onChartPivot: PropTypes.func,
  className: PropTypes.string,
  style: PropTypes.object
};

export default React.memo(InteractiveCharts);
