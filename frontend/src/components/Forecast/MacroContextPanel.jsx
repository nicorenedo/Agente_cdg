import React, { useEffect, useState } from 'react';
import { Skeleton, Tag } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
import api from '../../services/api';

const IMPACT_COLOR = {
  POSITIVO: 'green', MODERADO_POSITIVO: 'cyan', NEUTRAL: 'default', NEGATIVO: 'red'
};

const TrendIcon = ({ trend }) => {
  if (trend === 'alcista') return <ArrowUpOutlined style={{ color: '#FF6B6B', fontSize: 10 }} />;
  if (trend === 'bajista') return <ArrowDownOutlined style={{ color: '#4ADE80', fontSize: 10 }} />;
  return <MinusOutlined style={{ color: '#94A3B8', fontSize: 10 }} />;
};

const MacroContextPanel = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.forecast.macro().then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  const cardStyle = {
    background: 'rgba(15,23,42,0.6)', borderRadius: 10,
    border: '1px solid rgba(255,255,255,0.06)', padding: 14
  };

  if (loading) return <div style={cardStyle}><Skeleton active paragraph={{ rows: 4 }} /></div>;
  if (!data) return (
    <div style={cardStyle}>
      <span style={{ color: '#64748B', fontSize: 12 }}>Contexto macro no disponible</span>
    </div>
  );

  return (
    <div style={cardStyle}>
      <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 600, marginBottom: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>
        Contexto Macro
      </div>

      {/* Tipos hipotecarios */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ color: '#94A3B8', fontSize: 11 }}>Tipos hipotecarios</span>
          <span style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 15 }}>
            {data.tipos_hipotecas_pct}% <TrendIcon trend={data.tipos_hipotecas_tendencia} />
          </span>
        </div>
        <span style={{ color: '#475569', fontSize: 10 }}>{data.fuente_tipos}</span>
      </div>

      {/* IPC */}
      <div style={{ marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ color: '#94A3B8', fontSize: 11 }}>IPC España</span>
          <span style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 15 }}>
            {data.ipc_spain_pct}% <TrendIcon trend={data.ipc_tendencia} />
          </span>
        </div>
        <span style={{ color: '#475569', fontSize: 10 }}>{data.fuente_ipc}</span>
      </div>

      {/* Impacto por producto */}
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
        <Tag color={IMPACT_COLOR[data.impacto_hipotecario] || 'default'} style={{ fontSize: 10 }}>
          Hip: {(data.impacto_hipotecario || '').replace(/_/g, ' ')}
        </Tag>
        <Tag color={IMPACT_COLOR[data.impacto_depositos] || 'default'} style={{ fontSize: 10 }}>
          Dep: {data.impacto_depositos}
        </Tag>
        <Tag color={IMPACT_COLOR[data.impacto_frv] || 'default'} style={{ fontSize: 10 }}>
          FRV: {data.impacto_frv}
        </Tag>
      </div>

      {/* Narrativa */}
      <div style={{ color: '#64748B', fontSize: 11, lineHeight: 1.4 }}>
        {data.narrativa_corta}
      </div>
    </div>
  );
};

export default MacroContextPanel;
