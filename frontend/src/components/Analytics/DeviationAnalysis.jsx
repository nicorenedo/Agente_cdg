// src/components/Analytics/DeviationAnalysis.jsx
// Componente crítico para análisis de desviaciones con sistema de alertas y drill-down

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Alert, Badge, Button, Space, Tooltip, Select, Row, Col, Statistic } from 'antd';
import { 
  ExclamationCircleOutlined, 
  WarningOutlined, 
  CheckCircleOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  EyeOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import InteractiveCharts from '../Dashboard/InteractiveCharts';
import api from '../../services/api';
import theme from '../../styles/theme';

const { Option } = Select;

// Configuración de umbrales para análisis de desviaciones
const DEVIATION_THRESHOLDS = {
  CRITICAL: 25.0,    // Desviación crítica >25%
  WARNING: 15.0,     // Alerta >15%
  NORMAL: 5.0        // Normal <5%
};

// Tipos de desviaciones que el sistema puede detectar
const DEVIATION_TYPES = {
  PRECIO: 'precio',
  MARGEN: 'margen',
  VOLUMEN: 'volumen',
  EFICIENCIA: 'eficiencia'
};

// Configuración de colores para sistema de semáforo
const getDeviationColor = (deviation) => {
  const absDeviation = Math.abs(deviation);
  if (absDeviation >= DEVIATION_THRESHOLDS.CRITICAL) return theme.colors.error;
  if (absDeviation >= DEVIATION_THRESHOLDS.WARNING) return theme.colors.warning;
  return theme.colors.success;
};

// Badge de estado según severidad
const DeviationBadge = ({ deviation, type }) => {
  const absDeviation = Math.abs(deviation);
  let status = 'success';
  let icon = <CheckCircleOutlined />;
  let text = 'Normal';

  if (absDeviation >= DEVIATION_THRESHOLDS.CRITICAL) {
    status = 'error';
    icon = <ExclamationCircleOutlined />;
    text = 'Crítico';
  } else if (absDeviation >= DEVIATION_THRESHOLDS.WARNING) {
    status = 'warning';
    icon = <WarningOutlined />;
    text = 'Alerta';
  }

  return (
    <Badge
      status={status}
      text={
        <Space>
          {icon}
          <span style={{ fontWeight: 600 }}>
            {text} ({deviation > 0 ? '+' : ''}{deviation.toFixed(1)}%)
          </span>
        </Space>
      }
    />
  );
};

DeviationBadge.propTypes = {
  deviation: PropTypes.number.isRequired,
  type: PropTypes.string.isRequired
};

const DeviationAnalysis = ({ 
  userId, 
  gestorId = null, 
  periodo, 
  onDrillDown 
}) => {
  // Estados principales
  const [loading, setLoading] = useState(true);
  const [deviations, setDeviations] = useState([]);
  const [filteredDeviations, setFilteredDeviations] = useState([]);
  const [selectedType, setSelectedType] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [summary, setSummary] = useState({});
  const [chartData, setChartData] = useState([]);

  // Cargar datos de desviaciones
  const fetchDeviationData = useCallback(async () => {
    setLoading(true);
    try {
      const currentPeriod = periodo || new Date().toISOString().slice(0, 7);
      
      // Obtener alertas de desviación del backend
      const alertsResponse = await api.getDeviationAlerts(currentPeriod, DEVIATION_THRESHOLDS.WARNING);
      
      if (alertsResponse.data) {
        const allDeviations = [
          ...(alertsResponse.data.precio_alerts || []).map(item => ({
            ...item,
            type: DEVIATION_TYPES.PRECIO,
            deviation: item.precio_desviacion || 0,
            severity: getSeverityLevel(item.precio_desviacion || 0)
          })),
          ...(alertsResponse.data.margen_anomalies || []).map(item => ({
            ...item,
            type: DEVIATION_TYPES.MARGEN,
            deviation: item.margen_desviacion || 0,
            severity: getSeverityLevel(item.margen_desviacion || 0)
          })),
          ...(alertsResponse.data.volumen_outliers || []).map(item => ({
            ...item,
            type: DEVIATION_TYPES.VOLUMEN,
            deviation: item.volumen_desviacion || 0,
            severity: getSeverityLevel(item.volumen_desviacion || 0)
          }))
        ];

        setDeviations(allDeviations);
        setFilteredDeviations(allDeviations);
        
        // Calcular resumen de desviaciones
        calculateSummary(allDeviations);
        
        // Preparar datos para gráficos
        prepareChartData(allDeviations);
      }

    } catch (error) {
      console.error('Error cargando análisis de desviaciones:', error);
    } finally {
      setLoading(false);
    }
  }, [periodo]);

  // Determinar nivel de severidad
  const getSeverityLevel = (deviation) => {
    const absDeviation = Math.abs(deviation);
    if (absDeviation >= DEVIATION_THRESHOLDS.CRITICAL) return 'critical';
    if (absDeviation >= DEVIATION_THRESHOLDS.WARNING) return 'warning';
    return 'normal';
  };

  // Calcular resumen estadístico
  const calculateSummary = (data) => {
    const summary = {
      total: data.length,
      critical: data.filter(d => d.severity === 'critical').length,
      warning: data.filter(d => d.severity === 'warning').length,
      normal: data.filter(d => d.severity === 'normal').length,
      avgDeviation: data.reduce((sum, d) => sum + Math.abs(d.deviation), 0) / (data.length || 1)
    };
    setSummary(summary);
  };

  // Preparar datos para visualización
  const prepareChartData = (data) => {
    // Agrupar por tipo de desviación para gráfico
    const groupedData = data.reduce((acc, item) => {
      const existingType = acc.find(group => group.type === item.type);
      if (existingType) {
        existingType.count += 1;
        existingType.avgDeviation = (existingType.avgDeviation + Math.abs(item.deviation)) / 2;
      } else {
        acc.push({
          type: item.type,
          count: 1,
          avgDeviation: Math.abs(item.deviation)
        });
      }
      return acc;
    }, []);

    setChartData(groupedData);
  };

  // Filtrar desviaciones
  const applyFilters = useCallback(() => {
    let filtered = [...deviations];

    if (selectedType !== 'all') {
      filtered = filtered.filter(d => d.type === selectedType);
    }

    if (selectedSeverity !== 'all') {
      filtered = filtered.filter(d => d.severity === selectedSeverity);
    }

    setFilteredDeviations(filtered);
    calculateSummary(filtered);
  }, [deviations, selectedType, selectedSeverity]);

  // Efectos
  useEffect(() => {
    fetchDeviationData();
  }, [fetchDeviationData]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  // Configuración de columnas para la tabla de desviaciones
  const columns = [
    {
      title: 'Gestor',
      dataIndex: 'desc_gestor',
      key: 'gestor',
      ellipsis: true,
      sorter: (a, b) => (a.desc_gestor || '').localeCompare(b.desc_gestor || ''),
    },
    {
      title: 'Centro',
      dataIndex: 'desc_centro',
      key: 'centro',
      ellipsis: true,
    },
    {
      title: 'Tipo',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Badge 
          color={theme.colors.bmGreenLight} 
          text={type.toUpperCase()} 
        />
      ),
      filters: Object.values(DEVIATION_TYPES).map(type => ({
        text: type.toUpperCase(),
        value: type
      })),
      onFilter: (value, record) => record.type === value,
    },
    {
      title: 'Desviación',
      dataIndex: 'deviation',
      key: 'deviation',
      render: (deviation, record) => (
        <DeviationBadge deviation={deviation} type={record.type} />
      ),
      sorter: (a, b) => Math.abs(a.deviation) - Math.abs(b.deviation),
    },
    {
      title: 'Valor Real',
      dataIndex: 'valor_real',
      key: 'valor_real',
      render: (value) => value ? `€${value.toLocaleString()}` : '--',
    },
    {
      title: 'Valor Estándar',
      dataIndex: 'valor_estandar',
      key: 'valor_estandar',
      render: (value) => value ? `€${value.toLocaleString()}` : '--',
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Ver detalles y drill-down">
            <Button
              type="primary"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleDrillDown(record)}
              style={{
                backgroundColor: theme.colors.bmGreenLight,
                borderColor: theme.colors.bmGreenLight
              }}
            >
              Drill-Down
            </Button>
          </Tooltip>
        </Space>
      ),
    }
  ];

  // Manejar drill-down a detalle
  const handleDrillDown = (record) => {
    if (onDrillDown) {
      onDrillDown({
        gestorId: record.gestor_id,
        centroId: record.centro_id,
        type: record.type,
        deviation: record.deviation,
        period: periodo
      });
    }
  };

  return (
    <div style={{ padding: theme.spacing.md }}>
      
      {/* Header con resumen ejecutivo */}
      <Card 
        title={
          <Space>
            <ExclamationCircleOutlined style={{ color: theme.colors.bmGreenPrimary }} />
            <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
              Análisis de Desviaciones - Sistema de Alertas
            </span>
          </Space>
        }
        bordered={false}
        style={{ marginBottom: theme.spacing.lg }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={6}>
            <Statistic
              title="Total Desviaciones"
              value={summary.total || 0}
              prefix={<TrendingUpOutlined />}
              valueStyle={{ color: theme.colors.bmGreenPrimary }}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="Críticas"
              value={summary.critical || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: theme.colors.error }}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="Alertas"
              value={summary.warning || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: theme.colors.warning }}
            />
          </Col>
          <Col xs={24} sm={6}>
            <Statistic
              title="Desviación Promedio"
              value={summary.avgDeviation || 0}
              precision={1}
              suffix="%"
              prefix={<TrendingDownOutlined />}
              valueStyle={{ color: theme.colors.bmGreenLight }}
            />
          </Col>
        </Row>
      </Card>

      {/* Filtros y controles */}
      <Card 
        title="Filtros de Análisis"
        size="small"
        style={{ marginBottom: theme.spacing.md }}
      >
        <Space wrap>
          <Select
            placeholder="Tipo de desviación"
            value={selectedType}
            onChange={setSelectedType}
            style={{ width: 200 }}
          >
            <Option value="all">Todos los tipos</Option>
            {Object.values(DEVIATION_TYPES).map(type => (
              <Option key={type} value={type}>
                {type.toUpperCase()}
              </Option>
            ))}
          </Select>

          <Select
            placeholder="Severidad"
            value={selectedSeverity}
            onChange={setSelectedSeverity}
            style={{ width: 150 }}
          >
            <Option value="all">Todas</Option>
            <Option value="critical">Críticas</Option>
            <Option value="warning">Alertas</Option>
            <Option value="normal">Normales</Option>
          </Select>

          <Button 
            onClick={fetchDeviationData}
            style={{ borderColor: theme.colors.bmGreenLight }}
          >
            Actualizar
          </Button>
        </Space>
      </Card>

      {/* Gráfico de desviaciones por tipo */}
      {chartData.length > 0 && (
        <InteractiveCharts
          data={chartData}
          availableKpis={['count', 'avgDeviation']}
          title="Distribución de Desviaciones por Tipo"
          description="Análisis visual de desviaciones detectadas en el sistema"
        />
      )}

      {/* Alertas críticas */}
      {summary.critical > 0 && (
        <Alert
          message="Desviaciones Críticas Detectadas"
          description={`Se han detectado ${summary.critical} desviaciones críticas que requieren atención inmediata. Revise la tabla para más detalles.`}
          type="error"
          showIcon
          style={{ marginBottom: theme.spacing.md }}
          action={
            <Button 
              size="small" 
              type="primary" 
              danger
              onClick={() => setSelectedSeverity('critical')}
            >
              Ver Críticas
            </Button>
          }
        />
      )}

      {/* Tabla detallada de desviaciones */}
      <Card
        title={`Detalle de Desviaciones (${filteredDeviations.length})`}
        bordered={false}
        style={{ 
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      >
        <Table
          columns={columns}
          dataSource={filteredDeviations}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} de ${total} desviaciones`
          }}
          scroll={{ x: 'max-content' }}
          size="small"
          rowKey={(record) => `${record.gestor_id || record.desc_gestor}-${record.type}-${Math.random()}`}
          rowClassName={(record) => {
            if (record.severity === 'critical') return 'deviation-critical';
            if (record.severity === 'warning') return 'deviation-warning';
            return 'deviation-normal';
          }}
        />
      </Card>

      {/* Leyenda del sistema de semáforo */}
      <Card 
        title="Leyenda del Sistema de Alertas"
        size="small"
        style={{ marginTop: theme.spacing.md }}
      >
        <Space direction="vertical" size="small">
          <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <Badge status="success" />
            <span><strong>Normal:</strong> Desviación {'<'} {DEVIATION_THRESHOLDS.NORMAL}% - Dentro de parámetros aceptables</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <Badge status="warning" />
            <span><strong>Alerta:</strong> Desviación {DEVIATION_THRESHOLDS.NORMAL}% - {DEVIATION_THRESHOLDS.CRITICAL}% - Requiere monitoreo</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <Badge status="error" />
            <span><strong>Crítico:</strong> Desviación {'>'} {DEVIATION_THRESHOLDS.CRITICAL}% - Acción inmediata requerida</span>
          </div>
        </Space>
      </Card>

      {/* Estilos CSS para las filas de la tabla */}
      <style jsx>{`
        .deviation-critical {
          background-color: ${theme.colors.error}15 !important;
        }
        .deviation-warning {
          background-color: ${theme.colors.warning}15 !important;
        }
        .deviation-normal {
          background-color: ${theme.colors.success}08 !important;
        }
      `}</style>
    </div>
  );
};

DeviationAnalysis.propTypes = {
  userId: PropTypes.string.isRequired,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  onDrillDown: PropTypes.func
};

export default DeviationAnalysis;
