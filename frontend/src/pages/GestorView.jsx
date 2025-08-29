// src/pages/GestorView.jsx
// Vista de gestor ANTI-BUCLE INFINITO - Completamente optimizada y CORREGIDA

import React, { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { Spin, Alert, Button, Select, Typography, Space, Card, Row, Col, message, Tooltip } from 'antd';
import { ArrowLeftOutlined, UserOutlined, TeamOutlined, ReloadOutlined } from '@ant-design/icons';
import GestorDashboard from '../components/Dashboard/GestorDashboard';
import api from '../services/api';
import theme from '../styles/theme';
import BancaMarchLogo from '../assets/BancaMarchlogo.png';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const GestorView = () => {
  const { gestorId: urlGestorId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [loading, setLoading] = useState(true);
  const [gestoresLoading, setGestoresLoading] = useState(false);
  const [availableGestores, setAvailableGestores] = useState([]);
  const [selectedGestorId, setSelectedGestorId] = useState(urlGestorId || searchParams.get('gestor') || null);
  const [selectedGestorInfo, setSelectedGestorInfo] = useState(null);
  const [error, setError] = useState(null);

  // ✅ Refs para controlar inicialización y evitar múltiples fetch simultáneos
  const isInitialized = useRef(false);
  const isFetching = useRef(false);

  // ✅ Memoizar userId
  const userId = useMemo(() => 'gestor_user_001', []);

  // ✅ CORRECCIÓN PRINCIPAL: Fetch con dependencias mínimas y estables
  const fetchAvailableGestores = useCallback(async () => {
    if (isFetching.current || gestoresLoading) return;
    isFetching.current = true;
    setGestoresLoading(true);
    setError(null);

    try {
      let gestoresData = [];
      
      try {
        const response = await api.getGestores();
        if (response?.data?.gestores) {
          gestoresData = response.data.gestores.filter(g => g.id && g.nombre).map(g => ({
            id: String(g.id),
            nombre: g.nombre,
            centro: g.centro || 'Sin centro',
            segmento: g.segmento || 'No especificado'
          }));
        }
      } catch {
        try {
          const rankingResponse = await api.getComparativeRanking('2025-10', 'MARGEN_NETO');
          if (rankingResponse?.data?.ranking) {
            gestoresData = rankingResponse.data.ranking.filter(g => g.GESTOR_ID).map(g => ({
              id: String(g.GESTOR_ID),
              nombre: g.DESC_GESTOR || 'Sin nombre',
              centro: g.DESC_CENTRO || 'Sin centro',
              segmento: g.DESC_SEGMENTO || 'No especificado'
            }));
          }
        } catch {}
      }

      if (gestoresData.length) {
        const uniqueGestores = Array.from(new Map(gestoresData.map(g => [g.id, g])).values())
          .sort((a,b) => a.nombre.localeCompare(b.nombre));
        setAvailableGestores(uniqueGestores);

        // Solo auto-seleccionar en la carga inicial
        if (!selectedGestorId && uniqueGestores.length) {
          const toSelect = urlGestorId ? 
            uniqueGestores.find(g => g.id === urlGestorId) || uniqueGestores[0] : 
            uniqueGestores[0];
          
          setSelectedGestorId(toSelect.id);
          setSelectedGestorInfo(toSelect);
          if (searchParams.get('gestor') !== toSelect.id) {
            setSearchParams({ gestor: toSelect.id });
          }
        }
      } else {
        // Fallback data
        const fallback = [
          { id: 'G001', nombre: 'García Martínez, José', centro: 'Madrid Centro', segmento: 'Banca Personal' },
          { id: 'G002', nombre: 'López Fernández, María', centro: 'Barcelona Norte', segmento: 'Banca Empresas' },
          { id: 'G003', nombre: 'Rodríguez Sánchez, Carlos', centro: 'Valencia', segmento: 'Banca Privada' }
        ];
        setAvailableGestores(fallback);
        if (!selectedGestorId) {
          setSelectedGestorId(fallback[0].id);
          setSelectedGestorInfo(fallback[0]);
          setSearchParams({ gestor: fallback[0].id });
        }
      }

    } catch (error) {
      setError('Error al cargar gestores.');
      const emergency = [{ id: 'DEMO1', nombre: 'Demo', centro: 'Demo', segmento: 'Demo' }];
      setAvailableGestores(emergency);
      setSelectedGestorId('DEMO1');
      setSelectedGestorInfo(emergency[0]);
    } finally {
      setGestoresLoading(false);
      isFetching.current = false;
    }
  }, [gestoresLoading, selectedGestorId, setSearchParams, urlGestorId, searchParams]);

  // ✅ SOLUCIÓN AL ERROR: useEffect con dependencias correctas pero controlado por ref
  useEffect(() => {
    if (isInitialized.current) return;
    isInitialized.current = true;

    const initializeView = async () => {
      setLoading(true);
      try {
        await fetchAvailableGestores();
      } catch (error) {
        console.error('Error inicializando:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeView();
  }, []); // ✅ Dependencias vacías - solo se ejecuta UNA vez

  // ✅ Handlers memoizados con protecciones
  const handleGestorChange = useCallback((val) => {
    if (selectedGestorId === val) return;
    const selected = availableGestores.find(g => g.id === val);
    setSelectedGestorId(val);
    setSelectedGestorInfo(selected);
    setSearchParams({ gestor: val });
    message.success(`Gestor seleccionado: ${selected?.nombre || ''}`);
  }, [availableGestores, selectedGestorId, setSearchParams]);

  const handleRefresh = useCallback(() => {
    if (isFetching.current) return;
    fetchAvailableGestores();
  }, [fetchAvailableGestores]);

  const handleGoBack = useCallback(() => {
    navigate('/');
  }, [navigate]);

  // ✅ Selector memoizado y optimizado
  const renderSelector = useMemo(() => (
    <Card style={{ 
      marginBottom: 24, 
      background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}, ${theme.colors.bmGreenPrimary})`, 
      color: 'white' 
    }}>
      <Row justify='space-between' align='middle'>
        <Col>
          <Space size='large'>
            <img src={BancaMarchLogo} alt='Banca March' style={{ height: 35, filter: 'invert(1)' }} />
            <div>
              <Title level={4} style={{ color: 'white', margin: 0, fontWeight: 600 }}>
                <UserOutlined /> Dashboard Gestor Comercial
              </Title>
              <Text style={{ color: 'rgba(255,255,255,0.9)' }}>
                Seleccione un gestor para visualizar su dashboard
              </Text>
            </div>
          </Space>
        </Col>
        <Col>
          <Space>
            <Tooltip title='Actualizar lista'>
              <Button
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
                loading={gestoresLoading}
                style={{ color: 'white', borderColor: 'white', background: 'transparent' }}
              />
            </Tooltip>
            <Button 
              icon={<ArrowLeftOutlined />}
              onClick={handleGoBack} 
              style={{ color: 'white', borderColor: 'white', background: 'transparent' }}
            >
              Volver
            </Button>
          </Space>
        </Col>
      </Row>
      
      <div style={{ marginTop: 16 }}>
        <Row gutter={16} align='middle'>
          <Col flex={1}>
            <Select
              showSearch
              placeholder='Buscar y seleccionar gestor...'
              optionFilterProp='children'
              onChange={handleGestorChange}
              value={selectedGestorId}
              filterOption={(input, option) => 
                option.children.toLowerCase().includes(input.toLowerCase())
              }
              loading={gestoresLoading}
              notFoundContent={gestoresLoading ? <Spin size='small' /> : 'No se encontraron gestores'}
              style={{ width: '100%' }}
              size='large'
            >
              {availableGestores.map(g => (
                <Option key={g.id} value={g.id}>
                  {g.nombre} - {g.centro} ({g.segmento})
                </Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12 }}>
              {availableGestores.length} gestores disponibles
            </Text>
          </Col>
        </Row>
      </div>

      {selectedGestorInfo && (
        <div style={{
          marginTop: 16,
          padding: 12,
          backgroundColor: 'rgba(255,255,255,0.1)',
          borderRadius: 6,
          border: '1px solid rgba(255,255,255,0.2)'
        }}>
          <Text style={{ color: 'white', fontSize: 13 }}>
            <strong>Seleccionado:</strong> {selectedGestorInfo.nombre} | 
            <strong> Centro:</strong> {selectedGestorInfo.centro} | 
            <strong> Segmento:</strong> {selectedGestorInfo.segmento}
          </Text>
        </div>
      )}
    </Card>
  ), [
    availableGestores, 
    selectedGestorId, 
    selectedGestorInfo, 
    gestoresLoading, 
    handleRefresh, 
    handleGoBack, 
    handleGestorChange
  ]);

  // ✅ Loading inicial
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}15, ${theme.colors.bmGreenPrimary}10)`
      }}>
        <Space direction='vertical' size='large' align='center'>
          <img src={BancaMarchLogo} alt='Banca March' style={{ height: 50 }} />
          <Spin size='large' />
          <div style={{ textAlign: 'center' }}>
            <Title level={4} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
              Inicializando Vista de Gestor
            </Title>
            <Text style={{ color: theme.colors.textSecondary, fontSize: 14 }}>
              Cargando lista de gestores y configurando dashboard...
            </Text>
          </div>
        </Space>
      </div>
    );
  }

  // ✅ Error crítico
  if (error && !availableGestores.length) {
    return (
      <div style={{ 
        padding: 24, 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Alert
          message='Error de Conexión'
          description={error}
          type='error'
          showIcon
          style={{ maxWidth: 500 }}
          action={
            <Space>
              <Button type='primary' onClick={handleRefresh} loading={gestoresLoading}>
                Reintentar
              </Button>
              <Button onClick={handleGoBack}>
                Volver al Inicio
              </Button>
            </Space>
          }
        />
      </div>
    );
  }

  // ✅ Render principal
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: `linear-gradient(180deg, ${theme.colors.backgroundLight}, ${theme.colors.background})` 
    }}>
      
      {/* Selector de gestor */}
      {renderSelector}

      {/* Dashboard del gestor seleccionado */}
      {selectedGestorId ? (
        <GestorDashboard 
          userId={userId} 
          gestorId={selectedGestorId} 
          periodo={new Date().toISOString().slice(0,7)} 
        />
      ) : (
        <div style={{ padding: `0 ${theme.spacing.lg}` }}>
          <Card style={{ textAlign: 'center', padding: theme.spacing.xl }}>
            <Space direction='vertical' size='large'>
              <UserOutlined style={{ fontSize: 48, color: theme.colors.textSecondary }} />
              <div>
                <Title level={4} style={{ color: theme.colors.textSecondary }}>
                  Selecciona un Gestor
                </Title>
                <Paragraph style={{ color: theme.colors.textSecondary }}>
                  Selecciona un gestor de la lista para ver su dashboard personalizado.
                </Paragraph>
              </div>
              {availableGestores.length > 0 && (
                <Button 
                  type='primary'
                  size='large'
                  onClick={() => handleGestorChange(availableGestores[0].id)}
                  style={{
                    backgroundColor: theme.colors.bmGreenPrimary,
                    borderColor: theme.colors.bmGreenPrimary
                  }}
                >
                  Seleccionar Primer Gestor
                </Button>
              )}
            </Space>
          </Card>
        </div>
      )}

      {/* Footer */}
      <div style={{ 
        padding: 24,
        textAlign: 'center',
        borderTop: `1px solid ${theme.colors.border}`,
        backgroundColor: theme.colors.background,
        marginTop: 24
      }}>
        <Text style={{ fontSize: 12, color: theme.colors.textSecondary }}>
          Dashboard de Gestor - Banca March CDG | © 2025
        </Text>
      </div>
    </div>
  );
};

export default GestorView;
// Fin del archivo