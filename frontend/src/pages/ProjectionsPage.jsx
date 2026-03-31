import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Row, Col, Button, Table, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import api from '../services/api';

import ForecastChart from '../components/Forecast/ForecastChart';
import ScenarioKPICards from '../components/Forecast/ScenarioKPICards';
import ScenarioConfigurator from '../components/Forecast/ScenarioConfigurator';
import MacroContextPanel from '../components/Forecast/MacroContextPanel';
import ForecastChat from '../components/Forecast/ForecastChat';

/* ── CSS animations injected once ───────────────────────────────── */
const STYLE_ID = 'forecast-animations';
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    @keyframes shimmer { 0%{transform:translateX(-100%)} 100%{transform:translateX(100%)} }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.6;transform:scale(.85)} }
    @keyframes fadeInUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
    .dark-forecast-table .ant-table { background:transparent !important; }
    .dark-forecast-table .ant-table-thead>tr>th {
      background:rgba(255,255,255,.04)!important; color:#64748B!important;
      border-bottom:1px solid rgba(255,255,255,.06)!important;
      font-size:11px!important; text-transform:uppercase!important; letter-spacing:.8px!important;
    }
    .dark-forecast-table .ant-table-tbody>tr>td {
      background:transparent!important; border-bottom:1px solid rgba(255,255,255,.04)!important; color:#E2E8F0!important;
    }
    .dark-forecast-table .ant-table-tbody>tr:hover>td { background:rgba(161,0,255,.05)!important; }
    .dark-forecast-table .ant-table-cell-row-hover { background:rgba(161,0,255,.05)!important; }
  `;
  document.head.appendChild(style);
}

const ProjectionsPage = ({ mode = 'direccion' }) => {
  const navigate = useNavigate();
  const { gestorId } = useParams();
  const initialised = useRef(false);

  const [config, setConfig] = useState({
    horizonte: 6,
    dimension: mode === 'gestor' ? 'gestor' : 'entidad',
    filtroId: gestorId || null,
    shocks: { tipos_interes: 0, captacion_clientes: 0, reduccion_gastos: 0, mix_productos: 0 },
  });
  const [escenarios, setEscenarios] = useState(null);
  const [historicos, setHistoricos] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [dimensiones, setDimensiones] = useState({ centros: [], gestores: [] });

  /* ── Load dimensiones ───────────────────────────────────────── */
  useEffect(() => {
    api.forecast.dimensiones().then(setDimensiones).catch(() => {});
  }, []);

  /* ── Load historicos when dimension/filtro changes ──────────── */
  useEffect(() => {
    api.forecast.historicos({ dimension: config.dimension, filtro_id: config.filtroId })
      .then(setHistoricos)
      .catch(() => setHistoricos([]));
  }, [config.dimension, config.filtroId]);

  /* ── Calcular function (stable ref via latest config) ──────── */
  const configRef = useRef(config);
  configRef.current = config;

  const calcular = useCallback(async (overrideConfig) => {
    const c = overrideConfig || configRef.current;
    setIsLoading(true);
    try {
      const hasShocks = Object.values(c.shocks).some(v => v !== 0);
      const payload = {
        horizonte_meses: c.horizonte,
        dimension: c.dimension,
        filtro_id: c.filtroId,
      };
      const result = hasShocks
        ? await api.forecast.whatif({ ...payload, shocks: c.shocks })
        : await api.forecast.base(payload);
      setEscenarios(result);
    } catch (e) {
      message.error('Error calculando proyecciones');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /* ── Initial calculation ────────────────────────────────────── */
  useEffect(() => {
    if (!initialised.current) {
      initialised.current = true;
      calcular();
    }
  }, [calcular]);

  /* ── Auto-recalculate when horizonte changes ────────────────── */
  useEffect(() => {
    if (initialised.current && escenarios) {
      calcular();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config.horizonte]);

  /* ── Table data ─────────────────────────────────────────────── */
  const tableData = escenarios?.escenario_base?.valores?.map((b, i) => ({
    key: b.periodo, periodo: b.periodo,
    pesimista: escenarios.escenario_pesimista?.valores?.[i]?.valor,
    base: b.valor,
    optimista: escenarios.escenario_optimista?.valores?.[i]?.valor,
  })) || [];

  const fmt = (v) => v != null ? `€${Math.round(v).toLocaleString('es-ES')}` : '—';
  const columns = [
    { title: 'Periodo', dataIndex: 'periodo', key: 'periodo', width: 100 },
    { title: 'Pesimista', dataIndex: 'pesimista', render: v => <span style={{ color: '#FF6B6B' }}>{fmt(v)}</span> },
    { title: 'Base', dataIndex: 'base', render: v => <span style={{ color: '#E2E8F0', fontWeight: 600 }}>{fmt(v)}</span> },
    { title: 'Optimista', dataIndex: 'optimista', render: v => <span style={{ color: '#4ADE80' }}>{fmt(v)}</span> },
  ];

  /* ── Render ─────────────────────────────────────────────────── */
  return (
    <div style={{
      minHeight: '100vh', color: '#E2E8F0', background: '#0D0D1A',
      backgroundImage: 'linear-gradient(rgba(161,0,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(161,0,255,.025) 1px,transparent 1px)',
      backgroundSize: '40px 40px', position: 'relative',
      animation: 'fadeInUp .4s ease-out',
    }}>
      {/* Ambient glows */}
      <div style={{ position:'fixed',top:-200,right:-200,width:600,height:600,
        background:'radial-gradient(circle,rgba(161,0,255,.07) 0%,transparent 70%)',pointerEvents:'none',zIndex:0}} />
      <div style={{ position:'fixed',bottom:-200,left:-200,width:500,height:500,
        background:'radial-gradient(circle,rgba(0,194,255,.05) 0%,transparent 70%)',pointerEvents:'none',zIndex:0}} />

      {/* ── Header ────────────────────────────────────────────── */}
      <div style={{
        padding: '14px 24px', borderBottom: '1px solid rgba(255,255,255,.06)',
        background: 'linear-gradient(135deg,rgba(161,0,255,.08) 0%,transparent 50%,rgba(0,194,255,.04) 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'relative', overflow: 'hidden', zIndex: 1,
      }}>
        {/* top accent line */}
        <div style={{ position:'absolute',top:0,left:0,right:0,height:1,
          background:'linear-gradient(90deg,transparent 0%,#A100FF 30%,#00C2FF 70%,transparent 100%)'}} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} ghost
            style={{ borderColor: 'rgba(255,255,255,.15)', color: '#94A3B8' }}>Dashboard</Button>
          <div>
            <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: 17, letterSpacing: '-.3px' }}>
              CDG Intelligence</div>
            <div style={{ color: '#A100FF', fontSize: 11, fontWeight: 500, letterSpacing: '2px', textTransform: 'uppercase' }}>
              Modulo de Proyecciones</div>
          </div>
        </div>

        <div style={{ display:'flex',gap:8,alignItems:'center',background:'rgba(255,255,255,.04)',
          border:'1px solid rgba(161,0,255,.2)',borderRadius:20,padding:'5px 14px',fontSize:11,color:'#64748B' }}>
          <div style={{ width:6,height:6,borderRadius:'50%',background:'#4ADE80',
            boxShadow:'0 0 6px #4ADE80',animation:'pulse 2s infinite'}} />
          Prophet ML &middot; GPT-4o &middot; BCE &middot; INE
        </div>
      </div>

      {/* ── 3 columns ─────────────────────────────────────────── */}
      <Row gutter={[12, 12]} style={{ padding: '12px 16px', position: 'relative', zIndex: 1 }}>

        {/* Left */}
        <Col xs={24} lg={6} style={{ display:'flex',flexDirection:'column',gap:12,
          overflowY:'auto',maxHeight:'calc(100vh - 76px)' }}>
          <ScenarioConfigurator config={config} onChange={setConfig}
            onCalcular={() => calcular()} isLoading={isLoading} dimensiones={dimensiones} />
          <MacroContextPanel />
        </Col>

        {/* Center */}
        <Col xs={24} lg={12} style={{ display:'flex',flexDirection:'column',gap:12,
          overflowY:'auto',maxHeight:'calc(100vh - 76px)' }}>
          <ForecastChart
            historicos={historicos.slice(-8)}
            escenarios={{
              base: escenarios?.escenario_base?.valores || [],
              optimista: escenarios?.escenario_optimista?.valores || [],
              pesimista: escenarios?.escenario_pesimista?.valores || [],
            }}
            isLoading={isLoading}
          />
          <ScenarioKPICards escenarios={escenarios}
            ingresoActual={escenarios?.ingresos_actual || 0} isLoading={isLoading} />
          <div style={{ background:'rgba(15,23,42,.6)',borderRadius:12,
            border:'1px solid rgba(255,255,255,.06)',padding:12 }}>
            <Table dataSource={tableData} columns={columns} pagination={false}
              size="small" className="dark-forecast-table" />
          </div>
          {escenarios?.nota_metodologica && (
            <div style={{ color:'#475569',fontSize:11,padding:'4px 8px',lineHeight:1.4 }}>
              {escenarios.nota_metodologica}
            </div>
          )}
        </Col>

        {/* Right */}
        <Col xs={24} lg={6} style={{ height:'calc(100vh - 76px)' }}>
          <ForecastChat mode={mode} gestorId={gestorId} perioBase="2026-04" />
        </Col>
      </Row>
    </div>
  );
};

export default ProjectionsPage;
