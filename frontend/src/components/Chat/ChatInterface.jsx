// src/components/Chat/ChatInterface.jsx
// Componente de interfaz de chat - CORREGIDO para chatService actualizado

import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, Typography, Spin, message as antdMessage, Avatar, Card } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import theme from '../../styles/theme';

const { Paragraph, Text } = Typography;

// Mensaje individual en la interfaz de chat
const ChatMessageItem = ({ message, index }) => {
  const isUser = message.sender === 'user';

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
        border: !isUser ? `1px solid ${theme.colors.border}` : 'none'
      }}>
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
              Gráficos:
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
                  {JSON.stringify(chart, null, 2)}
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
              Recomendaciones:
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

        {/* Timestamp del mensaje */}
        <div style={{ 
          marginTop: 8, 
          fontSize: 11, 
          opacity: 0.7,
          textAlign: isUser ? 'right' : 'left'
        }}>
          {new Date().toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
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
    recommendations: PropTypes.array
  }).isRequired,
  index: PropTypes.number.isRequired
};

// ✅ CORREGIDO: Componente principal de chat con integración mejorada
const ChatInterface = ({ 
  userId, 
  initialMessages = [], 
  gestorId = null, 
  periodo = null,
  height = '500px' 
}) => {
  const [messages, setMessages] = useState(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const messagesEndRef = useRef(null);

  // Scroll automático al final
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ✅ CORREGIDO: Verificar conexión con el servicio de chat
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const isAvailable = await chatService.isServiceAvailable();
        setIsConnected(isAvailable);
      } catch (error) {
        console.warn('Chat service not available:', error);
        setIsConnected(false);
      }
    };

    if (userId) {
      checkConnection();
    }
  }, [userId]);

  // ✅ CORREGIDO: Manejar envío de mensaje con estructura actualizada
  const sendMessage = async () => {
    if (!inputValue.trim()) {
      antdMessage.warning('Por favor, escribe un mensaje antes de enviar');
      return;
    }

    const newUserMessage = {
      sender: 'user',
      text: inputValue.trim(),
      charts: [],
      recommendations: [],
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setInputValue('');
    setIsSending(true);

    try {
      // ✅ CORREGIDO: Usar estructura de opciones actualizada del chatService
      const response = await chatService.sendMessage(
        userId, 
        newUserMessage.text, 
        { 
          gestorId, 
          periodo,
          includeCharts: true,
          includeRecommendations: true,
          context: {
            previousMessages: messages.slice(-5), // Últimos 5 mensajes para contexto
            currentView: gestorId ? 'gestor' : 'direccion'
          }
        }
      );

      if (response.error) {
        antdMessage.error(`Error del agente: ${response.error}`);
        
        // Mensaje de error para el usuario
        const errorMessage = {
          sender: 'agent',
          text: response.response || `Lo siento, ha ocurrido un error: ${response.error}. Por favor, inténtalo de nuevo.`,
          charts: response.charts || [],
          recommendations: response.recommendations || ['Intenta reformular tu pregunta', 'Verifica tu conexión', 'Contacta al soporte si persiste'],
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      } else {
        const agentMessage = {
          sender: 'agent',
          text: response.response || 'He procesado tu solicitud. ¿Hay algo más en lo que pueda ayudarte?',
          charts: response.charts || [],
          recommendations: response.recommendations || [],
          timestamp: new Date()
        };
        setMessages(prev => [...prev, agentMessage]);
      }
    } catch (error) {
      console.error('Error en chat:', error);
      antdMessage.error(`Error de conexión con el chat`);
      
      // Mensaje de error de conexión
      const connectionErrorMessage = {
        sender: 'agent',
        text: 'Lo siento, hay un problema de conexión con el sistema. Por favor, verifica tu conexión e inténtalo nuevamente.',
        charts: [],
        recommendations: ['Verifica tu conexión a internet', 'Recarga la página si el problema persiste', 'Contacta al soporte técnico si continúa el error'],
        timestamp: new Date()
      };
      setMessages(prev => [...prev, connectionErrorMessage]);
      setIsConnected(false);
    } finally {
      setIsSending(false);
    }
  };

  // Manejar tecla Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSending && isConnected) {
        sendMessage();
      }
    }
  };

  // Limpiar chat
  const clearChat = () => {
    setMessages(initialMessages);
    antdMessage.success('Chat limpiado');
  };

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
        backgroundColor: theme.colors.bmGreenPrimary,
        color: '#fff',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <RobotOutlined style={{ fontSize: 16 }} />
          <Text strong style={{ color: '#fff', margin: 0 }}>
            Asistente CDG
          </Text>
          {!isConnected && (
            <ExclamationCircleOutlined 
              style={{ color: '#ff4d4f', fontSize: 14 }} 
              title="Sin conexión"
            />
          )}
        </div>
        
        <Button 
          type="text" 
          size="small" 
          onClick={clearChat}
          style={{ color: '#fff', padding: '4px 8px' }}
        >
          Limpiar
        </Button>
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
            marginTop: '20%'
          }}>
            <RobotOutlined style={{ fontSize: 32, marginBottom: 8 }} />
            <div>¡Hola! Soy tu asistente de Control de Gestión.</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>
              Pregúntame sobre KPIs, análisis o cualquier dato que necesites.
            </div>
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
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onPressEnter={handleKeyPress}
            placeholder={
              isConnected 
                ? 'Escribe tu pregunta sobre CDG aquí...' 
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

          <Button
            type="primary"
            icon={isSending ? <Spin size="small" /> : <SendOutlined />}
            onClick={sendMessage}
            disabled={isSending || !isConnected || !inputValue.trim()}
            style={{
              height: 60,
              width: 60,
              borderRadius: 6,
              backgroundColor: theme.colors.bmGreenPrimary,
              borderColor: theme.colors.bmGreenPrimary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Enviar mensaje"
          />
        </div>

        {/* Estado de conexión */}
        <div style={{
          marginTop: 4,
          fontSize: 11,
          color: theme.colors.textSecondary,
          textAlign: 'center'
        }}>
          {isConnected ? (
            `Conectado - ${gestorId ? `Gestor ${gestorId}` : 'Vista Dirección'} - ${periodo || 'Período actual'}`
          ) : (
            'Sin conexión con el servicio de chat'
          )}
        </div>
      </div>
    </div>
  );
};

ChatInterface.propTypes = {
  userId: PropTypes.string.isRequired,
  initialMessages: PropTypes.array,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  height: PropTypes.string
};

export default ChatInterface;
