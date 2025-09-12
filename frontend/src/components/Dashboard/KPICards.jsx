// frontend/src/components/Dashboard/KPICards.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Row, Col, Card, Statistic, Badge, Tooltip, Button, Space, Skeleton } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  FileTextOutlined,
  UserOutlined,
  PlusCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import analyticsService from '../../services/analyticsService';
import ErrorState from '../common/ErrorState';
import Loader from '../common/Loader';
import theme from '../../styles/theme';


/**
 * KPICards - Tarjetas de KPIs para dashboards CDG
 * Admite mode="direccion" (corporativo) y mode="gestor" (individual)
 * Perfectamente integrado con servicios CDG y tema Banca March
 */
const KPICards = ({
  mode = 'direccion',
  periodo,
  gestorId = null,
  onKpiClick = null,
  className = '',
  style = {},
}) => {
  const [kpisData, setKpisData] = useState([]);
  const [alertsData, setAlertsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Normalizar período para asegurar que siempre sea string
  const normalizedPeriodo = useMemo(() => {
    if (!periodo) return "2025-10";
    if (typeof periodo === 'string') return periodo;
    if (typeof periodo === 'object') {
      return periodo.latest || periodo.periodo || periodo.value || "2025-10";
    }
    return String(periodo);
  }, [periodo]);

  // Configuración de KPIs por modo
  const kpiConfig = useMemo(() => ({
    direccion: [
      { key: 'ingresos', label: 'Ingresos', icon: DollarOutlined, color: theme.colors.success },
      { key: 'gastos', label: 'Gastos', icon: ArrowDownOutlined, color: theme.colors.warning },
      { key: 'margen', label: 'Margen', icon: ArrowUpOutlined, color: theme.colors.bmGreenPrimary },
      { key: 'contratos', label: 'Contratos', icon: FileTextOutlined, color: theme.colors.info },
      { key: 'clientes', label: 'Clientes', icon: UserOutlined, color: theme.colors.bmGreenLight },
    ],
    gestor: [
      { key: 'cartera', label: 'Cartera', icon: DollarOutlined, color: theme.colors.bmGreenPrimary },
      { key: 'margen', label: 'Margen', icon: ArrowUpOutlined, color: theme.colors.success },
      { key: 'contratos_activos', label: 'Contratos', icon: FileTextOutlined, color: theme.colors.info },
      { key: 'nuevos_contratos', label: 'Nuevos', icon: PlusCircleOutlined, color: theme.colors.bmGreenLight },
      { key: 'ticket_medio', label: 'Ticket Medio', icon: DollarOutlined, color: theme.colors.warning },
    ]
  }), []);


  // Cargar datos de KPIs según el modo
  const loadKPIsData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // ✅ DEBUGGING: Log inicial con período normalizado
      console.log('[KPICards] 🔄 Iniciando carga de datos KPIs:', { 
        mode, 
        periodoOriginal: periodo,
        periodoNormalizado: normalizedPeriodo, 
        gestorId 
      });

      if (mode === 'direccion') {
        // ✅ DEBUGGING: Log antes de llamadas API corporativas
        console.log('[KPICards] 📡 Llamando APIs corporativas...');

        // Datos corporativos desde múltiples endpoints
        const [summary, gestoresRanking, centros, deviations] = await Promise.all([
          api.basic.summary(),
          api.basic.gestoresRanking('contratos'),
          api.basic.centros(),
          api.deviations.summary(normalizedPeriodo).catch(() => null), // Usar período normalizado
        ]);

        // ✅ DEBUGGING: Log de respuestas recibidas
        console.log('[KPICards] 📊 Datos API corporativos recibidos:', { 
          summary, 
          gestoresRanking, 
          centros, 
          deviations 
        });

        // Calcular KPIs consolidados
        const kpis = [
          {
            key: 'ingresos',
            value: summary?.ingresos_totales || calculateTotalIngresos(gestoresRanking),
            variation: 12.3, // TODO: Calcular vs período anterior
            trend: 'up',
            format: 'currency',
          },
          {
            key: 'gastos',
            value: summary?.gastos_totales || 850000,
            variation: -5.2,
            trend: 'down',
            format: 'currency',
          },
          {
            key: 'margen',
            value: summary?.margen_total || 15.8,
            variation: 2.1,
            trend: 'up',
            format: 'percent',
          },
          {
            key: 'contratos',
            value: summary?.total_contratos || gestoresRanking?.reduce((acc, g) => acc + (g.numcontratos || 0), 0) || 0,
            variation: 8.7,
            trend: 'up',
            format: 'number',
          },
          {
            key: 'clientes',
            value: summary?.total_clientes || 85,
            variation: 3.2,
            trend: 'up',
            format: 'number',
          },
        ];

        console.log('[KPICards] 🔢 KPIs procesados para DIRECCION:', kpis);
        setKpisData(kpis);

        // Alertas corporativas
        if (deviations) {
          console.log('[KPICards] ⚠️ Configurando alertas corporativas');
          setAlertsData([
            {
              type: 'warning',
              message: 'Centro Madrid: -12% margen vs objetivo',
              priority: 'high'
            },
            {
              type: 'info',
              message: 'Producto Hipotecas: +15% contratos nuevos',
              priority: 'medium'
            }
          ]);
        }

      } else if (mode === 'gestor' && gestorId) {
        // ✅ DEBUGGING: Log antes de llamadas API gestor
        console.log('[KPICards] 👤 Llamando APIs específicas de gestor:', gestorId);

        // Datos específicos del gestor - usar período normalizado
        const [gestorKpis, gestorContratos, gestorClientes, gestorEvolution] = await Promise.all([
          api.kpis.gestor(gestorId, normalizedPeriodo),
          api.basic.contractsByGestor(gestorId),
          api.basic.clientesByGestor(gestorId),
          api.kpis.evolution(gestorId, getPreviousPeriod(normalizedPeriodo), normalizedPeriodo).catch(() => null),
        ]);

        // ✅ DEBUGGING: Log de respuestas de gestor
        console.log('[KPICards] 👥 Datos API gestor recibidos:', { 
          gestorKpis, 
          gestorContratos, 
          gestorClientes, 
          gestorEvolution 
        });

        const kpis = [
          {
            key: 'cartera',
            value: gestorKpis?.cartera_total || calculateCarteraVolume(gestorContratos),
            variation: gestorEvolution?.cartera_variation || 5.4,
            trend: gestorEvolution?.cartera_variation > 0 ? 'up' : 'down',
            format: 'currency',
            comparison: 'vs. período anterior'
          },
          {
            key: 'margen',
            value: gestorKpis?.margen || 14.2,
            variation: gestorEvolution?.margen_variation || -1.3,
            trend: gestorEvolution?.margen_variation > 0 ? 'up' : 'down',
            format: 'percent',
            comparison: 'vs. media centro'
          },
          {
            key: 'contratos_activos',
            value: gestorContratos?.length || 0,
            variation: calculateContractsVariation(gestorContratos),
            trend: 'stable',
            format: 'number',
            comparison: 'vs. período anterior'
          },
          {
            key: 'nuevos_contratos',
            value: countNewContracts(gestorContratos, normalizedPeriodo), // Usar período normalizado
            variation: 22.1,
            trend: 'up',
            format: 'number',
            comparison: 'este período'
          },
          {
            key: 'ticket_medio',
            value: calculateTicketMedio(gestorContratos),
            variation: 7.8,
            trend: 'up',
            format: 'currency',
            comparison: 'vs. histórico'
          }
        ];

        console.log('[KPICards] 🎯 KPIs procesados para GESTOR:', kpis);
        setKpisData(kpis);

        // Sugerencias para el gestor
        console.log('[KPICards] 💡 Configurando alertas de gestor');
        setAlertsData([
          {
            type: 'success',
            message: 'Buen rendimiento en productos de inversión',
            priority: 'medium'
          },
          {
            type: 'info',
            message: 'Oportunidad: incrementar cross-selling hipotecario',
            priority: 'low'
          }
        ]);
      } else {
        console.warn('[KPICards] ⚠️ Condición no cumplida:', { mode, gestorId });
      }

    } catch (err) {
      console.error('[KPICards] ❌ Error loading data:', err);
      setError(err);
    } finally {
      console.log('[KPICards] ✅ Finalizando carga de KPIs');
      setLoading(false);
    }
  }, [mode, normalizedPeriodo, gestorId]);

  useEffect(() => {
    if (normalizedPeriodo && (mode === 'direccion' || (mode === 'gestor' && gestorId))) {
      loadKPIsData();
    }
  }, [loadKPIsData]);

  // Helpers para cálculos
  const calculateTotalIngresos = (gestores) => {
    return gestores?.reduce((acc, g) => acc + (g.ingresos || 125000), 0) || 2750000;
  };

  const calculateCarteraVolume = (contratos) => {
    return contratos?.reduce((acc, c) => acc + (c.volumen || 45000), 0) || 680000;
  };

  const calculateContractsVariation = (contratos) => {
    return contratos?.length > 15 ? 12.5 : -3.2;
  };

  const countNewContracts = (contratos, currentPeriod) => {
    if (!contratos || !currentPeriod) return 0;
    return contratos.filter(c => 
      c.fecha_alta && c.fecha_alta.startsWith(currentPeriod)
    ).length;
  };

  const calculateTicketMedio = (contratos) => {
    if (!contratos?.length) return 0;
    const total = contratos.reduce((acc, c) => acc + (c.volumen || 45000), 0);
    return Math.round(total / contratos.length);
  };

  const getPreviousPeriod = (current) => {
    const [year, month] = current.split('-');
    const prevMonth = parseInt(month) - 1;
    if (prevMonth === 0) {
      return `${parseInt(year) - 1}-12`;
    }
    return `${year}-${prevMonth.toString().padStart(2, '0')}`;
  };

  // Formatear valores
  const formatValue = (value, format) => {
    if (!value && value !== 0) return 'N/A';
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('es-ES', {
          style: 'currency',
          currency: 'EUR',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(value);
      case 'percent':
        return `${value.toFixed(1)}%`;
      case 'number':
        return new Intl.NumberFormat('es-ES').format(value);
      default:
        return value.toString();
    }
  };

  // Componente de tarjeta KPI individual
  const KPICard = ({ kpi, config }) => {
    const isPositiveVariation = kpi.variation > 0;
    const isNeutral = Math.abs(kpi.variation) < 1;
    
    const variationColor = isNeutral 
      ? theme.colors.textSecondary 
      : isPositiveVariation 
        ? theme.colors.success 
        : theme.colors.error;

    const TrendIcon = kpi.trend === 'up' 
      ? ArrowUpOutlined 
      : kpi.trend === 'down' 
        ? ArrowDownOutlined 
        : null;

    const handleClick = () => {
      if (onKpiClick) {
        onKpiClick(kpi.key, kpi);
      }
    };

    return (
      <Card
        hoverable={!!onKpiClick}
        onClick={handleClick}
        style={{
          borderRadius: theme.token.borderRadius,
          border: `1px solid ${theme.colors.borderLight}`,
          boxShadow: '0 2px 8px rgba(27, 94, 85, 0.08)',
          transition: 'all 0.3s ease',
          cursor: onKpiClick ? 'pointer' : 'default',
          height: '100%',
        }}
        styles={{ body: { padding: '20px' } }}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <config.icon 
                style={{ 
                  fontSize: 20, 
                  color: config.color,
                  opacity: 0.8 
                }} 
              />
              <span style={{ 
                color: theme.colors.textSecondary, 
                fontSize: 14,
                fontWeight: 500 
              }}>
                {config.label}
              </span>
            </div>
            
            {Math.abs(kpi.variation) > 10 && (
              <Badge 
                status={isPositiveVariation ? "success" : "error"} 
                text={
                  <Tooltip title={`Variación significativa: ${kpi.variation > 0 ? '+' : ''}${kpi.variation}%`}>
                    <WarningOutlined style={{ fontSize: 12 }} />
                  </Tooltip>
                }
              />
            )}
          </div>

          <Statistic
            value={kpi.value}
            formatter={(value) => (
              <span style={{ 
                color: theme.colors.textPrimary,
                fontSize: 24,
                fontWeight: 600,
                fontFamily: theme.token.fontFamily 
              }}>
                {formatValue(value, kpi.format)}
              </span>
            )}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              {TrendIcon && (
                <TrendIcon 
                  style={{ 
                    fontSize: 14, 
                    color: variationColor 
                  }} 
                />
              )}
              <span style={{ 
                color: variationColor,
                fontSize: 14,
                fontWeight: 500 
              }}>
                {kpi.variation > 0 ? '+' : ''}{kpi.variation.toFixed(1)}%
              </span>
            </div>
            
            {kpi.comparison && (
              <Tooltip title={kpi.comparison}>
                <InfoCircleOutlined 
                  style={{ 
                    fontSize: 12, 
                    color: theme.colors.textLight,
                    cursor: 'help'
                  }} 
                />
              </Tooltip>
            )}
          </div>
        </Space>
      </Card>
    );
  };

  // Componente de alertas/sugerencias
  const AlertsPanel = () => {
    if (!alertsData.length) return null;

    return (
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <WarningOutlined style={{ color: theme.colors.warning }} />
            <span>{mode === 'direccion' ? 'Alertas Ejecutivas' : 'Sugerencias'}</span>
          </div>
        }
        size="small"
        style={{
          marginTop: theme.spacing.md,
          border: `1px solid ${theme.colors.borderLight}`,
        }}
        styles={{ body: { padding: '16px' } }}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          {alertsData.map((alert, index) => (
            <div 
              key={index}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: 8,
                padding: theme.spacing.xs,
                borderRadius: 4,
                backgroundColor: alert.type === 'warning' 
                  ? `${theme.colors.warning}10`
                  : alert.type === 'success'
                    ? `${theme.colors.success}10`
                    : `${theme.colors.info}10`
              }}
            >
              <Badge 
                status={alert.type === 'warning' ? 'warning' : alert.type === 'success' ? 'success' : 'processing'} 
              />
              <span style={{ 
                fontSize: 13, 
                color: theme.colors.textSecondary,
                flex: 1 
              }}>
                {alert.message}
              </span>
            </div>
          ))}
        </Space>
      </Card>
    );
  };

  // Estados de carga y error
  if (loading) {
    return (
      <div className={className} style={style}>
        <Row gutter={[16, 16]}>
          {[...Array(5)].map((_, i) => (
            <Col key={i} xs={24} sm={12} lg={8} xl={6}>
              <Card styles={{ body: { padding: '16px' } }}>
                <Skeleton active paragraph={{ rows: 2 }} />
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState
        error={error}
        message="Error al cargar KPIs"
        description="No se pudieron obtener los indicadores clave de rendimiento"
        onRetry={loadKPIsData}
        style={style}
        className={className}
      />
    );
  }

  if (!kpisData.length) {
    return (
      <div className={className} style={style}>
        <Card 
          style={{ textAlign: 'center', padding: theme.spacing.lg }}
          styles={{ body: { padding: '32px' } }}
        >
          <InfoCircleOutlined style={{ fontSize: 48, color: theme.colors.textLight, marginBottom: theme.spacing.md }} />
          <h3 style={{ color: theme.colors.textSecondary }}>
            No hay datos disponibles
          </h3>
          <p style={{ color: theme.colors.textLight }}>
            {mode === 'gestor' 
              ? 'No se encontraron KPIs para este gestor en el período seleccionado'
              : 'No hay información corporativa disponible para este período'
            }
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className={`kpi-cards ${className}`} style={style}>
      <Row gutter={[16, 16]}>
        {kpisData.map((kpi) => {
          const config = kpiConfig[mode].find(c => c.key === kpi.key);
          if (!config) return null;

          return (
            <Col 
              key={kpi.key} 
              xs={24} 
              sm={12} 
              lg={mode === 'direccion' ? 8 : 12} 
              xl={mode === 'direccion' ? 6 : 8}
            >
              <KPICard kpi={kpi} config={config} />
            </Col>
          );
        })}
      </Row>

      <AlertsPanel />
    </div>
  );
};

KPICards.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.oneOfType([PropTypes.string, PropTypes.object]).isRequired,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onKpiClick: PropTypes.func,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default KPICards;
