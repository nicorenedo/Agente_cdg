// frontend/src/components/common/TopBar.jsx
import React, { useEffect, useState, useCallback } from 'react';
import { Row, Col, Select, DatePicker, Button, Space, Modal, Typography } from 'antd';
import { ReloadOutlined, QuestionCircleOutlined, CalendarOutlined, UserOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import dayjs from 'dayjs';
import api from '../../services/api';
import theme from '../../styles/theme';

const { Option } = Select;
const { Title, Paragraph } = Typography;

/**
 * TopBar - Barra superior fija para navegación del dashboard CDG
 * Integrada con endpoints corporativos y tema Banca March
 */
const TopBar = ({
  valuePeriod,
  onPeriodChange,
  valueGestor = null,
  onGestorChange = null,
  onRefresh,
  compact = false,
  showHelp = true,
}) => {
  const [periods, setPeriods] = useState([]);
  const [gestores, setGestores] = useState([]);
  const [loading, setLoading] = useState(false);
  const [helpVisible, setHelpVisible] = useState(false);

  // Cargar períodos desde /periods
  const loadPeriods = useCallback(async () => {
    try {
      const data = await api.catalogs.periods();
      setPeriods(Array.isArray(data) ? data : []);
    } catch (error) {
      console.warn('[TopBar] Error cargando períodos:', error.message);
      setPeriods([]);
    }
  }, []);

  // Cargar gestores desde /basic/gestores (solo si se necesita selector)
  const loadGestores = useCallback(async () => {
    if (!onGestorChange) return;
    
    try {
      const data = await api.basic.gestoresRanking();
      const gestoresList = Array.isArray(data) ? data
        .filter(g => {
          // Filtrar gestores con id válido (no null, undefined, o vacío)
          const id = g.GESTORID || g.gestor_id || g.id;
          return id !== null && id !== undefined && id !== '';
        })
        .map(g => ({
          id: g.GESTORID || g.gestor_id || g.id,
          name: g.DESCGESTOR || g.nombre || g.name || `Gestor ${g.GESTORID || g.id}`,
        })) : [];
      setGestores(gestoresList);
    } catch (error) {
      console.warn('[TopBar] Error cargando gestores:', error.message);
      setGestores([]);
    }
  }, [onGestorChange]);

  // Cargar datos iniciales
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await Promise.all([
        loadPeriods(),
        loadGestores(),
      ]);
      setLoading(false);
    };
    
    loadInitialData();
  }, [loadPeriods, loadGestores]);

  // Convertir período a dayjs - MANEJA TANTO STRING COMO OBJECT
  const toDate = useCallback((period) => {
    if (!period) return null;
    
    // Si es string, úsalo directamente
    if (typeof period === 'string') {
      return dayjs(period, 'YYYY-MM');
    }
    
    // Si es objeto, extraer el valor string
    if (typeof period === 'object' && period !== null) {
      const periodStr = period.latest || period.value || period.periodo || '';
      return periodStr ? dayjs(periodStr, 'YYYY-MM') : null;
    }
    
    return null;
  }, []);

  // Manejar cambio de período
  const handlePeriodChange = useCallback((date, dateString) => {
    if (onPeriodChange && dateString) {
      onPeriodChange(dateString);
    }
  }, [onPeriodChange]);

  // Manejar cambio de gestor
  const handleGestorChange = useCallback((value) => {
    if (onGestorChange) {
      onGestorChange(value || null);
    }
  }, [onGestorChange]);

  // Manejar refresh con loading
  const handleRefresh = useCallback(async () => {
    if (onRefresh) {
      setLoading(true);
      try {
        await onRefresh();
      } catch (error) {
        console.warn('[TopBar] Error en refresh:', error.message);
      } finally {
        setLoading(false);
      }
    }
  }, [onRefresh]);

  const topBarStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 1000,
    backgroundColor: theme.colors.backgroundLight,
    borderBottom: `1px solid ${theme.colors.border}`,
    padding: compact ? `${theme.spacing.xs} ${theme.spacing.sm}` : `${theme.spacing.sm} ${theme.spacing.md}`,
    fontFamily: theme.token.fontFamily,
    boxShadow: '0 2px 8px rgba(27, 94, 85, 0.08)',
  };

  return (
    <>
      <div style={topBarStyle}>
        <Row align="middle" justify="space-between" gutter={[16, 8]}>
          <Col flex="auto">
            <Space 
              direction={compact ? 'vertical' : 'horizontal'} 
              size={compact ? 8 : 16}
              wrap
            >
              {/* Selector de Período */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CalendarOutlined style={{ color: theme.colors.bmGreenPrimary }} />
                <DatePicker
                  picker="month"
                  value={toDate(valuePeriod)}
                  onChange={handlePeriodChange}
                  size={compact ? 'small' : 'middle'}
                  format="YYYY-MM"
                  allowClear={false}
                  placeholder="Seleccionar período"
                  style={{ 
                    minWidth: compact ? 120 : 140,
                    fontFamily: theme.token.fontFamily
                  }}
                />
              </div>

              {/* Selector de Gestor (opcional) */}
              {onGestorChange && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <UserOutlined style={{ color: theme.colors.bmGreenPrimary }} />
                  <Select
                    showSearch
                    allowClear
                    placeholder={compact ? 'Gestor' : 'Seleccionar Gestor'}
                    value={valueGestor}
                    onChange={handleGestorChange}
                    size={compact ? 'small' : 'middle'}
                    style={{ 
                      minWidth: compact ? 140 : 200,
                      fontFamily: theme.token.fontFamily
                    }}
                    filterOption={(input, option) =>
                      option.children.toLowerCase().includes(input.toLowerCase())
                    }
                    notFoundContent={loading ? "Cargando..." : "Sin resultados"}
                  >
                    {gestores.map(gestor => (
                      <Option key={`gestor-${gestor.id}`} value={gestor.id}>
                        {gestor.name}
                      </Option>
                    ))}
                  </Select>
                </div>
              )}
            </Space>
          </Col>

          <Col>
            <Space size={compact ? 8 : 12}>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
                loading={loading}
                size={compact ? 'small' : 'middle'}
                style={{
                  backgroundColor: theme.colors.bmGreenPrimary,
                  borderColor: theme.colors.bmGreenPrimary,
                }}
              >
                {!compact && 'Refrescar'}
              </Button>

              {showHelp && !compact && (
                <Button
                  icon={<QuestionCircleOutlined />}
                  onClick={() => setHelpVisible(true)}
                  size="middle"
                  type="text"
                  style={{ color: theme.colors.bmGreenPrimary }}
                >
                  Ayuda
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </div>

      {/* Modal de Ayuda */}
      <Modal
        open={helpVisible}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <QuestionCircleOutlined style={{ color: theme.colors.bmGreenPrimary }} />
            <span>Panel de Control CDG</span>
          </div>
        }
        onCancel={() => setHelpVisible(false)}
        footer={[
          <Button 
            key="ok" 
            type="primary" 
            onClick={() => setHelpVisible(false)}
            style={{
              backgroundColor: theme.colors.bmGreenPrimary,
              borderColor: theme.colors.bmGreenPrimary,
            }}
          >
            Entendido
          </Button>
        ]}
        centered
        width={500}
      >
        <Space direction="vertical" size={16} style={{ width: '100%' }}>
          <div>
            <Title level={5} style={{ color: theme.colors.bmGreenPrimary, margin: 0 }}>
              Sistema de Control de Gestión
            </Title>
            <Paragraph style={{ margin: '8px 0 0 0', color: theme.colors.textSecondary }}>
              Dashboard corporativo para análisis financiero y operativo de Banca March
            </Paragraph>
          </div>

          <div>
            <Title level={5} style={{ margin: 0 }}>Funcionalidades</Title>
            <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
              <li>Selección de período para análisis temporal</li>
              <li>Filtros por gestor para análisis específico</li>
              <li>Actualización de datos en tiempo real</li>
              <li>Análisis de KPIs y desviaciones</li>
            </ul>
          </div>

          <Paragraph style={{ fontSize: 12, color: theme.colors.textLight, margin: 0 }}>
            Para soporte técnico, contacte con el equipo de sistemas corporativo.
          </Paragraph>
        </Space>
      </Modal>
    </>
  );
};

TopBar.propTypes = {
  valuePeriod: PropTypes.oneOfType([PropTypes.string, PropTypes.object]).isRequired,
  onPeriodChange: PropTypes.func.isRequired,
  valueGestor: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onGestorChange: PropTypes.func,
  onRefresh: PropTypes.func.isRequired,
  compact: PropTypes.bool,
  showHelp: PropTypes.bool,
};

export default TopBar;
