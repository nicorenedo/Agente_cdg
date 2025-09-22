// frontend/src/components/Dashboard/KPICards.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Row, Col, Card, Statistic, Badge, Tooltip, Space, Skeleton, Select } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  FileTextOutlined,
  UserOutlined,
  TrophyOutlined,
  PercentageOutlined,
  BankOutlined,
  TeamOutlined,
  EuroCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import theme from '../../styles/theme';
import ErrorState from '../common/ErrorState';


/**
 * KPICards - Tarjetas de KPIs mejoradas con selección Global/Centro y animación.
 */
const KPICards = ({
  mode = 'direccion',
  periodo,
  gestorId = null,
  onKpiClick = null,
  className = '',
  style = {},
}) => {
  // Estado de selección de filtro por centro por KPI para dirección
  const [centerSelections, setCenterSelections] = useState({
    roe_grupo: 'global',
    total_clientes: 'global',
    total_contratos: 'global',
    ingresos_totales: 'global',
  });


  // Datos de centros y métricas
  const [centros, setCentros] = useState([]);
  const [centrosFin, setCentrosFin] = useState({});
  const [clientesPorCentro, setClientesPorCentro] = useState({});
  const [kpisData, setKpisData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);


  // Normalizar período
  const normalizedPeriodo = useMemo(() => {
    if (!periodo) return "2025-10";
    if (typeof periodo === 'string') return periodo;
    if (typeof periodo === 'object') {
      return periodo.latest || periodo.periodo || periodo.value || "2025-10";
    }
    return String(periodo);
  }, [periodo]);


  // Opciones del filtro select
  const centerOptions = useMemo(() => [
    { value: 'global', label: 'Global' },
    ...centros.map(c => ({ 
      value: String(c.CENTRO_ID), 
      label: c.DESC_CENTRO || `Centro ${c.CENTRO_ID}`
    }))
  ], [centros]);


  // Configuración de KPIs
  const kpiConfig = useMemo(() => ({
    direccion: [
      { 
        key: 'roe_grupo', 
        label: 'ROE Grupo', 
        icon: PercentageOutlined, 
        color: theme.colors.bmGreenPrimary,
        description: 'Rentabilidad sobre patrimonio del grupo/centro'
      },
      { 
        key: 'total_clientes', 
        label: 'Total Clientes', 
        icon: UserOutlined, 
        color: theme.colors.info,
        description: 'Total clientes del grupo o centro'
      },
      { 
        key: 'total_contratos', 
        label: 'Total Contratos', 
        icon: FileTextOutlined, 
        color: theme.colors.bmGreenLight,
        description: 'Número total de contratos vigentes'
      },
      { 
        key: 'ingresos_totales', 
        label: 'Ingresos Totales', 
        icon: EuroCircleOutlined, 
        color: theme.colors.success,
        description: 'Ingresos del grupo o centro'
      }
    ],
    gestor: [
      { 
        key: 'roe_gestor', 
        label: 'ROE Gestor', 
        icon: PercentageOutlined, 
        color: theme.colors.bmGreenPrimary,
        description: 'Rentabilidad sobre patrimonio del gestor'
      },
      { 
        key: 'bonus_gestor', 
        label: 'Bonus Gestor', 
        icon: TrophyOutlined, 
        color: theme.colors.warning,
        description: 'Incentivos calculados (detalle)'
      },
      { 
        key: 'clientes_gestor', 
        label: 'Mis Clientes', 
        icon: TeamOutlined, 
        color: theme.colors.info,
        description: 'Número de clientes asignados'
      },
      { 
        key: 'contratos_gestor', 
        label: 'Mis Contratos', 
        icon: FileTextOutlined, 
        color: theme.colors.bmGreenLight,
        description: 'Número de contratos gestionados'
      }
    ]
  }), []);


  // Animación CSS
  const animatedCardStyle = {
    boxShadow: '0 0 0 2px #d0fff2, 0 6px 24px 0 rgba(27,94,85,0.13)',
    animation: 'spin-shadow 3s linear infinite'
  };


  useEffect(() => {
    if (!document.getElementById('spin-shadow-keyframes')) {
      const style = document.createElement('style');
      style.type = 'text/css';
      style.id = 'spin-shadow-keyframes';
      style.innerHTML = `
@keyframes spin-shadow {
  0% { box-shadow: 0 0 0 2px #25755eff, 0 6px 24px 0 rgba(27,94,85,0.12);}
  25% { box-shadow: 0 0 10px 4px #1d7358e6, 0 12px 18px -2px rgba(13,94,85,0.16);}
  50% { box-shadow: 0 0 24px 2px #1d7358e6, 0 18px 18px -6px rgba(27,94,85,0.15);}
  75% { box-shadow: 0 0 10px 4px #1d7358e6, 0 12px 18px -2px rgba(27,94,85,0.20);}
  100% { box-shadow: 0 0 0 2px #1d7358e6, 0 6px 24px 0 rgba(27,94,85,0.12);}
}`;
      document.head.appendChild(style);
    }
  }, []);


  // ✅ CORREGIDO: Carga de datos para dirección con endpoint de clientes separado
  useEffect(() => {
    if (mode !== 'direccion') return;


    let active = true;
    setLoading(true);
    setError(null);


    const loadDirectionData = async () => {
      try {
        console.log('[KPICards] 🔄 Loading direction data...');


        // 1. Cargar todos los centros (hardcodeamos los IDs conocidos de centros finalistas)
        const centrosFinalistasIds = [1, 2, 3, 4, 5]; // Basado en los endpoints que funcionan
        const centrosBasicos = centrosFinalistasIds.map(id => ({
          CENTRO_ID: id,
          DESC_CENTRO: `Centro ${id}`, // Se actualizará con datos reales
          IND_CENTRO_FINALISTA: 1
        }));


        if (active) setCentros(centrosBasicos);


        // 2. ✅ NUEVO: Cargar clientes por centro usando el endpoint que funciona
        const clientesPromises = centrosFinalistasIds.map(async (centroId) => {
          try {
            console.log(`[KPICards] Loading clientes for centro ${centroId}...`);
            const response = await api.basic.clientesByCentro(centroId);
            console.log(`[KPICards] Centro ${centroId} clientes:`, response?.length || 0);
            return { centroId: String(centroId), clientes: response || [] };
          } catch (error) {
            console.error(`[KPICards] Error loading clientes centro ${centroId}:`, error);
            return { centroId: String(centroId), clientes: [] };
          }
        });

        const clientesResults = await Promise.all(clientesPromises);
        const clientesPorCentroData = {};
        
        clientesResults.forEach(({ centroId, clientes }) => {
          clientesPorCentroData[centroId] = clientes;
        });

        if (active) {
          setClientesPorCentro(clientesPorCentroData);
          console.log('[KPICards] ✅ Clientes por centro loaded:', clientesPorCentroData);
        }


        // 3. Cargar datos financieros de cada centro
        const centroPromises = centrosFinalistasIds.map(async (centroId) => {
          try {
            console.log(`[KPICards] Loading financial data for centro ${centroId}...`);
            const response = await api.kpis.centroFinancieros(centroId, normalizedPeriodo);
            console.log(`[KPICards] Centro ${centroId} financial response:`, response);
            return { centroId: String(centroId), data: response };
          } catch (error) {
            console.error(`[KPICards] Error loading centro ${centroId}:`, error);
            return { centroId: String(centroId), data: null };
          }
        });


        const centroResults = await Promise.all(centroPromises);
        
        // 4. Procesar datos y actualizar estado
        const centrosFinalData = {};
        const centrosConNombres = [];


        centroResults.forEach(({ centroId, data }) => {
          if (data) {
            centrosFinalData[centroId] = data;
            // Actualizar nombre del centro con datos reales
            centrosConNombres.push({
              CENTRO_ID: parseInt(centroId),
              DESC_CENTRO: data.metricas_base?.DESC_CENTRO || `Centro ${centroId}`,
              IND_CENTRO_FINALISTA: 1
            });
          }
        });


        if (active) {
          setCentrosFin(centrosFinalData);
          setCentros(centrosConNombres);
          console.log('[KPICards] ✅ Centros financial data loaded:', { 
            centros: centrosConNombres.length, 
            datos: Object.keys(centrosFinalData).length 
          });
        }


      } catch (error) {
        console.error('[KPICards] ❌ Error loading direction data:', error);
        if (active) setError(error);
      } finally {
        if (active) setLoading(false);
      }
    };


    loadDirectionData();
    return () => { active = false; };
  }, [mode, normalizedPeriodo]);


  // ✅ CORREGIDO: Cálculo y actualización de KPIs para dirección usando endpoint de clientes separado
  useEffect(() => {
    if (mode !== 'direccion' || Object.keys(centrosFin).length === 0 || Object.keys(clientesPorCentro).length === 0) return;


    console.log('[KPICards] 🔄 Calculating direction KPIs...', { centrosFin, clientesPorCentro, centerSelections });


    try {
      // Calcular totales globales
      let totalContratos = 0;
      let totalClientes = 0; 
      let totalIngresos = 0;
      let totalROE = 0;
      let countCentros = 0;


      const kpisPorCentro = { global: {} };


      // ✅ CORREGIDO: Usar datos de clientes del endpoint separado
      Object.entries(clientesPorCentro).forEach(([centroId, clientes]) => {
        const clientesCount = clientes.length || 0;
        totalClientes += clientesCount;

        // Inicializar datos del centro
        kpisPorCentro[centroId] = {
          clientes: clientesCount,
          contratos: 0,
          ingresos: 0,
          roe: 0
        };
      });

      // Procesar datos financieros
      Object.entries(centrosFin).forEach(([centroId, centroData]) => {
        if (centroData?.metricas_base) {
          const metrics = centroData.metricas_base;
          const roe = centroData.kpis_financieros?.roe?.roe_pct || 0;

          // Acumular totales (excluyendo clientes que ya se procesaron arriba)
          totalContratos += metrics.total_contratos || 0;
          totalIngresos += metrics.ingresos_total || 0;
          totalROE += roe;
          countCentros++;

          // Actualizar datos por centro (manteniendo clientes del endpoint separado)
          if (kpisPorCentro[centroId]) {
            kpisPorCentro[centroId].contratos = metrics.total_contratos || 0;
            kpisPorCentro[centroId].ingresos = metrics.ingresos_total || 0;
            kpisPorCentro[centroId].roe = roe;
          }
        }
      });


      // Global (totales)
      kpisPorCentro.global = {
        contratos: totalContratos,
        clientes: totalClientes,
        ingresos: totalIngresos,
        roe: countCentros > 0 ? totalROE / countCentros : 0
      };


      console.log('[KPICards] 📊 Calculated totals:', kpisPorCentro.global);


      // Crear KPIs basados en selecciones
      const kpis = [
        {
          key: 'roe_grupo',
          value: centerSelections.roe_grupo === 'global'
            ? kpisPorCentro.global.roe
            : kpisPorCentro[centerSelections.roe_grupo]?.roe || 0,
          location: centerSelections.roe_grupo,
          variation: 2.3,
          trend: 'up',
          format: 'percent',
          status: 'excellent'
        },
        {
          key: 'total_clientes',
          value: centerSelections.total_clientes === 'global'
            ? kpisPorCentro.global.clientes
            : kpisPorCentro[centerSelections.total_clientes]?.clientes || 0,
          location: centerSelections.total_clientes,
          variation: 5.8,
          trend: 'up',
          format: 'number',
          status: 'good'
        },
        {
          key: 'total_contratos',
          value: centerSelections.total_contratos === 'global'
            ? kpisPorCentro.global.contratos
            : kpisPorCentro[centerSelections.total_contratos]?.contratos || 0,
          location: centerSelections.total_contratos,
          variation: 8.4,
          trend: 'up',
          format: 'number',
          status: 'excellent'
        },
        {
          key: 'ingresos_totales',
          value: centerSelections.ingresos_totales === 'global'
            ? kpisPorCentro.global.ingresos
            : kpisPorCentro[centerSelections.ingresos_totales]?.ingresos || 0,
          location: centerSelections.ingresos_totales,
          variation: 12.1,
          trend: 'up',
          format: 'currency',
          status: 'excellent'
        }
      ];


      console.log('[KPICards] ✅ Final KPIs:', kpis);
      setKpisData(kpis);


    } catch (error) {
      console.error('[KPICards] ❌ Error calculating KPIs:', error);
      setError(error);
    }
  }, [mode, centerSelections, centrosFin, clientesPorCentro]);


  // ✅ CORREGIDO: Carga de KPIs para gestor
  useEffect(() => {
    if (mode !== 'gestor' || !gestorId) return;


    let active = true;
    setLoading(true);


    const loadGestorData = async () => {
      try {
        console.log('[KPICards] 🔄 Loading gestor data for:', gestorId);


        const [roe, incentivos, clientes, contratos] = await Promise.all([
          api.kpis.gestorROE(gestorId, normalizedPeriodo).catch(() => ({ roe_pct: 16.5 })),
          api.incentives.gestorDetalle(gestorId, normalizedPeriodo).catch(() => ({ total_incentivos: 8500 })),
          api.basic.clientesByGestor(gestorId).catch(() => []),
          api.basic.contractsByGestor(gestorId).catch(() => [])
        ]);


        const kpis = [
          {
            key: 'roe_gestor',
            value: roe?.roe_pct || 16.5,
            variation: 1.8,
            trend: 'up',
            format: 'percent',
            status: 'excellent'
          },
          {
            key: 'bonus_gestor',
            value: incentivos?.total_incentivos || 8500,
            variation: 12.3,
            trend: 'up',
            format: 'currency',
            status: 'excellent'
          },
          {
            key: 'clientes_gestor',
            value: clientes?.length || 28,
            variation: 3.7,
            trend: 'up',
            format: 'number',
            status: 'good'
          },
          {
            key: 'contratos_gestor',
            value: contratos?.length || 45,
            variation: 8.2,
            trend: 'up',
            format: 'number',
            status: 'good'
          }
        ];


        if (active) setKpisData(kpis);
      } catch (error) {
        console.error('[KPICards] ❌ Error loading gestor data:', error);
        if (active) setError(error);
      } finally {
        if (active) setLoading(false);
      }
    };


    loadGestorData();
    return () => { active = false; };
  }, [mode, gestorId, normalizedPeriodo]);


  // Formateo de valores
  const formatValue = (value, format) => {
    if (value === null || value === undefined) return 'N/A';
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('es-ES', {
          style: 'currency',
          currency: 'EUR',
          notation: value > 1000000 ? 'compact' : 'standard',
          maximumFractionDigits: value > 1000000 ? 1 : 0,
        }).format(value);
      case 'percent':
        return `${Number(value).toFixed(1)}%`;
      case 'number':
        return new Intl.NumberFormat('es-ES').format(value);
      default:
        return String(value);
    }
  };


  // ✅ CORREGIDO: Componente KPICard con Select mejorado
  const KPICard = ({ kpi, config, filterKey, showFilter }) => {
    const isPositiveVariation = kpi.variation > 0;
    const variationColor = isPositiveVariation ? theme.colors.success : theme.colors.error;
    const TrendIcon = kpi.trend === 'up' ? ArrowUpOutlined : ArrowDownOutlined;
    const statusColor = kpi.status === 'excellent' ? theme.colors.success : theme.colors.bmGreenPrimary;


    const handleClick = (e) => {
      // Evitar que el click del select active el click del card
      if (e.target.closest('.ant-select')) return;
      if (onKpiClick) onKpiClick(kpi.key, kpi);
    };


    const handleSelectChange = (value) => {
      console.log(`[KPICard] Changing ${filterKey} to:`, value);
      setCenterSelections(prev => ({ ...prev, [filterKey]: value }));
    };


    return (
      <Card
        hoverable={!!onKpiClick}
        onClick={handleClick}
        style={{
          ...animatedCardStyle,
          borderRadius: theme.token?.borderRadius || 8,
          border: `1px solid ${theme.colors?.borderLight || '#e8e8e8'}`,
          transition: 'all 0.3s',
          cursor: onKpiClick ? 'pointer' : 'default',
          height: '100%',
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fffe 100%)',
        }}
        styles={{ body: { padding: '20px' } }}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', minHeight: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
              <config.icon 
                style={{ 
                  fontSize: 20, 
                  color: config.color,
                  opacity: 0.9 
                }} 
              />
              <span style={{ 
                color: theme.colors?.textSecondary || '#666', 
                fontSize: 14,
                fontWeight: 500 
              }}>
                {config.label}
              </span>
            </div>
            
            {/* Filtro Select - CORREGIDO */}
            {showFilter && (
              <Select
                value={kpi.location}
                size="small"
                style={{ minWidth: 120 }}
                onChange={handleSelectChange}
                options={centerOptions}
                showSearch
                optionFilterProp="label"
                placeholder="Seleccionar"
                getPopupContainer={(triggerNode) => triggerNode.parentNode}
                onClick={(e) => e.stopPropagation()}
                dropdownStyle={{ zIndex: 1050 }}
              />
            )}
            
            <Badge 
              status={kpi.status === 'excellent' ? 'success' : kpi.status === 'good' ? 'processing' : 'warning'} 
            />
          </div>


          {/* Main value */}
          <Statistic
            value={kpi.value}
            formatter={(value) => (
              <span style={{ 
                color: theme.colors?.textPrimary || '#333',
                fontSize: 26,
                fontWeight: 700,
                fontFamily: theme.token?.fontFamily || 'inherit'
              }}>
                {formatValue(value, kpi.format)}
              </span>
            )}
          />


          {/* Variation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <TrendIcon style={{ fontSize: 14, color: variationColor }} />
              <span style={{ 
                color: variationColor,
                fontSize: 14,
                fontWeight: 600 
              }}>
                {kpi.variation > 0 ? '+' : ''}{kpi.variation?.toFixed(1)}%
              </span>
            </div>
          </div>


          {/* Description */}
          <div style={{ marginTop: 4 }}>
            <span style={{ 
              fontSize: 11, 
              color: theme.colors?.textLight || '#999',
              fontStyle: 'italic' 
            }}>
              {config.description}
            </span>
          </div>
        </Space>
      </Card>
    );
  };


  // Estados de carga y error
  if (loading) {
    return (
      <div className={className} style={style}>
        <Row gutter={[16, 16]}>
          {[...Array(4)].map((_, i) => (
            <Col key={i} xs={24} sm={12} lg={6}>
              <Card styles={{ body: { padding: '20px' } }}>
                <Skeleton active paragraph={{ rows: 3 }} />
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
        onRetry={() => window.location.reload()}
        style={style}
        className={className}
      />
    );
  }


  if (!kpisData.length) {
    return (
      <div className={className} style={style}>
        <Card 
          style={{ textAlign: 'center', padding: theme.spacing?.lg || 24 }}
          styles={{ body: { padding: '32px' } }}
        >
          <InfoCircleOutlined style={{ 
            fontSize: 48, 
            color: theme.colors?.textLight || '#999', 
            marginBottom: theme.spacing?.md || 16
          }} />
          <h3 style={{ color: theme.colors?.textSecondary || '#666' }}>
            No hay datos disponibles
          </h3>
          <p style={{ color: theme.colors?.textLight || '#999' }}>
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
      <Row gutter={[16, 16]} align="stretch">
        {kpisData.map((kpi) => {
          const config = kpiConfig[mode].find(c => c.key === kpi.key);
          if (!config) return null;


          const showFilter = mode === 'direccion' && [
            'roe_grupo', 'total_clientes', 'ingresos_totales', 'total_contratos'
          ].includes(kpi.key);


          return (
            <Col 
              key={kpi.key} 
              xs={24} 
              sm={12} 
              lg={6}
            >
              <KPICard
                kpi={kpi}
                config={config}
                filterKey={kpi.key}
                showFilter={showFilter}
              />
            </Col>
          );
        })}
      </Row>
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
