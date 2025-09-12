// frontend/src/components/common/FilterBar.jsx
import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Space, Select, Button, Form, Divider, Typography, Tooltip } from 'antd';
import { FilterOutlined, ClearOutlined, BarChartOutlined, ReloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import analyticsService from '../../services/analyticsService';
import theme from '../../styles/theme';

const { Text } = Typography;

/**
 * ✅ HELPER FUNCTIONS - DECLARADAS PRIMERO PARA EVITAR HOISTING ERROR
 */
const getMetricIcon = (metric) => {
  const icons = {
    'CONTRATOS': '📄',
    'CLIENTES': '👥', 
    'MARGEN': '💰',
    'INGRESOS': '💵',
    'VOLUMEN': '📊',
    'ROE': '📈',
    'GASTOS': '💸'
  };
  return icons[metric?.toUpperCase()] || '📈';
};

const getChartTypeLabel = (type) => {
  const labels = {
    'horizontal_bar': 'Barras H.',
    'bar': 'Barras',
    'line': 'Líneas',
    'pie': 'Circular',
    'donut': 'Dona',
    'stacked_bar': 'Barras Apiladas',
    'comparison': 'Comparación'
  };
  return labels[type] || type;
};

/**
 * ✅ FilterBar - COMPLETAMENTE CORREGIDO
 */
const FilterBar = ({
  mode = 'direccion',
  chartType = 'horizontal_bar',
  onChartTypeChange,
  metric = 'CONTRATOS',
  onMetricChange,
  dimension = 'gestor',
  onDimensionChange,
  filters = {},
  onFiltersChange,
  onApply,
  onClear,
  loading = false,
  gestorId = null
}) => {
  // Estados para opciones dinámicas
  const [chartMeta, setChartMeta] = useState(null);
  const [centros, setCentros] = useState([]);
  const [productos, setProductos] = useState([]);
  const [loadingOptions, setLoadingOptions] = useState(false);

  // ✅ CONFIGURACIÓN DINÁMICA SEGÚN EL MODO
  const filterConfig = useMemo(() => {
    if (mode === 'direccion') {
      return {
        title: 'Filtros Dashboard Dirección',
        showDimension: true,
        showCenter: true,
        showProduct: true,
        defaultDimensions: ['gestor', 'centro', 'producto', 'segmento'],
        defaultMetrics: ['CONTRATOS', 'CLIENTES', 'INGRESOS', 'MARGEN'],
        defaultChartTypes: ['horizontal_bar', 'bar', 'donut', 'pie', 'line']
      };
    } else {
      return {
        title: 'Filtros Dashboard Gestor',
        showDimension: false,
        showCenter: false,
        showProduct: true,
        defaultDimensions: [],
        defaultMetrics: ['MARGEN', 'CONTRATOS', 'INGRESOS'],
        defaultChartTypes: ['horizontal_bar', 'bar', 'donut', 'comparison']
      };
    }
  }, [mode]);

  // ✅ OPCIONES DINÁMICAS - USANDO FUNCIONES YA DECLARADAS
  const metricOptions = useMemo(() => {
    const dynamicMetrics = chartMeta?.metrics || {};
    const fallbackMetrics = {
      'CONTRATOS': 'Contratos',
      'CLIENTES': 'Clientes',
      'MARGEN': 'Margen',
      'INGRESOS': 'Ingresos'
    };

    const metricsToUse = Object.keys(dynamicMetrics).length > 0 ? dynamicMetrics : fallbackMetrics;
    
    return Object.entries(metricsToUse)
      .filter(([key]) => filterConfig.defaultMetrics.includes(key))
      .map(([value, label]) => ({
        label: label || value,
        value: value.toUpperCase(),
        icon: getMetricIcon(value) // ✅ FUNCIÓN YA DECLARADA
      }));
  }, [chartMeta, filterConfig.defaultMetrics]);

  const chartTypeOptions = useMemo(() => {
    const dynamicTypes = chartMeta?.charttypes || [];
    const fallbackTypes = ['horizontal_bar', 'bar', 'donut', 'pie', 'line'];
    
    const typesToUse = dynamicTypes.length > 0 ? dynamicTypes : fallbackTypes;
    
    return typesToUse
      .filter(type => filterConfig.defaultChartTypes.includes(type))
      .map(type => ({
        label: getChartTypeLabel(type), // ✅ FUNCIÓN YA DECLARADA
        value: type
      }));
  }, [chartMeta, filterConfig.defaultChartTypes]);

  const dimensionOptions = useMemo(() => {
    if (!filterConfig.showDimension) return [];

    const dynamicDimensions = chartMeta?.dimensions || {};
    const fallbackDimensions = {
      'gestor': 'Gestor',
      'centro': 'Centro', 
      'producto': 'Producto',
      'segmento': 'Segmento'
    };

    const dimensionsToUse = Object.keys(dynamicDimensions).length > 0 ? dynamicDimensions : fallbackDimensions;
    
    return Object.entries(dimensionsToUse)
      .filter(([key]) => filterConfig.defaultDimensions.includes(key))
      .map(([value, label]) => ({
        label: label || value,
        value
      }));
  }, [chartMeta, filterConfig.showDimension, filterConfig.defaultDimensions]);

  // ✅ CARGAR METADATOS
  const loadChartMeta = useCallback(async () => {
    try {
      console.log('[FilterBar] 🔍 Loading chart metadata...');
      const meta = await analyticsService.getChartMeta()(); // ✅ CAMBIO AQUÍ
      setChartMeta(meta);
      console.log('[FilterBar] ✅ Chart metadata loaded');
    } catch (error) {
      console.warn('[FilterBar] ⚠️ Error loading chart meta, using fallbacks:', error.message);
    }
  }, []);

  // ✅ CARGAR CENTROS
  const loadCentros = useCallback(async () => {
    if (!filterConfig.showCenter) return;

    try {
      console.log('[FilterBar] 🏢 Loading centros...');
      const data = await api.basic.centros() || await api.basic.centros() || [];
      const centrosList = Array.isArray(data) ? data.map((centro, index) => ({
        label: centro.DESC_CENTRO || centro.DESCCENTRO || centro.nombre || `Centro ${centro.CENTRO_ID || centro.CENTROID || index}`,
        value: centro.CENTRO_ID || centro.CENTROID || centro.id || index,
      })).filter(centro => centro.label && centro.value) : [];
      
      setCentros(centrosList);
      console.log('[FilterBar] ✅ Centros loaded:', centrosList.length);
    } catch (error) {
      console.warn('[FilterBar] ⚠️ Error cargando centros:', error.message);
      setCentros([]);
    }
  }, [filterConfig.showCenter]);

  // ✅ CARGAR PRODUCTOS
  const loadProductos = useCallback(async () => {
    if (!filterConfig.showProduct) return;

    try {
      console.log('[FilterBar] 📦 Loading productos...');
      const data = await api.basic.productos() || await api.basic.productos() || [];
      const productosList = Array.isArray(data) ? data.map((producto, index) => ({
        label: producto.DESC_PRODUCTO || producto.DESCPRODUCTO || producto.nombre || `Producto ${producto.PRODUCTO_ID || producto.PRODUCTOID || index}`,
        value: producto.PRODUCTO_ID || producto.PRODUCTOID || producto.id || index,
      })).filter(producto => producto.label && producto.value) : [];
      
      setProductos(productosList);
      console.log('[FilterBar] ✅ Productos loaded:', productosList.length);
    } catch (error) {
      console.warn('[FilterBar] ⚠️ Error cargando productos:', error.message);
      setProductos([]);
    }
  }, [filterConfig.showProduct]);

  // ✅ CARGAR OPCIONES INICIALES
  useEffect(() => {
    const loadOptions = async () => {
      console.log(`[FilterBar] 🚀 Loading options for mode: ${mode}`);
      setLoadingOptions(true);
      
      await Promise.all([
        loadChartMeta(),
        loadCentros(),
        loadProductos(),
      ]);
      
      setLoadingOptions(false);
      console.log('[FilterBar] ✅ All options loaded');
    };

    loadOptions();
  }, [mode, loadChartMeta, loadCentros, loadProductos]);

  // ✅ MANEJADORES DE EVENTOS
  const handleFilterChange = useCallback((key, value) => {
    console.log(`[FilterBar] 🔄 Filter change: ${key} = ${value}`);
    if (onFiltersChange) {
      onFiltersChange({
        ...filters,
        [key]: value === undefined ? null : value,
      });
    }
  }, [filters, onFiltersChange]);

  const handleMetricChange = useCallback((value) => {
    console.log(`[FilterBar] 📊 Metric change: ${value}`);
    if (onMetricChange) {
      onMetricChange(value.toUpperCase());
    }
  }, [onMetricChange]);

  const handleChartTypeChange = useCallback((value) => {
    console.log(`[FilterBar] 📈 Chart type change: ${value}`);
    if (onChartTypeChange) {
      onChartTypeChange(value);
    }
  }, [onChartTypeChange]);

  const handleDimensionChange = useCallback((value) => {
    console.log(`[FilterBar] 🎯 Dimension change: ${value}`);
    if (onDimensionChange) {
      onDimensionChange(value);
    }
  }, [onDimensionChange]);

  const handleClearAll = useCallback(() => {
    console.log('[FilterBar] 🧹 Clearing all filters');
    if (onFiltersChange && onClear) {
      const clearedFilters = {
        centro: null,
        producto: null,
      };
      onFiltersChange(clearedFilters);
      onClear();
    }
  }, [onFiltersChange, onClear]);

  const handleRefreshOptions = useCallback(async () => {
    console.log('[FilterBar] 🔄 Refreshing options');
    setLoadingOptions(true);
    
    // Limpiar cache si disponible
    if (analyticsService.clearAnalyticsCache) {
      analyticsService.clearAnalyticsCache();
    }
    
    await Promise.all([
      loadChartMeta(),
      loadCentros(),
      loadProductos(),
    ]);
    
    setLoadingOptions(false);
  }, [loadChartMeta, loadCentros, loadProductos]);

  // ✅ ESTILOS SEGUROS
  const containerStyle = {
    padding: `${theme.spacing?.sm || 12}px ${theme.spacing?.md || 16}px`,
    backgroundColor: theme.colors?.background || '#fafafa',
    borderRadius: theme.token?.borderRadius || 8,
    border: `1px solid ${theme.colors?.borderLight || '#e8e8e8'}`,
    boxShadow: '0 2px 8px rgba(27, 94, 85, 0.08)',
    marginBottom: theme.spacing?.md || 16,
  };

  // ✅ VALIDACIÓN DE OPCIONES
  const hasValidMetricOptions = metricOptions.length > 0;
  const hasValidChartTypeOptions = chartTypeOptions.length > 0;

  if (!hasValidMetricOptions || !hasValidChartTypeOptions) {
    return (
      <div style={containerStyle}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, padding: 20 }}>
          <BarChartOutlined style={{ color: theme.colors?.textSecondary || '#999' }} />
          <Text type="secondary">Cargando opciones de filtros...</Text>
          <Button 
            size="small" 
            icon={<ReloadOutlined />} 
            onClick={handleRefreshOptions}
            loading={loadingOptions}
          >
            Reintentar
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <Form layout="inline">
        <Space align="center" size="middle" wrap>
          {/* Header con indicador de modo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChartOutlined style={{ color: theme.colors?.bmGreenPrimary || '#1890ff' }} />
            <Text strong style={{ color: theme.colors?.bmGreenPrimary || '#1890ff' }}>
              {filterConfig.title}
            </Text>
            {gestorId && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                (Gestor: {gestorId})
              </Text>
            )}
          </div>

          <Divider type="vertical" style={{ height: 24 }} />

          {/* ✅ SELECTOR DE MÉTRICA */}
          <Form.Item label="Métrica" style={{ marginBottom: 0 }}>
            <Select
              value={metric?.toUpperCase()}
              onChange={handleMetricChange}
              size="middle"
              style={{ minWidth: 130 }}
              placeholder="Métrica"
              loading={loadingOptions}
            >
              {metricOptions.map(option => (
                <Select.Option key={option.value} value={option.value}>
                  <Space>
                    <span>{option.icon}</span>
                    {option.label}
                  </Space>
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          {/* ✅ SELECTOR DE TIPO DE GRÁFICO */}
          <Form.Item label="Gráfico" style={{ marginBottom: 0 }}>
            <Select
              value={chartType}
              onChange={handleChartTypeChange}
              size="middle"
              style={{ minWidth: 130 }}
              placeholder="Tipo"
              loading={loadingOptions}
              options={chartTypeOptions}
            />
          </Form.Item>

          {/* ✅ SELECTOR DE DIMENSIÓN (SOLO DASHBOARD DIRECCIÓN) */}
          {filterConfig.showDimension && (
            <Form.Item label="Dimensión" style={{ marginBottom: 0 }}>
              <Select
                value={dimension}
                onChange={handleDimensionChange}
                size="middle"
                style={{ minWidth: 120 }}
                placeholder="Dimensión"
                loading={loadingOptions}
                options={dimensionOptions}
              />
            </Form.Item>
          )}

          <Divider type="vertical" style={{ height: 24 }} />

          {/* ✅ SELECTOR DE CENTRO (SOLO DASHBOARD DIRECCIÓN) */}
          {filterConfig.showCenter && (
            <Form.Item label="Centro" style={{ marginBottom: 0 }}>
              <Select
                showSearch
                allowClear
                placeholder="Todos los centros"
                value={filters.centro || undefined}
                onChange={(value) => handleFilterChange('centro', value)}
                size="middle"
                style={{ minWidth: 180 }}
                loading={loadingOptions}
                filterOption={(input, option) =>
                  option?.label?.toLowerCase().includes(input.toLowerCase())
                }
                notFoundContent={loadingOptions ? "Cargando..." : "Sin resultados"}
                options={centros}
              />
            </Form.Item>
          )}

          {/* ✅ SELECTOR DE PRODUCTO */}
          {filterConfig.showProduct && (
            <Form.Item label="Producto" style={{ marginBottom: 0 }}>
              <Select
                showSearch
                allowClear
                placeholder="Todos los productos"
                value={filters.producto || undefined}
                onChange={(value) => handleFilterChange('producto', value)}
                size="middle"
                style={{ minWidth: 200 }}
                loading={loadingOptions}
                filterOption={(input, option) =>
                  option?.label?.toLowerCase().includes(input.toLowerCase())
                }
                notFoundContent={loadingOptions ? "Cargando..." : "Sin resultados"}
                options={productos}
              />
            </Form.Item>
          )}

          <Divider type="vertical" style={{ height: 24 }} />

          {/* ✅ BOTONES DE ACCIÓN */}
          <Space size="small">
            <Tooltip title="Aplicar filtros seleccionados">
              <Button
                type="primary"
                icon={<FilterOutlined />}
                onClick={onApply}
                loading={loading}
                style={{
                  backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff',
                  borderColor: theme.colors?.bmGreenPrimary || '#1890ff',
                }}
              >
                Aplicar
              </Button>
            </Tooltip>

            <Tooltip title="Limpiar todos los filtros">
              <Button
                icon={<ClearOutlined />}
                onClick={handleClearAll}
                disabled={loading}
              >
                Limpiar
              </Button>
            </Tooltip>

            <Tooltip title="Recargar opciones de filtros">
              <Button
                size="small"
                icon={<ReloadOutlined />}
                onClick={handleRefreshOptions}
                loading={loadingOptions}
                style={{ marginLeft: 8 }}
              />
            </Tooltip>
          </Space>
        </Space>
      </Form>
    </div>
  );
};

// ✅ PROPTYPES COMPLETOS
FilterBar.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']),
  chartType: PropTypes.oneOf(['horizontal_bar', 'bar', 'line', 'pie', 'donut', 'stacked_bar', 'comparison']),
  onChartTypeChange: PropTypes.func.isRequired,
  metric: PropTypes.oneOf(['CONTRATOS', 'CLIENTES', 'MARGEN', 'INGRESOS', 'VOLUMEN']),
  onMetricChange: PropTypes.func.isRequired,
  dimension: PropTypes.oneOf(['gestor', 'centro', 'producto', 'segmento']),
  onDimensionChange: PropTypes.func,
  filters: PropTypes.shape({
    centro: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    producto: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }),
  onFiltersChange: PropTypes.func.isRequired,
  onApply: PropTypes.func.isRequired,
  onClear: PropTypes.func.isRequired,
  loading: PropTypes.bool,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
};

export default FilterBar;
