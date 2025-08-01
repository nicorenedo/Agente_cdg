// src/components/Dashboard/KPICards.jsx
// Componente para mostrar KPIs principales en tarjetas estilizadas

import React from 'react';
import { Card, Statistic, Row, Col, Tooltip } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import theme from '../../styles/theme';

// Información de cada KPI para tooltips y formateo
const KPI_CONFIG = {
  roe: {
    title: 'ROE',
    description: 'Return on Equity - Rentabilidad sobre fondos propios, indicador clave en banca',
    unit: '%',
    precision: 2,
    threshold: { good: 8, excellent: 12 }
  },
  margen_neto: {
    title: 'Margen Neto',
    description: 'Margen neto como porcentaje sobre ingresos totales del gestor',
    unit: '%',
    precision: 2,
    threshold: { good: 10, excellent: 15 }
  },
  eficiencia: {
    title: 'Eficiencia Operativa',
    description: 'Ratio de eficiencia operativa - menor es mejor en este indicador',
    unit: '%',
    precision: 1,
    threshold: { good: 75, excellent: 65 },
    invertedLogic: true // Para eficiencia, menor es mejor
  },
  total_ingresos: {
    title: 'Total Ingresos',
    description: 'Suma total de ingresos gestionados por el gestor en el período',
    unit: '€',
    precision: 0,
    format: 'currency'
  },
  total_gastos: {
    title: 'Total Gastos',
    description: 'Suma total de gastos asociados a la gestión en el período',
    unit: '€',
    precision: 0,
    format: 'currency'
  }
};

// Función para determinar el color según el valor y umbrales
const getValueColor = (value, config) => {
  if (value === null || value === undefined) return theme.colors.textSecondary;
  
  const { threshold, invertedLogic } = config;
  if (!threshold) return theme.colors.bmGreenPrimary;
  
  if (invertedLogic) {
    // Para eficiencia, menor es mejor
    if (value <= threshold.excellent) return theme.colors.bmGreenPrimary;
    if (value <= threshold.good) return theme.colors.bmGreenLight;
    return theme.colors.warning;
  } else {
    // Para ROE y margen, mayor es mejor
    if (value >= threshold.excellent) return theme.colors.bmGreenPrimary;
    if (value >= threshold.good) return theme.colors.bmGreenLight;
    return theme.colors.warning;
  }
};

// Función para formatear valores según su tipo
const formatValue = (value, config) => {
  if (value === null || value === undefined) return '--';
  
  if (config.format === 'currency') {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }
  
  return value.toFixed(config.precision);
};

// Componente individual para cada tarjeta KPI
const KPICard = ({ kpiKey, value, previousValue }) => {
  const config = KPI_CONFIG[kpiKey];
  if (!config) return null;
  
  const formattedValue = formatValue(value, config);
  const valueColor = getValueColor(value, config);
  
  // Calcular cambio respecto al período anterior
  let changeIndicator = null;
  if (previousValue !== undefined && previousValue !== null && value !== null) {
    const change = value - previousValue;
    const changePercent = (change / previousValue) * 100;
    
    if (Math.abs(changePercent) > 0.1) { // Solo mostrar si el cambio es significativo
      const isPositive = change > 0;
      const iconColor = isPositive ? theme.colors.bmGreenPrimary : theme.colors.error;
      const Icon = isPositive ? ArrowUpOutlined : ArrowDownOutlined;
      
      changeIndicator = (
        <Tooltip title={`Cambio: ${isPositive ? '+' : ''}${changePercent.toFixed(1)}% vs período anterior`}>
          <Icon style={{ color: iconColor, marginLeft: 8, fontSize: 14 }} />
        </Tooltip>
      );
    }
  }
  
  return (
    <Card 
      bordered={false}
      style={{ 
        borderRadius: 8, 
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        border: `1px solid ${theme.colors.border}`,
        height: '120px'
      }}
      bodyStyle={{ padding: '16px' }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            marginBottom: 8,
            color: theme.colors.textSecondary,
            fontSize: 14,
            fontWeight: 500
          }}>
            {config.title}
            <Tooltip title={config.description}>
              <InfoCircleOutlined style={{ marginLeft: 6, color: theme.colors.bmGreenLight }} />
            </Tooltip>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'baseline' }}>
            <span style={{ 
              fontSize: 24,
              fontWeight: 700,
              color: valueColor,
              lineHeight: 1
            }}>
              {formattedValue}
            </span>
            {config.format !== 'currency' && (
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
      </div>
    </Card>
  );
};

KPICard.propTypes = {
  kpiKey: PropTypes.string.isRequired,
  value: PropTypes.number,
  previousValue: PropTypes.number
};

// Componente principal KPICards
const KPICards = ({ kpis, previousKpis = {} }) => {
  const kpiKeys = Object.keys(KPI_CONFIG).filter(key => 
    kpis.hasOwnProperty(key) && kpis[key] !== null
  );
  
  if (kpiKeys.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: theme.spacing.xl,
        color: theme.colors.textSecondary 
      }}>
        No hay KPIs disponibles para mostrar
      </div>
    );
  }
  
  return (
    <div style={{ marginBottom: theme.spacing.lg }}>
      <Row gutter={[16, 16]}>
        {kpiKeys.map(key => (
          <Col 
            key={key} 
            xs={24} 
            sm={12} 
            md={8} 
            lg={kpiKeys.length <= 3 ? 8 : 6}
          >
            <KPICard 
              kpiKey={key}
              value={kpis[key]}
              previousValue={previousKpis[key]}
            />
          </Col>
        ))}
      </Row>
    </div>
  );
};

KPICards.propTypes = {
  kpis: PropTypes.shape({
    roe: PropTypes.number,
    margen_neto: PropTypes.number,
    eficiencia: PropTypes.number,
    total_ingresos: PropTypes.number,
    total_gastos: PropTypes.number
  }).isRequired,
  previousKpis: PropTypes.object
};

export default KPICards;
