// src/components/Chat/ConversationalPivot.jsx
// ✅ VERSIÓN CORREGIDA v4.1 - Integración perfecta con ChatService y API
// ConversationalPivot v4.1 - Integración total con chatService.js v4.3 y api.js v5.5

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { 
  Input, Button, Typography, List, Space, Card, Spin, Badge, Divider, Row, Col, Progress,
  Collapse, Switch, Select, Tooltip, Avatar, Empty, Alert, Tag, App
} from 'antd';
import { 
  SendOutlined, SyncOutlined, BarChartOutlined, CheckCircleOutlined, LineChartOutlined, 
  PieChartOutlined, AreaChartOutlined, BulbOutlined, SettingOutlined, RobotOutlined, 
  UserOutlined, ThunderboltOutlined, ExperimentOutlined, EyeOutlined, ClearOutlined, 
  FullscreenOutlined, CompressOutlined, InfoCircleOutlined, WarningOutlined,
  ApiOutlined, DatabaseOutlined, ClockCircleOutlined, DashboardOutlined, FilterOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import { useChatService, CONNECTION_STATES } from '../../services/chatService';
import InteractiveCharts from '../Dashboard/InteractiveCharts';
import theme from '../../styles/theme';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { Panel } = Collapse;

// ============================================================================
// 🎯 CONFIGURACIÓN Y CONSTANTES v4.1
// ============================================================================

const CHART_COMMANDS = {
  TYPES: {
    'bar': ['barra', 'barras', 'columna', 'columnas', 'bar'],
    'line': ['línea', 'linea', 'líneas', 'lineas', 'evolución', 'tendencia', 'temporal'],
    'pie': ['circular', 'pastel', 'pie', 'torta', 'donut', 'dona'],
    'area': ['área', 'area', 'relleno', 'áreas', 'areas']
  },
  KPIS: {
    'ROE': ['roe', 'rentabilidad', 'return on equity'],
    'MARGEN_NETO': ['margen', 'margen neto', 'margin', 'beneficio', 'resultado'],
    'INGRESOS': ['ingresos', 'revenue', 'ventas', 'facturación'],
    'GASTOS': ['gastos', 'costes', 'expenses', 'costs'],
    'EFICIENCIA': ['eficiencia', 'efficiency', 'productividad'],
    'CONTRATOS': ['contratos', 'número de contratos', 'count'],
    'PRECIO_STD': ['precio estandar', 'precio std', 'precio estándar'],
    'PRECIO_REAL': ['precio real', 'precio actual']
  },
  DIMENSIONS: {
    'centro': ['centro', 'centros', 'oficina', 'oficinas', 'sucursal', 'sucursales'],
    'gestor': ['gestor', 'gestores', 'comercial', 'comerciales', 'vendedor', 'vendedores'],
    'cliente': ['cliente', 'clientes'],
    'producto': ['producto', 'productos', 'servicio', 'servicios'],
    'segmento': ['segmento', 'segmentos', 'categoria', 'categorias'],
    'contrato': ['contrato', 'contratos'],
    'periodo': ['tiempo', 'temporal', 'período', 'periodos', 'fecha', 'fechas']
  }
};

const SUGGESTION_COMMANDS = [
  'Cambia a gráfico circular',
  'Mostrar ROE por centro', 
  'Cambiar a líneas de tendencia',
  'Ver margen neto por gestor',
  'Gráfico de área para ingresos',
  'Comparar por período',
  'Mostrar eficiencia operativa',
  'Análisis por segmento',
  'Precio STD vs Real por producto',
  'Contratos por centro temporal',
  'Beneficio por segmento circular',
  'Evolución mensual de ingresos'
];

// ============================================================================
// 🎨 COMPONENTE MENSAJE CONVERSACIONAL
// ============================================================================

const ConversationMessage = React.memo(({ message, onSuggestCommand }) => {
  const isUser = message.sender === 'user';

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 12,
      gap: 8
    }}>
      {!isUser && (
        <Avatar 
          icon={<RobotOutlined />} 
          style={{ 
            backgroundColor: theme.colors.bmGreenLight,
            flexShrink: 0
          }} 
        />
      )}
      
      <div style={{
        maxWidth: '85%',
        backgroundColor: isUser ? theme.colors.bmGreenPrimary : '#fff',
        color: isUser ? '#fff' : theme.colors.textPrimary,
        borderRadius: 12,
        padding: '12px 16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        border: !isUser ? '1px solid ' + theme.colors.border : 'none',
        position: 'relative'
      }}>
        <Paragraph 
          style={{ 
            margin: 0, 
            color: isUser ? '#fff' : theme.colors.textPrimary,
            fontSize: 14,
            lineHeight: 1.5,
            whiteSpace: 'pre-wrap'
          }}
        >
          {message.text}
        </Paragraph>

        {/* Chart configurations */}
        {message.charts?.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text strong style={{ color: theme.colors.bmGreenDark, fontSize: 12 }}>
              📊 Configuraciones de gráfico:
            </Text>
            <div style={{ marginTop: 8 }}>
              {message.charts.map((chart, idx) => (
                <Tag key={idx} color="blue" style={{ marginBottom: 4 }}>
                  {chart.type || 'Configuración'}: {chart.title || `Gráfico ${idx + 1}`}
                </Tag>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {message.recommendations?.length > 0 && (
          <div style={{
            marginTop: 12,
            padding: 10,
            backgroundColor: theme.colors.bmGreenLight + '20',
            borderRadius: 6,
            borderLeft: '3px solid ' + theme.colors.bmGreenPrimary
          }}>
            <Text strong style={{ color: theme.colors.bmGreenDark, fontSize: 12 }}>
              💡 Sugerencias:
            </Text>
            <div style={{ marginTop: 6 }}>
              {message.recommendations.slice(0, 3).map((rec, idx) => (
                <div 
                  key={idx} 
                  style={{ 
                    fontSize: 12, 
                    marginBottom: 4,
                    cursor: 'pointer',
                    color: theme.colors.textPrimary
                  }}
                  onClick={() => onSuggestCommand && onSuggestCommand(typeof rec === 'string' ? rec : rec.text)}
                >
                  • {typeof rec === 'string' ? rec : rec.text || rec.suggestion}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        {message.metadata && !isUser && (
          <div style={{
            marginTop: 8,
            paddingTop: 8,
            borderTop: '1px solid ' + theme.colors.border,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{ fontSize: 10, color: theme.colors.textSecondary }}>
              {message.metadata.processing_type && (
                <Space>
                  {message.metadata.processing_type.includes('chart') && <BarChartOutlined />}
                  {message.metadata.processing_type.includes('dimension') && <FilterOutlined />}
                  {message.metadata.processing_type.includes('basic') && <ThunderboltOutlined />}
                  <Text>{message.metadata.processing_type}</Text>
                </Space>
              )}
              {message.metadata.execution_time && (
                <Text style={{ marginLeft: 8 }}>⚡ {message.metadata.execution_time}ms</Text>
              )}
            </div>

            {message.metadata.confidence && (
              <Progress
                percent={Math.round(message.metadata.confidence * 100)}
                size="small"
                strokeColor={message.metadata.confidence > 0.7 ? theme.colors.success : theme.colors.warning}
                showInfo={false}
                style={{ width: 50 }}
              />
            )}
          </div>
        )}

        <div style={{ 
          fontSize: 10, 
          color: isUser ? 'rgba(255,255,255,0.7)' : theme.colors.textSecondary,
          marginTop: 8,
          textAlign: isUser ? 'right' : 'left'
        }}>
          {message.timestamp?.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>

      {isUser && (
        <Avatar 
          icon={<UserOutlined />} 
          style={{ 
            backgroundColor: theme.colors.bmGreenDark,
            flexShrink: 0
          }} 
        />
      )}
    </div>
  );
});

ConversationMessage.propTypes = {
  message: PropTypes.object.isRequired,
  onSuggestCommand: PropTypes.func
};

// ============================================================================
// 🚀 COMPONENTE PRINCIPAL CONVERSATIONAL PIVOT v4.1
// ============================================================================

const ConversationalPivot = ({ 
  userId = 'frontend_user',
  gestorId = null,
  periodo = null,
  initialData = [],
  initialKpis = ['ROE', 'MARGEN_NETO', 'INGRESOS'],
  onChartUpdate,
  onChartGenerated,
  enableAdvancedFeatures = true,
  executiveMode = false,
  height = '700px',
  showHeader = true
}) => {
  // ============================================================================
  // ✅ FIX: TODOS LOS HOOKS AL INICIO - ORDEN CORRECTO
  // ============================================================================

  // States principales
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  
  // UI States
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [autoSuggestions, setAutoSuggestions] = useState(true);
  const [smartMode, setSmartMode] = useState(true);
  
  // Command history
  const [commandHistory, setCommandHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Chart configuration
  const [chartConfig, setChartConfig] = useState({
    chartType: 'bar',
    selectedKpi: initialKpis[0] || 'ROE',
    dimension: 'gestor',
    data: initialData || [],
    availableKpis: initialKpis || [],
    period: periodo,
    interactive: true,
    pivot_enabled: true,
    id: `chart_${Date.now()}`,
    title: 'Gráfico Conversacional v4.1',
    created_at: new Date().toISOString(),
    force_update: Date.now()
  });

  // ✅ FIX: useApp hook
  const { notification } = App.useApp();

  // Referencias
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const interactiveChartsRef = useRef(null);
  const containerRef = useRef(null);

  // ============================================================================
  // ✅ FIX: CHATSERVICE INTEGRATION MEJORADA v4.1
  // ============================================================================

  const {
    sendMessage,
    fetchDimensionData,
    connectionState,
    currentChartConfig,
    serviceMetrics,
    setUserId,
    updatePreferences,
    clearCache
  } = useChatService({
    autoConnect: enableAdvancedFeatures, // Solo conectar si features avanzadas están habilitadas
    userId,
    handlers: {
      onMessage: useCallback((data) => {
        console.log('📨 [ConversationalPivot v4.1] WebSocket message received:', data);
        if (data?.response) {
          addAgentMessage(data.response, data.charts || [], data.recommendations || [], {
            processing_type: 'websocket_message_v4.1',
            confidence: data.confidence_score || 0.8
          });
        }
      }, []),
      onError: useCallback((error) => {
        console.error('❌ [ConversationalPivot v4.1] Chat service error:', error);
        // ✅ FIX: Error handling silencioso para evitar spam
        if (!error?.message?.includes('No send method available')) {
          notification.warning({
            message: 'ChatService v4.1 Advertencia',
            description: 'Funcionalidad limitada - verificar conexión',
            duration: 3
          });
        }
      }, [notification]),
      onChartUpdate: useCallback((charts) => {
        console.log('📊 [ConversationalPivot v4.1] Chart update received:', charts);
        if (charts && charts.length > 0) {
          const latestChart = charts[charts.length - 1];
          updateChartConfiguration(latestChart);
        }
      }, []),
      onPivotSuggestion: useCallback((suggestions) => {
        console.log('💡 [ConversationalPivot v4.1] Pivot suggestions received:', suggestions);
        if (suggestions && suggestions.length > 0) {
          addAgentMessage(`💡 **Sugerencias de pivoteo:**\n\n${suggestions.slice(0, 3).map(s => `• ${s}`).join('\n')}`, [], suggestions);
        }
      }, []),
      onQuickResponse: useCallback((response) => {
        console.log('⚡ [ConversationalPivot v4.1] Quick response:', response);
      }, [])
    }
  });

  // ============================================================================
  // ✅ FIX: FUNCIONES INTELIGENTES v4.1 - USANDO useCallback
  // ============================================================================

  const addMessage = useCallback((sender, text, charts = [], recommendations = [], metadata = {}) => {
    const newMessage = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      sender,
      text,
      charts,
      recommendations: recommendations.slice(0, 3),
      metadata: {
        ...metadata,
        version: '4.1',
        timestamp: new Date().toISOString()
      },
      timestamp: new Date()
    };
    
    setMessages(prev => {
      // ✅ FIX: Evitar mensajes duplicados
      const isDuplicate = prev.some(msg => 
        msg.text === text && 
        msg.sender === sender && 
        (Date.now() - new Date(msg.timestamp).getTime()) < 2000
      );
      
      if (isDuplicate) return prev;
      
      const newMessages = [...prev, newMessage];
      return newMessages.length > 50 ? newMessages.slice(-50) : newMessages;
    });

    // ✅ FIX: Auto-scroll mejorado
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  }, []);

  const addUserMessage = useCallback((text) => {
    addMessage('user', text);
  }, [addMessage]);

  const addAgentMessage = useCallback((text, charts = [], recommendations = [], metadata = {}) => {
    addMessage('agent', text, charts, recommendations, metadata);
  }, [addMessage]);

  // ✅ FIX: Parse chart commands mejorado
  const parseChartCommands = useCallback((text) => {
    if (!text || typeof text !== 'string') return { hasChanges: false };
    
    const textLower = text.toLowerCase();
    let updates = {};
    let hasChanges = false;
    let suggestions = [];

    // Detect chart type
    for (const [type, keywords] of Object.entries(CHART_COMMANDS.TYPES)) {
      if (keywords.some(keyword => textLower.includes(keyword))) {
        if (type !== chartConfig.chartType) {
          updates.chartType = type;
          hasChanges = true;
          suggestions.push(`Cambiando a gráfico ${type === 'bar' ? 'de barras' : type === 'line' ? 'de líneas' : type === 'pie' ? 'circular' : 'de área'}`);
        }
        break;
      }
    }

    // Detect KPI
    for (const [kpi, keywords] of Object.entries(CHART_COMMANDS.KPIS)) {
      if (keywords.some(keyword => textLower.includes(keyword))) {
        if (chartConfig.availableKpis.includes(kpi) && kpi !== chartConfig.selectedKpi) {
          updates.selectedKpi = kpi;
          hasChanges = true;
          suggestions.push(`Mostrando ${kpi.replace('_', ' ').toLowerCase()}`);
        }
        break;
      }
    }

    // Detect dimension
    for (const [dimension, keywords] of Object.entries(CHART_COMMANDS.DIMENSIONS)) {
      if (keywords.some(keyword => textLower.includes(`por ${keyword}`) || textLower.includes(`de ${keyword}`))) {
        if (dimension !== chartConfig.dimension) {
          updates.dimension = dimension;
          hasChanges = true;
          suggestions.push(`Agrupando por ${dimension}`);
        }
        break;
      }
    }

    // Detect special commands
    const specialCommands = {
      'limpiar': ['limpiar', 'borrar', 'clear', 'reset'],
      'ayuda': ['ayuda', 'help', 'comandos', '?'],
      'fullscreen': ['pantalla completa', 'fullscreen', 'maximizar'],
      'actualizar': ['actualizar', 'refresh', 'reload']
    };

    for (const [command, keywords] of Object.entries(specialCommands)) {
      if (keywords.some(keyword => textLower.includes(keyword))) {
        updates.specialCommand = command;
        hasChanges = true;
        break;
      }
    }

    return { 
      ...updates, 
      hasChanges, 
      suggestions,
      confidence: hasChanges ? 0.9 : 0.3
    };
  }, [chartConfig]);

  // ✅ FIX: Update chart configuration mejorado
  const updateChartConfiguration = useCallback((updates) => {
    const newConfig = { 
      ...chartConfig, 
      ...updates,
      force_update: Date.now(),
      updated_at: new Date().toISOString()
    };
    
    setChartConfig(newConfig);
    
    // Update InteractiveCharts component
    if (interactiveChartsRef.current && typeof interactiveChartsRef.current.updateChart === 'function') {
      setTimeout(() => {
        interactiveChartsRef.current.updateChart(newConfig);
      }, 100);
    }
    
    // Notify parent
    if (onChartUpdate) {
      setTimeout(() => onChartUpdate(newConfig), 100);
    }
    
    return newConfig;
  }, [chartConfig, onChartUpdate]);

  // ✅ FIX: Execute special commands mejorado
  const executeSpecialCommand = useCallback(async (command) => {
    switch (command) {
      case 'limpiar':
        setMessages([]);
        addAgentMessage('🧹 Conversación limpiada v4.1. ¿En qué puedo ayudarte?');
        break;
        
      case 'ayuda':
        addAgentMessage(`📚 **Comandos disponibles v4.1:**

**Tipos de gráfico:**
• "Cambia a gráfico circular/de barras/de líneas/de área"

**KPIs disponibles:**
• ${chartConfig.availableKpis.map(kpi => `"${kpi.replace('_', ' ')}"`).join(', ')}

**Dimensiones:**
• "Mostrar por centro/gestor/cliente/producto/segmento"

**Comandos especiales:**
• "Ayuda" - Mostrar esta ayuda
• "Limpiar" - Borrar conversación
• "Pantalla completa" - Maximizar vista
• "Actualizar" - Refrescar datos

**Estado:** ${connectionState} v4.1 | **Charts:** ${chartConfig.availableKpis.length} KPIs

¡Combina comandos para mejores resultados!`);
        break;
        
      case 'fullscreen':
        setIsFullscreen(!isFullscreen);
        addAgentMessage(`📺 ${!isFullscreen ? 'Activando' : 'Desactivando'} modo pantalla completa v4.1`);
        break;
        
      case 'actualizar':
        addAgentMessage('🔄 Actualizando datos v4.1...');
        try {
          clearCache();
          updateChartConfiguration({ force_update: Date.now() });
          addAgentMessage('✅ Datos actualizados correctamente v4.1');
        } catch (error) {
          addAgentMessage('⚠️ Error actualizando datos v4.1');
        }
        break;
        
      default:
        break;
    }
  }, [isFullscreen, addAgentMessage, chartConfig.availableKpis, clearCache, updateChartConfiguration, connectionState]);

  // ============================================================================
  // ✅ FIX: FUNCIÓN PRINCIPAL DE ENVÍO v4.1 - CORREGIDA
  // ============================================================================

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isSending) return;

    const userMessage = inputValue.trim();
    
    // ✅ FIX: Add to command history
    setCommandHistory(prev => {
      const newHistory = [userMessage, ...prev.filter(cmd => cmd !== userMessage)];
      return newHistory.slice(0, 20);
    });
    setHistoryIndex(-1);
    
    // Clear input and add user message
    setInputValue('');
    setIsSending(true);
    addUserMessage(userMessage);

    try {
      // ✅ FIX: Parse commands locally first
      const parseResult = parseChartCommands(userMessage);
      const { hasChanges, specialCommand, suggestions, confidence, ...chartUpdates } = parseResult;
      
      console.log('🎯 [ConversationalPivot v4.1] Command analysis:', { hasChanges, specialCommand, confidence });

      // Execute special commands
      if (specialCommand) {
        await executeSpecialCommand(specialCommand);
        setIsSending(false);
        return;
      }
      
      // ✅ FIX: Apply local chart changes
      if (hasChanges && Object.keys(chartUpdates).length > 0) {
        const newConfig = updateChartConfiguration(chartUpdates);
        
        const changesList = [];
        if (chartUpdates.chartType) changesList.push(`Tipo: ${chartUpdates.chartType.toUpperCase()}`);
        if (chartUpdates.selectedKpi) changesList.push(`KPI: ${chartUpdates.selectedKpi.replace('_', ' ')}`);
        if (chartUpdates.dimension) changesList.push(`Dimensión: ${chartUpdates.dimension}`);
        
        const responseText = `✅ **Gráfico actualizado exitosamente v4.1**

${changesList.join('\n')}

${suggestions.length > 0 ? `\n🎯 **Cambios aplicados:**\n${suggestions.map(s => `• ${s}`).join('\n')}` : ''}

📊 **Estado actual:**
• Tipo: ${newConfig.chartType?.toUpperCase()}
• KPI: ${newConfig.selectedKpi?.replace('_', ' ')}
• Dimensión: ${newConfig.dimension}
• Elementos: ${newConfig.data?.length || 0}`;

        addAgentMessage(responseText, [], autoSuggestions ? [
          'Cambiar tipo de visualización',
          'Seleccionar otro KPI',
          'Modificar agrupación'
        ] : [], {
          confidence,
          processing_type: 'local_chart_update_v4.1',
          changes_applied: changesList.length,
          chart_interaction: true
        });

        // ✅ FIX: Try remote chart interaction if connected
        if (connectionState === CONNECTION_STATES.OPEN && sendMessage) {
          try {
            const response = await sendMessage(userMessage, {
              current_chart_config: newConfig,
              chart_interaction_type: 'pivot',
              gestorId,
              periodo,
              includeCharts: true,
              version: '4.1'
            });
            
            if (response?.pivot_suggestions?.length > 0) {
              setTimeout(() => {
                addAgentMessage(`💡 **Sugerencias adicionales del sistema v4.1:**\n\n${response.pivot_suggestions.slice(0, 3).map(s => `• ${s}`).join('\n')}`, [], response.pivot_suggestions.slice(0, 3), {
                  processing_type: 'remote_suggestions_v4.1'
                });
              }, 1000);
            }
          } catch (error) {
            console.warn('⚠️ [ConversationalPivot v4.1] Error in remote chart interaction:', error);
          }
        }

      } else {
        // ✅ FIX: Send to ChatService for full processing
        if (connectionState === CONNECTION_STATES.OPEN && sendMessage) {
          try {
            console.log('📤 [ConversationalPivot v4.1] Sending message to ChatService');
            const response = await sendMessage(userMessage, {
              gestorId,
              periodo,
              includeCharts: enableAdvancedFeatures,
              includeRecommendations: enableAdvancedFeatures,
              context: {
                current_chart_config: chartConfig,
                chart_interaction_type: 'general',
                mode: executiveMode ? 'executive' : 'standard',
                version: '4.1'
              }
            });
            
            if (response?.response) {
              addAgentMessage(response.response, response.charts || [], response.recommendations || [], {
                processing_type: 'full_chatservice_v4.1',
                execution_time: response.serviceMetadata?.processingTime,
                confidence: response.confidence_score || 0.8
              });
              
              // Update chart if new configurations
              if (response.chart_configs?.length > 0) {
                setTimeout(() => {
                  updateChartConfiguration(response.chart_configs[0]);
                }, 500);
              }
              
              // Notify chart generated
              if (onChartGenerated && (response.charts?.length > 0 || response.chart_configs?.length > 0)) {
                onChartGenerated(response);
              }
            }
          } catch (error) {
            console.error('❌ [ConversationalPivot v4.1] Error in ChatService:', error);
            addAgentMessage(`🤔 **No pude procesar completamente tu comando v4.1**

**Ejemplos de comandos válidos:**
• "Cambia a gráfico circular"
• "Muestra ROE por centro"
• "Cambiar a líneas de tendencia"
• "Ver eficiencia por gestor"

**Estado actual:**
• Gráfico: ${chartConfig.chartType} - ${chartConfig.selectedKpi} por ${chartConfig.dimension}
• Conexión: ${connectionState}

¿Podrías ser más específico?`, [], autoSuggestions ? SUGGESTION_COMMANDS.slice(0, 4) : [], {
              processing_type: 'fallback_v4.1'
            });
          }
        } else {
          // ✅ FIX: Fallback para modo offline
          addAgentMessage(`🟡 **Modo Local v4.1 Activo**

ChatService no está disponible, pero puedes usar comandos básicos:

**Comandos disponibles:**
• "Cambia a gráfico [circular/barras/líneas]"
• "Ayuda" - Ver todos los comandos
• "Limpiar" - Borrar conversación

**Estado:** ${connectionState}`, [], ['Ayuda', 'Limpiar'], {
            processing_type: 'offline_mode_v4.1'
          });
        }
      }

    } catch (error) {
      console.error('❌ [ConversationalPivot v4.1] Error processing command:', error);
      addAgentMessage(`❌ **Error procesando el comando v4.1**

Ocurrió un problema técnico. 

**Soluciones sugeridas:**
• Intenta reformular tu solicitud
• Usa comandos más simples como "ayuda"
• Verifica tu conexión

¿Quieres intentar de nuevo?`, [], ['Ayuda', 'Limpiar conversación'], {
        processing_type: 'error_v4.1'
      });
    } finally {
      setIsSending(false);
    }
  }, [
    inputValue, isSending, parseChartCommands, executeSpecialCommand, updateChartConfiguration,
    autoSuggestions, chartConfig, connectionState, sendMessage, gestorId, periodo, 
    enableAdvancedFeatures, executiveMode, onChartGenerated, addUserMessage, addAgentMessage
  ]);

  // ============================================================================
  // ✅ FIX: HANDLERS Y EVENTOS v4.1
  // ============================================================================

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSending && inputValue.trim()) {
        handleSendMessage();
      }
    } else if (e.key === 'ArrowUp' && commandHistory.length > 0) {
      e.preventDefault();
      const newIndex = Math.min(historyIndex + 1, commandHistory.length - 1);
      setHistoryIndex(newIndex);
      setInputValue(commandHistory[newIndex]);
    } else if (e.key === 'ArrowDown' && historyIndex >= 0) {
      e.preventDefault();
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setInputValue(newIndex >= 0 ? commandHistory[newIndex] : '');
    }
  }, [handleSendMessage, isSending, inputValue, commandHistory, historyIndex]);

  const handleSuggestCommand = useCallback((command) => {
    setInputValue(command);
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  }, []);

  const clearConversation = useCallback(() => {
    setMessages([]);
    addAgentMessage('🧹 Conversación limpiada v4.1. ¿En qué puedo ayudarte ahora?');
  }, [addAgentMessage]);

  // ============================================================================
  // ✅ FIX: EFFECTS v4.1
  // ============================================================================

  // Set user ID
  useEffect(() => {
    if (userId && setUserId) {
      setUserId(userId);
    }
  }, [userId, setUserId]);

  // ✅ FIX: Initial welcome message - solo una vez
  useEffect(() => {
    const timer = setTimeout(() => {
      const welcomeMessage = executiveMode 
        ? `🎯 **Panel Ejecutivo de Visualización v4.1**

Bienvenido al sistema avanzado de análisis conversacional.

**Configuración actual:**
• Tipo: ${chartConfig.chartType.toUpperCase()}
• KPI: ${chartConfig.selectedKpi.replace('_', ' ')}
• Dimensión: ${chartConfig.dimension}
• Elementos: ${chartConfig.data?.length || 0}

**ChatService v4.1:** ${connectionState === CONNECTION_STATES.OPEN ? '🟢 Online' : '🟡 Local'}

¿Qué análisis ejecutivo te gustaría realizar?`
        : `🎨 **Asistente de Visualización Inteligente v4.1**

¡Hola! Soy tu asistente para modificar gráficos mediante conversación natural.

**Estado actual:**
• Gráfico: ${chartConfig.chartType} - ${chartConfig.selectedKpi} por ${chartConfig.dimension}
• Conexión: ${connectionState === CONNECTION_STATES.OPEN ? '🟢 ChatService Online' : '🟡 Modo Local'}

**Ejemplos de comandos:**
• "Cambia a gráfico circular"
• "Muestra ROE por centro"
• "Cambiar a líneas de tendencia"

¿Qué modificación te gustaría hacer?`;

      addAgentMessage(welcomeMessage, [], autoSuggestions ? SUGGESTION_COMMANDS.slice(0, 4) : [], {
        processing_type: 'welcome_v4.1',
        version: '4.1'
      });
    }, 800);

    return () => clearTimeout(timer);
  }, []); // Solo ejecutar una vez al montar

  // ============================================================================
  // 🎨 ESTILOS MEMOIZADOS
  // ============================================================================

  const containerStyle = useMemo(() => ({
    height: isFullscreen ? '100vh' : height,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: theme.colors.background,
    borderRadius: isFullscreen ? 0 : 8,
    boxShadow: isFullscreen ? 'none' : '0 4px 16px rgba(0,0,0,0.1)',
    border: isFullscreen ? 'none' : '1px solid ' + theme.colors.border,
    overflow: 'hidden',
    position: isFullscreen ? 'fixed' : 'relative',
    top: isFullscreen ? 0 : 'auto',
    left: isFullscreen ? 0 : 'auto',
    right: isFullscreen ? 0 : 'auto',
    bottom: isFullscreen ? 0 : 'auto',
    zIndex: isFullscreen ? 1000 : 'auto'
  }), [isFullscreen, height]);

  const isConnected = connectionState === CONNECTION_STATES.OPEN;

  // ============================================================================
  // 🎨 RENDERIZADO PRINCIPAL v4.1
  // ============================================================================

  return (
    <div ref={containerRef} style={containerStyle}>
      
      {/* ✅ FIX: Header mejorado */}
      {showHeader && (
        <Card size="small" style={{ border: 'none', borderBottom: '1px solid ' + theme.colors.border }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space>
                <Avatar 
                  icon={<RobotOutlined />} 
                  style={{ backgroundColor: theme.colors.bmGreenLight }}
                />
                <div>
                  <Title level={5} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
                    {executiveMode ? 'Panel Ejecutivo Visual v4.1' : 'Pivot Conversacional v4.1'}
                  </Title>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    ChatService v4.1 • {chartConfig.data?.length || 0} elementos • {isConnected ? '🟢 Online' : '🟡 Local'}
                  </Text>
                </div>
              </Space>
            </Col>
            
            <Col>
              <Space>
                <Tooltip title="Configuración">
                  <Button 
                    size="small" 
                    icon={<SettingOutlined />}
                    onClick={() => setShowSettings(!showSettings)}
                  />
                </Tooltip>
                
                <Tooltip title={isFullscreen ? "Salir pantalla completa" : "Pantalla completa"}>
                  <Button 
                    size="small" 
                    icon={isFullscreen ? <CompressOutlined /> : <FullscreenOutlined />}
                    onClick={() => setIsFullscreen(!isFullscreen)}
                  />
                </Tooltip>
                
                <Tooltip title="Limpiar conversación">
                  <Button 
                    size="small" 
                    icon={<ClearOutlined />}
                    onClick={clearConversation}
                    disabled={messages.length === 0}
                  />
                </Tooltip>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* ✅ FIX: Settings panel mejorado */}
      {showSettings && (
        <Card size="small" style={{ border: 'none', borderBottom: '1px solid ' + theme.colors.border }}>
          <Collapse ghost size="small">
            <Panel header="Configuración Avanzada v4.1" key="settings">
              <Row gutter={[16, 8]} align="middle">
                <Col span={8}>
                  <Space>
                    <Text style={{ fontSize: 12 }}>Auto-sugerencias:</Text>
                    <Switch 
                      size="small" 
                      checked={autoSuggestions} 
                      onChange={setAutoSuggestions} 
                    />
                  </Space>
                </Col>
                <Col span={8}>
                  <Space>
                    <Text style={{ fontSize: 12 }}>Modo inteligente:</Text>
                    <Switch 
                      size="small" 
                      checked={smartMode} 
                      onChange={setSmartMode} 
                    />
                  </Space>
                </Col>
                <Col span={8}>
                  <Space>
                    <Text style={{ fontSize: 12 }}>KPI:</Text>
                    <Select 
                      size="small" 
                      value={chartConfig.selectedKpi} 
                      onChange={(value) => updateChartConfiguration({ selectedKpi: value })}
                      style={{ width: 120 }}
                    >
                      {chartConfig.availableKpis.map(kpi => (
                        <Option key={kpi} value={kpi}>
                          {kpi.replace('_', ' ')}
                        </Option>
                      ))}
                    </Select>
                  </Space>
                </Col>
              </Row>
            </Panel>
          </Collapse>
        </Card>
      )}

      {/* ✅ FIX: Layout mejorado: Chat + Chart */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        overflow: 'hidden',
        flexDirection: isFullscreen ? 'row' : 'column'
      }}>
        
        {/* Chat Area */}
        <div style={{
          flex: isFullscreen ? '0 0 400px' : '0 0 300px',
          display: 'flex',
          flexDirection: 'column',
          borderRight: isFullscreen ? '1px solid ' + theme.colors.border : 'none',
          borderBottom: isFullscreen ? 'none' : '1px solid ' + theme.colors.border
        }}>
          
          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: 16,
            backgroundColor: theme.colors.backgroundLight
          }}>
            {messages.length === 0 ? (
              <Empty 
                image={<RobotOutlined style={{ fontSize: 48, color: theme.colors.bmGreenLight }} />}
                description={
                  <span>
                    <Text strong>ChatService v4.1 listo</Text><br />
                    <Text type="secondary">Escribe un comando para comenzar</Text>
                  </span>
                }
              />
            ) : (
              <>
                {messages.map((message, index) => (
                  <ConversationMessage 
                    key={message.id}
                    message={message}
                    onSuggestCommand={handleSuggestCommand}
                  />
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* ✅ FIX: Suggestions bar mejorado */}
          <div style={{
            padding: '8px 16px',
            borderTop: '1px solid ' + theme.colors.border,
            backgroundColor: theme.colors.background
          }}>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {SUGGESTION_COMMANDS.slice(0, 6).map(cmd => (
                <Button 
                  key={cmd}
                  size="small" 
                  type="text"
                  onClick={() => handleSuggestCommand(cmd)}
                  style={{ 
                    fontSize: 10, 
                    height: 'auto', 
                    padding: '2px 6px',
                    border: '1px solid ' + theme.colors.border,
                    borderRadius: 4,
                    backgroundColor: theme.colors.backgroundLight
                  }}
                >
                  {cmd}
                </Button>
              ))}
            </div>
          </div>

          {/* ✅ FIX: Input area mejorado */}
          <div style={{
            padding: 16,
            backgroundColor: theme.colors.background
          }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
              <TextArea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Escribe tu comando: 'Cambia a gráfico circular', 'Muestra ROE por centro'..."
                rows={2}
                disabled={isSending}
                maxLength={500}
                showCount
                style={{
                  borderRadius: 6,
                  fontSize: 13
                }}
              />

              <Button
                type="primary"
                icon={isSending ? <SyncOutlined spin /> : <SendOutlined />}
                onClick={handleSendMessage}
                disabled={isSending || !inputValue.trim()}
                size="large"
                style={{
                  height: 48,
                  width: 48,
                  borderRadius: 6,
                  backgroundColor: isConnected && inputValue.trim() ? theme.colors.bmGreenPrimary : theme.colors.textSecondary
                }}
              />
            </div>

            {/* ✅ FIX: Status bar mejorado */}
            <div style={{
              marginTop: 8,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ fontSize: 10, color: theme.colors.textSecondary }}>
                {isConnected ? '🟢 ChatService v4.1 Online' : '🟡 Modo Local v4.1'}
              </div>
              {commandHistory.length > 0 && (
                <div style={{ fontSize: 10, color: theme.colors.textSecondary }}>
                  ↑↓ historial ({commandHistory.length})
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ✅ FIX: Chart Area mejorado */}
        <div style={{ 
          flex: 1, 
          backgroundColor: '#fff',
          overflow: 'hidden'
        }}>
          <InteractiveCharts
            ref={interactiveChartsRef}
            data={chartConfig.data}
            availableKpis={chartConfig.availableKpis}
            title="Vista Conversacional v4.1"
            description={`${chartConfig.chartType.toUpperCase()} - ${chartConfig.selectedKpi.replace('_', ' ')} por ${chartConfig.dimension}`}
            currentConfig={chartConfig}
            chartId={chartConfig.id}
            onChartChange={(config) => updateChartConfiguration(config)}
            enableInteraction={true}
            conversationalMode={true}
            executiveMode={executiveMode}
            version="4.1"
            key={`chart-${chartConfig.force_update}`}
          />
        </div>
      </div>

      {/* ✅ FIX: Status footer mejorado */}
      <div style={{
        padding: '8px 16px',
        borderTop: '1px solid ' + theme.colors.border,
        backgroundColor: theme.colors.background,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <Space split={<Divider type="vertical" />}>
            <Space>
              {chartConfig.chartType === 'bar' && <BarChartOutlined />}
              {chartConfig.chartType === 'line' && <LineChartOutlined />}
              {chartConfig.chartType === 'pie' && <PieChartOutlined />}
              {chartConfig.chartType === 'area' && <AreaChartOutlined />}
              <Text style={{ fontSize: 11 }}>
                <strong>{chartConfig.chartType?.toUpperCase()}</strong>
              </Text>
            </Space>
            <Text style={{ fontSize: 11 }}>
              KPI: <strong>{chartConfig.selectedKpi?.replace('_', ' ')}</strong>
            </Text>
            <Text style={{ fontSize: 11 }}>
              Por: <strong>{chartConfig.dimension}</strong>
            </Text>
          </Space>
        </div>

        <div>
          <Space>
            <Badge 
              status={isConnected ? 'success' : 'warning'} 
              text={
                <span style={{ fontSize: 10 }}>
                  {isConnected ? 'v4.1 Online' : 'v4.1 Local'}
                </span>
              }
            />
            <Text style={{ fontSize: 10, color: theme.colors.textSecondary }}>
              {messages.length} msgs
            </Text>
          </Space>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// 🏷️ PROPTYPES
// ============================================================================

ConversationalPivot.propTypes = {
  userId: PropTypes.string,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  initialData: PropTypes.array,
  initialKpis: PropTypes.array,
  onChartUpdate: PropTypes.func,
  onChartGenerated: PropTypes.func,
  enableAdvancedFeatures: PropTypes.bool,
  executiveMode: PropTypes.bool,
  height: PropTypes.string,
  showHeader: PropTypes.bool
};

export default ConversationalPivot;
