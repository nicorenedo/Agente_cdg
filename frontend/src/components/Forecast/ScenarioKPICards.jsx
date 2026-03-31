import React from 'react';
import { Row, Col, Skeleton } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, MinusOutlined } from '@ant-design/icons';

const fmt = (v) => v != null ? `€${Math.round(v).toLocaleString('es-ES')}` : '—';

const SCENARIO_CONFIG = {
  pesimista: { label: 'Pesimista', color: '#FF6B6B', border: 'rgba(255,107,107,0.3)', bg: 'rgba(255,107,107,0.04)', icon: <ArrowDownOutlined /> },
  base:      { label: 'Base',      color: '#E2E8F0', border: 'rgba(226,232,240,0.2)', bg: 'rgba(226,232,240,0.04)', icon: <MinusOutlined /> },
  optimista: { label: 'Optimista', color: '#4ADE80', border: 'rgba(74,222,128,0.3)',  bg: 'rgba(74,222,128,0.04)',  icon: <ArrowUpOutlined /> },
};

const ScenarioCard = ({ tipo, data, ingresoActual }) => {
  const cfg = SCENARIO_CONFIG[tipo];
  if (!data) return <Skeleton active />;

  const ultimoValor = data.valores?.[data.valores.length - 1]?.valor || 0;
  const var_pct = data.variacion_vs_actual_pct || 0;

  return (
    <div style={{
      background: cfg.bg, border: `1px solid ${cfg.border}`, borderRadius: 10,
      padding: '14px 16px', height: '100%'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
        <span style={{ color: cfg.color, fontSize: 14 }}>{cfg.icon}</span>
        <span style={{ color: cfg.color, fontWeight: 700, fontSize: 14 }}>{cfg.label}</span>
        <span style={{
          marginLeft: 'auto', fontSize: 11, color: '#64748B',
          background: 'rgba(255,255,255,0.05)', borderRadius: 4, padding: '1px 6px'
        }}>
          {Math.round((data.probabilidad || 0) * 100)}% prob.
        </span>
      </div>
      <div style={{ color: '#F1F5F9', fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
        {fmt(ultimoValor)}<span style={{ fontSize: 12, color: '#64748B', fontWeight: 400 }}>/mes</span>
      </div>
      <div style={{
        color: var_pct >= 0 ? '#4ADE80' : '#FF6B6B', fontSize: 13, fontWeight: 600, marginBottom: 6
      }}>
        {var_pct >= 0 ? '▲' : '▼'} {Math.abs(var_pct).toFixed(1)}% vs actual
      </div>
      <div style={{ color: '#94A3B8', fontSize: 11 }}>
        Acum. {fmt(data.ingresos_acumulados)}
      </div>
      {data.narrativa && (
        <div style={{ color: '#64748B', fontSize: 11, marginTop: 6, lineHeight: 1.4 }}>
          {data.narrativa.length > 100 ? data.narrativa.slice(0, 100) + '...' : data.narrativa}
        </div>
      )}
    </div>
  );
};

const ScenarioKPICards = ({ escenarios, ingresoActual = 0, isLoading }) => {
  if (isLoading) return <Row gutter={12}>{[1,2,3].map(i => <Col span={8} key={i}><Skeleton active /></Col>)}</Row>;

  return (
    <Row gutter={12}>
      {['pesimista', 'base', 'optimista'].map(tipo => (
        <Col xs={24} sm={8} key={tipo}>
          <ScenarioCard
            tipo={tipo}
            data={escenarios?.[`escenario_${tipo}`]}
            ingresoActual={ingresoActual}
          />
        </Col>
      ))}
    </Row>
  );
};

export default ScenarioKPICards;
