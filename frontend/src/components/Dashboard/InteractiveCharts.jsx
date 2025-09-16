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
  Alert,
  App
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
import analyticsService, { 
  validatePivotCombination, 
  PIVOTABLE_CONFIG, 
  getPivotableChartData 
} from '../../services/analyticsService';
import api from '../../services/api';
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

// ✅ MANTENER: Validaciones existentes como FALLBACK
const VALID_COMBINATIONS_DIRECCION_FALLBACK = {
  CONTRATOS: ['gestores', 'centros', 'productos', 'segmentos'],
  CLIENTES: ['gestores', 'centros', 'productos', 'segmentos'], 
  MARGEN: ['gestores', 'centros', 'productos', 'segmentos'],
  INGRESOS: ['gestores', 'centros', 'productos', 'segmentos'],
  GASTOS: ['gestores', 'centros', 'productos', 'segmentos']
};

const VALID_COMBINATIONS_GESTOR_FALLBACK = {
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

// ✅ CORREGIDO: Validación simplificada y directa por modo
const isValidCombination = (metric, dimension, mode) => {
  if (!metric || !dimension) return false;
  
  console.log(`[isValidCombination] Checking ${metric} by ${dimension} for mode ${mode}`);
  
  // ✅ CORREGIDO: Usar validaciones directas y específicas por modo
  if (mode === 'direccion') {
    const validCombinations = VALID_COMBINATIONS_DIRECCION_FALLBACK;
    const result = validCombinations[metric]?.includes(dimension) || false;
    console.log(`[isValidCombination] Direction result: ${result}`);
    return result;
  } else if (mode === 'gestor') {
    const validCombinations = VALID_COMBINATIONS_GESTOR_FALLBACK;
    const result = validCombinations[metric]?.includes(dimension) || false;
    console.log(`[isValidCombination] Gestor result: ${result}`);
    return result;
  }
  
  return false;
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

// ✅ MANTENER INTACTO: Transformador de datos de precios
const transformPriceComparisonData = (rawData) => {
  if (!rawData || !rawData.standard || !rawData.real) {
    return null;
  }

  const { standard, real } = rawData;
  
  // Crear mapas por producto
  const standardMap = {};
  const realMap = {};
  
  standard.forEach(item => {
    standardMap[item.PRODUCTO_ID] = {
      precio: Math.abs(item.PRECIO_MANTENIMIENTO || 0),
      descripcion: item.DESC_PRODUCTO
    };
  });
  
  real.forEach(item => {
    realMap[item.PRODUCTO_ID] = {
      precio: Math.abs(item.PRECIO_MANTENIMIENTO_REAL || 0),
      descripcion: item.DESC_PRODUCTO,
      contratos: item.NUM_CONTRATOS_BASE || 0,
      segmento: item.DESC_SEGMENTO
    };
  });
  
  // Obtener productos únicos
  const productos = [...new Set([...Object.keys(standardMap), ...Object.keys(realMap)])];
  
  const labels = [];
  const standardData = [];
  const realData = [];
  const tableData = [];
  
  productos.forEach(productoId => {
    const standardInfo = standardMap[productoId];
    const realInfo = realMap[productoId];
    
    if (standardInfo || realInfo) {
      const descripcion = (realInfo?.descripcion || standardInfo?.descripcion || productoId).substring(0, 20);
      labels.push(descripcion);
      
      const precioStd = standardInfo?.precio || 0;
      const precioReal = realInfo?.precio || 0;
      
      standardData.push(precioStd);
      realData.push(precioReal);
      
      // Calcular delta y semáforo
      const delta = precioStd > 0 ? ((precioReal - precioStd) / precioStd) * 100 : 0;
      const deltaPct = Math.abs(delta);
      
      let semaforo = 'Verde';
      if (deltaPct > 15) semaforo = 'Rojo';
      else if (deltaPct > 5) semaforo = 'Amarillo';
      
      tableData.push({
        producto_id: productoId,
        descripcion: realInfo?.descripcion || standardInfo?.descripcion,
        precio_std: precioStd,
        precio_real: precioReal,
        delta_pct: delta,
        semaforo,
        contratos: realInfo?.contratos || 0
      });
    }
  });
  
  return {
    labels,
    datasets: [
      {
        label: 'Precio Estándar',
        data: standardData,
        backgroundColor: 'rgba(21, 82, 63, 1)',
        borderColor: 'rgba(21, 82, 63, 1)',
        borderWidth: 1
      },
      {
        label: 'Precio Real',
        data: realData,
        backgroundColor: 'rgba(17, 124, 97, 1)',
        borderColor: 'rgba(17, 124, 97, 1)',
        borderWidth: 1
      }
    ],
    table: tableData,
    meta: {
      segmento_id: rawData.segmento_id,
      periodo: rawData.periodo,
      productos_count: productos.length,
      semaforos: {
        Verde: tableData.filter(item => item.semaforo === 'Verde').length,
        Amarillo: tableData.filter(item => item.semaforo === 'Amarillo').length,
        Rojo: tableData.filter(item => item.semaforo === 'Rojo').length
      }
    }
  };
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

// ✅ NUEVO: Función para obtener iconos de métricas
const getMetricIcon = (metricKey) => {
  const iconMap = {
    'CONTRATOS': <FundOutlined />,
    'CLIENTES': <TeamOutlined />,
    'INGRESOS': <DollarCircleOutlined />,
    'MARGEN_NETO': <LineChartOutlined />,
    'ROE': <TrophyOutlined />,
    'INCENTIVOS': <DollarCircleOutlined />
  };
  return iconMap[metricKey] || <BarChartOutlined />;
};

// ✅ NUEVO: Función para obtener iconos de dimensiones
const getDimensionIcon = (dimensionKey) => {
  const iconMap = {
    'gestor': <TeamOutlined />,
    'gestores': <TeamOutlined />,
    'centro': <FundOutlined />,
    'centros': <FundOutlined />,
    'producto': <DollarCircleOutlined />,
    'productos': <DollarCircleOutlined />,
    'segmento': <FundOutlined />,
    'segmentos': <FundOutlined />,
    'cliente': <TeamOutlined />,
    'clientes': <TeamOutlined />
  };
  return iconMap[dimensionKey] || <FundOutlined />;
};

/**
 * ✅ MEJORADO: ChartFilter con configuración dinámica de PIVOTABLE_CONFIG
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
  
  // ✅ CORREGIDO: Usar métricas básicas según el modo
  const metricOptions = useMemo(() => {
    if (chartKey === 'unified') {
      const baseMetrics = [
        { value: 'CONTRATOS', label: 'Contratos', icon: getMetricIcon('CONTRATOS') },
        { value: 'CLIENTES', label: 'Clientes', icon: getMetricIcon('CLIENTES') },
        { value: 'INGRESOS', label: 'Ingresos', icon: getMetricIcon('INGRESOS') },
        { value: 'MARGEN', label: 'Margen', icon: getMetricIcon('MARGEN') },
        { value: 'GASTOS', label: 'Gastos', icon: getMetricIcon('GASTOS') }
      ];
      
      // Filtrar métricas válidas para el modo
      return baseMetrics.filter(metric => 
        isValidCombination(metric.value, currentDimension, mode)
      );
    }
    return availableMetrics.length > 0 ? availableMetrics : [
      { value: currentMetric, label: currentMetric, icon: getMetricIcon(currentMetric) }
    ];
  }, [mode, chartKey, availableMetrics, currentMetric, currentDimension]);

  // ✅ CORREGIDO: Tipos de gráfico simplificados
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

  // ✅ CORREGIDO: Dimensiones según modo
  const dimensionOptions = useMemo(() => {
    let baseDimensions = [];
    
    if (chartKey === 'unified') {
      if (mode === 'direccion') {
        baseDimensions = [
          { value: 'gestores', label: 'Gestores', icon: getDimensionIcon('gestores') },
          { value: 'centros', label: 'Centros', icon: getDimensionIcon('centros') },
          { value: 'productos', label: 'Productos', icon: getDimensionIcon('productos') },
          { value: 'segmentos', label: 'Segmentos', icon: getDimensionIcon('segmentos') }
        ];
      } else if (mode === 'gestor') {
        baseDimensions = [
          { value: 'clientes', label: 'Clientes', icon: getDimensionIcon('clientes') },
          { value: 'productos', label: 'Productos', icon: getDimensionIcon('productos') }
        ];
      }
    }
    
    // ✅ CORREGIDO: Filtrar solo dimensiones válidas para la métrica actual
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

  // ✅ CORREGIDO: Limitar auto-ajustes solo cuando sea realmente necesario
  React.useEffect(() => {
    if (currentDimension !== effectiveDimension && effectiveDimension && onDimensionChange) {
      console.log(`[ChartFilter] 🔧 Auto-adjusting dimension from ${currentDimension} to ${effectiveDimension} for metric ${currentMetric} in mode ${mode}`);
      // ✅ SOLO hacer auto-ajuste si realmente es necesario y válido para el modo
      if (mode === 'direccion' && !['gestores', 'centros', 'productos', 'segmentos'].includes(currentDimension)) {
        onDimensionChange(effectiveDimension);
      } else if (mode === 'gestor' && !['clientes', 'productos'].includes(currentDimension)) {
        onDimensionChange(effectiveDimension);
      }
    }
  }, [currentDimension, effectiveDimension, currentMetric, onDimensionChange, mode]);

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
 * ✅ MANTENER INTACTO: PriceComparisonChart - NO MODIFICAR
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
  
  if (!validation.valid || validation.isEmpty) {
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
 * ✅ CORREGIDO: UnifiedChart con tooltips mejorados
 */
const UnifiedChart = ({ data, config = {}, height = 280, onDataClick }) => {
  const { chartType = 'horizontal_bar', metric = 'CONTRATOS' } = config;
  
  const validation = validateDataset(data, 'unified');
  
  if (validation.isLoading) {
    return (
      <div style={{ height, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
        <Loader size="large" />
        <Text type="secondary" style={{ marginTop: 16 }}>
          Cargando datos con Perfect Integration...
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
                Prueba cambiar la métrica o dimensión usando los filtros
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
            // ✅ CORREGIDO: Mostrar valor real sin formateo incorrecto
            const isCount = COUNT_METRICS.includes(metric);
            let displayValue = '';
            
            if (isCount) {
              displayValue = Math.round(Math.abs(value)).toLocaleString();
            } else {
              if (Math.abs(value) >= 1000000) {
                displayValue = (Math.abs(value) / 1000000).toFixed(2) + 'M€';
              } else if (Math.abs(value) >= 1000) {
                displayValue = (Math.abs(value) / 1000).toFixed(1) + 'K€';
              } else {
                displayValue = Math.abs(value).toFixed(2) + '€';
              }
            }
            
            return ` ${context.dataset.label || metric}: ${displayValue}`;
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
          {data.meta.pivot_enabled && (
            <span style={{ marginLeft: 8, color: theme.colors?.success || '#52c41a' }}>
              • Pivoteable
            </span>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * ✅ CORREGIDO: InteractiveCharts con Perfect Integration
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
  
  const { notification } = App.useApp();

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

  // ✅ MANTENER: Estados para gestión de segmento del gestor
  const [gestorSegmentoInfo, setGestorSegmentoInfo] = useState(null);
  const [loadingGestorSegmento, setLoadingGestorSegmento] = useState(false);

  // MANTENER: Estado para selector de segmentos en dashboard dirección
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

  // ✅ NUEVO: Exponer configuración actual para ConversationalPivot
  const currentChartConfig = useMemo(() => ({
    metric: unifiedConfig.metric,
    dimension: unifiedConfig.dimension,
    chartType: unifiedConfig.chartType,
    mode,
    gestorId: normalizedGestorId,
    periodo: normalizedPeriodo,
    unified: true // Identificar que es el gráfico unified
  }), [unifiedConfig, mode, normalizedGestorId, normalizedPeriodo]);

  // ✅ NUEVO: Efecto para manejar updates externos de ConversationalPivot
  useEffect(() => {
    if (externalChartConfig && externalChartConfig.source === 'conversational_pivot') {
      console.log('[InteractiveCharts] 🔄 Received update from ConversationalPivot:', externalChartConfig);
      
      // Actualizar configuración unified
      if (externalChartConfig.chartKey === 'unified') {
        setUnifiedConfig(prev => ({
          ...prev,
          metric: externalChartConfig.metric || prev.metric,
          dimension: externalChartConfig.dimension || prev.dimension, 
          chartType: externalChartConfig.chartType || prev.chartType
        }));
        
        // Si hay datos nuevos, actualizarlos directamente
        if (externalChartConfig.labels && externalChartConfig.datasets) {
          setChartsData(prev => ({
            ...prev,
            unified: {
              labels: externalChartConfig.labels,
              datasets: externalChartConfig.datasets,
              meta: externalChartConfig.meta || {}
            }
          }));
        }
      }
    }
  }, [externalChartConfig]);

  // ✅ NUEVO: Notificar cambios de configuración a ConversationalPivot
  useEffect(() => {
    if (onChartConfigChange) {
      onChartConfigChange(currentChartConfig);
    }
  }, [currentChartConfig, onChartConfigChange]);

  // ✅ MANTENER INTACTO: Efecto para cargar segmento del gestor
  useEffect(() => {
    const loadGestorSegmento = async () => {
      if (mode !== 'gestor' || !normalizedGestorId) return;
      
      setLoadingGestorSegmento(true);
      try {
        console.log(`[InteractiveCharts] 🔍 Loading segmento for gestor ${normalizedGestorId}`);
        
        const segmentoData = await api.basic.gestorSegmento(normalizedGestorId);
        
        console.log(`[InteractiveCharts] ✅ Gestor ${normalizedGestorId} segmento loaded:`, segmentoData);
        setGestorSegmentoInfo(segmentoData);
        
      } catch (error) {
        console.error(`[InteractiveCharts] ❌ Error loading gestor segmento:`, error);
        
        setGestorSegmentoInfo({
          GESTOR_ID: normalizedGestorId,
          SEGMENTO_ID: 'N10101',
          DESC_SEGMENTO: 'Segmento desconocido'
        });
        
      } finally {
        setLoadingGestorSegmento(false);
      }
    };

    loadGestorSegmento();
  }, [mode, normalizedGestorId]);

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
        
        // ✅ NUEVO: Notificar actualización a ConversationalPivot
        if (chartKey === 'unified' && result && onChartUpdate) {
          onChartUpdate({
            chartKey: 'unified',
            ...result,
            source: 'interactive_charts',
            timestamp: Date.now()
          });
        }
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
  }, [cleanupAbortController, unifiedConfig, mode, onChartUpdate]);

  // ✅ CORREGIDO: loadUnifiedData con separación clara por modo
  const loadUnifiedData = useCallback(async () => {
    const config = unifiedConfig;
    
    console.log(`[InteractiveCharts] 🎯 Loading unified data with config:`, config);
    
    // ✅ CORREGIDO: En modo dirección, usar endpoints específicos de dirección
    if (mode === 'direccion') {
      console.log(`[InteractiveCharts] 🏢 Using direction-specific endpoints`);
      
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
    }
    
    // ✅ SOLO para modo gestor: intentar getPivotableChartData
    if (mode === 'gestor' && normalizedGestorId) {
      try {
        console.log(`[InteractiveCharts] 🚀 Trying getPivotableChartData for ${config.metric} by ${config.dimension}`);
        
        // Mapear dimensiones de UI a dimensiones de PIVOTABLE_CONFIG
        const dimensionMap = {
          'clientes': 'cliente',
          'productos': 'producto'
        };
        
        const mappedDimension = dimensionMap[config.dimension] || config.dimension;
        
        const result = await getPivotableChartData(
          config.metric,
          mappedDimension,
          config.chartType,
          {
            periodo: normalizedPeriodo,
            gestorId: normalizedGestorId,
            mode,
            ...filters
          }
        );
        
        console.log(`[InteractiveCharts] ✅ getPivotableChartData successful:`, result.meta);
        return result;
        
      } catch (pivotError) {
        console.warn(`[InteractiveCharts] ⚠️ getPivotableChartData failed, using fallback:`, pivotError.message);
        
        // Fallback para gestor
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
    }
    
    // Fallback final
    console.warn(`[InteractiveCharts] ⚠️ No valid data loading path found`);
    throw new Error('No hay datos disponibles para esta configuración');
  }, [mode, normalizedGestorId, normalizedPeriodo, filters, unifiedConfig]);

  // ✅ MANTENER INTACTO: loadPriceData sin modificaciones
  const loadPriceData = useCallback(async () => {
    if (mode === 'direccion') {
      console.log(`[InteractiveCharts] 🎯 Loading price data for DIRECTION mode (segment: ${selectedSegment})`);
      const rawData = await api.dataQueries.pricesComparisonBySegment(selectedSegment, normalizedPeriodo);
      return transformPriceComparisonData(rawData);
      
    } else if (normalizedGestorId && gestorSegmentoInfo) {
      const gestorSegmentoId = gestorSegmentoInfo.SEGMENTO_ID;
      console.log(`[InteractiveCharts] 🎯 Loading price data for GESTOR mode (gestor ${normalizedGestorId}, segmento: ${gestorSegmentoId})`);
      
      const rawData = await api.dataQueries.pricesComparisonBySegment(gestorSegmentoId, normalizedPeriodo);
      return transformPriceComparisonData(rawData);
      
    } else if (normalizedGestorId && !gestorSegmentoInfo) {
      console.log(`[InteractiveCharts] ⏳ Esperando segmento del gestor ${normalizedGestorId}...`);
      return {
        labels: ['Cargando...'],
        datasets: [{
          label: 'Cargando datos del segmento...',
          data: [0],
          backgroundColor: '#f0f0f0'
        }],
        meta: { loading: true, gestorId: normalizedGestorId }
      };
    }
    
    return null;
  }, [mode, normalizedGestorId, normalizedPeriodo, gestorSegmentoInfo, selectedSegment]);

  // ✅ MANTENER: Efectos para recargar precios
  useEffect(() => {
    if (mode === 'gestor' && gestorSegmentoInfo && !loadingGestorSegmento) {
      console.log(`[InteractiveCharts] 🔄 Gestor segmento loaded, reloading price data for ${gestorSegmentoInfo.SEGMENTO_ID}`);
      loadChartData('priceComparison', loadPriceData, true);
    }
  }, [mode, gestorSegmentoInfo, loadingGestorSegmento, loadChartData, loadPriceData]);

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
      filters,
      gestorSegmentoInfo: gestorSegmentoInfo?.SEGMENTO_ID
    }), 
    [mode, normalizedGestorId, normalizedPeriodo, unifiedConfig, priceConfig, filters, gestorSegmentoInfo]
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

    if (mode === 'gestor' && !gestorSegmentoInfo) {
      console.log('[InteractiveCharts] ⏳ Waiting for gestor segmento info before loading charts');
      return;
    }

    lastLoadKey.current = dependencyKey;
    console.log('[InteractiveCharts] 🚀 Loading all charts with Perfect Integration');

    setChartsData({});
    setErrorStates({});

    const loadPromises = [
      loadChartData('unified', loadUnifiedData, true),
      loadChartData('priceComparison', loadPriceData, true)
    ];

    Promise.allSettled(loadPromises).then(() => {
      console.log('[InteractiveCharts] ✅ All charts loading completed with Perfect Integration');
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
    gestorSegmentoInfo,
    loadChartData,
    loadUnifiedData,
    loadPriceData,
    cleanupAbortController
  ]);

  // ✅ CORREGIDO: handleUnifiedConfigChange con validaciones correctas según el modo
  const handleUnifiedConfigChange = useCallback((configType, value) => {
    console.log(`[InteractiveCharts] 🔧 Unified config change: ${configType} = ${value}`);
    
    setUnifiedConfig(prev => {
      const newConfig = { ...prev, [configType]: value };
      
      if (configType === 'metric') {
        if (!isValidCombination(value, newConfig.dimension, mode)) {
          // ✅ CORREGIDO: Usar dimensiones correctas según el modo
          let validDimensions = [];
          
          if (mode === 'direccion') {
            // Para dirección: usar dimensiones estándar
            const validCombinations = {
              'CONTRATOS': ['gestores', 'centros', 'productos', 'segmentos'],
              'CLIENTES': ['gestores', 'centros', 'productos', 'segmentos'], 
              'MARGEN': ['gestores', 'centros', 'productos', 'segmentos'],
              'INGRESOS': ['gestores', 'centros', 'productos', 'segmentos'],
              'GASTOS': ['gestores', 'centros', 'productos', 'segmentos']
            };
            validDimensions = validCombinations[value] || ['gestores'];
          } else {
            // Para gestor: usar dimensiones limitadas
            const validCombinations = {
              'CONTRATOS': ['clientes', 'productos'],
              'CLIENTES': ['productos'],
              'MARGEN': ['productos', 'clientes'],
              'INGRESOS': ['productos', 'clientes'],
              'GASTOS': ['productos', 'clientes']
            };
            validDimensions = validCombinations[value] || ['clientes'];
          }
          
          if (validDimensions.length > 0) {
            const fallbackDimension = mode === 'direccion' 
              ? (validDimensions.includes('gestores') ? 'gestores' : validDimensions[0])
              : (validDimensions.includes('clientes') ? 'clientes' : validDimensions[0]);
              
            newConfig.dimension = fallbackDimension;
            console.log(`[InteractiveCharts] 🔧 Auto-adjusted dimension to ${fallbackDimension} for metric ${value} in mode ${mode}`);
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
    console.log('[InteractiveCharts] 🔄 Refreshing all charts with Perfect Integration');
    
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
                Análisis General Dinámico v11.1
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
                  ? `✅ Vista corporativa • ${unifiedConfig.metric} por ${unifiedConfig.dimension} • Perfect Integration`
                  : `🎯 Vista personal • ${unifiedConfig.metric} por ${unifiedConfig.dimension} • getPivotableChartData()`}
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

  // ✅ MANTENER INTACTO: renderPriceTab sin modificaciones
  const renderPriceTab = () => {
    const data = chartsData.priceComparison;
    const loading = loadingStates.priceComparison || loadingGestorSegmento;
    const error = errorStates.priceComparison;

    const handleSegmentChange = (value) => {
      setSelectedSegment(value);
    };

    const getSegmentDisplayInfo = () => {
      if (mode === 'direccion') {
        const selectedSegmentInfo = segmentos.find(s => s.id === selectedSegment);
        return {
          nombre: selectedSegmentInfo?.nombre || 'Desconocido',
          id: selectedSegment,
          type: 'manual'
        };
      } else if (gestorSegmentoInfo) {
        return {
          nombre: gestorSegmentoInfo.DESC_SEGMENTO || 'Segmento desconocido',
          id: gestorSegmentoInfo.SEGMENTO_ID,
          type: 'auto'
        };
      }
      return { nombre: 'Cargando...', id: 'loading', type: 'loading' };
    };

    const segmentInfo = getSegmentDisplayInfo();

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
                  ? `✅ Filtrado por segmento: ${segmentInfo.nombre}`
                  : `🎯 Segmento específico del Gestor ${normalizedGestorId}: ${segmentInfo.nombre} (${segmentInfo.id})`}
                {segmentInfo.type === 'auto' && (
                  <span style={{ color: theme.colors?.success || '#52c41a', marginLeft: 8 }}>
                    • Detectado automáticamente
                  </span>
                )}
              </Text>
                
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
            description={`Mostrando precios del segmento ${segmentInfo.nombre}. Usa el selector arriba para cambiar de segmento.`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {mode === 'gestor' && gestorSegmentoInfo && (
          <Alert
            message="Vista Personalizada del Gestor"
            description={`Mostrando precios específicos del segmento ${segmentInfo.nombre} (${segmentInfo.id}) correspondiente al Gestor ${normalizedGestorId}. Datos automáticamente filtrados por tu segmento asignado.`}
            type="success"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {mode === 'gestor' && !gestorSegmentoInfo && !loadingGestorSegmento && (
          <Alert
            message="Error cargando segmento"
            description="No se pudo determinar el segmento del gestor. Mostrando datos por defecto."
            type="warning"
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
            key={`price-${normalizedGestorId || selectedSegment}-${priceConfig.chartType}-${segmentInfo.id}`}
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
          <Badge 
            count="v11.1" 
            size="small" 
            style={{ backgroundColor: theme.colors?.success || '#52c41a' }}
          />
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
          {mode === 'gestor' && gestorSegmentoInfo && (
            <Badge 
              count={gestorSegmentoInfo.SEGMENTO_ID} 
              size="small" 
              style={{ backgroundColor: theme.colors?.success || '#52c41a' }}
            />
          )}
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
              Dashboard Perfect Integration v11.1
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
                  ? `✅ Dashboard corporativo • Perfect Integration • PIVOTABLE_CONFIG • Período: ${normalizedPeriodo}`
                  : `🎯 Panel personalizado • getPivotableChartData() • Período: ${normalizedPeriodo}`}
                {mode === 'gestor' && normalizedGestorId && ` • Gestor: ${normalizedGestorId}`}
                {mode === 'gestor' && gestorSegmentoInfo && (
                  <span style={{ color: theme.colors?.success || '#52c41a', marginLeft: 8 }}>
                    • Segmento: {gestorSegmentoInfo.SEGMENTO_ID}
                  </span>
                )}
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
          message="✅ Perfect Integration v11.1 Activa"
          description={`Gráfico de análisis general: ${mode === 'gestor' ? 'Usa getPivotableChartData() con función unificada para cualquier combinación métricas+dimensión. Validaciones dinámicas con PIVOTABLE_CONFIG.' : 'Integración completa con función unificada y validaciones dinámicas.'} Gráfico de precios: ${mode === 'gestor' ? 'Filtrado automático por segmento del gestor detectado.' : 'Selector manual de segmentos para análisis detallado.'} ConversationalPivot conectado para pivoteo conversacional.`}
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
        tooltip={`Perfect Integration v11.1 - Modo: ${mode === 'direccion' ? 'Dirección' : 'Gestor'}`}
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
          <div style={{ fontSize: 10, opacity: 0.8, marginTop: 4 }}>
            Perfect Integration v11.1 • {chartsData.unified?.meta?.pivot_enabled ? 'Pivoteable' : 'Estático'}
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

const InteractiveChartsWithApp = (props) => (
  <App>
    <InteractiveCharts {...props} />
  </App>
);

export default React.memo(InteractiveChartsWithApp);
