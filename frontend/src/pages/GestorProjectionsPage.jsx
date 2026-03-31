import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Row, Col, Button, Radio, Spin, Table } from 'antd';
import { ArrowLeftOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import api from '../services/api';
import ForecastChart from '../components/Forecast/ForecastChart';
import ForecastChat from '../components/Forecast/ForecastChat';

/* ── CSS (injected once) ─────────────────────────────────────────── */
const STYLE_ID = 'gestor-forecast-css';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const s = document.createElement('style');
  s.id = STYLE_ID;
  s.textContent = `
    @keyframes fadeInUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
    @keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(.85)}}
    .gf-table .ant-table{background:transparent!important}
    .gf-table .ant-table-thead>tr>th{background:rgba(255,255,255,.04)!important;color:#64748B!important;
      border-bottom:1px solid rgba(255,255,255,.06)!important;font-size:11px!important;letter-spacing:.5px!important}
    .gf-table .ant-table-tbody>tr>td{background:transparent!important;
      border-bottom:1px solid rgba(255,255,255,.04)!important;color:#E2E8F0!important}
    .gf-table .ant-table-tbody>tr:hover>td{background:rgba(161,0,255,.05)!important}
  `;
  document.head.appendChild(s);
}

const card = {
  background: 'rgba(15,23,42,.55)', borderRadius: 12,
  border: '1px solid rgba(255,255,255,.06)', padding: 14,
};
const fmt = (v) => v != null ? `€${Math.round(v).toLocaleString('es-ES')}` : '—';

/* ── KPI mini-card ───────────────────────────────────────────────── */
const KPIMini = ({ label, value, suffix, color = '#E2E8F0' }) => (
  <div style={{ marginBottom: 10 }}>
    <div style={{ fontSize: 11, color: '#64748B' }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700, color, letterSpacing: '-.5px' }}>
      {value}<span style={{ fontSize: 12, color: '#64748B', fontWeight: 400 }}>{suffix}</span>
    </div>
  </div>
);

/* ── Scenario mini-card ──────────────────────────────────────────── */
const ScenarioMini = ({ tipo, data }) => {
  const cfg = {
    pesimista: { color: '#FF6B6B', label: 'Pesimista', icon: '▼' },
    base:      { color: '#E2E8F0', label: 'Base',      icon: '→' },
    optimista: { color: '#4ADE80', label: 'Optimista', icon: '▲' },
  }[tipo] || {};
  if (!data) return null;
  const ultimo = data.valores?.[data.valores.length - 1]?.valor || 0;
  return (
    <div style={{ background: `${cfg.color}08`, border: `1px solid ${cfg.color}25`,
      borderRadius: 8, padding: '8px 10px', marginBottom: 6 }}>
      <div style={{ fontSize: 11, color: cfg.color, fontWeight: 600 }}>{cfg.icon} {cfg.label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: '#E2E8F0' }}>{fmt(ultimo)}/mes</div>
      <div style={{ fontSize: 10, color: '#64748B' }}>
        Acum: {fmt(data.ingresos_acumulados)} · {data.variacion_vs_actual_pct >= 0 ? '+' : ''}{data.variacion_vs_actual_pct}%
      </div>
    </div>
  );
};

/* ── Palanca card ────────────────────────────────────────────────── */
const PalancaCard = ({ text, index }) => (
  <div style={{ background: 'rgba(161,0,255,.05)', border: '1px solid rgba(161,0,255,.12)',
    borderRadius: 8, padding: '8px 10px', marginBottom: 6, display: 'flex', gap: 8 }}>
    <span style={{ color: '#A100FF', fontWeight: 700, fontSize: 13 }}>{index + 1}</span>
    <span style={{ color: '#C4B5FD', fontSize: 12, lineHeight: 1.4 }}>{text}</span>
  </div>
);

/* ════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ════════════════════════════════════════════════════════════════════ */
const GestorProjectionsPage = () => {
  const navigate = useNavigate();
  const { gestorId } = useParams();

  const [horizonte, setHorizonte] = useState(6);
  const [escenarios, setEscenarios] = useState(null);
  const [historicos, setHistoricos] = useState([]);
  const [contexto, setContexto] = useState(null);
  const [palancas, setPalancas] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const init = useRef(false);

  /* ── Load on mount ─────────────────────────────────────────── */
  useEffect(() => {
    if (!gestorId) return;
    // Historical data
    api.forecast.historicos({ dimension: 'gestor', filtro_id: gestorId })
      .then(setHistoricos).catch(() => setHistoricos([]));
    // Gestor context
    api.http.get(`/forecast/gestor/${gestorId}/contexto`)
      .then(r => setContexto(r.data?.data || r.data || r))
      .catch(() => {});
    // Recommendations
    api.forecast.recs({ objetivo: 'maximizar ingresos y mejorar margen con mi cartera actual', horizonte_meses: 6 })
      .then(r => setPalancas(r?.acciones || []))
      .catch(() => {});
  }, [gestorId]);

  /* ── Calculate projection ──────────────────────────────────── */
  const calcular = useCallback(async (h) => {
    if (!gestorId) return;
    setIsLoading(true);
    try {
      const result = await api.forecast.base({
        horizonte_meses: h ?? horizonte,
        dimension: 'gestor',
        filtro_id: gestorId,
      });
      setEscenarios(result);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  }, [gestorId, horizonte]);

  useEffect(() => {
    if (!init.current && gestorId) { init.current = true; calcular(); }
  }, [calcular, gestorId]);

  useEffect(() => {
    if (init.current && escenarios) calcular(horizonte);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [horizonte]);

  /* ── Table ─────────────────────────────────────────────────── */
  const tableData = escenarios?.escenario_base?.valores?.map((b, i) => ({
    key: b.periodo, periodo: b.periodo,
    pes: escenarios.escenario_pesimista?.valores?.[i]?.valor,
    base: b.valor,
    opt: escenarios.escenario_optimista?.valores?.[i]?.valor,
  })) || [];

  const columns = [
    { title: 'Mes', dataIndex: 'periodo', width: 90 },
    { title: 'Pesimista', dataIndex: 'pes', render: v => <span style={{color:'#FF6B6B'}}>{fmt(v)}</span> },
    { title: 'Base', dataIndex: 'base', render: v => <span style={{color:'#E2E8F0',fontWeight:600}}>{fmt(v)}</span> },
    { title: 'Optimista', dataIndex: 'opt', render: v => <span style={{color:'#4ADE80'}}>{fmt(v)}</span> },
  ];

  const lastIngreso = contexto?.ingreso_ultimo_mes || (historicos.length > 0 ? historicos[historicos.length-1]?.valor : 0);
  const tendencia = contexto?.tendencia || 'estable';

  /* ── Render ─────────────────────────────────────────────────── */
  return (
    <div style={{
      minHeight: '100vh', color: '#E2E8F0', background: '#0D0D1A',
      backgroundImage: 'linear-gradient(rgba(161,0,255,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(161,0,255,.02) 1px,transparent 1px)',
      backgroundSize: '40px 40px', animation: 'fadeInUp .4s ease-out',
    }}>
      {/* Ambient glows */}
      <div style={{position:'fixed',top:-200,right:-200,width:500,height:500,
        background:'radial-gradient(circle,rgba(161,0,255,.06),transparent 70%)',pointerEvents:'none'}} />

      {/* ── Header ───────────────────────────────────────────── */}
      <div style={{
        padding:'14px 24px',borderBottom:'1px solid rgba(255,255,255,.06)',
        background:'linear-gradient(135deg,rgba(161,0,255,.06),transparent,rgba(0,194,255,.03))',
        display:'flex',alignItems:'center',justifyContent:'space-between',position:'relative',
      }}>
        <div style={{position:'absolute',top:0,left:0,right:0,height:1,
          background:'linear-gradient(90deg,transparent,#A100FF 30%,#00C2FF 70%,transparent)'}} />
        <div style={{display:'flex',alignItems:'center',gap:16}}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} ghost
            style={{borderColor:'rgba(255,255,255,.15)',color:'#94A3B8'}}>Mi Dashboard</Button>
          <div>
            <div style={{color:'#E2E8F0',fontWeight:700,fontSize:17}}>Mis Proyecciones</div>
            <div style={{color:'#A100FF',fontSize:11,letterSpacing:'2px',textTransform:'uppercase'}}>
              Gestor {gestorId} · Forecast Personal
            </div>
          </div>
        </div>
        <div style={{display:'flex',gap:8,alignItems:'center',background:'rgba(255,255,255,.04)',
          border:'1px solid rgba(161,0,255,.2)',borderRadius:20,padding:'5px 14px',fontSize:11,color:'#64748B'}}>
          <div style={{width:6,height:6,borderRadius:'50%',background:'#4ADE80',
            boxShadow:'0 0 6px #4ADE80',animation:'pulse 2s infinite'}} />
          Prophet ML · GPT-4o
        </div>
      </div>

      {/* ── Content ──────────────────────────────────────────── */}
      <Row gutter={[12,12]} style={{padding:'12px 16px'}}>

        {/* LEFT: KPIs + Config + Escenarios + Palancas */}
        <Col xs={24} lg={7} style={{display:'flex',flexDirection:'column',gap:10,
          overflowY:'auto',maxHeight:'calc(100vh - 76px)'}}>

          {/* KPIs */}
          <div style={card}>
            <div style={{fontSize:11,color:'#94A3B8',fontWeight:600,textTransform:'uppercase',
              letterSpacing:'.8px',marginBottom:10}}>Mi Situacion Actual</div>
            <KPIMini label="Ingresos ultimo mes" value={fmt(lastIngreso)} color="#A100FF" />
            <KPIMini label="Media 6 meses" value={fmt(contexto?.ingreso_medio_6m)} color="#00C2FF" />
            <KPIMini label="Tendencia" value={tendencia === 'creciente' ? '▲ Creciente' :
              tendencia === 'decreciente' ? '▼ Decreciente' : '→ Estable'}
              color={tendencia === 'creciente' ? '#4ADE80' : tendencia === 'decreciente' ? '#FF6B6B' : '#94A3B8'} />
          </div>

          {/* Horizonte */}
          <div style={card}>
            <div style={{fontSize:11,color:'#94A3B8',marginBottom:6}}>Horizonte</div>
            <Radio.Group value={horizonte} onChange={e => setHorizonte(e.target.value)}
              buttonStyle="solid" size="small" style={{width:'100%'}}>
              <Radio.Button value={3} style={{width:'33%',textAlign:'center'}}>3m</Radio.Button>
              <Radio.Button value={6} style={{width:'34%',textAlign:'center'}}>6m</Radio.Button>
              <Radio.Button value={12} style={{width:'33%',textAlign:'center'}}>12m</Radio.Button>
            </Radio.Group>
          </div>

          {/* Escenarios */}
          <div style={card}>
            <div style={{fontSize:11,color:'#94A3B8',fontWeight:600,textTransform:'uppercase',
              letterSpacing:'.8px',marginBottom:8}}>Escenarios</div>
            {isLoading ? <Spin size="small" /> : <>
              <ScenarioMini tipo="optimista" data={escenarios?.escenario_optimista} />
              <ScenarioMini tipo="base" data={escenarios?.escenario_base} />
              <ScenarioMini tipo="pesimista" data={escenarios?.escenario_pesimista} />
            </>}
          </div>

          {/* Palancas */}
          <div style={card}>
            <div style={{fontSize:11,color:'#94A3B8',fontWeight:600,textTransform:'uppercase',
              letterSpacing:'.8px',marginBottom:8}}>Acciones Recomendadas</div>
            {palancas.length > 0
              ? palancas.slice(0, 3).map((p, i) => <PalancaCard key={i} text={p} index={i} />)
              : <span style={{color:'#475569',fontSize:12}}>Cargando recomendaciones...</span>}
          </div>
        </Col>

        {/* CENTER-RIGHT: Chart + Table + Chat */}
        <Col xs={24} lg={17} style={{display:'flex',flexDirection:'column',gap:10,
          maxHeight:'calc(100vh - 76px)'}}>

          {/* Chart */}
          <ForecastChart
            historicos={(historicos || []).slice(-8)}
            escenarios={{
              base: escenarios?.escenario_base?.valores || [],
              optimista: escenarios?.escenario_optimista?.valores || [],
              pesimista: escenarios?.escenario_pesimista?.valores || [],
            }}
            isLoading={isLoading}
          />

          {/* Bottom: Table + Chat side by side */}
          <Row gutter={[10,10]} style={{flex:1,minHeight:0}}>
            <Col xs={24} lg={10} style={{overflowY:'auto',maxHeight:'calc(100vh - 500px)'}}>
              <div style={{...card,padding:10}}>
                <Table dataSource={tableData} columns={columns} pagination={false}
                  size="small" className="gf-table" />
              </div>
              {escenarios?.nota_metodologica && (
                <div style={{color:'#475569',fontSize:10,padding:'4px 6px',lineHeight:1.3,marginTop:4}}>
                  {escenarios.nota_metodologica}
                </div>
              )}
            </Col>
            <Col xs={24} lg={14} style={{height:'calc(100vh - 500px)',minHeight:300}}>
              <ForecastChat mode="gestor" gestorId={gestorId} perioBase="2026-04" />
            </Col>
          </Row>
        </Col>
      </Row>
    </div>
  );
};

export default GestorProjectionsPage;
