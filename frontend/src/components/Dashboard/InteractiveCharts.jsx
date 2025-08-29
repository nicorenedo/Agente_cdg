// src/components/Dashboard/InteractiveCharts.jsx
// Componente para gráficos interactivos - CORREGIDO: defaultProps + Card deprecated props

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Radio, Select, Tooltip, Row, Col, Spin, Alert, Button, Space } from 'antd';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  Legend, ResponsiveContainer 
} from 'recharts';
import { InfoCircleOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import theme from '../../styles/theme';

const { Option } = Select;

// Colores corporativos de Banca March para gráficos
const CHART_COLORS = [
  theme.colors.bmGreenPrimary,
  theme.colors.bmGreenLight,
  theme.colors.bmGreenDark,
  '#4CAF50',
  '#FF9800',
  '#2196F3',
  '#9C27B0',
  '#607D8B'
];

// Tipos de gráficos disponibles
const CHART_TYPES = {
  bar: 'Barras',
  line: 'Línea',
  area: 'Área',
  pie: 'Circular'
};

// KPIs disponibles con formateo
const KPI_FORMATS = {
  ROE: { suffix: '%', decimals: 2, label: 'ROE' },
  MARGEN_NETO: { suffix: '%', decimals: 2, label: 'Margen Neto' },
  TOTAL_INGRESOS: { prefix: '€', decimals: 0, thousands: true, label: 'Total Ingresos' },
  TOTAL_GASTOS: { prefix: '€', decimals: 0, thousands: true, label: 'Total Gastos' },
  BENEFICIO_NETO: { prefix: '€', decimals: 0, thousands: true, label: 'Beneficio Neto' }
};

// Función para formatear valores según el KPI
const formatValue = (value, kpiKey) => {
  if (value === null || value === undefined || isNaN(value)) return '--';
  
  const format = KPI_FORMATS[kpiKey] || { decimals: 2 };
  let formattedValue = Number(value).toFixed(format.decimals);
  
  if (format.thousands) {
    formattedValue = Number(formattedValue).toLocaleString('es-ES');
  }
  
  return `${format.prefix || ''}${formattedValue}${format.suffix || ''}`;
};

// Función para obtener label del KPI
const getKpiLabel = (kpiKey) => {
  return KPI_FORMATS[kpiKey]?.label || kpiKey.replace(/_/g, ' ').toUpperCase();
};

// Tooltip personalizado para los gráficos
const CustomTooltip = ({ active, payload, label, selectedKpi }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: '#fff',
        padding: '12px',
        border: `1px solid ${theme.colors.border}`,
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        maxWidth: '200px'
      }}>
        <p style={{ 
          margin: 0, 
          fontWeight: 600, 
          color: theme.colors.textPrimary,
          fontSize: '13px',
          marginBottom: '4px'
        }}>
          {label}
        </p>
        {payload.map((entry, index) => (
          <p key={index} style={{ 
            margin: '2px 0', 
            color: entry.color,
            fontSize: '12px'
          }}>
            {`${getKpiLabel(entry.dataKey)}: ${formatValue(entry.value, entry.dataKey)}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

CustomTooltip.propTypes = {
  active: PropTypes.bool,
  payload: PropTypes.array,
  label: PropTypes.string,
  selectedKpi: PropTypes.string
};

// ✅ CORRECCIÓN: Usar parámetros por defecto ES6 en lugar de defaultProps
const InteractiveCharts = ({ 
  data = [], 
  availableKpis = ['ROE', 'MARGEN_NETO', 'TOTAL_INGRESOS', 'TOTAL_GASTOS', 'BENEFICIO_NETO'], 
  title = 'Análisis de KPIs', 
  description = 'Visualización interactiva de indicadores clave de performance',
  onChartChange,
  gestorId,
  periodo,
  autoRefresh = false,
  showMultipleKpis = false,
  height = 350
}) => {
  // Estados principales
  const [chartType, setChartType] = useState('bar');
  const [selectedKpi, setSelectedKpi] = useState(availableKpis?.[0] || 'ROE');
  const [selectedKpis, setSelectedKpis] = useState(availableKpis?.slice(0, 3) || ['ROE']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Estados de datos
  const [chartData, setChartData] = useState(data || []);
  const [availableKpisState, setAvailableKpisState] = useState(availableKpis || []);

  // Cargar datos con campos en mayúsculas
  const fetchChartData = useCallback(async () => {
    if (!gestorId && !periodo) return;

    setLoading(true);
    setError(null);

    try {
      let response;
      
      if (gestorId) {
        // Datos específicos del gestor
        response = await api.getGestorPerformance(gestorId, periodo || '2025-10');
        
        if (response.data?.kpis) {
          const gestorData = [{
            DESC_GESTOR: response.data.gestor?.nombre || 'Gestor',
            ...response.data.kpis
          }];
          setChartData(gestorData);
          setAvailableKpisState(Object.keys(response.data.kpis));
        }
      } else {
        // Datos comparativos
        try {
          response = await api.getComparativeRanking(periodo || '2025-10', 'MARGEN_NETO');
          
          if (response.data?.ranking) {
            const rankingData = response.data.ranking.map(item => ({
              DESC_GESTOR: item.DESC_GESTOR || 'Gestor',
              DESC_CENTRO: item.DESC_CENTRO || 'Centro',
              ROE: item.ROE || 0,
              MARGEN_NETO: item.MARGEN_NETO || 0,
              TOTAL_INGRESOS: item.TOTAL_INGRESOS || 0,
              TOTAL_GASTOS: item.TOTAL_GASTOS || 0,
              BENEFICIO_NETO: item.BENEFICIO_NETO || 0
            }));
            
            setChartData(rankingData);
            setAvailableKpisState(['ROE', 'MARGEN_NETO', 'TOTAL_INGRESOS', 'TOTAL_GASTOS', 'BENEFICIO_NETO']);
          }
        } catch (rankingError) {
          console.warn('Endpoint comparative/ranking no disponible, usando análisis comparativo:', rankingError);
          
          // Fallback usando análisis comparativo
          const comparativoResponse = await api.getAnalisisComparativo(periodo || '2025-10');
          if (comparativoResponse.data?.gestores) {
            const gestoresData = comparativoResponse.data.gestores.map(item => ({
              DESC_GESTOR: item.DESC_GESTOR || 'Gestor',
              DESC_CENTRO: item.DESC_CENTRO || 'Centro',
              ROE: item.ROE || 0,
              MARGEN_NETO: item.MARGEN_NETO || 0,
              TOTAL_INGRESOS: item.TOTAL_INGRESOS || 0,
              TOTAL_GASTOS: item.TOTAL_GASTOS || 0,
              BENEFICIO_NETO: item.BENEFICIO_NETO || 0
            }));
            
            setChartData(gestoresData);
            setAvailableKpisState(['ROE', 'MARGEN_NETO', 'TOTAL_INGRESOS', 'TOTAL_GASTOS', 'BENEFICIO_NETO']);
          }
        }
      }

    } catch (error) {
      console.error('Error cargando datos del gráfico:', error);
      setError('Error al cargar datos del gráfico');
      
      // Usar datos de props como fallback
      if (data && data.length > 0) {
        setChartData(data);
        setAvailableKpisState(availableKpis || []);
      }
    } finally {
      setLoading(false);
    }
  }, [gestorId, periodo, data, availableKpis]);

  // Efectos
  useEffect(() => {
    if (data && data.length > 0) {
      setChartData(data);
      setAvailableKpisState(availableKpis || []);
    } else {
      fetchChartData();
    }
  }, [data, availableKpis, fetchChartData]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchChartData, 30000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchChartData]);

  // Handlers
  const handleChartTypeChange = (e) => {
    const newType = e.target.value;
    setChartType(newType);
    if (onChartChange) {
      onChartChange({ chartType: newType, selectedKpi, selectedKpis });
    }
  };

  const handleKpiChange = (kpi) => {
    setSelectedKpi(kpi);
    if (onChartChange) {
      onChartChange({ chartType, selectedKpi: kpi, selectedKpis });
    }
  };

  const handleMultipleKpisChange = (kpis) => {
    setSelectedKpis(kpis);
    if (onChartChange) {
      onChartChange({ chartType, selectedKpi, selectedKpis: kpis });
    }
  };

  // Preparar datos para gráficos
  const getFilteredData = () => {
    if (!chartData || chartData.length === 0) return [];

    if (showMultipleKpis) {
      return chartData.filter(item => 
        selectedKpis.some(kpi => 
          item[kpi] !== null && item[kpi] !== undefined && !isNaN(item[kpi])
        )
      );
    } else {
      return chartData.filter(item => 
        item[selectedKpi] !== null && item[selectedKpi] !== undefined && !isNaN(item[selectedKpi])
      );
    }
  };

  const filteredData = getFilteredData();

  // Función para exportar datos
  const exportData = () => {
    const csvData = filteredData.map(item => {
      const row = { Gestor: item.DESC_GESTOR || item.nombre || 'N/A' };
      if (showMultipleKpis) {
        selectedKpis.forEach(kpi => {
          row[getKpiLabel(kpi)] = formatValue(item[kpi], kpi);
        });
      } else {
        row[getKpiLabel(selectedKpi)] = formatValue(item[selectedKpi], selectedKpi);
      }
      return row;
    });

    if (csvData.length === 0) return;

    const csvContent = "data:text/csv;charset=utf-8," 
      + Object.keys(csvData[0]).join(",") + "\n"
      + csvData.map(row => Object.values(row).join(",")).join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `grafico_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Renderizar gráfico según tipo seleccionado
  const renderChart = () => {
    if (loading) {
      return (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: height 
        }}>
          <Spin size="large" />
        </div>
      );
    }

    if (error) {
      return (
        <Alert
          message="Error al cargar el gráfico"
          description={error}
          type="error"
          showIcon
          style={{ margin: '20px 0' }}
          action={
            <Button size="small" onClick={fetchChartData}>
              Reintentar
            </Button>
          }
        />
      );
    }

    if (!filteredData.length) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          height: height,
          color: theme.colors.textSecondary
        }}>
          <div style={{ fontSize: '16px', marginBottom: '8px' }}>
            No hay datos disponibles para mostrar
          </div>
          <div style={{ fontSize: '12px' }}>
            Verifica los filtros seleccionados o la conexión con el backend
          </div>
        </div>
      );
    }

    const commonProps = {
      data: filteredData,
      margin: { top: 20, right: 30, left: 20, bottom: chartType === 'pie' ? 5 : 60 }
    };

    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} />
              <XAxis 
                dataKey="DESC_GESTOR" 
                angle={-45}
                textAnchor="end"
                height={80}
                fontSize={12}
                interval={0}
              />
              <YAxis fontSize={12} />
              <RechartsTooltip content={<CustomTooltip selectedKpi={selectedKpi} />} />
              <Legend />
              
              {showMultipleKpis ? (
                selectedKpis.map((kpi, index) => (
                  <Bar 
                    key={kpi}
                    dataKey={kpi} 
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                    name={getKpiLabel(kpi)}
                  />
                ))
              ) : (
                <Bar 
                  dataKey={selectedKpi} 
                  fill={theme.colors.bmGreenLight}
                  name={getKpiLabel(selectedKpi)}
                />
              )}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} />
              <XAxis 
                dataKey="DESC_GESTOR" 
                angle={-45}
                textAnchor="end"
                height={80}
                fontSize={12}
                interval={0}
              />
              <YAxis fontSize={12} />
              <RechartsTooltip content={<CustomTooltip selectedKpi={selectedKpi} />} />
              <Legend />
              
              {showMultipleKpis ? (
                selectedKpis.map((kpi, index) => (
                  <Line 
                    key={kpi}
                    type="monotone" 
                    dataKey={kpi} 
                    stroke={CHART_COLORS[index % CHART_COLORS.length]}
                    strokeWidth={3}
                    dot={{ r: 4 }}
                    activeDot={{ r: 6 }}
                    name={getKpiLabel(kpi)}
                  />
                ))
              ) : (
                <Line 
                  type="monotone" 
                  dataKey={selectedKpi} 
                  stroke={theme.colors.bmGreenPrimary}
                  strokeWidth={3}
                  dot={{ fill: theme.colors.bmGreenPrimary, r: 4 }}
                  activeDot={{ r: 6, fill: theme.colors.bmGreenDark }}
                  name={getKpiLabel(selectedKpi)}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} />
              <XAxis 
                dataKey="DESC_GESTOR" 
                angle={-45}
                textAnchor="end"
                height={80}
                fontSize={12}
                interval={0}
              />
              <YAxis fontSize={12} />
              <RechartsTooltip content={<CustomTooltip selectedKpi={selectedKpi} />} />
              <Legend />
              
              {showMultipleKpis ? (
                selectedKpis.map((kpi, index) => (
                  <Area
                    key={kpi}
                    type="monotone"
                    dataKey={kpi}
                    stackId="1"
                    stroke={CHART_COLORS[index % CHART_COLORS.length]}
                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                    fillOpacity={0.6}
                    name={getKpiLabel(kpi)}
                  />
                ))
              ) : (
                <Area
                  type="monotone"
                  dataKey={selectedKpi}
                  stroke={theme.colors.bmGreenPrimary}
                  fill={theme.colors.bmGreenLight}
                  fillOpacity={0.6}
                  name={getKpiLabel(selectedKpi)}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pie':
        const pieData = filteredData.slice(0, 8).map((item, index) => ({
          name: item.DESC_GESTOR || `Item ${index + 1}`,
          value: item[selectedKpi] || 0,
          fill: CHART_COLORS[index % CHART_COLORS.length]
        }));

        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={Math.min(height * 0.3, 120)}
                fill={theme.colors.bmGreenPrimary}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <RechartsTooltip 
                formatter={(value) => formatValue(value, selectedKpi)}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: theme.colors.textPrimary, fontSize: '16px', fontWeight: 600 }}>
              {title}
            </span>
            {description && (
              <Tooltip title={description}>
                <InfoCircleOutlined style={{ color: theme.colors.bmGreenLight }} />
              </Tooltip>
            )}
          </div>
          <Space>
            {autoRefresh && (
              <Button 
                size="small" 
                icon={<ReloadOutlined />} 
                onClick={fetchChartData}
                loading={loading}
              >
                Actualizar
              </Button>
            )}
            <Button 
              size="small" 
              icon={<DownloadOutlined />} 
              onClick={exportData}
              disabled={!filteredData.length}
            >
              Exportar
            </Button>
          </Space>
        </div>
      }
      variant="outlined"
      style={{
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        marginBottom: theme.spacing.lg
      }}
    >
      {/* Controles de gráfico */}
      <Row justify="space-between" align="middle" style={{ marginBottom: theme.spacing.md }}>
        <Col>
          <Radio.Group 
            value={chartType} 
            onChange={handleChartTypeChange}
            optionType="button"
            buttonStyle="solid"
            size="small"
          >
            {Object.entries(CHART_TYPES).map(([key, label]) => (
              <Radio.Button key={key} value={key}>
                {label}
              </Radio.Button>
            ))}
          </Radio.Group>
        </Col>
        
        <Col>
          {showMultipleKpis ? (
            <Select
              mode="multiple"
              value={selectedKpis}
              onChange={handleMultipleKpisChange}
              style={{ width: 250 }}
              placeholder="Seleccionar KPIs"
              maxTagCount={2}
            >
              {availableKpisState.map(kpi => (
                <Option key={kpi} value={kpi}>
                  {getKpiLabel(kpi)}
                </Option>
              ))}
            </Select>
          ) : (
            <Select
              value={selectedKpi}
              onChange={handleKpiChange}
              style={{ width: 200 }}
              placeholder="Seleccionar KPI"
            >
              {availableKpisState.map(kpi => (
                <Option key={kpi} value={kpi}>
                  {getKpiLabel(kpi)}
                </Option>
              ))}
            </Select>
          )}
        </Col>
      </Row>

      {/* Información de datos */}
      <div style={{ 
        marginBottom: theme.spacing.sm, 
        fontSize: '12px', 
        color: theme.colors.textSecondary 
      }}>
        Mostrando {filteredData.length} de {chartData.length} elementos
        {gestorId && ` • Gestor: ${gestorId}`}
        {periodo && ` • Período: ${periodo}`}
      </div>

      {/* Gráfico */}
      {renderChart()}
    </Card>
  );
};

InteractiveCharts.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object),
  availableKpis: PropTypes.arrayOf(PropTypes.string),
  title: PropTypes.string,
  description: PropTypes.string,
  onChartChange: PropTypes.func,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  autoRefresh: PropTypes.bool,
  showMultipleKpis: PropTypes.bool,
  height: PropTypes.number
};

// ✅ CORRECCIÓN: Eliminado InteractiveCharts.defaultProps completamente

export default InteractiveCharts;
