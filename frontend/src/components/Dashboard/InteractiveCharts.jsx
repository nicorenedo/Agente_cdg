// src/components/Dashboard/InteractiveCharts.jsx
// Componente para gráficos interactivos dinámicos con Recharts

import React, { useState } from 'react';
import { Card, Radio, Select, Tooltip, Row, Col } from 'antd';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, 
  Legend, ResponsiveContainer 
} from 'recharts';
import { InfoCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import theme from '../../styles/theme';

const { Option } = Select;

// Colores corporativos de Banca March para gráficos
const CHART_COLORS = [
  theme.colors.bmGreenPrimary,
  theme.colors.bmGreenLight,
  theme.colors.bmGreenDark,
  '#4CAF50',
  '#FF9800',
  '#2196F3'
];

// Tipos de gráficos disponibles
const CHART_TYPES = {
  bar: 'Barras',
  line: 'Línea',
  pie: 'Circular'
};

// Configuración de KPIs para formateo
const KPI_FORMATS = {
  roe: { suffix: '%', decimals: 2 },
  margen_neto: { suffix: '%', decimals: 2 },
  eficiencia: { suffix: '%', decimals: 1 },
  total_ingresos: { prefix: '€', decimals: 0, thousands: true },
  total_gastos: { prefix: '€', decimals: 0, thousands: true }
};

// Función para formatear valores según el KPI
const formatValue = (value, kpiKey) => {
  if (value === null || value === undefined) return '--';
  
  const format = KPI_FORMATS[kpiKey] || { decimals: 2 };
  let formattedValue = Number(value).toFixed(format.decimals);
  
  if (format.thousands) {
    formattedValue = Number(formattedValue).toLocaleString('es-ES');
  }
  
  return `${format.prefix || ''}${formattedValue}${format.suffix || ''}`;
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
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <p style={{ 
          margin: 0, 
          fontWeight: 600, 
          color: theme.colors.textPrimary 
        }}>
          {label}
        </p>
        <p style={{ 
          margin: '4px 0 0 0', 
          color: payload[0].color 
        }}>
          {`${selectedKpi}: ${formatValue(payload[0].value, selectedKpi)}`}
        </p>
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

// Componente principal InteractiveCharts
const InteractiveCharts = ({ 
  data, 
  availableKpis, 
  title, 
  description,
  onChartChange 
}) => {
  const [chartType, setChartType] = useState('bar');
  const [selectedKpi, setSelectedKpi] = useState(availableKpis[0] || '');

  // Manejar cambio de tipo de gráfico
  const handleChartTypeChange = (e) => {
    const newType = e.target.value;
    setChartType(newType);
    if (onChartChange) {
      onChartChange({ chartType: newType, selectedKpi });
    }
  };

  // Manejar cambio de KPI seleccionado
  const handleKpiChange = (kpi) => {
    setSelectedKpi(kpi);
    if (onChartChange) {
      onChartChange({ chartType, selectedKpi: kpi });
    }
  };

  // Preparar datos para gráficos
  const chartData = data.filter(item => item[selectedKpi] !== null && item[selectedKpi] !== undefined);

  // Renderizar gráfico según tipo seleccionado
  const renderChart = () => {
    if (!chartData.length) {
      return (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '300px',
          color: theme.colors.textSecondary
        }}>
          No hay datos disponibles para mostrar
        </div>
      );
    }

    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart 
              data={chartData} 
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="desc_gestor" 
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis />
              <RechartsTooltip 
                content={<CustomTooltip selectedKpi={selectedKpi} />}
              />
              <Legend />
              <Bar 
                dataKey={selectedKpi} 
                fill={theme.colors.bmGreenLight}
                name={selectedKpi.replace('_', ' ').toUpperCase()}
              />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart 
              data={chartData} 
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="desc_gestor" 
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis />
              <RechartsTooltip 
                content={<CustomTooltip selectedKpi={selectedKpi} />}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey={selectedKpi} 
                stroke={theme.colors.bmGreenPrimary}
                strokeWidth={3}
                dot={{ fill: theme.colors.bmGreenPrimary, r: 4 }}
                activeDot={{ r: 6, fill: theme.colors.bmGreenDark }}
                name={selectedKpi.replace('_', ' ').toUpperCase()}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        // Para pie chart, usar solo los primeros 8 elementos para legibilidad
        const pieData = chartData.slice(0, 8).map((item, index) => ({
          name: item.desc_gestor || `Item ${index + 1}`,
          value: item[selectedKpi],
          fill: CHART_COLORS[index % CHART_COLORS.length]
        }));

        return (
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: theme.colors.textPrimary, fontSize: '16px', fontWeight: 600 }}>
            {title || 'Gráfico Interactivo'}
          </span>
          {description && (
            <Tooltip title={description}>
              <InfoCircleOutlined style={{ color: theme.colors.bmGreenLight }} />
            </Tooltip>
          )}
        </div>
      }
      bordered={false}
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
          >
            {Object.entries(CHART_TYPES).map(([key, label]) => (
              <Radio.Button key={key} value={key}>
                {label}
              </Radio.Button>
            ))}
          </Radio.Group>
        </Col>
        
        <Col>
          <Select
            value={selectedKpi}
            onChange={handleKpiChange}
            style={{ width: 200 }}
            placeholder="Seleccionar KPI"
          >
            {availableKpis.map(kpi => (
              <Option key={kpi} value={kpi}>
                {kpi.replace('_', ' ').toUpperCase()}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      {/* Gráfico */}
      {renderChart()}
    </Card>
  );
};

InteractiveCharts.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  availableKpis: PropTypes.arrayOf(PropTypes.string).isRequired,
  title: PropTypes.string,
  description: PropTypes.string,
  onChartChange: PropTypes.func
};

InteractiveCharts.defaultProps = {
  title: 'Análisis de KPIs',
  description: 'Visualización interactiva de indicadores clave de performance'
};

export default InteractiveCharts;
