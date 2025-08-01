// src/components/Chat/ChatInterface.jsx
// Componente de interfaz de chat para interacción conversacional con el agente CDG

import React, { useState, useEffect, useRef } from 'react';
import { Input, Button, List, Typography, Spin, Tooltip, message as antdMessage } from 'antd';
import { SendOutlined, ReloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import InteractiveCharts from '../Dashboard/InteractiveCharts';
import theme from '../../styles/theme';

const { Text, Paragraph } = Typography;

// Mensaje individual en la interfaz de chat
const ChatMessageItem = ({ message }) => {
  const isUser = message.sender === 'user';

  return (
    <div style={{
      maxWidth: '75%',
      alignSelf: isUser ? 'flex-end' : 'flex-start',
      backgroundColor: isUser ? theme.colors.bmGreenPrimary : theme.colors.background,
      color: isUser ? '#fff' : theme.colors.textPrimary,
      borderRadius: 12,
      padding: '10px 16px',
      marginBottom: 12,
      boxShadow: isUser ? '0 2px 8px rgba(0,100,0,0.4)' : '0 2px 8px rgba(0,0,0,0.1)',
      wordWrap: 'break-word',
      whiteSpace: 'pre-wrap',
      fontSize: 14
    }}>
      <Paragraph style={{ margin: 0 }}>
        {message.text}
      </Paragraph>
      {/* Optionally render charts if any are present with the message */}
      {message.charts && message.charts.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {message.charts.map((chart, index) => (
            <div key={index} style={{ marginBottom: 16 }}>
              {/* Render the chart JSON for now. This will be replaced with actual chart rendering later */}
              <pre style={{
                backgroundColor: theme.colors.background,
                border: `1px solid ${theme.colors.border}`,
                padding: '8px',
                borderRadius: 6,
                overflowX: 'auto',
                fontSize: 12
              }}>{JSON.stringify(chart, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}
      {/* Render recommendations if any */}
      {message.recommendations && message.recommendations.length > 0 && (
        <div style={{ marginTop: 8, fontStyle: 'italic', color: theme.colors.bmGreenDark }}>
          <b>Recomendaciones:</b>
          <ul style={{ marginTop: 4 }}>
            {message.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
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
  }).isRequired
};

// Componente principal de chat
const ChatInterface = ({ userId, initialMessages = [], gestorId = null, periodo = null }) => {
  const [messages, setMessages] = useState(initialMessages);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom helper
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle sending message
  const sendMessage = async () => {
    if (!inputValue.trim()) {
      antdMessage.warning('Por favor, escribe un mensaje antes de enviar');
      return;
    }

    const newUserMessage = {
      sender: 'user',
      text: inputValue.trim(),
      charts: [],
      recommendations: []
    };

    setMessages((prev) => [...prev, newUserMessage]);
    setInputValue('');
    setIsSending(true);

    try {
      const response = await chatService.sendMessage(userId, newUserMessage.text, { gestorId, periodo });

      if (response.error) {
        antdMessage.error(`Error del agente: ${response.error}`);
      } else {
        const agentMessage = {
          sender: 'agent',
          text: response.response || 'Aquí está la información solicitada.',
          charts: response.charts || [],
          recommendations: response.recommendations || []
        };
        setMessages((prev) => [...prev, agentMessage]);
      }
    } catch (error) {
      antdMessage.error(`Error al comunicarse con el agente: ${error.message}`);
    } finally {
      setIsSending(false);
    }
  };

  // Handle Enter key in input
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSending) {
        sendMessage();
      }
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      maxHeight: '700px',
      border: `1px solid ${theme.colors.border}`,
      borderRadius: 8,
      padding: 16,
      backgroundColor: theme.colors.background
    }}>

      <div style={{
        flex: '1 1 auto',
        overflowY: 'auto',
        paddingRight: 12,
        marginBottom: 16
      }}>
        <List
          dataSource={messages}
          renderItem={msg => <ChatMessageItem key={msg.text + Math.random()} message={msg} />}
        />
        <div ref={messagesEndRef} />
      </div>

      <div style={{ display: 'flex', gap: 12 }}>

        <Input.TextArea
          value={inputValue}
          onChange={e => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder='Escribe tu pregunta o comando aquí...'
          rows={2}
          disabled={isSending}
          maxLength={1000}
        />

        <Button
          type='primary'
          icon={isSending ? <Spin size='small' /> : <SendOutlined />}
          onClick={sendMessage}
          disabled={isSending}
          style={{
            width: 60,
            height: 60,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          aria-label='Enviar mensaje'
        />
      </div>

    </div>
  );
};

ChatInterface.propTypes = {
  userId: PropTypes.string.isRequired,
  initialMessages: PropTypes.array,
  gestorId: PropTypes.string,
  periodo: PropTypes.string
};

export default ChatInterface;
