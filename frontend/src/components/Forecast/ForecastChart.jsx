import React, { useMemo } from 'react';
import { Spin } from 'antd';
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer
} from 'recharts';

const COLORS = {
  actual: '#A100FF',
  base: '#E2E8F0',
  optimista: '#4ADE80',
  pesimista: '#FF6B6B',
  grid: '#1E2A3A',
};

const fmt = (v) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v;

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(161,0,255,0.3)',
      borderRadius: 8, padding: '10px 14px', backdropFilter: 'blur(10px)'
    }}>
      <p style={{ color: '#94A3B8', margin: '0 0 6px', fontSize: 12 }}>{label}</p>
      {payload.filter(p => p.value != null).map(p => (
        <p key={p.name} style={{ color: p.color, margin: '2px 0', fontSize: 13 }}>
          {p.name}: {typeof p.value === 'number'
            ? `€${p.value.toLocaleString('es-ES', { maximumFractionDigits: 0 })}`
            : p.value}
        </p>
      ))}
    </div>
  );
};

const ForecastChart = ({ historicos = [], escenarios, isLoading }) => {
  const chartData = useMemo(() => {
    const hist = (historicos || []).map(h => ({
      periodo: h.periodo, actual: h.valor, base: null, optimista: null, pesimista: null
    }));
    if (!escenarios?.base) return hist;

    const proj = escenarios.base.map((b, i) => ({
      periodo: b.periodo, actual: null,
      base: b.valor,
      optimista: escenarios.optimista?.[i]?.valor,
      pesimista: escenarios.pesimista?.[i]?.valor,
    }));

    if (hist.length > 0 && proj.length > 0) {
      hist[hist.length - 1].base = hist[hist.length - 1].actual;
      hist[hist.length - 1].optimista = hist[hist.length - 1].actual;
      hist[hist.length - 1].pesimista = hist[hist.length - 1].actual;
    }
    return [...hist, ...proj];
  }, [historicos, escenarios]);

  const lastHistPeriod = historicos?.length > 0 ? historicos[historicos.length - 1].periodo : null;

  if (isLoading) return (
    <div style={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spin tip="Calculando proyecciones..." />
    </div>
  );

  return (
    <div style={{
      background: 'rgba(15,23,42,0.6)', borderRadius: 12,
      border: '1px solid rgba(255,255,255,0.06)', padding: '16px 8px 8px'
    }}>
      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
          <XAxis dataKey="periodo" tick={{ fill: '#64748B', fontSize: 11 }} tickLine={false} />
          <YAxis tick={{ fill: '#64748B', fontSize: 11 }} tickFormatter={fmt} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94A3B8' }} />

          {lastHistPeriod && (
            <ReferenceLine x={lastHistPeriod} stroke="#A100FF" strokeDasharray="4 4"
              label={{ value: 'Hoy', fill: '#A100FF', fontSize: 11, position: 'top' }} />
          )}

          <Area type="monotone" dataKey="optimista" name="Optimista"
            stroke={COLORS.optimista} fill={COLORS.optimista} fillOpacity={0.08}
            strokeWidth={1.5} dot={false} connectNulls />
          <Area type="monotone" dataKey="pesimista" name="Pesimista"
            stroke={COLORS.pesimista} fill={COLORS.pesimista} fillOpacity={0.08}
            strokeWidth={1.5} dot={false} connectNulls />
          <Line type="monotone" dataKey="base" name="Base"
            stroke={COLORS.base} strokeWidth={2} dot={false} connectNulls />
          <Line type="monotone" dataKey="actual" name="Actual"
            stroke={COLORS.actual} strokeWidth={2.5} dot={{ r: 2, fill: COLORS.actual }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ForecastChart;
