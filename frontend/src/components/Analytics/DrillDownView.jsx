// src/components/Analytics/DrillDownView.jsx
// Vista drill-down crítica para navegación desde consolidado hasta transacción individual

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Breadcrumb, Button, Space, Tooltip, Tag, Descriptions, Row, Col } from 'antd';
import { 
  ArrowLeftOutlined, 
  FileTextOutlined,
  DollarOutlined,
  UserOutlined,
  BankOutlined,
  CalendarOutlined,
  SearchOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';
import api from '../../services/api';
import InteractiveCharts from '../Dashboard/InteractiveCharts';
import theme from '../../styles/theme';

// Niveles de drill-down según las instrucciones del proyecto CDG
const DRILL_LEVELS = {
  CONSOLIDATED: 'consolidated',     // Vista consolidada
  CENTER: 'center',                // Por centro
  MANAGER: 'manager',              // Por gestor
  CLIENT: 'client',                // Por cliente
  CONTRACT: 'contract',            // Por contrato
  TRANSACTION: 'transaction'       // Transacción individual
};

// Configuración de breadcrumb según nivel
const getBreadcrumbItems = (level, context) => {
  const items = [
    { title: 'Consolidado', key: DRILL_LEVELS.CONSOLIDATED }
  ];

  if (level === DRILL_LEVELS.CONSOLIDATED) return items;

  if (context.centroId) {
    items.push({ 
      title: context.centroName || `Centro ${context.centroId}`, 
      key: DRILL_LEVELS.CENTER 
    });
  }

  if (level === DRILL_LEVELS.CENTER) return items;

  if (context.gestorId) {
    items.push({ 
      title: context.gestorName || `Gestor ${context.gestorId}`, 
      key: DRILL_LEVELS.MANAGER 
    });
  }

  if (level === DRILL_LEVELS.MANAGER) return items;

  if (context.clienteId) {
    items.push({ 
      title: context.clienteName || `Cliente ${context.clienteId}`, 
      key: DRILL_LEVELS.CLIENT 
    });
  }

  if (level === DRILL_LEVELS.CLIENT) return items;

  if (context.contratoId) {
    items.push({ 
      title: `Contrato ${context.contratoId}`, 
      key: DRILL_LEVELS.CONTRACT 
    });
  }

  if (level === DRILL_LEVELS.CONTRACT) return items;

  items.push({ title: 'Movimiento Individual', key: DRILL_LEVELS.TRANSACTION });
  
  return items;
};

const DrillDownView = ({ 
  initialLevel = DRILL_LEVELS.CONSOLIDATED,
  initialContext = {},
  onLevelChange,
  userId,
  periodo 
}) => {
  // Estados principales
  const [currentLevel, setCurrentLevel] = useState(initialLevel);
  const [context, setContext] = useState(initialContext);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [chartData, setChartData] = useState([]);

  // Cargar datos según el nivel actual
  const loadLevelData = useCallback(async () => {
    setLoading(true);
    try {
      const currentPeriod = periodo || new Date().toISOString().slice(0, 7);
      let response;

      switch (currentLevel) {
        case DRILL_LEVELS.CONSOLIDATED:
          // Vista consolidada - ranking de gestores
          response = await api.getComparativeRanking(currentPeriod, 'margen_neto');
          if (response.data) {
            setData(response.data.ranking || []);
            prepareConsolidatedChartData(response.data.ranking || []);
          }
          break;

        case DRILL_LEVELS.CENTER:
          // Vista por centro - gestores del centro
          response = await api.getComparativeRanking(currentPeriod, 'margen_neto');
          if (response.data && context.centroId) {
            const centerData = response.data.ranking.filter(
              item => item.centro_id === context.centroId || item.desc_centro === context.centroName
            );
            setData(centerData);
            prepareManagerChartData(centerData);
          }
          break;

        case DRILL_LEVELS.MANAGER:
          // Vista por gestor - performance específica
          if (context.gestorId) {
            response = await api.getGestorPerformance(context.gestorId, currentPeriod);
            if (response.data) {
              const gestorData = [response.data.gestor];
              setData(gestorData);
              prepareGestorChartData(response.data.kpis);
            }
          }
          break;

        case DRILL_LEVELS.CLIENT:
          // Simular datos de clientes del gestor
          // En producción vendría de un endpoint específico
          setData(generateMockClientData(context.gestorId));
          break;

        case DRILL_LEVELS.CONTRACT:
          // Simular contratos del cliente
          // En producción vendría de MAESTROCONTRATOS filtrado
          setData(generateMockContractData(context.clienteId));
          break;

        case DRILL_LEVELS.TRANSACTION:
          // Simular movimientos del contrato
          // En producción vendría de MOVIMIENTOSCONTRATOS filtrado
          setData(generateMockTransactionData(context.contratoId));
          break;

        default:
          setData([]);
      }

    } catch (error) {
      console.error('Error cargando datos de drill-down:', error);
    } finally {
      setLoading(false);
    }
  }, [currentLevel, context, periodo]);

  // Efectos
  useEffect(() => {
    loadLevelData();
  }, [loadLevelData]);

  // Función para navegar a un nivel más profundo
  const drillDown = (record) => {
    let newLevel;
    let newContext = { ...context };

    switch (currentLevel) {
      case DRILL_LEVELS.CONSOLIDATED:
        newLevel = DRILL_LEVELS.CENTER;
        newContext = {
          ...newContext,
          centroId: record.centro_id,
          centroName: record.desc_centro
        };
        break;

      case DRILL_LEVELS.CENTER:
        newLevel = DRILL_LEVELS.MANAGER;
        newContext = {
          ...newContext,
          gestorId: record.gestor_id,
          gestorName: record.desc_gestor
        };
        break;

      case DRILL_LEVELS.MANAGER:
        newLevel = DRILL_LEVELS.CLIENT;
        newContext = {
          ...newContext,
          clienteId: record.cliente_id,
          clienteName: record.nombre_cliente
        };
        break;

      case DRILL_LEVELS.CLIENT:
        newLevel = DRILL_LEVELS.CONTRACT;
        newContext = {
          ...newContext,
          contratoId: record.contrato_id,
          productName: record.producto_desc
        };
        break;

      case DRILL_LEVELS.CONTRACT:
        newLevel = DRILL_LEVELS.TRANSACTION;
        newContext = {
          ...newContext,
          movimientoId: record.movimiento_id
        };
        break;

      default:
        return;
    }

    setCurrentLevel(newLevel);
    setContext(newContext);
    setSelectedRecord(record);

    if (onLevelChange) {
      onLevelChange(newLevel, newContext, record);
    }
  };

  // Función para navegar hacia atrás
  const navigateBack = (targetLevel) => {
    let newContext = { ...context };

    // Limpiar contexto según el nivel objetivo
    switch (targetLevel) {
      case DRILL_LEVELS.CONSOLIDATED:
        newContext = {};
        break;
      case DRILL_LEVELS.CENTER:
        delete newContext.gestorId;
        delete newContext.gestorName;
        delete newContext.clienteId;
        delete newContext.clienteName;
        delete newContext.contratoId;
        delete newContext.productName;
        delete newContext.movimientoId;
        break;
      case DRILL_LEVELS.MANAGER:
        delete newContext.clienteId;
        delete newContext.clienteName;
        delete newContext.contratoId;
        delete newContext.productName;
        delete newContext.movimientoId;
        break;
      case DRILL_LEVELS.CLIENT:
        delete newContext.contratoId;
        delete newContext.productName;
        delete newContext.movimientoId;
        break;
      case DRILL_LEVELS.CONTRACT:
        delete newContext.movimientoId;
        break;
    }

    setCurrentLevel(targetLevel);
    setContext(newContext);
    setSelectedRecord(null);

    if (onLevelChange) {
      onLevelChange(targetLevel, newContext, null);
    }
  };

  // Funciones para preparar datos de gráficos
  const prepareConsolidatedChartData = (data) => {
    const chartData = data.slice(0, 10).map(item => ({
      desc_gestor: item.desc_gestor || 'Gestor',
      margen_neto: item.margen_neto || 0,
      roe: item.roe || 0,
      eficiencia: item.eficiencia || 75
    }));
    setChartData(chartData);
  };

  const prepareManagerChartData = (data) => {
    const chartData = data.map(item => ({
      desc_gestor: item.desc_gestor || 'Gestor',
      margen_neto: item.margen_neto || 0,
      roe: item.roe || 0
    }));
    setChartData(chartData);
  };

  const prepareGestorChartData = (kpis) => {
    const chartData = [{
      metric: 'KPIs',
      margen_neto: kpis.margen_neto || 0,
      roe: kpis.roe || 0,
      eficiencia: kpis.eficiencia || 75
    }];
    setChartData(chartData);
  };

  // Funciones para generar datos mock (en producción serían endpoints reales)
  const generateMockClientData = (gestorId) => {
    return [
      {
        cliente_id: 1,
        nombre_cliente: 'García Martínez, José Luis',
        segmento: 'Banca Personal',
        total_contratos: 3,
        volumen_gestionado: 285000,
        margen_generado: 3420
      },
      {
        cliente_id: 2,
        nombre_cliente: 'Tecnologías Avanzadas S.L.',
        segmento: 'Banca de Empresas',
        total_contratos: 5,
        volumen_gestionado: 750000,
        margen_generado: 8950
      },
      {
        cliente_id: 3,
        nombre_cliente: 'López Fernández, María Carmen',
        segmento: 'Banca Privada',
        total_contratos: 2,
        volumen_gestionado: 1250000,
        margen_generado: 12300
      }
    ];
  };

  const generateMockContractData = (clienteId) => {
    return [
      {
        contrato_id: '1001',
        producto_desc: 'Préstamo Hipotecario',
        fecha_alta: '2025-03-15',
        volumen: 250000,
        margen_mensual: 890,
        estado: 'Activo'
      },
      {
        contrato_id: '2005',
        producto_desc: 'Depósito a Plazo Fijo',
        fecha_alta: '2025-05-20',
        volumen: 35000,
        margen_mensual: 125,
        estado: 'Activo'
      }
    ];
  };

  const generateMockTransactionData = (contratoId) => {
    return [
      {
        movimiento_id: 'M001',
        fecha: '2025-10-01',
        concepto: 'Intereses cobrados préstamo hipotecario',
        cuenta: '760001',
        importe: 890.50,
        tipo: 'Ingreso'
      },
      {
        movimiento_id: 'M002',
        fecha: '2025-10-15',
        concepto: 'Comisión de gestión',
        cuenta: '760012',
        importe: 45.00,
        tipo: 'Ingreso'
      },
      {
        movimiento_id: 'M003',
        fecha: '2025-10-20',
        concepto: 'Gasto operativo asignado',
        cuenta: '620001',
        importe: -125.30,
        tipo: 'Gasto'
      }
    ];
  };

  // Configuración de columnas según nivel
  const getTableColumns = () => {
    switch (currentLevel) {
      case DRILL_LEVELS.CONSOLIDATED:
        return [
          {
            title: 'Centro',
            dataIndex: 'desc_centro',
            key: 'centro',
            ellipsis: true,
            render: (text, record) => (
              <Button
                type="link"
                onClick={() => drillDown(record)}
                style={{ color: theme.colors.bmGreenPrimary, padding: 0 }}
              >
                <BankOutlined /> {text}
              </Button>
            ),
          },
          {
            title: 'Gestor',
            dataIndex: 'desc_gestor',
            key: 'gestor',
            ellipsis: true,
          },
          {
            title: 'Margen Neto (%)',
            dataIndex: 'margen_neto',
            key: 'margen_neto',
            render: (value) => `${(value || 0).toFixed(2)}%`,
            sorter: (a, b) => (a.margen_neto || 0) - (b.margen_neto || 0),
          },
          {
            title: 'ROE (%)',
            dataIndex: 'roe',
            key: 'roe',
            render: (value) => `${(value || 0).toFixed(2)}%`,
            sorter: (a, b) => (a.roe || 0) - (b.roe || 0),
          },
          {
            title: 'Acciones',
            key: 'actions',
            render: (_, record) => (
              <Tooltip title="Ver detalle del centro">
                <Button
                  type="primary"
                  size="small"
                  icon={<SearchOutlined />}
                  onClick={() => drillDown(record)}
                  style={{
                    backgroundColor: theme.colors.bmGreenLight,
                    borderColor: theme.colors.bmGreenLight
                  }}
                >
                  Drill-Down
                </Button>
              </Tooltip>
            ),
          }
        ];

      case DRILL_LEVELS.CENTER:
      case DRILL_LEVELS.MANAGER:
        return [
          {
            title: 'Gestor',
            dataIndex: 'desc_gestor',
            key: 'gestor',
            render: (text, record) => (
              <Button
                type="link"
                onClick={() => drillDown(record)}
                style={{ color: theme.colors.bmGreenPrimary, padding: 0 }}
              >
                <UserOutlined /> {text}
              </Button>
            ),
          },
          {
            title: 'Segmento',
            dataIndex: 'desc_segmento',
            key: 'segmento',
            ellipsis: true,
          },
          {
            title: 'Margen Neto (%)',
            dataIndex: 'margen_neto',
            key: 'margen_neto',
            render: (value) => `${(value || 0).toFixed(2)}%`,
          },
          {
            title: 'Total Ingresos',
            dataIndex: 'total_ingresos',
            key: 'ingresos',
            render: (value) => `€${(value || 0).toLocaleString()}`,
          },
          {
            title: 'Acciones',
            key: 'actions',
            render: (_, record) => (
              <Button
                type="primary"
                size="small"
                icon={<SearchOutlined />}
                onClick={() => drillDown(record)}
                style={{
                  backgroundColor: theme.colors.bmGreenLight,
                  borderColor: theme.colors.bmGreenLight
                }}
              >
                Ver Clientes
              </Button>
            ),
          }
        ];

      case DRILL_LEVELS.CLIENT:
        return [
          {
            title: 'Cliente',
            dataIndex: 'nombre_cliente',
            key: 'cliente',
            render: (text, record) => (
              <Button
                type="link"
                onClick={() => drillDown(record)}
                style={{ color: theme.colors.bmGreenPrimary, padding: 0 }}
              >
                <UserOutlined /> {text}
              </Button>
            ),
          },
          {
            title: 'Segmento',
            dataIndex: 'segmento',
            key: 'segmento',
            render: (text) => (
              <Tag color={theme.colors.bmGreenLight}>{text}</Tag>
            ),
          },
          {
            title: 'Contratos',
            dataIndex: 'total_contratos',
            key: 'contratos',
          },
          {
            title: 'Volumen Gestionado',
            dataIndex: 'volumen_gestionado',
            key: 'volumen',
            render: (value) => `€${(value || 0).toLocaleString()}`,
          },
          {
            title: 'Margen Generado',
            dataIndex: 'margen_generado',
            key: 'margen',
            render: (value) => `€${(value || 0).toLocaleString()}`,
          },
          {
            title: 'Acciones',
            key: 'actions',
            render: (_, record) => (
              <Button
                type="primary"
                size="small"
                icon={<FileTextOutlined />}
                onClick={() => drillDown(record)}
                style={{
                  backgroundColor: theme.colors.bmGreenLight,
                  borderColor: theme.colors.bmGreenLight
                }}
              >
                Ver Contratos
              </Button>
            ),
          }
        ];

      case DRILL_LEVELS.CONTRACT:
        return [
          {
            title: 'Contrato ID',
            dataIndex: 'contrato_id',
            key: 'contrato',
            render: (text, record) => (
              <Button
                type="link"
                onClick={() => drillDown(record)}
                style={{ color: theme.colors.bmGreenPrimary, padding: 0 }}
              >
                {text}
              </Button>
            ),
          },
          {
            title: 'Producto',
            dataIndex: 'producto_desc',
            key: 'producto',
          },
          {
            title: 'Fecha Alta',
            dataIndex: 'fecha_alta',
            key: 'fecha',
            render: (date) => (
              <Space>
                <CalendarOutlined />
                {date}
              </Space>
            ),
          },
          {
            title: 'Volumen',
            dataIndex: 'volumen',
            key: 'volumen',
            render: (value) => `€${(value || 0).toLocaleString()}`,
          },
          {
            title: 'Margen Mensual',
            dataIndex: 'margen_mensual',
            key: 'margen',
            render: (value) => `€${(value || 0).toLocaleString()}`,
          },
          {
            title: 'Estado',
            dataIndex: 'estado',
            key: 'estado',
            render: (status) => (
              <Tag color={status === 'Activo' ? 'green' : 'orange'}>
                {status}
              </Tag>
            ),
          },
          {
            title: 'Acciones',
            key: 'actions',
            render: (_, record) => (
              <Button
                type="primary"
                size="small"
                icon={<DollarOutlined />}
                onClick={() => drillDown(record)}
                style={{
                  backgroundColor: theme.colors.bmGreenLight,
                  borderColor: theme.colors.bmGreenLight
                }}
              >
                Ver Movimientos
              </Button>
            ),
          }
        ];

      case DRILL_LEVELS.TRANSACTION:
        return [
          {
            title: 'Movimiento ID',
            dataIndex: 'movimiento_id',
            key: 'movimiento',
          },
          {
            title: 'Fecha',
            dataIndex: 'fecha',
            key: 'fecha',
            render: (date) => (
              <Space>
                <CalendarOutlined />
                {date}
              </Space>
            ),
          },
          {
            title: 'Concepto',
            dataIndex: 'concepto',
            key: 'concepto',
            ellipsis: true,
          },
          {
            title: 'Cuenta',
            dataIndex: 'cuenta',
            key: 'cuenta',
          },
          {
            title: 'Importe',
            dataIndex: 'importe',
            key: 'importe',
            render: (value) => (
              <span style={{ 
                color: value >= 0 ? theme.colors.success : theme.colors.error,
                fontWeight: 600 
              }}>
                €{(value || 0).toLocaleString()}
              </span>
            ),
          },
          {
            title: 'Tipo',
            dataIndex: 'tipo',
            key: 'tipo',
            render: (type) => (
              <Tag color={type === 'Ingreso' ? 'green' : 'red'}>
                {type}
              </Tag>
            ),
          }
        ];

      default:
        return [];
    }
  };

  // Renderizar título según nivel
  const renderTitle = () => {
    const icons = {
      [DRILL_LEVELS.CONSOLIDATED]: '🏦',
      [DRILL_LEVELS.CENTER]: '🏢',
      [DRILL_LEVELS.MANAGER]: '👨‍💼',
      [DRILL_LEVELS.CLIENT]: '👤',
      [DRILL_LEVELS.CONTRACT]: '📄',
      [DRILL_LEVELS.TRANSACTION]: '💰'
    };

    const titles = {
      [DRILL_LEVELS.CONSOLIDATED]: 'Vista Consolidada - Todos los Centros',
      [DRILL_LEVELS.CENTER]: `Centro: ${context.centroName || context.centroId}`,
      [DRILL_LEVELS.MANAGER]: `Gestor: ${context.gestorName || context.gestorId}`,
      [DRILL_LEVELS.CLIENT]: `Cartera del Gestor ${context.gestorName}`,
      [DRILL_LEVELS.CONTRACT]: `Contratos de ${context.clienteName}`,
      [DRILL_LEVELS.TRANSACTION]: `Movimientos del Contrato ${context.contratoId}`
    };

    return `${icons[currentLevel]} ${titles[currentLevel]}`;
  };

  return (
    <div style={{ padding: theme.spacing.md }}>
      
      {/* Breadcrumb de navegación */}
      <Card size="small" style={{ marginBottom: theme.spacing.md }}>
        <Breadcrumb separator=">">
          {getBreadcrumbItems(currentLevel, context).map((item, index, array) => (
            <Breadcrumb.Item key={item.key}>
              {index === array.length - 1 ? (
                <span style={{ fontWeight: 600, color: theme.colors.bmGreenPrimary }}>
                  {item.title}
                </span>
              ) : (
                <Button
                  type="link"
                  size="small"
                  onClick={() => navigateBack(item.key)}
                  style={{ color: theme.colors.textSecondary, padding: 0 }}
                >
                  {item.title}
                </Button>
              )}
            </Breadcrumb.Item>
          ))}
        </Breadcrumb>
      </Card>

      {/* Header con información contextual */}
      <Card 
        title={renderTitle()}
        extra={
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => {
              const breadcrumbs = getBreadcrumbItems(currentLevel, context);
              if (breadcrumbs.length > 1) {
                const previousLevel = breadcrumbs[breadcrumbs.length - 2];
                navigateBack(previousLevel.key);
              }
            }}
            disabled={currentLevel === DRILL_LEVELS.CONSOLIDATED}
            style={{ borderColor: theme.colors.bmGreenLight }}
          >
            Volver
          </Button>
        }
        bordered={false}
        style={{ 
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          marginBottom: theme.spacing.md
        }}
      >
        {/* Información contextual detallada */}
        {selectedRecord && (
          <Descriptions size="small" column={3} style={{ marginTop: theme.spacing.sm }}>
            <Descriptions.Item label="Período">{periodo || 'Actual'}</Descriptions.Item>
            <Descriptions.Item label="Usuario">{userId}</Descriptions.Item>
            <Descriptions.Item label="Nivel">{currentLevel}</Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      {/* Gráfico según nivel actual */}
      {chartData.length > 0 && (
        <InteractiveCharts
          data={chartData}
          availableKpis={['margen_neto', 'roe', 'eficiencia']}
          title={`Análisis Visual - ${renderTitle()}`}
          description="Visualización de datos del nivel actual de drill-down"
        />
      )}

      {/* Tabla principal con datos del nivel actual */}
      <Card
        title={`Detalle (${data.length} elementos)`}
        bordered={false}
        style={{
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      >
        <Table
          columns={getTableColumns()}
          dataSource={data}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} de ${total} elementos`
          }}
          scroll={{ x: 'max-content' }}
          size="small"
          rowKey={(record) => 
            record.gestor_id || 
            record.cliente_id || 
            record.contrato_id || 
            record.movimiento_id || 
            Math.random()
          }
        />
      </Card>

      {/* Información de trazabilidad */}
      <Card 
        title="Trazabilidad Completa"
        size="small"
        style={{ marginTop: theme.spacing.md }}
      >
        <Row gutter={[16, 8]}>
          <Col span={12}>
            <strong>Ruta de navegación:</strong> {getBreadcrumbItems(currentLevel, context).map(item => item.title).join(' → ')}
          </Col>
          <Col span={12}>
            <strong>Capacidad drill-down:</strong> {currentLevel !== DRILL_LEVELS.TRANSACTION ? 'Disponible' : 'Nivel máximo alcanzado'}
          </Col>
        </Row>
      </Card>
    </div>
  );
};

DrillDownView.propTypes = {
  initialLevel: PropTypes.oneOf(Object.values(DRILL_LEVELS)),
  initialContext: PropTypes.object,
  onLevelChange: PropTypes.func,
  userId: PropTypes.string.isRequired,
  periodo: PropTypes.string
};

export default DrillDownView;
