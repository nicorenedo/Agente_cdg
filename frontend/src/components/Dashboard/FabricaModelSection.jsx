/**
 * FabricaModelSection.jsx
 * Modelo Fábrica — Fondos de Inversión (banda compacta, ~140px)
 * Solo visible en DireccionView (CDG/Dirección).
 */
import React, { useEffect, useState, useCallback } from 'react';
import { Card, Row, Col, Statistic, Spin, Alert, Tag, Space } from 'antd';
import { BankOutlined, PercentageOutlined, SwapOutlined, ContainerOutlined } from '@ant-design/icons';
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

  const oct = data.oct_2025 || {};
  const sep = data.sep_2025 || {};
  const desvRatio = data.desviacion_ratio_vs_target ?? null;
  const varCedido = data.variacion_cedido_pct ?? null;

  const ratioStatus = desvRatio == null ? null : Math.abs(desvRatio) < 1 ? 'success' : Math.abs(desvRatio) < 3 ? 'warning' : 'error';
  const ratioTagColor = ratioStatus === 'success' ? 'green' : ratioStatus === 'warning' ? 'orange' : 'red';

  const varSepOct = varCedido != null
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
          Gestora: {oct.ratio_gestora_pct ?? '—'}%
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
            title={<span style={{ fontSize: 11, color: '#666' }}>Cedido Gestora (oct)</span>}
            value={oct.cedido_gestora || 0}
            formatter={(v) => fmt(v)}
            prefix={<PercentageOutlined style={{ color: '#A100FF', fontSize: 12 }} />}
            valueStyle={{ color: '#A100FF', fontWeight: 700, fontSize: 16 }}
          />
        </Col>
        <Col xs={24} sm={7}>
          <Statistic
            title={<span style={{ fontSize: 11, color: '#666' }}>Retenido Banco (oct)</span>}
            value={oct.retenido_banco || 0}
            formatter={(v) => fmt(v)}
            prefix={<BankOutlined style={{ color: '#7B00CC', fontSize: 12 }} />}
            valueStyle={{ color: '#7B00CC', fontWeight: 700, fontSize: 16 }}
          />
        </Col>
        <Col xs={24} sm={5}>
          <Statistic
            title={<span style={{ fontSize: 11, color: '#666' }}>Contratos Fondo</span>}
            value={oct.contratos_fondo || 0}
            prefix={<ContainerOutlined style={{ color: '#5500AA', fontSize: 12 }} />}
            valueStyle={{ color: '#5500AA', fontWeight: 700, fontSize: 16 }}
            suffix={<span style={{ fontSize: 11, color: '#999', fontWeight: 400 }}>ctos</span>}
          />
        </Col>
        <Col xs={24} sm={5} style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 2 }}>Variación oct vs sep</div>
          {varSepOct != null ? (
            <span style={{
              fontSize: 15,
              fontWeight: 700,
              color: varCedido >= 0 ? '#52c41a' : '#ff4d4f'
            }}>
              {varCedido >= 0 ? '▲' : '▼'} {varSepOct}
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
