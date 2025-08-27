// src/components/Dashboard/GestorDashboard.jsx
// Dashboard específico por gestor - CORREGIDO para backend Banca March

import React, { useState, useEffect, useCallback } from 'react';
import { Row, Col, Card, Typography, Spin, message, Button, Select, Alert, Statistic, Table, Tag } from 'antd';
import { 
  ReloadOutlined, 
  UserOutlined, 
  TrophyOutlined, 
  DollarOutlined,
  PercentageOutlined,
  LineChartOutlined,
  TeamOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import KPICards from './KPICards';
import InteractiveCharts from './InteractiveCharts';
import ChatInterface from '../Chat/ChatInterface';
import ConversationalPivot from '../Chat/ConversationalPivot';
import DeviationAnalysis from '../Analytics/DeviationAnalysis';
import api from '../../services/api';
import theme from '../../styles/theme';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const GestorDashboard = ({ userId, gestorId, periodo }) => {
  // Estados principales
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [gestoresLoading, setGestoresLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Estados de selección
  const [availableGestores, setAvailableGestores] = useState([]);
  const [selectedGestorId, setSelectedGestorId] = useState(gestorId || null);
  const [selectedGestorInfo, setSelectedGestorInfo] = useState(null);

  // Estados de datos
  const [gestorKpis, setGestorKpis] = useState({});
  const [previousKpis, setPreviousKpis] = useState({});
  const [gestorClientes, setGestorClientes] = useState([]);
  const [, setGestorContratos] = useState([]);
  const [centerComparison, setCenterComparison] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [availableKpis, setAvailableKpis] = useState(['ROE', 'MARGEN_NETO', 'TOTAL_INGRESOS']);
  const [lastUpdate, setLastUpdate] = useState(null);

  // ✅ CORREGIDO: Cargar lista de gestores con campos en mayúsculas
  const fetchAvailableGestores = useCallback(async () => {
    setGestoresLoading(true);
    try {
      const response = await api.getComparativeRanking(periodo || '2025-10', 'MARGEN_NETO');
      
      if (response.data?.ranking) {
        const gestores = response.data.ranking.map(gestor => ({
          id: gestor.GESTOR_ID || gestor.DESC_GESTOR, // Usar ID si está disponible
          nombre: gestor.DESC_GESTOR,
          centro: gestor.DESC_CENTRO,
          segmento: gestor.DESC_SEGMENTO || 'No especificado',
          margen_neto: gestor.MARGEN_NETO,
          roe: gestor.ROE
        }));
        
        setAvailableGestores(gestores);
        
        // Seleccionar gestor por defecto o el pasado por props
        if (selectedGestorId) {
          const gestorInfo = gestores.find(g => g.id === selectedGestorId);
          if (gestorInfo) {
            setSelectedGestorInfo(gestorInfo);
          }
        } else if (gestores.length > 0) {
          setSelectedGestorId(gestores[0].id);
          setSelectedGestorInfo(gestores[0]);
        }
      }
    } catch (error) {
      console.error('Error cargando gestores:', error);
      message.warning('Error al cargar la lista de gestores. Usando datos por defecto.');
      
      // Datos fallback
      const fallbackGestores = [
        { id: 'G001', nombre: 'García Martínez, José', centro: 'Madrid Centro', segmento: 'Banca Personal' },
        { id: 'G002', nombre: 'López Fernández, María', centro: 'Barcelona Norte', segmento: 'Banca Empresas' },
        { id: 'G003', nombre: 'Rodríguez Sánchez, Carlos', centro: 'Valencia Sur', segmento: 'Banca Privada' }
      ];
      
      setAvailableGestores(fallbackGestores);
      if (!selectedGestorId) {
        setSelectedGestorId(fallbackGestores[0].id);
        setSelectedGestorInfo(fallbackGestores[0]);
      }
    } finally {
      setGestoresLoading(false);
    }
  }, [periodo, selectedGestorId]);

  // ✅ CORREGIDO: Cargar datos específicos del gestor con campos en mayúsculas
  const fetchGestorData = useCallback(async (gestorId, showRefreshing = false) => {
    if (!gestorId) return;

    if (showRefreshing) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const currentPeriod = periodo || new Date().toISOString().slice(0, 7);

      // Usar endpoint existente para performance del gestor
      const gestorPerformanceResponse = await api.getGestorPerformance(gestorId, currentPeriod);

      // ✅ CORREGIDO: Procesar KPIs del gestor con campos correctos
      if (gestorPerformanceResponse.data?.kpis) {
        const kpis = gestorPerformanceResponse.data.kpis;
        setGestorKpis(kpis);
        setAvailableKpis(Object.keys(kpis));

        // Generar datos anteriores simulados para comparación
        const previousData = Object.keys(kpis).reduce((acc, key) => {
          acc[key] = kpis[key] ? kpis[key] * (0.92 + Math.random() * 0.16) : null;
          return acc;
        }, {});
        setPreviousKpis(previousData);

        // ✅ CORREGIDO: Preparar datos para gráficos con campo correcto
        const chartData = [{
          DESC_GESTOR: selectedGestorInfo?.nombre || 'Gestor',
          ...kpis
        }];
        setChartData(chartData);
      }

      // Obtener información adicional del gestor si está disponible
      if (gestorPerformanceResponse.data?.gestor) {
        const gestorData = gestorPerformanceResponse.data.gestor;
        setGestorClientes(gestorData.clientes || []);
        setGestorContratos(gestorData.contratos || []);
      }

      // ✅ CORREGIDO: Obtener comparación con el centro con campos correctos
      try {
        const centerResponse = await api.getComparativeRanking(currentPeriod, 'MARGEN_NETO');
        if (centerResponse.data?.ranking) {
          const centerGestores = centerResponse.data.ranking.filter(
            g => g.DESC_CENTRO === selectedGestorInfo?.centro
          );
          const gestorPosition = centerGestores.findIndex(g => 
            (g.GESTOR_ID || g.DESC_GESTOR) === gestorId
          ) + 1;
          
          setCenterComparison({
            ranking: gestorPosition || 0,
            total: centerGestores.length,
            gestores: centerGestores
          });
        }
      } catch (centerError) {
        console.warn('No se pudo cargar comparación del centro:', centerError);
        setCenterComparison({ ranking: 0, total: 0, gestores: [] });
      }

      setLastUpdate(new Date());
      message.success(`Datos actualizados para ${selectedGestorInfo?.nombre}`);

    } catch (error) {
      console.error('Error cargando datos del gestor:', error);
      setError('Error al cargar datos del gestor. Algunos datos pueden no estar disponibles.');
      message.error('Error al cargar algunos datos del gestor');
      
      // ✅ CORREGIDO: Datos fallback básicos con campos correctos
      setGestorKpis({
        ROE: 0,
        MARGEN_NETO: 0,
        TOTAL_INGRESOS: 0,
        TOTAL_GASTOS: 0,
        BENEFICIO_NETO: 0
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [periodo, selectedGestorInfo?.nombre, selectedGestorInfo?.centro]);

  // Efectos
  useEffect(() => {
    fetchAvailableGestores();
  }, [fetchAvailableGestores]);

  useEffect(() => {
    if (selectedGestorId) {
      fetchGestorData(selectedGestorId);
    }
  }, [selectedGestorId, fetchGestorData]);

  // Handlers
  const handleGestorChange = (gestorId) => {
    const gestorInfo = availableGestores.find(g => g.id === gestorId);
    setSelectedGestorId(gestorId);
    setSelectedGestorInfo(gestorInfo);
  };

  const handleRefresh = () => {
    if (selectedGestorId) {
      fetchGestorData(selectedGestorId, true);
    }
  };

  // ✅ CORREGIDO: Columnas para tabla de comparación con campos en mayúsculas
  const centerComparisonColumns = [
    {
      title: 'Posición',
      key: 'position',
      render: (_, __, index) => (
        <Tag color={index < 3 ? 'gold' : 'default'}>
          #{index + 1}
        </Tag>
      ),
      width: 80
    },
    {
      title: 'Gestor',
      dataIndex: 'DESC_GESTOR',
      key: 'DESC_GESTOR',
      render: (text, record) => (
        <Text strong={(record.GESTOR_ID || record.DESC_GESTOR) === selectedGestorId}>
          {text}
        </Text>
      )
    },
    {
      title: 'Margen Neto (%)',
      dataIndex: 'MARGEN_NETO',
      key: 'MARGEN_NETO',
      render: (value) => (
        <Text style={{ fontWeight: 600 }}>
          {value ? value.toFixed(2) : '--'}%
        </Text>
      ),
      sorter: (a, b) => (a.MARGEN_NETO || 0) - (b.MARGEN_NETO || 0)
    },
    {
      title: 'ROE (%)',
      dataIndex: 'ROE',
      key: 'ROE',
      render: (value) => (
        <Text style={{ fontWeight: 600 }}>
          {value ? value.toFixed(2) : '--'}%
        </Text>
      ),
      sorter: (a, b) => (a.ROE || 0) - (b.ROE || 0)
    }
  ];

  // Navegador de pestañas
  const renderTabNavigator = () => (
    <div style={{ 
      marginBottom: theme.spacing.md,
      padding: theme.spacing.sm,
      backgroundColor: theme.colors.background,
      borderRadius: 6,
      border: `1px solid ${theme.colors.border}`
    }}>
      <div style={{ display: 'flex', gap: 8 }}>
        {[
          { key: 'overview', label: 'Vista General', icon: <LineChartOutlined /> },
          { key: 'comparison', label: 'Comparación Centro', icon: <TeamOutlined /> },
          { key: 'analysis', label: 'Análisis Desviaciones', icon: <FileTextOutlined /> },
          { key: 'chat', label: 'Asistente Personal', icon: <UserOutlined /> }
        ].map(tab => (
          <Button
            key={tab.key}
            type={activeTab === tab.key ? 'primary' : 'default'}
            size="small"
            icon={tab.icon}
            onClick={() => setActiveTab(tab.key)}
            style={{
              backgroundColor: activeTab === tab.key ? theme.colors.bmGreenPrimary : 'transparent',
              borderColor: activeTab === tab.key ? theme.colors.bmGreenPrimary : theme.colors.border
            }}
          >
            {tab.label}
          </Button>
        ))}
      </div>
    </div>
  );

  // Renderizar loading inicial
  if (loading && !selectedGestorId) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '60vh'
      }}>
        <Spin size="large" />
        <Paragraph style={{ marginTop: theme.spacing.lg, color: theme.colors.textSecondary }}>
          Cargando dashboard de gestor...
        </Paragraph>
      </div>
    );
  }

  return (
    <div style={{
      padding: theme.spacing.lg,
      minHeight: '100vh',
      backgroundColor: theme.colors.backgroundLight
    }}>
      
      {/* Header con selector de gestor */}
      <Row justify="space-between" align="middle" style={{ marginBottom: theme.spacing.lg }}>
        <Col xs={24} lg={16}>
          <div style={{ marginBottom: theme.spacing.sm }}>
            <Title level={2} style={{ color: theme.colors.bmGreenDark, margin: 0 }}>
              <UserOutlined style={{ marginRight: 8 }} />
              Dashboard del Gestor Comercial
            </Title>
            <Text style={{ color: theme.colors.textSecondary, fontSize: '16px' }}>
              Análisis personalizado por gestor - Período: {periodo || 'Actual'}
            </Text>
          </div>
          
          {/* Selector de gestor */}
          <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <Text strong style={{ color: theme.colors.bmGreenDark }}>
              Seleccionar Gestor:
            </Text>
            <Select
              value={selectedGestorId}
              onChange={handleGestorChange}
              loading={gestoresLoading}
              style={{ minWidth: 300 }}
              placeholder="Selecciona un gestor"
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {availableGestores.map(gestor => (
                <Option key={gestor.id} value={gestor.id}>
                  {gestor.nombre} - {gestor.centro}
                </Option>
              ))}
            </Select>
          </div>
        </Col>
        
        <Col>
          <Button
            icon={<ReloadOutlined />}
            loading={refreshing}
            onClick={handleRefresh}
            disabled={!selectedGestorId}
            type="primary"
            style={{ 
              backgroundColor: theme.colors.bmGreenPrimary,
              borderColor: theme.colors.bmGreenPrimary 
            }}
          >
            Actualizar Datos
          </Button>
        </Col>
      </Row>

      {/* Información del gestor seleccionado */}
      {selectedGestorInfo && (
        <Card
          size="small"
          style={{
            marginBottom: theme.spacing.lg,
            backgroundColor: theme.colors.bmGreenLight + '20',
            borderLeft: `4px solid ${theme.colors.bmGreenPrimary}`
          }}
        >
          <Row gutter={[16, 8]} align="middle">
            <Col>
              <Text strong style={{ color: theme.colors.bmGreenDark }}>
                Gestor Activo:
              </Text>
            </Col>
            <Col>
              <Text style={{ fontSize: '16px' }}>
                <UserOutlined /> {selectedGestorInfo.nombre}
              </Text>
            </Col>
            <Col>
              <Text>
                Centro: <strong>{selectedGestorInfo.centro}</strong>
              </Text>
            </Col>
            <Col>
              <Text>
                Segmento: <strong>{selectedGestorInfo.segmento}</strong>
              </Text>
            </Col>
            {lastUpdate && (
              <Col>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Actualizado: {lastUpdate.toLocaleTimeString('es-ES')}
                </Text>
              </Col>
            )}
          </Row>
        </Card>
      )}

      {/* Mostrar error si existe */}
      {error && (
        <Alert
          message="Advertencia"
          description={error}
          type="warning"
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: theme.spacing.md }}
        />
      )}

      {/* ✅ CORREGIDO: Resumen rápido de performance con campos correctos */}
      <Row gutter={[16, 16]} style={{ marginBottom: theme.spacing.lg }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="ROE"
              value={gestorKpis.ROE || 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: theme.colors.bmGreenPrimary }}
              prefix={<PercentageOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Margen Neto"
              value={gestorKpis.MARGEN_NETO || 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: theme.colors.bmGreenPrimary }}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Clientes"
              value={gestorClientes.length || 0}
              valueStyle={{ color: theme.colors.bmGreenPrimary }}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic
              title="Ranking Centro"
              value={centerComparison.ranking || 0}
              suffix={`/${centerComparison.total || 0}`}
              valueStyle={{ color: theme.colors.bmGreenPrimary }}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Navegador de pestañas */}
      {renderTabNavigator()}

      {/* KPIs del gestor - Siempre visibles */}
      <Card
        title={
          <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
            KPIs del Gestor - {selectedGestorInfo?.nombre}
          </span>
        }
        bordered={false}
        style={{
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: theme.spacing.lg
        }}
      >
        <KPICards kpis={gestorKpis} previousKpis={previousKpis} />
      </Card>

      {/* Contenido condicional según pestaña activa */}
      {activeTab === 'overview' && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={16}>
            {/* Gráfico de evolución del gestor */}
            {chartData.length > 0 && (
              <Card
                title={
                  <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
                    Evolución y Performance Personal
                  </span>
                }
                bordered={false}
                style={{
                  borderRadius: 8,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}
              >
                <InteractiveCharts
                  data={chartData}
                  availableKpis={availableKpis}
                  title={`Performance de ${selectedGestorInfo?.nombre}`}
                  description="Análisis personalizado de KPIs del gestor"
                />
              </Card>
            )}
          </Col>

          <Col xs={24} lg={8}>
            {/* Control conversacional */}
            <Card
              title={
                <span style={{ color: theme.colors.bmGreenDark, fontSize: '16px', fontWeight: 600 }}>
                  Control de Gráficos
                </span>
              }
              bordered={false}
              style={{
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                height: '400px'
              }}
            >
              <ConversationalPivot
                userId={userId}
                gestorId={selectedGestorId}
                periodo={periodo}
                initialData={chartData}
                initialKpis={availableKpis}
              />
            </Card>
          </Col>
        </Row>
      )}

      {activeTab === 'comparison' && (
        <Card
          title={
            <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
              Comparación con el Centro - {selectedGestorInfo?.centro}
            </span>
          }
          bordered={false}
          style={{
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          {centerComparison.gestores && centerComparison.gestores.length > 0 ? (
            <Table
              columns={centerComparisonColumns}
              dataSource={centerComparison.gestores}
              pagination={false}
              size="small"
              rowKey={(record) => record.GESTOR_ID || record.DESC_GESTOR || `row-${Math.random()}`}
              rowClassName={(record) => 
                (record.GESTOR_ID || record.DESC_GESTOR) === selectedGestorId ? 'current-gestor-row' : ''
              }
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <Text style={{ color: theme.colors.textSecondary }}>
                No hay datos de comparación disponibles para el centro.
              </Text>
            </div>
          )}
        </Card>
      )}

      {activeTab === 'analysis' && (
        <DeviationAnalysis
          userId={userId}
          gestorId={selectedGestorId}
          periodo={periodo}
        />
      )}

      {activeTab === 'chat' && (
        <Card
          title={
            <span style={{ color: theme.colors.bmGreenDark, fontSize: '18px', fontWeight: 600 }}>
              Asistente Personal de {selectedGestorInfo?.nombre}
            </span>
          }
          bordered={false}
          style={{
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            minHeight: '600px'
          }}
        >
          <ChatInterface
            userId={userId}
            gestorId={selectedGestorId}
            periodo={periodo}
            height="550px"
            initialMessages={[
              {
                sender: 'agent',
                text: `¡Hola ${selectedGestorInfo?.nombre || 'Gestor'}! Soy tu asistente personal de Control de Gestión. Puedo ayudarte con análisis detallado de tu cartera, seguimiento de KPIs, comparación con tu centro, identificación de oportunidades y estrategias de mejora. ¿En qué puedo asistirte?`,
                charts: [],
                recommendations: [
                  'Analiza tu ranking en el centro',
                  'Revisa las desviaciones en tus KPIs',
                  'Compara tu rendimiento mensual',
                  'Identifica oportunidades de mejora'
                ]
              }
            ]}
          />
        </Card>
      )}
    </div>
  );
};

GestorDashboard.propTypes = {
  userId: PropTypes.string.isRequired,
  gestorId: PropTypes.string,
  periodo: PropTypes.string
};

export default GestorDashboard;
