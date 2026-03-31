import React, { useMemo } from 'react';
import { Spin } from 'antd';
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer
} from 'recharts';

const COLORS = {
  actual: '#A100FF', base: '#E2E8F0', optimista: '#4ADE80', pesimista: '#FF6B6B', grid: '#1E2A3A',
};

const fmtAxis = (v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const isHist = payload.some(p => p.dataKey === 'actual' && p.value != null);
  return (
    <div style={{
      background: 'rgba(13,13,26,.95)', backdropFilter: 'blur(20px)',
      border: `1px solid ${isHist ? 'rgba(161,0,255,.4)' : 'rgba(0,194,255,.3)'}`,
      borderRadius: 10, padding: '12px 16px', boxShadow: '0 8px 32px rgba(0,0,0,.4)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        <span style={{ fontSize: 10, color: isHist ? '#A100FF' : '#00C2FF',
          textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 600 }}>
          {isHist ? '● Dato real' : '◈ Proyeccion'}
        </span>
        <span style={{ color: '#475569', fontSize: 11 }}>{label}</span>
      </div>
      {payload.filter(p => p.value != null).map(p => (
        <div key={p.dataKey} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginBottom: 3 }}>
          <span style={{ color: p.color, fontSize: 12 }}>
            {p.dataKey === 'actual' ? 'Real' : p.dataKey === 'base' ? 'Base' :
             p.dataKey === 'optimista' ? 'Optimista' : 'Pesimista'}
          </span>
          <span style={{ color: '#E2E8F0', fontSize: 12, fontWeight: 600 }}>
            €{Math.round(p.value).toLocaleString('es-ES')}
          </span>
        </div>
      ))}
    </div>
  );
};

const LastDot = (props) => {
  const { cx, cy, index, data } = props;
  if (!data || index !== data.length - 1 - (data.filter(d => d.base != null && d.actual == null).length)) return null;
  // Only render on the last actual point
  const isLastActual = data[index]?.actual != null && (index === data.length - 1 || data[index + 1]?.actual == null);
  if (!isLastActual) return null;
  return (
    <g>
      <circle cx={cx} cy={cy} r={5} fill="#A100FF" stroke="#0D0D1A" strokeWidth={2} />
      <circle cx={cx} cy={cy} r={9} fill="none" stroke="#A100FF" strokeWidth={1} opacity={0.4} />
    </g>
  );
};

const ForecastChart = ({ historicos = [], escenarios, isLoading }) => {
  const chartData = useMemo(() => {
    const hist = (historicos || []).map(h => ({
      periodo: h.periodo, actual: h.valor, base: null, optimista: null, pesimista: null,
    }));
    if (!escenarios?.base?.length) return hist;

    const proj = escenarios.base.map((b, i) => ({
      periodo: b.periodo, actual: null,
      base: b.valor,
      optimista: escenarios.optimista?.[i]?.valor,
      pesimista: escenarios.pesimista?.[i]?.valor,
    }));

    // Connect last historical to first projection
    if (hist.length > 0 && proj.length > 0) {
      const lastVal = hist[hist.length - 1].actual;
      hist[hist.length - 1].base = lastVal;
      hist[hist.length - 1].optimista = lastVal;
      hist[hist.length - 1].pesimista = lastVal;
    }
    return [...hist, ...proj];
  }, [historicos, escenarios]);

  const lastHistPeriod = historicos?.length > 0 ? historicos[historicos.length - 1].periodo : null;

  if (isLoading) return (
    <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'rgba(15,23,42,.6)', borderRadius: 12, border: '1px solid rgba(255,255,255,.06)' }}>
      <Spin tip="Calculando proyecciones..." />
    </div>
  );

  return (
    <div style={{
      background: 'rgba(15,23,42,.5)', borderRadius: 12,
      border: '1px solid rgba(255,255,255,.06)', padding: '16px 8px 8px',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* Subtle glow behind the chart */}
      <div style={{ position: 'absolute', top: '30%', left: '50%', transform: 'translate(-50%,-50%)',
        width: 300, height: 200, background: 'radial-gradient(ellipse,rgba(161,0,255,.06),transparent 70%)',
        pointerEvents: 'none' }} />

      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="gradOpt" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS.optimista} stopOpacity={0.15} />
              <stop offset="100%" stopColor={COLORS.optimista} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradPes" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={COLORS.pesimista} stopOpacity={0.12} />
              <stop offset="100%" stopColor={COLORS.pesimista} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
          <XAxis dataKey="periodo" tick={{ fill: '#64748B', fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: '#64748B', fontSize: 11 }} tickFormatter={fmtAxis} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94A3B8' }} />

          {lastHistPeriod && (
            <ReferenceLine x={lastHistPeriod} stroke="rgba(255,255,255,.25)" strokeDasharray="4 4"
              label={{ value: 'HOY', fill: '#94A3B8', fontSize: 10, fontWeight: 600, letterSpacing: '1px', position: 'top' }} />
          )}

          <Area type="monotone" dataKey="optimista" name="Optimista"
            stroke={COLORS.optimista} fill="url(#gradOpt)" strokeWidth={1.5} dot={false} connectNulls />
          <Area type="monotone" dataKey="pesimista" name="Pesimista"
            stroke={COLORS.pesimista} fill="url(#gradPes)" strokeWidth={1.5} dot={false} connectNulls />
          <Line type="monotone" dataKey="base" name="Base"
            stroke={COLORS.base} strokeWidth={2} dot={false} connectNulls strokeDasharray="6 3" />
          <Line type="monotone" dataKey="actual" name="Actual"
            stroke={COLORS.actual} strokeWidth={2.5}
            dot={<LastDot data={chartData} />} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ForecastChart;
