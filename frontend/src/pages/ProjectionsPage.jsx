import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Row, Col, Button, Table, Typography, message } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import api from '../services/api';

import ForecastChart from '../components/Forecast/ForecastChart';
import ScenarioKPICards from '../components/Forecast/ScenarioKPICards';
import ScenarioConfigurator from '../components/Forecast/ScenarioConfigurator';
import MacroContextPanel from '../components/Forecast/MacroContextPanel';
import ForecastChat from '../components/Forecast/ForecastChat';

const { Title } = Typography;

const ProjectionsPage = ({ mode = 'direccion' }) => {
  const navigate = useNavigate();
  const { gestorId } = useParams();

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

  // Load dimensiones on mount
  useEffect(() => {
    api.forecast.dimensiones().then(setDimensiones).catch(() => {});
  }, []);

  // Load historicos on mount
  useEffect(() => {
    api.forecast.historicos({ dimension: config.dimension, filtro_id: config.filtroId })
      .then(setHistoricos)
      .catch(() => setHistoricos([]));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Initial calculation
  useEffect(() => {
    calcular();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const calcular = useCallback(async () => {
    setIsLoading(true);
    try {
      const hasShocks = Object.values(config.shocks).some(v => v !== 0);
      let result;
      if (hasShocks) {
        result = await api.forecast.whatif({
          shocks: config.shocks,
          horizonte_meses: config.horizonte,
          dimension: config.dimension,
          filtro_id: config.filtroId,
        });
      } else {
        result = await api.forecast.base({
          horizonte_meses: config.horizonte,
          dimension: config.dimension,
          filtro_id: config.filtroId,
        });
      }
      setEscenarios(result);
    } catch (e) {
      message.error('Error calculando proyecciones');
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, [config]);

  // Table data
  const tableData = escenarios?.escenario_base?.valores?.map((b, i) => ({
    key: b.periodo,
    periodo: b.periodo,
    pesimista: escenarios.escenario_pesimista?.valores?.[i]?.valor,
    base: b.valor,
    optimista: escenarios.escenario_optimista?.valores?.[i]?.valor,
  })) || [];

  const fmt = (v) => v != null ? `€${Math.round(v).toLocaleString('es-ES')}` : '—';

  const columns = [
    { title: 'Periodo', dataIndex: 'periodo', key: 'periodo', width: 100,
      render: v => <span style={{ color: '#94A3B8' }}>{v}</span> },
    { title: 'Pesimista', dataIndex: 'pesimista', key: 'pes',
      render: v => <span style={{ color: '#FF6B6B' }}>{fmt(v)}</span> },
    { title: 'Base', dataIndex: 'base', key: 'base',
      render: v => <span style={{ color: '#E2E8F0', fontWeight: 600 }}>{fmt(v)}</span> },
    { title: 'Optimista', dataIndex: 'optimista', key: 'opt',
      render: v => <span style={{ color: '#4ADE80' }}>{fmt(v)}</span> },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0D0D1A 0%, #111827 100%)',
      color: '#E2E8F0',
    }}>
      {/* Header */}
      <div style={{
        padding: '12px 24px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', gap: 12,
        background: 'rgba(13,13,26,0.8)', backdropFilter: 'blur(10px)',
      }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}
          ghost style={{ color: '#94A3B8', borderColor: '#334155' }}>
          Dashboard
        </Button>
        <Title level={4} style={{ color: '#E2E8F0', margin: 0, flex: 1 }}>
          CDG Intelligence — Proyecciones
        </Title>
        <span style={{
          fontSize: 10, color: '#64748B', background: 'rgba(161,0,255,0.1)',
          borderRadius: 4, padding: '2px 8px'
        }}>
          Prophet + GPT-4o
        </span>
      </div>

      {/* 3 columns */}
      <Row gutter={[12, 12]} style={{ padding: '12px 16px', height: 'calc(100vh - 52px)' }}>
        {/* Left: Config + Macro */}
        <Col xs={24} lg={6} style={{ display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto', maxHeight: 'calc(100vh - 76px)' }}>
          <ScenarioConfigurator
            config={config}
            onChange={setConfig}
            onCalcular={calcular}
            isLoading={isLoading}
            dimensiones={dimensiones}
          />
          <MacroContextPanel />
        </Col>

        {/* Center: Chart + KPIs + Table */}
        <Col xs={24} lg={12} style={{ display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto', maxHeight: 'calc(100vh - 76px)' }}>
          <ForecastChart
            historicos={historicos}
            escenarios={{
              base: escenarios?.escenario_base?.valores || [],
              optimista: escenarios?.escenario_optimista?.valores || [],
              pesimista: escenarios?.escenario_pesimista?.valores || [],
            }}
            isLoading={isLoading}
          />
          <ScenarioKPICards
            escenarios={escenarios}
            ingresoActual={escenarios?.ingresos_actual || 0}
            isLoading={isLoading}
          />
          <div style={{
            background: 'rgba(15,23,42,0.6)', borderRadius: 10,
            border: '1px solid rgba(255,255,255,0.06)', padding: 12,
          }}>
            <Table
              dataSource={tableData}
              columns={columns}
              pagination={false}
              size="small"
              style={{ background: 'transparent' }}
            />
          </div>
          {escenarios?.nota_metodologica && (
            <div style={{ color: '#475569', fontSize: 11, padding: '4px 8px', lineHeight: 1.4 }}>
              {escenarios.nota_metodologica}
            </div>
          )}
        </Col>

        {/* Right: Chat */}
        <Col xs={24} lg={6} style={{ height: 'calc(100vh - 76px)' }}>
          <ForecastChat
            mode={mode}
            gestorId={gestorId}
            perioBase="2026-04"
          />
        </Col>
      </Row>
    </div>
  );
};

export default ProjectionsPage;
