import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Spin } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import api from '../../services/api';

const SUGGESTIONS = [
  'Como cerraremos el ano?',
  'Que pasa si captamos 20% mas?',
  'Que deberiamos priorizar?',
  'Escenario pesimista detallado',
];

const ForecastChat = ({ mode = 'direccion', gestorId, perioBase = '2026-04' }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const send = async (text) => {
    if (!text?.trim()) return;
    const userMsg = text.trim();
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.forecast.chat({
        message: userMsg,
        user_role: mode === 'gestor' ? 'gestor' : 'control_gestion',
        gestor_id: gestorId || null,
        periodo_base: perioBase,
        session_id: `forecast_${mode}_${Date.now()}`,
      });
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: res.response || 'Sin respuesta del agente.',
        tools: res.tools_used || [],
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const cardStyle = {
    background: 'rgba(15,23,42,0.6)', borderRadius: 10,
    border: '1px solid rgba(255,255,255,0.06)',
    display: 'flex', flexDirection: 'column', height: '100%',
  };

  return (
    <div style={cardStyle}>
      {/* Header */}
      <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <span style={{ color: '#94A3B8', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Chat Proyecciones
        </span>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 10 }}>
            <span style={{ color: '#64748B', fontSize: 11, marginBottom: 4 }}>Prueba preguntar:</span>
            {SUGGESTIONS.map((s, i) => (
              <div key={i} onClick={() => send(s)}
                style={{
                  background: 'rgba(161,0,255,0.08)', border: '1px solid rgba(161,0,255,0.15)',
                  borderRadius: 8, padding: '6px 10px', cursor: 'pointer',
                  color: '#C4B5FD', fontSize: 12, transition: 'all 0.2s'
                }}
                onMouseEnter={e => e.target.style.background = 'rgba(161,0,255,0.15)'}
                onMouseLeave={e => e.target.style.background = 'rgba(161,0,255,0.08)'}
              >
                {s}
              </div>
            ))}
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '90%',
            background: m.role === 'user'
              ? 'linear-gradient(135deg, #A100FF, #7C3AED)'
              : 'rgba(30,42,56,0.8)',
            border: m.role === 'user' ? 'none' : '1px solid rgba(255,255,255,0.06)',
            borderRadius: m.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
            padding: '8px 12px', color: '#E2E8F0', fontSize: 13, lineHeight: 1.5,
            whiteSpace: 'pre-wrap',
          }}>
            {m.text}
          </div>
        ))}

        {loading && (
          <div style={{ alignSelf: 'flex-start', padding: '8px 12px' }}>
            <Spin size="small" />
            <span style={{ color: '#64748B', fontSize: 11, marginLeft: 8 }}>Analizando...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: '8px 12px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: 8 }}>
        <Input
          value={input} onChange={e => setInput(e.target.value)}
          onPressEnter={() => send(input)}
          placeholder="Pregunta sobre proyecciones..."
          disabled={loading}
          style={{
            background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(255,255,255,0.1)',
            color: '#E2E8F0', borderRadius: 8
          }}
        />
        <Button icon={<SendOutlined />} onClick={() => send(input)} loading={loading}
          style={{ background: '#A100FF', border: 'none', color: 'white', borderRadius: 8 }} />
      </div>
    </div>
  );
};

export default ForecastChat;
