// frontend/src/components/Dashboard/ConversationalPivot.jsx
/* eslint-disable no-console */

/**
 * ConversationalPivot v2.0 — Perfect Integration + Role-Based Chart Pivoting
 * ---------------------------------------------------------------------------
 * ✅ Pivoteo conversacional de gráficos mediante lenguaje natural
 * ✅ Perfect Integration con Chat Agent v11.0 + CDG Agent v6.1
 * ✅ Control de acceso por rol (gestor vs dirección)
 * ✅ Integración bidireccional con InteractiveCharts.jsx
 * ✅ Interpretación inteligente del LLM con contexto bancario
 * ✅ Sugerencias contextuales según gráfico actual
 * ✅ Validaciones de permisos en tiempo real
 * ✅ Historial de conversación persistente
 * ✅ Feedback visual de cambios aplicados
 * ✅ Fallback local si backend no disponible
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  List,
  Tag,
  Avatar,
  Tooltip,
  Alert,
  Spin,
  Badge,
  Divider,
  Empty,
  App
} from 'antd';

import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  BulbOutlined,
  ReloadOutlined,
  ClearOutlined,
  LockOutlined,
  UnlockOutlined
} from '@ant-design/icons';

import PropTypes from 'prop-types';

// ✅ Services
import analyticsService, {
  pivotChart,
  getPivotableChartData,
  PIVOTABLE_CONFIG
} from '../../services/analyticsService';

import chatService, {
  parsePivotIntent,
  validatePivotCombination,
  PIVOT_CONFIG
} from '../../services/chatService';

import theme from '../../styles/theme';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

/* =========================================
 * ✅ CONFIGURACIÓN DE PERMISOS POR ROL
 * ========================================= */

/**
 * Métricas permitidas por rol
 */
const ALLOWED_METRICS = {
  direccion: ['CONTRATOS', 'CLIENTES', 'INGRESOS', 'GASTOS', 'MARGEN_NETO', 'ROE', 'INCENTIVOS'],
  gestor: ['CONTRATOS', 'CLIENTES', 'INGRESOS', 'GASTOS', 'MARGEN_NETO', 'ROE'] // Sin INCENTIVOS de otros
};

/**
 * Dimensiones permitidas por rol
 */
const ALLOWED_DIMENSIONS = {
  direccion: ['gestor', 'centro', 'producto', 'cliente', 'segmento', 'contrato'],
  gestor: ['cliente', 'producto', 'contrato'] // Solo datos propios
};

/**
 * Tipos de gráfico permitidos (común para ambos)
 */
const ALLOWED_CHART_TYPES = ['bar', 'horizontal_bar', 'pie', 'donut', 'line', 'area'];

/**
 * Valida si el usuario tiene permiso para esta combinación
 */
const validateUserPermissions = (metric, dimension, mode) => {
  const allowedMetrics = ALLOWED_METRICS[mode];
  const allowedDimensions = ALLOWED_DIMENSIONS[mode];

  if (!allowedMetrics.includes(metric)) {
    return {
      allowed: false,
      reason: `No tienes permiso para ver la métrica ${metric}`,
      suggestion: `Prueba con: ${allowedMetrics.join(', ')}`
    };
  }

  if (!allowedDimensions.includes(dimension)) {
    return {
      allowed: false,
      reason: `No tienes permiso para ver datos por ${dimension}`,
      suggestion: `Prueba con: ${allowedDimensions.join(', ')}`
    };
  }

  return { allowed: true };
};

/* =========================================
 * ✅ UTILIDADES
 * ========================================= */

/**
 * Genera ejemplos contextuales según rol
 */
const getContextualExamples = (mode, currentConfig = {}) => {
  if (mode === 'direccion') {
    return [
      'Muéstrame los top 10 gestores por margen neto',
      'Cambia a ingresos por centro',
      'Ponlo en gráfico circular',
      'Muestra los gastos por segmento',
      'Ranking de contratos por gestor',
      'Comparativa de ROE entre centros'
    ];
  } else {
    return [
      'Muéstrame mis clientes por margen',
      'Cambia a ingresos por producto',
      'Ponlo en gráfico de barras',
      'Mis contratos por cliente',
      'Productos más rentables',
      'Gastos por tipo de producto'
    ];
  }
};

/**
 * Genera sugerencias según gráfico actual
 */
const generateSuggestions = (currentConfig, mode) => {
  const suggestions = [];

  if (!currentConfig || !currentConfig.metric) {
    suggestions.push('¿Qué te gustaría visualizar?');
    return suggestions;
  }

  const { metric, dimension, chartType } = currentConfig;
  
  // Sugerir cambio de métrica
  const allowedMetrics = ALLOWED_METRICS[mode];
  const otherMetrics = allowedMetrics.filter(m => m !== metric);
  if (otherMetrics.length > 0) {
    suggestions.push(`Cambia a ${otherMetrics[0].toLowerCase()}`);
  }

  // Sugerir cambio de dimensión
  const allowedDimensions = ALLOWED_DIMENSIONS[mode];
  const otherDimensions = allowedDimensions.filter(d => d !== dimension);
  if (otherDimensions.length > 0) {
    suggestions.push(`Muestra por ${otherDimensions[0]}`);
  }

  // Sugerir cambio de tipo de gráfico
  const otherChartTypes = ALLOWED_CHART_TYPES.filter(t => t !== chartType);
  if (otherChartTypes.length > 0 && otherChartTypes[0] !== 'bar') {
    const chartTypeLabels = {
      horizontal_bar: 'barras horizontales',
      pie: 'circular',
      donut: 'donut',
      line: 'líneas',
      area: 'área'
    };
    suggestions.push(`Ponlo en ${chartTypeLabels[otherChartTypes[0]] || otherChartTypes[0]}`);
  }

  return suggestions.slice(0, 3); // Máximo 3 sugerencias
};

/**
 * Formatea el nombre de métrica para mostrar
 */
const formatMetricLabel = (metric) => {
  const labels = {
    CONTRATOS: 'Contratos',
    CLIENTES: 'Clientes',
    INGRESOS: 'Ingresos',
    GASTOS: 'Gastos',
    MARGEN_NETO: 'Margen Neto',
    ROE: 'ROE',
    INCENTIVOS: 'Incentivos'
  };
  return labels[metric] || metric;
};

/**
 * Formatea el nombre de dimensión para mostrar
 */
const formatDimensionLabel = (dimension) => {
  const labels = {
    gestor: 'Gestores',
    centro: 'Centros',
    producto: 'Productos',
    cliente: 'Clientes',
    segmento: 'Segmentos',
    contrato: 'Contratos'
  };
  return labels[dimension] || dimension;
};

/* =========================================
 * ✅ COMPONENTE PRINCIPAL
 * ========================================= */

const ConversationalPivot = ({
  mode = 'direccion',
  periodo = '2025-10',
  gestorId = null,
  currentChartConfig = null,
  onChartUpdate = () => {},
  height = 600,
  className = '',
  style = {}
}) => {
  
  const { notification, message: antMessage } = App.useApp();

  /* =========================================
   * Estados
   * ========================================= */
  
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [currentConfig, setCurrentConfig] = useState(currentChartConfig);
  const [suggestions, setSuggestions] = useState([]);
  const [lastPivotResult, setLastPivotResult] = useState(null);

  const inputRef = useRef(null);
  const historyEndRef = useRef(null);

  /* =========================================
   * Sincronizar currentConfig externo
   * ========================================= */

  useEffect(() => {
    if (currentChartConfig) {
      setCurrentConfig(currentChartConfig);
      setSuggestions(generateSuggestions(currentChartConfig, mode));
    }
  }, [currentChartConfig, mode]);

  /* =========================================
   * Auto-scroll al final del historial
   * ========================================= */

  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationHistory]);

  /* =========================================
   * Cargar historial desde localStorage
   * ========================================= */

  useEffect(() => {
    const savedHistory = localStorage.getItem(`conversational-pivot-history-${mode}`);
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setConversationHistory(parsed);
      } catch (e) {
        console.warn('[ConversationalPivot] Error loading history:', e);
      }
    }
  }, [mode]);

  /* =========================================
   * Guardar historial en localStorage
   * ========================================= */

  const saveHistory = useCallback((history) => {
    try {
      localStorage.setItem(`conversational-pivot-history-${mode}`, JSON.stringify(history));
    } catch (e) {
      console.warn('[ConversationalPivot] Error saving history:', e);
    }
  }, [mode]);

  /* =========================================
   * Procesamiento de mensaje
   * ========================================= */

  const processMessage = useCallback(async (userMessage) => {
    if (!userMessage.trim()) return;

    console.log(`[ConversationalPivot] 🚀 Processing message: "${userMessage}"`);

    setIsProcessing(true);

    // Añadir mensaje del usuario al historial
    const userEntry = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    const newHistory = [...conversationHistory, userEntry];
    setConversationHistory(newHistory);
    setInputValue('');

    try {
      // ✅ PASO 1: Intentar backend primero (Chat Agent v11.0)
      let pivotResult = null;
      let usedFallback = false;

      try {
        console.log('[ConversationalPivot] 🔄 Attempting backend pivot...');
        
        pivotResult = await analyticsService.pivotChart(
          'user-id', // TODO: Obtener de contexto de usuario
          userMessage,
          currentConfig || {},
          'pivot',
          {
            gestorId,
            periodo,
            mode
          }
        );

        console.log('[ConversationalPivot] ✅ Backend pivot successful:', pivotResult);

      } catch (backendError) {
        console.warn('[ConversationalPivot] ⚠️ Backend pivot failed, using local fallback:', backendError.message);
        usedFallback = true;

        // ✅ PASO 2: Fallback local con parsePivotIntent
        const parsedIntent = parsePivotIntent(userMessage, currentConfig || {});

        if (!parsedIntent) {
          throw new Error('No se pudo interpretar tu solicitud. Intenta ser más específico.');
        }

        console.log('[ConversationalPivot] 🔍 Local parsing result:', parsedIntent);

        // ✅ PASO 3: Validar permisos
        const permissionCheck = validateUserPermissions(
          parsedIntent.metric,
          parsedIntent.dimension,
          mode
        );

        if (!permissionCheck.allowed) {
          throw new Error(`🔒 ${permissionCheck.reason}. ${permissionCheck.suggestion}`);
        }

        // ✅ PASO 4: Validar combinación técnica
        const combinationCheck = validatePivotCombination(
          parsedIntent.metric,
          parsedIntent.dimension,
          parsedIntent.chartType
        );

        if (!combinationCheck.valid) {
          throw new Error(`❌ ${combinationCheck.reason}`);
        }

        // ✅ PASO 5: Obtener datos
        console.log('[ConversationalPivot] 📊 Fetching chart data...');

        const chartData = await getPivotableChartData(
          parsedIntent.metric,
          parsedIntent.dimension,
          parsedIntent.chartType,
          {
            gestorId,
            periodo,
            mode
          }
        );

        pivotResult = {
          success: true,
          data: chartData,
          source: 'local_fallback',
          newConfig: {
            metric: parsedIntent.metric,
            dimension: parsedIntent.dimension,
            chartType: parsedIntent.chartType
          },
          changesMade: [
            `Métrica: ${formatMetricLabel(parsedIntent.metric)}`,
            `Dimensión: ${formatDimensionLabel(parsedIntent.dimension)}`,
            `Tipo: ${parsedIntent.chartType}`
          ]
        };
      }

      // ✅ PASO 6: Procesar resultado exitoso
      if (pivotResult && pivotResult.success) {
        const newConfig = pivotResult.newConfig || pivotResult.data?.meta;

        setCurrentConfig(newConfig);
        setLastPivotResult(pivotResult);
        setSuggestions(generateSuggestions(newConfig, mode));

        // Notificar a InteractiveCharts
        onChartUpdate(pivotResult.data, newConfig);

        // ✅ PASO 7: Generar interpretación del LLM (simulada si es fallback)
        let interpretation = '';

        if (usedFallback) {
          // Interpretación local básica
          const metric = formatMetricLabel(newConfig.metric);
          const dimension = formatDimensionLabel(newConfig.dimension);
          
          interpretation = `He actualizado el gráfico para mostrar **${metric}** por **${dimension}**.\n\n`;
          
          // Añadir insights básicos según métrica
          if (newConfig.metric === 'MARGEN_NETO') {
            interpretation += '📊 Este gráfico te permite identificar las áreas más rentables. ';
          } else if (newConfig.metric === 'CONTRATOS') {
            interpretation += '📊 Este gráfico muestra la distribución de contratos. ';
          } else if (newConfig.metric === 'INGRESOS') {
            interpretation += '💰 Este gráfico muestra los ingresos generados. ';
          }

          interpretation += 'Puedes pedirme que cambie la métrica, dimensión o tipo de gráfico.';

        } else {
          // Usar interpretación del backend (Chat Agent v11.0)
          interpretation = pivotResult.interpretation || 
            pivotResult.data?.interpretation || 
            'Gráfico actualizado correctamente.';
        }

        // Añadir respuesta del agente al historial
        const agentEntry = {
          id: Date.now() + 1,
          type: 'agent',
          content: interpretation,
          timestamp: new Date().toISOString(),
          changes: pivotResult.changesMade || [],
          config: newConfig,
          source: usedFallback ? 'local' : 'backend'
        };

        const updatedHistory = [...newHistory, agentEntry];
        setConversationHistory(updatedHistory);
        saveHistory(updatedHistory);

        // Notificación de éxito
        antMessage.success({
          content: '✅ Gráfico actualizado',
          duration: 2
        });

      } else {
        throw new Error('No se pudo completar el cambio solicitado');
      }

    } catch (error) {
      console.error('[ConversationalPivot] ❌ Error processing message:', error);

      // Añadir error al historial
      const errorEntry = {
        id: Date.now() + 1,
        type: 'error',
        content: error.message,
        timestamp: new Date().toISOString()
      };

      const updatedHistory = [...newHistory, errorEntry];
      setConversationHistory(updatedHistory);
      saveHistory(updatedHistory);

      notification.error({
        message: 'Error al procesar solicitud',
        description: error.message,
        duration: 4
      });
    } finally {
      setIsProcessing(false);
    }
  }, [
    conversationHistory,
    currentConfig,
    mode,
    gestorId,
    periodo,
    onChartUpdate,
    notification,
    antMessage,
    saveHistory
  ]);

  /* =========================================
   * Handlers
   * ========================================= */

  const handleSend = useCallback(() => {
    if (inputValue.trim() && !isProcessing) {
      processMessage(inputValue.trim());
    }
  }, [inputValue, isProcessing, processMessage]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleSuggestionClick = useCallback((suggestion) => {
    setInputValue(suggestion);
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  const handleClearHistory = useCallback(() => {
    setConversationHistory([]);
    localStorage.removeItem(`conversational-pivot-history-${mode}`);
    setLastPivotResult(null);
    antMessage.success('Historial limpiado');
  }, [mode, antMessage]);

  /* =========================================
   * Renderizado de mensajes
   * ========================================= */

  const renderMessage = (entry) => {
    const isUser = entry.type === 'user';
    const isError = entry.type === 'error';
    const isAgent = entry.type === 'agent';

    return (
      <List.Item
        key={entry.id}
        style={{
          padding: '12px 0',
          border: 'none',
          justifyContent: isUser ? 'flex-end' : 'flex-start'
        }}
      >
        <Space
          align="start"
          direction={isUser ? 'horizontal-reverse' : 'horizontal'}
          style={{ maxWidth: '85%' }}
        >
          {/* Avatar */}
          <Avatar
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{
              backgroundColor: isError
                ? '#ff4d4f'
                : isUser
                ? theme.colors?.bmGreenPrimary || '#1b5e55'
                : '#52c41a'
            }}
          />

          {/* Contenido del mensaje */}
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 8,
              backgroundColor: isError
                ? '#fff1f0'
                : isUser
                ? '#e6f7ff'
                : '#f6ffed',
              border: `1px solid ${
                isError ? '#ffccc7' : isUser ? '#91d5ff' : '#b7eb8f'
              }`,
              maxWidth: '100%'
            }}
          >
            {/* Contenido */}
            <Paragraph
              style={{
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}
            >
              {entry.content}
            </Paragraph>

            {/* Cambios aplicados (solo agente) */}
            {isAgent && entry.changes && entry.changes.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <Divider style={{ margin: '8px 0' }} />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  <CheckCircleOutlined /> Cambios aplicados:
                </Text>
                <div style={{ marginTop: 4 }}>
                  {entry.changes.map((change, idx) => (
                    <Tag
                      key={idx}
                      color="success"
                      style={{ marginBottom: 4 }}
                    >
                      {change}
                    </Tag>
                  ))}
                </div>
              </div>
            )}

            {/* Fuente (solo agente) */}
            {isAgent && entry.source && (
              <div style={{ marginTop: 8 }}>
                <Tag
                  icon={entry.source === 'backend' ? <ThunderboltOutlined /> : <BulbOutlined />}
                  color={entry.source === 'backend' ? 'blue' : 'orange'}
                  style={{ fontSize: 11 }}
                >
                  {entry.source === 'backend' ? 'Chat Agent v11.0' : 'Parser Local'}
                </Tag>
              </div>
            )}

            {/* Timestamp */}
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 11 }}>
                {new Date(entry.timestamp).toLocaleTimeString()}
              </Text>
            </div>
          </div>
        </Space>
      </List.Item>
    );
  };

  /* =========================================
   * Configuración actual
   * ========================================= */

  const currentConfigDisplay = useMemo(() => {
    if (!currentConfig) return null;

    return (
      <Card
        size="small"
        title={
          <Space>
            <InfoCircleOutlined />
            <Text strong>Configuración Actual</Text>
          </Space>
        }
        style={{ marginBottom: 12 }}
      >
        <Space wrap>
          <Tag color="blue">
            <strong>Métrica:</strong> {formatMetricLabel(currentConfig.metric)}
          </Tag>
          <Tag color="green">
            <strong>Dimensión:</strong> {formatDimensionLabel(currentConfig.dimension)}
          </Tag>
          <Tag color="orange">
            <strong>Tipo:</strong> {currentConfig.chartType}
          </Tag>
        </Space>
      </Card>
    );
  }, [currentConfig]);

  /* =========================================
   * Ejemplos contextuales
   * ========================================= */

  const contextualExamples = useMemo(() => {
    return getContextualExamples(mode, currentConfig);
  }, [mode, currentConfig]);

  /* =========================================
   * Render principal
   * ========================================= */

  return (
    <div className={`conversational-pivot ${className}`} style={style}>
      <Card
        title={
          <Space>
            <RobotOutlined style={{ fontSize: 20, color: theme.colors?.bmGreenPrimary }} />
            <div>
              <Title level={5} style={{ margin: 0 }}>
                Pivoteo Conversacional de Gráficos
              </Title>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Chat Agent v11.0 • Perfect Integration
              </Text>
            </div>
          </Space>
        }
        extra={
          <Space>
            <Badge
              status={mode === 'direccion' ? 'success' : 'processing'}
              text={mode === 'direccion' ? 'Acceso Completo' : 'Acceso Limitado'}
            />
            <Tooltip title="Limpiar historial">
              <Button
                size="small"
                icon={<ClearOutlined />}
                onClick={handleClearHistory}
                disabled={conversationHistory.length === 0}
              />
            </Tooltip>
          </Space>
        }
        styles={{
          body: {
            height: height - 56,
            display: 'flex',
            flexDirection: 'column',
            padding: 16
          }
        }}
      >
        {/* Alert de control de acceso */}
        <Alert
          message={
            mode === 'direccion'
              ? '✅ Puedes visualizar todas las métricas y dimensiones'
              : '🔒 Solo puedes ver tus clientes, productos y contratos'
          }
          type={mode === 'direccion' ? 'success' : 'info'}
          showIcon
          icon={mode === 'direccion' ? <UnlockOutlined /> : <LockOutlined />}
          style={{ marginBottom: 12 }}
          closable
        />

        {/* Configuración actual */}
        {currentConfigDisplay}

        {/* Historial de conversación */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            marginBottom: 12,
            padding: '0 8px',
            backgroundColor: '#fafafa',
            borderRadius: 8
          }}
        >
          {conversationHistory.length === 0 ? (
            <Empty
              description={
                <div>
                  <Paragraph>
                    👋 ¡Hola! Soy tu asistente para pivoteo de gráficos.
                  </Paragraph>
                  <Paragraph type="secondary">
                    Dime qué te gustaría visualizar y yo me encargo del resto.
                  </Paragraph>
                </div>
              }
              image={<RobotOutlined style={{ fontSize: 64, opacity: 0.3 }} />}
            />
          ) : (
            <List
              dataSource={conversationHistory}
              renderItem={renderMessage}
              split={false}
            />
          )}
          <div ref={historyEndRef} />
        </div>

        {/* Sugerencias contextuales */}
        {suggestions.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
              <BulbOutlined /> Sugerencias:
            </Text>
            <Space wrap size="small">
              {suggestions.map((suggestion, idx) => (
                <Tag
                  key={idx}
                  color="blue"
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  {suggestion}
                </Tag>
              ))}
            </Space>
          </div>
        )}

        {/* Ejemplos iniciales */}
        {conversationHistory.length === 0 && (
          <div style={{ marginBottom: 12 }}>
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
              <BulbOutlined /> Ejemplos:
            </Text>
            <Space wrap size="small">
              {contextualExamples.slice(0, 3).map((example, idx) => (
                <Tag
                  key={idx}
                  color="default"
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleSuggestionClick(example)}
                >
                  {example}
                </Tag>
              ))}
            </Space>
          </div>
        )}

        {/* Input de mensaje */}
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            ref={inputRef}
            placeholder="Escribe tu solicitud (ej: 'Cambia a ingresos por cliente')"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isProcessing}
            autoSize={{ minRows: 1, maxRows: 3 }}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={isProcessing ? <ReloadOutlined spin /> : <SendOutlined />}
            onClick={handleSend}
            disabled={!inputValue.trim() || isProcessing}
            loading={isProcessing}
          >
            Enviar
          </Button>
        </Space.Compact>
      </Card>
    </div>
  );
};

ConversationalPivot.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.string.isRequired,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  currentChartConfig: PropTypes.shape({
    metric: PropTypes.string,
    dimension: PropTypes.string,
    chartType: PropTypes.string
  }),
  onChartUpdate: PropTypes.func.isRequired,
  height: PropTypes.number,
  className: PropTypes.string,
  style: PropTypes.object
};

const ConversationalPivotWithApp = (props) => (
  <App>
    <ConversationalPivot {...props} />
  </App>
);

export default React.memo(ConversationalPivotWithApp);
