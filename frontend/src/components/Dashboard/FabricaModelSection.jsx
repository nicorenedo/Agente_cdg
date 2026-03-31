/**
 * FabricaModelSection.jsx
 * Modelo Fábrica — Fondos de Inversión (banda compacta, ~140px)
 * Solo visible en DireccionView (CDG/Dirección).
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Card, Row, Col, Statistic, Spin, Alert, Tag, Space } from 'antd';
import { BankOutlined, EuroCircleOutlined, SwapOutlined, ContainerOutlined } from '@ant-design/icons';
import { analytics } from '../../services/api';

const fmt = (v) =>
  v == null
    ? '—'
    : new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(v);

const cardStyle = {
  borderRadius: 6,
  boxShadow: '0 1px 6px rgba(161,0,255,0.07)',
  borderTop: '2px solid #A100FF',
};

const FabricaModelSection = ({ periodo = '2026-04' }) => {
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

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <Card size="small" style={{ marginTop: 16, ...cardStyle }}>
      <Spin size="small" tip="Cargando modelo fábrica..." />
    </Card>
  );
  if (error) return (
    <Card size="small" style={{ marginTop: 16, ...cardStyle }}>
      <Alert type="error" message={error} banner />
    </Card>
  );
  if (!data) return null;

  // Dynamic: use data for the selected period (the API returns period-keyed data)
  const periodoKey = periodo ? periodo.replace('-', '_') : '';
  const current = data[periodoKey] || data.oct_2025 || data || {};
  const periodoLabel = periodo ? periodo.substring(0, 7) : 'periodo';
  const desvRatio = data.desviacion_ratio_vs_target ?? null;
  const varCedido = data.variacion_cedido_pct ?? null;

  const ratioStatus = desvRatio == null ? null : Math.abs(desvRatio) < 1 ? 'success' : Math.abs(desvRatio) < 3 ? 'warning' : 'error';
  const ratioTagColor = ratioStatus === 'success' ? 'green' : ratioStatus === 'warning' ? 'orange' : 'red';

  const varDisplay = (varCedido != null)
    ? `${varCedido >= 0 ? '+' : ''}${varCedido}%`
    : null;

  return (
    <Card
      size="small"
      title={
        <Space size={6}>
          <SwapOutlined style={{ color: '#A100FF' }} />
          <span style={{ color: '#1A0033', fontWeight: 700, fontSize: 13 }}>
            Modelo Fábrica — Fondos de Inversión
          </span>
        </Space>
      }
      style={{ marginTop: 16, ...cardStyle }}
      styles={{ body: { padding: '8px 16px' } }}
      extra={
        <Tag color={ratioTagColor} style={{ fontSize: 11 }}>
          Gestora: {current.ratio_gestora_pct ?? '—'}%
          {desvRatio != null && (
            <span style={{ marginLeft: 4 }}>
              ({desvRatio > 0 ? '+' : ''}{desvRatio}% vs 85%)
            </span>
          )}
        </Tag>
      }
    >
      <Row gutter={[12, 0]} align="middle">
        <Col xs={24} sm={7}>
          <Statistic
            title={<span style={{ fontSize: 11, color: '#666' }}>Cedido Gestora ({periodoLabel})</span>}
            value={current.cedido_gestora || 0}
            formatter={(v) => fmt(v)}
            prefix={<EuroCircleOutlined style={{ color: '#A100FF', fontSize: 12 }} />}
            valueStyle={{ color: '#A100FF', fontWeight: 700, fontSize: 16 }}
          />
        </Col>
        <Col xs={24} sm={7}>
          <Statistic
            title={<span style={{ fontSize: 11, color: '#666' }}>Retenido Banco ({periodoLabel})</span>}
            value={current.retenido_banco || 0}
            formatter={(v) => fmt(v)}
            prefix={<BankOutlined style={{ color: '#7B00CC', fontSize: 12 }} />}
            valueStyle={{ color: '#7B00CC', fontWeight: 700, fontSize: 16 }}
          />
        </Col>
        <Col xs={24} sm={5}>
          <Statistic
            title={<span style={{ fontSize: 11, color: '#666' }}>Contratos Fondo</span>}
            value={current.contratos_fondo || 0}
            prefix={<ContainerOutlined style={{ color: '#5500AA', fontSize: 12 }} />}
            valueStyle={{ color: '#5500AA', fontWeight: 700, fontSize: 16 }}
            suffix={<span style={{ fontSize: 11, color: '#999', fontWeight: 400 }}>ctos</span>}
          />
        </Col>
        <Col xs={24} sm={5} style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Variación MoM</div>
          {varDisplay != null ? (
            <span style={{
              fontSize: 15,
              fontWeight: 700,
              color: varCedido >= 0 ? '#52c41a' : '#ff4d4f'
            }}>
              {varCedido >= 0 ? '▲' : '▼'} {varDisplay}
            </span>
          ) : (
            <span style={{ fontSize: 15, color: '#ccc' }}>—</span>
          )}
        </Col>
      </Row>
    </Card>
  );
};

export default FabricaModelSection;
