// src/components/Chat/ChatInterface.jsx
// Interfaz de chat profesional v2.1 - Compatible con api.js v2.1 y chatService.js v2.1
// Integración completa con procesamiento inteligente automático

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Input, Button, Typography, Spin, message as antdMessage, Avatar, Card, Tooltip, Badge } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, ExclamationCircleOutlined, ClearOutlined, BulbOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import theme from '../../styles/theme';

const { Paragraph, Text } = Typography;

// ========================================
// 🎨 COMPONENTE DE MENSAJE INDIVIDUAL
// ========================================

const ChatMessageItem = ({ message, index }) => {
  const isUser = message.sender === 'user';
  const hasExtras = message.charts?.length > 0 || message.recommendations?.length > 0;

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      alignItems: 'flex-start',
      marginBottom: 16,
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
        maxWidth: '75%',
        backgroundColor: isUser ? theme.colors.bmGreenPrimary : theme.colors.background,
        color: isUser ? '#fff' : theme.colors.textPrimary,
        borderRadius: 12,
        padding: '12px 16px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        wordWrap: 'break-word',
        whiteSpace: 'pre-wrap',
        fontSize: 14,
        border: !isUser ? `1px solid ${theme.colors.border}` : 'none',
        position: 'relative'
      }}>
        {/* Badge para mensajes con extras */}
        {!isUser && hasExtras && (
          <Badge 
            count={<BulbOutlined style={{ color: theme.colors.bmGreenPrimary }} />}
            style={{ 
              position: 'absolute', 
              top: -4, 
              right: -4,
              backgroundColor: 'transparent'
            }}
          />
        )}

        <Paragraph 
          style={{ 
            margin: 0, 
            color: isUser ? '#fff' : theme.colors.textPrimary 
          }}
        >
          {message.text}
        </Paragraph>

        {/* Renderizar gráficos si los hay */}
        {message.charts && message.charts.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text strong style={{ color: isUser ? '#fff' : theme.colors.bmGreenDark }}>
              📊 Gráficos Generados ({message.charts.length}):
            </Text>
            {message.charts.map((chart, chartIndex) => (
              <Card 
                key={chartIndex} 
                size="small"
                style={{ 
                  marginTop: 8,
                  backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : theme.colors.backgroundLight 
                }}
              >
                <pre style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  padding: 0,
                  margin: 0,
                  overflow: 'auto',
                  fontSize: 12,
                  color: isUser ? '#fff' : theme.colors.textSecondary
                }}>
                  {typeof chart === 'string' ? chart : JSON.stringify(chart, null, 2)}
                </pre>
              </Card>
            ))}
          </div>
        )}

        {/* Renderizar recomendaciones si las hay */}
        {message.recommendations && message.recommendations.length > 0 && (
          <div style={{ 
            marginTop: 12, 
            padding: 8, 
            backgroundColor: isUser ? 'rgba(255,255,255,0.1)' : theme.colors.bmGreenLight + '20',
            borderRadius: 6,
            borderLeft: `3px solid ${isUser ? '#fff' : theme.colors.bmGreenPrimary}`
          }}>
            <Text strong style={{ color: isUser ? '#fff' : theme.colors.bmGreenDark }}>
              💡 Recomendaciones:
            </Text>
            <ul style={{ 
              marginTop: 4, 
              marginBottom: 0,
              paddingLeft: 20
            }}>
              {message.recommendations.map((rec, recIndex) => (
                <li 
                  key={recIndex}
                  style={{ 
                    color: isUser ? 'rgba(255,255,255,0.9)' : theme.colors.textPrimary,
                    marginBottom: 4
                  }}
                >
                  {rec}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Metadatos del procesamiento */}
        {message.metadata && message.metadata.processing_type && (
          <div style={{
            marginTop: 8,
            fontSize: 10,
            opacity: 0.6,
            textAlign: 'right',
            fontStyle: 'italic'
          }}>
            {message.metadata.processing_type === 'intelligent_success' ? '🧠 Procesamiento Inteligente' : '🔄 Procesamiento Estándar'}
          </div>
        )}

        {/* Timestamp del mensaje */}
        <div style={{ 
          marginTop: 8, 
          fontSize: 11, 
          opacity: 0.7,
          textAlign: isUser ? 'right' : 'left'
        }}>
          {message.timestamp ? new Date(message.timestamp).toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }) : ''}
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
};

ChatMessageItem.propTypes = {
  message: PropTypes.shape({
    sender: PropTypes.oneOf(['user', 'agent']).isRequired,
    text: PropTypes.string.isRequired,
    charts: PropTypes.array,
    recommendations: PropTypes.array,
    metadata: PropTypes.object,
    timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)])
  }).isRequired,
  index: PropTypes.number.isRequired
};

// ========================================
// 🎯 COMPONENTE PRINCIPAL DE CHAT
// ========================================

const ChatInterface = ({ 
  userId = 'frontend_user', 
  initialMessages = [], 
  gestorId = null, 
  periodo = null,
  height = '500px' 
}) => {
  const [messages, setMessages] = useState(initialMessages);
  const [inputMessage, setInputMessage] = useState(''); // ✅ CORREGIDO: Variable correcta
  const [isSending, setIsSending] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);

  // ========================================
  // 🔧 INICIALIZACIÓN Y CONFIGURACIÓN
  // ========================================

  // Configurar usuario en chatService al montar
  useEffect(() => {
    if (userId) {
      chatService.setCurrentUserId(userId);
      console.log(`🆔 Usuario configurado en ChatInterface: ${userId}`);
    }
  }, [userId]);

  // Cargar sugerencias personalizadas
  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const suggestionsData = await chatService.getChatSuggestions();
        setSuggestions(suggestionsData.suggestions || []);
      } catch (error) {
        console.warn('No se pudieron cargar sugerencias:', error);
      }
    };
    
    if (isConnected && messages.length === 0) {
      loadSuggestions();
    }
  }, [isConnected, messages.length]);

  // Scroll automático optimizado
  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Verificar conexión con el servicio
  useEffect(() => {
    const checkConnection = async () => {
      try {
        setConnectionStatus('checking');
        const isAvailable = await chatService.isServiceAvailable();
        setIsConnected(isAvailable);
        setConnectionStatus(isAvailable ? 'connected' : 'disconnected');
      } catch (error) {
        console.warn('Chat service no disponible:', error);
        setIsConnected(false);
        setConnectionStatus('error');
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  // ========================================
  // 💬 FUNCIONALIDADES DE CHAT
  // ========================================

  // ✅ CORREGIDO: Manejo de envío de mensaje
  const sendMessage = useCallback(async () => {
    const messageText = inputMessage.trim(); // ✅ USAR LA VARIABLE CORRECTA
    
    if (!messageText) {
      antdMessage.warning('Por favor, escribe un mensaje antes de enviar');
      return;
    }

    if (!isConnected) {
      antdMessage.error('No hay conexión con el servicio de chat');
      return;
    }

    // Crear mensaje del usuario
    const userMessage = {
      sender: 'user',
      text: messageText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage(''); // ✅ LIMPIAR EL INPUT CORRECTAMENTE
    setIsSending(true);

    try {
      // ✅ CORREGIDO: Llamada correcta a chatService.sendMessage
      const options = {
        gestorId,
        periodo,
        includeCharts: true,
        includeRecommendations: true,
        context: {
          previousMessages: messages.slice(-3),
          currentView: gestorId ? 'gestor' : 'direccion',
          sessionInfo: {
            gestorId,
            periodo,
            timestamp: new Date().toISOString()
          }
        }
      };

      console.log('🚀 Enviando mensaje:', messageText, 'con opciones:', options);

      // ✅ PARÁMETROS CORRECTOS: solo (message, options)
      const response = await chatService.sendMessage(messageText, options);

      console.log('✅ Respuesta recibida:', response);

      // Procesar respuesta del agente
      const agentMessage = {
        sender: 'agent',
        text: response.response || '✅ He procesado tu solicitud correctamente.',
        charts: response.charts || [],
        recommendations: response.recommendations || [],
        metadata: {
          processing_type: response.serviceMetadata?.processingType || 'unknown',
          confidence: response.confidence_score,
          execution_time: response.execution_time
        },
        timestamp: new Date()
      };

      setMessages(prev => [...prev, agentMessage]);

      // Notificaciones de éxito
      if (response.charts?.length > 0 || response.recommendations?.length > 0) {
        antdMessage.success('Consulta procesada con información adicional');
      }

    } catch (error) {
      console.error('❌ Error enviando mensaje:', error);
      
      const errorMessage = {
        sender: 'agent',
        text: '🔌 Lo siento, hay un problema de conexión. Por favor, verifica tu conexión e inténtalo nuevamente.',
        recommendations: [
          'Verifica tu conexión a internet',
          'Recarga la página si el problema persiste',
          'El servicio puede estar temporalmente caído'
        ],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
      setIsConnected(false);
      setConnectionStatus('error');
      antdMessage.error('Error de conexión con el servicio de chat');
    } finally {
      setIsSending(false);
    }
  }, [inputMessage, isConnected, gestorId, periodo, messages]);

  // Manejar tecla Enter
  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSending && isConnected) {
        sendMessage();
      }
    }
  }, [isSending, isConnected, sendMessage]);

  // Usar sugerencia
  const handleSuggestion = useCallback((suggestion) => {
    setInputMessage(suggestion);
    setTimeout(() => {
      sendMessage();
    }, 100);
  }, [sendMessage]);

  // Limpiar chat
  const clearChat = useCallback(async () => {
    try {
      await chatService.resetChatSession();
      setMessages([]);
      antdMessage.success('💬 Chat reiniciado exitosamente');
    } catch (error) {
      console.warn('Error reiniciando chat:', error);
      setMessages([]);
      antdMessage.success('💬 Chat limpiado localmente');
    }
  }, []);

  // Estado de conexión
  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'checking': return 'Verificando conexión...';
      case 'connected': return `🟢 Conectado${gestorId ? ` - Gestor ${gestorId}` : ' - Vista Dirección'}${periodo ? ` - ${periodo}` : ''}`;
      case 'disconnected': return '🔴 Sin conexión con el servicio';
      case 'error': return '⚠️ Error de conexión';
      default: return 'Estado desconocido';
    }
  };

  // ========================================
  // 🎨 RENDERIZADO DEL COMPONENTE
  // ========================================

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: height,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: 8,
      backgroundColor: theme.colors.background,
      overflow: 'hidden'
    }}>
      
      {/* Header del chat */}
      <div style={{
        padding: '12px 16px',
        borderBottom: `1px solid ${theme.colors.border}`,
        backgroundColor: isConnected ? theme.colors.bmGreenPrimary : theme.colors.textSecondary,
        color: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ fontSize: 16 }} />
          <Text strong style={{ color: '#fff', margin: 0 }}>
            Asistente CDG v2.1
          </Text>
          {!isConnected && (
            <Tooltip title="Sin conexión con el servicio">
              <ExclamationCircleOutlined 
                style={{ color: '#ff4d4f', fontSize: 14 }} 
              />
            </Tooltip>
          )}
        </div>
        
        <Tooltip title="Reiniciar conversación">
          <Button 
            type="text" 
            size="small" 
            icon={<ClearOutlined />}
            onClick={clearChat}
            disabled={isSending}
            style={{ color: '#fff', padding: '4px 8px' }}
          />
        </Tooltip>
      </div>

      {/* Área de mensajes */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        backgroundColor: theme.colors.backgroundLight
      }}>
        {messages.length === 0 ? (
          <div style={{
            textAlign: 'center',
            color: theme.colors.textSecondary,
            marginTop: '10%'
          }}>
            <RobotOutlined style={{ fontSize: 32, marginBottom: 8 }} />
            <div style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 4 }}>
              ¡Hola! Soy tu asistente de Control de Gestión
            </div>
            <div style={{ fontSize: 14, marginBottom: 16 }}>
              Pregúntame sobre KPIs, análisis financieros o cualquier dato que necesites.
            </div>

            {/* Sugerencias */}
            {suggestions.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text strong style={{ marginBottom: 8, display: 'block' }}>
                  💡 Sugerencias:
                </Text>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
                  {suggestions.slice(0, 3).map((suggestion, index) => (
                    <Button
                      key={index}
                      size="small"
                      type="dashed"
                      onClick={() => handleSuggestion(suggestion)}
                      style={{
                        borderColor: theme.colors.bmGreenPrimary,
                        color: theme.colors.bmGreenPrimary
                      }}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <ChatMessageItem 
                key={`${message.timestamp || Date.now()}-${index}`} 
                message={message} 
                index={index}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Área de entrada */}
      <div style={{
        padding: '12px 16px',
        borderTop: `1px solid ${theme.colors.border}`,
        backgroundColor: theme.colors.background
      }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <Input.TextArea
            value={inputMessage} // ✅ CORREGIDO: Variable correcta
            onChange={(e) => setInputMessage(e.target.value)} // ✅ CORREGIDO: Setter correcto
            onPressEnter={handleKeyPress}
            placeholder={
              isConnected 
                ? 'Pregunta sobre KPIs, análisis, gestores, centros...' 
                : 'Servicio de chat no disponible'
            }
            rows={2}
            disabled={isSending || !isConnected}
            maxLength={1000}
            showCount
            style={{
              borderRadius: 6,
              borderColor: theme.colors.border
            }}
          />

          <Tooltip title={isSending ? 'Enviando...' : 'Enviar mensaje'}>
            <Button
              type="primary"
              icon={isSending ? <Spin size="small" /> : <SendOutlined />}
              onClick={sendMessage}
              disabled={isSending || !isConnected || !inputMessage.trim()} // ✅ CORREGIDO: Variable correcta
              style={{
                height: 60,
                width: 60,
                borderRadius: 6,
                backgroundColor: isConnected ? theme.colors.bmGreenPrimary : theme.colors.textSecondary,
                borderColor: isConnected ? theme.colors.bmGreenPrimary : theme.colors.textSecondary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            />
          </Tooltip>
        </div>

        {/* Estado de conexión */}
        <div style={{
          marginTop: 6,
          fontSize: 11,
          color: isConnected ? theme.colors.textSecondary : theme.colors.error,
          textAlign: 'center',
          fontWeight: !isConnected ? 'bold' : 'normal'
        }}>
          {getConnectionStatusText()}
        </div>
      </div>
    </div>
  );
};

ChatInterface.propTypes = {
  userId: PropTypes.string,
  initialMessages: PropTypes.array,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  height: PropTypes.string
};

export default ChatInterface;
