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
  Empty
} from 'antd';
import { 
  SendOutlined, 
  RobotOutlined, 
  UserOutlined, 
  MessageOutlined,
  LoadingOutlined,
  ThunderboltOutlined,
  ClearOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import theme from '../../styles/theme';

const { TextArea } = Input;
const { Text } = Typography;

/**
 * ✅ ConversationalPivot - Chat Simple para Pivoteo de Gráficos
 * 
 * FUNCIONALIDADES:
 * 1. Chat simple que se conecta a chatService
 * 2. Solo modifica el gráfico de "Análisis General" (unified chart)
 * 3. No toca el gráfico de precios para simplicidad
 * 4. Se integra como panel lateral junto a InteractiveCharts
 * 5. Funciona en modo dirección y gestor
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
  
  // ✅ ESTADOS PRINCIPALES
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  // ✅ USER ID ÚNICO POR MODO
  const userId = React.useMemo(() => {
    const baseUserId = gestorId ? String(gestorId) : 'anonymous';
    return mode === 'direccion' ? `direction_${baseUserId}` : `gestor_${baseUserId}`;
  }, [mode, gestorId]);

  const chatSessionRef = useRef(null);
  const messagesEndRef = useRef(null);

  // ✅ SCROLL AUTOMÁTICO
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // ✅ INICIALIZAR CHAT SESSION
  useEffect(() => {
    console.log(`[ConversationalPivot] Initializing chat for userId: ${userId}`);

    // Crear sesión de chat
    chatSessionRef.current = chatService.createChatSession(userId, {
      onOpen: () => {
        console.log('[ConversationalPivot] ✅ WebSocket connected');
        setIsConnected(true);
        
        // Mensaje de bienvenida
        const welcomeMsg = {
          id: Date.now(),
          sender: 'assistant',
          text: `¡Hola! Soy tu asistente para cambiar gráficos. Puedo ayudarte a modificar el gráfico de análisis general usando lenguaje natural.

Ejemplos:
• "Cambia a barras horizontales"
• "Muestra como gráfico circular"
• "Convierte a formato de líneas"
• "Cambiar métrica a MARGEN"

Solo modifico el gráfico de análisis general, no el de precios.`,
          timestamp: new Date().toLocaleTimeString(),
          isWelcome: true
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
      },
      onMessage: (wsMessage) => {
        console.log('[ConversationalPivot] 📨 Received WebSocket message:', wsMessage);
        
        if (wsMessage.text) {
          const assistantMessage = {
            id: Date.now(),
            sender: 'assistant',
            text: wsMessage.text,
            timestamp: new Date().toLocaleTimeString(),
            source: 'websocket'
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
        
        // ✅ ACTUALIZAR GRÁFICO SOLO SI ES EL ANÁLISIS GENERAL
        if (wsMessage.charts && wsMessage.charts.length > 0) {
          const unifiedChart = wsMessage.charts.find(chart => 
            chart.meta?.type === 'unified' || 
            chart.meta?.chart_id === 'unified' ||
            !chart.meta?.type // Asumir que es el gráfico principal si no especifica
          );
          
          if (unifiedChart && onChartUpdate) {
            console.log('[ConversationalPivot] 🔄 Updating unified chart');
            onChartUpdate(unifiedChart);
          }
        }
      }
    });

    // Conectar WebSocket
    chatSessionRef.current.connect();

    return () => {
      if (chatSessionRef.current) {
        chatSessionRef.current.close();
      }
    };
  }, [userId, onChartUpdate]);

  // ✅ ENVIAR MENSAJE
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

    try {
      console.log(`[ConversationalPivot] 📤 Sending message: "${inputMessage}"`);
      
      // ✅ PREPARAR CONTEXTO
      const context = {
        mode,
        gestorId: gestorId ? String(gestorId) : undefined,
        periodo: periodo ? String(periodo) : undefined,
        currentChartConfig: currentChartConfig || {},
        chartTarget: 'unified', // Solo modificar gráfico de análisis general
        intent: 'chart_modification'
      };

      // ✅ ENVIAR VIA WEBSOCKET PRIMERO
      if (isConnected && chatSessionRef.current) {
        chatSessionRef.current.send({
          message: inputMessage,
          context
        });
      } else {
        // ✅ FALLBACK HTTP
        console.log('[ConversationalPivot] 📡 Using HTTP fallback');
        const response = await chatService.http.sendMessage({
          user_id: userId,
          message: inputMessage,
          gestor_id: gestorId ? String(gestorId) : undefined,
          periodo: periodo ? String(periodo) : undefined,
          include_charts: true,
          include_recommendations: false,
          context,
          current_chart_config: currentChartConfig || {},
          chart_interaction_type: 'pivot',
          use_basic_queries: true,
          quick_mode: true
        });

        if (response.text) {
          const assistantMessage = {
            id: Date.now() + 1,
            sender: 'assistant',
            text: response.text,
            timestamp: new Date().toLocaleTimeString(),
            source: 'http'
          };
          setMessages(prev => [...prev, assistantMessage]);
        }

        // ✅ ACTUALIZAR GRÁFICO VIA HTTP
        if (response.charts && response.charts.length > 0) {
          const unifiedChart = response.charts.find(chart => 
            chart.meta?.type === 'unified' || 
            !chart.meta?.type
          );
          
          if (unifiedChart && onChartUpdate) {
            console.log('[ConversationalPivot] 🔄 Updating chart via HTTP');
            onChartUpdate(unifiedChart);
          }
        }
      }

      notification.success({
        message: 'Mensaje enviado',
        description: 'Procesando tu solicitud...',
        duration: 2
      });

    } catch (error) {
      console.error('[ConversationalPivot] ❌ Error sending message:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: `❌ Error: ${error.message || 'No se pudo procesar tu solicitud'}. Intenta reformular tu mensaje.`,
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
      
      notification.error({
        message: 'Error al enviar mensaje',
        description: error.message || 'Error desconocido',
        duration: 4
      });
    } finally {
      setIsLoading(false);
      setInputMessage('');
    }
  }, [inputMessage, isLoading, isConnected, userId, mode, gestorId, periodo, currentChartConfig, onChartUpdate]);

  // ✅ MANEJAR ENTER
  const handleKeyPress = useCallback((event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  }, [handleSendMessage]);

  // ✅ LIMPIAR CHAT
  const handleClearChat = useCallback(async () => {
    try {
      if (chatSessionRef.current) {
        await chatSessionRef.current.reset();
      }
      setMessages([]);
    } catch (error) {
      console.warn('[ConversationalPivot] Error clearing chat:', error);
      setMessages([]);
    }
  }, []);

  // ✅ SUGERENCIAS RÁPIDAS
  const quickSuggestions = [
    "Cambia a barras horizontales",
    "Muestra como gráfico circular",
    "Convierte a líneas",
    "Cambiar métrica a MARGEN"
  ];

  const handleUseSuggestion = useCallback((suggestion) => {
    setInputMessage(suggestion);
  }, []);

  // ✅ RENDERIZADO
  return (
    <Card
      className={className}
      style={{
        width: 350,
        height: 500,
        display: 'flex',
        flexDirection: 'column',
        ...style
      }}
      title={
        <Space>
          <Avatar 
            icon={<RobotOutlined />} 
            style={{ 
              backgroundColor: isConnected ? '#52c41a' : '#ff4d4f'
            }} 
            size="small"
          />
          <Text strong>Chat Pivoteo</Text>
          <Tag color={isConnected ? 'green' : 'red'} size="small">
            {isConnected ? 'Conectado' : 'Desconectado'}
          </Tag>
        </Space>
      }
      extra={
        <Button 
          size="small" 
          icon={<ClearOutlined />} 
          onClick={handleClearChat}
          type="text"
        >
          Limpiar
        </Button>
      }
      bodyStyle={{ 
        padding: 0, 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column' 
      }}
    >
      {/* ✅ ÁREA DE MENSAJES */}
      <div 
        style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '16px', 
          backgroundColor: '#fafafa',
          minHeight: 300
        }}
      >
        {messages.length === 0 ? (
          <Empty 
            image={<MessageOutlined style={{ fontSize: 32, color: '#ccc' }} />}
            description={
              <div>
                <div style={{ marginBottom: 8 }}>
                  <Text type="secondary">¡Hola! Escribe un mensaje para cambiar el gráfico</Text>
                </div>
                <div style={{ marginBottom: 16 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Solo modifico el gráfico de análisis general
                  </Text>
                </div>
                {currentChartConfig ? (
                  <Tag color="green" size="small">✅ Gráfico detectado</Tag>
                ) : (
                  <Tag color="orange" size="small">⚠️ Sin gráfico activo</Tag>
                )}
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
                    backgroundColor: message.isError ? '#ff4d4f' : '#1890ff',
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
                    (message.isError ? '#fff2f0' : '#f0f0f0'),
                  color: message.sender === 'user' ? 'white' : '#333',
                  wordBreak: 'break-word',
                  border: message.isError ? '1px solid #ffccc7' : 'none',
                  whiteSpace: 'pre-wrap'
                }}
              >
                {message.text}
                
                {message.isWelcome && (
                  <div style={{ marginTop: 12 }}>
                    <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, color: '#666' }}>
                      Prueba estas sugerencias:
                    </Text>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {quickSuggestions.slice(0, 2).map((suggestion, index) => (
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
                  textAlign: message.sender === 'user' ? 'right' : 'left'
                }}>
                  {message.timestamp}
                  {message.source && ` • ${message.source}`}
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
        
        {/* ✅ INDICADOR DE CARGA */}
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
                marginTop: 4
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
                <span style={{ fontSize: 12 }}>Procesando...</span>
              </Space>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* ✅ SUGERENCIAS RÁPIDAS (solo si no hay mensajes) */}
      {messages.length <= 1 && (
        <div style={{ padding: '8px 16px', borderTop: '1px solid #f0f0f0' }}>
          <Text strong style={{ fontSize: 11, display: 'block', marginBottom: 8, color: '#666' }}>
            <ThunderboltOutlined /> Sugerencias rápidas:
          </Text>
          <Space wrap>
            {quickSuggestions.map((suggestion, index) => (
              <Button
                key={index}
                size="small"
                type="dashed"
                onClick={() => handleUseSuggestion(suggestion)}
                style={{ fontSize: 11 }}
              >
                {suggestion}
              </Button>
            ))}
          </Space>
        </div>
      )}

      {/* ✅ ÁREA DE INPUT */}
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
            placeholder="Escribe tu solicitud para cambiar el gráfico..."
            autoSize={{ minRows: 1, maxRows: 2 }}
            disabled={isLoading}
            maxLength={300}
            style={{ 
              borderRadius: '6px 0 0 6px',
              resize: 'none'
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
              backgroundColor: theme.colors?.bmGreenPrimary || '#1890ff',
              borderColor: theme.colors?.bmGreenPrimary || '#1890ff'
            }}
          >
            Enviar
          </Button>
        </Space.Compact>

        {/* ✅ ESTADO DE CONEXIÓN */}
        <div style={{ marginTop: 8, textAlign: 'center' }}>
          <Text type="secondary" style={{ fontSize: 11 }}>
            Enter para enviar • Solo modifica gráfico de análisis general
          </Text>
        </div>
      </div>

      {/* ✅ ALERT DE ESTADO DEL GRÁFICO */}
      {!currentChartConfig && (
        <Alert
          message="Sin gráfico activo"
          description="Asegúrate de que InteractiveCharts esté visible para usar el pivoteo"
          type="warning"
          showIcon
          style={{ margin: '8px 16px 16px 16px', fontSize: 11 }}
        />
      )}
    </Card>
  );
};

// ✅ PROP TYPES
ConversationalPivot.propTypes = {
  mode: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  periodo: PropTypes.string,
  currentChartConfig: PropTypes.object,
  onChartUpdate: PropTypes.func.isRequired,
  className: PropTypes.string,
  style: PropTypes.object
};

export default ConversationalPivot;
