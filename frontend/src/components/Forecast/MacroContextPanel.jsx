import React, { useEffect, useState } from 'react';
import { Skeleton } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';
import api from '../../services/api';

const IMPACT_STYLE = {
  POSITIVO:          { bg: 'rgba(74,222,128,.06)', border: 'rgba(74,222,128,.25)', text: '#4ADE80' },
  MODERADO_POSITIVO: { bg: 'rgba(0,194,255,.06)',  border: 'rgba(0,194,255,.25)',  text: '#00C2FF' },
  NEUTRAL:           { bg: 'rgba(148,163,184,.04)',border: 'rgba(148,163,184,.15)',text: '#94A3B8' },
  NEGATIVO:          { bg: 'rgba(255,107,107,.06)',border: 'rgba(255,107,107,.25)',text: '#FF6B6B' },
};

const TrendIcon = ({ trend }) => {
  if (trend === 'alcista') return <ArrowUpOutlined style={{ color: '#FF6B6B', fontSize: 11 }} />;
  if (trend === 'bajista') return <ArrowDownOutlined style={{ color: '#4ADE80', fontSize: 11 }} />;
  return <MinusOutlined style={{ color: '#64748B', fontSize: 11 }} />;
};

const MacroIndicator = ({ label, value, unit, trend, fuente, color }) => (
  <div style={{
    background: 'rgba(255,255,255,.02)', border: `1px solid ${color}22`,
    borderRadius: 10, padding: '10px 14px', marginBottom: 8, position: 'relative', overflow: 'hidden',
  }}>
    <div style={{ position:'absolute',top:0,right:0,width:50,height:50,
      background:`radial-gradient(circle,${color}12,transparent 70%)`,borderRadius:'0 10px 0 0' }} />
    <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start' }}>
      <div>
        <div style={{ fontSize:11,color:'#64748B',marginBottom:3 }}>{label}</div>
        <div style={{ fontSize:20,fontWeight:700,color,letterSpacing:'-.5px' }}>{value}{unit}</div>
      </div>
      <TrendIcon trend={trend} />
    </div>
    <div style={{ marginTop:6,height:2,background:'rgba(255,255,255,.05)',borderRadius:1 }}>
      <div style={{ height:'100%',width:`${Math.min(value*20,100)}%`,background:color,
        borderRadius:1,transition:'width 1s ease' }} />
    </div>
    <div style={{ fontSize:10,color:'#475569',marginTop:4 }}>Fuente: {fuente}</div>
  </div>
);

const ProductImpact = ({ product, impact }) => {
  const s = IMPACT_STYLE[impact] || IMPACT_STYLE.NEUTRAL;
  return (
    <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',
      padding:'5px 10px',borderRadius:8,background:s.bg,border:`1px solid ${s.border}`,marginBottom:4 }}>
      <span style={{ color:'#94A3B8',fontSize:12 }}>{product}</span>
      <span style={{ color:s.text,fontSize:11,fontWeight:600 }}>{(impact||'').replace(/_/g,' ')}</span>
    </div>
  );
};

const MacroContextPanel = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.forecast.macro().then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, []);

  const card = {
    background: 'rgba(15,23,42,.6)', borderRadius: 12,
    border: '1px solid rgba(255,255,255,.06)', padding: 14,
  };

  if (loading) return <div style={card}><Skeleton active paragraph={{ rows: 5 }} /></div>;
  if (!data) return <div style={card}><span style={{ color:'#64748B',fontSize:12 }}>Contexto macro no disponible</span></div>;

  return (
    <div style={card}>
      <div style={{ color:'#94A3B8',fontSize:11,fontWeight:600,marginBottom:10,
        textTransform:'uppercase',letterSpacing:'.8px' }}>Contexto Macro</div>

      <MacroIndicator label="Tipos hipotecarios" value={data.tipos_hipotecas_pct}
        unit="%" trend={data.tipos_hipotecas_tendencia} fuente={data.fuente_tipos} color="#00C2FF" />
      <MacroIndicator label="IPC Espana" value={data.ipc_spain_pct}
        unit="%" trend={data.ipc_tendencia} fuente={data.fuente_ipc} color="#A100FF" />

      <div style={{ marginTop:8,marginBottom:6,color:'#64748B',fontSize:10,
        textTransform:'uppercase',letterSpacing:'.5px' }}>Impacto por producto</div>
      <ProductImpact product="Hipotecario" impact={data.impacto_hipotecario} />
      <ProductImpact product="Deposito" impact={data.impacto_depositos} />
      <ProductImpact product="FRV" impact={data.impacto_frv} />

      <div style={{ color:'#475569',fontSize:11,marginTop:8,lineHeight:1.4 }}>
        {data.narrativa_corta}
      </div>
    </div>
  );
};

export default MacroContextPanel;
