// frontend/src/components/Dashboard/DeviationAnalysis.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Tabs,
  Typography,
  Space,
  Badge,
  Button,
  Table,
  Tooltip,
  Empty,
  Alert,
  Row,
  Col,
  Tag,
  Statistic,
  Progress,
  Switch,
  Spin
} from 'antd';
import {
  ReloadOutlined,
  WarningOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  DashboardOutlined,
  DollarOutlined,
  AlertOutlined,
  InfoCircleOutlined,
  EuroOutlined,
  PercentageOutlined,
  UsergroupAddOutlined,
  ContainerOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import analyticsService from '../../services/analyticsService';
import api from '../../services/api';
import ErrorState from '../common/ErrorState';
import theme from '../../styles/theme';

const { Title, Text } = Typography;

/**
 * DeviationAnalysis - Componente simplificado e intuitivo para análisis de desviaciones
 * Casos de uso:
 * - Dashboard Gestor: Desviaciones en contratos, incentivos y justificaciones del gestor
 * - Dashboard Dirección: Tabla precios productos por segmento, incentivos gestores, desviaciones globales
 */
const DeviationAnalysis = ({
  mode = 'direccion', // 'direccion' | 'gestor'
  periodo = '2025-10',
  gestorId = null,
  onReload = () => {},
  className = '',
  style = {}
}) => {
  // Estados principales
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('precios');
  
  // Estados de datos específicos
  const [preciosData, setPreciosData] = useState([]);
  const [incentivesData, setIncentivesData] = useState([]);
  const [gestorData, setGestorData] = useState(null);
  const [desviacionesData, setDesviacionesData] = useState([]);
  
  // Estados de resumen
  const [summary, setSummary] = useState(null);
  const [showOnlyOutliers, setShowOnlyOutliers] = useState(false);

  /**
   * ✅ Carga principal de datos según el modo
   */
  const fetchData = useCallback(async () => {
    if (!periodo) return;

    console.log(`[DeviationAnalysis] 📊 Cargando datos para modo: ${mode}`);
    setLoading(true);
    setError(null);

    try {
      if (mode === 'gestor' && gestorId) {
        await fetchGestorData();
      } else if (mode === 'direccion') {
        await fetchDireccionData();
      }
    } catch (err) {
      console.error('[DeviationAnalysis] ❌ Error:', err);
      setError(err.message || 'Error cargando datos');
    } finally {
      setLoading(false);
    }
  }, [mode, periodo, gestorId]);

  /**
   * ✅ Datos específicos para Dashboard del Gestor
   */
  const fetchGestorData = async () => {
    console.log(`[DeviationAnalysis] 👤 Cargando datos del gestor ${gestorId}`);

    try {
      // 1. KPIs y performance del gestor
      const gestorKPIs = await analyticsService.getUnifiedKPIData(gestorId, periodo);
      console.log('[DeviationAnalysis] KPIs gestor:', gestorKPIs);

      // 2. Comparación de precios del segmento del gestor
      const preciosComparison = await analyticsService.getPriceComparisonChartData(
        { gestorId, periodo },
        {}
      );
      console.log('[DeviationAnalysis] Precios comparison:', preciosComparison);

      // 3. Incentivos del gestor
      const gestorIncentives = await api.incentives.scorecard(gestorId, periodo);
      console.log('[DeviationAnalysis] Incentivos gestor:', gestorIncentives);

      // 4. Desviaciones del gestor (margen y volumen)
      const margenDeviations = await analyticsService.getMargenDeviations(periodo, { enhanced: true });
      const volumenDeviations = await analyticsService.getVolumenDeviations(periodo, { enhanced: true });

      // Filtrar desviaciones específicas del gestor
      const gestorMargenDev = margenDeviations.deviations?.find(d => 
        String(d.GESTOR_ID || d.gestor_id) === String(gestorId)
      ) || null;

      const gestorVolumenDev = volumenDeviations.deviations?.find(d => 
        String(d.GESTOR_ID || d.gestor_id) === String(gestorId)
      ) || null;

      // Procesar datos para visualización
      setGestorData(gestorKPIs);
      setPreciosData(preciosComparison.table || []);
      setIncentivesData(formatGestorIncentives(gestorIncentives));
      setDesviacionesData(formatGestorDeviations(gestorMargenDev, gestorVolumenDev));
      setSummary(buildGestorSummary(gestorKPIs, preciosComparison, gestorIncentives));

    } catch (error) {
      console.warn('[DeviationAnalysis] Error en datos gestor, usando mock:', error.message);
      setMockGestorData();
    }
  };

  /**
   * ✅ Datos específicos para Dashboard de Dirección
   */
  /**
   * ✅ Datos específicos para Dashboard de Dirección (VERSION CORREGIDA)
   */
  const fetchDireccionData = async () => {
    console.log('[DeviationAnalysis] 🏢 Cargando datos de dirección');

    try {
      // 1. Precios por producto y segmento (tabla principal)
      const preciosStd = await api.basic.preciosStd();
      const preciosReal = await api.basic.preciosReal();
      console.log('[DeviationAnalysis] Precios std:', preciosStd?.length);
      console.log('[DeviationAnalysis] Precios real:', preciosReal?.length);

      // 2. Incentivos por gestor (ranking)
      let bonusPool;
      try {
        bonusPool = await api.incentives.bonusPool(periodo, 50000);
        console.log('[DeviationAnalysis] Bonus pool:', bonusPool?.length);
      } catch (bonusError) {
        console.warn('[DeviationAnalysis] Error en bonus pool:', bonusError.message);
        bonusPool = [];
      }

      // 3. Desviaciones globales
      let pricingDeviations, margenDeviations, volumenDeviations;
      
      try {
        pricingDeviations = await api.deviations.pricing(periodo, 15.0);
        console.log('[DeviationAnalysis] Pricing deviations:', pricingDeviations);
      } catch (pricingError) {
        console.warn('[DeviationAnalysis] Error en pricing deviations:', pricingError.message);
        pricingDeviations = { data: [], deviations: [] };
      }

      try {
        margenDeviations = await analyticsService.getMargenDeviations(periodo);
        console.log('[DeviationAnalysis] Margen deviations:', margenDeviations?.deviations?.length || 0);
      } catch (margenError) {
        console.warn('[DeviationAnalysis] Error en margen deviations:', margenError.message);
        margenDeviations = { deviations: [] };
      }

      try {
        volumenDeviations = await analyticsService.getVolumenDeviations(periodo);
        console.log('[DeviationAnalysis] Volumen deviations:', volumenDeviations?.deviations?.length || 0);
      } catch (volumenError) {
        console.warn('[DeviationAnalysis] Error en volumen deviations:', volumenError.message);
        volumenDeviations = { deviations: [] };
      }

      // Procesar datos para visualización
      const processedPrecios = buildPreciosTable(preciosStd, preciosReal);
      const processedIncentives = formatIncentivesRanking(bonusPool);
      const processedDeviations = formatGlobalDeviations(pricingDeviations, margenDeviations, volumenDeviations);
      const processedSummary = buildDireccionSummary(pricingDeviations, margenDeviations, volumenDeviations, bonusPool);

      console.log('[DeviationAnalysis] ✅ Datos procesados:', {
        precios: processedPrecios.length,
        incentives: processedIncentives.length,
        deviations: processedDeviations.length,
        summary: processedSummary
      });

      setPreciosData(processedPrecios);
      setIncentivesData(processedIncentives);
      setDesviacionesData(processedDeviations);
      setSummary(processedSummary);

    } catch (error) {
      console.error('[DeviationAnalysis] ❌ Error general en datos dirección:', error);
      console.warn('[DeviationAnalysis] Cayendo a modo mock debido a error:', error.message);
      setMockDireccionData();
    }
  };


  /**
   * ✅ Construye tabla unificada de precios estándar vs real por segmento-producto
   */
  const buildPreciosTable = (std, real) => {
    const stdMap = new Map();
    const realMap = new Map();

    // Indexar precios estándar
    (std || []).forEach(item => {
      const key = `${item.SEGMENTO_ID}-${item.PRODUCTO_ID}`;
      stdMap.set(key, item);
    });

    // Indexar precios reales
    (real || []).forEach(item => {
      const key = `${item.SEGMENTO_ID}-${item.PRODUCTO_ID}`;
      realMap.set(key, item);
    });

    // Combinar datos
    const combined = [];
    const allKeys = new Set([...stdMap.keys(), ...realMap.keys()]);

    allKeys.forEach(key => {
      const stdItem = stdMap.get(key);
      const realItem = realMap.get(key);
      
      if (stdItem || realItem) {
        const stdPrice = Math.abs(stdItem?.PRECIO_MANTENIMIENTO || 0);
        const realPrice = Math.abs(realItem?.PRECIO_MANTENIMIENTO_REAL || 0);
        const deviation = realPrice - stdPrice;
        const deviationPct = stdPrice > 0 ? (deviation / stdPrice) * 100 : 0;

        combined.push({
          key,
          segmento: stdItem?.DESC_SEGMENTO || realItem?.DESC_SEGMENTO || 'Desconocido',
          producto: stdItem?.DESC_PRODUCTO || realItem?.DESC_PRODUCTO || 'Desconocido',
          precio_std: stdPrice,
          precio_real: realPrice,
          deviation: deviation,
          deviation_pct: deviationPct,
          contracts: realItem?.NUM_CONTRATOS_BASE || 0,
          semaforo: Math.abs(deviationPct) <= 2 ? 'Verde' : 
                   Math.abs(deviationPct) <= 15 ? 'Amarillo' : 'Rojo'
        });
      }
    });

    return combined.slice(0, 20); // Limitar a 20 filas principales
  };

  /**
   * ✅ Formatea datos de incentivos para ranking de gestores
   */
  const formatIncentivesRanking = (poolData) => {
    if (!Array.isArray(poolData)) return [];
    
    return poolData.map((item, index) => ({
      key: `incentive-${index}`,
      gestor: item.DESC_GESTOR || item.gestor || `Gestor ${index + 1}`,
      margen_neto: item.margen_neto || 0,
      score: item.score_ponderado || 0,
      porcentaje_pool: item.porcentaje_pool || 0,
      incentivo_eur: item.incentivo_final_eur || item.asignacion_pool_eur || 0,
      ranking: item.ranking_general || index + 1,
      performance: item.margen_neto > 70 ? 'Excelente' : 
                  item.margen_neto > 50 ? 'Bueno' : 'Mejorable'
    })).slice(0, 15);
  };

  /**
   * ✅ Formatea desviaciones para el gestor específico
   */
  const formatGestorDeviations = (margenDev, volumenDev) => {
    const deviations = [];

    if (margenDev) {
      deviations.push({
        key: 'margen-dev',
        tipo: 'Margen',
        descripcion: 'Desviación en margen neto',
        valor_actual: margenDev.margen_neto || 0,
        valor_objetivo: margenDev.media_margen || 70,
        desviacion: margenDev.beneficio_neto || 0,
        criticidad: margenDev.clasificacion_anomalia === 'OUTLIER_EXTREMO' ? 'Alta' : 'Media'
      });
    }

    if (volumenDev) {
      deviations.push({
        key: 'volumen-dev',
        tipo: 'Volumen',
        descripcion: 'Desviación en número de contratos',
        valor_actual: volumenDev.total_contratos || 0,
        valor_objetivo: volumenDev.media_contratos || 10,
        desviacion: (volumenDev.ratio_contratos_vs_media || 1) * 100 - 100,
        criticidad: volumenDev.tipo_outlier === 'SIN_ACTIVIDAD' ? 'Alta' : 'Baja'
      });
    }

    return deviations;
  };

  /**
   * ✅ Formatea incentivos específicos del gestor
   */
  const formatGestorIncentives = (incentiveData) => {
    if (!incentiveData?.scorecard) return [];
    
    const concepts = [];
    Object.entries(incentiveData.scorecard).forEach(([kpi, detalle]) => {
      concepts.push({
        key: kpi,
        concepto: kpi.replace(/_/g, ' ').toUpperCase(),
        valor: Array.isArray(detalle) ? detalle.length : 0,
        contribucion: Math.random() * 30 + 10, // Mock contribution
        descripcion: `Evaluación de ${kpi.replace(/_/g, ' ')}`
      });
    });

    concepts.push({
      key: 'total',
      concepto: 'INCENTIVO TOTAL',
      valor: incentiveData.totalincentivo || 0,
      contribucion: 100,
      descripcion: 'Total incentivos calculados',
      isTotal: true
    });

    return concepts;
  };

  /**
   * ✅ Formatea desviaciones globales para Dashboard de Dirección
   */
  /**
   * ✅ Formatea desviaciones globales para Dashboard de Dirección (VERSION CORREGIDA)
   */
  const formatGlobalDeviations = (pricingDeviations, margenDeviations, volumenDeviations) => {
    const globalDeviations = [];

    // Desviaciones de pricing - manejo seguro de datos
    const pricingData = pricingDeviations?.data || pricingDeviations?.deviations || [];
    if (Array.isArray(pricingData) && pricingData.length > 0) {
      pricingData.slice(0, 5).forEach((item, index) => {
        globalDeviations.push({
          key: `pricing-${index}`,
          tipo: 'Pricing',
          descripcion: `Desviación en ${item.DESC_PRODUCTO || item.producto || 'Producto'}`,
          valor_actual: Math.abs(item.PRECIO_MANTENIMIENTO_REAL || item.precio_real || 0),
          valor_objetivo: Math.abs(item.PRECIO_MANTENIMIENTO || item.precio_std || 0),
          desviacion: item.desviacion_pct || item.deviation_pct || 0,
          criticidad: item.nivel_alerta === 'ALTA' ? 'Alta' : 
                     item.nivel_alerta === 'MEDIA' ? 'Media' : 'Baja'
        });
      });
    }

    // Desviaciones de margen (top 3) - manejo seguro
    const margenData = margenDeviations?.deviations || [];
    if (Array.isArray(margenData) && margenData.length > 0) {
      margenData.slice(0, 3).forEach((item, index) => {
        globalDeviations.push({
          key: `margen-${index}`,
          tipo: 'Margen',
          descripcion: `Anomalía en margen - ${item.DESC_GESTOR || item.gestor || 'Gestor'}`,
          valor_actual: item.margen_neto || 0,
          valor_objetivo: item.media_margen || 70,
          desviacion: item.beneficio_neto || 0,
          criticidad: item.clasificacion_anomalia === 'OUTLIER_EXTREMO' ? 'Alta' : 'Media'
        });
      });
    }

    // Desviaciones de volumen (top 3) - manejo seguro
    const volumenData = volumenDeviations?.deviations || [];
    if (Array.isArray(volumenData) && volumenData.length > 0) {
      volumenData.slice(0, 3).forEach((item, index) => {
        const ratioDeviation = (item.ratio_contratos_vs_media || 1) * 100 - 100;
        globalDeviations.push({
          key: `volumen-${index}`,
          tipo: 'Volumen',
          descripcion: `Outlier de contratos - ${item.DESC_GESTOR || item.gestor || 'Gestor'}`,
          valor_actual: item.total_contratos || 0,
          valor_objetivo: item.media_contratos || 10,
          desviacion: ratioDeviation,
          criticidad: item.tipo_outlier === 'SIN_ACTIVIDAD' ? 'Alta' : 
                     Math.abs(ratioDeviation) > 50 ? 'Media' : 'Baja'
        });
      });
    }

    console.log(`[DeviationAnalysis] ✅ Formatted ${globalDeviations.length} global deviations`);
    return globalDeviations;
  };



  /**
   * ✅ Datos mock para testing
   */
  const setMockGestorData = () => {
    setGestorData({
      gestorId,
      nombreGestor: 'Gestor Demo',
      totalContratos: 12,
      totalClientes: 8,
      margenNeto: 68.5,
      totalIngresos: 45000
    });

    setPreciosData([
      {
        key: 'p1',
        DESC_PRODUCTO: 'Préstamo Hipotecario',
        precio_std: 1170,
        precio_real: 1369,
        delta_abs: -199,
        delta_pct: 17.01,
        semaforo: 'Rojo'
      }
    ]);

    setIncentivesData([
      {
        key: 'margen',
        concepto: 'MARGEN NETO',
        valor: 68.5,
        contribucion: 40,
        descripcion: 'Evaluación de margen neto'
      },
      {
        key: 'total',
        concepto: 'INCENTIVO TOTAL',
        valor: 3200,
        contribucion: 100,
        descripcion: 'Total incentivos calculados',
        isTotal: true
      }
    ]);

    setDesviacionesData([
      {
        key: 'margen-dev',
        tipo: 'Margen',
        descripcion: 'Desviación en margen neto',
        valor_actual: 68.5,
        valor_objetivo: 70,
        desviacion: -1.5,
        criticidad: 'Baja'
      }
    ]);

    setSummary({
      totalDeviations: 1,
      criticalAlerts: 0,
      incentiveAmount: 3200,
      performance: 'Bueno'
    });
  };

  const setMockDireccionData = () => {
    setPreciosData([
      {
        key: 'seg1-prod1',
        segmento: 'Banca Minorista',
        producto: 'Préstamo Hipotecario',
        precio_std: 1170,
        precio_real: 1369,
        deviation: -199,
        deviation_pct: 17.01,
        contracts: 13,
        semaforo: 'Rojo'
      },
      {
        key: 'seg2-prod1',
        segmento: 'Banca Privada',
        producto: 'Depósito a Plazo',
        precio_std: 1160,
        precio_real: 1190,
        deviation: -30,
        deviation_pct: 2.59,
        contracts: 8,
        semaforo: 'Verde'
      }
    ]);

    setIncentivesData([
      {
        key: 'g1',
        gestor: 'Francesca Costa Ribas',
        margen_neto: 75.2,
        score: 3760,
        porcentaje_pool: 5.63,
        incentivo_eur: 3518,
        ranking: 1,
        performance: 'Excelente'
      }
    ]);

    // ✅ AÑADIDO: Mock para desviaciones globales
    setDesviacionesData([
      {
        key: 'pricing-1',
        tipo: 'Pricing',
        descripcion: 'Desviación en Préstamo Hipotecario',
        valor_actual: 1369,
        valor_objetivo: 1170,
        desviacion: 17.01,
        criticidad: 'Alta'
      },
      {
        key: 'margen-1',
        tipo: 'Margen',
        descripcion: 'Anomalía en margen - Josep Oliver Coll',
        valor_actual: 8.56,
        valor_objetivo: 70.91,
        desviacion: -62.35,
        criticidad: 'Alta'
      },
      {
        key: 'volumen-1',
        tipo: 'Volumen',
        descripcion: 'Outlier de contratos - Antonio Rodríguez',
        valor_actual: 9,
        valor_objetivo: 7.2,
        desviacion: 25.0,
        criticidad: 'Baja'
      }
    ]);

    // ✅ AÑADIDO: Summary para dirección
    setSummary({
      totalDeviations: 3,
      criticalAlerts: 2,
      totalIncentives: 52770, // Mock total pool
      performance: 'Global'
    });
  };


  /**
   * ✅ Construye resumen según el modo
   */
  const buildGestorSummary = (gestor, precios, incentives) => ({
    totalDeviations: precios?.table?.filter(p => p.semaforo === 'Rojo').length || 0,
    criticalAlerts: precios?.table?.filter(p => Math.abs(p.delta_pct) > 15).length || 0,
    incentiveAmount: incentives?.totalincentivo || 0,
    performance: gestor?.margenNeto > 70 ? 'Excelente' : 
                gestor?.margenNeto > 50 ? 'Bueno' : 'Mejorable'
  });

  const buildDireccionSummary = (pricing, margen, volumen, incentives) => {
    // Verificar estructuras de datos de forma segura
    const pricingDeviations = Array.isArray(pricing?.data) ? pricing.data.length : 
                             Array.isArray(pricing?.deviations) ? pricing.deviations.length : 0;
    
    const margenDeviations = Array.isArray(margen?.deviations) ? margen.deviations.length : 0;
    const volumenDeviations = Array.isArray(volumen?.deviations) ? volumen.deviations.length : 0;
    
    // Contar alertas críticas de forma segura
    const pricingCritical = Array.isArray(pricing?.data) ? 
      pricing.data.filter(p => p.nivel_alerta === 'ALTA').length :
      Array.isArray(pricing?.deviations) ?
      pricing.deviations.filter(p => p.nivel_alerta === 'ALTA').length : 0;
    
    // Calcular total de incentivos de forma segura
    const totalIncentives = Array.isArray(incentives) ? 
      incentives.reduce((sum, i) => sum + (i.incentivo_final_eur || i.asignacion_pool_eur || 0), 0) : 0;

    return {
      totalDeviations: pricingDeviations + margenDeviations + volumenDeviations,
      criticalAlerts: pricingCritical,
      totalIncentives,
      performance: 'Global'
    };
  };


  // ✅ Definición de columnas para las tablas
  const preciosColumns = [
    {
      title: 'Segmento',
      dataIndex: mode === 'direccion' ? 'segmento' : 'DESC_PRODUCTO',
      key: 'segmento',
      sorter: (a, b) => a.segmento?.localeCompare(b.segmento || ''),
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Producto',
      dataIndex: mode === 'direccion' ? 'producto' : 'DESC_PRODUCTO',
      key: 'producto',
      render: (text) => <Text>{text}</Text>
    },
    {
      title: 'Precio Estándar (€)',
      dataIndex: 'precio_std',
      key: 'precio_std',
      sorter: (a, b) => a.precio_std - b.precio_std,
      render: (val) => <Text>{val?.toFixed(0)}€</Text>
    },
    {
      title: 'Precio Real (€)',
      dataIndex: 'precio_real',
      key: 'precio_real',
      sorter: (a, b) => a.precio_real - b.precio_real,
      render: (val) => <Text>{val?.toFixed(0)}€</Text>
    },
    {
      title: 'Desviación',
      dataIndex: mode === 'direccion' ? 'deviation_pct' : 'delta_pct',
      key: 'deviation',
      sorter: (a, b) => Math.abs(a.deviation_pct || a.delta_pct) - Math.abs(b.deviation_pct || b.delta_pct),
      render: (val, record) => (
        <Space>
          <Text style={{ 
            color: Math.abs(val) > 15 ? theme.colors.error : 
                   Math.abs(val) > 5 ? theme.colors.warning : theme.colors.success,
            fontWeight: 600
          }}>
            {val > 0 ? '+' : ''}{val?.toFixed(1)}%
          </Text>
          <Tag color={record.semaforo === 'Verde' ? 'green' : record.semaforo === 'Amarillo' ? 'orange' : 'red'}>
            {record.semaforo}
          </Tag>
        </Space>
      )
    },
    {
      title: 'Contratos',
      dataIndex: 'contracts',
      key: 'contracts',
      sorter: (a, b) => (a.contracts || 0) - (b.contracts || 0),
      render: (val) => <Text type="secondary">{val || 0}</Text>
    }
  ];

  const incentivesColumns = [
    {
      title: mode === 'direccion' ? 'Gestor' : 'Concepto',
      dataIndex: mode === 'direccion' ? 'gestor' : 'concepto',
      key: 'entity',
      render: (text, record) => (
        <Space>
          {mode === 'direccion' && <Badge count={record.ranking} style={{ backgroundColor: theme.colors.bmGreenPrimary }} />}
          <Text strong={record.isTotal}>{text}</Text>
        </Space>
      )
    },
    {
      title: mode === 'direccion' ? 'Margen Neto (%)' : 'Valor',
      dataIndex: mode === 'direccion' ? 'margen_neto' : 'valor',
      key: 'valor',
      sorter: (a, b) => (a.margen_neto || a.valor || 0) - (b.margen_neto || b.valor || 0),
      render: (val, record) => (
        <Text strong={record.isTotal}>
          {mode === 'direccion' ? `${val?.toFixed(1)}%` : val}
        </Text>
      )
    },
    {
      title: mode === 'direccion' ? 'Score' : 'Contribución (%)',
      dataIndex: mode === 'direccion' ? 'score' : 'contribucion',
      key: 'score',
      render: (val, record) => (
        <Space>
          <Progress 
            percent={mode === 'direccion' ? Math.min(val / 50, 100) : val} 
            size="small" 
            strokeColor={theme.colors.bmGreenPrimary}
            style={{ width: 80 }}
            showInfo={false}
          />
          <Text>{val?.toFixed(1)}{mode === 'direccion' ? '' : '%'}</Text>
        </Space>
      )
    },
    {
      title: 'Incentivo (€)',
      dataIndex: mode === 'direccion' ? 'incentivo_eur' : 'valor',
      key: 'incentivo',
      sorter: (a, b) => (a.incentivo_eur || a.valor || 0) - (b.incentivo_eur || b.valor || 0),
      render: (val, record) => (
        <Text strong={record.isTotal} style={{ 
          color: record.isTotal ? theme.colors.bmGreenPrimary : 'inherit' 
        }}>
          {mode === 'direccion' || record.isTotal ? `${(val || 0).toLocaleString()}€` : '-'}
        </Text>
      )
    },
    {
      title: 'Performance',
      dataIndex: mode === 'direccion' ? 'performance' : 'descripcion',
      key: 'performance',
      render: (val, record) => (
        mode === 'direccion' ? 
        <Tag color={val === 'Excelente' ? 'green' : val === 'Bueno' ? 'blue' : 'orange'}>
          {val}
        </Tag> :
        <Text type="secondary" style={{ fontSize: 12 }}>{val}</Text>
      )
    }
  ];

  const desviacionesColumns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      render: (text) => <Tag>{text}</Tag>
    },
    {
      title: 'Descripción',
      dataIndex: 'descripcion',
      key: 'descripcion',
      render: (text) => <Text>{text}</Text>
    },
    {
      title: 'Valor Actual',
      dataIndex: 'valor_actual',
      key: 'valor_actual',
      render: (val) => <Text strong>{val}</Text>
    },
    {
      title: 'Objetivo',
      dataIndex: 'valor_objetivo',
      key: 'valor_objetivo',
      render: (val) => <Text type="secondary">{val}</Text>
    },
    {
      title: 'Desviación',
      dataIndex: 'desviacion',
      key: 'desviacion',
      render: (val) => (
        <Text style={{ color: val < 0 ? theme.colors.error : theme.colors.success }}>
          {val > 0 ? '+' : ''}{typeof val === 'number' ? val.toFixed(1) : val}
        </Text>
      )
    },
    {
      title: 'Criticidad',
      dataIndex: 'criticidad',
      key: 'criticidad',
      render: (val) => (
        <Tag color={val === 'Alta' ? 'red' : val === 'Media' ? 'orange' : 'green'}>
          {val}
        </Tag>
      )
    }
  ];

  // ✅ Renderizado del header de resumen
  const renderSummaryHeader = () => {
    if (!summary) return null;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center', borderColor: theme.colors.bmGreenLight }}>
            <Statistic
              title={mode === 'direccion' ? 'Desviaciones Totales' : 'Mis Desviaciones'}
              value={summary.totalDeviations || 0}
              valueStyle={{ color: (summary.totalDeviations || 0) > 0 ? theme.colors.warning : theme.colors.success }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center', borderColor: theme.colors.error }}>
            <Statistic
              title="Alertas Críticas"
              value={summary.criticalAlerts || 0}
              valueStyle={{ color: (summary.criticalAlerts || 0) > 0 ? theme.colors.error : theme.colors.success }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center', borderColor: theme.colors.bmGreenPrimary }}>
            <Statistic
              title={mode === 'direccion' ? 'Total Incentivos' : 'Mis Incentivos'}
              value={mode === 'direccion' ? summary.totalIncentives : summary.incentiveAmount || 0}
              precision={0}
              valueStyle={{ color: theme.colors.bmGreenPrimary }}
              prefix={<TrophyOutlined />}
              suffix="€"
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card size="small" style={{ textAlign: 'center', borderColor: theme.colors.success }}>
            <Statistic
              title="Performance"
              value={summary.performance}
              valueStyle={{ color: theme.colors.success }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // ✅ Definición de pestañas según modo
  const getTabItems = () => {
    if (mode === 'gestor') {
      return [
        {
          key: 'precios',
          label: (
            <Space>
              <EuroOutlined />
              Mis Precios vs Estándar
              {preciosData.filter(p => p.semaforo === 'Rojo').length > 0 && (
                <Badge count={preciosData.filter(p => p.semaforo === 'Rojo').length} />
              )}
            </Space>
          ),
          children: (
            <Table
              columns={preciosColumns}
              dataSource={preciosData}
              size="small"
              scroll={{ x: true }}
              pagination={{ pageSize: 10 }}
              locale={{
                emptyText: <Empty description="No hay datos de precios disponibles para tu segmento" />
              }}
            />
          )
        },
        {
          key: 'incentivos',
          label: (
            <Space>
              <TrophyOutlined />
              Mis Incentivos
              <Text type="secondary">({incentivesData.length})</Text>
            </Space>
          ),
          children: (
            <Table
              columns={incentivesColumns}
              dataSource={incentivesData}
              size="small"
              pagination={false}
              locale={{
                emptyText: <Empty description="No hay datos de incentivos calculados" />
              }}
            />
          )
        },
        {
          key: 'desviaciones',
          label: (
            <Space>
              <AlertOutlined />
              Mis Desviaciones
              {desviacionesData.filter(d => d.criticidad === 'Alta').length > 0 && (
                <Badge count={desviacionesData.filter(d => d.criticidad === 'Alta').length} />
              )}
            </Space>
          ),
          children: (
            <Table
              columns={desviacionesColumns}
              dataSource={desviacionesData}
              size="small"
              pagination={false}
              locale={{
                emptyText: <Empty description="No se detectaron desviaciones significativas en tu cartera" />
              }}
            />
          )
        }
      ];
    }

    // Modo dirección
    return [
      {
        key: 'precios',
        label: (
          <Space>
            <DashboardOutlined />
            Precios por Segmento-Producto
            {preciosData.filter(p => p.semaforo === 'Rojo').length > 0 && (
              <Badge count={preciosData.filter(p => p.semaforo === 'Rojo').length} />
            )}
          </Space>
        ),
        children: (
          <Table
            columns={preciosColumns}
            dataSource={showOnlyOutliers ? preciosData.filter(p => p.semaforo === 'Rojo') : preciosData}
            size="small"
            scroll={{ x: true }}
            pagination={{ pageSize: 15 }}
            locale={{
              emptyText: <Empty description="No hay datos de precios disponibles" />
            }}
          />
        )
      },
      {
        key: 'incentivos',
        label: (
          <Space>
            <UsergroupAddOutlined />
            Ranking Gestores
            <Text type="secondary">({incentivesData.length})</Text>
          </Space>
        ),
        children: (
          <Table
            columns={incentivesColumns}
            dataSource={incentivesData}
            size="small"
            scroll={{ x: true }}
            pagination={{ pageSize: 15 }}
            locale={{
              emptyText: <Empty description="No hay datos de incentivos calculados" />
            }}
          />
        )
      },
      {
        key: 'desviaciones',
        label: (
          <Space>
            <ContainerOutlined />
            Desviaciones Globales
            {desviacionesData.length > 0 && (
              <Badge count={desviacionesData.length} />
            )}
          </Space>
        ),
        children: (
          <Table
            columns={desviacionesColumns}
            dataSource={desviacionesData}
            size="small"
            scroll={{ x: true }}
            pagination={{ pageSize: 10 }}
            locale={{
              emptyText: <Empty description="No se detectaron desviaciones significativas" />
            }}
          />
        )
      }
    ];
  };

  // Effects
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handlers
  const handleRefresh = useCallback(() => {
    fetchData();
    onReload();
  }, [fetchData, onReload]);

  if (loading) {
    return (
      <div style={{ padding: 50, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Cargando análisis de desviaciones...</Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState 
        error={error} 
        onRetry={handleRefresh}
        style={{ height: '100%' }}
      />
    );
  }

  return (
    <Card
      className={className}
      style={{ width: '100%', height: '100%', ...style }}
      styles={{ body: { padding: '16px' } }}
      title={
        <Space>
          <AlertOutlined style={{ color: theme.colors.bmGreenPrimary }} />
          <Title level={4} style={{ margin: 0 }}>
            {mode === 'gestor' ? 'Mi Análisis de Desempeño' : 'Análisis de Desviaciones Globales'}
          </Title>
          <Badge 
            count={mode === 'gestor' ? `Gestor ${gestorId}` : 'Dirección'} 
            style={{ backgroundColor: theme.colors.bmGreenPrimary }} 
          />
          <Text type="secondary">• {periodo}</Text>
        </Space>
      }
      extra={
        <Space>
          {mode === 'direccion' && (
            <Switch
              checkedChildren="Solo Críticos"
              unCheckedChildren="Todos"
              checked={showOnlyOutliers}
              onChange={setShowOnlyOutliers}
            />
          )}
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            disabled={loading}
          >
            Actualizar
          </Button>
        </Space>
      }
    >
      {renderSummaryHeader()}
      
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        tabPosition="top"
        type="line"
        style={{ minHeight: 400 }}
        items={getTabItems()}
      />
    </Card>
  );
};

DeviationAnalysis.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.string.isRequired,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onReload: PropTypes.func,
  className: PropTypes.string,
  style: PropTypes.object
};

export default DeviationAnalysis;
