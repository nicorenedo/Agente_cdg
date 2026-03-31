import React, { useState, useRef, useEffect } from 'react';
import { Input, Button, Spin } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import api from '../../services/api';

const SUGGESTIONS = [
  '¿Como cerraremos el ejercicio?',
  '¿Que ocurre si captamos 20% mas?',
  '¿Que deberiamos priorizar?',
  'Explica el escenario pesimista',
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
      setMessages(prev => [...prev, { role: 'assistant', text: res.response || 'Sin respuesta.' }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      background: 'rgba(15,23,42,.6)', borderRadius: 12,
      border: '1px solid rgba(255,255,255,.06)',
      display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 18px', borderBottom: '1px solid rgba(161,0,255,.15)',
        background: 'linear-gradient(135deg,rgba(161,0,255,.08),rgba(0,194,255,.04))',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{ position:'absolute',top:0,left:0,right:0,height:2,
          background:'linear-gradient(90deg,transparent,#A100FF,#00C2FF,transparent)',
          animation:'shimmer 3s infinite' }} />
        <div style={{ display:'flex',alignItems:'center',gap:10 }}>
          <div style={{ width:8,height:8,borderRadius:'50%',background:'#4ADE80',
            boxShadow:'0 0 8px #4ADE80',animation:'pulse 2s infinite' }} />
          <span style={{ color:'#E2E8F0',fontWeight:600,fontSize:14 }}>Agente de Proyecciones</span>
          <span style={{ fontSize:10,color:'#64748B',background:'rgba(255,255,255,.05)',
            padding:'2px 8px',borderRadius:10,marginLeft:'auto' }}>Prophet + GPT-4o</span>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} style={{ flex:1,overflowY:'auto',padding:'12px 14px',
        display:'flex',flexDirection:'column',gap:10 }}>
        {messages.length === 0 && (
          <div style={{ display:'flex',flexDirection:'column',gap:6,marginTop:12 }}>
            <span style={{ color:'#64748B',fontSize:11,marginBottom:4 }}>Pregunta sobre proyecciones:</span>
            {SUGGESTIONS.map((s, i) => (
              <div key={i} onClick={() => send(s)} style={{
                background:'rgba(161,0,255,.06)',border:'1px solid rgba(161,0,255,.15)',
                borderRadius:10,padding:'8px 12px',cursor:'pointer',
                color:'#C4B5FD',fontSize:12,transition:'all .2s',
              }}
              onMouseEnter={e => { e.currentTarget.style.background='rgba(161,0,255,.12)';
                e.currentTarget.style.borderColor='rgba(161,0,255,.3)'; }}
              onMouseLeave={e => { e.currentTarget.style.background='rgba(161,0,255,.06)';
                e.currentTarget.style.borderColor='rgba(161,0,255,.15)'; }}>
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
              ? 'linear-gradient(135deg,rgba(161,0,255,.3),rgba(0,194,255,.2))'
              : 'rgba(161,0,255,.06)',
            border: m.role === 'user'
              ? '1px solid rgba(0,194,255,.3)'
              : '1px solid rgba(161,0,255,.15)',
            borderRadius: m.role === 'user' ? '14px 4px 14px 14px' : '4px 14px 14px 14px',
            padding: '10px 14px', color: '#E2E8F0', fontSize: 13, lineHeight: 1.6,
            whiteSpace: 'pre-wrap', backdropFilter: 'blur(10px)',
            boxShadow: m.role === 'assistant' ? '0 4px 16px rgba(161,0,255,.08)' : 'none',
          }}>
            {m.text}
          </div>
        ))}
        {loading && (
          <div style={{ alignSelf:'flex-start',padding:'8px 12px',display:'flex',alignItems:'center',gap:8 }}>
            <Spin size="small" />
            <span style={{ color:'#64748B',fontSize:11 }}>Analizando...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding:'10px 14px',borderTop:'1px solid rgba(255,255,255,.06)',
        background:'rgba(0,0,0,.15)' }}>
        <div style={{ display:'flex',gap:8,alignItems:'center',
          background:'rgba(255,255,255,.03)',border:'1px solid rgba(161,0,255,.15)',
          borderRadius:10,padding:'6px 10px' }}>
          <Input value={input} onChange={e => setInput(e.target.value)}
            onPressEnter={() => send(input)} disabled={loading}
            placeholder="Pregunta sobre proyecciones..."
            style={{ background:'transparent',border:'none',color:'#E2E8F0',
              fontSize:13,boxShadow:'none' }} />
          <Button icon={<SendOutlined />} onClick={() => send(input)} loading={loading}
            shape="circle" style={{ background:'linear-gradient(135deg,#A100FF,#00C2FF)',
              border:'none',color:'white',minWidth:32,height:32 }} />
        </div>
      </div>
    </div>
  );
};

export default ForecastChat;
