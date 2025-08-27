// src/pages/LandingPage.jsx
// Landing page mejorada con selector de gestor integrado con backend

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Row, Col, Select, Typography, Space, Spin, message, Card } from 'antd';
import { 
  ArrowRightOutlined, 
  UserOutlined, 
  TeamOutlined, 
  DashboardOutlined,
  ReloadOutlined 
} from '@ant-design/icons';
import api from '../services/api';
import theme from '../styles/theme';
import BancaMarchLogo from '../assets/BancaMarchlogo.png';
import FondoInterfaz from '../assets/FondoInterfazBM.png';

const { Option } = Select;
const { Title, Text } = Typography;

const LandingPage = () => {
  const navigate = useNavigate();
  
  // Estados
  const [gestores, setGestores] = useState([]);
  const [selectedGestor, setSelectedGestor] = useState(null);
  const [selectedGestorInfo, setSelectedGestorInfo] = useState(null);
  const [loadingGestores, setLoadingGestores] = useState(false);
  const [error, setError] = useState(null);

  // ✅ MEJORADO: Cargar lista de gestores con múltiples fallbacks
  const fetchGestores = useCallback(async () => {
    setLoadingGestores(true);
    setError(null);
    
    try {
      console.log('🔍 DEBUG: Iniciando carga de gestores...');
      let gestoresData = [];

      // Intento 1: Endpoint dedicado de gestores
      try {
        console.log('📡 DEBUG: Intentando api.getGestores()...');
        const response = await api.getGestores();
        console.log('📦 DEBUG: Respuesta getGestores:', response);
        
        // Múltiples formatos de respuesta soportados
        const rawData = response?.data?.gestores || response?.data || response || [];
        
        if (Array.isArray(rawData) && rawData.length > 0) {
          gestoresData = rawData.map(g => ({
            id: g.gestor_id || g.GESTORID || g.id || g.gestorId,
            nombre: g.nombre || g.desc_gestor || g.DESC_GESTOR || g.name || g.gestorName,
            centro: g.centro || g.desc_centro || g.DESC_CENTRO || g.center || g.centroName,
            segmento: g.segmento || g.desc_segmento || g.SEGMENTO || g.DESC_SEGMENTO || g.segment || 'No especificado'
          }));
          console.log('✅ DEBUG: Gestores mapeados desde getGestores:', gestoresData);
        }
      } catch (innerErr) {
        console.warn('⚠️ DEBUG: Endpoint getGestores falló, intentando fallback:', innerErr.message);
        
        // Intento 2: Fallback usando endpoint de ranking
        try {
          console.log('📡 DEBUG: Intentando fallback con getComparativeRanking...');
          const rankingResponse = await api.getComparativeRanking('2025-10', 'margen_neto');
          console.log('📦 DEBUG: Respuesta ranking:', rankingResponse);
          
          const rankingData = rankingResponse?.data?.ranking || rankingResponse?.ranking || [];
          
          if (Array.isArray(rankingData) && rankingData.length > 0) {
            gestoresData = rankingData.map(g => ({
              id: g.gestor_id || g.GESTORID || g.id,
              nombre: g.desc_gestor || g.DESC_GESTOR || g.nombre,
              centro: g.desc_centro || g.DESC_CENTRO || g.centro,
              segmento: g.segmento || g.desc_segmento || g.SEGMENTO || g.DESC_SEGMENTO || 'No especificado'
            }));
            console.log('✅ DEBUG: Gestores mapeados desde ranking:', gestoresData);
          }
        } catch (rankingErr) {
          console.warn('⚠️ DEBUG: Fallback de ranking también falló:', rankingErr.message);
        }
      }

      if (gestoresData.length > 0) {
        // Eliminar duplicados basados en ID y ordenar alfabéticamente
        const gestoresUnicos = gestoresData.reduce((acc, current) => {
          const exists = acc.find(gestor => gestor.id === current.id);
          if (!exists && current.id && current.nombre) {
            acc.push(current);
          }
          return acc;
        }, []).sort((a, b) => a.nombre.localeCompare(b.nombre));

        console.log(`✅ DEBUG: ${gestoresUnicos.length} gestores únicos procesados`);
        setGestores(gestoresUnicos);
        
        // Seleccionar primer gestor por defecto si no hay selección previa
        if (gestoresUnicos.length > 0 && !selectedGestor) {
          setSelectedGestor(gestoresUnicos[0].id);
          setSelectedGestorInfo(gestoresUnicos[0]);
          console.log('🎯 DEBUG: Gestor por defecto seleccionado:', gestoresUnicos[0]);
        }
        
        setError(null);
      } else {
        throw new Error('No se encontraron gestores en ningún endpoint');
      }

    } catch (error) {
      console.error('❌ DEBUG: Error general cargando gestores:', error);
      setError('Error al cargar gestores del backend');
      
      // Datos fallback para desarrollo/demo
      const fallbackGestores = [
        { id: 'G001', nombre: 'García Martínez, José', centro: 'Madrid Centro', segmento: 'Banca Personal' },
        { id: 'G002', nombre: 'López Fernández, María', centro: 'Barcelona Norte', segmento: 'Banca Empresas' },
        { id: 'G003', nombre: 'Rodríguez Sánchez, Carlos', centro: 'Valencia Sur', segmento: 'Banca Privada' },
        { id: 'G004', nombre: 'Fernández Ruiz, Ana', centro: 'Sevilla Este', segmento: 'Fondos' },
        { id: 'G005', nombre: 'Martín González, Pedro', centro: 'Bilbao Centro', segmento: 'Banca Minorista' }
      ];
      
      setGestores(fallbackGestores);
      if (!selectedGestor) {
        setSelectedGestor(fallbackGestores[0].id);
        setSelectedGestorInfo(fallbackGestores[0]);
      }
      
      message.warning('Usando datos de ejemplo. Verifica la conexión con el backend.');
      console.log('🔄 DEBUG: Usando gestores fallback:', fallbackGestores);
    } finally {
      setLoadingGestores(false);
    }
  }, [selectedGestor]);

  useEffect(() => {
    fetchGestores();
  }, [fetchGestores]);

  // ✅ MEJORADO: Manejar cambio de gestor con validación
  const handleGestorChange = (gestorId) => {
    console.log('👤 DEBUG: Cambiando gestor a ID:', gestorId);
    const gestorInfo = gestores.find(g => g.id === gestorId);
    setSelectedGestor(gestorId);
    setSelectedGestorInfo(gestorInfo);
    console.log('👤 DEBUG: Información del gestor seleccionado:', gestorInfo);
  };

  // ✅ MEJORADO: Navegar a dashboard de gestor con parámetros completos
  const handleNavigateGestor = () => {
    if (!selectedGestor) {
      message.warning('Por favor selecciona un gestor para continuar');
      return;
    }
    
    console.log('🚀 DEBUG: Navegando a dashboard de gestor:', {
      gestorId: selectedGestor,
      gestorInfo: selectedGestorInfo
    });
    
    // Navegar con query param y state para máxima compatibilidad
    navigate(`/gestor-dashboard?gestor=${selectedGestor}`, {
      state: {
        gestorId: selectedGestor,
        gestorName: selectedGestorInfo?.nombre,
        gestorCenter: selectedGestorInfo?.centro,
        gestorSegment: selectedGestorInfo?.segmento
      }
    });
  };

  // Actualizar lista manualmente
  const handleRefresh = () => {
    console.log('🔄 DEBUG: Refrescando lista de gestores...');
    fetchGestores();
  };

  // ✅ CONSERVADO: Estilos originales con pequeñas mejoras
  const containerStyle = {
    height: '100vh',
    background: `linear-gradient(rgba(27, 94, 85, 0.7), rgba(18, 59, 54, 0.8)), url(${FondoInterfaz})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '2rem',
  };

  const logoStyle = {
    maxWidth: '280px',
    height: 'auto',
    marginBottom: '3rem',
    filter: 'brightness(1.1)',
  };

  const titleStyle = {
    color: '#FFFFFF',
    fontSize: '2.8rem',
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: '2rem',
    textShadow: '2px 2px 4px rgba(0, 0, 0, 0.3)',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  };

  const buttonStyle = {
    height: '70px',
    fontSize: '20px',
    fontWeight: '600',
    padding: '0 3rem',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    transition: 'all 0.3s ease',
  };

  return (
    <div style={containerStyle}>
      {/* Logo corporativo */}
      <img 
        src={BancaMarchLogo} 
        alt="Banca March" 
        style={logoStyle}
      />
      
      {/* Título principal */}
      <h1 style={titleStyle}>
        Sistema de Control de Gestión
      </h1>
      
      <Text style={{
        color: 'rgba(255,255,255,0.9)',
        fontSize: '18px',
        textAlign: 'center',
        marginBottom: '3rem',
        textShadow: '1px 1px 2px rgba(0, 0, 0, 0.3)'
      }}>
        Selecciona tu panel de control
      </Text>

      {/* Selector de gestor y botones */}
      <Row gutter={[24, 24]} justify="center" align="middle" style={{ width: '100%', maxWidth: '900px' }}>
        
        {/* ✅ CORREGIDO: Panel de Gestor con props actualizados */}
        <Col xs={24} md={12}>
          <Card
            style={{
              backgroundColor: 'rgba(255,255,255,0.1)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '12px',
              textAlign: 'center',
              padding: '20px'
            }}
            styles={{ body: { padding: 0 } }} 
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <UserOutlined style={{ fontSize: '32px', color: '#fff', marginBottom: '8px' }} />
                <Title level={4} style={{ color: '#fff', margin: 0 }}>
                  Panel de Gestor
                </Title>
                <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                  Dashboard personalizado por gestor
                </Text>
              </div>

              <div style={{ width: '100%' }}>
                <Text style={{ color: '#fff', fontSize: '14px', fontWeight: 500, display: 'block', marginBottom: '8px' }}>
                  Seleccionar Gestor:
                </Text>
                
                <Space.Compact style={{ width: '100%' }}>
                  <Select
                    placeholder="Buscar gestor..."
                    value={selectedGestor}
                    onChange={handleGestorChange}
                    loading={loadingGestores}
                    showSearch
                    optionFilterProp="children"
                    style={{ flex: 1 }}
                    size="large"
                    disabled={loadingGestores}
                    filterOption={(input, option) =>
                      option.children.props.children[0].props.children.toLowerCase().includes(input.toLowerCase()) ||
                      option.children.props.children[1].props.children.toLowerCase().includes(input.toLowerCase())
                    }
                    styles={{ popup: { root: { backgroundColor: '#fff' } } }}
                    notFoundContent={loadingGestores ? <Spin size="small" /> : 'No se encontraron gestores'}
                  >
                    {gestores.map((gestor) => (
                      <Option key={gestor.id} value={gestor.id}>
                        <div>
                          <div style={{ fontWeight: 500 }}>{gestor.nombre}</div>
                          <div style={{ fontSize: '12px', color: '#666' }}>
                            {gestor.centro} • {gestor.segmento}
                          </div>
                        </div>
                      </Option>
                    ))}
                  </Select>
                  
                  <Button 
                    icon={<ReloadOutlined />} 
                    onClick={handleRefresh}
                    loading={loadingGestores}
                    size="large"
                    style={{ borderColor: 'rgba(255,255,255,0.3)' }}
                    title="Actualizar lista de gestores"
                  />
                </Space.Compact>
              </div>

              {/* ✅ MEJORADO: Información del gestor seleccionado */}
              {selectedGestorInfo && (
                <div style={{
                  padding: '8px 12px',
                  backgroundColor: 'rgba(255,255,255,0.1)',
                  borderRadius: '6px',
                  border: '1px solid rgba(255,255,255,0.2)'
                }}>
                  <Text style={{ color: '#fff', fontSize: '12px' }}>
                    <strong>✓ Seleccionado:</strong> {selectedGestorInfo.nombre}<br/>
                    <strong>Centro:</strong> {selectedGestorInfo.centro}<br/>
                    <strong>Segmento:</strong> {selectedGestorInfo.segmento}
                  </Text>
                </div>
              )}

              <Button
                size="large"
                type="primary"
                style={{
                  ...buttonStyle,
                  background: theme.colors.bmGreenLight,
                  borderColor: theme.colors.bmGreenLight,
                  color: '#FFFFFF',
                  width: '100%'
                }}
                onClick={handleNavigateGestor}
                disabled={!selectedGestor || loadingGestores}
                icon={<ArrowRightOutlined />}
                onMouseEnter={(e) => {
                  if (selectedGestor && !loadingGestores) {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                }}
              >
                {loadingGestores ? 'CARGANDO...' : 'ACCEDER AL PANEL'}
              </Button>
            </Space>
          </Card>
        </Col>

        {/* ✅ CORREGIDO: Panel de Dirección con props actualizados */}
        <Col xs={24} md={12}>
          <Card
            style={{
              backgroundColor: 'rgba(255,255,255,0.1)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '12px',
              textAlign: 'center',
              padding: '20px',
              height: '100%'
            }}
            styles={{ body: { padding: '16px', height: '100%' } }} 
          >
            <Space direction="vertical" size="large" style={{ width: '100%', height: '100%', justifyContent: 'center' }}>
              <div>
                <DashboardOutlined style={{ fontSize: '32px', color: '#fff', marginBottom: '8px' }} />
                <Title level={4} style={{ color: '#fff', margin: 0 }}>
                  Panel de Dirección
                </Title>
                <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                  Vista consolidada ejecutiva
                </Text>
              </div>

              <div style={{ padding: '20px 0' }}>
                <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>
                  • Control consolidado de toda la red<br/>
                  • KPIs ejecutivos en tiempo real<br/>
                  • Análisis comparativo de centros<br/>
                  • Sistema de alertas inteligente
                </Text>
              </div>

              <Button
                size="large"
                type="primary"
                style={{
                  ...buttonStyle,
                  background: theme.colors.bmGreenPrimary,
                  borderColor: theme.colors.bmGreenPrimary,
                  color: '#FFFFFF',
                  width: '100%'
                }}
                onClick={() => navigate('/direccion-dashboard')}
                icon={<TeamOutlined />}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.boxShadow = '0 6px 16px rgba(0, 0, 0, 0.2)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                }}
              >
                ACCEDER AL PANEL
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
      
      {/* ✅ MEJORADO: Información de estado con más detalles */}
      {error && (
        <div style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          color: 'rgba(255,255,255,0.9)',
          fontSize: '12px',
          backgroundColor: 'rgba(255,165,0,0.2)',
          padding: '8px 12px',
          borderRadius: '4px',
          border: '1px solid rgba(255,165,0,0.3)',
          maxWidth: '300px'
        }}>
          ⚠️ {error}<br/>
          <small>Gestores cargados: {gestores.length}</small>
        </div>
      )}

      {/* ✅ CONSERVADO: Footer original */}
      <div style={{
        position: 'absolute',
        bottom: '2rem',
        color: 'rgba(255, 255, 255, 0.8)',
        fontSize: '14px',
        textAlign: 'center',
      }}>
        Agente CDG - Control de Gestión Inteligente<br />
        Banca March © 2025 - Powered by Azure OpenAI
      </div>
    </div>
  );
};

export default LandingPage;
