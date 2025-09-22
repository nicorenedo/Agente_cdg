// frontend/src/components/Dashboard/DeviationAnalysis.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  Spin,
  InputNumber,
  Select,
  Divider,
  message,
  AutoComplete
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
  ContainerOutlined,
  SettingOutlined,
  FilterOutlined,
  ThunderboltOutlined,
  LineChartOutlined,
  TeamOutlined,
  BugOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import ErrorState from '../common/ErrorState';
import theme from '../../styles/theme';

const { Title, Text } = Typography;
const { Option } = Select;

/**
 * DeviationAnalysis v8.0 - PROBLEMA RESUELTO: Manejo robusto de todas las estructuras de respuesta
 * 
 * ✅ PROBLEMA IDENTIFICADO EN LOGS:
 * - margenRes tiene 3 keys pero margenRes.data es undefined
 * - La función unwrap está procesando mal la respuesta { status, data, meta }
 * - Necesitamos acceder directamente a las keys del objeto respuesta
 */
const DeviationAnalysis = ({
  mode = 'direccion',
  periodo = '2025-10',
  gestorId = null,
  onReload = () => {},
  className = '',
  style = {}
}) => {
  // Estados principales
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('pricing');
  
  // Estados de datos específicos
  const [pricingData, setPricingData] = useState({ data: [], total: 0, umbral: 15.0 });
  const [margenData, setMargenData] = useState({ data: [], total: 0, z: 2.0 });
  const [volumenData, setVolumenData] = useState({ data: [], total: 0, factor: 3.0 });
  const [summaryData, setSummaryData] = useState(null);
  
  // Estados de configuración de parámetros
  const [pricingUmbral, setPricingUmbral] = useState(15.0);
  const [margenZScore, setMargenZScore] = useState(2.0);
  const [volumenFactor, setVolumenFactor] = useState(3.0);
  
  // Estado para debugging
  const [useDebugMode, setUseDebugMode] = useState(true);
  const [parametersChanged, setParametersChanged] = useState(false);
  
  /**
   * ✅ FUNCIÓN ULTRA-ROBUSTA: Extrae datos de cualquier estructura de respuesta
   */
  const extractDeviationsFromResponse = (response, type = 'unknown') => {
    console.log(`[DeviationAnalysis] 🔍 Extracting ${type} data from response:`, response);
    console.log(`[DeviationAnalysis] 🔍 Response type:`, typeof response);
    console.log(`[DeviationAnalysis] 🔍 Response keys:`, Object.keys(response || {}));
    
    // Caso 1: Respuesta directa con deviations (estructura actual de pricing)
    if (response && response.deviations && Array.isArray(response.deviations)) {
      console.log(`[DeviationAnalysis] ✅ ${type} - Estructura directa encontrada:`, response.deviations.length, 'elementos');
      return response.deviations;
    }
    
    // Caso 2: Respuesta con data.deviations (estructura esperada)
    if (response && response.data && response.data.deviations && Array.isArray(response.data.deviations)) {
      console.log(`[DeviationAnalysis] ✅ ${type} - Estructura data.deviations encontrada:`, response.data.deviations.length, 'elementos');
      return response.data.deviations;
    }
    
    // Caso 3: La respuesta ES el objeto data completo (lo que parece estar pasando)
    if (response && response.status === 'success' && response.data && response.data.deviations) {
      console.log(`[DeviationAnalysis] ✅ ${type} - Estructura {status, data, meta} encontrada:`, response.data.deviations.length, 'elementos');
      return response.data.deviations;
    }
    
    // Caso 4: La respuesta MISMA es el array de deviations
    if (response && Array.isArray(response)) {
      console.log(`[DeviationAnalysis] ✅ ${type} - Array directo encontrado:`, response.length, 'elementos');
      return response;
    }
    
    // Caso 5: Buscar recursivamente en todas las propiedades
    if (response && typeof response === 'object') {
      for (const [key, value] of Object.entries(response)) {
        console.log(`[DeviationAnalysis] 🔍 ${type} - Checking key '${key}':`, typeof value, Array.isArray(value) ? `Array[${value.length}]` : value);
        
        if (key === 'deviations' && Array.isArray(value)) {
          console.log(`[DeviationAnalysis] ✅ ${type} - Deviations encontrado en key '${key}':`, value.length, 'elementos');
          return value;
        }
        
        if (value && typeof value === 'object' && value.deviations && Array.isArray(value.deviations)) {
          console.log(`[DeviationAnalysis] ✅ ${type} - Deviations encontrado en '${key}.deviations':`, value.deviations.length, 'elementos');
          return value.deviations;
        }
      }
    }
    
    console.log(`[DeviationAnalysis] ⚠️ ${type} - No se encontraron deviations en ninguna estructura`);
    return [];
  };

  /**
   * ✅ FUNCIÓN CORREGIDA: Procesamiento ultra-robusto de respuestas
   */
  const fetchAllDeviationData = useCallback(async () => {
    if (!periodo) return;

    console.log(`[DeviationAnalysis] 🔄 Cargando datos para período: ${periodo}`);
    console.log(`[DeviationAnalysis] 📊 Parámetros: pricing=${pricingUmbral}%, margen_z=${margenZScore}, volumen_factor=${volumenFactor}`);
    console.log(`[DeviationAnalysis] 🐛 Debug mode: ${useDebugMode}`);
    
    setLoading(true);
    setError(null);

    try {
      console.log('[DeviationAnalysis] 🚀 Iniciando llamadas a endpoints...');

      // 1. ✅ PRICING - Funciona correctamente, no tocar
      console.log('[DeviationAnalysis] 📞 Llamando pricing endpoint...');
      const pricingRes = await api.deviations.pricing(periodo, pricingUmbral).catch(err => {
        console.error('[DeviationAnalysis] ❌ Pricing endpoint failed:', err);
        return { deviations: [], umbral: pricingUmbral };
      });
      console.log('[DeviationAnalysis] ✅ Pricing response:', pricingRes);

      // 2. ✅ MARGEN - ULTRA-ROBUSTO
      console.log('[DeviationAnalysis] 📞 Llamando margen endpoint...');
      let margenRes;
      try {
        margenRes = await api.deviations.margen(periodo, { z: margenZScore, enhanced: true });
        console.log('[DeviationAnalysis] ✅ Margen response RAW COMPLETA:', margenRes);
        console.log('[DeviationAnalysis] 🔍 Margen response keys detalladas:', Object.keys(margenRes || {}));
        
        // Debugging extremo - mostrar cada key
        if (margenRes && typeof margenRes === 'object') {
          Object.entries(margenRes).forEach(([key, value]) => {
            console.log(`[DeviationAnalysis] 🔍 Key '${key}':`, typeof value, Array.isArray(value) ? `Array[${value.length}]` : value);
          });
        }
        
      } catch (err) {
        console.error('[DeviationAnalysis] ❌ Margen endpoint failed:', err);
        margenRes = { deviations: [], z: margenZScore };
      }

      // 3. ✅ VOLUMEN - ULTRA-ROBUSTO
      console.log('[DeviationAnalysis] 📞 Llamando volumen endpoint...');
      let volumenRes;
      try {
        volumenRes = await api.deviations.volumen(periodo, { factor: volumenFactor, enhanced: true });
        console.log('[DeviationAnalysis] ✅ Volumen response RAW COMPLETA:', volumenRes);
        console.log('[DeviationAnalysis] 🔍 Volumen response keys detalladas:', Object.keys(volumenRes || {}));
        
        // Debugging extremo - mostrar cada key
        if (volumenRes && typeof volumenRes === 'object') {
          Object.entries(volumenRes).forEach(([key, value]) => {
            console.log(`[DeviationAnalysis] 🔍 Key '${key}':`, typeof value, Array.isArray(value) ? `Array[${value.length}]` : value);
          });
        }
        
      } catch (err) {
        console.error('[DeviationAnalysis] ❌ Volumen endpoint failed:', err);
        volumenRes = { deviations: [], factor: volumenFactor };
      }

      // 4. ✅ SUMMARY
      const summaryRes = await api.deviations.summary(periodo).catch(err => {
        console.warn('[DeviationAnalysis] Summary endpoint error:', err.message);
        return { precio: { total: 0 }, margen: { total: 0 }, volumen: { total: 0 } };
      });

      // ✅ PROCESAMIENTO ULTRA-ROBUSTO CON EXTRACTOR INTELIGENTE
      console.log('[DeviationAnalysis] 🔧 Procesando respuestas con extractor inteligente...');

      // Pricing - mantener como funciona
      const pricingDataArray = extractDeviationsFromResponse(pricingRes, 'Pricing');
      console.log('[DeviationAnalysis] ✅ Pricing procesado:', pricingDataArray.length, 'elementos');

      // Margen - extracción inteligente
      const margenDataArray = extractDeviationsFromResponse(margenRes, 'Margen');
      console.log('[DeviationAnalysis] ✅ Margen procesado:', margenDataArray.length, 'elementos');

      // Volumen - extracción inteligente
      const volumenDataArray = extractDeviationsFromResponse(volumenRes, 'Volumen');
      console.log('[DeviationAnalysis] ✅ Volumen procesado:', volumenDataArray.length, 'elementos');

      // ✅ ESTABLECER ESTADOS FINALES
      setPricingData({
        data: pricingDataArray,
        total: pricingDataArray.length,
        umbral: (pricingRes && pricingRes.umbral) || pricingUmbral,
        periodo: periodo
      });

      setMargenData({
        data: margenDataArray,
        total: margenDataArray.length,
        z: (margenRes && (margenRes.z || (margenRes.data && margenRes.data.z))) || margenZScore,
        periodo: periodo
      });

      setVolumenData({
        data: volumenDataArray,
        total: volumenDataArray.length,
        factor: (volumenRes && (volumenRes.factor || (volumenRes.data && volumenRes.data.factor))) || volumenFactor,
        periodo: periodo
      });

      setSummaryData({
        precio: { total: pricingDataArray.length },
        margen: { total: margenDataArray.length },
        volumen: { total: volumenDataArray.length }
      });

      // ✅ DEBUGGING FINAL DETALLADO
      console.log('[DeviationAnalysis] ✅ ESTADOS FINALES ESTABLECIDOS:', {
        pricingTotal: pricingDataArray.length,
        margenTotal: margenDataArray.length,
        volumenTotal: volumenDataArray.length,
        pricingUmbral: pricingUmbral,
        margenZ: margenZScore,
        volumenFactor: volumenFactor
      });

      console.log('[DeviationAnalysis] ✅ EXTRACCIÓN COMPLETADA CON ÉXITO');
      setParametersChanged(false);

    } catch (error) {
      console.error('[DeviationAnalysis] ❌ Error global crítico:', error);
      setError(`Error cargando desviaciones: ${error.message}`);
      message.error('Error crítico cargando análisis de desviaciones');
    } finally {
      setLoading(false);
    }
  }, [periodo, pricingUmbral, margenZScore, volumenFactor, useDebugMode]);

  /**
   * ✅ Manejo de cambios de parámetros
   */
  const handleParameterChange = useCallback((paramType, value) => {
    console.log(`[DeviationAnalysis] 🔧 Cambiando ${paramType} a ${value}`);
    
    switch (paramType) {
      case 'pricing':
        setPricingUmbral(value);
        break;
      case 'margen':
        setMargenZScore(value);
        break;
      case 'volumen':
        setVolumenFactor(value);
        break;
    }
    
    setParametersChanged(true);
  }, []);

  /**
   * ✅ Panel de controles
   */
  const renderDynamicParameterControls = () => (
    <Card 
      size="small" 
      style={{ marginBottom: 16, borderColor: parametersChanged ? theme.colors.warning : theme.colors.borderLight }}
      title={
        <Space>
          <SettingOutlined style={{ color: theme.colors.bmGreenPrimary }} />
          <Text strong>Parámetros de Análisis Dinámico</Text>
          {parametersChanged && (
            <Badge 
              status="processing" 
              text={<Text type="secondary" style={{ fontSize: 12 }}>Cambios pendientes</Text>} 
            />
          )}
          {useDebugMode && (
            <Tag color="purple" icon={<BugOutlined />}>
              ULTRA DEBUG
            </Tag>
          )}
        </Space>
      }
      extra={
        <Space>
          <Button 
            size="small" 
            type={parametersChanged ? "primary" : "default"}
            icon={<FilterOutlined />} 
            onClick={fetchAllDeviationData}
            loading={loading}
            style={{
              backgroundColor: parametersChanged ? theme.colors.bmGreenPrimary : undefined,
              borderColor: parametersChanged ? theme.colors.bmGreenPrimary : undefined
            }}
          >
            {parametersChanged ? 'Aplicar Cambios' : 'Actualizar'}
          </Button>
          <Button 
            size="small" 
            icon={<BugOutlined />}
            onClick={() => setUseDebugMode(!useDebugMode)}
            type={useDebugMode ? "primary" : "default"}
          >
            Debug {useDebugMode ? 'ON' : 'OFF'}
          </Button>
        </Space>
      }
    >
      <Row gutter={[16, 8]} align="middle">
        <Col xs={24} sm={8}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <DollarOutlined /> Umbral Pricing (%)
            </Text>
            <InputNumber
              size="small"
              min={5}
              max={50}
              step={0.5}
              value={pricingUmbral}
              onChange={(val) => handleParameterChange('pricing', val)}
              style={{ 
                width: '100%',
                borderColor: pricingUmbral !== (pricingData.umbral || 15.0) ? theme.colors.warning : undefined
              }}
              addonAfter="%"
            />
            <Text type="secondary" style={{ fontSize: 11 }}>
              Actual: <Text strong style={{ color: theme.colors.success }}>{pricingData.total || 0}</Text> desviaciones
            </Text>
          </Space>
        </Col>
        
        <Col xs={24} sm={8}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <LineChartOutlined /> Z-Score Margen
            </Text>
            <InputNumber
              size="small"
              min={1}
              max={5}
              step={0.1}
              value={margenZScore}
              onChange={(val) => handleParameterChange('margen', val)}
              style={{ 
                width: '100%',
                borderColor: margenZScore !== (margenData.z || 2.0) ? theme.colors.warning : undefined
              }}
              addonAfter="σ"
            />
            <Text type="secondary" style={{ fontSize: 11 }}>
              Actual: <Text strong style={{ color: theme.colors.info }}>{margenData.total || 0}</Text> anomalías
            </Text>
          </Space>
        </Col>
        
        <Col xs={24} sm={8}>
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              <TeamOutlined /> Factor Volumen
            </Text>
            <InputNumber
              size="small"
              min={1}
              max={10}
              step={0.1}
              value={volumenFactor}
              onChange={(val) => handleParameterChange('volumen', val)}
              style={{ 
                width: '100%',
                borderColor: volumenFactor !== (volumenData.factor || 3.0) ? theme.colors.warning : undefined
              }}
              addonAfter="x"
            />
            <Text type="secondary" style={{ fontSize: 11 }}>
              Actual: <Text strong style={{ color: theme.colors.bmGreenLight }}>{volumenData.total || 0}</Text> outliers
            </Text>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  /**
   * ✅ Header dinámico
   */
  const renderDynamicSummaryHeader = () => (
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={8}>
        <Card 
          size="small" 
          style={{ 
            textAlign: 'center', 
            borderColor: pricingData.total > 0 ? theme.colors.warning : theme.colors.success,
            cursor: 'pointer',
            backgroundColor: activeTab === 'pricing' ? '#f6ffed' : 'white'
          }}
          onClick={() => setActiveTab('pricing')}
          hoverable
        >
          <Statistic
            title={
              <Space>
                <DollarOutlined />
                <span>Pricing (≥{pricingData.umbral}%)</span>
              </Space>
            }
            value={pricingData.total}
            valueStyle={{ 
              color: pricingData.total > 0 ? theme.colors.warning : theme.colors.success,
              fontSize: 24
            }}
          />
          {pricingData.data.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              Top: {pricingData.data[0]?.DESC_PRODUCTO?.substring(0, 20)}...
            </Text>
          )}
        </Card>
      </Col>
      
      <Col xs={24} sm={8}>
        <Card 
          size="small" 
          style={{ 
            textAlign: 'center', 
            borderColor: margenData.total > 0 ? theme.colors.info : theme.colors.success,
            cursor: 'pointer',
            backgroundColor: activeTab === 'margen' ? '#f0f5ff' : 'white'
          }}
          onClick={() => setActiveTab('margen')}
          hoverable
        >
          <Statistic
            title={
              <Space>
                <PercentageOutlined />
                <span>Margen (Z≥{margenData.z})</span>
              </Space>
            }
            value={margenData.total}
            valueStyle={{ 
              color: margenData.total > 0 ? theme.colors.info : theme.colors.success,
              fontSize: 24
            }}
          />
          {margenData.data.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              Top: {margenData.data[0]?.DESC_GESTOR?.split(' ')[0]}...
            </Text>
          )}
        </Card>
      </Col>

      <Col xs={24} sm={8}>
        <Card 
          size="small" 
          style={{ 
            textAlign: 'center', 
            borderColor: volumenData.total > 0 ? theme.colors.bmGreenLight : theme.colors.success,
            cursor: 'pointer',
            backgroundColor: activeTab === 'volumen' ? '#f6ffed' : 'white'
          }}
          onClick={() => setActiveTab('volumen')}
          hoverable
        >
          <Statistic
            title={
              <Space>
                <UsergroupAddOutlined />
                <span>Volumen (×{volumenData.factor})</span>
              </Space>
            }
            value={volumenData.total}
            valueStyle={{ 
              color: volumenData.total > 0 ? theme.colors.bmGreenLight : theme.colors.success,
              fontSize: 24
            }}
          />
          {volumenData.data.length > 0 && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              Top: {volumenData.data[0]?.DESC_GESTOR?.split(' ')[0]}...
            </Text>
          )}
        </Card>
      </Col>
    </Row>
  );

  /**
   * ✅ Columnas de tabla (IDÉNTICAS AL ORIGINAL - NO TOCAR)
   */
  const getPricingColumns = () => [
    {
      title: 'Producto',
      dataIndex: 'DESC_PRODUCTO',
      key: 'producto',
      width: 200,
      fixed: 'left',
      render: (text) => (
        <Tooltip title={text}>
          <Text strong style={{ fontSize: 12 }}>
            {text?.substring(0, 30)}{text?.length > 30 ? '...' : ''}
          </Text>
        </Tooltip>
      )
    },
    {
      title: 'Segmento',
      dataIndex: 'DESC_SEGMENTO',
      key: 'segmento',
      width: 120,
      render: (text) => <Text style={{ fontSize: 12 }}>{text}</Text>
    },
    {
      title: 'Precio Std',
      dataIndex: 'PRECIO_MANTENIMIENTO',
      key: 'precio_std',
      width: 100,
      align: 'right',
      render: (val) => (
        <Text style={{ fontSize: 12 }}>
          {Math.abs(val || 0).toFixed(0)}€
        </Text>
      )
    },
    {
      title: 'Precio Real',
      dataIndex: 'PRECIO_MANTENIMIENTO_REAL',
      key: 'precio_real',
      width: 100,
      align: 'right',
      render: (val) => (
        <Text style={{ fontSize: 12 }}>
          {Math.abs(val || 0).toFixed(0)}€
        </Text>
      )
    },
    {
      title: 'Desviación',
      dataIndex: 'desviacion_pct',
      key: 'desviacion',
      width: 100,
      align: 'right',
      sorter: (a, b) => Math.abs(a.desviacion_pct || 0) - Math.abs(b.desviacion_pct || 0),
      render: (val) => (
        <Tag 
          color={Math.abs(val) > 20 ? 'red' : Math.abs(val) > 15 ? 'orange' : 'blue'}
          style={{ fontSize: 11 }}
        >
          {val > 0 ? '+' : ''}{(val || 0).toFixed(1)}%
        </Tag>
      )
    },
    {
      title: 'Contratos',
      dataIndex: 'NUM_CONTRATOS_BASE',
      key: 'contratos',
      width: 80,
      align: 'center',
      render: (val) => <Badge count={val || 0} />
    },
    {
      title: 'Nivel',
      dataIndex: 'nivel_alerta',
      key: 'nivel',
      width: 80,
      render: (val) => (
        <Tag 
          color={val === 'ALTA' ? 'red' : val === 'MEDIA' ? 'orange' : 'green'}
          style={{ fontSize: 11 }}
        >
          {val}
        </Tag>
      )
    },
    {
      title: 'Acción',
      dataIndex: 'accion_recomendada',
      key: 'accion',
      width: 200,
      render: (text) => (
        <Tooltip title={text}>
          <Text style={{ fontSize: 11 }}>
            {text?.length > 30 ? `${text.substring(0, 30)}...` : text}
          </Text>
        </Tooltip>
      )
    }
  ];

  const getMargenColumns = () => [
    {
      title: 'Gestor',
      dataIndex: 'DESC_GESTOR',
      key: 'gestor',
      width: 180,
      fixed: 'left',
      render: (text) => <Text strong style={{ fontSize: 12 }}>{text}</Text>
    },
    {
      title: 'Centro',
      dataIndex: 'DESC_CENTRO',
      key: 'centro',
      width: 140,
      render: (text) => (
        <Text style={{ fontSize: 12 }}>
          {text?.replace('MADRID-', '')?.replace('PALMA-', '')?.replace('BARCELONA-', '')?.replace('BILBAO-', '')?.replace('MALAGA-', '')}
        </Text>
      )
    },
    {
      title: 'Segmento',
      dataIndex: 'DESC_SEGMENTO',
      key: 'segmento',
      width: 120,
      render: (text) => <Text style={{ fontSize: 12 }}>{text?.replace('Banca de ', '').replace('Banca ', '')}</Text>
    },
    {
      title: 'Margen %',
      dataIndex: 'margen_neto',
      key: 'margen',
      width: 90,
      align: 'right',
      sorter: (a, b) => (a.margen_neto || 0) - (b.margen_neto || 0),
      render: (val) => (
        <Text style={{ 
          color: (val || 0) < 0 ? theme.colors.error : (val || 0) < 30 ? theme.colors.warning : theme.colors.success,
          fontWeight: 600,
          fontSize: 12
        }}>
          {(val || 0).toFixed(1)}%
        </Text>
      )
    },
    {
      title: 'Beneficio (€)',
      dataIndex: 'beneficio_neto',
      key: 'beneficio',
      width: 100,
      align: 'right',
      render: (val) => (
        <Text style={{ 
          color: (val || 0) < 0 ? theme.colors.error : theme.colors.success,
          fontSize: 12
        }}>
          {(val || 0).toLocaleString('es-ES')}€
        </Text>
      )
    },
    {
      title: 'Z-Score',
      dataIndex: 'z_score',
      key: 'zscore',
      width: 80,
      align: 'right',
      sorter: (a, b) => Math.abs(a.z_score || 0) - Math.abs(b.z_score || 0),
      render: (val) => (
        <Tag color={Math.abs(val || 0) > 2.5 ? 'red' : 'blue'} style={{ fontSize: 11 }}>
          {(val || 0).toFixed(2)}
        </Tag>
      )
    },
    {
      title: 'Clasificación',
      dataIndex: 'clasificacion_margen',
      key: 'clasificacion',
      width: 100,
      render: (val) => (
        <Tag 
          color={val === 'PERDIDAS' ? 'red' : val === 'BAJO' ? 'orange' : val === 'ACEPTABLE' ? 'blue' : 'green'}
          style={{ fontSize: 10 }}
        >
          {val}
        </Tag>
      )
    },
    {
      title: 'Anomalía',
      dataIndex: 'clasificacion_anomalia',
      key: 'anomalia',
      width: 120,
      render: (val) => (
        <Tag 
          color={val === 'OUTLIER_EXTREMO' ? 'red' : val === 'OUTLIER_MODERADO' ? 'orange' : 'green'}
          style={{ fontSize: 10 }}
        >
          {val?.replace('OUTLIER_', '')}
        </Tag>
      )
    }
  ];

  const getVolumenColumns = () => [
    {
      title: 'Gestor',
      dataIndex: 'DESC_GESTOR',
      key: 'gestor',
      width: 180,
      fixed: 'left',
      render: (text) => <Text strong style={{ fontSize: 12 }}>{text}</Text>
    },
    {
      title: 'Centro',
      dataIndex: 'DESC_CENTRO',
      key: 'centro',
      width: 140,
      render: (text) => (
        <Text style={{ fontSize: 12 }}>
          {text?.replace('MADRID-', '')?.replace('PALMA-', '')?.replace('BARCELONA-', '')?.replace('BILBAO-', '')?.replace('MALAGA-', '')}
        </Text>
      )
    },
    {
      title: 'Segmento',
      dataIndex: 'DESC_SEGMENTO',
      key: 'segmento',
      width: 120,
      render: (text) => <Text style={{ fontSize: 12 }}>{text?.replace('Banca de ', '').replace('Banca ', '')}</Text>
    },
    {
      title: 'Contratos',
      dataIndex: 'total_contratos',
      key: 'contratos',
      width: 80,
      align: 'center',
      sorter: (a, b) => (a.total_contratos || 0) - (b.total_contratos || 0),
      render: (val) => <Badge count={val || 0} />
    },
    {
      title: 'Nuevos',
      dataIndex: 'contratos_nuevos_periodo',
      key: 'nuevos',
      width: 70,
      align: 'center',
      render: (val) => (
        <Text style={{ 
          color: (val || 0) > 2 ? theme.colors.success : (val || 0) > 0 ? theme.colors.warning : theme.colors.error,
          fontWeight: 600,
          fontSize: 12
        }}>
          {val || 0}
        </Text>
      )
    },
    {
      title: 'Movimientos',
      dataIndex: 'total_movimientos',
      key: 'movimientos',
      width: 90,
      align: 'center',
      render: (val) => <Text style={{ fontSize: 12 }}>{val || 0}</Text>
    },
    {
      title: 'Ratio Contratos',
      dataIndex: 'ratio_contratos_vs_media',
      key: 'ratio_contratos',
      width: 110,
      align: 'right',
      sorter: (a, b) => (a.ratio_contratos_vs_media || 0) - (b.ratio_contratos_vs_media || 0),
      render: (val) => (
        <Text style={{ 
          color: (val || 0) < 0.5 ? theme.colors.error : (val || 0) > 2 ? theme.colors.warning : theme.colors.success,
          fontWeight: 600,
          fontSize: 12
        }}>
          {(val || 0).toFixed(2)}×
        </Text>
      )
    },
    {
      title: 'Ingresos (€)',
      dataIndex: 'ingresos_generados',
      key: 'ingresos',
      width: 100,
      align: 'right',
      render: (val) => (
        <Text style={{ fontSize: 12 }}>
          {(val || 0).toLocaleString('es-ES', { maximumFractionDigits: 0 })}€
        </Text>
      )
    },
    {
      title: 'Tipo Outlier',
      dataIndex: 'tipo_outlier',
      key: 'tipo',
      width: 120,
      render: (val) => (
        <Tag 
          color={val === 'SIN_ACTIVIDAD' ? 'red' : val === 'PICO_COMERCIAL' ? 'blue' : 'green'}
          style={{ fontSize: 10 }}
        >
          {val?.replace('_', ' ')}
        </Tag>
      )
    },
    {
      title: 'Eficiencia',
      dataIndex: 'clasificacion_eficiencia',
      key: 'eficiencia',
      width: 100,
      render: (val) => (
        <Tag 
          color={val === 'INEFICIENTE' ? 'red' : val === 'EQUILIBRADO' ? 'orange' : val === 'EFICIENTE' ? 'blue' : 'green'}
          style={{ fontSize: 10 }}
        >
          {val}
        </Tag>
      )
    }
  ];

  /**
   * ✅ Pestañas dinámicas
   */
  const getDynamicTabItems = () => {
    const commonTableProps = {
      size: "small",
      scroll: { x: 1400, y: 500 },
      pagination: { 
        pageSize: 10, 
        size: 'small',
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) => (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {range[0]}-{range[1]} de {total} elementos
          </Text>
        )
      },
      bordered: true,
      style: { backgroundColor: 'white' }
    };

    return [
      {
        key: 'pricing',
        label: (
          <Space>
            <DollarOutlined />
            <span>Pricing</span>
            <Badge 
              count={pricingData.total} 
              size="small"
              style={{ backgroundColor: pricingData.total > 0 ? theme.colors.warning : theme.colors.success }}
            />
          </Space>
        ),
        children: (
          <div>
            {pricingData.total > 0 && (
              <Alert
                message={`${pricingData.total} desviaciones de pricing detectadas con umbral ≥${pricingData.umbral}%`}
                type="warning"
                showIcon
                closable
                style={{ marginBottom: 16 }}
                description={
                  pricingData.data.length > 0 && 
                  `Producto más desviado: ${pricingData.data[0]?.DESC_PRODUCTO} (${(pricingData.data[0]?.desviacion_pct || 0).toFixed(1)}%)`
                }
              />
            )}
            <Table
              {...commonTableProps}
              columns={getPricingColumns()}
              dataSource={pricingData.data.map((item, idx) => ({ ...item, key: `pricing-${idx}` }))}
              locale={{
                emptyText: (
                  <Empty 
                    description={`No hay desviaciones de pricing ≥${pricingData.umbral}% en ${periodo}`}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )
              }}
            />
          </div>
        )
      },
      {
        key: 'margen',
        label: (
          <Space>
            <PercentageOutlined />
            <span>Margen</span>
            <Badge 
              count={margenData.total} 
              size="small"
              style={{ backgroundColor: margenData.total > 0 ? theme.colors.info : theme.colors.success }}
            />
          </Space>
        ),
        children: (
          <div>
            {margenData.total > 0 && (
              <Alert
                message={`${margenData.total} anomalías de margen detectadas con Z-Score ≥${margenData.z}`}
                type="info"
                showIcon
                closable
                style={{ marginBottom: 16 }}
                description={
                  margenData.data.length > 0 && 
                  `Gestor más anómalo: ${margenData.data[0]?.DESC_GESTOR} (Z=${(margenData.data[0]?.z_score || 0).toFixed(2)})`
                }
              />
            )}
            <Table
              {...commonTableProps}
              columns={getMargenColumns()}
              dataSource={margenData.data.map((item, idx) => ({ ...item, key: `margen-${idx}` }))}
              locale={{
                emptyText: (
                  <Empty 
                    description={`No hay anomalías de margen con Z-Score ≥${margenData.z} en ${periodo}`}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )
              }}
            />
          </div>
        )
      },
      {
        key: 'volumen',
        label: (
          <Space>
            <UsergroupAddOutlined />
            <span>Volumen</span>
            <Badge 
              count={volumenData.total} 
              size="small"
              style={{ backgroundColor: volumenData.total > 0 ? theme.colors.bmGreenLight : theme.colors.success }}
            />
          </Space>
        ),
        children: (
          <div>
            {volumenData.total > 0 && (
              <Alert
                message={`${volumenData.total} outliers de volumen detectados con factor ×${volumenData.factor}`}
                type="success"
                showIcon
                closable
                style={{ marginBottom: 16 }}
                description={
                  volumenData.data.length > 0 && 
                  `Gestor más outlier: ${volumenData.data[0]?.DESC_GESTOR} (${volumenData.data[0]?.tipo_outlier})`
                }
              />
            )}
            <Table
              {...commonTableProps}
              columns={getVolumenColumns()}
              dataSource={volumenData.data.map((item, idx) => ({ ...item, key: `volumen-${idx}` }))}
              locale={{
                emptyText: (
                  <Empty 
                    description={`No hay outliers de volumen con factor ×${volumenData.factor} en ${periodo}`}
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                  />
                )
              }}
            />
          </div>
        )
      }
    ];
  };

  // Effects
  useEffect(() => {
    fetchAllDeviationData();
  }, [fetchAllDeviationData]);

  // Handlers
  const handleRefresh = useCallback(() => {
    fetchAllDeviationData();
    onReload();
  }, [fetchAllDeviationData, onReload]);

  if (loading) {
    return (
      <div style={{ padding: 50, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>
            Cargando análisis de desviaciones para {periodo}...
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            Pricing: {pricingUmbral}% | Margen: Z≥{margenZScore} | Volumen: ×{volumenFactor}
          </Text>
          {useDebugMode && (
            <div style={{ marginTop: 8 }}>
              <Tag color="purple">ULTRA DEBUG - Extractor inteligente activo</Tag>
            </div>
          )}
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
        message="Error cargando desviaciones"
        description="No se pudieron obtener los datos de los endpoints de desviaciones"
      />
    );
  }

  const totalDeviations = pricingData.total + margenData.total + volumenData.total;

  return (
    <div 
      className={className} 
      style={{ 
        width: '100%', 
        height: '100vh',
        overflowY: 'auto',
        backgroundColor: '#fafafa',
        padding: '16px',
        ...style 
      }}
    >
      <Card
        style={{ 
          width: '100%', 
          minHeight: '95vh',
          backgroundColor: 'white',
          borderRadius: 8
        }}
        styles={{ body: { padding: '24px' } }}
        title={
          <Space>
            <AlertOutlined style={{ color: theme.colors.bmGreenPrimary }} />
            <Title level={4} style={{ margin: 0 }}>
              Análisis de Desviaciones Dinámico
            </Title>
            <Badge 
              count={totalDeviations} 
              style={{ backgroundColor: theme.colors.bmGreenPrimary }} 
            />
            <Text type="secondary">• {periodo}</Text>
            {parametersChanged && (
              <Tag color="processing">Parámetros modificados</Tag>
            )}
            {useDebugMode && (
              <Tag color="purple" icon={<BugOutlined />}>Extractor</Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Última actualización: {new Date().toLocaleTimeString()}
            </Text>
            <Button 
              size="small"
              icon={<ReloadOutlined />} 
              onClick={handleRefresh}
              loading={loading}
            >
              Actualizar
            </Button>
          </Space>
        }
      >
        {renderDynamicParameterControls()}
        {renderDynamicSummaryHeader()}
        
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          size="small"
          style={{ minHeight: 600 }}
          items={getDynamicTabItems()}
          tabBarStyle={{ marginBottom: 16 }}
        />
      </Card>
    </div>
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
