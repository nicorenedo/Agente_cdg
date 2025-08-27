// src/pages/GestorView.jsx
// Vista de gestor ANTI-BUCLE INFINITO - Completamente optimizada

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

  // Estados principales
  const [loading, setLoading] = useState(true);
  const [gestoresLoading, setGestoresLoading] = useState(false);
  const [availableGestores, setAvailableGestores] = useState([]);
  const [selectedGestorId, setSelectedGestorId] = useState(urlGestorId || searchParams.get('gestor') || null);
  const [selectedGestorInfo, setSelectedGestorInfo] = useState(null);
  const [error, setError] = useState(null);

  // 🔥 ANTI-BUCLE: Refs para controlar inicialización
  const isInitialized = useRef(false);
  const isFetching = useRef(false);

  // 🔥 SOLUCIÓN 1: UserId memoizado
  const userId = useMemo(() => 'gestor_user_001', []);

  // 🔥 VERSIÓN CORREGIDA del fetchAvailableGestores
  const fetchAvailableGestores = useCallback(async () => {
    if (isFetching.current || gestoresLoading) return;
    
    isFetching.current = true;
    setGestoresLoading(true);
    setError(null);
    
    try {
      let gestoresData = [];
    
      try {
        console.log('🔄 Intentando cargar gestores...');
        const response = await api.getGestores();
        console.log('📦 Respuesta API:', response);
        
        if (response && response.data && response.data.gestores) {
          gestoresData = response.data.gestores
            .filter(g => g.gestor_id != null && g.gestor_id !== undefined) // ✅ Filtro mejorado
            .map(g => ({
              id: String(g.gestor_id), // ✅ Asegurar que sea string
              nombre: g.nombre || g.desc_gestor || 'Sin nombre',
              centro: g.centro || g.desc_centro || 'Sin centro',
              segmento: g.segmento || g.desc_segmento || 'No especificado'
            }));
            
          console.log('✅ Gestores procesados:', gestoresData.length);
        }
      } catch (error) {
        console.warn('⚠️ Endpoint getGestores falló, usando ranking fallback');
        
        // Fallback mejorado
        try {
          const rankingResponse = await api.getComparativeRanking('2025-10', 'margen_neto');
          if (rankingResponse && rankingResponse.data && rankingResponse.data.ranking) {
            gestoresData = rankingResponse.data.ranking
              .filter(g => g.gestor_id != null && g.gestor_id !== undefined)
              .map(g => ({
                id: String(g.gestor_id),
                nombre: g.desc_gestor || 'Sin nombre',
                centro: g.desc_centro || 'Sin centro',
                segmento: g.desc_segmento || 'No especificado'
              }));
          }
        } catch (fallbackError) {
          console.error('❌ Fallback también falló:', fallbackError);
        }
      }
    
      console.log('🎯 Total gestores encontrados:', gestoresData.length);
    
      if (gestoresData.length > 0) {
        // Eliminar duplicados y ordenar
        const gestoresUnicos = Array.from(
          new Map(gestoresData.map(g => [g.id, g])).values()
        ).sort((a, b) => a.nombre.localeCompare(b.nombre));
      
        setAvailableGestores(gestoresUnicos);
      
        // Solo establecer selección si no hay gestor seleccionado
        if (!selectedGestorId && gestoresUnicos.length > 0) {
          const gestorToSelect = urlGestorId 
            ? gestoresUnicos.find(g => g.id === urlGestorId) || gestoresUnicos[0]
            : gestoresUnicos[0];
          
          setSelectedGestorId(gestorToSelect.id);
          setSelectedGestorInfo(gestorToSelect);
          
          const currentUrlGestor = searchParams.get('gestor');
          if (currentUrlGestor !== gestorToSelect.id) {
            setSearchParams({ gestor: gestorToSelect.id });
          }
        }
      } else {
        // ✅ Usar datos de fallback siempre disponibles
        console.log('📋 Usando datos fallback');
        const fallbackGestores = [
          { id: 'G001', nombre: 'García Martínez, José', centro: 'Madrid Centro', segmento: 'Banca Personal' },
          { id: 'G002', nombre: 'López Fernández, María', centro: 'Barcelona Norte', segmento: 'Banca Empresas' },
          { id: 'G003', nombre: 'Rodríguez Sánchez, Carlos', centro: 'Valencia Sur', segmento: 'Banca Privada' }
        ];
      
        setAvailableGestores(fallbackGestores);
        if (!selectedGestorId) {
          setSelectedGestorId(fallbackGestores[0].id);
          setSelectedGestorInfo(fallbackGestores[0]);
          setSearchParams({ gestor: fallbackGestores[0].id });
        }
      }
    
    } catch (error) {
      console.error('❌ Error crítico cargando gestores:', error);
      setError('Error de conexión con el servidor');
      message.error('Error al cargar gestores. Usando datos de ejemplo.');
      
      // Fallback final
      const emergencyFallback = [
        { id: 'DEMO1', nombre: 'Gestor Demo 1', centro: 'Centro Demo', segmento: 'Demo' }
      ];
      setAvailableGestores(emergencyFallback);
      setSelectedGestorId(emergencyFallback[0].id);
      setSelectedGestorInfo(emergencyFallback[0]);
      
    } finally {
      setGestoresLoading(false);
      isFetching.current = false;
    }
  }, [gestoresLoading, selectedGestorId, setSearchParams, urlGestorId, searchParams]);


  // 🔥 SOLUCIÓN ANTI-BUCLE: useEffect de inicialización UNA SOLA VEZ
  useEffect(() => {
    if (isInitialized.current) return;
    
    let isMounted = true;
    isInitialized.current = true;

    const initializeView = async () => {
      if (!isMounted) return;
      
      setLoading(true);
      
      try {
        await fetchAvailableGestores();
      } catch (error) {
        console.error('Error inicializando vista:', error);
      } finally {
        if (isMounted) {
          setTimeout(() => setLoading(false), 300);
        }
      }
    };

    initializeView();

    return () => {
      isMounted = false;
    };
  }, []); // ✅ DEPENDENCIAS VACÍAS - Solo se ejecuta UNA vez

  // 🔥 SOLUCIÓN 4: Handlers memoizados CON PROTECCIÓN
  const handleGestorChange = useCallback((gestorId) => {
    if (selectedGestorId === gestorId) return; // ✅ Evitar cambios innecesarios
    
    const gestorInfo = availableGestores.find(g => g.id === gestorId);
    setSelectedGestorId(gestorId);
    setSelectedGestorInfo(gestorInfo);
    setSearchParams({ gestor: gestorId });
    message.success(`Dashboard cargado para ${gestorInfo?.nombre}`);
  }, [availableGestores, setSearchParams, selectedGestorId]);

  const handleRefresh = useCallback(async () => {
    if (isFetching.current) return; // ✅ Evitar múltiples refreshes
    await fetchAvailableGestores();
  }, [fetchAvailableGestores]);

  const handleGoBack = useCallback(() => {
    navigate('/');
  }, [navigate]);

  // 🔥 SOLUCIÓN 5: Selector memoizado
  const renderGestorSelector = useMemo(() => (
    <Card 
      variant="outlined"
      style={{ 
        marginBottom: theme.spacing.lg,
        background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}, ${theme.colors.bmGreenPrimary})`,
        color: 'white',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
      }}
    >
      <Row justify="space-between" align="middle">
        <Col>
          <Space align="center" size="large">
            <img 
              src={BancaMarchLogo} 
              alt="Banca March" 
              style={{ height: '35px', filter: 'brightness(0) invert(1)' }}
            />
            <div>
              <Title level={3} style={{ color: 'white', margin: 0, fontWeight: 600 }}>
                <UserOutlined style={{ marginRight: 8 }} />
                Dashboard de Gestor Comercial
              </Title>
              <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
                Selecciona un gestor para visualizar su panel de control personalizado
              </Text>
            </div>
          </Space>
        </Col>

        <Col>
          <Space>
            <Tooltip title="Actualizar lista de gestores">
              <Button 
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
                loading={gestoresLoading}
                style={{ 
                  borderColor: 'white',
                  color: 'white',
                  background: 'transparent'
                }}
              />
            </Tooltip>

            <Button
              icon={<ArrowLeftOutlined />}
              onClick={handleGoBack}
              style={{ 
                borderColor: 'white',
                color: 'white',
                background: 'transparent'
              }}
            >
              Volver a Inicio
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Selector de gestor */}
      <div style={{ marginTop: theme.spacing.md }}>
        <Row gutter={16} align="middle">
          <Col xs={24} md={4}>
            <Text style={{ color: 'white', fontWeight: 500, fontSize: '14px' }}>
              <TeamOutlined style={{ marginRight: 4 }} />
              Seleccionar Gestor:
            </Text>
          </Col>
          <Col xs={24} md={16}>
            <Select
              showSearch
              loading={gestoresLoading}
              placeholder="Busca y selecciona un gestor..."
              value={selectedGestorId}
              onChange={handleGestorChange}
              style={{ width: '100%' }}
              size="large"
              optionFilterProp="children"
              filterOption={(input, option) =>
                option.children.props.children[0].props.children.toLowerCase().includes(input.toLowerCase())
              }
              notFoundContent={gestoresLoading ? <Spin size="small" /> : 'No se encontraron gestores'}
            >
              {availableGestores
                .filter(gestor => gestor.id !== null && gestor.id !== undefined)
                .map((gestor) => (
                <Option key={`gestor-${gestor.id}`} value={gestor.id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 500 }}>{gestor.nombre}</span>
                    <span style={{ fontSize: '12px', color: '#999', marginLeft: 8 }}>
                      {gestor.centro} • {gestor.segmento}
                    </span>
                  </div>
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={4}>
            <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>
              {availableGestores.length} gestores disponibles
            </Text>
          </Col>
        </Row>
      </div>

      {/* Información del gestor seleccionado */}
      {selectedGestorInfo && (
        <div style={{
          marginTop: theme.spacing.md,
          padding: theme.spacing.sm,
          backgroundColor: 'rgba(255,255,255,0.1)',
          borderRadius: 6,
          border: '1px solid rgba(255,255,255,0.2)'
        }}>
          <Text style={{ color: 'white', fontSize: '13px' }}>
            <strong>Gestor Seleccionado:</strong> {selectedGestorInfo.nombre} | 
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
    handleGestorChange, 
    handleGoBack
  ]);

  // Props memoizadas para GestorDashboard
  const dashboardProps = useMemo(() => ({
    userId,
    gestorId: selectedGestorId,
    periodo: new Date().toISOString().slice(0, 7)
  }), [userId, selectedGestorId]);

  // Loading inicial
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: theme.colors.backgroundLight,
        background: `linear-gradient(135deg, ${theme.colors.bmGreenDark}15, ${theme.colors.bmGreenPrimary}10)`
      }}>
        <Space direction="vertical" align="center" size="large">
          <img 
            src={BancaMarchLogo} 
            alt="Banca March" 
            style={{ height: '50px', marginBottom: theme.spacing.lg }}
          />
          <Spin size="large" />
          <div style={{ textAlign: 'center' }}>
            <Title level={4} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
              Inicializando Vista de Gestor
            </Title>
            <Text style={{ 
              color: theme.colors.textSecondary,
              fontSize: '14px',
              marginTop: theme.spacing.sm
            }}>
              Cargando lista de gestores y configurando dashboard...
            </Text>
          </div>
        </Space>
      </div>
    );
  }

  // Error crítico
  if (error && availableGestores.length === 0) {
    return (
      <div style={{ 
        padding: theme.spacing.xl,
        backgroundColor: theme.colors.backgroundLight,
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <Alert
          message="Error de Conexión"
          description={error}
          type="error"
          showIcon
          style={{ maxWidth: '500px' }}
          action={
            <Space>
              <Button 
                type="primary" 
                onClick={handleRefresh}
                loading={gestoresLoading}
                style={{
                  backgroundColor: theme.colors.bmGreenPrimary,
                  borderColor: theme.colors.bmGreenPrimary
                }}
              >
                Reintentar
              </Button>
              <Button onClick={handleGoBack}>
                Volver a Inicio
              </Button>
            </Space>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundColor: theme.colors.backgroundLight,
      background: `linear-gradient(180deg, ${theme.colors.backgroundLight} 0%, ${theme.colors.background} 100%)`
    }}>
      
      {/* Header con selector de gestor */}
      {renderGestorSelector}

      {/* Dashboard del gestor seleccionado - PROPS MEMOIZADAS */}
      {selectedGestorId ? (
        <GestorDashboard {...dashboardProps} />
      ) : (
        <div style={{ padding: `0 ${theme.spacing.lg}` }}>
          <Card variant="outlined" style={{ textAlign: 'center', padding: theme.spacing.xl }}>
            <Space direction="vertical" size="large">
              <UserOutlined style={{ fontSize: '48px', color: theme.colors.textSecondary }} />
              <div>
                <Title level={4} style={{ color: theme.colors.textSecondary }}>
                  Selecciona un Gestor
                </Title>
                <Paragraph style={{ color: theme.colors.textSecondary }}>
                  Por favor, selecciona un gestor de la lista desplegable para visualizar su dashboard personalizado.
                </Paragraph>
              </div>
              {availableGestores.length > 0 && (
                <Button 
                  type="primary"
                  size="large"
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
        padding: theme.spacing.lg,
        textAlign: 'center',
        borderTop: `1px solid ${theme.colors.border}`,
        backgroundColor: theme.colors.background,
        marginTop: theme.spacing.xl
      }}>
        <Text style={{ 
          color: theme.colors.textSecondary,
          fontSize: '12px'
        }}>
          Dashboard de Gestor - Banca March CDG | © 2025
        </Text>
      </div>
    </div>
  );
};

export default GestorView;
