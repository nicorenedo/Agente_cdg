// src/pages/LandingPage.jsx
// Landing Page v5.1 – Selector limpio e integrado (FIX: usa api.agent.gestores)

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button, Row, Col, Select, Typography, Space, Spin, Card,
  Badge, Tooltip, Divider, Alert, App
} from 'antd';
import {
  ArrowRightOutlined, UserOutlined, TeamOutlined, DashboardOutlined,
  ReloadOutlined, SearchOutlined, CrownOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';

import api from '../services/api';
import theme from '../styles/theme';
import BancaMarchLogo from '../assets/BancaMarchlogo.png';
import FondoInterfaz from '../assets/FondoInterfazBM.png';

const { Option } = Select;
const { Title, Text } = Typography;

/* ───────────────────────────────────────────── */
/* 🔧 Landing Page Content                       */
/* ───────────────────────────────────────────── */
const LandingPageContent = () => {
  const navigate = useNavigate();
  const { message, notification } = App.useApp();

  const [gestores, setGestores] = useState([]);
  const [selectedGestor, setSelectedGestor] = useState(null);
  const [selectedGestorInfo, setSelectedGestorInfo] = useState(null);
  const [loadingGestores, setLoadingGestores] = useState(false);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState('checking');

// LandingPage.jsx - LÍNEA CORREGIDA (~41)

  /* ───── ✅ FIX: usar api.basic.allGestores() - Endpoint específico para gestores ───── */
  const fetchGestores = useCallback(async () => {
    setLoadingGestores(true);
    setSystemStatus('loading');
    setError(null);

    try {
      // ✅ CORRECCIÓN: Usar el nuevo endpoint específico para gestores
      const rows = await api.basic.allGestores(); // ✅ Endpoint: /basic/gestores
      const list = Array.isArray(rows) ? rows : [];


      const mapped = list
        .map((g) => {
          // ✅ CORREGIR: usar las claves exactas que devuelve el backend
          const id = g.GESTOR_ID || g.gestor_id || g.id || null;           // ✅ GESTOR_ID (no GESTORID)
          const nombre = g.DESC_GESTOR || g.nombre || g.desc_gestor || null; // ✅ DESC_GESTOR (no DESCGESTOR)

          if (!id || !nombre) return null;

          // ✅ Usar las claves correctas del response del backend
          const centro = g.DESC_CENTRO || g.centro || g.CENTRO || 'Centro no especificado';
          const segmento = g.DESC_SEGMENTO || g.segmento || g.SEGMENTO_ID || 'Segmento no especificado';

          return {
            id: String(id),
            nombre: String(nombre),
            centro: String(centro),
            segmento: String(segmento),
            performance: 'Regular',
            displayName: `${String(nombre)} - ${String(centro)}`,
          };
        })

        .filter(Boolean)
        .sort((a, b) => a.nombre.localeCompare(b.nombre));

      if (!mapped.length) {
        throw new Error('Sin gestores disponibles');
      }

      setGestores(mapped);
      setSelectedGestor(mapped[0].id);
      setSelectedGestorInfo(mapped[0]);
      setSystemStatus('healthy');
      message.success(`${mapped.length} gestores cargados correctamente`);

    } catch (err) {
      // ✅ El fallback existing está bien
      const fallback = [
        {
          id: '18',
          nombre: 'Laia Vila Costa',
          centro: 'BARCELONA-BALMES',
          segmento: 'Banca Personal',
          performance: 'Excelente',
          displayName: 'Laia Vila Costa - BARCELONA-BALMES',
        },
        {
          id: '1',
          nombre: 'Antonio Rodríguez García',
          centro: 'MADRID-OFICINA PRINCIPAL',
          segmento: 'Banca Minorista',
          performance: 'Bueno',
          displayName: 'Antonio Rodríguez García - MADRID-OFICINA PRINCIPAL',
        },
      ];

      setGestores(fallback);
      setSelectedGestor(fallback[0].id);
      setSelectedGestorInfo(fallback[0]);
      setError('Conexión limitada – datos de demostración');
      setSystemStatus('error');

      message.warning('Usando datos de demostración');
      notification.error({
        message: 'API no disponible',
        description: `Error: ${err?.message || 'Desconocido'}. Usando datos de demostración.`,
        duration: 4,
      });
    } finally {
      setLoadingGestores(false);
    }
  }, [message, notification]);


  useEffect(() => {
    fetchGestores();
  }, [fetchGestores]);

  /* ───── Handlers ───── */
  const handleGestorChange = (id) => {
    setSelectedGestor(id);
    setSelectedGestorInfo(gestores.find((g) => g.id === id) || null);
  };

  const handleNavigateGestor = () => {
    if (!selectedGestor) {
      message.warning('Selecciona un gestor');
      return;
    }
    navigate(`/gestor-dashboard?gestor=${encodeURIComponent(selectedGestor)}`);
  };

  const handleNavigateDireccion = () => navigate('/direccion-dashboard');
  const handleRefresh = () => fetchGestores();

  /* ───── Estilos básicos ───── */
  const containerStyle = {
    height: '100vh',
    background: `linear-gradient(135deg, rgba(27, 94, 85, 0.85), rgba(18, 59, 54, 0.9)), url(${FondoInterfaz})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '2rem',
    position: 'relative',
  };

  /* ───────────────────────────────────────────── */
  /* Render                                       */
  /* ───────────────────────────────────────────── */
  return (
    <div style={containerStyle}>
      {systemStatus !== 'healthy' && (
        <Badge
          status={
            systemStatus === 'loading'
              ? 'processing'
              : systemStatus === 'error'
              ? 'error'
              : 'warning'
          }
          text={
            <Text style={{ color: 'white' }}>
              {systemStatus === 'loading'
                ? 'Cargando…'
                : systemStatus === 'error'
                ? 'Conexión limitada'
                : 'Verificando sistema'}
            </Text>
          }
          style={{ position: 'absolute', top: 24, right: 24 }}
        />
      )}

      <img src={BancaMarchLogo} alt="Banca March" style={{ maxWidth: 260, marginBottom: 32 }} />

      <Title level={1} style={{ color: 'white', marginBottom: 8, textAlign: 'center' }}>
        Sistema de Control de Gestión
      </Title>
      <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: 18, marginBottom: 48 }}>
        Plataforma Inteligente de Análisis Financiero
      </Text>

      <Row gutter={[24, 32]} justify="center" style={{ width: '100%', maxWidth: 1200 }}>
        {/* Panel Gestor */}
        <Col xs={24} lg={13}>
          <Card
            style={{
              backgroundColor: 'rgba(255,255,255,0.15)',
              backdropFilter: 'blur(15px)',
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: 20,
              textAlign: 'center',
              padding: 24,
              minHeight: 480,
            }}
          >
            <Space direction="vertical" size="large" style={{ width: '100%', height: '100%' }}>
              <UserOutlined style={{ fontSize: 46, color: '#fff' }} />
              <Title level={3} style={{ color: '#fff', margin: 0 }}>
                Panel Personal
              </Title>

              {/* Selector limpio */}
              <div style={{ width: '100%' }}>
                <Text style={{ color: '#fff', marginBottom: 8, display: 'block' }}>
                  Seleccionar Gestor Comercial
                </Text>
                <Space.Compact style={{ width: '100%' }}>
                  <Select
                    showSearch
                    placeholder="🔍 Buscar gestor…"
                    value={selectedGestor}
                    onChange={handleGestorChange}
                    loading={loadingGestores}
                    size="large"
                    style={{ flex: 1 }}
                    disabled={loadingGestores || gestores.length === 0}
                    suffixIcon={<SearchOutlined />}
                    optionFilterProp="children"
                    filterOption={(input, option) =>
                      option?.children?.toLowerCase().includes(input.toLowerCase())
                    }
                    notFoundContent={
                      loadingGestores ? <Spin size="small" style={{ margin: 12 }} /> : 'Sin resultados'
                    }
                  >
                    {gestores.map((g) => (
                      <Option key={g.id} value={g.id}>
                        {g.displayName}
                      </Option>
                    ))}
                  </Select>
                  <Tooltip title="Actualizar">
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={handleRefresh}
                      loading={loadingGestores}
                      size="large"
                      style={{
                        borderColor: 'rgba(255,255,255,0.4)',
                        backgroundColor: 'rgba(255,255,255,0.1)',
                        color: 'white',
                      }}
                    />
                  </Tooltip>
                </Space.Compact>
              </div>

              {selectedGestorInfo && (
                <Alert
                  type="success"
                  showIcon
                  description={
                    <Space direction="vertical" size={0}>
                      <Text strong>{selectedGestorInfo.nombre}</Text>
                      <Text>
                        {selectedGestorInfo.centro} • {selectedGestorInfo.segmento}
                      </Text>
                    </Space>
                  }
                  style={{ background: 'rgba(0,0,0,0.2)', color: 'white' }}
                />
              )}

              <Button
                type="primary"
                size="large"
                icon={<ArrowRightOutlined />}
                onClick={handleNavigateGestor}
                disabled={!selectedGestor}
                loading={loadingGestores}
                style={{
                  width: '100%',
                  background: `linear-gradient(135deg, ${theme.colors.bmGreenLight}, ${theme.colors.bmGreenPrimary})`,
                  border: 'none',
                }}
              >
                {loadingGestores ? 'Cargando...' : 'Acceder a Mi Panel'}
              </Button>
            </Space>
          </Card>
        </Col>

        {/* Panel Dirección */}
        <Col xs={24} lg={13}>
          <Card
            style={{
              backgroundColor: 'rgba(255,255,255,0.15)',
              backdropFilter: 'blur(15px)',
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: 20,
              textAlign: 'center',
              padding: 24,
              minHeight: 480,
            }}
          >
            <Space direction="vertical" size="large" style={{ width: '100%', height: '100%' }}>
              <DashboardOutlined style={{ fontSize: 46, color: '#fff' }} />
              <Title level={3} style={{ color: '#fff', margin: 0 }}>
                Panel Ejecutivo
              </Title>

              <Space direction="vertical" size="small">
                <div>
                  <TeamOutlined style={{ color: theme.colors.bmGreenLight }} /> Control consolidado
                </div>
                <div>
                  <ThunderboltOutlined style={{ color: theme.colors.bmGreenLight }} /> KPIs en tiempo real
                </div>
              </Space>

              <Button
                type="primary"
                size="large"
                icon={<CrownOutlined />}
                onClick={handleNavigateDireccion}
                style={{
                  width: '100%',
                  background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}, ${theme.colors.bmGreenPrimary})`,
                  border: 'none',
                  marginTop: 16,
                }}
              >
                Acceder al Panel Ejecutivo
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Footer */}
      <div style={{ position: 'absolute', bottom: 32, color: 'white', textAlign: 'center' }}>
        <Space split={<Divider type="vertical" style={{ borderColor: 'rgba(255,255,255,0.4)' }} />}>
          <span>Agente CDG ©2025 Banca March</span>
          <span>{gestores.length} gestores disponibles</span>
          <span style={{ color: systemStatus === 'healthy' ? '#52c41a' : '#fa8c16' }}>
            {systemStatus === 'healthy' ? 'Datos reales' : 'Datos demo'}
          </span>
        </Space>
      </div>
    </div>
  );
};

/* ───────────────────────────────────────────── */
/* ✅ Wrapper principal con App                  */
/* ───────────────────────────────────────────── */
const LandingPage = () => (
  <App>
    <LandingPageContent />
  </App>
);

export default LandingPage;
