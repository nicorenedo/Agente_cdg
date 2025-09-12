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
 * ✅ ConversationalPivot v11.0 - Perfect Integration
 * 
 * FUNCIONALIDADES NUEVAS:
 * 1. Perfect Integration con InteractiveCharts v11.0
 * 2. Usa analyticsService.pivotChart() para modificación real
 * 3. Chat Agent v10.0 + CDG Agent v6.0 integration
 * 4. Classification inteligente de requests
 * 5. Feedback loop para mejora continua
 * 6. Sugerencias dinámicas contextuales
 * 7. Estados avanzados de IA
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
  const [aiMode, setAiMode] = useState('chat'); // 'chat' | 'pivot' | 'analysis'
  const [lastPivotSuccess, setLastPivotSuccess] = useState(false);
  const [availableQueries, setAvailableQueries] = useState([]);
  const [integrationStatus, setIntegrationStatus] = useState('idle'); // 'idle' | 'processing' | 'success' | 'error'

  // ✅ USER ID ÚNICO POR MODO
  const userId = React.useMemo(() => {
    const baseUserId = gestorId ? String(gestorId) : 'anonymous';
    return mode === 'direccion' ? `direction_${baseUserId}` : `gestor_${baseUserId}`;
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

  // ✅ INICIALIZAR CHAT SESSION CON PERFECT INTEGRATION
  useEffect(() => {
    console.log(`[ConversationalPivot] 🚀 Initializing Perfect Integration for userId: ${userId}`);

    // Crear sesión de chat con Chat Agent v10.0
    chatSessionRef.current = chatService.createChatSession(userId, {
      onOpen: () => {
        console.log('[ConversationalPivot] ✅ Chat Agent v10.0 connected');
        setIsConnected(true);
        
        // ✅ Mensaje de bienvenida mejorado
        const welcomeMsg = {
          id: Date.now(),
          sender: 'assistant',
          text: `🤖 **Perfect Integration v11.0 Activada**

¡Hola! Soy tu asistente IA para modificar gráficos de manera conversacional.

**Nuevas capacidades:**
• Chat Agent v10.0 + CDG Agent v6.0
• Clasificación inteligente de consultas
• Modificación real de gráficos usando AnalyticsService
• Soporte para ${mode === 'direccion' ? 'dashboard corporativo' : 'panel de gestor'}

**Ejemplos de comandos:**
• "Cambia a barras horizontales"
• "Muestra por centros en lugar de gestores"
• "Convierte a gráfico circular"
• "Cambiar métrica a MARGEN"
• "Analizar por productos"

**Objetivo:** Solo modifico el gráfico de análisis general para mantener simplicidad.`,
          timestamp: new Date().toLocaleTimeString(),
          isWelcome: true,
          aiMode: 'welcome'
        };
        setMessages([welcomeMsg]);
      },

      onClose: () => {
        console.log('[ConversationalPivot] ❌ WebSocket disconnected');
        setIsConnected(false);
      },

      onError: (error) => {
        console.error('[ConversationalPivot] WebSocket error:', error);
        setIsConnected(false);
        setIntegrationStatus('error');
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

    // Conectar WebSocket
    chatSessionRef.current.connect();

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
              text: `✅ **Gráfico actualizado correctamente**

Tu solicitud "${messageText}" ha sido procesada usando Perfect Integration v11.0.

**Cambios aplicados:**
• Gráfico modificado usando AnalyticsService
• Datos actualizados en tiempo real
• Configuración guardada automáticamente

¡El cambio ya es visible en el panel principal!`,
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
        duration: 3
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
• Intenta reformular tu mensaje
• Verifica que InteractiveCharts esté visible
• Prueba con comandos más específicos como "Cambia a barras horizontales"

**Estado:** ${isConnected ? 'Conectado' : 'Desconectado'} • Modo: ${mode}`,
        timestamp: new Date().toLocaleTimeString(),
        isError: true,
        aiMode: 'error'
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      notification.error({
        message: '❌ Error en IA',
        description: error.message || 'Error desconocido en Perfect Integration',
        duration: 4
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
    integrationStatus
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
      
      if (chatSessionRef.current) {
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
        description: 'Sesión reiniciada con Perfect Integration',
        duration: 2
      });
      
    } catch (error) {
      console.warn('[ConversationalPivot] Error clearing chat:', error);
      setMessages([]);
    }
  }, []);

  // ✅ SUGERENCIAS CONTEXTUALES DINÁMICAS
  const getContextualSuggestions = useCallback(() => {
    const baseSuggestions = [
      "Cambia a barras horizontales",
      "Muestra como gráfico circular", 
      "Convierte a líneas",
      "Cambiar métrica a MARGEN"
    ];

    if (mode === 'direccion') {
      return [
        ...baseSuggestions,
        "Mostrar por centros",
        "Análisis por segmentos",
        "Vista de productos"
      ];
    } else {
      return [
        ...baseSuggestions,
        "Ver mis clientes",
        "Análisis por productos",
        "Mostrar evolución"
      ];
    }
  }, [mode]);

  const contextualSuggestions = getContextualSuggestions();

  const handleUseSuggestion = useCallback((suggestion) => {
    setInputMessage(suggestion);
  }, []);

  // ✅ MENU DE CONFIGURACIÓN
  const configMenu = {
    items: [
      {
        key: 'reset',
        icon: <ClearOutlined />,
        label: 'Reiniciar sesión',
        onClick: handleClearChat
      },
      {
        key: 'queries',
        icon: <QuestionCircleOutlined />,
        label: `Queries disponibles: ${availableQueries.length}`,
        disabled: true
      },
      {
        key: 'mode',
        icon: <SettingOutlined />,
        label: `Modo: ${mode}`,
        disabled: true
      }
    ]
  };

  // ✅ RENDERIZADO MEJORADO
  return (
    <Card
      className={`conversational-pivot-v11 ${className}`}
      style={{
        width: 380,
        height: 520,
        display: 'flex',
        flexDirection: 'column',
        border: integrationStatus === 'success' ? '2px solid #52c41a' : 
               integrationStatus === 'error' ? '2px solid #ff4d4f' :
               integrationStatus === 'processing' ? '2px solid #1890ff' : '1px solid #d9d9d9',
        boxShadow: integrationStatus === 'processing' ? '0 0 12px rgba(24, 144, 255, 0.3)' : undefined,
        ...style
      }}
      title={
        <Space>
          <Avatar 
            icon={<RobotOutlined />} 
            style={{ 
              backgroundColor: isConnected ? '#52c41a' : '#ff4d4f',
              border: integrationStatus === 'processing' ? '2px solid #1890ff' : 'none'
            }} 
            size="small"
          />
          <div>
            <Text strong>Perfect Integration</Text>
            <div style={{ fontSize: 10, color: '#666', marginTop: -2 }}>
              Chat Agent v10.0 + CDG Agent v6.0
            </div>
          </div>
          <Space size="small">
            <Tag color={isConnected ? 'green' : 'red'} size="small">
              {isConnected ? 'Conectado' : 'Desconectado'}
            </Tag>
            {integrationStatus === 'processing' && (
              <Badge count="Procesando..." style={{ backgroundColor: '#1890ff', fontSize: 9 }} />
            )}
            {lastPivotSuccess && (
              <Badge count="✅ Éxito" style={{ backgroundColor: '#52c41a', fontSize: 9 }} />
            )}
          </Space>
        </Space>
      }
      extra={
        <Space size="small">
          <Tooltip title="Estado de IA">
            <Avatar 
              size="small"
              style={{ 
                backgroundColor: aiMode === 'pivot' ? '#52c41a' : 
                               aiMode === 'analysis' ? '#1890ff' : '#f0f0f0',
                color: aiMode !== 'chat' ? 'white' : '#666'
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
      styles={{ body: {
        padding: 0, 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column' 
      }}}
    >
      {/* ✅ ÁREA DE MENSAJES MEJORADA */}
      <div 
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '16px', 
          backgroundColor: '#fafafa',
          minHeight: 320
        }}
      >
        {messages.length === 0 ? (
          <Empty 
            image={<MessageOutlined style={{ fontSize: 32, color: '#ccc' }} />}
            description={
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">¡Hola! Usa Perfect Integration v11.0</Text>
                </div>
                <div style={{ marginBottom: 16 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Modifica gráficos con lenguaje natural
                  </Text>
                </div>
                {currentChartConfig ? (
                  <Tag color="green" size="small">✅ Gráfico detectado</Tag>
                ) : (
                  <Tag color="orange" size="small">⚠️ Sin gráfico activo</Tag>
                )}
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    Modo: {mode} • Estado: {integrationStatus}
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
                marginBottom: 12,
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
                                   message.aiMode === 'analysis' ? '#722ed1' : '#1890ff',
                    marginRight: 8,
                    marginTop: 4
                  }} 
                />
              )}
              
              <div
                style={{
                  maxWidth: '75%',
                  padding: '8px 12px',
                  borderRadius: 12,
                  backgroundColor: message.sender === 'user' ? 
                    (theme.colors?.bmGreenPrimary || '#1890ff') : 
                    (message.isError ? '#fff2f0' : 
                     message.source === 'pivot_success' ? '#f6ffed' : '#f0f0f0'),
                  color: message.sender === 'user' ? 'white' : '#333',
                  wordBreak: 'break-word',
                  border: message.isError ? '1px solid #ffccc7' : 
                         message.source === 'pivot_success' ? '1px solid #b7eb8f' : 'none',
                  whiteSpace: 'pre-wrap'
                }}
              >
                {message.text}
                
                {message.isWelcome && (
                  <div style={{ marginTop: 12 }}>
                    <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, color: '#666' }}>
                      <BulbOutlined /> Prueba estos comandos:
                    </Text>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {contextualSuggestions.slice(0, 3).map((suggestion, index) => (
                        <Button
                          key={index}
                          type="link"
                          size="small"
                          onClick={() => handleUseSuggestion(suggestion)}
                          style={{ 
                            padding: '2px 0',
                            height: 'auto',
                            fontSize: 11,
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
                  fontSize: 10, 
                  opacity: 0.7, 
                  marginTop: 4,
                  textAlign: message.sender === 'user' ? 'right' : 'left',
                  display: 'flex',
                  justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                  alignItems: 'center',
                  gap: 4
                }}>
                  <span>{message.timestamp}</span>
                  {message.source && <span>• {message.source}</span>}
                  {message.aiMode && message.aiMode !== 'chat' && (
                    <Tag size="small" color="blue">{message.aiMode.toUpperCase()}</Tag>
                  )}
                </div>
              </div>
              
              {message.sender === 'user' && (
                <Avatar 
                  icon={<UserOutlined />} 
                  size="small"
                  style={{ 
                    backgroundColor: '#52c41a',
                    marginLeft: 8,
                    marginTop: 4
                  }} 
                />
              )}
            </div>
          ))
        )}
        
        {/* ✅ INDICADOR DE CARGA MEJORADO */}
        {isLoading && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'flex-start', 
            alignItems: 'center',
            marginBottom: 12
          }}>
            <Avatar 
              icon={<RobotOutlined />} 
              size="small"
              style={{ 
                backgroundColor: '#1890ff',
                marginRight: 8,
                marginTop: 4,
                border: '2px solid #1890ff',
                animation: 'pulse 1s infinite'
              }} 
            />
            <div style={{
              padding: '8px 12px',
              borderRadius: 12,
              backgroundColor: '#f0f0f0',
              border: '2px solid #1890ff'
            }}>
              <Space>
                <Spin 
                  indicator={<LoadingOutlined style={{ fontSize: 14 }} spin />} 
                />
                <span style={{ fontSize: 12 }}>
                  {integrationStatus === 'processing' ? 'Procesando con Perfect Integration...' : 'Procesando...'}
                </span>
              </Space>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* ✅ SUGERENCIAS CONTEXTUALES */}
      {messages.length <= 1 && (
        <div style={{ padding: '8px 16px', borderTop: '1px solid #f0f0f0' }}>
          <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, color: '#666' }}>
            <ThunderboltOutlined /> Comandos {mode === 'direccion' ? 'corporativos' : 'personales'}:
          </Text>
          <Space wrap size="small">
            {contextualSuggestions.map((suggestion, index) => (
              <Button
                key={index}
                size="small"
                type="dashed"
                onClick={() => handleUseSuggestion(suggestion)}
                style={{ fontSize: 10 }}
              >
                {suggestion}
              </Button>
            ))}
          </Space>
        </div>
      )}

      {/* ✅ ÁREA DE INPUT MEJORADA */}
      <div style={{ 
        padding: 12, 
        borderTop: '1px solid #f0f0f0',
        backgroundColor: 'white'
      }}>
        <Space.Compact style={{ width: '100%' }}>
          <TextArea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`Escribe tu comando para modificar el gráfico... (Modo: ${mode})`}
            autoSize={{ minRows: 1, maxRows: 3 }}
            disabled={isLoading}
            maxLength={400}
            style={{ 
              borderRadius: '6px 0 0 6px',
              resize: 'none',
              borderColor: integrationStatus === 'processing' ? '#1890ff' : undefined
            }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSendMessage}
            loading={isLoading}
            disabled={!inputMessage.trim()}
            style={{ 
              borderRadius: '0 6px 6px 0',
              backgroundColor: integrationStatus === 'processing' ? '#1890ff' :
                             lastPivotSuccess ? '#52c41a' :
                             theme.colors?.bmGreenPrimary || '#1890ff',
              borderColor: integrationStatus === 'processing' ? '#1890ff' :
                          lastPivotSuccess ? '#52c41a' :
                          theme.colors?.bmGreenPrimary || '#1890ff'
            }}
          >
            {integrationStatus === 'processing' ? 'Procesando' : 'Enviar'}
          </Button>
        </Space.Compact>

        {/* ✅ ESTADO DE CONEXIÓN E INTEGRACIÓN */}
        <div style={{ marginTop: 8, textAlign: 'center' }}>
          <Space split={<span>•</span>} size="small">
            <Text type="secondary" style={{ fontSize: 10 }}>
              Enter para enviar
            </Text>
            <Text type="secondary" style={{ fontSize: 10 }}>
              Estado: {integrationStatus}
            </Text>
            <Text type="secondary" style={{ fontSize: 10 }}>
              {mode === 'direccion' ? 'Dashboard Corporativo' : 'Panel Personal'}
            </Text>
          </Space>
        </div>
      </div>

      {/* ✅ ALERTAS DE ESTADO */}
      {!currentChartConfig && (
        <Alert
          message="⚠️ Configuración de gráfico no detectada"
          description="Asegúrate de que InteractiveCharts esté visible y cargado para usar Perfect Integration"
          type="warning"
          showIcon
          style={{ margin: '8px 16px 16px 16px', fontSize: 11 }}
        />
      )}

      {integrationStatus === 'error' && (
        <Alert
          message="❌ Error en Perfect Integration"
          description="Revisa la conexión y intenta de nuevo. El sistema está funcionando en modo fallback."
          type="error"
          showIcon
          closable
          onClose={() => setIntegrationStatus('idle')}
          style={{ margin: '8px 16px 16px 16px', fontSize: 11 }}
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
