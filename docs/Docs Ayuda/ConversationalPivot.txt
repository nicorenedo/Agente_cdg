// frontend/src/components/Dashboard/ConversationalPivot.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Typography, 
  Space, 
  Alert,
  Avatar,
  Spin,
  notification,
  Tag,
  Empty,
  Tooltip,
  Badge,
  Dropdown
} from 'antd';
import { 
  SendOutlined, 
  RobotOutlined, 
  UserOutlined, 
  MessageOutlined,
  LoadingOutlined,
  ThunderboltOutlined,
  ClearOutlined,
  ExperimentOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
  BulbOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import analyticsService from '../../services/analyticsService';
import theme from '../../styles/theme';

const { TextArea } = Input;
const { Text } = Typography;

/**
 * ✅ ConversationalPivot v11.1 - Perfect Integration FIXED
 * 
 * CORRECCIONES v11.1:
 * 1. ✅ UserIds únicos para evitar colisiones con ChatInterface
 * 2. ✅ Detección automática de conflictos WebSocket 
 * 3. ✅ Fallback automático a HTTP-only cuando hay múltiples componentes
 * 4. ✅ Layout completamente responsivo
 * 5. ✅ Mejor gestión de errores y reconexiones
 */
const ConversationalPivot = ({
  mode = 'direccion',
  gestorId = null,
  periodo = null,
  currentChartConfig = null,
  onChartUpdate = () => {},
  className = '',
  style = {}
}) => {
  
  // ✅ ESTADOS PRINCIPALES MEJORADOS
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isHttpOnlyMode, setIsHttpOnlyMode] = useState(false);
  const [aiMode, setAiMode] = useState('chat'); // 'chat' | 'pivot' | 'analysis'
  const [lastPivotSuccess, setLastPivotSuccess] = useState(false);
  const [availableQueries, setAvailableQueries] = useState([]);
  const [integrationStatus, setIntegrationStatus] = useState('idle'); // 'idle' | 'processing' | 'success' | 'error'

  // ✅ USER ID ÚNICO POR MODO - FIXED COLLISION
  const userId = React.useMemo(() => {
    const baseUserId = gestorId ? String(gestorId) : 'anonymous';
    const timestamp = Date.now().toString(36).slice(-4);
    const random = Math.random().toString(36).slice(-4);
    return mode === 'direccion' 
      ? `pivot-direction-${baseUserId}-${timestamp}${random}` 
      : `pivot-gestor-${baseUserId}-${timestamp}${random}`;
  }, [mode, gestorId]);

  const chatSessionRef = useRef(null);
  const messagesEndRef = useRef(null);
  const pivotControllerRef = useRef(null);

  // ✅ SCROLL AUTOMÁTICO
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // ✅ CARGAR CONFIGURACIÓN INICIAL
  useEffect(() => {
    const loadInitialConfig = async () => {
      try {
        // ✅ Cargar queries disponibles
        const queries = await analyticsService.getAvailableQuickQueries();
        setAvailableQueries(queries || []);

        // ✅ Verificar estado de integración
        const coordination = await chatService.http.agentCoordination();
        console.log('[ConversationalPivot] ✅ Agent coordination status:', coordination);
        
      } catch (error) {
        console.warn('[ConversationalPivot] Error loading initial config:', error.message);
      }
    };

    loadInitialConfig();
  }, []);

  // ✅ INICIALIZAR CHAT SESSION CON PERFECT INTEGRATION - CONFLICT DETECTION
  useEffect(() => {
    console.log(`[ConversationalPivot] 🚀 Initializing Perfect Integration for userId: ${userId}`);
    
    // ✅ NUEVO: Verificar si ya hay conexiones activas para evitar conflictos
    const checkActiveConnections = () => {
      // Buscar conexiones WebSocket activas en la página
      const existingConnections = document.querySelectorAll('[class*="conversational-pivot"], [class*="chat-interface"]');
      console.log(`[ConversationalPivot] 🔍 Found ${existingConnections.length} chat components`);
      
      return existingConnections.length > 1; // Si hay más de uno, hay potencial conflicto
    };
    
    const hasConflict = checkActiveConnections();
    
    if (hasConflict) {
      console.log(`[ConversationalPivot] ⚠️ Multiple chat components detected, using HTTP-only mode`);
      
      setIsHttpOnlyMode(true);
      setIsConnected(true); // Marcar como "conectado" aunque sea HTTP-only
      
      // Mostrar mensaje de modo HTTP-only
      const conflictMsg = {
        id: Date.now(),
        sender: 'assistant',
        text: `🔄 **Modo HTTP-Only activado**

Detectadas múltiples interfaces de chat.
Usando comunicación HTTP para evitar conflictos.

✅ **Funcionalidad completa disponible:**
• Perfect Integration v11.1 mediante HTTP
• Modificación de gráficos en tiempo real
• Chat Agent v10.0 + CDG Agent v6.0
• Análisis complejos especializados

**Comandos disponibles:**
• "Cambia a barras horizontales"
• "Muestra por centros"
• "Convierte a circular"
• "Métrica MARGEN"

¡Todo funciona igual de bien!`,
        timestamp: new Date().toLocaleTimeString(),
        isWelcome: true,
        aiMode: 'http-only'
      };
      setMessages([conflictMsg]);
      setIntegrationStatus('success');
      return;
    }
    
    // Crear sesión de chat con Chat Agent v10.0
    chatSessionRef.current = chatService.createChatSession(userId, {
      onOpen: () => {
        console.log('[ConversationalPivot] ✅ Chat Agent v10.0 connected');
        setIsConnected(true);
        
        // ✅ Mensaje de bienvenida mejorado y más compacto
        const welcomeMsg = {
          id: Date.now(),
          sender: 'assistant',
          text: `🤖 **Perfect Integration v11.1**
¡Hola! Modifica gráficos con lenguaje natural.

**Ejemplos rápidos:**
• "Cambia a barras horizontales"
• "Muestra por centros"
• "Convierte a circular"
• "Métrica MARGEN"

Solo modifico el gráfico de análisis general.`,
          timestamp: new Date().toLocaleTimeString(),
          isWelcome: true,
          aiMode: 'welcome'
        };
        setMessages([welcomeMsg]);
      },

      onClose: (event) => {
        console.log('[ConversationalPivot] ❌ WebSocket disconnected:', event?.code);
        setIsConnected(false);
        
        // ✅ NUEVA LÓGICA: Si hay códigos de conflicto, cambiar a HTTP-only
        if (event?.code === 1005 || event?.code === 1012 || event?.code === 1000) {
          console.log('[ConversationalPivot] 🔄 Conflict detected, switching to HTTP-only');
          setIsHttpOnlyMode(true);
          setIsConnected(true);
          
          const httpFallbackMsg = {
            id: Date.now(),
            sender: 'assistant',
            text: `🔄 **Cambiado a modo HTTP-Only**

WebSocket cerrado (código: ${event?.code || 'unknown'})
Continuando con Perfect Integration via HTTP.

✅ Funcionalidad completa mantenida
¡Sigue funcionando perfectamente!`,
            timestamp: new Date().toLocaleTimeString(),
            aiMode: 'http-fallback'
          };
          setMessages(prev => [...prev, httpFallbackMsg]);
        }
      },

      onError: (error) => {
        console.error('[ConversationalPivot] WebSocket error:', error);
        setIsConnected(false);
        setIntegrationStatus('error');
        
        // ✅ NUEVA LÓGICA: Después de múltiples errores, cambiar a HTTP-only
        setTimeout(() => {
          console.log('[ConversationalPivot] 🔄 After error, switching to HTTP-only');
          setIsHttpOnlyMode(true);
          setIsConnected(true);
          setIntegrationStatus('success');
        }, 2000);
      },

      // ✅ NUEVO: Handler mejorado para integration events
      onMessage: (wsMessage) => {
        console.log('[ConversationalPivot] 📨 Received message:', wsMessage);
        
        if (wsMessage.text) {
          const assistantMessage = {
            id: Date.now(),
            sender: 'assistant',
            text: wsMessage.text,
            timestamp: new Date().toLocaleTimeString(),
            source: 'websocket',
            aiMode: wsMessage.responseType || 'chat'
          };
          setMessages(prev => [...prev, assistantMessage]);
        }

        // ✅ PERFECT INTEGRATION: Procesar charts usando InteractiveCharts
        if (wsMessage.charts && wsMessage.charts.length > 0) {
          handleChartsFromWebSocket(wsMessage.charts);
        }
      },

      // ✅ NUEVOS: Event handlers específicos
      onIntegrationReady: (data) => {
        console.log('[ConversationalPivot] 🔗 Perfect Integration ready:', data);
        setIntegrationStatus('success');
      },

      onComplexAnalysis: (data) => {
        console.log('[ConversationalPivot] 🧠 Complex analysis:', data);
        setAiMode('analysis');
      },

      onClassification: (data) => {
        console.log('[ConversationalPivot] 🎯 Message classified:', data);
        setAiMode(data.flowType === 'PIVOT' ? 'pivot' : 'chat');
      }
    });

    // ✅ Solo conectar WebSocket si no hay conflictos
    if (!hasConflict) {
      chatSessionRef.current.connect();
    }

    return () => {
      if (chatSessionRef.current) {
        chatSessionRef.current.close();
      }
      if (pivotControllerRef.current) {
        pivotControllerRef.current.abort();
      }
    };
  }, [userId]);

  // ✅ FUNCIÓN: Manejar charts desde WebSocket
  const handleChartsFromWebSocket = useCallback(async (charts) => {
    console.log('[ConversationalPivot] 🔄 Processing charts from WebSocket:', charts.length);
    
    try {
      const unifiedChart = charts.find(chart => 
        chart.meta?.type === 'unified' || 
        chart.meta?.chart_id === 'unified' ||
        chart.chartKey === 'unified' ||
        !chart.meta?.type
      );
      
      if (unifiedChart) {
        console.log('[ConversationalPivot] ✅ Found unified chart, updating InteractiveCharts');
        
        // ✅ Usar onChartUpdate para Perfect Integration
        if (onChartUpdate && typeof onChartUpdate === 'function') {
          onChartUpdate({
            chartKey: 'unified',
            ...unifiedChart,
            source: 'conversational_pivot',
            timestamp: Date.now()
          });
        }
        
        setLastPivotSuccess(true);
        setIntegrationStatus('success');
        
        // Auto-reset success indicator
        setTimeout(() => setLastPivotSuccess(false), 3000);
      }
      
    } catch (error) {
      console.error('[ConversationalPivot] ❌ Error processing charts:', error);
      setIntegrationStatus('error');
    }
  }, [onChartUpdate]);

  // ✅ FUNCIÓN PRINCIPAL: Enviar mensaje con Perfect Integration
  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: inputMessage.trim(),
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIntegrationStatus('processing');

    // ✅ Abort controller para request
    pivotControllerRef.current = new AbortController();

    try {
      console.log(`[ConversationalPivot] 🚀 Processing message with Perfect Integration: "${inputMessage}"`);
      
      // ✅ NUEVO: Verificar si estamos en modo HTTP-only
      if (isHttpOnlyMode) {
        console.log('[ConversationalPivot] 📡 Using HTTP-only mode for this request');
      }
      
      const messageText = inputMessage.trim();
      
      // ✅ STEP 1: Clasificación inteligente
      const classification = await chatService.http.classifyAndRoute(messageText, {
        mode,
        gestorId: gestorId ? String(gestorId) : undefined,
        periodo: periodo ? String(periodo) : undefined,
        currentChartConfig: currentChartConfig || {}
      });

      console.log('[ConversationalPivot] 🎯 Message classified:', classification);

      let response = null;
      let updatedChart = null;

      if (classification.flowType === 'PIVOT' || messageText.toLowerCase().includes('cambia') || 
          messageText.toLowerCase().includes('convierte') || messageText.toLowerCase().includes('muestra')) {
        
        // ✅ STEP 2: Usar analyticsService.pivotChart para modificación real
        console.log('[ConversationalPivot] 🔄 Using pivotChart for real modification');
        
        try {
          updatedChart = await analyticsService.pivotChart(userId, messageText, currentChartConfig, 'pivot');
          
          if (updatedChart) {
            console.log('[ConversationalPivot] ✅ Chart pivoted successfully');
            
            // ✅ STEP 3: Actualizar InteractiveCharts directamente
            if (onChartUpdate) {
              onChartUpdate({
                chartKey: 'unified',
                ...updatedChart,
                source: 'pivot_direct',
                message: messageText,
                timestamp: Date.now()
              });
            }

            setLastPivotSuccess(true);
            setIntegrationStatus('success');
            
            response = {
              text: `✅ **Gráfico actualizado**
"${messageText}" procesado con Perfect Integration.
✅ Cambios aplicados en tiempo real
¡El cambio ya es visible!${isHttpOnlyMode ? '\n🔄 Via HTTP-Only' : ''}`,
              charts: [updatedChart]
            };
          }
          
        } catch (pivotError) {
          console.warn('[ConversationalPivot] Pivot failed, using chat fallback:', pivotError.message);
          
          // ✅ FALLBACK: Chat normal si pivot falla
          response = await chatService.http.sendMessage({
            user_id: userId,
            message: messageText,
            gestor_id: gestorId ? String(gestorId) : undefined,
            periodo: periodo ? String(periodo) : undefined,
            include_charts: true,
            include_recommendations: false,
            context: {
              mode,
              chartTarget: 'unified',
              intent: 'chart_modification',
              fallbackReason: pivotError.message
            },
            current_chart_config: currentChartConfig || {},
            chart_interaction_type: 'pivot',
            use_basic_queries: true,
            quick_mode: true
          });
        }
        
      } else {
        // ✅ STEP 2B: Chat normal para consultas no-pivot
        console.log('[ConversationalPivot] 💬 Using regular chat for non-pivot message');
        
        response = await chatService.http.sendMessage({
          user_id: userId,
          message: messageText,
          gestor_id: gestorId ? String(gestorId) : undefined,
          periodo: periodo ? String(periodo) : undefined,
          include_charts: false, // No charts para consultas generales
          include_recommendations: true,
          context: {
            mode,
            chartTarget: 'unified',
            intent: 'general_query'
          },
          quick_mode: true
        });
      }

      // ✅ STEP 4: Procesar respuesta
      if (response && response.text) {
        const assistantMessage = {
          id: Date.now() + 1,
          sender: 'assistant',
          text: response.text,
          timestamp: new Date().toLocaleTimeString(),
          source: updatedChart ? 'pivot_success' : 'chat_response',
          aiMode: classification.flowType?.toLowerCase() || 'chat'
        };
        setMessages(prev => [...prev, assistantMessage]);
      }

      // ✅ STEP 5: Procesar charts adicionales si existen
      if (response && response.charts && response.charts.length > 0) {
        await handleChartsFromWebSocket(response.charts);
      }

      notification.success({
        message: '🤖 Procesado con IA',
        description: updatedChart ? 'Gráfico actualizado correctamente' : 'Consulta procesada',
        duration: 2
      });

    } catch (error) {
      console.error('[ConversationalPivot] ❌ Error processing message:', error);
      setIntegrationStatus('error');
      
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: `❌ **Error en Perfect Integration**

${error.message || 'No se pudo procesar tu solicitud.'}

**Sugerencias:**
• Reformula tu mensaje
• Verifica que InteractiveCharts esté visible
• Prueba: "Cambia a barras horizontales"`,
        timestamp: new Date().toLocaleTimeString(),
        isError: true,
        aiMode: 'error'
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      notification.error({
        message: '❌ Error en IA',
        description: error.message || 'Error desconocido',
        duration: 3
      });
    } finally {
      setIsLoading(false);
      setInputMessage('');
      
      // Reset integration status after delay
      setTimeout(() => {
        if (integrationStatus !== 'success') {
          setIntegrationStatus('idle');
        }
      }, 2000);
    }
  }, [
    inputMessage, 
    isLoading, 
    userId, 
    mode, 
    gestorId, 
    periodo, 
    currentChartConfig, 
    onChartUpdate,
    integrationStatus,
    isHttpOnlyMode
  ]);

  // ✅ MANEJAR ENTER
  const handleKeyPress = useCallback((event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  // ✅ LIMPIAR CHAT CON RESET MEJORADO
  const handleClearChat = useCallback(async () => {
    try {
      console.log('[ConversationalPivot] 🧹 Clearing chat with Perfect Integration reset');
      
      if (chatSessionRef.current && !isHttpOnlyMode) {
        await chatSessionRef.current.reset();
      }
      
      // ✅ Limpiar cache de analytics
      if (analyticsService.clearAnalyticsCache) {
        analyticsService.clearAnalyticsCache();
      }
      
      setMessages([]);
      setLastPivotSuccess(false);
      setIntegrationStatus('idle');
      setAiMode('chat');
      
      notification.info({
        message: '🧹 Chat limpiado',
        description: 'Sesión reiniciada',
        duration: 2
      });
      
    } catch (error) {
      console.warn('[ConversationalPivot] Error clearing chat:', error);
      setMessages([]);
    }
  }, [isHttpOnlyMode]);

  // ✅ SUGERENCIAS CONTEXTUALES DINÁMICAS Y COMPACTAS
  const getContextualSuggestions = useCallback(() => {
    const baseSuggestions = [
      "Barras horizontales",
      "Gráfico circular", 
      "Métrica MARGEN"
    ];

    if (mode === 'direccion') {
      return [
        ...baseSuggestions,
        "Por centros",
        "Por segmentos"
      ];
    } else {
      return [
        ...baseSuggestions,
        "Mis clientes",
        "Por productos"
      ];
    }
  }, [mode]);

  const contextualSuggestions = getContextualSuggestions();

  const handleUseSuggestion = useCallback((suggestion) => {
    setInputMessage(suggestion);
  }, []);

  // ✅ MENU DE CONFIGURACIÓN COMPACTO
  const configMenu = {
    items: [
      {
        key: 'reset',
        icon: <ClearOutlined />,
        label: 'Reiniciar',
        onClick: handleClearChat
      },
      {
        key: 'mode',
        icon: <SettingOutlined />,
        label: `Modo: ${isHttpOnlyMode ? 'HTTP-Only' : 'WebSocket'}`,
        disabled: true
      }
    ]
  };

  // ✅ RENDERIZADO COMPLETAMENTE RESPONSIVO
  return (
    <Card
      className={`conversational-pivot-v11 ${className}`}
      style={{
        width: '100%', // ✅ CAMBIO CLAVE: width 100% en lugar de fijo
        height: '100%', // ✅ CAMBIO CLAVE: height 100% en lugar de fijo
        display: 'flex',
        flexDirection: 'column',
        border: integrationStatus === 'success' ? '2px solid #52c41a' : 
               integrationStatus === 'error' ? '2px solid #ff4d4f' :
               integrationStatus === 'processing' ? '2px solid #1890ff' : '1px solid #d9d9d9',
        boxShadow: integrationStatus === 'processing' ? '0 0 12px rgba(24, 144, 255, 0.3)' : undefined,
        ...style
      }}
      title={
        <Space size="small">
          <Avatar 
            icon={<RobotOutlined />} 
            style={{ 
              backgroundColor: isConnected ? '#52c41a' : '#ff4d4f',
              border: integrationStatus === 'processing' ? '2px solid #1890ff' : 'none'
            }} 
            size="small"
          />
          <div>
            <Text strong style={{ fontSize: 13 }}>Chat IA</Text>
            <div style={{ fontSize: 9, color: '#666', marginTop: -2 }}>
              Perfect Integration v11.1 {isHttpOnlyMode && '(HTTP-Only)'}
            </div>
          </div>
          <Space size="small">
            <Tag color={isConnected ? 'green' : 'red'} size="small">
              {isConnected ? (isHttpOnlyMode ? 'HTTP' : 'WS') : 'OFF'}
            </Tag>
            {integrationStatus === 'processing' && (
              <Badge count="..." style={{ backgroundColor: '#1890ff', fontSize: 8 }} />
            )}
            {lastPivotSuccess && (
              <Badge count="✅" style={{ backgroundColor: '#52c41a', fontSize: 8 }} />
            )}
          </Space>
        </Space>
      }
      extra={
        <Space size="small">
          <Tooltip title={`Modo: ${aiMode} ${isHttpOnlyMode ? '(HTTP-Only)' : ''}`}>
            <Avatar 
              size="small"
              style={{ 
                backgroundColor: aiMode === 'pivot' ? '#52c41a' : 
                               aiMode === 'analysis' ? '#1890ff' : '#f0f0f0',
                color: aiMode !== 'chat' ? 'white' : '#666',
                fontSize: 10
              }}
            >
              {aiMode === 'pivot' ? 'P' : aiMode === 'analysis' ? 'A' : 'C'}
            </Avatar>
          </Tooltip>
          <Dropdown menu={configMenu} placement="bottomRight">
            <Button size="small" icon={<SettingOutlined />} />
          </Dropdown>
        </Space>
      }
      styles={{ 
        body: {
          padding: 0, 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column',
          overflow: 'hidden' // ✅ CAMBIO CLAVE: Prevenir scroll externo
        }
      }}
    >
      {/* ✅ ÁREA DE MENSAJES COMPLETAMENTE RESPONSIVA */}
      <div 
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '12px', 
          backgroundColor: '#fafafa',
          minHeight: 0 // ✅ CAMBIO CLAVE: Permite que flex shrink funcione
        }}
      >
        {messages.length === 0 ? (
          <Empty 
            image={<MessageOutlined style={{ fontSize: 24, color: '#ccc' }} />}
            description={
              <div style={{ textAlign: 'center' }}>
                <div style={{ marginBottom: 6 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>Perfect Integration v11.1</Text>
                </div>
                <div style={{ marginBottom: 12 }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    Modifica gráficos con lenguaje natural
                  </Text>
                </div>
                {currentChartConfig ? (
                  <Tag color="green" size="small">✅ Gráfico detectado</Tag>
                ) : (
                  <Tag color="orange" size="small">⚠️ Sin gráfico</Tag>
                )}
                {isHttpOnlyMode && (
                  <Tag color="blue" size="small">📡 Modo HTTP-Only</Tag>
                )}
                <div style={{ marginTop: 6 }}>
                  <Text type="secondary" style={{ fontSize: 10 }}>
                    Modo: {mode}
                  </Text>
                </div>
              </div>
            }
          />
        ) : (
          messages.map(message => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                marginBottom: 10,
                alignItems: 'flex-start'
              }}
            >
              {message.sender === 'assistant' && (
                <Avatar 
                  icon={<RobotOutlined />} 
                  size="small"
                  style={{ 
                    backgroundColor: message.isError ? '#ff4d4f' : 
                                   message.source === 'pivot_success' ? '#52c41a' :
                                   message.aiMode === 'analysis' ? '#722ed1' : 
                                   isHttpOnlyMode ? '#1890ff' : '#52c41a',
                    marginRight: 6,
                    marginTop: 2
                  }} 
                />
              )}
              
              <div
                style={{
                  maxWidth: '80%',
                  padding: '6px 10px',
                  borderRadius: 8,
                  backgroundColor: message.sender === 'user' ? 
                    (theme.colors?.bmGreenPrimary || '#1890ff') : 
                    (message.isError ? '#fff2f0' : 
                     message.source === 'pivot_success' ? '#f6ffed' : '#f0f0f0'),
                  color: message.sender === 'user' ? 'white' : '#333',
                  wordBreak: 'break-word',
                  fontSize: 12,
                  lineHeight: 1.4,
                  border: message.isError ? '1px solid #ffccc7' : 
                         message.source === 'pivot_success' ? '1px solid #b7eb8f' : 'none',
                  whiteSpace: 'pre-wrap'
                }}
              >
                {message.text}
                
                {message.isWelcome && (
                  <div style={{ marginTop: 8 }}>
                    <Text strong style={{ fontSize: 10, display: 'block', marginBottom: 6, color: '#666' }}>
                      <BulbOutlined /> Prueba:
                    </Text>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {contextualSuggestions.slice(0, 2).map((suggestion, index) => (
                        <Button
                          key={index}
                          type="link"
                          size="small"
                          onClick={() => handleUseSuggestion(suggestion)}
                          style={{ 
                            padding: '1px 0',
                            height: 'auto',
                            fontSize: 10,
                            textAlign: 'left',
                            color: '#1890ff'
                          }}
                        >
                          "{suggestion}"
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
                
                <div style={{ 
                  fontSize: 9, 
                  opacity: 0.7, 
                  marginTop: 4,
                  textAlign: message.sender === 'user' ? 'right' : 'left',
                  display: 'flex',
                  justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                  alignItems: 'center',
                  gap: 4
                }}>
                  <span>{message.timestamp}</span>
                  {message.aiMode && message.aiMode !== 'chat' && (
                    <Tag size="small" color="blue" style={{ fontSize: 8, padding: '0 4px', lineHeight: '14px' }}>
                      {message.aiMode.toUpperCase()}
                    </Tag>
                  )}
                </div>
              </div>
              
              {message.sender === 'user' && (
                <Avatar 
                  icon={<UserOutlined />} 
                  size="small"
                  style={{ 
                    backgroundColor: '#52c41a',
                    marginLeft: 6,
                    marginTop: 2
                  }} 
                />
              )}
            </div>
          ))
        )}
        
        {/* ✅ INDICADOR DE CARGA MEJORADO Y COMPACTO */}
        {isLoading && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-start', 
            alignItems: 'center',
            marginBottom: 10
          }}>
            <Avatar 
              icon={<RobotOutlined />} 
              size="small"
              style={{ 
                backgroundColor: '#1890ff',
                marginRight: 6,
                marginTop: 2,
                border: '2px solid #1890ff'
              }} 
            />
            <div style={{
              padding: '6px 10px',
              borderRadius: 8,
              backgroundColor: '#f0f0f0',
              border: '2px solid #1890ff',
              fontSize: 12
            }}>
              <Space size="small">
                <Spin 
                  indicator={<LoadingOutlined style={{ fontSize: 12 }} spin />} 
                />
                <span>
                  {integrationStatus === 'processing' ? 'Procesando...' : 'Procesando...'}
                </span>
              </Space>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* ✅ SUGERENCIAS CONTEXTUALES COMPACTAS */}
      {messages.length <= 1 && (
        <div style={{ padding: '6px 12px', borderTop: '1px solid #f0f0f0', backgroundColor: '#fafafa' }}>
          <Text strong style={{ fontSize: 10, display: 'block', marginBottom: 6, color: '#666' }}>
            <ThunderboltOutlined /> Comandos rápidos:
          </Text>
          <Space wrap size="small">
            {contextualSuggestions.map((suggestion, index) => (
              <Button
                key={index}
                size="small"
                type="dashed"
                onClick={() => handleUseSuggestion(suggestion)}
                style={{ fontSize: 9, padding: '2px 6px', height: 24 }}
              >
                {suggestion}
              </Button>
            ))}
          </Space>
        </div>
      )}

      {/* ✅ ÁREA DE INPUT COMPLETAMENTE RESPONSIVA */}
      <div style={{ 
        padding: 10, 
        borderTop: '1px solid #f0f0f0',
        backgroundColor: 'white',
        flexShrink: 0 // ✅ CAMBIO CLAVE: Evita que se comprima
      }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`Comando para gráfico... (${mode})`}
            autoSize={{ minRows: 1, maxRows: 2 }}
            disabled={isLoading}
            maxLength={200}
            style={{ 
              borderRadius: '4px 0 0 4px',
              resize: 'none',
              fontSize: 12,
              borderColor: integrationStatus === 'processing' ? '#1890ff' : undefined
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={isLoading}
            disabled={!inputMessage.trim()}
            size="small"
            style={{ 
              borderRadius: '0 4px 4px 0',
              backgroundColor: integrationStatus === 'processing' ? '#1890ff' :
                             lastPivotSuccess ? '#52c41a' :
                             theme.colors?.bmGreenPrimary || '#1890ff',
              borderColor: integrationStatus === 'processing' ? '#1890ff' :
                          lastPivotSuccess ? '#52c41a' :
                          theme.colors?.bmGreenPrimary || '#1890ff'
            }}
          >
            {integrationStatus === 'processing' ? '...' : 'Enviar'}
          </Button>
        </Space.Compact>

        {/* ✅ ESTADO DE CONEXIÓN COMPACTO */}
        <div style={{ marginTop: 6, textAlign: 'center' }}>
          <Space split={<span>•</span>} size="small">
            <Text type="secondary" style={{ fontSize: 9 }}>
              Enter para enviar
            </Text>
            <Text type="secondary" style={{ fontSize: 9 }}>
              {integrationStatus}
            </Text>
            <Text type="secondary" style={{ fontSize: 9 }}>
              {mode === 'direccion' ? 'Corporativo' : 'Personal'}
            </Text>
            {isHttpOnlyMode && (
              <Text type="secondary" style={{ fontSize: 9, color: '#1890ff' }}>
                HTTP-Only
              </Text>
            )}
          </Space>
        </div>
      </div>

      {/* ✅ ALERTAS DE ESTADO COMPACTAS */}
      {!currentChartConfig && (
        <Alert
          message="Sin gráfico detectado"
          description="Asegúrate de que InteractiveCharts esté visible"
          type="warning"
          showIcon
          style={{ margin: '6px 10px 10px 10px', fontSize: 10 }}
        />
      )}

      {integrationStatus === 'error' && !isHttpOnlyMode && (
        <Alert
          message="Error en Perfect Integration"
          description="Revisa la conexión e intenta de nuevo"
          type="error"
          showIcon
          closable
          onClose={() => setIntegrationStatus('idle')}
          style={{ margin: '6px 10px 10px 10px', fontSize: 10 }}
        />
      )}

      {isHttpOnlyMode && (
        <Alert
          message="Modo HTTP-Only activo"
          description="Funcionalidad completa via HTTP para evitar conflictos"
          type="info"
          showIcon
          style={{ margin: '6px 10px 10px 10px', fontSize: 10 }}
        />
      )}
    </Card>
  );
};

// ✅ PROP TYPES ACTUALIZADOS
ConversationalPivot.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  periodo: PropTypes.string,
  currentChartConfig: PropTypes.object,
  onChartUpdate: PropTypes.func.isRequired,
  className: PropTypes.string,
  style: PropTypes.object
};

export default React.memo(ConversationalPivot);
