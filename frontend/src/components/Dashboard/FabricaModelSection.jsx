/**
 * FabricaModelSection.jsx
 * Modelo Fábrica — Fondos de Inversión
 * Solo visible en DireccionView (CDG/Dirección).
 * Muestra importe cedido a gestora (760025) vs retenido por banco (760024).
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Card, Row, Col, Statistic, Spin, Alert, Tag } from 'antd';
import { BankOutlined, PercentageOutlined, SwapOutlined } from '@ant-design/icons';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { analytics } from '../../services/api';

const COLORS = {
  gestora: '#A100FF',
  banco: '#7B00CC',
  axis: '#888',
  gridStroke: '#e0d0ff',
};

const fmt = (v) =>
  v == null
    ? '—'
    : new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v);

const FabricaModelSection = ({ periodo = '2025-10' }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analytics.fabrica(periodo);
      setData(res);
    } catch (e) {
      setError(e.message || 'Error cargando datos de fábrica');
    } finally {
      setLoading(false);
    }
  }, [periodo]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <Card style={{ marginTop: 24 }}>
        <Spin tip="Cargando modelo fábrica..." />
      </Card>
    );
  }
  if (error) {
    return (
      <Card style={{ marginTop: 24 }}>
        <Alert type="error" message={error} />
      </Card>
    );
  }
  if (!data) return null;

  const oct = data.oct_2025 || {};
  const sep = data.sep_2025 || {};
  const desvRatio = data.desviacion_ratio_vs_target ?? null;
  const varCedido = data.variacion_cedido_pct ?? null;

  // Semáforo desviación vs 85% target
  const ratioStatus = desvRatio == null ? null : Math.abs(desvRatio) < 1 ? 'success' : Math.abs(desvRatio) < 3 ? 'warning' : 'error';
  const ratioTag = ratioStatus === 'success' ? 'green' : ratioStatus === 'warning' ? 'orange' : 'red';

  // Datos para el gráfico comparativo sep vs oct
  const chartData = [
    {
      name: 'Cedido Gestora',
      'Sep 2025': sep.cedido_gestora || 0,
      'Oct 2025': oct.cedido_gestora || 0,
    },
    {
      name: 'Retenido Banco',
      'Sep 2025': sep.retenido_banco || 0,
      'Oct 2025': oct.retenido_banco || 0,
    },
  ];

  const cardStyle = {
    borderRadius: 8,
    boxShadow: '0 2px 12px rgba(161,0,255,0.08)',
    borderTop: '3px solid #A100FF',
  };

  return (
    <Card
      title={
        <span style={{ color: '#1A0033', fontWeight: 700 }}>
          <SwapOutlined style={{ marginRight: 8, color: '#A100FF' }} />
          Modelo Fábrica — Fondos de Inversión
        </span>
      }
      style={{ marginTop: 24, ...cardStyle }}
      extra={
        <Tag color={ratioTag}>
          Ratio gestora: {oct.ratio_gestora_pct ?? '—'}%
          {desvRatio != null && (
            <span style={{ marginLeft: 4 }}>
              ({desvRatio > 0 ? '+' : ''}{desvRatio}% vs 85% target)
            </span>
          )}
        </Tag>
      }
    >
      {/* KPI Cards Row */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card size="small" style={cardStyle}>
            <Statistic
              title="Cedido a Gestora (oct)"
              value={oct.cedido_gestora || 0}
              formatter={(v) => fmt(v)}
              prefix={<PercentageOutlined style={{ color: '#A100FF' }} />}
              valueStyle={{ color: '#A100FF', fontWeight: 700 }}
              suffix={
                varCedido != null ? (
                  <span style={{ fontSize: 12, color: varCedido >= 0 ? '#52c41a' : '#ff4d4f', marginLeft: 6 }}>
                    {varCedido >= 0 ? '▲' : '▼'} {Math.abs(varCedido)}%
                  </span>
                ) : null
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" style={{ ...cardStyle, borderTopColor: '#7B00CC' }}>
            <Statistic
              title="Retenido por Banco (oct)"
              value={oct.retenido_banco || 0}
              formatter={(v) => fmt(v)}
              prefix={<BankOutlined style={{ color: '#7B00CC' }} />}
              valueStyle={{ color: '#7B00CC', fontWeight: 700 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" style={{ ...cardStyle, borderTopColor: '#CC66FF' }}>
            <Statistic
              title="Contratos Fondo activos (oct)"
              value={oct.contratos_fondo || 0}
              valueStyle={{ color: '#5500AA', fontWeight: 700 }}
              suffix={
                <span style={{ fontSize: 13, color: '#888', fontWeight: 400, marginLeft: 4 }}>
                  contratos
                </span>
              }
            />
            <div style={{ marginTop: 4, fontSize: 12, color: '#666' }}>
              Banco: {oct.ratio_banco_pct ?? '—'}% · Gestora: {oct.ratio_gestora_pct ?? '—'}%
            </div>
          </Card>
        </Col>
      </Row>

      {/* Bar Chart: Sep vs Oct */}
      <div style={{ marginTop: 20 }}>
        <div style={{ fontWeight: 600, color: '#1A0033', marginBottom: 8 }}>
          Evolución Sep → Oct
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData} barGap={4} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" stroke={COLORS.gridStroke} />
            <XAxis dataKey="name" tick={{ fill: COLORS.axis, fontSize: 12 }} />
            <YAxis tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} tick={{ fill: COLORS.axis, fontSize: 11 }} />
            <Tooltip
              formatter={(value) => fmt(value)}
              contentStyle={{ borderRadius: 8, fontSize: 12 }}
            />
            <Legend />
            <Bar dataKey="Sep 2025" fill="#CC66FF" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Oct 2025" fill={COLORS.gestora} radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

export default FabricaModelSection;
