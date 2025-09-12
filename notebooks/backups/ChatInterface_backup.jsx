// frontend/src/components/Dashboard/ChatInterface.jsx
import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Badge,
  Tag,
  Empty,
  Alert,
  Tooltip,
  Spin,
  Row,
  Col,
  Switch,
  notification
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  MessageOutlined,
  WifiOutlined,
  DisconnectOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
  CopyOutlined,
  LoadingOutlined,
  DashboardOutlined,
  ExpandOutlined,
  CompressOutlined,
  EyeOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import theme from '../../styles/theme';

const { TextArea } = Input;
const { Text, Title } = Typography;

/**
 * ✅ ChatInterface - CHAT GENERAL CDG (NO PIVOTEO)
 * ------------------------------------------------
 * - Chat conversacional general con Agente CDG
 * - Consultas sobre KPIs, métricas, análisis, informes
 * - Respuestas en lenguaje natural del chat_agent.py
 * - NO maneja pivoteo de gráficos (eso es ConversationalPivot)
 * - Soporte WebSocket + HTTP fallback
 */
const ChatInterface = ({
  scope = 'direccion',
  periodo = null,
  gestorId = null,
  currentChartConfig = null,
  onNewChart = () => {},
  onCommand = () => {},
  suggestions = null,
  expanded = false,
  className = '',
  style = {}
}) => {
  
  // ✅ ESTADOS PRINCIPALES
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [error, setError] = useState(null);
  const [useWebSocket, setUseWebSocket] = useState(true);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isExpanded, setIsExpanded] = useState(expanded);
  const [connectionAttempts, setConnectionAttempts] = useState(0);

  // ✅ REFERENCIAS
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const inputRef = useRef(null);
  const sessionRef = useRef(null);
  const reconnectTimer = useRef(null);
  const isManualDisconnect = useRef(false);
  const isMounted = useRef(true);

  // ✅ USER ID ESTABLE
  const userId = useMemo(() => 
    `cdg-chat-${scope}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`, 
    [scope]
  );

  // ✅ CONTEXTO PARA EL CHAT GENERAL
  const buildContext = useCallback(() => ({
    scope,
    periodo: periodo || undefined,
    gestor_id: scope === 'gestor' ? gestorId : undefined,
    user_role: scope,
    chat_type: 'general', // ✅ IMPORTANTE: Diferencia del chat de pivoteo
    current_chart_available: !!currentChartConfig
  }), [scope, periodo, gestorId, currentChartConfig]);

  // ✅ MENSAJE DE BIENVENIDA ESPECÍFICO
  const welcomeMessage = useMemo(() => ({
    id: `welcome-${Date.now()}`,
    type: 'assistant',
    content: scope === 'direccion' 
      ? `¡Hola! Soy tu **Asistente CDG para Análisis Corporativo**. Puedo ayudarte con:\n\n• Consultas sobre KPIs consolidados\n• Rankings de gestores y centros\n• Análisis de desviaciones\n• Interpretación de métricas financieras\n• Generación de informes ejecutivos\n\n¿En qué análisis te puedo ayudar?`
      : `¡Hola${gestorId ? ` Gestor ${gestorId}` : ''}! Soy tu **Asistente CDG Personal**. Puedo ayudarte con:\n\n• Análisis de tu cartera de clientes\n• Comparativas de tu rendimiento\n• Interpretación de tus KPIs personales\n• Oportunidades de mejora\n• Consultas sobre tus métricas\n\n¿Qué te gustaría consultar sobre tu gestión?`,
    timestamp: new Date(),
    recommendations: [
      scope === 'direccion' ? 'KPIs corporativos principales' : 'Mis KPIs principales',
      scope === 'direccion' ? 'Top 5 gestores por margen' : 'Mi posición vs otros gestores',
      scope === 'direccion' ? 'Desviaciones críticas' : 'Oportunidades en mi cartera'
    ]
  }), [scope, gestorId]);

  // ✅ SUGERENCIAS CONTEXTUALES
  const defaultSuggestions = useMemo(() => {
    if (scope === 'direccion') {
      return [
        '¿Cuáles son los KPIs principales del periodo?',
        '¿Qué gestores tienen mejor rendimiento?',
        '¿Hay desviaciones importantes vs presupuesto?',
        'Resume el estado consolidado del negocio',
        '¿Qué centros necesitan atención prioritaria?'
      ];
    } else {
      return [
        '¿Cómo está mi rendimiento este periodo?',
        '¿Cuáles son mis mejores clientes por margen?',
        '¿Cómo me comparo con otros gestores?',
        '¿Qué productos debería priorizar?',
        '¿Tengo oportunidades de cross-selling?'
      ];
    }
  }, [scope]);

  const activeSuggestions = suggestions || defaultSuggestions;

  // ✅ PROCESAR MENSAJE DEL CHAT AGENT
  const handleChatMessage = useCallback((data) => {
    console.log('[ChatInterface] 📥 Chat response received:', data);

    const responseData = data?.data || data;
    const { text, response, recommendations = [], metadata = {} } = responseData;
    const content = text || response || 'Respuesta procesada correctamente.';

    const assistantMessage = {
      id: `assistant-${Date.now()}`,
      type: 'assistant',
      content,
      timestamp: new Date(),
      recommendations: Array.isArray(recommendations) ? recommendations : [],
      metadata,
      source: 'chat_agent'
    };

    setMessages(prev => [...prev, assistantMessage]);
    setIsSending(false);
    setIsTyping(false);

    // ✅ Scroll automático
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end' 
      });
    }, 150);
  }, []);

  // ✅ INICIALIZAR WEBSOCKET
  const initializeWebSocket = useCallback(() => {
    if (!isMounted.current) return;
    if (sessionRef.current && sessionRef.current.readyState === WebSocket.CONNECTING) return;

    console.log('[ChatInterface] 🌐 Initializing WebSocket...');

    // Limpiar sesión anterior
    if (sessionRef.current) {
      try {
        sessionRef.current.close();
      } catch (e) {
        console.warn('Error closing previous session:', e);
      }
      sessionRef.current = null;
    }

    try {
      const session = chatService.createChatSession(userId, {
        onMessage: handleChatMessage,
        onOpen: () => {
          if (isMounted.current) {
            console.log('[ChatInterface] ✅ WebSocket connected');
            setIsConnected(true);
            setConnectionStatus('connected');
            setConnectionAttempts(0);
            setError(null);
          }
        },
        onClose: () => {
          if (isMounted.current && !isManualDisconnect.current) {
            console.log('[ChatInterface] 🔌 WebSocket closed');
            setIsConnected(false);
            setConnectionStatus('disconnected');
            attemptReconnect();
          }
        },
        onError: (error) => {
          if (isMounted.current && !isManualDisconnect.current) {
            console.error('[ChatInterface] ❌ WebSocket error:', error);
            setIsConnected(false);
            setConnectionStatus('error');
            attemptReconnect();
          }
        },
        onTyping: ({ active }) => {
          if (isMounted.current) {
            setIsTyping(active);
          }
        }
      });

      sessionRef.current = session;
      session.connect();

    } catch (error) {
      console.error('[ChatInterface] Error initializing WebSocket:', error);
      if (!isManualDisconnect.current && isMounted.current) {
        attemptReconnect();
      }
    }
  }, [userId, handleChatMessage]);

  // ✅ LÓGICA DE RECONEXIÓN
  const attemptReconnect = useCallback(() => {
    if (!isMounted.current || isManualDisconnect.current || connectionAttempts >= 3) {
      console.log('[ChatInterface] 🔄 Max attempts reached, switching to HTTP');
      if (isMounted.current) {
        setUseWebSocket(false);
        setConnectionStatus('http-fallback');
        setConnectionAttempts(0);
        setIsConnected(true);
      }
      return;
    }

    const delay = Math.min(2000 * Math.pow(1.5, connectionAttempts), 8000);
    console.log(`[ChatInterface] 🕒 Reconnecting in ${delay}ms (attempt ${connectionAttempts + 1})`);

    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }

    reconnectTimer.current = setTimeout(() => {
      if (isMounted.current && !isManualDisconnect.current) {
        setConnectionAttempts(prev => prev + 1);
        initializeWebSocket();
      }
    }, delay);
  }, [connectionAttempts, initializeWebSocket]);

  // ✅ ENVIAR MENSAJE
  const sendMessage = useCallback(async (messageText, isQuickAction = false) => {
    if (!messageText.trim() || isSending) return;

    console.log('[ChatInterface] 📤 Sending message:', {
      text: messageText,
      scope,
      gestorId,
      periodo,
      useWebSocket,
      isConnected
    });

    const userMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: messageText,
      timestamp: new Date(),
      isQuickAction
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsSending(true);
    setIsTyping(true);
    setError(null);

    // ✅ Scroll al enviar
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end' 
      });
    }, 100);

    try {
      const context = buildContext();

      if (useWebSocket && sessionRef.current && isConnected) {
        console.log('[ChatInterface] 🌐 Sending via WebSocket');
        sessionRef.current.send({
          message: messageText,
          context
        });
      } else {
        console.log('[ChatInterface] 📡 Sending via HTTP');
        const response = await chatService.http.sendMessage({
          user_id: userId,
          message: messageText,
          periodo,
          gestor_id: scope === 'gestor' ? gestorId : undefined,
          context,
          include_charts: false, // ✅ IMPORTANTE: Sin gráficos para chat general
          include_recommendations: true,
          chart_interaction_type: 'query' // No pivot
        });

        handleChatMessage(response);
      }

    } catch (error) {
      console.error('[ChatInterface] ❌ Send error:', error);
      setError(error?.message || 'Error al enviar mensaje');
      setIsSending(false);
      setIsTyping(false);

      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: `❌ Error: ${error?.message || 'No se pudo procesar tu consulta'}. Por favor, inténtalo de nuevo.`,
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    }
  }, [isSending, isConnected, useWebSocket, buildContext, userId, periodo, gestorId, scope, handleChatMessage]);

  // ✅ HANDLERS DE UI
  const handleSend = useCallback(() => {
    sendMessage(currentMessage);
  }, [currentMessage, sendMessage]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleSuggestion = useCallback((suggestion) => {
    sendMessage(suggestion);
  }, [sendMessage]);

  const handleCopyMessage = useCallback((content) => {
    navigator.clipboard.writeText(content).then(() => {
      notification.success({
        message: 'Copiado',
        description: 'Mensaje copiado al portapapeles',
        duration: 2,
        placement: 'bottomRight'
      });
    }).catch(() => {
      notification.error({
        message: 'Error',
        description: 'No se pudo copiar el mensaje',
        duration: 2,
        placement: 'bottomRight'
      });
    });
  }, []);

  const handleRetry = useCallback(() => {
    const lastUserMessage = [...messages].reverse().find(m => m.type === 'user');
    if (lastUserMessage) {
      sendMessage(lastUserMessage.content, lastUserMessage.isQuickAction);
    }
  }, [messages, sendMessage]);

  const handleReconnect = useCallback(() => {
    setConnectionAttempts(0);
    setError(null);
    initializeWebSocket();
  }, [initializeWebSocket]);

  const handleWebSocketToggle = useCallback((checked) => {
    isManualDisconnect.current = !checked;
    
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }

    if (sessionRef.current) {
      try {
        sessionRef.current.close();
      } catch (e) {
        // Ignore
      }
      sessionRef.current = null;
    }

    setConnectionAttempts(0);
    setUseWebSocket(checked);
    setError(null);
    
    if (checked) {
      initializeWebSocket();
    } else {
      setConnectionStatus('http-ready');
      setIsConnected(true);
    }
  }, [initializeWebSocket]);

  const handleToggleExpansion = useCallback(() => {
    setIsExpanded(prev => !prev);
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end' 
      });
    }, 300);
  }, []);

  // ✅ INICIALIZACIÓN
  useEffect(() => {
    isMounted.current = true;
    
    console.log('[ChatInterface] 🚀 Component initialized');
    setMessages([welcomeMessage]);
    setError(null);
    isManualDisconnect.current = false;
    
    if (useWebSocket) {
      setConnectionStatus('connecting');
      setTimeout(() => {
        if (isMounted.current) {
          initializeWebSocket();
        }
      }, 100);
    } else {
      setConnectionStatus('http-ready');
      setIsConnected(true);
    }

    return () => {
      console.log('[ChatInterface] 🧹 Component cleanup');
      isMounted.current = false;
      isManualDisconnect.current = true;

      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }

      if (sessionRef.current) {
        try {
          sessionRef.current.close();
        } catch (e) {
          // Ignore cleanup errors
        }
        sessionRef.current = null;
      }
    };
  }, []);

  // ✅ SCROLL AUTOMÁTICO
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'end' 
      });
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages, isTyping]);

  // ✅ RENDERIZAR MENSAJE
  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const isError = message.isError;

    return (
      <div 
        key={message.id} 
        style={{ 
          display: 'flex', 
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16,
          alignItems: 'flex-start'
        }}
      >
        {!isUser && (
          <Avatar 
            icon={<RobotOutlined />} 
            style={{ 
              backgroundColor: isError ? theme.colors?.error || '#ff4d4f' : theme.colors?.bmGreenPrimary || '#1890ff',
              marginRight: 12,
              flexShrink: 0
            }} 
            size="small"
          />
        )}
        
        <div style={{ 
          maxWidth: isExpanded ? '90%' : '80%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start'
        }}>
          <div style={{
            backgroundColor: isUser 
              ? theme.colors?.bmGreenPrimary || '#1890ff'
              : isError 
                ? `${theme.colors?.error || '#ff4d4f'}10`
                : theme.colors?.backgroundLight || '#fafafa',
            color: isUser ? 'white' : theme.colors?.textPrimary || '#333',
            padding: '12px 16px',
            borderRadius: 16,
            borderTopRightRadius: isUser ? 4 : 16,
            borderTopLeftRadius: isUser ? 16 : 4,
            marginBottom: 6,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            position: 'relative',
            border: isError ? `1px solid ${theme.colors?.error || '#ff4d4f'}40` : 'none',
            wordBreak: 'break-word'
          }}>
            <Text style={{ 
              color: isUser ? 'white' : theme.colors?.textPrimary || '#333',
              fontSize: 14,
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap'
            }}>
              {message.content}
            </Text>
            
            {message.isQuickAction && (
              <Tag 
                size="small" 
                color="blue" 
                style={{ 
                  position: 'absolute', 
                  top: -8, 
                  right: 8,
                  fontSize: 10
                }}
              >
                Consulta Rápida
              </Tag>
            )}
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {message.timestamp.toLocaleTimeString()}
            </Text>
            {!isUser && (
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => handleCopyMessage(message.content)}
                style={{ fontSize: 10, padding: 0, height: 'auto' }}
              />
            )}
          </div>
          
          {/* Recomendaciones */}
          {message.recommendations && message.recommendations.length > 0 && (
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {message.recommendations.slice(0, 4).map((rec, index) => (
                <Tag
                  key={index}
                  style={{ 
                    cursor: 'pointer',
                    borderColor: theme.colors?.bmGreenLight,
                    color: theme.colors?.bmGreenPrimary,
                    fontSize: 11
                  }}
                  onClick={() => handleSuggestion(rec)}
                >
                  {rec}
                </Tag>
              ))}
            </div>
          )}
        </div>
        
        {isUser && (
          <Avatar 
            icon={<UserOutlined />} 
            style={{ 
              backgroundColor: theme.colors?.textSecondary || '#666',
              marginLeft: 12,
              flexShrink: 0
            }} 
            size="small"
          />
        )}
      </div>
    );
  };

  return (
    <Card
      className={className}
      style={{
        height: isExpanded ? '80vh' : '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'height 0.3s ease',
        ...style
      }}
      styles={{ 
        body: { 
          padding: 0, 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column' 
        } 
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space>
            <MessageOutlined style={{ color: theme.colors?.bmGreenPrimary }} />
            <Title level={5} style={{ margin: 0 }}>
              Chat CDG - Análisis General
            </Title>
            <Badge 
              count={scope === 'direccion' ? 'Corporativo' : 'Personal'} 
              style={{ backgroundColor: theme.colors?.bmGreenPrimary }} 
            />
          </Space>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tooltip title={isExpanded ? 'Contraer' : 'Expandir'}>
              <Button
                type="text"
                size="small"
                icon={isExpanded ? <CompressOutlined /> : <ExpandOutlined />}
                onClick={handleToggleExpansion}
              />
            </Tooltip>
            
            <Switch
              size="small"
              checked={useWebSocket}
              onChange={handleWebSocketToggle}
              checkedChildren={<WifiOutlined />}
              unCheckedChildren={<DisconnectOutlined />}
            />
            
            <Badge 
              status={
                connectionStatus === 'connected' ? 'success' :
                connectionStatus.includes('reconnecting') ? 'processing' :
                connectionStatus === 'http-ready' || connectionStatus === 'http-fallback' ? 'default' : 'error'
              }
              text={
                connectionStatus === 'connected' ? 'WS' :
                connectionStatus.includes('reconnecting') ? 'Recon' :
                connectionStatus === 'http-ready' || connectionStatus === 'http-fallback' ? 'HTTP' : 'Error'
              }
              style={{ fontSize: 10 }}
            />
          </div>
        </div>
      }
    >
      {/* ✅ Sugerencias rápidas */}
      {showSuggestions && activeSuggestions.length > 0 && (
        <div style={{ 
          padding: '16px 20px',
          backgroundColor: `${theme.colors?.bmGreenLight || '#52c41a'}08`,
          borderBottom: `1px solid ${theme.colors?.borderLight || '#f0f0f0'}`
        }}>
          <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Text strong style={{ fontSize: 12, color: theme.colors?.textSecondary }}>
              <ThunderboltOutlined style={{ marginRight: 4 }} />
              Consultas Sugeridas
            </Text>
            <Button 
              type="text" 
              size="small" 
              onClick={() => setShowSuggestions(false)}
              style={{ fontSize: 10, padding: 0 }}
            >
              Ocultar
            </Button>
          </div>
          <Space wrap size={[8, 8]}>
            {activeSuggestions.slice(0, 5).map((suggestion, index) => (
              <Button
                key={index}
                size="small"
                onClick={() => handleSuggestion(suggestion)}
                disabled={isSending}
                style={{
                  borderColor: theme.colors?.bmGreenPrimary,
                  color: theme.colors?.bmGreenPrimary,
                  fontSize: 11
                }}
              >
                {suggestion}
              </Button>
            ))}
          </Space>
        </div>
      )}

      {/* ✅ Área de mensajes */}
      <div 
        ref={messagesContainerRef}
        style={{ 
          flex: 1,
          padding: '20px',
          overflow: 'auto',
          backgroundColor: theme.colors?.backgroundLight || '#fafafa',
          maxHeight: isExpanded ? '60vh' : '400px',
          minHeight: '200px'
        }}
      >
        {messages.length === 0 ? (
          <Empty 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Inicia una conversación con el Agente CDG"
            style={{ marginTop: 40 }}
          />
        ) : (
          <>
            {messages.map(renderMessage)}
            {isTyping && (
              <div style={{ 
                display: 'flex', 
                justifyContent: 'flex-start', 
                marginBottom: 16,
                alignItems: 'center'
              }}>
                <Avatar 
                  icon={<RobotOutlined />} 
                  style={{ 
                    backgroundColor: theme.colors?.bmGreenPrimary,
                    marginRight: 12
                  }} 
                  size="small"
                />
                <div style={{
                  backgroundColor: theme.colors?.backgroundLight,
                  padding: '12px 16px',
                  borderRadius: 16,
                  borderTopLeftRadius: 4,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  <Spin 
                    indicator={<LoadingOutlined style={{ fontSize: 14 }} spin />} 
                    size="small" 
                  />
                  <Text style={{ fontSize: 14, color: theme.colors?.textSecondary }}>
                    Procesando consulta...
                  </Text>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} style={{ height: '1px' }} />
          </>
        )}
      </div>

      {/* ✅ Error */}
      {error && (
        <div style={{ padding: '0 20px 12px' }}>
          <Alert
            message={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
            action={
              <Space>
                <Button 
                  size="small" 
                  onClick={handleRetry} 
                  disabled={isSending}
                  icon={<ReloadOutlined />}
                >
                  Reintentar
                </Button>
                <Button 
                  size="small" 
                  onClick={handleReconnect}
                  type="primary"
                >
                  Reconectar
                </Button>
              </Space>
            }
          />
        </div>
      )}

      {/* ✅ Input de mensaje */}
      <div style={{ 
        padding: '16px 20px',
        backgroundColor: 'white',
        borderTop: `1px solid ${theme.colors?.borderLight || '#f0f0f0'}`
      }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <TextArea
            ref={inputRef}
            placeholder={`Consulta sobre ${scope === 'direccion' ? 'KPIs corporativos, rankings, análisis financieros...' : 'tu cartera, rendimiento, oportunidades...'}`}
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isSending}
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={isSending ? <LoadingOutlined spin /> : <SendOutlined />}
            onClick={handleSend}
            disabled={!currentMessage.trim() || isSending}
            style={{
              backgroundColor: theme.colors?.bmGreenPrimary,
              borderColor: theme.colors?.bmGreenPrimary,
              height: 32
            }}
            loading={isSending}
          >
            Enviar
          </Button>
        </div>
        
        <div style={{ 
          marginTop: 8, 
          fontSize: 11, 
          color: theme.colors?.textSecondary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span>
            <EyeOutlined style={{ marginRight: 4 }} />
            Enter para enviar • Shift+Enter para nueva línea
          </span>
          {periodo && (
            <Text type="secondary" style={{ fontSize: 10 }}>
              Contexto: {scope === 'direccion' ? 'Corporativo' : `Gestor ${gestorId}`} • {periodo}
            </Text>
          )}
        </div>
      </div>
    </Card>
  );
};

ChatInterface.propTypes = {
  scope: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.string,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  currentChartConfig: PropTypes.object,
  onNewChart: PropTypes.func,
  onCommand: PropTypes.func,
  suggestions: PropTypes.arrayOf(PropTypes.string),
  expanded: PropTypes.bool,
  className: PropTypes.string,
  style: PropTypes.object
};

export default ChatInterface;
