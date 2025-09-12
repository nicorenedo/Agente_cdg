// src/components/Dashboard/InteractiveCharts.jsx
// InteractiveCharts v4.0 - Integración total con api.js v4.0 y chatService.js v4.0
// ✅ CORRECCIÓN: Eliminado dropdownStyle deprecado, usando styles.popup.root

import React, { useState, useEffect, useCallback, useMemo, useRef, forwardRef, useImperativeHandle } from 'react';
import { 
  Card, Radio, Select, Tooltip, Row, Col, Spin, Alert, Button, Space, 
  Tag, Divider, Switch, notification, Badge, Progress, Empty, Popover,
  Typography, Slider, InputNumber
} from 'antd';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  Legend, ResponsiveContainer, ScatterChart, Scatter, ComposedChart
} from 'recharts';
import { 
  BarChartOutlined, LineChartOutlined, PieChartOutlined, DotChartOutlined,
  AreaChartOutlined, TrophyFilled, RiseOutlined, DollarOutlined, InfoCircleOutlined,
  SyncOutlined, ExclamationCircleOutlined, CheckCircleOutlined, ThunderboltOutlined,
  SettingOutlined, EyeOutlined, ReloadOutlined, ApiOutlined, DatabaseOutlined,
  ClockCircleOutlined, BulbOutlined, WarningOutlined, FilterOutlined, FullscreenOutlined,
  CompressOutlined, DownloadOutlined, ShareAltOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import theme from '../../styles/theme';
import { useChatService, CONNECTION_STATES } from '../../services/chatService';
import api from '../../services/api';

const { Option } = Select;
const { Text, Title } = Typography;

// ============================================================================
// 🎨 CONFIGURACIÓN Y CONSTANTES v4.0
// ============================================================================

const CHART_COLORS = [
  '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#607D8B', '#F44336', 
  '#00BCD4', '#8BC34A', '#FFC107', '#E91E63', '#795548', '#009688',
  '#607D8B', '#3F51B5', '#E91E63', '#FF5722', '#795548', '#9E9E9E'
];

const CHART_TYPES = {
  bar: { 
    label: 'Barras', 
    icon: <BarChartOutlined />, 
    description: 'Comparación de valores entre categorías',
    multiMetric: true,
    bestFor: ['comparar', 'ranking', 'categorías', 'gestores', 'centros'],
    minDataPoints: 1,
    maxDataPoints: 50
  },
  line: { 
    label: 'Líneas', 
    icon: <LineChartOutlined />, 
    description: 'Tendencias temporales y evolución',
    multiMetric: true,
    bestFor: ['temporal', 'tendencia', 'evolución', 'periodo', 'tiempo'],
    minDataPoints: 2,
    maxDataPoints: 100
  },
  area: { 
    label: 'Área', 
    icon: <AreaChartOutlined />, 
    description: 'Volúmenes acumulativos y composición',
    multiMetric: true,
    bestFor: ['volumen', 'composición', 'acumulativo', 'ingresos'],
    minDataPoints: 2,
    maxDataPoints: 100
  },
  pie: { 
    label: 'Circular', 
    icon: <PieChartOutlined />, 
    description: 'Distribución proporcional (máx 8 elementos)',
    multiMetric: false,
    bestFor: ['distribución', 'proporción', 'partes', 'segmentos'],
    minDataPoints: 2,
    maxDataPoints: 8
  },
  scatter: { 
    label: 'Dispersión', 
    icon: <DotChartOutlined />, 
    description: 'Correlaciones entre dos variables',
    multiMetric: true,
    bestFor: ['correlación', 'relación', 'dispersión', 'análisis'],
    minDataPoints: 5,
    maxDataPoints: 200
  }
};

const DIMENSION_MAPPING = {
  patterns: {
    centro: ['centro', 'oficina', 'sucursal', 'branch', 'office', 'desc_centro', 'nombre_centro'],
    gestor: ['gestor', 'comercial', 'manager', 'vendedor', 'rep', 'desc_gestor', 'nombre_gestor'],
    cliente: ['cliente', 'customer', 'client', 'nombre_cliente'],
    producto: ['producto', 'product', 'servicio', 'service', 'desc_producto'],
    segmento: ['segmento', 'segment', 'categoria', 'category', 'desc_segmento'],
    contrato: ['contrato', 'contract', 'acuerdo', 'deal', 'contrato_id'],
    periodo: ['periodo', 'period', 'fecha', 'date', 'mes', 'month', 'año', 'year', 'trimestre', 'quarter']
  },
  
  knownFields: {
    'DESC_CENTRO': 'centro',
    'NOMBRE_CENTRO': 'centro',
    'DESC_GESTOR': 'gestor',
    'NOMBRE_GESTOR': 'gestor',
    'NOMBRE_CLIENTE': 'cliente',
    'DESC_PRODUCTO': 'producto',
    'DESC_SEGMENTO': 'segmento',
    'CONTRATO_ID': 'contrato',
    'FECHA': 'periodo',
    'MES': 'periodo',
    'PERIODO': 'periodo'
  }
};

const FINANCIAL_METRICS_CONFIG = {
  formats: {
    currency: { prefix: '€', decimals: 0, thousands: true },
    percentage: { suffix: '%', decimals: 2 },
    ratio: { decimals: 3 },
    count: { decimals: 0, thousands: true },
    default: { decimals: 2 }
  },
  
  typePatterns: {
    currency: ['precio', 'ingreso', 'gasto', 'coste', 'beneficio', 'margen_neto', 'total_'],
    percentage: ['roe', 'ratio', 'porcentaje', 'eficiencia', 'tasa'],
    count: ['numero', 'cantidad', 'count', 'volumen', 'contratos'],
    ratio: ['indice', 'factor', 'multiplicador']
  },
  
  kpiIcons: {
    'ROE': <TrophyFilled style={{ color: '#faad14' }} />,
    'MARGEN_NETO': <DollarOutlined style={{ color: '#52c41a' }} />,
    'TOTAL_INGRESOS': <RiseOutlined style={{ color: '#1890ff' }} />,
    'INGRESOS': <RiseOutlined style={{ color: '#1890ff' }} />,
    'TOTAL_GASTOS': <WarningOutlined style={{ color: '#f5222d' }} />,
    'BENEFICIO_NETO': <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    'EFICIENCIA': <ThunderboltOutlined style={{ color: '#722ed1' }} />,
    'CONTRATOS': <DatabaseOutlined style={{ color: '#13c2c2' }} />
  }
};

// ✅ CORRECCIÓN: Estilos para Select - Reemplaza dropdownStyle deprecado
const SELECT_DROPDOWN_STYLES = {
  popup: {
    root: {
      maxHeight: 300,
      overflowY: 'auto',
      zIndex: 1050
    }
  }
};

// ============================================================================
// 🧠 SISTEMA INTELIGENTE DE DETECCIÓN v4.0
// ============================================================================

const detectAvailableDimensions = (data) => {
  if (!data?.length) return [];
  
  const firstItem = data[0];
  const dimensions = [];
  const dimensionValues = {};
  
  // Analizar todos los elementos para obtener valores únicos
  data.forEach(item => {
    Object.keys(item).forEach(key => {
      const value = item[key];
      if (typeof value === 'string' && value.trim()) {
        if (!dimensionValues[key]) {
          dimensionValues[key] = new Set();
        }
        dimensionValues[key].add(value);
      }
    });
  });
  
  // Identificar dimensiones basado en campos string con múltiples valores únicos
  Object.keys(firstItem).forEach(key => {
    const value = firstItem[key];
    
    if (typeof value === 'string' && value && dimensionValues[key]?.size > 1) {
      const uniqueValues = Array.from(dimensionValues[key]);
      
      let dimensionType = 'other';
      let priority = 100;
      
      // Buscar en campos conocidos
      if (DIMENSION_MAPPING.knownFields[key.toUpperCase()]) {
        dimensionType = DIMENSION_MAPPING.knownFields[key.toUpperCase()];
        priority = 1;
      } else {
        // Buscar por patrones
        Object.entries(DIMENSION_MAPPING.patterns).forEach(([type, patterns]) => {
          const keyLower = key.toLowerCase();
          if (patterns.some(pattern => keyLower.includes(pattern))) {
            dimensionType = type;
            priority = 5;
          }
        });
      }
      
      // Verificar si es temporal
      if (isTemporalDimension(uniqueValues)) {
        dimensionType = 'periodo';
        priority = 3;
      }
      
      dimensions.push({
        key,
        type: dimensionType,
        label: formatDimensionLabel(key),
        values: uniqueValues.slice(0, 50),
        valueCount: uniqueValues.length,
        priority,
        isUniversal: true,
        chatServiceCompatible: true
      });
    }
  });
  
  return dimensions.sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority;
    return a.label.localeCompare(b.label);
  });
};

const detectAvailableMetrics = (data) => {
  if (!data?.length) return [];
  
  const firstItem = data[0];
  const metrics = [];
  
  Object.keys(firstItem).forEach(key => {
    const value = firstItem[key];
    
    // Verificar si es numérico válido
    if ((typeof value === 'number' && !isNaN(value)) || 
        (typeof value === 'string' && !isNaN(parseFloat(value)) && isFinite(value))) {
      
      // Calcular estadísticas básicas
      const numericValues = data
        .map(item => parseFloat(item[key]))
        .filter(v => !isNaN(v) && isFinite(v));
      
      if (numericValues.length > 0) {
        const min = Math.min(...numericValues);
        const max = Math.max(...numericValues);
        const avg = numericValues.reduce((a, b) => a + b, 0) / numericValues.length;
        const type = detectMetricType(key);
        
        metrics.push({
          key,
          label: formatMetricLabel(key),
          type,
          format: getMetricFormat(key),
          icon: FINANCIAL_METRICS_CONFIG.kpiIcons[key.toUpperCase()],
          values: numericValues,
          stats: { min, max, avg, count: numericValues.length },
          isFinancial: isFinancialMetric(key),
          chatServiceCompatible: true
        });
      }
    }
  });
  
  return metrics.sort((a, b) => {
    // Priorizar métricas financieras conocidas
    if (a.isFinancial && !b.isFinancial) return -1;
    if (!a.isFinancial && b.isFinancial) return 1;
    return a.label.localeCompare(b.label);
  });
};

const isTemporalDimension = (values) => {
  if (!values || values.length === 0) return false;
  
  const temporalPatterns = [
    /^\d{4}-\d{2}-\d{2}$/, // YYYY-MM-DD
    /^\d{2}\/\d{2}\/\d{4}$/, // DD/MM/YYYY
    /^\d{4}-\d{2}$/, // YYYY-MM
    /^(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)/i,
    /^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,
    /^Q[1-4]\s\d{4}$/i, // Q1 2025
    /^\d{4}$/ // Solo año
  ];
  
  const temporalCount = values.filter(value => 
    temporalPatterns.some(pattern => pattern.test(value.toString()))
  ).length;
  
  return temporalCount / values.length > 0.5;
};

const isFinancialMetric = (key) => {
  const financialKeywords = ['roe', 'margen', 'ingreso', 'gasto', 'beneficio', 'precio', 'coste', 'eficiencia'];
  return financialKeywords.some(keyword => key.toLowerCase().includes(keyword));
};

const formatDimensionLabel = (key) => {
  const cleanKey = key
    .replace(/^(DESC_|NOMBRE_|ID_|COD_)/g, '')
    .replace(/_/g, ' ')
    .toLowerCase();
    
  const specialCases = {
    'centro': 'Centro',
    'gestor': 'Gestor Comercial',
    'cliente': 'Cliente',
    'producto': 'Producto',
    'segmento': 'Segmento',
    'contrato': 'Contrato',
    'periodo': 'Período'
  };
  
  return specialCases[cleanKey] || cleanKey.replace(/\b\w/g, l => l.toUpperCase());
};

const formatMetricLabel = (key) => {
  const commonLabels = {
    'ROE': 'ROE (%)',
    'MARGEN_NETO': 'Margen Neto (€)',
    'TOTAL_INGRESOS': 'Ingresos Totales (€)',
    'INGRESOS': 'Ingresos (€)',
    'TOTAL_GASTOS': 'Gastos Totales (€)', 
    'BENEFICIO_NETO': 'Beneficio Neto (€)',
    'PRECIO_STD': 'Precio Estándar (€)',
    'PRECIO_REAL': 'Precio Real (€)',
    'VOLUMEN': 'Volumen',
    'CANTIDAD': 'Cantidad',
    'EFICIENCIA': 'Eficiencia (%)',
    'CONTRATOS': 'Número de Contratos',
    'CLIENTES': 'Número de Clientes'
  };
  
  if (commonLabels[key.toUpperCase()]) {
    return commonLabels[key.toUpperCase()];
  }
  
  return key.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
};

const detectMetricType = (key) => {
  const keyLower = key.toLowerCase();
  
  for (const [type, patterns] of Object.entries(FINANCIAL_METRICS_CONFIG.typePatterns)) {
    if (patterns.some(pattern => keyLower.includes(pattern))) {
      return type;
    }
  }
  
  return 'default';
};

const getMetricFormat = (key) => {
  const type = detectMetricType(key);
  return FINANCIAL_METRICS_CONFIG.formats[type] || FINANCIAL_METRICS_CONFIG.formats.default;
};

const formatValue = (value, metricKey) => {
  if (value == null || isNaN(value)) return '--';
  
  const format = getMetricFormat(metricKey);
  let formatted = Number(value).toFixed(format.decimals);
  
  if (format.thousands) {
    formatted = Number(formatted).toLocaleString('es-ES');
  }
  
  return `${format.prefix || ''}${formatted}${format.suffix || ''}`;
};

// ============================================================================
// 🔄 PROCESAMIENTO DE DATOS v4.0
// ============================================================================

const mapDimensionToField = (requestedDimension, availableDimensions) => {
  if (!requestedDimension || !availableDimensions?.length) {
    return availableDimensions[0]?.key || null;
  }
  
  const requested = requestedDimension.toLowerCase();
  
  // 1. Buscar coincidencia exacta por tipo
  const exactMatch = availableDimensions.find(dim => dim.type === requested);
  if (exactMatch) return exactMatch.key;
  
  // 2. Buscar por nombre/clave similar
  const keyMatch = availableDimensions.find(dim => 
    dim.key.toLowerCase().includes(requested) || 
    dim.label.toLowerCase().includes(requested)
  );
  if (keyMatch) return keyMatch.key;
  
  // 3. Buscar por patrones
  const patternMatch = availableDimensions.find(dim => {
    const patterns = DIMENSION_MAPPING.patterns[requested] || [];
    return patterns.some(pattern => 
      dim.key.toLowerCase().includes(pattern) ||
      dim.label.toLowerCase().includes(pattern)
    );
  });
  if (patternMatch) return patternMatch.key;
  
  // 4. Fallback
  return availableDimensions.reduce((best, current) => 
    current.priority < best.priority ? current : best
  ).key;
};

const processDataForVisualization = (data, dimensionField, metrics, groupingType = 'individual') => {
  if (!data?.length || !dimensionField) return [];
  
  console.log('🔄 [InteractiveCharts v4.0] Procesando datos:', { 
    dimensionField, 
    metrics, 
    dataLength: data.length, 
    groupingType 
  });
  
  if (groupingType === 'individual') {
    const processed = data
      .map(item => {
        const result = { [dimensionField]: item[dimensionField] };
        
        metrics.forEach(metric => {
          if (item[metric] != null) {
            const value = typeof item[metric] === 'string' ? parseFloat(item[metric]) : item[metric];
            if (!isNaN(value) && isFinite(value)) {
              result[metric] = value;
            }
          }
        });
        
        return result;
      })
      .filter(item => item[dimensionField] && 
        metrics.some(metric => item[metric] != null && !isNaN(item[metric]))
      );
    
    console.log('✅ Datos procesados individuales:', processed.length);
    return processed;
  }
  
  if (groupingType === 'grouped') {
    const grouped = {};
    
    data.forEach(item => {
      const dimensionValue = item[dimensionField];
      if (!dimensionValue) return;
      
      if (!grouped[dimensionValue]) {
        grouped[dimensionValue] = {
          [dimensionField]: dimensionValue,
          _count: 0,
          _sum: {},
          _valid: {}
        };
        metrics.forEach(metric => {
          grouped[dimensionValue]._sum[metric] = 0;
          grouped[dimensionValue]._valid[metric] = 0;
        });
      }
      
      grouped[dimensionValue]._count += 1;
      
      metrics.forEach(metric => {
        const value = typeof item[metric] === 'string' ? parseFloat(item[metric]) : item[metric];
        if (value != null && !isNaN(value) && isFinite(value)) {
          grouped[dimensionValue]._sum[metric] += value;
          grouped[dimensionValue]._valid[metric] += 1;
        }
      });
    });
    
    const result = Object.values(grouped).map(group => {
      const finalGroup = { [dimensionField]: group[dimensionField] };
      
      metrics.forEach(metric => {
        if (group._valid[metric] > 0) {
          finalGroup[metric] = group._sum[metric] / group._valid[metric];
        } else {
          finalGroup[metric] = 0;
        }
      });
      
      return finalGroup;
    });
    
    console.log('✅ Datos procesados agrupados:', result.length);
    return result;
  }
  
  return data;
};

const suggestBestChartType = (data, selectedMetrics, dimensionType) => {
  if (!data?.length || !selectedMetrics?.length) return 'bar';
  
  const dataCount = data.length;
  const isMultiMetric = selectedMetrics.length > 1;
  const isTemporal = dimensionType === 'periodo';
  
  if (isTemporal && dataCount > 3) return 'line';
  if (dataCount <= 8 && !isMultiMetric) return 'pie';
  if (isMultiMetric && dataCount <= 20) return 'bar';
  if (dataCount > 50) return 'line';
  if (selectedMetrics.length === 2 && dataCount >= 10) return 'scatter';
  
  return 'bar';
};

// ============================================================================
// 🎨 COMPONENTES UI v4.0
// ============================================================================

const UniversalTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  
  return (
    <div style={{
      backgroundColor: 'rgba(255,255,255,0.98)',
      padding: '12px 16px',
      border: '1px solid #d9d9d9',
      borderRadius: 8,
      boxShadow: '0 6px 20px rgba(0,0,0,0.15)',
      maxWidth: 320,
      minWidth: 200
    }}>
      <div style={{ 
        fontWeight: 600, 
        marginBottom: 8, 
        fontSize: 14, 
        color: theme.colors?.primary || '#1890ff',
        borderBottom: '1px solid #f0f0f0', 
        paddingBottom: 6 
      }}>
        {label}
      </div>
      {payload.map((entry, index) => (
        <div key={`tooltip-${index}`} style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: 4,
          minHeight: 20
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ 
              width: 12, 
              height: 12, 
              backgroundColor: entry.color, 
              borderRadius: 2,
              boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
            }} />
            <span style={{ fontSize: 13 }}>
              {FINANCIAL_METRICS_CONFIG.kpiIcons[entry.dataKey?.toUpperCase()]}
              {formatMetricLabel(entry.dataKey)}:
            </span>
          </div>
          <span style={{ 
            color: entry.color, 
            fontWeight: 600, 
            marginLeft: 12,
            fontSize: 13
          }}>
            {formatValue(entry.value, entry.dataKey)}
          </span>
        </div>
      ))}
      <div style={{ 
        marginTop: 8, 
        paddingTop: 6, 
        borderTop: '1px solid #f0f0f0',
        fontSize: 11,
        color: '#666',
        textAlign: 'center'
      }}>
        🎯 InteractiveCharts v4.0
      </div>
    </div>
  );
};

const DataStatusIndicator = ({ data, selectedDimension, selectedMetrics, connectionState }) => {
  const status = useMemo(() => {
    if (!data?.length) return { 
      type: 'error', 
      message: 'No hay datos disponibles',
      icon: <DatabaseOutlined />
    };
    
    if (!selectedDimension) return { 
      type: 'warning', 
      message: 'Selecciona una dimensión',
      icon: <InfoCircleOutlined />
    };
    
    if (!selectedMetrics?.length) return { 
      type: 'warning', 
      message: 'Selecciona al menos una métrica',
      icon: <BarChartOutlined />
    };
    
    const validRows = data.filter(item => 
      item[selectedDimension] && 
      selectedMetrics.some(metric => item[metric] != null && !isNaN(item[metric]))
    ).length;
    
    if (validRows === 0) return { 
      type: 'error', 
      message: 'No hay datos válidos para la configuración actual',
      icon: <ExclamationCircleOutlined />
    };
    
    if (validRows < data.length * 0.5) return { 
      type: 'warning', 
      message: `Datos parciales: ${validRows}/${data.length} registros válidos`,
      icon: <WarningOutlined />
    };
    
    return { 
      type: 'success', 
      message: `${validRows} registros válidos • v4.0`,
      icon: <CheckCircleOutlined />
    };
  }, [data, selectedDimension, selectedMetrics]);
  
  const colors = {
    success: '#52c41a',
    warning: '#faad14', 
    error: '#ff4d4f'
  };
  
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: 6,
      color: colors[status.type],
      fontSize: 12
    }}>
      {status.icon}
      <span>{status.message}</span>
      {connectionState && (
        <Badge 
          status={connectionState === CONNECTION_STATES.OPEN ? 'success' : 'warning'} 
          text={connectionState === CONNECTION_STATES.OPEN ? 'Online' : 'Local'}
        />
      )}
    </div>
  );
};

// ============================================================================
// 🚀 COMPONENTE PRINCIPAL v4.0 - ✅ CORRECCIÓN: Uso de default parameters
// ============================================================================

const InteractiveCharts = forwardRef(({ 
  data = [], 
  availableKpis = [],
  title = 'Análisis Financiero v4.0',
  description = '',
  onChartChange,
  currentConfig = null,
  height = 400,
  conversationalMode = false,
  executiveMode = false,
  showConfigInfo = true,
  enableFilters = true,
  userId = 'chart_user',
  gestorId = null,
  periodo = null,
  version = '4.0'
}, ref) => {
  
  // ============================================================================
  // 🏗️ STATES v4.0
  // ============================================================================
  
  const [chartType, setChartType] = useState('bar');
  const [selectedMetrics, setSelectedMetrics] = useState([]);
  const [selectedDimension, setSelectedDimension] = useState('');
  const [groupingType, setGroupingType] = useState('individual');
  const [isProcessing, setIsProcessing] = useState(false);
  const [forceRenderKey, setForceRenderKey] = useState(Date.now());
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  
  // Advanced features
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showTooltips, setShowTooltips] = useState(true);
  const [showLegend, setShowLegend] = useState(true);
  const [maxDataPoints, setMaxDataPoints] = useState(50);
  
  // Referencias
  const configRef = useRef({});
  const chartRef = useRef(null);
  const lastConfigRef = useRef(null);
  
  // ============================================================================
  // 🔌 CHATSERVICE INTEGRATION v4.0
  // ============================================================================
  
  const {
    fetchDimensionData,
    connectionState,
    serviceMetrics,
    updatePreferences,
    clearCache
  } = useChatService({
    userId,
    autoConnect: true,
    handlers: {
      onChartUpdate: useCallback((charts) => {
        console.log('📊 Chart update received v4.0:', charts);
        if (charts && charts.length > 0) {
          const latestChart = charts[charts.length - 1];
          if (latestChart.chartType && latestChart.chartType !== chartType) {
            setChartType(latestChart.chartType);
          }
          if (latestChart.selectedKpi && !selectedMetrics.includes(latestChart.selectedKpi)) {
            setSelectedMetrics([latestChart.selectedKpi]);
          }
          if (latestChart.dimension && latestChart.dimension !== selectedDimension) {
            setSelectedDimension(latestChart.dimension);
          }
          forceUpdate();
        }
      }, [chartType, selectedMetrics, selectedDimension])
    }
  });
  
  // ============================================================================
  // 🧠 DETECCIÓN AUTOMÁTICA v4.0
  // ============================================================================
  
  const availableDimensions = useMemo(() => {
    console.log('🔍 [InteractiveCharts v4.0] Detectando dimensiones...');
    const detected = detectAvailableDimensions(data);
    console.log('✅ Dimensiones detectadas:', detected.length);
    return detected;
  }, [data]);
  
  const availableMetrics = useMemo(() => {
    console.log('🔍 [InteractiveCharts v4.0] Detectando métricas...');
    const detected = detectAvailableMetrics(data);
    console.log('✅ Métricas detectadas:', detected.length);
    return detected;
  }, [data]);
  
  const processedData = useMemo(() => {
    if (!data?.length || !selectedDimension || !selectedMetrics.length) {
      return [];
    }
    
    setIsProcessing(true);
    
    try {
      const dimensionField = mapDimensionToField(selectedDimension, availableDimensions);
      let processed = processDataForVisualization(data, dimensionField, selectedMetrics, groupingType);
      
      // Apply max data points limit
      if (processed.length > maxDataPoints) {
        processed = processed.slice(0, maxDataPoints);
      }
      
      setTimeout(() => setIsProcessing(false), 300);
      setError(null);
      
      return processed;
    } catch (error) {
      console.error('❌ Error procesando datos:', error);
      setError(error.message);
      setIsProcessing(false);
      return [];
    }
  }, [data, selectedDimension, selectedMetrics, availableDimensions, groupingType, maxDataPoints]);
  
  const currentChartConfig = useMemo(() => ({
    chartType,
    selectedMetrics,
    selectedDimension,
    groupingType,
    dimensionField: mapDimensionToField(selectedDimension, availableDimensions),
    dataCount: processedData.length,
    version: '4.0',
    timestamp: lastUpdate,
    userId,
    gestorId,
    periodo
  }), [chartType, selectedMetrics, selectedDimension, groupingType, availableDimensions, processedData, lastUpdate, userId, gestorId, periodo]);
  
  // ============================================================================
  // 🔧 FUNCTIONS AND HANDLERS v4.0
  // ============================================================================
  
  const forceUpdate = useCallback(() => {
    const newTimestamp = Date.now();
    setForceRenderKey(newTimestamp);
    setLastUpdate(newTimestamp);
    console.log('🔄 [InteractiveCharts v4.0] Forzando actualización');
  }, []);
  
  const handleChartTypeChange = useCallback((e) => {
    const newType = e.target.value;
    console.log('🎨 [InteractiveCharts v4.0] Cambiando tipo:', newType);
    
    setChartType(newType);
    configRef.current = { ...configRef.current, chartType: newType };
    forceUpdate();
    
    if (onChartChange) {
      onChartChange(configRef.current);
    }
    
    notification.success({
      message: 'Gráfico actualizado v4.0',
      description: `Cambiado a ${CHART_TYPES[newType]?.label || newType}`,
      duration: 2
    });
  }, [onChartChange, forceUpdate]);
  
  const handleMetricsChange = useCallback((metrics) => {
    const metricsArray = Array.isArray(metrics) ? metrics : [metrics];
    console.log('📊 [InteractiveCharts v4.0] Cambiando métricas:', metricsArray);
    
    setSelectedMetrics(metricsArray);
    configRef.current = { ...configRef.current, selectedMetrics: metricsArray };
    forceUpdate();
    
    if (onChartChange) {
      onChartChange(configRef.current);
    }
  }, [onChartChange, forceUpdate]);
  
  const handleDimensionChange = useCallback((dimension) => {
    console.log('🎯 [InteractiveCharts v4.0] Cambiando dimensión:', dimension);
    
    setSelectedDimension(dimension);
    configRef.current = { ...configRef.current, dimension };
    forceUpdate();
    
    if (onChartChange) {
      onChartChange(configRef.current);
    }
  }, [onChartChange, forceUpdate]);
  
  const handleExport = useCallback(async () => {
    try {
      // Create export data
      const exportData = {
        config: currentChartConfig,
        data: processedData,
        timestamp: new Date().toISOString(),
        version: '4.0'
      };
      
      // Download as JSON
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `chart-export-${Date.now()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      notification.success({
        message: 'Gráfico exportado',
        description: 'Configuración y datos exportados correctamente'
      });
    } catch (error) {
      notification.error({
        message: 'Error exportando',
        description: error.message
      });
    }
  }, [currentChartConfig, processedData]);
  
  // ============================================================================
  // ⚡ EFFECTS v4.0
  // ============================================================================
  
  // Inicialización automática
  useEffect(() => {
    if (data?.length && availableDimensions.length && availableMetrics.length) {
      console.log('🎬 [InteractiveCharts v4.0] Inicializando configuración automática...');
      
      // Auto-seleccionar primera dimensión
      if (!selectedDimension && availableDimensions.length > 0) {
        const defaultDimension = availableDimensions[0].type || availableDimensions[0].key;
        setSelectedDimension(defaultDimension);
      }
      
      // Auto-seleccionar métricas
      if (!selectedMetrics.length) {
        if (availableKpis.length > 0) {
          setSelectedMetrics([availableKpis[0]]);
        } else if (availableMetrics.length > 0) {
          const financialMetrics = availableMetrics.filter(m => m.isFinancial);
          setSelectedMetrics([financialMetrics.length > 0 ? financialMetrics[0].key : availableMetrics[0].key]);
        }
      }
      
      // Sugerir mejor tipo de gráfico
      if (selectedDimension && selectedMetrics.length) {
        const dimensionData = availableDimensions.find(d => d.type === selectedDimension || d.key === selectedDimension);
        const suggestedType = suggestBestChartType(processedData, selectedMetrics, dimensionData?.type);
        if (suggestedType !== chartType) {
          setChartType(suggestedType);
        }
      }
    }
  }, [data, availableDimensions, availableMetrics, selectedDimension, selectedMetrics, availableKpis, processedData, chartType]);
  
  // Sincronización con configuración externa
  useEffect(() => {
    if (currentConfig && JSON.stringify(currentConfig) !== JSON.stringify(lastConfigRef.current)) {
      console.log('🔄 [InteractiveCharts v4.0] Sincronizando con configuración externa');
      
      if (currentConfig.chartType && currentConfig.chartType !== chartType) {
        setChartType(currentConfig.chartType);
      }
      
      if (currentConfig.selectedKpi && !selectedMetrics.includes(currentConfig.selectedKpi)) {
        setSelectedMetrics([currentConfig.selectedKpi]);
      }
      
      if (currentConfig.selectedMetrics && JSON.stringify(currentConfig.selectedMetrics) !== JSON.stringify(selectedMetrics)) {
        setSelectedMetrics(currentConfig.selectedMetrics);
      }
      
      if (currentConfig.dimension && currentConfig.dimension !== selectedDimension) {
        setSelectedDimension(currentConfig.dimension);
      }
      
      configRef.current = { ...configRef.current, ...currentConfig };
      lastConfigRef.current = currentConfig;
      forceUpdate();
    }
  }, [currentConfig, chartType, selectedMetrics, selectedDimension, forceUpdate]);
  
  // ============================================================================
  // 🎨 CHART RENDERING v4.0
  // ============================================================================
  
  const renderChart = useCallback(() => {
    if (error) {
      return (
        <Alert
          message="Error en el procesamiento"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" type="primary" onClick={forceUpdate}>
              Reintentar
            </Button>
          }
        />
      );
    }
    
    if (!processedData?.length) {
      return (
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height,
          color: '#666',
          backgroundColor: '#fafafa',
          borderRadius: 8,
          border: '2px dashed #d9d9d9'
        }}>
          <Empty
            image={<BarChartOutlined style={{ fontSize: 48, opacity: 0.3 }} />}
            description={
              <div>
                <div style={{ fontSize: 16, marginBottom: 8 }}>No hay datos disponibles</div>
                <DataStatusIndicator 
                  data={data}
                  selectedDimension={selectedDimension}
                  selectedMetrics={selectedMetrics}
                  connectionState={connectionState}
                />
              </div>
            }
          />
        </div>
      );
    }
    
    const dimensionField = mapDimensionToField(selectedDimension, availableDimensions);
    const chartKey = `${chartType}-${selectedDimension}-${selectedMetrics.join('-')}-${forceRenderKey}`;
    
    console.log('🎨 [InteractiveCharts v4.0] Renderizando:', {
      chartType,
      selectedDimension,
      dimensionField,
      selectedMetrics,
      dataLength: processedData.length
    });
    
    const commonProps = {
      data: processedData,
      margin: { top: 20, right: 30, left: 20, bottom: chartType === 'pie' ? 20 : 100 }
    };
    
    const renderAxis = (dataLength) => ({
      angle: dataLength > 8 ? -45 : 0,
      textAnchor: dataLength > 8 ? "end" : "middle",
      height: dataLength > 8 ? 100 : 60,
      fontSize: 12,
      interval: 0
    });
    
    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer key={chartKey} width="100%" height={height}>
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey={dimensionField}
                {...renderAxis(processedData.length)}
                tick={{ fill: '#666' }}
              />
              <YAxis tick={{ fill: '#666', fontSize: 12 }} />
              {showTooltips && <RechartsTooltip content={<UniversalTooltip />} />}
              {showLegend && <Legend />}
              {selectedMetrics.map((metric, index) => (
                <Bar 
                  key={metric}
                  dataKey={metric} 
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                  name={formatMetricLabel(metric)}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
        
      case 'line':
        return (
          <ResponsiveContainer key={chartKey} width="100%" height={height}>
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey={dimensionField}
                {...renderAxis(processedData.length)}
                tick={{ fill: '#666' }}
              />
              <YAxis tick={{ fill: '#666', fontSize: 12 }} />
              {showTooltips && <RechartsTooltip content={<UniversalTooltip />} />}
              {showLegend && <Legend />}
              {selectedMetrics.map((metric, index) => (
                <Line 
                  key={metric}
                  type="monotone" 
                  dataKey={metric} 
                  stroke={CHART_COLORS[index % CHART_COLORS.length]}
                  strokeWidth={3}
                  dot={{ r: 5, strokeWidth: 2, fill: '#fff' }}
                  activeDot={{ r: 7, strokeWidth: 2 }}
                  name={formatMetricLabel(metric)}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
        
      case 'area':
        return (
          <ResponsiveContainer key={chartKey} width="100%" height={height}>
            <AreaChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey={dimensionField}
                {...renderAxis(processedData.length)}
                tick={{ fill: '#666' }}
              />
              <YAxis tick={{ fill: '#666', fontSize: 12 }} />
              {showTooltips && <RechartsTooltip content={<UniversalTooltip />} />}
              {showLegend && <Legend />}
              {selectedMetrics.map((metric, index) => (
                <Area 
                  key={metric}
                  type="monotone" 
                  dataKey={metric} 
                  stackId={selectedMetrics.length > 1 ? "1" : undefined}
                  stroke={CHART_COLORS[index % CHART_COLORS.length]}
                  fill={CHART_COLORS[index % CHART_COLORS.length]}
                  fillOpacity={0.6}
                  name={formatMetricLabel(metric)}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );
        
      case 'pie':
        const pieMetric = selectedMetrics[0];
        const pieData = processedData
          .slice(0, 8)
          .map((item, index) => ({
            name: item[dimensionField] || `Item ${index + 1}`,
            value: Math.abs(parseFloat(item[pieMetric]) || 0),
            fill: CHART_COLORS[index % CHART_COLORS.length]
          }))
          .filter(item => item.value > 0);
        
        return (
          <ResponsiveContainer key={chartKey} width="100%" height={height}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={Math.min(height * 0.35, 140)}
                innerRadius={Math.min(height * 0.15, 60)}
                dataKey="value"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                labelLine={false}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              {showTooltips && <RechartsTooltip formatter={(value) => [formatValue(value, pieMetric), formatMetricLabel(pieMetric)]} />}
              {showLegend && <Legend />}
            </PieChart>
          </ResponsiveContainer>
        );
        
      case 'scatter':
        const xMetric = selectedMetrics[0];
        const yMetric = selectedMetrics[1] || selectedMetrics[0];
        
        return (
          <ResponsiveContainer key={chartKey} width="100%" height={height}>
            <ScatterChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                type="number"
                dataKey={xMetric}
                name={formatMetricLabel(xMetric)}
                tick={{ fill: '#666', fontSize: 12 }}
              />
              <YAxis 
                type="number"
                dataKey={yMetric}
                name={formatMetricLabel(yMetric)}
                tick={{ fill: '#666', fontSize: 12 }}
              />
              {showTooltips && (
                <RechartsTooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  content={<UniversalTooltip />}
                />
              )}
              <Scatter 
                name="Datos"
                data={processedData}
                fill={CHART_COLORS[0]}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );
        
      default:
        return (
          <Alert 
            message="Tipo de gráfico no soportado" 
            description={`El tipo "${chartType}" no está implementado en v4.0`}
            type="warning" 
            showIcon 
          />
        );
    }
  }, [processedData, chartType, selectedDimension, selectedMetrics, availableDimensions, height, forceRenderKey, error, data, connectionState, showTooltips, showLegend]);
  
  // ============================================================================
  // 🎯 IMPERATIVE HANDLE v4.0
  // ============================================================================
  
  useImperativeHandle(ref, () => ({
    updateChart: (config) => {
      console.log('🔄 [InteractiveCharts v4.0 API] Actualizando:', config);
      
      if (config.chartType && config.chartType !== chartType) {
        setChartType(config.chartType);
      }
      
      if (config.selectedKpi && !selectedMetrics.includes(config.selectedKpi)) {
        setSelectedMetrics([config.selectedKpi]);
      }
      
      if (config.selectedMetrics && JSON.stringify(config.selectedMetrics) !== JSON.stringify(selectedMetrics)) {
        setSelectedMetrics(config.selectedMetrics);
      }
      
      if (config.dimension && config.dimension !== selectedDimension) {
        setSelectedDimension(config.dimension);
      }
      
      if (config.groupingType && config.groupingType !== groupingType) {
        setGroupingType(config.groupingType);
      }
      
      configRef.current = { ...configRef.current, ...config };
      forceUpdate();
      
      if (onChartChange) {
        onChartChange(configRef.current);
      }
    },
    
    // Getters
    get availableDimensions() { return availableDimensions; },
    get availableMetrics() { return availableMetrics; },
    get processedData() { return processedData; },
    get currentConfig() { return currentChartConfig; },
    get version() { return '4.0'; },
    
    // Utility methods
    refresh: forceUpdate,
    suggestChartType: () => {
      const dimensionData = availableDimensions.find(d => d.type === selectedDimension || d.key === selectedDimension);
      return suggestBestChartType(processedData, selectedMetrics, dimensionData?.type);
    },
    getMetrics: () => ({
      dataPoints: processedData.length,
      dimensions: availableDimensions.length,
      metrics: availableMetrics.length,
      chartType,
      connectionState
    }),
    export: handleExport
  }), [
    availableDimensions, availableMetrics, processedData, currentChartConfig, 
    forceUpdate, chartType, selectedMetrics, selectedDimension, groupingType, 
    onChartChange, connectionState, handleExport
  ]);
  
  // ============================================================================
  // 🎨 MAIN RENDER v4.0
  // ============================================================================
  
  return (
    <div style={{ 
      width: '100%', 
      minHeight: height + 200,
      position: isFullscreen ? 'fixed' : 'relative',
      top: isFullscreen ? 0 : 'auto',
      left: isFullscreen ? 0 : 'auto',
      right: isFullscreen ? 0 : 'auto',
      bottom: isFullscreen ? 0 : 'auto',
      zIndex: isFullscreen ? 1000 : 'auto',
      backgroundColor: isFullscreen ? '#fff' : 'transparent'
    }}>
      <Card
        ref={chartRef}
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <Title level={4} style={{ margin: 0, fontSize: 16 }}>{title}</Title>
              {description && (
                <div style={{ fontSize: 12, color: '#666', fontWeight: 'normal', marginTop: 2 }}>
                  {description}
                </div>
              )}
            </div>
            <Space wrap>
              <Tag color="blue">v{version}</Tag>
              <Tag color="green">{availableDimensions.length} dimensiones</Tag>
              <Tag color="orange">{availableMetrics.length} métricas</Tag>
              {conversationalMode && <Tag color="purple">Conversacional</Tag>}
              {executiveMode && <Tag color="gold">Ejecutivo</Tag>}
              {isProcessing && <Spin size="small" />}
            </Space>
          </div>
        }
        extra={
          <Space>
            <Tooltip title="Configuración avanzada">
              <Button 
                size="small" 
                icon={<SettingOutlined />}
                type={showAdvanced ? "primary" : "default"}
                onClick={() => setShowAdvanced(!showAdvanced)}
              />
            </Tooltip>
            
            <Tooltip title="Actualizar gráfico">
              <Button 
                size="small" 
                icon={<ReloadOutlined />}
                onClick={forceUpdate}
                loading={isProcessing}
              />
            </Tooltip>
            
            <Tooltip title="Exportar datos">
              <Button 
                size="small" 
                icon={<DownloadOutlined />}
                onClick={handleExport}
              />
            </Tooltip>
            
            <Tooltip title={isFullscreen ? "Salir pantalla completa" : "Pantalla completa"}>
              <Button 
                size="small" 
                icon={isFullscreen ? <CompressOutlined /> : <FullscreenOutlined />}
                onClick={() => setIsFullscreen(!isFullscreen)}
              />
            </Tooltip>
            
            <Tooltip title={`ChatService: ${connectionState}`}>
              <Button 
                size="small" 
                icon={<ApiOutlined />}
                type={connectionState === CONNECTION_STATES.OPEN ? "primary" : "default"}
              />
            </Tooltip>
          </Space>
        }
        style={{ 
          borderRadius: 8, 
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          border: conversationalMode ? '2px solid #1890ff' : undefined,
          height: isFullscreen ? '100vh' : 'auto'
        }}
      >
        
        {/* Main Controls */}
        <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
          <Col xs={24} lg={6}>
            <div style={{ marginBottom: 8, fontWeight: 600, color: '#333' }}>
              Tipo de Gráfico:
            </div>
            <Radio.Group 
              value={chartType} 
              onChange={handleChartTypeChange}
              optionType="button"
              buttonStyle="solid"
              size="small"
              style={{ width: '100%', display: 'flex', flexWrap: 'wrap' }}
            >
              {Object.entries(CHART_TYPES).map(([key, config]) => (
                <Radio.Button 
                  key={key} 
                  value={key}
                  style={{ 
                    flex: '1 1 auto', 
                    textAlign: 'center',
                    marginBottom: 4,
                    minWidth: '80px'
                  }}
                >
                  <Tooltip title={config.description}>
                    <div>
                      {config.icon}
                      <div style={{ fontSize: 11 }}>{config.label}</div>
                    </div>
                  </Tooltip>
                </Radio.Button>
              ))}
            </Radio.Group>
          </Col>
          
          <Col xs={24} lg={6}>
            <div style={{ marginBottom: 8, fontWeight: 600, color: '#333' }}>
              Dimensión:
            </div>
            <Select
              value={selectedDimension}
              onChange={handleDimensionChange}
              style={{ width: '100%' }}
              placeholder="Seleccionar dimensión..."
              showSearch
              optionFilterProp="children"
              loading={isProcessing}
              // ✅ CORRECCIÓN: Reemplazado dropdownStyle por styles
              styles={SELECT_DROPDOWN_STYLES}
            >
              {availableDimensions.map(dim => (
                <Option key={dim.key} value={dim.type}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Space>
                      <InfoCircleOutlined style={{ color: dim.type === 'periodo' ? '#52c41a' : '#1890ff' }} />
                      <span>{dim.label}</span>
                    </Space>
                    <Tag size="small" color={dim.isUniversal ? "blue" : "default"}>
                      {dim.valueCount} valores
                    </Tag>
                  </div>
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} lg={8}>
            <div style={{ marginBottom: 8, fontWeight: 600, color: '#333' }}>
              Métricas:
            </div>
            <Select
              mode={chartType === 'pie' ? undefined : "multiple"}
              value={selectedMetrics}
              onChange={handleMetricsChange}
              style={{ width: '100%' }}
              placeholder="Seleccionar métricas..."
              showSearch
              optionFilterProp="children"
              maxTagCount={2}
              loading={isProcessing}
              // ✅ CORRECCIÓN: Reemplazado dropdownStyle por styles
              styles={SELECT_DROPDOWN_STYLES}
            >
              {availableMetrics.map(metric => (
                <Option key={metric.key} value={metric.key}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Space>
                      {metric.icon || (
                        <span style={{ color: metric.isFinancial ? '#52c41a' : '#666' }}>
                          {metric.type === 'percentage' && <TrophyFilled />}
                          {metric.type === 'currency' && <DollarOutlined />}
                          {metric.type === 'count' && <RiseOutlined />}
                          {!['percentage', 'currency', 'count'].includes(metric.type) && <BarChartOutlined />}
                        </span>
                      )}
                      <span>{metric.label}</span>
                    </Space>
                    <Tag size="small" color={metric.isFinancial ? "green" : "default"}>
                      {metric.type}
                    </Tag>
                  </div>
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} lg={4}>
            <div style={{ marginBottom: 8, fontWeight: 600, color: '#333' }}>
              Agrupación:
            </div>
            <Select
              value={groupingType}
              onChange={setGroupingType}
              style={{ width: '100%' }}
              size="small"
            >
              <Option value="individual">Individual</Option>
              <Option value="grouped">Agrupado</Option>
            </Select>
          </Col>
        </Row>
        
        {/* Advanced Configuration */}
        {showAdvanced && (
          <Card size="small" style={{ marginBottom: 16, backgroundColor: '#f8f9fa' }}>
            <Row gutter={[16, 8]} align="middle">
              <Col span={6}>
                <DataStatusIndicator 
                  data={data}
                  selectedDimension={selectedDimension}
                  selectedMetrics={selectedMetrics}
                  connectionState={connectionState}
                />
              </Col>
              
              <Col span={6}>
                <Space direction="vertical" size="small">
                  <div>
                    <Text style={{ fontSize: 12 }}>Tooltips:</Text>
                    <Switch 
                      size="small" 
                      checked={showTooltips} 
                      onChange={setShowTooltips}
                      style={{ marginLeft: 8 }}
                    />
                  </div>
                  <div>
                    <Text style={{ fontSize: 12 }}>Leyenda:</Text>
                    <Switch 
                      size="small" 
                      checked={showLegend} 
                      onChange={setShowLegend}
                      style={{ marginLeft: 8 }}
                    />
                  </div>
                </Space>
              </Col>
              
              <Col span={6}>
                <div>
                  <Text style={{ fontSize: 12 }}>Max puntos de datos:</Text>
                  <InputNumber
                    size="small"
                    min={10}
                    max={500}
                    value={maxDataPoints}
                    onChange={setMaxDataPoints}
                    style={{ width: '100%', marginTop: 4 }}
                  />
                </div>
              </Col>
              
              <Col span={6}>
                <div style={{ textAlign: 'right' }}>
                  <Text style={{ fontSize: 11, color: '#666' }}>
                    Última actualización:<br />
                    {new Date(lastUpdate).toLocaleTimeString()}
                  </Text>
                </div>
              </Col>
            </Row>
          </Card>
        )}
        
        {/* Status Info */}
        {showConfigInfo && (
          <div style={{ 
            marginBottom: 16, 
            padding: 12, 
            backgroundColor: '#f0f9ff', 
            borderRadius: 6,
            border: '1px solid #d1ecf1'
          }}>
            <Row justify="space-between" align="middle">
              <Col>
                <Space split={<Divider type="vertical" />} wrap>
                  <Space>
                    <ThunderboltOutlined style={{ color: '#1890ff' }} />
                    <span style={{ fontSize: 12 }}>
                      <strong>Datos:</strong> {processedData.length}
                    </span>
                  </Space>
                  <span style={{ fontSize: 12 }}>
                    <strong>Dimensión:</strong> {formatDimensionLabel(selectedDimension)}
                  </span>
                  <span style={{ fontSize: 12 }}>
                    <strong>Métricas:</strong> {selectedMetrics.map(m => formatMetricLabel(m)).join(', ')}
                  </span>
                  <Space>
                    <ApiOutlined style={{ color: connectionState === CONNECTION_STATES.OPEN ? '#52c41a' : '#faad14' }} />
                    <span style={{ fontSize: 12 }}>
                      <strong>ChatService:</strong> {connectionState}
                    </span>
                  </Space>
                </Space>
              </Col>
              <Col>
                <Badge 
                  status={processedData.length > 0 ? 'success' : 'warning'} 
                  text={
                    <span style={{ fontSize: 11 }}>
                      {processedData.length > 0 ? '✓ v4.0' : '○ Sin datos v4.0'}
                    </span>
                  }
                />
              </Col>
            </Row>
          </div>
        )}
        
        {/* Main Chart */}
        <div style={{ 
          width: '100%', 
          height: isFullscreen ? 'calc(100vh - 300px)' : height, 
          overflow: 'visible',
          position: 'relative'
        }}>
          {isProcessing && (
            <div style={{
              position: 'absolute',
              top: 10,
              right: 10,
              zIndex: 10,
              backgroundColor: 'rgba(255,255,255,0.9)',
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}>
              <Spin size="small" />
              Procesando v4.0...
            </div>
          )}
          {renderChart()}
        </div>
        
      </Card>
    </div>
  );
});

InteractiveCharts.displayName = 'InteractiveCharts';

// ✅ CORRECCIÓN: PropTypes en lugar de defaultProps
InteractiveCharts.propTypes = {
  data: PropTypes.array,
  availableKpis: PropTypes.array,
  title: PropTypes.string,
  description: PropTypes.string,
  onChartChange: PropTypes.func,
  currentConfig: PropTypes.object,
  height: PropTypes.number,
  conversationalMode: PropTypes.bool,
  executiveMode: PropTypes.bool,
  showConfigInfo: PropTypes.bool,
  enableFilters: PropTypes.bool,
  userId: PropTypes.string,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  version: PropTypes.string
};

export default InteractiveCharts;
