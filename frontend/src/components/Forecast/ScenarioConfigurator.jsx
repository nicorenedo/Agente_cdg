import React from 'react';
import { Radio, Select, Slider, Button, Divider, Collapse } from 'antd';
import { ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons';

const ScenarioConfigurator = ({ config, onChange, onCalcular, isLoading, dimensiones = {} }) => {
  const { horizonte = 6, dimension = 'entidad', filtroId = null, shocks = {} } = config;
  const hasShocks = Object.values(shocks).some(v => v !== 0);

  const update = (key, val) => onChange({ ...config, [key]: val });
  const updateShock = (key, val) => onChange({ ...config, shocks: { ...shocks, [key]: val } });
  const resetShocks = () => onChange({
    ...config,
    shocks: { tipos_interes: 0, captacion_clientes: 0, reduccion_gastos: 0, mix_productos: 0 }
  });

  const cardStyle = {
    background: 'rgba(15,23,42,0.6)', borderRadius: 10,
    border: '1px solid rgba(255,255,255,0.06)', padding: 16
  };
  const labelStyle = { color: '#94A3B8', fontSize: 12, marginBottom: 6, display: 'block' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Horizonte */}
      <div style={cardStyle}>
        <span style={labelStyle}>Horizonte temporal</span>
        <Radio.Group value={horizonte} onChange={e => update('horizonte', e.target.value)}
          buttonStyle="solid" size="small" style={{ width: '100%' }}>
          <Radio.Button value={3} style={{ width: '33%', textAlign: 'center' }}>3 meses</Radio.Button>
          <Radio.Button value={6} style={{ width: '34%', textAlign: 'center' }}>6 meses</Radio.Button>
          <Radio.Button value={12} style={{ width: '33%', textAlign: 'center' }}>12 meses</Radio.Button>
        </Radio.Group>
      </div>

      {/* Dimensión */}
      <div style={cardStyle}>
        <span style={labelStyle}>Dimensión</span>
        <Select value={dimension} onChange={v => { update('dimension', v); update('filtroId', null); }}
          style={{ width: '100%', marginBottom: 8 }} size="small"
          options={[
            { value: 'entidad', label: 'Entidad completa' },
            { value: 'centro', label: 'Por centro' },
            { value: 'gestor', label: 'Por gestor' },
          ]}
        />
        {dimension === 'centro' && (
          <Select value={filtroId} onChange={v => update('filtroId', v)}
            placeholder="Selecciona centro" style={{ width: '100%' }} size="small"
            options={(dimensiones.centros || []).map(c => ({ value: String(c.id), label: c.nombre }))}
          />
        )}
        {dimension === 'gestor' && (
          <Select value={filtroId} onChange={v => update('filtroId', v)}
            placeholder="Selecciona gestor" style={{ width: '100%' }} size="small" showSearch
            filterOption={(input, opt) => opt.label.toLowerCase().includes(input.toLowerCase())}
            options={(dimensiones.gestores || []).map(g => ({ value: String(g.id), label: g.nombre }))}
          />
        )}
      </div>

      {/* Shocks */}
      <Collapse ghost expandIconPosition="end"
        items={[{
          key: 'shocks',
          label: <span style={{ color: '#94A3B8', fontSize: 12 }}>
            <ThunderboltOutlined style={{ marginRight: 4 }} />
            Escenarios What-If {hasShocks && <span style={{ color: '#A100FF' }}>(activos)</span>}
          </span>,
          children: (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <span style={{ color: '#94A3B8', fontSize: 11 }}>
                  Tipos interés: <b style={{ color: '#E2E8F0' }}>{shocks.tipos_interes || 0} pb</b>
                </span>
                <Slider min={-100} max={200} step={25} value={shocks.tipos_interes || 0}
                  onChange={v => updateShock('tipos_interes', v)} />
              </div>
              <div>
                <span style={{ color: '#94A3B8', fontSize: 11 }}>
                  Captación: <b style={{ color: '#E2E8F0' }}>{shocks.captacion_clientes || 0}%</b>
                </span>
                <Slider min={-50} max={50} step={5} value={shocks.captacion_clientes || 0}
                  onChange={v => updateShock('captacion_clientes', v)} />
              </div>
              <div>
                <span style={{ color: '#94A3B8', fontSize: 11 }}>
                  Gastos: <b style={{ color: '#E2E8F0' }}>-{shocks.reduccion_gastos || 0}%</b>
                </span>
                <Slider min={0} max={30} step={5} value={shocks.reduccion_gastos || 0}
                  onChange={v => updateShock('reduccion_gastos', v)} />
              </div>
              {hasShocks && (
                <Button size="small" icon={<ReloadOutlined />} onClick={resetShocks} ghost
                  style={{ color: '#94A3B8', borderColor: '#334155' }}>
                  Resetear shocks
                </Button>
              )}
            </div>
          ),
        }]}
        style={{ background: 'rgba(15,23,42,0.6)', borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)' }}
      />

      {/* Calcular */}
      <Button type="primary" size="large" loading={isLoading} onClick={onCalcular}
        style={{
          width: '100%', background: 'linear-gradient(135deg, #A100FF 0%, #00C2FF 100%)',
          border: 'none', height: 44, fontSize: 14, fontWeight: 600, borderRadius: 8
        }}>
        {isLoading ? 'Calculando...' : 'Calcular Proyección'}
      </Button>
    </div>
  );
};

export default ScenarioConfigurator;
