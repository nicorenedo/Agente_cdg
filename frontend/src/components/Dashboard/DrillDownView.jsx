// frontend/src/components/Dashboard/DrillDownView.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Card, 
  Table, 
  Input, 
  Button, 
  Space, 
  Tag, 
  Tooltip, 
  Typography, 
  Row, 
  Col,
  Statistic,
  Empty,
  Divider,
  Alert,
  Progress
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  BankOutlined,
  UserOutlined,
  FileTextOutlined,
  DollarOutlined,
  TrophyOutlined,
  PercentageOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  BarChartOutlined,
  TeamOutlined,
  AppstoreOutlined,
  CalendarOutlined,
  EuroCircleOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import analyticsService from '../../services/analyticsService';
import ErrorState from '../common/ErrorState';
import Loader from '../common/Loader';
import theme from '../../styles/theme';

const { Search } = Input;
const { Title, Text } = Typography;

const DrillDownView = ({
  mode = 'direccion',
  periodo,
  gestorId = null,
  onSelectLeaf = null,
  refreshToken = null,
  style = {},
  className = '',
}) => {
  // Normalizar período
  const normalizedPeriodo = useMemo(() => {
    if (!periodo) return "2025-10";
    if (typeof periodo === 'string') return periodo;
    if (typeof periodo === 'object') {
      return periodo.latest || periodo.periodo || periodo.value || "2025-10";
    }
    return String(periodo);
  }, [periodo]);

  // Estados
  const [rootData, setRootData] = useState([]);
  const [expandedRowKeys, setExpandedRowKeys] = useState([]);
  const [childDataMap, setChildDataMap] = useState({});
  const [loadingChildren, setLoadingChildren] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [metricsCache, setMetricsCache] = useState({});

  // ✅ CONFIGURACIÓN ACTUALIZADA con nuevos endpoints de métricas
  const drillConfig = useMemo(() => ({
    direccion: [
      { 
        key: 'centros', 
        label: 'Centros', 
        icon: BankOutlined, 
        color: theme.colors.bmGreenPrimary,
        endpoint: () => api.basic.centros(),
        metricsEndpoint: (centroId) => Promise.all([
          analyticsService.getCentroKPIsFinancieros(centroId, normalizedPeriodo),
          analyticsService.getCentroMargen(centroId, normalizedPeriodo),
          analyticsService.getCentroBonusTotal(centroId, normalizedPeriodo)
        ]),
        idKey: 'CENTRO_ID',
        nameKey: 'DESC_CENTRO',
        metricsKeys: ['ingresos', 'gastos', 'beneficio', 'roe', 'margen_pct', 'bonus_total']
      },
      { 
        key: 'gestores', 
        label: 'Gestores', 
        icon: UserOutlined, 
        color: theme.colors.bmGreenLight,
        endpoint: (centroId) => api.basic.gestoresByCentro(centroId),
        metricsEndpoint: (gestorId) => Promise.all([
          analyticsService.getGestorKPIsFinancieros(gestorId, normalizedPeriodo),
          analyticsService.getGestorROE(gestorId, normalizedPeriodo),
          analyticsService.getIncentivesGestorDetalle(gestorId, normalizedPeriodo)
        ]),
        idKey: 'GESTOR_ID',
        nameKey: 'DESC_GESTOR',
        metricsKeys: ['ingresos', 'gastos', 'beneficio', 'roe', 'margen_pct', 'bonus_total']
      },
      { 
        key: 'clientes', 
        label: 'Clientes', 
        icon: TeamOutlined, 
        color: theme.colors.info,
        endpoint: (gestorId) => api.basic.clientesByGestor(gestorId),
        metricsEndpoint: (clienteId) => analyticsService.getClienteMetricas(clienteId, normalizedPeriodo),
        idKey: 'CLIENTE_ID',
        nameKey: 'NOMBRE_CLIENTE',
        metricsKeys: ['beneficio', 'ingresos', 'num_contratos']
      },
      { 
        key: 'contratos', 
        label: 'Contratos', 
        icon: FileTextOutlined, 
        color: theme.colors.success,
        endpoint: (clienteId) => api.basic.contractsByCliente(clienteId),
        metricsEndpoint: (contratoId) => analyticsService.getContratoDetalleCompleto(contratoId),
        idKey: 'CONTRATO_ID',
        nameKey: 'CONTRATO_ID',
        metricsKeys: ['importe', 'ingresos', 'margen', 'fecha_alta'],
        isLeaf: true
      }
    ],
    gestor: [
      { 
        key: 'clientes', 
        label: 'Mis Clientes', 
        icon: TeamOutlined, 
        color: theme.colors.info,
        endpoint: (gestorIdParam) => api.basic.clientesByGestor(gestorIdParam || gestorId),
        metricsEndpoint: (clienteId) => analyticsService.getClienteMetricas(clienteId, normalizedPeriodo),
        idKey: 'CLIENTE_ID',
        nameKey: 'NOMBRE_CLIENTE',
        metricsKeys: ['beneficio', 'ingresos', 'num_contratos']
      },
      { 
        key: 'contratos', 
        label: 'Contratos', 
        icon: FileTextOutlined, 
        color: theme.colors.success,
        endpoint: (clienteId) => api.basic.contractsByCliente(clienteId),
        metricsEndpoint: (contratoId) => analyticsService.getContratoDetalleCompleto(contratoId),
        idKey: 'CONTRATO_ID',
        nameKey: 'CONTRATO_ID',
        metricsKeys: ['importe', 'ingresos', 'margen', 'fecha_alta'],
        isLeaf: true
      }
    ]
  }), [gestorId, normalizedPeriodo]);

  // ✅ FUNCIÓN MEJORADA PARA CARGAR MÉTRICAS REALES
  const loadMetrics = useCallback(async (id, levelConfig) => {
    const cacheKey = `${levelConfig.key}_${id}_${normalizedPeriodo}`;
    
    if (metricsCache[cacheKey]) {
      console.log(`[DrillDownView] Using cached metrics for ${levelConfig.key}:${id}`);
      return metricsCache[cacheKey];
    }

    try {
      console.log(`[DrillDownView] 📊 Loading metrics for ${levelConfig.key}:${id}...`);
      let metrics = {};
      
      if (levelConfig.metricsEndpoint) {
        const metricsData = await levelConfig.metricsEndpoint(id);
        console.log(`[DrillDownView] Raw metrics data for ${id}:`, metricsData);
        
        // ✅ PROCESAMIENTO ESPECÍFICO POR TIPO DE ENDPOINT
        if (Array.isArray(metricsData)) {
          // Para centros y gestores que devuelven arrays de promesas
          const [kpisData, roeData, bonusData] = metricsData;
          
          metrics = {
            ingresos: kpisData?.total_ingresos || kpisData?.ingresos_totales || 0,
            gastos: kpisData?.total_gastos || kpisData?.gastos_totales || 0,
            beneficio: kpisData?.beneficio_neto || kpisData?.margen_total || (kpisData?.total_ingresos || 0) - (kpisData?.total_gastos || 0),
            roe: roeData?.roe_pct || kpisData?.roe_pct || 0,
            margen_pct: kpisData?.margen_neto_pct || kpisData?.margen_pct || 0,
            bonus_total: bonusData?.total_incentivos || bonusData?.bonus_total || bonusData?.incentivo_final_eur || 0,
            clasificacion_roe: roeData?.clasificacion || kpisData?.clasificacion_roe || 'N/A',
            clasificacion_margen: kpisData?.clasificacion_margen || 'N/A'
          };
        } else if (metricsData && typeof metricsData === 'object') {
          // ✅ PROCESAMIENTO MEJORADO para clientes y contratos
          if (levelConfig.key === 'contratos') {
            // Para contratos usando el endpoint detalle-completo
            metrics = {
              ingresos: Math.abs(metricsData.ingresos_total || metricsData.importe || 0),
              gastos: Math.abs(metricsData.gastos_total || 0),
              beneficio: metricsData.beneficio_neto || 0,
              margen: metricsData.margen_neto_pct || 0,
              margen_pct: metricsData.margen_neto_pct || 0,
              num_movimientos: metricsData.num_movimientos || 0,
              fecha_alta: metricsData.FECHA_ALTA || metricsData.fecha_alta,
              producto: metricsData.DESC_PRODUCTO || metricsData.producto,
              promedio_movimiento: metricsData.promedio_por_movimiento || 0
            };
          } else {
            // Para clientes usando el endpoint cliente/metricas
            metrics = {
              ingresos: Math.abs(metricsData.ingresos_totales || metricsData.total_ingresos || 0),
              beneficio: metricsData.beneficio_neto || metricsData.beneficio || 0,
              margen: metricsData.margen_neto || 0,
              margen_pct: metricsData.margen_pct || 0,
              num_contratos: metricsData.num_contratos || metricsData.total_contratos || 0,
              total_movimientos: metricsData.total_movimientos || 0
            };
          }
        }
      }
      
      console.log(`[DrillDownView] ✅ Processed metrics for ${levelConfig.key}:${id}:`, metrics);
      setMetricsCache(prev => ({ ...prev, [cacheKey]: metrics }));
      return metrics;
      
    } catch (error) {
      console.warn(`[DrillDownView] ⚠️ Error loading metrics for ${levelConfig.key}:${id}:`, error.message);
      return {};
    }
  }, [metricsCache, normalizedPeriodo]);

  // ✅ NUEVA FUNCIÓN: Cargar métricas bajo demanda para centros
  const loadCentroMetricsOnDemand = useCallback(async (centroId) => {
    const levelConfig = drillConfig.direccion[0]; // Configuración de centros
    if (!levelConfig?.metricsEndpoint) return {};

    console.log(`[DrillDownView] 📊 Loading on-demand metrics for centro: ${centroId}`);
    
    try {
      const metrics = await loadMetrics(centroId, levelConfig);
      
      // Actualizar el rootData con las métricas cargadas
      setRootData(prevData => 
        prevData.map(item => {
          if (item.id === centroId) {
            const ingresos = Math.round(Math.abs(metrics.ingresos || 0));
            const gastos = Math.round(Math.abs(metrics.gastos || 0));
            const beneficio = Math.round(metrics.beneficio || (ingresos - gastos));
            const margen_pct = Math.round((metrics.margen_pct || 0) * 100) / 100;
            const roe = Math.round((metrics.roe || 0) * 100) / 100;
            const alerta = Math.abs(margen_pct) >= 15 ? 'success' : 
                          Math.abs(margen_pct) >= 10 ? 'warning' : 
                          beneficio < 0 ? 'error' : 'warning';

            return {
              ...item,
              ingresos,
              gastos,
              beneficio,
              margen_pct,
              roe,
              bonus_total: Math.round(metrics.bonus_total || 0),
              alerta,
              clasificacion_roe: metrics.clasificacion_roe || 'N/A',
              clasificacion_margen: metrics.clasificacion_margen || 'N/A',
              _needsMetricsLoad: false,
              _metrics: metrics
            };
          }
          return item;
        })
      );
      
      return metrics;
    } catch (error) {
      console.warn(`[DrillDownView] ⚠️ Error loading centro metrics for ${centroId}:`, error.message);
      return {};
    }
  }, [drillConfig, loadMetrics]);

  // ✅ NORMALIZACIÓN MEJORADA con métricas reales - CORREGIDO PARA CENTROS
  const normalizeData = useCallback(async (rawData, levelConfig, forceLoadMetrics = false) => {
    if (!Array.isArray(rawData)) return [];
    
    console.log(`[DrillDownView] 🔄 Normalizing ${rawData.length} items for level: ${levelConfig.key}`);
    
    const normalizedData = await Promise.all(
      rawData.map(async (item, index) => {
        const id = item[levelConfig.idKey] || item.id || index;
        let nombre = item[levelConfig.nameKey] || item.nombre || `Item ${index + 1}`;
        
        // Para contratos, mostrar ID + Producto
        if (levelConfig.key === 'contratos') {
          nombre = `${item.CONTRATO_ID} - ${item.DESC_PRODUCTO || 'Producto'}`;
        }

        // ✅ CARGAR MÉTRICAS REALES - FORZAR CARGA O CARGAR BAJO DEMANDA
        let metrics = {};
        if (levelConfig.metricsEndpoint && (forceLoadMetrics || levelConfig.key !== 'centros')) {
          console.log(`[DrillDownView] 📊 Loading metrics for ${levelConfig.key}:${id} (forced: ${forceLoadMetrics})`);
          metrics = await loadMetrics(id, levelConfig);
        } else if (levelConfig.key === 'centros') {
          console.log(`[DrillDownView] ⚠️ Deferred metrics loading for centro ${id}`);
          // Para centros, usar datos básicos disponibles y marcar para carga posterior
          metrics = {
            ingresos: 0,
            gastos: 0,
            beneficio: 0,
            roe: 0,
            margen_pct: 0,
            bonus_total: 0,
            _needsMetricsLoad: true
          };
        }
        
        // ✅ CÁLCULOS MEJORADOS basados en datos reales o básicos
        const ingresos = metrics.ingresos || item.ingresos_total || item.total_ingresos || 0;
        const gastos = metrics.gastos || item.gastos_total || item.total_gastos || 0;
        const beneficio = metrics.beneficio || (ingresos - gastos);
        
        // Margen porcentual más robusto
        let margen_pct = metrics.margen_pct || metrics.margen || 0;
        if (margen_pct === 0 && ingresos > 0) {
          margen_pct = (beneficio / ingresos) * 100;
        }
        
        // ROE y score
        const roe = metrics.roe || 0;
        const score = Math.min(Math.round((roe * 0.4) + (Math.abs(margen_pct) * 0.6)), 100);
        
        // ✅ ESTADO DE ALERTA MEJORADO - Para centros sin métricas, estado neutral
        const alerta = metrics._needsMetricsLoad ? 'warning' :
                      Math.abs(margen_pct) >= 15 ? 'success' : 
                      Math.abs(margen_pct) >= 10 ? 'warning' : 
                      beneficio < 0 ? 'error' : 'warning';
        
        return {
          key: id,
          id: id,
          nombre: nombre,
          ingresos: Math.round(Math.abs(ingresos)),
          gastos: Math.round(Math.abs(gastos)),
          beneficio: Math.round(beneficio),
          margen_pct: Math.round(margen_pct * 100) / 100,
          roe: Math.round(roe * 100) / 100,
          bonus_total: Math.round(metrics.bonus_total || 0),
          num_contratos: metrics.num_contratos || item.num_contratos || 0,
          score: Math.max(0, score),
          alerta: alerta,
          clasificacion_roe: metrics.clasificacion_roe || 'N/A',
          clasificacion_margen: metrics.clasificacion_margen || 'N/A',
          _needsMetricsLoad: metrics._needsMetricsLoad || false,
          
          // Datos específicos por tipo
          segmento: item.DESC_SEGMENTO || item.segmento || null,
          fechaAlta: metrics.fecha_alta || item.FECHA_ALTA || null,
          producto: metrics.producto || item.DESC_PRODUCTO || null,
          centro: item.DESC_CENTRO || null,
          num_movimientos: metrics.num_movimientos || 0,
          
          // Metadatos
          _originalData: item,
          _level: levelConfig.key,
          _metrics: metrics
        };
      })
    );
    
    // Ordenar por ingresos descendente
    const sorted = normalizedData.sort((a, b) => (b.ingresos || 0) - (a.ingresos || 0));
    console.log(`[DrillDownView] ✅ Normalized ${sorted.length} items for ${levelConfig.key}`);
    return sorted;
  }, [loadMetrics]);

  // ✅ CARGA DE DATOS RAÍZ - FORZAR CARGA DE MÉTRICAS PARA CENTROS
  const loadRootData = useCallback(async () => {
    const levelConfig = drillConfig[mode] && drillConfig[mode][0];
    if (!levelConfig) return;

    try {
      setLoading(true);
      setError(null);
      console.log(`[DrillDownView] 🚀 Loading root data for mode: ${mode}...`);
      
      let rawData;
      if (mode === 'gestor' && gestorId) {
        rawData = await levelConfig.endpoint(gestorId);
        console.log(`[DrillDownView] ✅ Root data loaded for gestor ${gestorId}:`, rawData);
      } else {
        rawData = await levelConfig.endpoint();
        console.log('[DrillDownView] ✅ Root data loaded:', rawData);
      }
      
      // ✅ FORZAR CARGA DE MÉTRICAS PARA CENTROS EN MODO DIRECCIÓN
      const shouldForceLoad = mode === 'direccion' && levelConfig.key === 'centros';
      const normalizedData = await normalizeData(rawData, levelConfig, shouldForceLoad);
      setRootData(normalizedData);
      
    } catch (err) {
      console.error('[DrillDownView] ❌ Error loading root data:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [mode, drillConfig, normalizeData, gestorId]);

  const getLevelConfig = useCallback((levelIndex) => {
    const configs = drillConfig[mode];
    if (!configs || !Array.isArray(configs) || levelIndex >= configs.length) {
      return null;
    }
    return configs[levelIndex];
  }, [drillConfig, mode]);

  // ✅ MANEJO DE EXPANSIÓN - ACTUALIZADO para cargar métricas de centros si es necesario
  const handleRowExpand = useCallback(async (expanded, record) => {
    const recordId = record.id;
    console.log(`[DrillDownView] 🔽 Row expand ${expanded ? 'OPEN' : 'CLOSE'}:`, recordId);

    if (expanded) {
      setExpandedRowKeys(prev => {
        if (!prev.includes(recordId)) {
          return [...prev, recordId];
        }
        return prev;
      });

      // ✅ CARGAR MÉTRICAS DE CENTROS BAJO DEMANDA SI ES NECESARIO
      if (record._needsMetricsLoad && record._level === 'centros') {
        console.log(`[DrillDownView] 🔄 Loading centro metrics on expand for: ${recordId}`);
        await loadCentroMetricsOnDemand(recordId);
      }

      if (!childDataMap[recordId]) {
        const currentLevel = record._level || (mode === 'gestor' ? 'clientes' : 'centros');
        const currentLevelIndex = drillConfig[mode] ? drillConfig[mode].findIndex(level => level.key === currentLevel) : -1;
        const nextLevelIndex = currentLevelIndex + 1;
        const nextLevelConfig = getLevelConfig(nextLevelIndex);
        
        if (!nextLevelConfig) {
          console.log('[DrillDownView] 🍃 No next level config, this is a leaf');
          return;
        }

        console.log(`[DrillDownView] 📡 Fetching ${nextLevelConfig.key} for ${recordId}...`);
        
        try {
          setLoadingChildren(prev => ({ ...prev, [recordId]: true }));
          
          const rawChildData = await nextLevelConfig.endpoint(recordId);
          console.log(`[DrillDownView] ✅ Child data loaded for ${recordId}:`, rawChildData);
          
          // ✅ PARA GESTORES (hijos de centros), FORZAR CARGA DE MÉTRICAS
          const forceLoadMetrics = nextLevelConfig.key === 'gestores';
          const normalizedChildData = await normalizeData(rawChildData, nextLevelConfig, forceLoadMetrics);
          
          setChildDataMap(prev => ({
            ...prev,
            [recordId]: {
              data: normalizedChildData,
              level: nextLevelIndex,
              config: nextLevelConfig
            }
          }));
          
        } catch (err) {
          console.error(`[DrillDownView] ❌ Error loading child data for ${recordId}:`, err);
          
          setChildDataMap(prev => ({
            ...prev,
            [recordId]: {
              data: [],
              level: nextLevelIndex,
              config: nextLevelConfig,
              error: err.message
            }
          }));
        } finally {
          setLoadingChildren(prev => {
            const updated = { ...prev };
            delete updated[recordId];
            return updated;
          });
        }
      }
    } else {
      setExpandedRowKeys(prev => prev.filter(key => key !== recordId));
    }
  }, [mode, drillConfig, normalizeData, childDataMap, getLevelConfig, loadCentroMetricsOnDemand]);

  // ✅ COLUMNAS DINÁMICAS ACTUALIZADAS con indicadores de carga
  const getColumns = useCallback((levelConfig) => {
    const columns = [
      {
        title: levelConfig.key === 'contratos' ? 'Contrato - Producto' : 
               levelConfig.key === 'centros' ? 'Centro' :
               levelConfig.key === 'gestores' ? 'Gestor' : 'Cliente',
        dataIndex: 'nombre',
        key: 'nombre',
        fixed: 'left',
        width: levelConfig.key === 'contratos' ? 320 : 280,
        render: (text, record) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <levelConfig.icon style={{ color: levelConfig.color, fontSize: 16 }} />
            <div>
              <div style={{ fontWeight: 500, color: theme.colors.textPrimary }}>
                {text}
              </div>
              {record.segmento && (
                <Text type="secondary" style={{ fontSize: 11 }}>
                  Segmento: {record.segmento}
                </Text>
              )}
              {record.fechaAlta && (
                <Text type="secondary" style={{ fontSize: 10, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <CalendarOutlined /> {new Date(record.fechaAlta).toLocaleDateString('es-ES')}
                </Text>
              )}
              {record.num_movimientos > 0 && (
                <Text type="secondary" style={{ fontSize: 10 }}>
                  {record.num_movimientos} movimientos
                </Text>
              )}
              {record.clasificacion_roe && record.clasificacion_roe !== 'N/A' && (
                <Tag size="small" color={record.alerta === 'success' ? 'green' : record.alerta === 'warning' ? 'orange' : 'red'}>
                  {record.clasificacion_roe}
                </Tag>
              )}
            </div>
          </div>
        ),
        filteredValue: searchText ? [searchText] : null,
        onFilter: (value, record) =>
          record.nombre.toLowerCase().includes(value.toLowerCase()),
      }
    ];

    // ✅ INGRESOS (siempre mostrar) - ACTUALIZADO con indicador de carga
    columns.push({
      title: 'Ingresos',
      dataIndex: 'ingresos',
      key: 'ingresos',
      width: 120,
      render: (value, record) => (
        <div>
          <Statistic
            value={value || 0}
            prefix={record._needsMetricsLoad ? 
              <Tooltip title="Expandir fila para cargar métricas">
                <BarChartOutlined style={{ color: theme.colors.warning }} />
              </Tooltip> : 
              <EuroCircleOutlined />
            }
            formatter={val => record._needsMetricsLoad ? 'Pendiente...' : new Intl.NumberFormat('es-ES', { 
              style: 'currency', 
              currency: 'EUR',
              notation: 'compact'
            }).format(val)}
            valueStyle={{ 
              fontSize: 13, 
              color: record._needsMetricsLoad ? theme.colors.warning : theme.colors.textPrimary 
            }}
          />
          {record._needsMetricsLoad && (
            <div style={{ fontSize: 10, color: theme.colors.warning }}>
              Expandir para cargar
            </div>
          )}
        </div>
      ),
      sorter: (a, b) => (a.ingresos || 0) - (b.ingresos || 0),
    });

    // ✅ BENEFICIO/MARGEN para centros y gestores
    if (levelConfig.key === 'centros' || levelConfig.key === 'gestores') {
      columns.push({
        title: 'Beneficio',
        dataIndex: 'beneficio',
        key: 'beneficio',
        width: 120,
        render: (value, record) => (
          <div>
            <Statistic
              value={value || 0}
              formatter={val => record._needsMetricsLoad ? 'Pendiente...' : new Intl.NumberFormat('es-ES', { 
                style: 'currency', 
                currency: 'EUR',
                notation: 'compact'
              }).format(val)}
              valueStyle={{ 
                fontSize: 13, 
                color: record._needsMetricsLoad ? theme.colors.warning : 
                       value >= 0 ? theme.colors.success : theme.colors.error 
              }}
            />
            <div style={{ fontSize: 10, color: '#666' }}>
              Margen: {record._needsMetricsLoad ? '-' : `${Math.abs(record.margen_pct || 0).toFixed(1)}%`}
            </div>
          </div>
        ),
        sorter: (a, b) => (a.beneficio || 0) - (b.beneficio || 0),
      });

      // ✅ ROE para centros y gestores
      columns.push({
        title: 'ROE',
        dataIndex: 'roe',
        key: 'roe',
        width: 100,
        render: (value, record) => (
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              fontWeight: 600, 
              fontSize: 14,
              color: record._needsMetricsLoad ? theme.colors.warning :
                     value >= 15 ? theme.colors.success : 
                     value >= 10 ? theme.colors.warning : theme.colors.error 
            }}>
              {record._needsMetricsLoad ? '-' : `${value?.toFixed(1) || 0}%`}
            </div>
            {!record._needsMetricsLoad && (
              <Progress 
                percent={Math.min(value || 0, 25) * 4} 
                showInfo={false}
                strokeColor={value >= 15 ? theme.colors.success : 
                            value >= 10 ? theme.colors.warning : theme.colors.error}
                size="small"
              />
            )}
          </div>
        ),
        sorter: (a, b) => (a.roe || 0) - (b.roe || 0),
      });

      // ✅ BONUS para centros y gestores
      columns.push({
        title: 'Bonus',
        dataIndex: 'bonus_total',
        key: 'bonus_total',
        width: 100,
        render: (value, record) => (
          <Statistic
            value={value || 0}
            prefix={<TrophyOutlined />}
            formatter={val => record._needsMetricsLoad ? '-' : new Intl.NumberFormat('es-ES', { 
              style: 'currency', 
              currency: 'EUR',
              notation: 'compact'
            }).format(val)}
            valueStyle={{ 
              fontSize: 12, 
              color: record._needsMetricsLoad ? theme.colors.warning :
                     value > 0 ? theme.colors.bmGreenPrimary : theme.colors.textSecondary 
            }}
          />
        ),
        sorter: (a, b) => (a.bonus_total || 0) - (b.bonus_total || 0),
      });
    }

    // ✅ BENEFICIO para clientes
    if (levelConfig.key === 'clientes') {
      columns.push({
        title: 'Beneficio',
        dataIndex: 'beneficio',
        key: 'beneficio',
        width: 120,
        render: (value, record) => (
          <div>
            <Statistic
              value={value || 0}
              formatter={val => new Intl.NumberFormat('es-ES', { 
                style: 'currency', 
                currency: 'EUR',
                notation: 'compact'
              }).format(val)}
              valueStyle={{ 
                fontSize: 13, 
                color: value >= 0 ? theme.colors.success : theme.colors.error 
              }}
            />
            <div style={{ fontSize: 10, color: '#666' }}>
              {record.num_contratos} contrato{record.num_contratos !== 1 ? 's' : ''}
            </div>
          </div>
        ),
        sorter: (a, b) => (a.beneficio || 0) - (b.beneficio || 0),
      });
    }

    // ✅ IMPORTE para contratos
    if (levelConfig.key === 'contratos') {
      columns.push({
        title: 'Importe',
        dataIndex: 'ingresos',
        key: 'importe_contrato',
        width: 120,
        render: (value, record) => (
          <div>
            <Statistic
              value={value || 0}
              formatter={val => new Intl.NumberFormat('es-ES', { 
                style: 'currency', 
                currency: 'EUR'
              }).format(val)}
              valueStyle={{ fontSize: 13, color: theme.colors.textPrimary }}
            />
            {record.margen_pct !== 0 && (
              <div style={{ 
                fontSize: 10, 
                color: record.margen_pct > 0 ? theme.colors.success : theme.colors.error 
              }}>
                {record.margen_pct > 0 ? '+' : ''}{Math.abs(record.margen_pct).toFixed(1)}% margen
              </div>
            )}
          </div>
        ),
        sorter: (a, b) => (a.ingresos || 0) - (b.ingresos || 0),
      });
    }

    // ✅ ESTADO/ALERTA (común para todos)
    columns.push({
      title: 'Estado',
      dataIndex: 'alerta',
      key: 'estado',
      width: 100,
      render: (value, record) => (
        <div style={{ textAlign: 'center' }}>
          <div 
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 36,
              height: 36,
              borderRadius: '50%',
              backgroundColor: value === 'success' ? theme.colors.success :
                             value === 'warning' ? theme.colors.warning : theme.colors.error,
              color: 'white',
              fontSize: 12,
              fontWeight: 600,
              marginBottom: 4
            }}
          >
            {record._needsMetricsLoad ? '⏳' : 
             value === 'success' ? '✓' : value === 'warning' ? '!' : '✗'}
          </div>
          <div style={{ fontSize: 10, color: '#666' }}>
            {record._needsMetricsLoad ? 'Pendiente' :
             value === 'success' ? 'Óptimo' : value === 'warning' ? 'Atención' : 'Crítico'}
          </div>
        </div>
      ),
      filters: [
        { text: 'Óptimo', value: 'success' },
        { text: 'Atención', value: 'warning' },
        { text: 'Crítico', value: 'error' }
      ],
      onFilter: (value, record) => record.alerta === value,
    });

    return columns;
  }, [searchText]);

  // ✅ RENDERIZADO DE FILAS EXPANDIDAS MEJORADO
  const expandedRowRender = useCallback((record) => {
    const recordId = record.id;
    const childInfo = childDataMap[recordId];
    const isLoading = loadingChildren[recordId];

    if (isLoading) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <Loader tip={`Cargando ${record._level === 'centros' ? 'gestores' : 
                                   record._level === 'gestores' ? 'clientes' : 'contratos'}...`} />
        </div>
      );
    }

    if (childInfo?.error) {
      return (
        <div style={{ padding: '20px' }}>
          <ErrorState
            error={childInfo.error}
            message={`Error al cargar datos de ${record.nombre}`}
            size="small"
          />
        </div>
      );
    }

    if (!childInfo || !childInfo.data) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <Empty 
            description={`No hay datos disponibles para ${record.nombre}`} 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </div>
      );
    }

    const { data, config } = childInfo;
    const columns = getColumns(config);

    // ✅ MÉTRICAS AGREGADAS mejoradas
    const totalIngresos = data.reduce((acc, item) => acc + (item.ingresos || 0), 0);
    const totalBeneficio = data.reduce((acc, item) => acc + (item.beneficio || 0), 0);
    const avgMargen = data.length > 0 ? data.reduce((acc, item) => acc + Math.abs(item.margen_pct || 0), 0) / data.length : 0;
    const totalBonus = data.reduce((acc, item) => acc + (item.bonus_total || 0), 0);

    return (
      <div style={{ 
        margin: '16px 0', 
        backgroundColor: '#fafafa', 
        borderRadius: 6, 
        padding: '16px',
        border: `1px solid ${theme.colors.borderLight}`,
        maxHeight: '600px',
        overflow: 'auto'
      }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div>
              <Text strong style={{ color: theme.colors.bmGreenPrimary, fontSize: 16 }}>
                <config.icon style={{ marginRight: 8 }} />
                {config.label} de {record.nombre}
              </Text>
              <Text type="secondary" style={{ marginLeft: 12, fontSize: 12 }}>
                {data.length} registros encontrados
              </Text>
            </div>
          </div>
          
          {/* ✅ PANEL DE MÉTRICAS AGREGADAS */}
          <Row gutter={16} style={{ marginBottom: 12 }}>
            <Col span={6}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <Statistic 
                  title="Total Ingresos" 
                  value={totalIngresos}
                  formatter={val => new Intl.NumberFormat('es-ES', {
                    style: 'currency',
                    currency: 'EUR',
                    notation: 'compact'
                  }).format(val)}
                  valueStyle={{ fontSize: 14, color: theme.colors.bmGreenPrimary }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <Statistic 
                  title="Total Beneficio" 
                  value={totalBeneficio}
                  formatter={val => new Intl.NumberFormat('es-ES', {
                    style: 'currency',
                    currency: 'EUR',
                    notation: 'compact'
                  }).format(val)}
                  valueStyle={{ 
                    fontSize: 14, 
                    color: totalBeneficio >= 0 ? theme.colors.success : theme.colors.error 
                  }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <Statistic 
                  title="Margen Promedio" 
                  value={avgMargen}
                  formatter={val => `${val.toFixed(1)}%`}
                  valueStyle={{ 
                    fontSize: 14,
                    color: avgMargen >= 15 ? theme.colors.success : 
                           avgMargen >= 10 ? theme.colors.warning : theme.colors.error
                  }}
                />
              </Card>
            </Col>
            {totalBonus > 0 && (
              <Col span={6}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <Statistic 
                    title="Total Bonus" 
                    value={totalBonus}
                    prefix={<TrophyOutlined />}
                    formatter={val => new Intl.NumberFormat('es-ES', {
                      style: 'currency',
                      currency: 'EUR',
                      notation: 'compact'
                    }).format(val)}
                    valueStyle={{ fontSize: 14, color: theme.colors.bmGreenPrimary }}
                  />
                </Card>
              </Col>
            )}
          </Row>
        </div>

        <Table
          columns={columns}
          dataSource={data}
          size="small"
          pagination={{
            size: 'small',
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            pageSizeOptions: ['5', '10', '20']
          }}
          scroll={{ x: true }}
          expandable={config.isLeaf ? undefined : {
            onExpand: handleRowExpand,
            expandedRowKeys: expandedRowKeys,
            expandedRowRender: expandedRowRender
          }}
          locale={{
            emptyText: <Empty description={`No hay ${config.label.toLowerCase()} disponibles`} />
          }}
        />
      </div>
    );
  }, [childDataMap, loadingChildren, getColumns, expandedRowKeys, handleRowExpand]);

  // Effects
  useEffect(() => {
    loadRootData();
  }, [loadRootData]);

  useEffect(() => {
    if (refreshToken) {
      loadRootData();
    }
  }, [refreshToken, loadRootData]);

  // Handlers
  const handleRefresh = useCallback(() => {
    setChildDataMap({});
    setExpandedRowKeys([]);
    setMetricsCache({});
    loadRootData();
  }, [loadRootData]);

  const handleSearch = useCallback((value) => {
    setSearchText(value);
  }, []);

  if (loading) {
    return <Loader tip="Cargando análisis navegable..." />;
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

  const currentLevelConfig = drillConfig[mode] && drillConfig[mode][0];
  if (!currentLevelConfig) {
    return (
      <Card style={style} className={className}>
        <Empty 
          description="Configuración no disponible para este modo" 
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </Card>
    );
  }

  const columns = getColumns(currentLevelConfig);

  return (
    <Card
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space>
            <BarChartOutlined style={{ color: theme.colors.bmGreenPrimary }} />
            <Title level={5} style={{ margin: 0 }}>
              Análisis Navegable - Vista {mode === 'gestor' ? 'Personal' : 'Corporativa'}
            </Title>
            <Text type="secondary">
              Navega por la jerarquía expandiendo filas • Período: {normalizedPeriodo}
            </Text>
          </Space>
          <Space>
            <Search
              placeholder={`Buscar ${currentLevelConfig.label.toLowerCase()}...`}
              allowClear
              onSearch={handleSearch}
              style={{ width: 200 }}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={handleRefresh}
              disabled={loading}
            >
              Actualizar
            </Button>
          </Space>
        </div>
      }
      style={style}
      className={className}
      styles={{ body: { padding: '16px' } }}
    >
      <Table
        columns={columns}
        dataSource={rootData}
        size="middle"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['5', '10', '20', '50'],
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} de ${total} ${currentLevelConfig.label.toLowerCase()}`
        }}
        scroll={{ x: 1200 }}
        expandable={{
          onExpand: handleRowExpand,
          expandedRowKeys: expandedRowKeys,
          expandedRowRender: expandedRowRender,
          expandIcon: ({ expanded, onExpand, record }) => 
            expanded ? (
              <MinusOutlined onClick={e => onExpand(record, e)} style={{ color: theme.colors.bmGreenPrimary }} />
            ) : (
              <ArrowDownOutlined onClick={e => onExpand(record, e)} style={{ color: theme.colors.bmGreenPrimary }} />
            )
        }}
        locale={{
          emptyText: <Empty description={`No hay ${currentLevelConfig.label.toLowerCase()} disponibles`} />
        }}
        rowClassName={(record) => 
          record.alerta === 'error' ? 'row-critical' : 
          record.alerta === 'warning' ? 'row-warning' : 'row-success'
        }
      />
    </Card>
  );
};

DrillDownView.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onSelectLeaf: PropTypes.func,
  refreshToken: PropTypes.any,
  style: PropTypes.object,
  className: PropTypes.string,
};

export default DrillDownView;
