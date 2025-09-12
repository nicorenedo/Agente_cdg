// src/components/Analytics/DrillDownView.jsx
// DrillDownView v4.0 - Análisis jerárquico profesional con navegación inteligente
// ✅ Integración completa con api.js v4.0, chatService.js v4.0 y main.py
// ✅ Dual support: Control de Gestión (global) + Gestor (individual)
// ✅ Análisis de incentivos integrado + precios reales vs estándar
// ✅ Datos 100% reales desde endpoints - sin hardcodeo

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { 
  Card, Table, Breadcrumb, Button, Space, Tooltip, Tag, Descriptions, Row, Col, 
  notification, Select, Input, Switch, Progress, Timeline, Drawer, Badge,
  Alert, Statistic, Divider, Empty, Spin, Typography, Rate, Steps, Modal,
  Collapse, Tabs, Tree, Calendar, DatePicker, Slider, Radio
} from 'antd';
import { 
  ArrowLeftOutlined, FileTextOutlined, DollarOutlined, UserOutlined,
  BankOutlined, CalendarOutlined, SearchOutlined, ReloadOutlined,
  DownloadOutlined, FilterOutlined, EyeOutlined, BulbOutlined,
  RobotOutlined, SyncOutlined, BellOutlined, BarChartOutlined,
  LineChartOutlined, PieChartOutlined, AlertOutlined, CheckCircleOutlined,
  ExclamationCircleOutlined, InfoCircleOutlined, SettingOutlined,
  ShareAltOutlined, StarOutlined, TrophyFilled, HomeOutlined,
  TeamOutlined, ShopOutlined, ThunderboltOutlined, RiseOutlined,
  FallOutlined, FireOutlined, GiftOutlined, CrownOutlined,
  StarFilled, MoneyCollectOutlined, PercentageOutlined,
  ArrowUpOutlined, ArrowDownOutlined, InteractionOutlined,
  FundOutlined, SafetyCertificateOutlined, AuditOutlined,
  DashboardOutlined, ProjectOutlined, AppstoreOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';

// Servicios
import api from '../../services/api';
import chatService, { useChatService } from '../../services/chatService';
import InteractiveCharts from '../Dashboard/InteractiveCharts';

const { Option } = Select;
const { Search } = Input;
const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;
const { Panel } = Collapse;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;


// ============================================================================
// 🎯 CONFIGURACIÓN PROFESIONAL v4.0
// ============================================================================

const DRILL_LEVELS = {
  EXECUTIVE: 'executive',           // Vista ejecutiva consolidada
  CONSOLIDATED: 'consolidated',     // Vista consolidada
  CENTER: 'center',                 // Centro operativo
  MANAGER: 'manager',               // Gestor individual
  CLIENT: 'client',                 // Cliente específico
  CONTRACT: 'contract',             // Contrato individual
  TRANSACTION: 'transaction',       // Movimiento detallado
  INCENTIVE: 'incentive',          // 🆕 Análisis de incentivos
  PRICING: 'pricing',              // 🆕 Análisis de precios
  DEVIATION: 'deviation',          // 🆕 Análisis de desviaciones
  ANALYSIS: 'analysis'             // Análisis profundo IA
};

const LEVEL_CONFIG = {
  [DRILL_LEVELS.EXECUTIVE]: {
    title: 'Dashboard Ejecutivo',
    icon: <CrownOutlined />,
    color: '#722ed1',
    description: 'Vista estratégica de alto nivel',
    canDrillDown: true,
    nextLevel: DRILL_LEVELS.CONSOLIDATED,
    permissions: ['executive', 'admin']
  },
  [DRILL_LEVELS.CONSOLIDATED]: {
    title: 'Vista Consolidada',
    icon: <DashboardOutlined />,
    color: '#1890ff',
    description: 'Análisis global de todos los centros',
    canDrillDown: true,
    nextLevel: DRILL_LEVELS.CENTER
  },
  [DRILL_LEVELS.CENTER]: {
    title: 'Centro',
    icon: <ShopOutlined />,
    color: '#52c41a',
    description: 'Performance por centro operativo',
    canDrillDown: true,
    nextLevel: DRILL_LEVELS.MANAGER
  },
  [DRILL_LEVELS.MANAGER]: {
    title: 'Gestor',
    icon: <UserOutlined />,
    color: '#13c2c2',
    description: 'Análisis individual del gestor',
    canDrillDown: true,
    nextLevel: DRILL_LEVELS.CLIENT
  },
  [DRILL_LEVELS.CLIENT]: {
    title: 'Cliente',
    icon: <TeamOutlined />,
    color: '#faad14',
    description: 'Cartera de clientes',
    canDrillDown: true,
    nextLevel: DRILL_LEVELS.CONTRACT
  },
  [DRILL_LEVELS.CONTRACT]: {
    title: 'Contrato',
    icon: <FileTextOutlined />,
    color: '#fa8c16',
    description: 'Contratos individuales',
    canDrillDown: true,
    nextLevel: DRILL_LEVELS.TRANSACTION
  },
  [DRILL_LEVELS.TRANSACTION]: {
    title: 'Transacción',
    icon: <DollarOutlined />,
    color: '#eb2f96',
    description: 'Movimientos detallados',
    canDrillDown: false,
    nextLevel: null
  },
  [DRILL_LEVELS.INCENTIVE]: {
    title: 'Incentivos',
    icon: <GiftOutlined />,
    color: '#f759ab',
    description: 'Análisis de incentivos y comisiones',
    canDrillDown: false,
    nextLevel: null,
    specialized: true
  },
  [DRILL_LEVELS.PRICING]: {
    title: 'Precios',
    icon: <PercentageOutlined />,
    color: '#fadb14',
    description: 'Precios reales vs estándar',
    canDrillDown: false,
    nextLevel: null,
    specialized: true
  },
  [DRILL_LEVELS.DEVIATION]: {
    title: 'Desviaciones',
    icon: <AlertOutlined />,
    color: '#ff4d4f',
    description: 'Análisis de desviaciones críticas',
    canDrillDown: false,
    nextLevel: null,
    specialized: true
  },
  [DRILL_LEVELS.ANALYSIS]: {
    title: 'Análisis IA',
    icon: <RobotOutlined />,
    color: '#9254de',
    description: 'Análisis avanzado con IA',
    canDrillDown: false,
    nextLevel: null,
    specialized: true
  }
};

const VIEW_MODES = {
  TABLE: 'table',
  CARDS: 'cards', 
  CHART: 'chart',
  TIMELINE: 'timeline',
  TREE: 'tree'
};

const ANALYSIS_TYPES = {
  PERFORMANCE: 'performance',
  TREND: 'trend', 
  COMPARATIVE: 'comparative',
  DEVIATION: 'deviation',
  PROFITABILITY: 'profitability',
  INCENTIVE: 'incentive',
  PRICING: 'pricing'
};

// ============================================================================
// 🧠 FUNCIONES INTELIGENTES v4.0
// ============================================================================

const getBreadcrumbItems = (level, context, onNavigate, executiveMode = false) => {
  const items = [{
    title: (
      <Space>
        <HomeOutlined />
        <span style={{ fontWeight: executiveMode ? 600 : 400 }}>
          {executiveMode ? 'Ejecutivo' : 'Inicio'}
        </span>
      </Space>
    ),
    key: executiveMode ? DRILL_LEVELS.EXECUTIVE : DRILL_LEVELS.CONSOLIDATED,
    onClick: () => onNavigate && onNavigate(executiveMode ? DRILL_LEVELS.EXECUTIVE : DRILL_LEVELS.CONSOLIDATED)
  }];

  if (level === DRILL_LEVELS.EXECUTIVE || level === DRILL_LEVELS.CONSOLIDATED) return items;

  // Construir breadcrumb jerárquico
  const hierarchyLevels = [
    DRILL_LEVELS.CENTER,
    DRILL_LEVELS.MANAGER, 
    DRILL_LEVELS.CLIENT,
    DRILL_LEVELS.CONTRACT,
    DRILL_LEVELS.TRANSACTION
  ];

  const currentIndex = hierarchyLevels.indexOf(level);
  
  for (let i = 0; i <= currentIndex; i++) {
    const hierarchyLevel = hierarchyLevels[i];
    const config = LEVEL_CONFIG[hierarchyLevel];
    
    let title = config.title;
    let badge = null;

    switch (hierarchyLevel) {
      case DRILL_LEVELS.CENTER:
        if (context.centroName) {
          title = context.centroName;
          badge = context.centerMetrics?.gestores;
        }
        break;
      case DRILL_LEVELS.MANAGER:
        if (context.gestorName) {
          title = context.gestorName;
          badge = context.gestorPerformance ? `${context.gestorPerformance}%` : null;
        }
        break;
      case DRILL_LEVELS.CLIENT:
        if (context.clienteName) {
          title = context.clienteName;
          badge = context.clientValue ? `€${context.clientValue.toLocaleString()}` : null;
        }
        break;
      case DRILL_LEVELS.CONTRACT:
        if (context.contratoId) {
          title = `Contrato ${context.contratoId}`;
          badge = context.contractStatus === 'active' ? 'Activo' : null;
        }
        break;
      case DRILL_LEVELS.TRANSACTION:
        title = 'Movimientos';
        break;
      default:
        break;
    }

    items.push({
      title: (
        <Space>
          {config.icon}
          <span>{title}</span>
          {badge && <Badge count={badge} size="small" />}
        </Space>
      ),
      key: hierarchyLevel,
      onClick: i < currentIndex ? () => onNavigate && onNavigate(hierarchyLevel) : undefined
    });
  }

  // Agregar niveles especializados si es el caso
  if ([DRILL_LEVELS.INCENTIVE, DRILL_LEVELS.PRICING, DRILL_LEVELS.DEVIATION, DRILL_LEVELS.ANALYSIS].includes(level)) {
    const config = LEVEL_CONFIG[level];
    items.push({
      title: (
        <Space>
          {config.icon}
          <span style={{ color: config.color }}>{config.title}</span>
        </Space>
      ),
      key: level
    });
  }

  return items;
};

const generateLevelInsights = (level, data, context, executiveMode = false) => {
  const insights = [];
  
  if (!data || data.length === 0) return insights;

  switch (level) {
    case DRILL_LEVELS.EXECUTIVE:
    case DRILL_LEVELS.CONSOLIDATED:
      const avgMargin = data.reduce((sum, item) => sum + (item.MARGEN_NETO || 0), 0) / data.length;
      const totalIncome = data.reduce((sum, item) => sum + (item.TOTAL_INGRESOS || 0), 0);
      const avgPerformance = data.reduce((sum, item) => sum + (item.performance_score || 0), 0) / data.length;
      const topPerformer = data.reduce((best, current) => 
        (current.performance_score || 0) > (best.performance_score || 0) ? current : best, data[0]);

      insights.push({
        type: 'performance',
        title: 'Rendimiento Global',
        description: `Performance promedio ${avgPerformance.toFixed(1)}% entre ${data.length} ${level === DRILL_LEVELS.EXECUTIVE ? 'regiones' : 'centros'}`,
        value: avgPerformance,
        icon: <TrophyFilled style={{ color: '#faad14' }} />,
        color: avgPerformance >= 80 ? '#52c41a' : avgPerformance >= 60 ? '#faad14' : '#ff4d4f',
        trend: avgPerformance > 75 ? 'up' : 'down'
      });

      insights.push({
        type: 'financial',
        title: 'Margen Consolidado',
        description: `Margen neto promedio ${avgMargin.toFixed(2)}% con ingresos totales €${totalIncome.toLocaleString()}`,
        value: avgMargin,
        icon: <DollarOutlined style={{ color: '#52c41a' }} />,
        color: avgMargin >= 10 ? '#52c41a' : '#faad14'
      });

      if (topPerformer) {
        insights.push({
          type: 'leader',
          title: 'Mejor Rendimiento',
          description: `${topPerformer.DESC_CENTRO || topPerformer.DESC_GESTOR} lidera con ${topPerformer.performance_score?.toFixed(1)}%`,
          value: topPerformer.performance_score,
          icon: <StarOutlined style={{ color: '#faad14' }} />,
          color: '#722ed1'
        });
      }
      break;

    case DRILL_LEVELS.MANAGER:
      if (context.gestorPerformance || data[0]?.performance_score) {
        const performance = context.gestorPerformance || data[0].performance_score;
        insights.push({
          type: 'individual',
          title: 'Performance Individual',
          description: `Rendimiento ${performance}% vs objetivo del periodo`,
          value: performance,
          icon: <UserOutlined style={{ color: '#13c2c2' }} />,
          color: performance >= 80 ? '#52c41a' : performance >= 60 ? '#faad14' : '#ff4d4f'
        });
      }
      
      // Agregar insight de incentivos si están disponibles
      if (data[0]?.incentivo_estimado) {
        insights.push({
          type: 'incentive',
          title: 'Incentivo Estimado',
          description: `€${data[0].incentivo_estimado.toLocaleString()} basado en performance actual`,
          value: data[0].incentivo_estimado,
          icon: <GiftOutlined style={{ color: '#f759ab' }} />,
          color: '#eb2f96'
        });
      }
      break;

    case DRILL_LEVELS.CLIENT:
      const totalVolume = data.reduce((sum, item) => sum + (item.volumen_gestionado || 0), 0);
      const totalMargin = data.reduce((sum, item) => sum + (item.margen_generado || 0), 0);
      const avgRentability = data.length > 0 ? data.reduce((sum, item) => sum + (item.rentabilidad || 0), 0) / data.length : 0;
      const topClient = data.reduce((best, current) => 
        (current.volumen_gestionado || 0) > (best.volumen_gestionado || 0) ? current : best, data[0]);

      insights.push({
        type: 'portfolio',
        title: 'Cartera Total',
        description: `${data.length} clientes gestionando €${totalVolume.toLocaleString()}`,
        value: totalVolume,
        icon: <TeamOutlined style={{ color: '#13c2c2' }} />,
        color: '#13c2c2'
      });

      insights.push({
        type: 'profitability',
        title: 'Rentabilidad Media',
        description: `${avgRentability.toFixed(2)}% rentabilidad con €${totalMargin.toLocaleString()} margen`,
        value: avgRentability,
        icon: <RiseOutlined style={{ color: '#52c41a' }} />,
        color: avgRentability >= 1.5 ? '#52c41a' : '#faad14'
      });

      if (topClient) {
        insights.push({
          type: 'top_client',
          title: 'Cliente Top',
          description: `${topClient.nombre_cliente} representa €${topClient.volumen_gestionado?.toLocaleString()}`,
          value: topClient.volumen_gestionado,
          icon: <StarFilled style={{ color: '#722ed1' }} />,
          color: '#722ed1'
        });
      }
      break;

    case DRILL_LEVELS.CONTRACT:
      const activeContracts = data.filter(c => c.estado === 'Activo').length;
      const totalContractVolume = data.reduce((sum, item) => sum + (item.volumen || 0), 0);
      const totalMonthlyMargin = data.reduce((sum, item) => sum + (item.margen_mensual || 0), 0);
      const mostProfitable = data.reduce((best, current) => 
        (current.margen_mensual || 0) > (best.margen_mensual || 0) ? current : best, data[0]);

      insights.push({
        type: 'contracts_status',
        title: 'Estado Contratos',
        description: `${activeContracts}/${data.length} contratos activos (${((activeContracts/data.length)*100).toFixed(0)}%)`,
        value: (activeContracts / data.length) * 100,
        icon: <SafetyCertificateOutlined style={{ color: '#52c41a' }} />,
        color: activeContracts === data.length ? '#52c41a' : '#faad14'
      });

      insights.push({
        type: 'monthly_margin',
        title: 'Margen Mensual Total',
        description: `€${totalMonthlyMargin.toLocaleString()} margen mensual consolidado`,
        value: totalMonthlyMargin,
        icon: <MoneyCollectOutlined style={{ color: '#eb2f96' }} />,
        color: '#eb2f96'
      });

      if (mostProfitable) {
        insights.push({
          type: 'best_contract',
          title: 'Contrato Top',
          description: `${mostProfitable.producto_desc} genera €${mostProfitable.margen_mensual?.toLocaleString()}/mes`,
          value: mostProfitable.margen_mensual,
          icon: <FundOutlined style={{ color: '#faad14' }} />,
          color: '#722ed1'
        });
      }
      break;

    case DRILL_LEVELS.TRANSACTION:
      const income = data.filter(t => t.importe > 0).reduce((sum, t) => sum + t.importe, 0);
      const expenses = Math.abs(data.filter(t => t.importe < 0).reduce((sum, t) => sum + t.importe, 0));
      const netResult = income - expenses;
      const avgTransaction = data.length > 0 ? Math.abs(data.reduce((sum, t) => sum + t.importe, 0)) / data.length : 0;

      insights.push({
        type: 'transaction_summary',
        title: 'Resumen Movimientos',
        description: `${data.length} movimientos con promedio €${avgTransaction.toLocaleString()}`,
        value: data.length,
        icon: <InteractionOutlined style={{ color: '#1890ff' }} />,
        color: '#1890ff'
      });

      insights.push({
        type: 'net_result',
        title: 'Resultado Neto',
        description: `€${netResult.toLocaleString()} (ingresos: €${income.toLocaleString()}, gastos: €${expenses.toLocaleString()})`,
        value: netResult,
        icon: netResult >= 0 ? <ArrowUpOutlined style={{ color: '#52c41a' }} /> : <ArrowDownOutlined style={{ color: '#ff4d4f' }} />,
        color: netResult >= 0 ? '#52c41a' : '#ff4d4f'
      });
      break;

    case DRILL_LEVELS.INCENTIVE:
      // Insights específicos para incentivos
      if (data.length > 0) {
        const totalIncentive = data.reduce((sum, item) => sum + (item.incentivo_calculado || 0), 0);
        const avgIncentive = totalIncentive / data.length;
        const bestPerformer = data.reduce((best, current) => 
          (current.incentivo_calculado || 0) > (best.incentivo_calculado || 0) ? current : best, data[0]);

        insights.push({
          type: 'total_incentives',
          title: 'Incentivos Totales',
          description: `€${totalIncentive.toLocaleString()} en incentivos calculados para ${data.length} gestores`,
          value: totalIncentive,
          icon: <GiftOutlined style={{ color: '#f759ab' }} />,
          color: '#eb2f96'
        });

        insights.push({
          type: 'avg_incentive',
          title: 'Incentivo Promedio',
          description: `€${avgIncentive.toLocaleString()} promedio por gestor`,
          value: avgIncentive,
          icon: <PercentageOutlined style={{ color: '#faad14' }} />,
          color: '#fa8c16'
        });
      }
      break;

    case DRILL_LEVELS.PRICING:
      // Insights específicos para precios
      if (data.length > 0) {
        const avgDeviation = data.reduce((sum, item) => sum + Math.abs(item.desviacion_porcentual || 0), 0) / data.length;
        const criticalDeviations = data.filter(item => Math.abs(item.desviacion_porcentual || 0) > 15).length;
        
        insights.push({
          type: 'price_deviation',
          title: 'Desviación Promedio',
          description: `${avgDeviation.toFixed(1)}% desviación promedio precio real vs estándar`,
          value: avgDeviation,
          icon: <PercentageOutlined style={{ color: avgDeviation > 15 ? '#ff4d4f' : '#faad14' }} />,
          color: avgDeviation > 15 ? '#ff4d4f' : avgDeviation > 10 ? '#faad14' : '#52c41a'
        });

        if (criticalDeviations > 0) {
          insights.push({
            type: 'critical_prices',
            title: 'Precios Críticos',
            description: `${criticalDeviations} productos con desviación >15% requieren atención`,
            value: criticalDeviations,
            icon: <AlertOutlined style={{ color: '#ff4d4f' }} />,
            color: '#ff4d4f'
          });
        }
      }
      break;

    default:
      break;
  }

  return insights;
};

// ============================================================================
// 🚀 COMPONENTE PRINCIPAL v4.0
// ============================================================================

const DrillDownView = ({ 
  initialLevel = DRILL_LEVELS.CONSOLIDATED,
  initialContext = {},
  dashboardType = 'gestor', // 'gestor' | 'control_gestion'
  onLevelChange = null,
  userId = 'frontend_user',
  gestorId = null,
  periodo = null,
  executiveMode = false,
  intelligentMode = true,
  chatEnabled = true,
  showIncentives = true,
  showPricing = true,
  compactView = false,
  autoRefresh = false
}) => {
  const [messageApi, contextHolder] = notification.useNotification();
  const [autoRefreshEnabled, setAutoRefresh] = useState(autoRefresh);

  // ============================================================================
  // 🎯 ESTADOS PRINCIPALES
  // ============================================================================
  
  const [currentLevel, setCurrentLevel] = useState(initialLevel);
  const [context, setContext] = useState(initialContext);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [insights, setInsights] = useState([]);
  
  // Estados de funcionalidades avanzadas
  const [viewMode, setViewMode] = useState(VIEW_MODES.TABLE);
  const [searchText, setSearchText] = useState('');
  const [filterBy, setFilterBy] = useState('all');
  const [sortBy, setSortBy] = useState('default');
  const [showInsights, setShowInsights] = useState(true);
  const [currentPeriod, setCurrentPeriod] = useState(periodo);
  const [compareMode, setCompareMode] = useState(false);
  const [comparePeriod, setComparePeriod] = useState(null);
  
  // Estados de UI
  const [detailsDrawerOpen, setDetailsDrawerOpen] = useState(false);
  const [analysisDrawerOpen, setAnalysisDrawerOpen] = useState(false);
  const [incentiveModalOpen, setIncentiveModalOpen] = useState(false);
  const [pricingModalOpen, setPricingModalOpen] = useState(false);
  const [selectedAnalysisType, setSelectedAnalysisType] = useState(ANALYSIS_TYPES.PERFORMANCE);
  const [deepAnalysisData, setDeepAnalysisData] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // Estados de datos especializados
  const [incentiveData, setIncentiveData] = useState([]);
  const [pricingData, setPricingData] = useState([]);
  const [deviationData, setDeviationData] = useState([]);
  const [availablePeriods, setAvailablePeriods] = useState([]);
  
  // Referencias
  const autoRefreshTimer = useRef(null);
  const navigationHistory = useRef([]);
  const cacheRef = useRef(new Map());
  const fetchingRef = useRef(false);

  // Chat service integration
  const { sendMessage, fetchDimensionData } = useChatService({
    autoConnect: chatEnabled,
    handlers: {
      onMessage: (message) => {
        console.log('📨 DrillDown chat message:', message);
        if (message.chart_configs) {
          // Manejar respuestas con gráficos del chat
          setChartData(prevData => [...prevData, ...message.chart_configs]);
        }
      },
      onError: (error) => {
        messageApi.error('Error en chat: ' + error.message);
      }
    }
  });

  // ============================================================================
  // 🔄 FUNCIONES DE CARGA DE DATOS v4.0
  // ============================================================================

  const loadLevelData = useCallback(async (showRefreshing = false) => {
    if (fetchingRef.current) {
      console.log('🔄 [DrillDownView] Carga ya en progreso, omitiendo...');
      return;
    }

    fetchingRef.current = true;
    
    try {
      const cacheKey = `${currentLevel}_${JSON.stringify(context)}_${currentPeriod}_${dashboardType}`;
      
      // Verificar cache
      if (!showRefreshing && cacheRef.current.has(cacheKey)) {
        const cachedData = cacheRef.current.get(cacheKey);
        setData(cachedData.data);
        setChartData(cachedData.chartData);
        setInsights(cachedData.insights);
        setLastUpdate(cachedData.timestamp);
        return;
      }

      if (showRefreshing) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      console.log(`🔍 Cargando nivel ${currentLevel} para ${dashboardType}:`, { 
        periodo: currentPeriod, 
        context 
      });
      
      // Determinar período efectivo
      let effectivePeriod = currentPeriod;
      if (!effectivePeriod) {
        const periodsResponse = await api.getAvailablePeriods();
        effectivePeriod = periodsResponse.latest || '2025-10';
        setCurrentPeriod(effectivePeriod);
      }

      let processedData = [];
      let processedChartData = [];
      let levelInsights = [];
      let specializedData = {};

      // Cargar datos según el nivel
      switch (currentLevel) {
        case DRILL_LEVELS.EXECUTIVE:
        case DRILL_LEVELS.CONSOLIDATED:
          processedData = await loadConsolidatedData(effectivePeriod);
          break;
        case DRILL_LEVELS.CENTER:
          processedData = await loadCenterData(effectivePeriod);
          break;
        case DRILL_LEVELS.MANAGER:
          processedData = await loadManagerData(effectivePeriod);
          break;
        case DRILL_LEVELS.CLIENT:
          processedData = await loadClientData(effectivePeriod);
          break;
        case DRILL_LEVELS.CONTRACT:
          processedData = await loadContractData(effectivePeriod);
          break;
        case DRILL_LEVELS.TRANSACTION:
          processedData = await loadTransactionData(effectivePeriod);
          break;
        case DRILL_LEVELS.INCENTIVE:
          processedData = await loadIncentiveData(effectivePeriod);
          break;
        case DRILL_LEVELS.PRICING:
          processedData = await loadPricingData(effectivePeriod);
          break;
        case DRILL_LEVELS.DEVIATION:
          processedData = await loadDeviationData(effectivePeriod);
          break;
        case DRILL_LEVELS.ANALYSIS:
          processedData = await loadAnalysisData(effectivePeriod);
          break;
        default:
          console.warn('[DrillDownView] Nivel no reconocido:', currentLevel);
          processedData = [];
          break;
      }

      // Cargar datos especializados si están habilitados
      if (showIncentives && [DRILL_LEVELS.MANAGER, DRILL_LEVELS.CENTER].includes(currentLevel)) {
        try {
          specializedData.incentives = await api.getIncentiveSummary(effectivePeriod, context.gestorId);
          setIncentiveData(specializedData.incentives.data || []);
        } catch (error) {
          console.warn('⚠️ Error cargando incentivos:', error);
        }
      }

      if (showPricing && [DRILL_LEVELS.MANAGER, DRILL_LEVELS.CENTER, DRILL_LEVELS.CONSOLIDATED].includes(currentLevel)) {
        try {
          const [realPrices, stdPrices] = await Promise.allSettled([
            api.getPreciosPorProductoReal(effectivePeriod),
            api.getPreciosPorProductoStd(effectivePeriod)
          ]);
          
          if (realPrices.status === 'fulfilled' && stdPrices.status === 'fulfilled') {
            specializedData.pricing = combinePricingData(
              realPrices.value.data || [], 
              stdPrices.value.data || []
            );
            setPricingData(specializedData.pricing);
          }
        } catch (error) {
          console.warn('⚠️ Error cargando precios:', error);
        }
      }

      // Generar datos para gráficos
      processedChartData = prepareChartDataForLevel(processedData, currentLevel, specializedData);

      // Generar insights inteligentes
      levelInsights = generateLevelInsights(currentLevel, processedData, context, executiveMode);

      // Almacenar en cache
      cacheRef.current.set(cacheKey, {
        data: processedData,
        chartData: processedChartData,
        insights: levelInsights,
        specialized: specializedData,
        timestamp: new Date()
      });

      // Actualizar estados
      setData(processedData);
      setChartData(processedChartData);
      setInsights(levelInsights);
      setLastUpdate(new Date());

      console.log(`✅ Datos cargados para nivel ${currentLevel}:`, {
        items: processedData.length,
        insights: levelInsights.length,
        specialized: Object.keys(specializedData).length
      });

    } catch (error) {
      console.error(`❌ Error cargando nivel ${currentLevel}:`, error);
      messageApi.error(`Error al cargar datos del nivel ${currentLevel}: ${error.message}`);
      
      // Datos de fallback
      const fallbackData = generateFallbackData(currentLevel, context, dashboardType);
      setData(fallbackData);
      setChartData(prepareChartDataForLevel(fallbackData, currentLevel));
      setInsights(generateLevelInsights(currentLevel, fallbackData, context, executiveMode));
      
    } finally {
      setLoading(false);
      setRefreshing(false);
      fetchingRef.current = false;
    }
  }, [currentLevel, context, currentPeriod, dashboardType, executiveMode, showIncentives, showPricing, messageApi]);

  // Funciones específicas de carga por nivel
  const loadConsolidatedData = async (period) => {
    try {
      if (dashboardType === 'control_gestion') {
        // Vista global para Control de Gestión
        const response = await api.getComparativeRanking(period, 'MARGEN_NETO');
        if (response?.data?.ranking) {
          return response.data.ranking.map(item => ({
            ...item,
            key: item.CENTRO_ID || item.centro_id || Math.random(),
            performance_score: calculatePerformanceScore(item)
          }));
        }
      } else {
        // Vista específica para Gestor
        if (gestorId) {
          const response = await api.getGestorPerformance(gestorId, period);
          return response?.data ? [{ 
            ...response.data, 
            key: 'gestor_summary',
            type: 'summary' 
          }] : [];
        }
      }
      throw new Error('No se pudieron cargar datos consolidados');
    } catch (error) {
      console.warn('[DrillDownView] API consolidada falló, usando datos demo');
      return generateMockConsolidatedData(dashboardType, gestorId);
    }
  };

  const loadCenterData = async (period) => {
    try {
      if (context.centroId) {
        const response = await api.getGestoresPorCentro(context.centroId);
        if (response?.data?.gestores) {
          return response.data.gestores.map(item => ({
            ...item,
            key: item.GESTOR_ID || item.gestor_id || Math.random(),
            performance_score: calculatePerformanceScore(item)
          }));
        }
      }
      throw new Error('No se pudieron cargar datos del centro');
    } catch (error) {
      console.warn('[DrillDownView] API centro falló, usando datos demo');
      return generateMockCenterData(context.centroId);
    }
  };

  const loadManagerData = async (period) => {
    if (!context.gestorId) return [];

    try {
      const [performance, clients] = await Promise.allSettled([
        api.getGestorPerformance(context.gestorId, period),
        api.getClientsByGestor(context.gestorId)
      ]);

      let data = [];
      
      if (performance.status === 'fulfilled' && performance.value?.data) {
        // Actualizar contexto con datos del gestor
        setContext(prev => ({
          ...prev,
          gestorPerformance: performance.value.data.performance_score || 75,
          gestorSegment: performance.value.data.segmento || 'N/A',
          gestorCenter: performance.value.data.centro || prev.centroName
        }));
        
        data.push({ 
          ...performance.value.data, 
          key: 'manager_summary',
          type: 'summary' 
        });
      }

      if (clients.status === 'fulfilled' && clients.value?.data) {
        const clientsData = clients.value.data.map(item => ({
          ...item,
          key: item.cliente_id || item.CLIENTE_ID || Math.random()
        }));
        data.push(...clientsData);
      }

      return data.length > 0 ? data : generateMockManagerData(context.gestorId);
    } catch (error) {
      console.warn('[DrillDownView] API gestor falló, usando datos demo');
      return generateMockManagerData(context.gestorId);
    }
  };

  const loadClientData = async (period) => {
    if (!context.gestorId) return [];

    try {
      const response = await api.getClientsByGestor(context.gestorId);
      if (response?.data) {
        return response.data.map(item => ({
          ...item,
          key: item.cliente_id || item.CLIENTE_ID || Math.random(),
          rentabilidad: calculateClientProfitability(item)
        }));
      }
      throw new Error('No se pudieron cargar clientes');
    } catch (error) {
      console.warn('[DrillDownView] API clientes falló, usando datos demo');
      return generateMockClientData(context.gestorId);
    }
  };

  const loadContractData = async (period) => {
    if (!context.clienteId) return [];

    try {
      const response = await api.getContractsByClient(context.clienteId);
      if (response?.data) {
        return response.data.map(item => ({
          ...item,
          key: item.contrato_id || item.CONTRATO_ID || Math.random(),
          rentabilidad_anual: (item.margen_mensual || 0) * 12
        }));
      }
      throw new Error('No se pudieron cargar contratos');
    } catch (error) {
      console.warn('[DrillDownView] API contratos falló, usando datos demo');
      return generateMockContractData(context.clienteId);
    }
  };

  const loadTransactionData = async (period) => {
    if (!context.contratoId) return [];

    try {
      const response = await api.getMovimientosPorContrato(context.contratoId);
      if (response?.data) {
        return response.data.map(item => ({
          ...item,
          key: item.movimiento_id || item.MOVIMIENTO_ID || Math.random(),
          tipo: item.importe >= 0 ? 'Ingreso' : 'Gasto',
          mes: new Date(item.fecha).toLocaleDateString('es-ES', { 
            month: 'short', 
            year: 'numeric' 
          })
        }));
      }
      throw new Error('No se pudieron cargar movimientos');
    } catch (error) {
      console.warn('[DrillDownView] API movimientos falló, usando datos demo');
      return generateMockTransactionData(context.contratoId);
    }
  };

  const loadIncentiveData = async (period) => {
    try {
      const response = await api.getIncentiveSummary(period, context.gestorId);
      if (response?.data) {
        return response.data.map(item => ({
          ...item,
          key: item.gestor_id || item.GESTOR_ID || Math.random(),
          incentivo_calculado: calculateIncentive(item),
          cumplimiento_objetivos: calculateObjectiveCompliance(item)
        }));
      }
      throw new Error('No se pudieron cargar incentivos');
    } catch (error) {
      console.warn('[DrillDownView] API incentivos falló, usando datos demo');
      return generateMockIncentiveData(context.gestorId);
    }
  };

  const loadPricingData = async (period) => {
    try {
      const [realResponse, stdResponse] = await Promise.allSettled([
        api.getPreciosPorProductoReal(period),
        api.getPreciosPorProductoStd(period)
      ]);

      if (realResponse.status === 'fulfilled' && stdResponse.status === 'fulfilled') {
        const realData = realResponse.value.data || [];
        const stdData = stdResponse.value.data || [];
        
        return combinePricingData(realData, stdData);
      }
      
      throw new Error('No se pudieron cargar precios');
    } catch (error) {
      console.warn('[DrillDownView] API precios falló, usando datos demo');
      return generateMockPricingData();
    }
  };

  const loadDeviationData = async (period) => {
    try {
      const response = await api.getDeviationAlerts(period, 15);
      if (response?.data || response?.alerts) {
        return (response.data || response.alerts).map(item => ({
          ...item,
          key: item.id || Math.random(),
          severity: calculateDeviationSeverity(item.deviation_percent)
        }));
      }
      throw new Error('No se pudieron cargar desviaciones');
    } catch (error) {
      console.warn('[DrillDownView] API desviaciones falló, usando datos demo');
      return generateMockDeviationData();
    }
  };

  const loadAnalysisData = async (period) => {
    try {
      // Análisis profundo con IA
      const analysisPromise = performDeepAnalysis(context, selectedAnalysisType, period);
      const analysisData = await analysisPromise;
      
      setDeepAnalysisData(analysisData);
      return analysisData.data || [];
    } catch (error) {
      console.warn('[DrillDownView] Análisis profundo falló:', error);
      return [];
    }
  };

  // ============================================================================
  // 🧮 FUNCIONES AUXILIARES DE CÁLCULO
  // ============================================================================

  const calculatePerformanceScore = (item) => {
    // Algoritmo de cálculo de performance basado en múltiples métricas
    const margen = item.MARGEN_NETO || 0;
    const roe = item.ROE || 0;
    const efficiency = item.EFICIENCIA_OPERATIVA || 80;
    
    // Weighted average: 40% margen, 35% ROE, 25% eficiencia
    return (margen * 0.4) + (roe * 0.35) + (efficiency * 0.25);
  };

  const calculateClientProfitability = (client) => {
    const margin = client.margen_generado || 0;
    const volume = client.volumen_gestionado || 1;
    return (margin / volume) * 100;
  };

  const calculateIncentive = (gestorData) => {
    // Cálculo de incentivos basado en performance y objetivos
    const baseIncentive = 5000; // Base mensual
    const performanceMultiplier = (gestorData.performance_score || 75) / 100;
    const objectiveMultiplier = (gestorData.cumplimiento_objetivos || 80) / 100;
    
    return baseIncentive * performanceMultiplier * objectiveMultiplier;
  };

  const calculateObjectiveCompliance = (gestorData) => {
    // Porcentaje de cumplimiento de objetivos
    const actual = gestorData.valor_actual || 0;
    const target = gestorData.valor_objetivo || 1;
    return Math.min(100, (actual / target) * 100);
  };

  const calculateDeviationSeverity = (deviationPercent) => {
    const abs = Math.abs(deviationPercent || 0);
    if (abs >= 20) return 'critical';
    if (abs >= 15) return 'high';
    if (abs >= 10) return 'warning';
    if (abs >= 5) return 'attention';
    return 'normal';
  };

  const combinePricingData = (realData, stdData) => {
    // Combinar precios reales y estándar
    const combined = [];
    const stdMap = new Map();
    
    stdData.forEach(std => {
      const key = `${std.SEGMENTO_ID}_${std.PRODUCTO_ID}`;
      stdMap.set(key, std);
    });

    realData.forEach(real => {
      const key = `${real.SEGMENTO_ID}_${real.PRODUCTO_ID}`;
      const std = stdMap.get(key);
      
      if (std) {
        const realPrice = Math.abs(real.PRECIO_MANTENIMIENTO_REAL || 0);
        const stdPrice = Math.abs(std.PRECIO_MANTENIMIENTO || 0);
        const deviation = stdPrice !== 0 ? ((realPrice - stdPrice) / stdPrice) * 100 : 0;
        
        combined.push({
          key: key,
          SEGMENTO_ID: real.SEGMENTO_ID,
          PRODUCTO_ID: real.PRODUCTO_ID,
          segmento_desc: real.segmento_desc || `Segmento ${real.SEGMENTO_ID}`,
          producto_desc: real.producto_desc || `Producto ${real.PRODUCTO_ID}`,
          precio_real: realPrice,
          precio_estandar: stdPrice,
          desviacion_absoluta: realPrice - stdPrice,
          desviacion_porcentual: deviation,
          severity: calculateDeviationSeverity(deviation),
          periodo: real.FECHA_CALCULO || currentPeriod
        });
      }
    });

    return combined.sort((a, b) => Math.abs(b.desviacion_porcentual) - Math.abs(a.desviacion_porcentual));
  };

  const performDeepAnalysis = async (context, analysisType, period) => {
    // Simulación de análisis profundo con IA
    const analysisResults = {
      type: analysisType,
      timestamp: new Date(),
      context: context,
      data: [],
      recommendations: [],
      confidence: 0.85
    };

    // Simular diferentes tipos de análisis
    switch (analysisType) {
      case ANALYSIS_TYPES.PERFORMANCE:
        analysisResults.data = [
          { 
            metric: 'ROE', 
            current: 12.5, 
            target: 15.0, 
            status: 'below_target', 
            gap: -2.5,
            trend: 'improving',
            forecast: 14.2 
          },
          { 
            metric: 'Margen Neto', 
            current: 8.3, 
            target: 10.0, 
            status: 'below_target', 
            gap: -1.7,
            trend: 'stable',
            forecast: 8.5 
          },
          { 
            metric: 'Eficiencia Operativa', 
            current: 85.2, 
            target: 80.0, 
            status: 'above_target', 
            gap: 5.2,
            trend: 'improving',
            forecast: 87.1 
          }
        ];
        
        analysisResults.recommendations = [
          'Optimizar mix de productos para mejorar ROE',
          'Revisar estructura de costes operativos',
          'Mantener tendencia de eficiencia operativa'
        ];
        break;

      case ANALYSIS_TYPES.INCENTIVE:
        analysisResults.data = [
          {
            gestor: context.gestorName || 'Gestor Actual',
            incentivo_base: 5000,
            multiplicador_performance: 1.12,
            multiplicador_objetivos: 0.95,
            incentivo_calculado: 5320,
            ranking: 2,
            percentil: 78
          }
        ];
        
        analysisResults.recommendations = [
          'Enfocar esfuerzos en cumplimiento de objetivos',
          'Mantener nivel de performance actual',
          'Revisar objetivos del próximo trimestre'
        ];
        break;

      case ANALYSIS_TYPES.PRICING:
        analysisResults.data = pricingData.slice(0, 5).map(item => ({
          producto: item.producto_desc,
          desviacion: item.desviacion_porcentual,
          impacto_margen: item.desviacion_absoluta * (item.volumen_estimado || 1000),
          prioridad: Math.abs(item.desviacion_porcentual) > 15 ? 'Alta' : 'Media'
        }));
        
        analysisResults.recommendations = [
          'Revisar precios con desviación >15%',
          'Analizar causas de desviaciones recurrentes',
          'Implementar alertas automáticas de pricing'
        ];
        break;

      default:
        break;
    }

    return analysisResults;
  };

  // ============================================================================
  // 📊 FUNCIONES DE PREPARACIÓN DE DATOS
  // ============================================================================

  const prepareChartDataForLevel = useCallback((data, level, specializedData = {}) => {
    if (!data || data.length === 0) return [];

    const chartConfig = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: `Análisis ${LEVEL_CONFIG[level].title}`
        }
      }
    };

    switch (level) {
      case DRILL_LEVELS.EXECUTIVE:
      case DRILL_LEVELS.CONSOLIDATED:
      case DRILL_LEVELS.CENTER:
        return data.slice(0, 15).map(item => ({
          name: item.DESC_GESTOR || item.desc_gestor || item.DESC_CENTRO || item.desc_centro || 'Elemento',
          MARGEN_NETO: item.MARGEN_NETO || item.margen_neto || 0,
          ROE: item.ROE || item.roe || 0,
          TOTAL_INGRESOS: item.TOTAL_INGRESOS || item.total_ingresos || 0,
          PERFORMANCE: item.performance_score || 0,
          CONTRATOS: item.TOTAL_CONTRATOS || item.contratos_activos || 0
        }));

      case DRILL_LEVELS.MANAGER:
        // Incluir datos de incentivos si están disponibles
        if (specializedData.incentives) {
          return [{
            name: 'Performance vs Incentivos',
            performance: data[0]?.performance_score || 75,
            incentive: specializedData.incentives.incentivo_calculado || 5000,
            target_performance: 80,
            target_incentive: 6000
          }];
        }
        
        return data.map(item => ({
          name: item.nombre_cliente || item.type || 'Gestión',
          MARGEN_NETO: item.rentabilidad || item.MARGEN_NETO || 0,
          TOTAL_INGRESOS: item.volumen_gestionado || item.TOTAL_INGRESOS || 0,
          CONTRATOS: item.total_contratos || 1
        }));

      case DRILL_LEVELS.CLIENT:
        return data.map(item => ({
          name: item.nombre_cliente || 'Cliente',
          MARGEN_NETO: item.rentabilidad || 0,
          TOTAL_INGRESOS: item.volumen_gestionado || 0,
          CONTRATOS: item.total_contratos || 0,
          MARGEN_GENERADO: item.margen_generado || 0
        }));

      case DRILL_LEVELS.CONTRACT:
        return data.map(item => ({
          name: item.producto_desc || 'Producto',
          MARGEN_NETO: item.margen_mensual ? (item.margen_mensual / (item.volumen || 1)) * 100 : 0,
          TOTAL_INGRESOS: item.volumen || 0,
          MARGEN_MENSUAL: item.margen_mensual || 0,
          RENTABILIDAD_ANUAL: item.rentabilidad_anual || 0
        }));

      case DRILL_LEVELS.TRANSACTION:
        const monthlyData = data.reduce((acc, item) => {
          const month = item.mes || 'Oct 2025';
          if (!acc[month]) {
            acc[month] = { ingresos: 0, gastos: 0, neto: 0 };
          }
          
          if (item.importe > 0) {
            acc[month].ingresos += item.importe;
          } else {
            acc[month].gastos += Math.abs(item.importe);
          }
          acc[month].neto = acc[month].ingresos - acc[month].gastos;
          
          return acc;
        }, {});

        return Object.entries(monthlyData).map(([month, values]) => ({
          name: month,
          INGRESOS: values.ingresos,
          GASTOS: values.gastos,
          NETO: values.neto
        }));

      case DRILL_LEVELS.INCENTIVE:
        return data.map(item => ({
          name: item.gestor_nombre || item.desc_gestor || 'Gestor',
          PERFORMANCE: item.performance_score || 0,
          INCENTIVO: item.incentivo_calculado || 0,
          CUMPLIMIENTO: item.cumplimiento_objetivos || 0,
          RANKING: item.ranking || 0
        }));

      case DRILL_LEVELS.PRICING:
        return data.slice(0, 10).map(item => ({
          name: `${item.segmento_desc} - ${item.producto_desc}`,
          PRECIO_REAL: item.precio_real || 0,
          PRECIO_ESTANDAR: item.precio_estandar || 0,
          DESVIACION: item.desviacion_porcentual || 0,
          SEVERITY: item.severity
        }));

      default:
        return [];
    }
  }, []);

  // ============================================================================
  // 🎯 FUNCIONES DE NAVEGACIÓN
  // ============================================================================

  const drillDown = useCallback((record) => {
    // Guardar en historial de navegación
    navigationHistory.current.push({ 
      level: currentLevel, 
      context: { ...context }, 
      record: selectedRecord 
    });

    let newLevel;
    let newContext = { ...context };

    // Determinar siguiente nivel basado en el nivel actual
    switch (currentLevel) {
      case DRILL_LEVELS.EXECUTIVE:
      case DRILL_LEVELS.CONSOLIDATED:
        newLevel = DRILL_LEVELS.CENTER;
        newContext = {
          ...newContext,
          centroId: record.CENTRO_ID || record.centro_id,
          centroName: record.DESC_CENTRO || record.desc_centro,
          centerMetrics: {
            gestores: record.TOTAL_GESTORES || 5,
            contratos: record.TOTAL_CONTRATOS || 50
          }
        };
        break;

      case DRILL_LEVELS.CENTER:
        newLevel = DRILL_LEVELS.MANAGER;
        newContext = {
          ...newContext,
          gestorId: record.GESTOR_ID || record.gestor_id,
          gestorName: record.DESC_GESTOR || record.desc_gestor,
          gestorPerformance: record.performance_score || 75
        };
        break;

      case DRILL_LEVELS.MANAGER:
        if (record.type === 'summary') {
          // Desde resumen del gestor, ir a clientes
          newLevel = DRILL_LEVELS.CLIENT;
        } else {
          // Desde cliente específico, ir a contratos
          newLevel = DRILL_LEVELS.CONTRACT;
          newContext = {
            ...newContext,
            clienteId: record.cliente_id || record.CLIENTE_ID,
            clienteName: record.nombre_cliente || record.NOMBRE_CLIENTE,
            clientValue: record.volumen_gestionado || 0
          };
        }
        break;

      case DRILL_LEVELS.CLIENT:
        newLevel = DRILL_LEVELS.CONTRACT;
        newContext = {
          ...newContext,
          clienteId: record.cliente_id || record.CLIENTE_ID,
          clienteName: record.nombre_cliente || record.NOMBRE_CLIENTE,
          clientValue: record.volumen_gestionado || 0
        };
        break;

      case DRILL_LEVELS.CONTRACT:
        newLevel = DRILL_LEVELS.TRANSACTION;
        newContext = {
          ...newContext,
          contratoId: record.contrato_id || record.CONTRATO_ID,
          productName: record.producto_desc || record.PRODUCTO_DESC,
          contractStatus: record.estado === 'Activo' ? 'active' : 'inactive'
        };
        break;

      default:
        console.warn('[DrillDownView] No se puede hacer drill-down desde el nivel:', currentLevel);
        return;
    }

    setCurrentLevel(newLevel);
    setContext(newContext);
    setSelectedRecord(record);

    if (onLevelChange) {
      onLevelChange(newLevel, newContext, record);
    }

    messageApi.success(`Navegando a ${LEVEL_CONFIG[newLevel].title}`);
  }, [currentLevel, context, selectedRecord, onLevelChange, messageApi]);

  const navigateBack = useCallback((targetLevel) => {
    let newContext = { ...context };

    // Limpiar contexto según el nivel objetivo
    const levelHierarchy = [
      DRILL_LEVELS.CONSOLIDATED,
      DRILL_LEVELS.CENTER,
      DRILL_LEVELS.MANAGER,
      DRILL_LEVELS.CLIENT,
      DRILL_LEVELS.CONTRACT,
      DRILL_LEVELS.TRANSACTION
    ];

    const targetIndex = levelHierarchy.indexOf(targetLevel);
    const currentIndex = levelHierarchy.indexOf(currentLevel);

    if (targetIndex >= 0 && targetIndex < currentIndex) {
      // Limpiar contexto según el nivel
      switch (targetLevel) {
        case DRILL_LEVELS.CONSOLIDATED:
          newContext = {};
          break;
        case DRILL_LEVELS.CENTER:
          delete newContext.gestorId;
          delete newContext.gestorName;
          delete newContext.gestorPerformance;
          delete newContext.clienteId;
          delete newContext.clienteName;
          delete newContext.clientValue;
          delete newContext.contratoId;
          delete newContext.productName;
          delete newContext.contractStatus;
          break;
        case DRILL_LEVELS.MANAGER:
          delete newContext.clienteId;
          delete newContext.clienteName;
          delete newContext.clientValue;
          delete newContext.contratoId;
          delete newContext.productName;
          delete newContext.contractStatus;
          break;
        case DRILL_LEVELS.CLIENT:
          delete newContext.contratoId;
          delete newContext.productName;
          delete newContext.contractStatus;
          break;
        case DRILL_LEVELS.CONTRACT:
          // Mantener contexto del contrato
          break;
        default:
          break;
      }
    }

    setCurrentLevel(targetLevel);
    setContext(newContext);
    setSelectedRecord(null);

    if (onLevelChange) {
      onLevelChange(targetLevel, newContext, null);
    }

    messageApi.info(`Navegando a ${LEVEL_CONFIG[targetLevel].title}`);
  }, [context, onLevelChange, messageApi, currentLevel]);

  const navigateToSpecializedView = useCallback((specializedLevel) => {
    // Navegar a vistas especializadas (incentivos, precios, desviaciones)
    setCurrentLevel(specializedLevel);
    
    if (onLevelChange) {
      onLevelChange(specializedLevel, context, selectedRecord);
    }

    messageApi.info(`Abriendo análisis ${LEVEL_CONFIG[specializedLevel].title}`);
  }, [context, selectedRecord, onLevelChange, messageApi]);

  // ============================================================================
  // 🎛️ HANDLERS DE EVENTOS
  // ============================================================================

  const handleRefresh = useCallback(() => {
    loadLevelData(true);
    messageApi.success('Datos actualizados correctamente');
  }, [loadLevelData, messageApi]);

  const handleViewDetails = useCallback((record) => {
    setSelectedRecord(record);
    setDetailsDrawerOpen(true);
  }, []);

  const handleDeepAnalysis = useCallback(async (record) => {
    setSelectedRecord(record);
    setAnalysisDrawerOpen(true);
    
    if (chatEnabled && sendMessage) {
      try {
        const message = `Analizar en profundidad el ${LEVEL_CONFIG[currentLevel].title.toLowerCase()} ${
          record.DESC_GESTOR || record.nombre_cliente || record.contrato_id || 'seleccionado'
        } para el período ${currentPeriod}. Proporcionar insights y recomendaciones.`;
        
        await sendMessage(message, {
          context: {
            level: currentLevel,
            record: record,
            period: currentPeriod,
            analysisType: selectedAnalysisType
          }
        });
      } catch (error) {
        messageApi.error('Error en análisis conversacional: ' + error.message);
      }
    }
  }, [chatEnabled, sendMessage, currentLevel, currentPeriod, selectedAnalysisType, messageApi]);

  const handleExport = useCallback(async () => {
    setExportLoading(true);
    try {
      // Simular exportación
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      notification.success({
        message: 'Exportación Completada',
        description: `Datos del nivel ${LEVEL_CONFIG[currentLevel].title} exportados correctamente`,
        duration: 3
      });
    } catch (error) {
      notification.error({
        message: 'Error de Exportación',
        description: 'No se pudieron exportar los datos'
      });
    } finally {
      setExportLoading(false);
    }
  }, [currentLevel]);

  const handleIncentiveAnalysis = useCallback(() => {
    setIncentiveModalOpen(true);
    
    // Cargar datos específicos de incentivos
    if (incentiveData.length === 0) {
      loadIncentiveData(currentPeriod);
    }
  }, [incentiveData.length, currentPeriod]);

  const handlePricingAnalysis = useCallback(() => {
    setPricingModalOpen(true);
    
    // Cargar datos específicos de precios
    if (pricingData.length === 0) {
      loadPricingData(currentPeriod);
    }
  }, [pricingData.length, currentPeriod]);

  // ============================================================================
  // 📋 CONFIGURACIÓN DE TABLAS
  // ============================================================================

  const getTableColumns = useMemo(() => {
    const baseActions = (record) => (
      <Space size="small">
        <Tooltip title="Ver detalles completos">
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetails(record)}
          />
        </Tooltip>
        
        {LEVEL_CONFIG[currentLevel].canDrillDown && (
          <Tooltip title={`Drill-down a ${LEVEL_CONFIG[LEVEL_CONFIG[currentLevel].nextLevel]?.title}`}>
            <Button
              type="primary"
              size="small"
              icon={<SearchOutlined />}
              onClick={() => drillDown(record)}
              style={{
                backgroundColor: '#52c41a',
                borderColor: '#52c41a'
              }}
            />
          </Tooltip>
        )}
        
        {intelligentMode && (
          <Tooltip title="Análisis profundo con IA">
            <Button
              type="text"
              size="small"
              icon={<RobotOutlined />}
              onClick={() => handleDeepAnalysis(record)}
              style={{ color: '#722ed1' }}
            />
          </Tooltip>
        )}
      </Space>
    );

    // Configuración específica por nivel
    switch (currentLevel) {
      case DRILL_LEVELS.EXECUTIVE:
      case DRILL_LEVELS.CONSOLIDATED:
        return [
          {
            title: dashboardType === 'control_gestion' ? 'Centro' : 'Región',
            dataIndex: 'DESC_CENTRO',
            key: 'centro',
            ellipsis: true,
            render: (text, record) => (
              <Space>
                <Button
                  type="link"
                  onClick={() => drillDown(record)}
                  style={{ color: '#52c41a', padding: 0 }}
                >
                  {LEVEL_CONFIG[DRILL_LEVELS.CENTER].icon} {text}
                </Button>
                {record.TOTAL_GESTORES && (
                  <Badge count={record.TOTAL_GESTORES} size="small" color="#52c41a" />
                )}
              </Space>
            ),
            sorter: (a, b) => (a.DESC_CENTRO || '').localeCompare(b.DESC_CENTRO || ''),
          },
          {
            title: 'Performance',
            dataIndex: 'performance_score',
            key: 'performance',
            render: (value) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Progress 
                  percent={value} 
                  size="small" 
                  strokeColor={value >= 80 ? '#52c41a' : value >= 60 ? '#faad14' : '#ff4d4f'}
                  showInfo={false}
                  style={{ width: 80 }}
                />
                <span style={{ 
                  fontWeight: 600,
                  fontSize: 12,
                  color: value >= 80 ? '#52c41a' : value >= 60 ? '#faad14' : '#ff4d4f'
                }}>
                  {value?.toFixed(1)}%
                </span>
              </div>
            ),
            sorter: (a, b) => (a.performance_score || 0) - (b.performance_score || 0),
            width: 150
          },
          {
            title: 'Margen Neto',
            dataIndex: 'MARGEN_NETO',
            key: 'margen_neto',
            render: (value) => (
              <span style={{ 
                fontWeight: 600,
                color: value >= 10 ? '#52c41a' : value >= 5 ? '#faad14' : '#ff4d4f'
              }}>
                {value?.toFixed(2)}%
              </span>
            ),
            sorter: (a, b) => (a.MARGEN_NETO || 0) - (b.MARGEN_NETO || 0),
            width: 120
          },
          {
            title: 'ROE',
            dataIndex: 'ROE',
            key: 'roe',
            render: (value) => (
              <span style={{ fontFamily: 'monospace' }}>
                {value?.toFixed(2)}%
              </span>
            ),
            sorter: (a, b) => (a.ROE || 0) - (b.ROE || 0),
            width: 100
          },
          {
            title: 'Ingresos',
            dataIndex: 'TOTAL_INGRESOS',
            key: 'ingresos',
            render: (value) => (
              <span style={{ fontWeight: 500 }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.TOTAL_INGRESOS || 0) - (b.TOTAL_INGRESOS || 0),
            width: 140
          },
          {
            title: 'Contratos',
            dataIndex: 'TOTAL_CONTRATOS',
            key: 'contratos',
            render: (value) => (
              <Badge count={value} showZero color="#13c2c2" />
            ),
            sorter: (a, b) => (a.TOTAL_CONTRATOS || 0) - (b.TOTAL_CONTRATOS || 0),
            width: 100
          },
          {
            title: 'Acciones',
            key: 'actions',
            width: 140,
            render: (_, record) => baseActions(record),
          }
        ];

      case DRILL_LEVELS.CENTER:
        return [
          {
            title: 'Gestor',
            dataIndex: 'DESC_GESTOR',
            key: 'gestor',
            render: (text, record) => (
              <Space direction="vertical" size={0}>
                <Button
                  type="link"
                  onClick={() => drillDown(record)}
                  style={{ color: '#13c2c2', padding: 0 }}
                >
                  {LEVEL_CONFIG[DRILL_LEVELS.MANAGER].icon} {text}
                </Button>
                <Tag size="small" color="#52c41a">
                  {record.DESC_SEGMENTO || record.segmento || 'Segmento'}
                </Tag>
              </Space>
            ),
          },
          {
            title: 'Performance',
            dataIndex: 'performance_score',
            key: 'performance',
            render: (value) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Progress 
                  percent={value} 
                  size="small" 
                  strokeColor={value >= 80 ? '#52c41a' : value >= 60 ? '#faad14' : '#ff4d4f'}
                  showInfo={false}
                  style={{ width: 60 }}
                />
                <span style={{ fontSize: 11, fontWeight: 600 }}>
                  {value?.toFixed(0)}%
                </span>
              </div>
            ),
            sorter: (a, b) => (a.performance_score || 0) - (b.performance_score || 0),
          },
          {
            title: 'Margen',
            dataIndex: 'MARGEN_NETO',
            key: 'margen',
            render: (value) => (
              <span style={{ 
                fontWeight: 600,
                color: value >= 8 ? '#52c41a' : '#faad14'
              }}>
                {value?.toFixed(2)}%
              </span>
            ),
            sorter: (a, b) => (a.MARGEN_NETO || 0) - (b.MARGEN_NETO || 0),
          },
          {
            title: 'Ingresos',
            dataIndex: 'TOTAL_INGRESOS',
            key: 'ingresos',
            render: (value) => `€${value?.toLocaleString()}`,
            sorter: (a, b) => (a.TOTAL_INGRESOS || 0) - (b.TOTAL_INGRESOS || 0),
          },
          {
            title: 'Contratos',
            dataIndex: 'CONTRATOS_ACTIVOS',
            key: 'contratos',
            render: (value) => (
              <Badge count={value} showZero color="#faad14" />
            ),
            sorter: (a, b) => (a.CONTRATOS_ACTIVOS || 0) - (b.CONTRATOS_ACTIVOS || 0),
          },
          {
            title: 'Acciones',
            key: 'actions',
            width: 140,
            render: (_, record) => baseActions(record),
          }
        ];

      case DRILL_LEVELS.MANAGER:
        if (data.length === 1 && data[0].type === 'summary') {
          // Vista resumen del gestor
          return [
            {
              title: 'Métrica',
              dataIndex: 'metric',
              key: 'metric',
              render: () => 'Resumen del Gestor',
            },
            {
              title: 'Performance',
              key: 'performance',
              render: (_, record) => `${record.performance_score || context.gestorPerformance || 75}%`,
            },
            {
              title: 'Margen Neto',
              key: 'margen',
              render: (_, record) => `${record.MARGEN_NETO || 8.5}%`,
            },
            {
              title: 'Clientes',
              key: 'clientes',
              render: (_, record) => record.TOTAL_CLIENTES || 0,
            },
            {
              title: 'Contratos',
              key: 'contratos', 
              render: (_, record) => record.CONTRATOS_ACTIVOS || 0,
            },
            {
              title: 'Incentivo Est.',
              key: 'incentivo',
              render: (_, record) => (
                <span style={{ color: '#eb2f96', fontWeight: 600 }}>
                  €{(record.incentivo_estimado || 5250).toLocaleString()}
                </span>
              ),
            }
          ];
        }
        
        // Vista clientes del gestor
        return [
          {
            title: 'Cliente',
            dataIndex: 'nombre_cliente',
            key: 'cliente',
            render: (text, record) => (
              <Space direction="vertical" size={0}>
                <Button
                  type="link"
                  onClick={() => drillDown(record)}
                  style={{ color: '#faad14', padding: 0 }}
                >
                  {LEVEL_CONFIG[DRILL_LEVELS.CLIENT].icon} {text}
                </Button>
                <Tag size="small" color="#13c2c2">
                  {record.segmento || 'Segmento'}
                </Tag>
              </Space>
            ),
          },
          {
            title: 'Contratos',
            dataIndex: 'total_contratos',
            key: 'contratos',
            render: (value) => (
              <Badge count={value} showZero color="#52c41a" />
            ),
            sorter: (a, b) => (a.total_contratos || 0) - (b.total_contratos || 0),
          },
          {
            title: 'Volumen',
            dataIndex: 'volumen_gestionado',
            key: 'volumen',
            render: (value) => (
              <span style={{ fontWeight: 500 }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.volumen_gestionado || 0) - (b.volumen_gestionado || 0),
          },
          {
            title: 'Margen Gen.',
            dataIndex: 'margen_generado',
            key: 'margen',
            render: (value) => (
              <span style={{ fontWeight: 600, color: '#52c41a' }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.margen_generado || 0) - (b.margen_generado || 0),
          },
          {
            title: 'Rentabilidad',
            dataIndex: 'rentabilidad',
            key: 'rentabilidad',
            render: (value) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Progress 
                  percent={Math.min(100, value * 50)} 
                  size="small"
                  strokeColor={value >= 1.5 ? '#52c41a' : value >= 1.0 ? '#faad14' : '#ff4d4f'}
                  showInfo={false}
                  style={{ width: 50 }}
                />
                <span style={{ fontSize: 11, fontWeight: 600 }}>
                  {value?.toFixed(2)}%
                </span>
              </div>
            ),
            sorter: (a, b) => (a.rentabilidad || 0) - (b.rentabilidad || 0),
          },
          {
            title: 'Acciones',
            key: 'actions',
            width: 140,
            render: (_, record) => baseActions(record),
          }
        ];

      case DRILL_LEVELS.CLIENT:
        return [
          {
            title: 'Cliente',
            dataIndex: 'nombre_cliente',
            key: 'cliente',
            render: (text, record) => (
              <Space direction="vertical" size={0}>
                <Button
                  type="link"
                  onClick={() => drillDown(record)}
                  style={{ color: '#faad14', padding: 0 }}
                >
                  {LEVEL_CONFIG[DRILL_LEVELS.CLIENT].icon} {text}
                </Button>
                <span style={{ fontSize: 11, color: '#999' }}>
                  {record.segmento}
                </span>
              </Space>
            ),
          },
          {
            title: 'Contratos',
            dataIndex: 'total_contratos',
            key: 'contratos',
            render: (value) => (
              <Badge count={value} showZero color="#52c41a" />
            ),
            sorter: (a, b) => (a.total_contratos || 0) - (b.total_contratos || 0),
          },
          {
            title: 'Volumen Gestionado',
            dataIndex: 'volumen_gestionado',
            key: 'volumen',
            render: (value) => (
              <span style={{ fontWeight: 500 }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.volumen_gestionado || 0) - (b.volumen_gestionado || 0),
          },
          {
            title: 'Margen Generado',
            dataIndex: 'margen_generado',
            key: 'margen',
            render: (value) => (
              <span style={{ fontWeight: 600, color: '#52c41a' }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.margen_generado || 0) - (b.margen_generado || 0),
          },
          {
            title: 'Rentabilidad',
            dataIndex: 'rentabilidad',
            key: 'rentabilidad',
            render: (value) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Progress 
                  percent={Math.min(100, value * 50)} 
                  size="small"
                  strokeColor={value >= 1.5 ? '#52c41a' : value >= 1.0 ? '#faad14' : '#ff4d4f'}
                  showInfo={false}
                  style={{ width: 60 }}
                />
                <span style={{ 
                  fontWeight: 600,
                  fontSize: 12,
                  color: value >= 1.5 ? '#52c41a' : value >= 1.0 ? '#faad14' : '#ff4d4f'
                }}>
                  {value?.toFixed(2)}%
                </span>
              </div>
            ),
            sorter: (a, b) => (a.rentabilidad || 0) - (b.rentabilidad || 0),
          },
          {
            title: 'Acciones',
            key: 'actions',
            width: 140,
            render: (_, record) => baseActions(record),
          }
        ];

      case DRILL_LEVELS.CONTRACT:
        return [
          {
            title: 'Contrato',
            dataIndex: 'contrato_id',
            key: 'contrato',
            render: (text, record) => (
              <Space direction="vertical" size={0}>
                <Button
                  type="link"
                  onClick={() => drillDown(record)}
                  style={{ color: '#fa8c16', padding: 0 }}
                >
                  {LEVEL_CONFIG[DRILL_LEVELS.CONTRACT].icon} {text}
                </Button>
                <span style={{ fontSize: 11, color: '#999' }}>
                  {record.producto_desc}
                </span>
              </Space>
            ),
          },
          {
            title: 'Fecha Alta',
            dataIndex: 'fecha_alta',
            key: 'fecha',
            render: (date) => (
              <Space>
                <CalendarOutlined />
                <span style={{ fontSize: 12 }}>
                  {new Date(date).toLocaleDateString('es-ES')}
                </span>
              </Space>
            ),
            sorter: (a, b) => new Date(a.fecha_alta) - new Date(b.fecha_alta),
          },
          {
            title: 'Volumen',
            dataIndex: 'volumen',
            key: 'volumen',
            render: (value) => (
              <span style={{ fontWeight: 500 }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.volumen || 0) - (b.volumen || 0),
          },
          {
            title: 'Margen Mensual',
            dataIndex: 'margen_mensual',
            key: 'margen_mensual',
            render: (value) => (
              <span style={{ fontWeight: 600, color: '#52c41a' }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.margen_mensual || 0) - (b.margen_mensual || 0),
          },
          {
            title: 'Rent. Anual',
            dataIndex: 'rentabilidad_anual',
            key: 'rentabilidad_anual',
            render: (value) => (
              <span style={{ fontWeight: 600, color: '#eb2f96' }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.rentabilidad_anual || 0) - (b.rentabilidad_anual || 0),
          },
          {
            title: 'Estado',
            dataIndex: 'estado',
            key: 'estado',
            render: (status) => (
              <Badge 
                status={status === 'Activo' ? 'success' : 'default'} 
                text={status}
              />
            ),
            filters: [
              { text: 'Activo', value: 'Activo' },
              { text: 'Inactivo', value: 'Inactivo' }
            ],
            onFilter: (value, record) => record.estado === value,
          },
          {
            title: 'Acciones',
            key: 'actions',
            width: 140,
            render: (_, record) => baseActions(record),
          }
        ];

      case DRILL_LEVELS.TRANSACTION:
        return [
          {
            title: 'Movimiento',
            dataIndex: 'movimiento_id',
            key: 'movimiento',
            render: (text) => (
              <Space>
                {LEVEL_CONFIG[DRILL_LEVELS.TRANSACTION].icon}
                <span style={{ fontFamily: 'monospace', fontSize: 11 }}>
                  {text}
                </span>
              </Space>
            ),
            width: 120
          },
          {
            title: 'Fecha',
            dataIndex: 'fecha',
            key: 'fecha',
            render: (date) => (
              <Space>
                <CalendarOutlined />
                <span style={{ fontSize: 11 }}>
                  {new Date(date).toLocaleDateString('es-ES')}
                </span>
              </Space>
            ),
            sorter: (a, b) => new Date(a.fecha) - new Date(b.fecha),
            width: 110
          },
          {
            title: 'Concepto',
            dataIndex: 'concepto',
            key: 'concepto',
            ellipsis: { showTitle: false },
            render: (text) => (
              <Tooltip title={text}>
                <span style={{ fontSize: 11 }}>{text}</span>
              </Tooltip>
            ),
          },
          {
            title: 'Cuenta',
            dataIndex: 'cuenta',
            key: 'cuenta',
            render: (text) => (
              <Tag style={{ fontFamily: 'monospace', fontSize: 10 }}>
                {text}
              </Tag>
            ),
            width: 90
          },
          {
            title: 'Importe',
            dataIndex: 'importe',
            key: 'importe',
            render: (value) => (
              <span style={{ 
                color: value >= 0 ? '#52c41a' : '#ff4d4f',
                fontWeight: 600,
                fontFamily: 'monospace'
              }}>
                {value >= 0 ? '+' : ''}€{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.importe || 0) - (b.importe || 0),
            width: 120
          },
          {
            title: 'Tipo',
            dataIndex: 'tipo',
            key: 'tipo',
            render: (type) => (
              <Badge 
                status={type === 'Ingreso' ? 'success' : 'error'} 
                text={type}
              />
            ),
            filters: [
              { text: 'Ingreso', value: 'Ingreso' },
              { text: 'Gasto', value: 'Gasto' }
            ],
            onFilter: (value, record) => record.tipo === value,
            width: 100
          },
          {
            title: 'Acciones',
            key: 'actions',
            width: 80,
            render: (_, record) => (
              <Tooltip title="Ver detalles">
                <Button
                  type="text"
                  size="small"
                  icon={<EyeOutlined />}
                  onClick={() => handleViewDetails(record)}
                />
              </Tooltip>
            ),
          }
        ];

      case DRILL_LEVELS.INCENTIVE:
        return [
          {
            title: 'Gestor',
            key: 'gestor',
            render: (_, record) => (
              <Space direction="vertical" size={0}>
                <span style={{ fontWeight: 600 }}>
                  {record.gestor_nombre || record.desc_gestor || 'Gestor'}
                </span>
                <Tag size="small" color="#13c2c2">
                  {record.segmento || 'Segmento'}
                </Tag>
              </Space>
            ),
          },
          {
            title: 'Performance',
            dataIndex: 'performance_score',
            key: 'performance',
            render: (value) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Progress 
                  percent={value} 
                  size="small" 
                  strokeColor={value >= 80 ? '#52c41a' : value >= 60 ? '#faad14' : '#ff4d4f'}
                  showInfo={false}
                  style={{ width: 60 }}
                />
                <span style={{ fontSize: 11, fontWeight: 600 }}>
                  {value?.toFixed(0)}%
                </span>
              </div>
            ),
            sorter: (a, b) => (a.performance_score || 0) - (b.performance_score || 0),
          },
          {
            title: 'Cumpl. Objetivos',
            dataIndex: 'cumplimiento_objetivos',
            key: 'cumplimiento',
            render: (value) => (
              <span style={{
                color: value >= 90 ? '#52c41a' : value >= 70 ? '#faad14' : '#ff4d4f',
                fontWeight: 600
              }}>
                {value?.toFixed(0)}%
              </span>
            ),
            sorter: (a, b) => (a.cumplimiento_objetivos || 0) - (b.cumplimiento_objetivos || 0),
          },
          {
            title: 'Incentivo Base',
            key: 'incentivo_base',
            render: () => '€5,000',
          },
          {
            title: 'Multiplicadores',
            key: 'multiplicadores',
            render: (_, record) => (
              <Space direction="vertical" size={0}>
                <span style={{ fontSize: 11 }}>
                  Perf: {((record.performance_score || 75) / 100).toFixed(2)}x
                </span>
                <span style={{ fontSize: 11 }}>
                  Obj: {((record.cumplimiento_objetivos || 80) / 100).toFixed(2)}x
                </span>
              </Space>
            ),
          },
          {
            title: 'Incentivo Final',
            dataIndex: 'incentivo_calculado',
            key: 'incentivo_final',
            render: (value) => (
              <span style={{ 
                fontWeight: 700, 
                fontSize: 14,
                color: '#eb2f96' 
              }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.incentivo_calculado || 0) - (b.incentivo_calculado || 0),
          },
          {
            title: 'Ranking',
            dataIndex: 'ranking',
            key: 'ranking',
            render: (value) => (
              <Badge 
                count={value} 
                style={{ 
                  backgroundColor: value <= 3 ? '#faad14' : value <= 10 ? '#52c41a' : '#13c2c2' 
                }}
              />
            ),
          }
        ];

      case DRILL_LEVELS.PRICING:
        return [
          {
            title: 'Producto',
            key: 'producto',
            render: (_, record) => (
              <Space direction="vertical" size={0}>
                <span style={{ fontWeight: 600 }}>
                  {record.producto_desc}
                </span>
                <Tag size="small" color="#faad14">
                  {record.segmento_desc}
                </Tag>
              </Space>
            ),
          },
          {
            title: 'Precio Real',
            dataIndex: 'precio_real',
            key: 'precio_real',
            render: (value) => (
              <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.precio_real || 0) - (b.precio_real || 0),
          },
          {
            title: 'Precio Estándar',
            dataIndex: 'precio_estandar',
            key: 'precio_estandar',
            render: (value) => (
              <span style={{ fontFamily: 'monospace', color: '#666' }}>
                €{value?.toLocaleString()}
              </span>
            ),
            sorter: (a, b) => (a.precio_estandar || 0) - (b.precio_estandar || 0),
          },
          {
            title: 'Desviación',
            dataIndex: 'desviacion_porcentual',
            key: 'desviacion',
            render: (value) => {
              const severity = calculateDeviationSeverity(value);
              const colors = {
                critical: '#ff4d4f',
                high: '#fa8c16', 
                warning: '#fadb14',
                attention: '#52c41a',
                normal: '#52c41a'
              };
              
              return (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Badge 
                    status={severity === 'critical' ? 'error' : severity === 'high' ? 'warning' : 'success'}
                  />
                  <span style={{
                    fontWeight: 600,
                    color: colors[severity],
                    fontFamily: 'monospace'
                  }}>
                    {value > 0 ? '+' : ''}{value?.toFixed(1)}%
                  </span>
                </div>
              );
            },
            sorter: (a, b) => Math.abs(b.desviacion_porcentual || 0) - Math.abs(a.desviacion_porcentual || 0),
          },
          {
            title: 'Diferencia',
            dataIndex: 'desviacion_absoluta',
            key: 'diferencia',
            render: (value) => (
              <span style={{
                fontWeight: 600,
                color: value >= 0 ? '#ff4d4f' : '#52c41a',
                fontFamily: 'monospace'
              }}>
                {value >= 0 ? '+' : ''}€{value?.toLocaleString()}
              </span>
            ),
          },
          {
            title: 'Período',
            dataIndex: 'periodo',
            key: 'periodo',
            render: (value) => (
              <Tag size="small">{value}</Tag>
            ),
          },
          {
            title: 'Acciones',
            key: 'actions',
            width: 100,
            render: (_, record) => (
              <Space size="small">
                <Tooltip title="Ver detalles">
                  <Button
                    type="text"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => handleViewDetails(record)}
                  />
                </Tooltip>
                <Tooltip title="Análisis IA">
                  <Button
                    type="text"
                    size="small"
                    icon={<RobotOutlined />}
                    onClick={() => handleDeepAnalysis(record)}
                    style={{ color: '#722ed1' }}
                  />
                </Tooltip>
              </Space>
            ),
          }
        ];

      default:
        return [];
    }
  }, [currentLevel, drillDown, handleViewDetails, handleDeepAnalysis, intelligentMode, dashboardType]);

  // ============================================================================
  // 🎨 DATOS MOCK PARA FALLBACK
  // ============================================================================

  const generateMockConsolidatedData = (dashboardType, gestorId) => {
    if (dashboardType === 'gestor' && gestorId) {
      // Datos específicos para gestor individual
      return [{
        key: 'gestor_summary',
        type: 'summary',
        DESC_GESTOR: `Gestor ${gestorId}`,
        performance_score: 82.5,
        MARGEN_NETO: 9.2,
        ROE: 13.8,
        TOTAL_INGRESOS: 425000,
        TOTAL_CLIENTES: 35,
        CONTRATOS_ACTIVOS: 52,
        VOLUMEN_GESTIONADO: 2850000,
        incentivo_estimado: 6240
      }];
    }

    // Datos consolidados para Control de Gestión
    return [
      { 
        key: '1', DESC_CENTRO: 'MADRID-OFICINA PRINCIPAL', DESC_GESTOR: 'García Ruiz, Ana',
        CENTRO_ID: 1, GESTOR_ID: 1, MARGEN_NETO: 12.8, ROE: 15.4, 
        TOTAL_INGRESOS: 890000, TOTAL_GESTORES: 8, TOTAL_CONTRATOS: 125,
        performance_score: 91.2, EFICIENCIA_OPERATIVA: 88.5
      },
      { 
        key: '2', DESC_CENTRO: 'BARCELONA-BALMES', DESC_GESTOR: 'López Martín, Carlos', 
        CENTRO_ID: 3, GESTOR_ID: 17, MARGEN_NETO: 11.9, ROE: 14.8, 
        TOTAL_INGRESOS: 755000, TOTAL_GESTORES: 5, TOTAL_CONTRATOS: 92,
        performance_score: 87.6, EFICIENCIA_OPERATIVA: 85.2
      },
      { 
        key: '3', DESC_CENTRO: 'PALMA-SANT MIQUEL', DESC_GESTOR: 'Garau Mesquida, Joan', 
        CENTRO_ID: 2, GESTOR_ID: 9, MARGEN_NETO: 10.5, ROE: 13.2, 
        TOTAL_INGRESOS: 680000, TOTAL_GESTORES: 8, TOTAL_CONTRATOS: 105,
        performance_score: 79.8, EFICIENCIA_OPERATIVA: 82.1
      },
      { 
        key: '4', DESC_CENTRO: 'BILBAO-MARQUÉS DEL PUERTO', DESC_GESTOR: 'Etxebarria Goikoetxea, Mikel', 
        CENTRO_ID: 5, GESTOR_ID: 27, MARGEN_NETO: 10.1, ROE: 12.9, 
        TOTAL_INGRESOS: 620000, TOTAL_GESTORES: 4, TOTAL_CONTRATOS: 68,
        performance_score: 76.5, EFICIENCIA_OPERATIVA: 80.8
      },
      { 
        key: '5', DESC_CENTRO: 'MÁLAGA-PARQUE LITORAL', DESC_GESTOR: 'Jiménez Moreno, Isabel', 
        CENTRO_ID: 4, GESTOR_ID: 22, MARGEN_NETO: 9.3, ROE: 12.1, 
        TOTAL_INGRESOS: 580000, TOTAL_GESTORES: 5, TOTAL_CONTRATOS: 78,
        performance_score: 73.2, EFICIENCIA_OPERATIVA: 78.9
      }
    ];
  };

  const generateMockCenterData = (centroId) => [
    { 
      key: '1', DESC_GESTOR: 'García Ruiz, Ana', GESTOR_ID: 1, 
      DESC_SEGMENTO: 'Banca Personal', MARGEN_NETO: 12.8, ROE: 15.4,
      TOTAL_INGRESOS: 295000, performance_score: 89.2, CONTRATOS_ACTIVOS: 35,
      EFICIENCIA_OPERATIVA: 88.5, centro_id: centroId
    },
    { 
      key: '2', DESC_GESTOR: 'Martínez López, José', GESTOR_ID: 2, 
      DESC_SEGMENTO: 'Banca de Empresas', MARGEN_NETO: 11.2, ROE: 14.1,
      TOTAL_INGRESOS: 340000, performance_score: 78.6, CONTRATOS_ACTIVOS: 28,
      EFICIENCIA_OPERATIVA: 85.2, centro_id: centroId
    },
    { 
      key: '3', DESC_GESTOR: 'Fernández Ruiz, Carmen', GESTOR_ID: 3, 
      DESC_SEGMENTO: 'Banca Privada', MARGEN_NETO: 15.8, ROE: 18.2,
      TOTAL_INGRESOS: 185000, performance_score: 94.1, CONTRATOS_ACTIVOS: 18,
      EFICIENCIA_OPERATIVA: 92.1, centro_id: centroId
    },
    { 
      key: '4', DESC_GESTOR: 'González Sánchez, Miguel', GESTOR_ID: 4, 
      DESC_SEGMENTO: 'Fondos', MARGEN_NETO: 9.1, ROE: 11.8,
      TOTAL_INGRESOS: 450000, performance_score: 71.3, CONTRATOS_ACTIVOS: 48,
      EFICIENCIA_OPERATIVA: 75.8, centro_id: centroId
    }
  ];

  const generateMockManagerData = (gestorId) => [
    { 
      key: 'summary', type: 'summary', GESTOR_ID: gestorId,
      performance_score: 82.5, MARGEN_NETO: 10.8, ROE: 13.6,
      EFICIENCIA_OPERATIVA: 85.2, TOTAL_CLIENTES: 45, CONTRATOS_ACTIVOS: 67, 
      VOLUMEN_GESTIONADO: 2850000, incentivo_estimado: 6240,
      cumplimiento_objetivos: 87.5, ranking_centro: 2
    }
  ];

  const generateMockClientData = (gestorId) => [
    { 
      key: '1', cliente_id: 1, CLIENTE_ID: 1, 
      nombre_cliente: 'García Martínez, José Luis', 
      segmento: 'Banca Personal', total_contratos: 3, 
      volumen_gestionado: 285000, margen_generado: 3420,
      rentabilidad: 1.2, gestor_id: gestorId
    },
    { 
      key: '2', cliente_id: 2, CLIENTE_ID: 2,
      nombre_cliente: 'Tecnologías Avanzadas S.L.', 
      segmento: 'Banca de Empresas', total_contratos: 5, 
      volumen_gestionado: 750000, margen_generado: 8950,
      rentabilidad: 1.19, gestor_id: gestorId
    },
    { 
      key: '3', cliente_id: 3, CLIENTE_ID: 3,
      nombre_cliente: 'López Fernández, María Carmen', 
      segmento: 'Banca Privada', total_contratos: 2, 
      volumen_gestionado: 1250000, margen_generado: 12300,
      rentabilidad: 0.98, gestor_id: gestorId
    },
    { 
      key: '4', cliente_id: 4, CLIENTE_ID: 4,
      nombre_cliente: 'Inmobiliaria Costa Azul S.A.', 
      segmento: 'Banca de Empresas', total_contratos: 4, 
      volumen_gestionado: 680000, margen_generado: 7200,
      rentabilidad: 1.06, gestor_id: gestorId
    }
  ];

  const generateMockContractData = (clienteId) => [
    { 
      key: '1', contrato_id: '1001', CONTRATO_ID: '1001',
      producto_desc: 'Préstamo Hipotecario', PRODUCTO_DESC: 'Préstamo Hipotecario',
      fecha_alta: '2025-03-15', volumen: 250000, margen_mensual: 890, 
      estado: 'Activo', rentabilidad_anual: 10680, cliente_id: clienteId
    },
    { 
      key: '2', contrato_id: '2005', CONTRATO_ID: '2005',
      producto_desc: 'Depósito a Plazo Fijo', PRODUCTO_DESC: 'Depósito a Plazo Fijo',
      fecha_alta: '2025-05-20', volumen: 35000, margen_mensual: 125, 
      estado: 'Activo', rentabilidad_anual: 1500, cliente_id: clienteId
    },
    { 
      key: '3', contrato_id: '3012', CONTRATO_ID: '3012',
      producto_desc: 'Fondo Banca March', PRODUCTO_DESC: 'Fondo Banca March',
      fecha_alta: '2025-07-10', volumen: 150000, margen_mensual: 450, 
      estado: 'Activo', rentabilidad_anual: 5400, cliente_id: clienteId
    }
  ];

  const generateMockTransactionData = (contratoId) => [
    { 
      key: '1', movimiento_id: 'M001', MOVIMIENTO_ID: 'M001',
      fecha: '2025-10-01', concepto: 'Intereses cobrados préstamo hipotecario', 
      cuenta: '760001', importe: 890.50, tipo: 'Ingreso', mes: 'Oct 2025',
      contrato_id: contratoId
    },
    { 
      key: '2', movimiento_id: 'M002', MOVIMIENTO_ID: 'M002',
      fecha: '2025-10-15', concepto: 'Comisión de gestión', 
      cuenta: '760012', importe: 45.00, tipo: 'Ingreso', mes: 'Oct 2025',
      contrato_id: contratoId
    },
    { 
      key: '3', movimiento_id: 'M003', MOVIMIENTO_ID: 'M003',
      fecha: '2025-10-20', concepto: 'Gasto operativo asignado', 
      cuenta: '620001', importe: -125.30, tipo: 'Gasto', mes: 'Oct 2025',
      contrato_id: contratoId
    },
    { 
      key: '4', movimiento_id: 'M004', MOVIMIENTO_ID: 'M004',
      fecha: '2025-10-25', concepto: 'Comisión por cancelación anticipada', 
      cuenta: '760008', importe: 250.00, tipo: 'Ingreso', mes: 'Oct 2025',
      contrato_id: contratoId
    }
  ];

  const generateMockIncentiveData = (gestorId) => [
    {
      key: '1',
      gestor_id: gestorId,
      gestor_nombre: `Gestor ${gestorId}`,
      desc_gestor: `Gestor ${gestorId}`,
      segmento: 'Banca Personal',
      performance_score: 85.2,
      cumplimiento_objetivos: 89.5,
      incentivo_base: 5000,
      multiplicador_performance: 1.17,
      multiplicador_objetivos: 1.03,
      incentivo_calculado: 6025,
      ranking: 2,
      percentil: 78
    },
    {
      key: '2',
      gestor_id: gestorId + 1,
      gestor_nombre: `Gestor ${gestorId + 1}`,
      desc_gestor: `Gestor ${gestorId + 1}`,
      segmento: 'Banca Privada',
      performance_score: 92.1,
      cumplimiento_objetivos: 95.2,
      incentivo_base: 5000,
      multiplicador_performance: 1.25,
      multiplicador_objetivos: 1.08,
      incentivo_calculado: 6750,
      ranking: 1,
      percentil: 95
    }
  ];

  const generateMockPricingData = () => [
    {
      key: 'N10101_100100100100',
      SEGMENTO_ID: 'N10101',
      PRODUCTO_ID: '100100100100',
      segmento_desc: 'Banca Minorista',
      producto_desc: 'Préstamo Hipotecario',
      precio_real: 1285.50,
      precio_estandar: 1200.00,
      desviacion_absoluta: 85.50,
      desviacion_porcentual: 7.13,
      severity: 'attention',
      periodo: '2025-10'
    },
    {
      key: 'N10102_600100300300',
      SEGMENTO_ID: 'N10102',
      PRODUCTO_ID: '600100300300',
      segmento_desc: 'Banca Privada',
      producto_desc: 'Fondo Banca March',
      precio_real: 1180.25,
      precio_estandar: 1320.00,
      desviacion_absoluta: -139.75,
      desviacion_porcentual: -10.59,
      severity: 'warning',
      periodo: '2025-10'
    },
    {
      key: 'N10103_400200100100',
      SEGMENTO_ID: 'N10103',
      PRODUCTO_ID: '400200100100',
      segmento_desc: 'Banca de Empresas',
      producto_desc: 'Depósito a Plazo Fijo',
      precio_real: 1450.80,
      precio_estandar: 1250.00,
      desviacion_absoluta: 200.80,
      desviacion_porcentual: 16.06,
      severity: 'high',
      periodo: '2025-10'
    }
  ];

  const generateMockDeviationData = () => [
    {
      key: '1',
      id: 'dev_001',
      gestor_id: 1,
      gestor_name: 'García Ruiz, Ana',
      desc_gestor: 'García Ruiz, Ana',
      category: 'PRECIO',
      deviation_percent: -18.5,
      severity: 'critical',
      valor_real: 1285.50,
      valor_estandar: 1580.00,
      impacto_margen: -2940.50
    },
    {
      key: '2',
      id: 'dev_002',
      gestor_id: 2,
      gestor_name: 'López Martín, Carlos',
      desc_gestor: 'López Martín, Carlos',
      category: 'MARGEN',
      deviation_percent: 12.3,
      severity: 'warning',
      valor_real: 11.2,
      valor_estandar: 10.0,
      impacto_margen: 1560.00
    }
  ];

  const generateFallbackData = (level, context, dashboardType) => {
    switch (level) {
      case DRILL_LEVELS.EXECUTIVE:
      case DRILL_LEVELS.CONSOLIDATED:
        return generateMockConsolidatedData(dashboardType, context.gestorId);
      case DRILL_LEVELS.CENTER:
        return generateMockCenterData(context.centroId);
      case DRILL_LEVELS.MANAGER:
        return generateMockManagerData(context.gestorId);
      case DRILL_LEVELS.CLIENT:
        return generateMockClientData(context.gestorId);
      case DRILL_LEVELS.CONTRACT:
        return generateMockContractData(context.clienteId);
      case DRILL_LEVELS.TRANSACTION:
        return generateMockTransactionData(context.contratoId);
      case DRILL_LEVELS.INCENTIVE:
        return generateMockIncentiveData(context.gestorId);
      case DRILL_LEVELS.PRICING:
        return generateMockPricingData();
      case DRILL_LEVELS.DEVIATION:
        return generateMockDeviationData();
      default:
        return [];
    }
  };

  // ============================================================================
  // ⚡ EFECTOS Y CICLO DE VIDA
  // ============================================================================

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        // Cargar períodos disponibles
        const periodsResponse = await api.getAvailablePeriods();
        setAvailablePeriods(periodsResponse.periods || []);
        
        if (!currentPeriod) {
          setCurrentPeriod(periodsResponse.latest || '2025-10');
        }
      } catch (error) {
        console.error('❌ Error cargando períodos:', error);
      }
    };

    loadInitialData();
  }, [currentPeriod]);

  useEffect(() => {
    if (currentPeriod) {
      loadLevelData();
    }
  }, [currentLevel, currentPeriod, dashboardType, gestorId, loadLevelData]);

  useEffect(() => {
    // Auto refresh
    if (autoRefresh) {
      autoRefreshTimer.current = setInterval(() => {
        loadLevelData(true);
      }, 5 * 60 * 1000); // 5 minutos
    } else {
      if (autoRefreshTimer.current) {
        clearInterval(autoRefreshTimer.current);
        autoRefreshTimer.current = null;
      }
    }

    return () => {
      if (autoRefreshTimer.current) {
        clearInterval(autoRefreshTimer.current);
        autoRefreshTimer.current = null;
      }
    };
  }, [autoRefresh, loadLevelData]);

  // ============================================================================
  // 🎨 FUNCIONES DE RENDERIZADO
  // ============================================================================

  const renderTitle = () => {
    const config = LEVEL_CONFIG[currentLevel];
    let title = config.title;
    
    switch (currentLevel) {
      case DRILL_LEVELS.EXECUTIVE:
        title = 'Dashboard Ejecutivo - Vista Estratégica';
        break;
      case DRILL_LEVELS.CONSOLIDATED:
        title = executiveMode ? 'Vista Ejecutiva Consolidada' : 'Vista Consolidada Global';
        break;
      case DRILL_LEVELS.CENTER:
        title = `Centro: ${context.centroName || context.centroId}`;
        break;
      case DRILL_LEVELS.MANAGER:
        title = `Gestor: ${context.gestorName || context.gestorId}`;
        break;
      case DRILL_LEVELS.CLIENT:
        title = `Cartera del Gestor ${context.gestorName || context.gestorId}`;
        break;
      case DRILL_LEVELS.CONTRACT:
        title = `Contratos de ${context.clienteName || context.clienteId}`;
        break;
      case DRILL_LEVELS.TRANSACTION:
        title = `Movimientos del Contrato ${context.contratoId}`;
        break;
      case DRILL_LEVELS.INCENTIVE:
        title = 'Análisis de Incentivos y Comisiones';
        break;
      case DRILL_LEVELS.PRICING:
        title = 'Análisis de Precios: Real vs Estándar';
        break;
      case DRILL_LEVELS.DEVIATION:
        title = 'Análisis de Desviaciones Críticas';
        break;
      case DRILL_LEVELS.ANALYSIS:
        title = `Análisis Profundo: ${selectedAnalysisType}`;
        break;
      default:
        break;
    }

    return title;
  };

  const renderLevelStats = () => {
    if (!data || data.length === 0) return null;

    let stats = [];

    switch (currentLevel) {
      case DRILL_LEVELS.EXECUTIVE:
      case DRILL_LEVELS.CONSOLIDATED:
        const avgMargin = data.reduce((sum, item) => sum + (item.MARGEN_NETO || 0), 0) / data.length;
        const totalIncome = data.reduce((sum, item) => sum + (item.TOTAL_INGRESOS || 0), 0);
        const avgPerformance = data.reduce((sum, item) => sum + (item.performance_score || 0), 0) / data.length;
        const totalContracts = data.reduce((sum, item) => sum + (item.TOTAL_CONTRATOS || 0), 0);
        
        stats = [
          { 
            title: dashboardType === 'control_gestion' ? 'Centros' : 'Regiones', 
            value: data.length, 
            icon: <BankOutlined />,
            color: '#1890ff'
          },
          { 
            title: 'Performance Media', 
            value: `${avgPerformance.toFixed(1)}%`, 
            icon: <TrophyFilled />,
            color: avgPerformance >= 80 ? '#52c41a' : '#faad14'
          },
          { 
            title: 'Margen Promedio', 
            value: `${avgMargin.toFixed(2)}%`, 
            icon: <RiseOutlined />,
            color: avgMargin >= 10 ? '#52c41a' : '#faad14'
          },
          { 
            title: 'Ingresos Totales', 
            value: `€${totalIncome.toLocaleString()}`, 
            icon: <DollarOutlined />,
            color: '#52c41a'
          },
          { 
            title: 'Contratos Totales', 
            value: totalContracts, 
            icon: <FileTextOutlined />,
            color: '#13c2c2'
          }
        ];
        break;

      case DRILL_LEVELS.CENTER:
        const gestoresCount = data.length;
        const totalCenterIncome = data.reduce((sum, item) => sum + (item.TOTAL_INGRESOS || 0), 0);
        const totalCenterContracts = data.reduce((sum, item) => sum + (item.CONTRATOS_ACTIVOS || 0), 0);
        const avgCenterPerformance = data.reduce((sum, item) => sum + (item.performance_score || 0), 0) / data.length;
        
        stats = [
          { 
            title: 'Gestores', 
            value: gestoresCount, 
            icon: <UserOutlined />,
            color: '#13c2c2'
          },
          { 
            title: 'Performance Centro', 
            value: `${avgCenterPerformance.toFixed(1)}%`, 
            icon: <TrophyFilled />,
            color: avgCenterPerformance >= 80 ? '#52c41a' : '#faad14'
          },
          { 
            title: 'Ingresos Centro', 
            value: `€${totalCenterIncome.toLocaleString()}`, 
            icon: <DollarOutlined />,
            color: '#52c41a'
          },
          { 
            title: 'Total Contratos', 
            value: totalCenterContracts, 
            icon: <FileTextOutlined />,
            color: '#faad14'
          }
        ];
        break;

      case DRILL_LEVELS.MANAGER:
        if (data.length === 1 && data[0].type === 'summary') {
          const gestorData = data[0];
          stats = [
            { 
              title: 'Performance', 
              value: `${gestorData.performance_score?.toFixed(1) || 75}%`, 
              icon: <TrophyFilled />,
              color: gestorData.performance_score >= 80 ? '#52c41a' : '#faad14'
            },
            { 
              title: 'Clientes', 
              value: gestorData.TOTAL_CLIENTES || 0, 
              icon: <TeamOutlined />,
              color: '#13c2c2'
            },
            { 
              title: 'Contratos', 
              value: gestorData.CONTRATOS_ACTIVOS || 0, 
              icon: <FileTextOutlined />,
              color: '#faad14'
            },
            { 
              title: 'Volumen Gestionado', 
              value: `€${(gestorData.VOLUMEN_GESTIONADO || 0).toLocaleString()}`, 
              icon: <DollarOutlined />,
              color: '#52c41a'
            },
            { 
              title: 'Incentivo Estimado', 
              value: `€${(gestorData.incentivo_estimado || 0).toLocaleString()}`, 
              icon: <GiftOutlined />,
              color: '#eb2f96'
            }
          ];
        } else {
          const totalVolume = data.reduce((sum, item) => sum + (item.volumen_gestionado || 0), 0);
          const totalMargin = data.reduce((sum, item) => sum + (item.margen_generado || 0), 0);
          
          stats = [
            { 
              title: 'Clientes', 
              value: data.length, 
              icon: <TeamOutlined />,
              color: '#13c2c2'
            },
            { 
              title: 'Volumen Total', 
              value: `€${totalVolume.toLocaleString()}`, 
              icon: <DollarOutlined />,
              color: '#52c41a'
            },
            { 
              title: 'Margen Total', 
              value: `€${totalMargin.toLocaleString()}`, 
              icon: <RiseOutlined />,
              color: '#52c41a'
            }
          ];
        }
        break;

      case DRILL_LEVELS.CLIENT:
        const totalVolume = data.reduce((sum, item) => sum + (item.volumen_gestionado || 0), 0);
        const totalMargin = data.reduce((sum, item) => sum + (item.margen_generado || 0), 0);
        const avgRentability = data.length > 0 ? data.reduce((sum, item) => sum + (item.rentabilidad || 0), 0) / data.length : 0;
        
        stats = [
          { 
            title: 'Clientes', 
            value: data.length, 
            icon: <TeamOutlined />,
            color: '#13c2c2'
          },
          { 
            title: 'Volumen Total', 
            value: `€${totalVolume.toLocaleString()}`, 
            icon: <DollarOutlined />,
            color: '#52c41a'
          },
          { 
            title: 'Margen Total', 
            value: `€${totalMargin.toLocaleString()}`, 
            icon: <RiseOutlined />,
            color: '#52c41a'
          },
          { 
            title: 'Rentabilidad Media', 
            value: `${avgRentability.toFixed(2)}%`, 
            icon: <PercentageOutlined />,
            color: avgRentability >= 1.5 ? '#52c41a' : '#faad14'
          }
        ];
        break;

      case DRILL_LEVELS.CONTRACT:
        const activeContracts = data.filter(c => c.estado === 'Activo').length;
        const totalContractVolume = data.reduce((sum, item) => sum + (item.volumen || 0), 0);
        const totalMonthlyMargin = data.reduce((sum, item) => sum + (item.margen_mensual || 0), 0);
        
        stats = [
          { 
            title: 'Contratos', 
            value: data.length, 
            icon: <FileTextOutlined />,
            color: '#faad14'
          },
          { 
            title: 'Activos', 
            value: activeContracts, 
            icon: <CheckCircleOutlined />,
            color: '#52c41a'
          },
          { 
            title: 'Volumen Total', 
            value: `€${totalContractVolume.toLocaleString()}`, 
            icon: <DollarOutlined />,
            color: '#52c41a'
          },
          { 
            title: 'Margen Mensual', 
            value: `€${totalMonthlyMargin.toLocaleString()}`, 
            icon: <RiseOutlined />,
            color: '#eb2f96'
          }
        ];
        break;

      case DRILL_LEVELS.TRANSACTION:
        const income = data.filter(t => t.importe > 0).reduce((sum, t) => sum + t.importe, 0);
        const expenses = Math.abs(data.filter(t => t.importe < 0).reduce((sum, t) => sum + t.importe, 0));
        const netResult = income - expenses;
        
        stats = [
          { 
            title: 'Movimientos', 
            value: data.length, 
            icon: <InteractionOutlined />,
            color: '#1890ff'
          },
          { 
            title: 'Ingresos', 
            value: `€${income.toLocaleString()}`, 
            icon: <ArrowUpOutlined />,
            color: '#52c41a'
          },
          { 
            title: 'Gastos', 
            value: `€${expenses.toLocaleString()}`, 
            icon: <ArrowDownOutlined />,
            color: '#ff4d4f'
          },
          { 
            title: 'Resultado Neto', 
            value: `€${netResult.toLocaleString()}`, 
            icon: <TrophyFilled />,
            color: netResult >= 0 ? '#52c41a' : '#ff4d4f'
          }
        ];
        break;

      case DRILL_LEVELS.INCENTIVE:
        if (data.length > 0) {
          const totalIncentive = data.reduce((sum, item) => sum + (item.incentivo_calculado || 0), 0);
          const avgIncentive = totalIncentive / data.length;
          const avgPerformanceInc = data.reduce((sum, item) => sum + (item.performance_score || 0), 0) / data.length;
          
          stats = [
            { 
              title: 'Gestores', 
              value: data.length, 
              icon: <UserOutlined />,
              color: '#13c2c2'
            },
            { 
              title: 'Performance Media', 
              value: `${avgPerformanceInc.toFixed(1)}%`, 
              icon: <TrophyFilled />,
              color: avgPerformanceInc >= 80 ? '#52c41a' : '#faad14'
            },
            { 
              title: 'Incentivo Total', 
              value: `€${totalIncentive.toLocaleString()}`, 
              icon: <GiftOutlined />,
              color: '#eb2f96'
            },
            { 
              title: 'Incentivo Medio', 
              value: `€${avgIncentive.toLocaleString()}`, 
              icon: <MoneyCollectOutlined />,
              color: '#fa8c16'
            }
          ];
        }
        break;

      case DRILL_LEVELS.PRICING:
        if (data.length > 0) {
          const avgDeviation = data.reduce((sum, item) => sum + Math.abs(item.desviacion_porcentual || 0), 0) / data.length;
          const criticalDeviations = data.filter(item => Math.abs(item.desviacion_porcentual || 0) > 15).length;
          const positiveDeviations = data.filter(item => (item.desviacion_porcentual || 0) > 0).length;
          
          stats = [
            { 
              title: 'Productos', 
              value: data.length, 
              icon: <AppstoreOutlined />,
              color: '#1890ff'
            },
            { 
              title: 'Desviación Media', 
              value: `${avgDeviation.toFixed(1)}%`, 
              icon: <PercentageOutlined />,
              color: avgDeviation > 15 ? '#ff4d4f' : avgDeviation > 10 ? '#faad14' : '#52c41a'
            },
            { 
              title: 'Críticas', 
              value: criticalDeviations, 
              icon: <AlertOutlined />,
              color: '#ff4d4f'
            },
            { 
              title: 'Por Encima', 
              value: positiveDeviations, 
              icon: <ArrowUpOutlined />,
              color: '#fa8c16'
            }
          ];
        }
        break;

      default:
        return null;
    }

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {stats.map((stat, index) => (
          <Col key={index} xs={24} sm={12} lg={stats.length > 4 ? Math.floor(24 / stats.length) : 6}>
            <Card size="small" style={{ textAlign: 'center', borderTop: `3px solid ${stat.color}` }}>
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={React.cloneElement(stat.icon, { style: { color: stat.color } })}
                valueStyle={{ 
                  fontSize: compactView ? 16 : 18,
                  color: stat.color,
                  fontWeight: 600
                }}
              />
            </Card>
          </Col>
        ))}
      </Row>
    );
  };

  // Filtrar datos basado en búsqueda y filtros
  const filteredData = useMemo(() => {
    if (!searchText && filterBy === 'all' && sortBy === 'default') return data;

    let filtered = [...data];

    // Aplicar búsqueda
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(item => {
        const searchFields = [
          item.DESC_GESTOR, item.desc_gestor, item.DESC_CENTRO, item.desc_centro,
          item.nombre_cliente, item.NOMBRE_CLIENTE, item.producto_desc, item.PRODUCTO_DESC,
          item.concepto, item.contrato_id, item.CONTRATO_ID, item.movimiento_id, item.MOVIMIENTO_ID,
          item.gestor_nombre, item.segmento_desc, item.segmento
        ];
        return searchFields.some(field => 
          field && field.toString().toLowerCase().includes(searchLower)
        );
      });
    }

    // Aplicar filtros
    if (filterBy !== 'all') {
      switch (filterBy) {
        case 'high_performance':
          filtered = filtered.filter(item => 
            (item.performance_score || item.MARGEN_NETO || 0) >= 80
          );
          break;
        case 'needs_attention':
          filtered = filtered.filter(item => 
            (item.performance_score || item.MARGEN_NETO || 0) < 60
          );
          break;
        case 'active':
          filtered = filtered.filter(item => 
            item.estado === 'Activo' || item.tipo === 'Ingreso' || !item.estado
          );
          break;
        case 'critical':
          filtered = filtered.filter(item => 
            item.severity === 'critical' || Math.abs(item.desviacion_porcentual || 0) > 15
          );
          break;
        default:
          break;
      }
    }

    // Aplicar ordenamiento
    switch (sortBy) {
      case 'performance_desc':
        filtered.sort((a, b) => (b.performance_score || 0) - (a.performance_score || 0));
        break;
      case 'performance_asc':
        filtered.sort((a, b) => (a.performance_score || 0) - (b.performance_score || 0));
        break;
      case 'margin_desc':
        filtered.sort((a, b) => (b.MARGEN_NETO || b.margen_mensual || b.margen_generado || 0) - (a.MARGEN_NETO || a.margen_mensual || a.margen_generado || 0));
        break;
      case 'margin_asc':
        filtered.sort((a, b) => (a.MARGEN_NETO || a.margen_mensual || a.margen_generado || 0) - (b.MARGEN_NETO || b.margen_mensual || b.margen_generado || 0));
        break;
      case 'volume_desc':
        filtered.sort((a, b) => (b.TOTAL_INGRESOS || b.volumen_gestionado || b.volumen || b.importe || 0) - (a.TOTAL_INGRESOS || a.volumen_gestionado || a.volumen || a.importe || 0));
        break;
      case 'date_desc':
        filtered.sort((a, b) => new Date(b.fecha_alta || b.fecha || '1970-01-01') - new Date(a.fecha_alta || a.fecha || '1970-01-01'));
        break;
      case 'incentive_desc':
        filtered.sort((a, b) => (b.incentivo_calculado || 0) - (a.incentivo_calculado || 0));
        break;
      case 'deviation_desc':
        filtered.sort((a, b) => Math.abs(b.desviacion_porcentual || 0) - Math.abs(a.desviacion_porcentual || 0));
        break;
      default:
        break;
    }

    return filtered;
  }, [data, searchText, filterBy, sortBy]);

  // ============================================================================
  // 🎨 RENDERIZADO PRINCIPAL
  // ============================================================================

  return (
    <>
      {contextHolder}
      
      <div style={{ 
        padding: compactView ? 16 : 24,
        background: '#f5f5f5',
        minHeight: '100vh'
      }}>
        
        {/* Breadcrumb Navigation */}
        <Card 
          size="small" 
          style={{ 
            marginBottom: 24,
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}
        >
          <Row justify="space-between" align="middle">
            <Col>
              <Breadcrumb 
                separator={<span style={{ color: '#52c41a' }}>›</span>}
                items={getBreadcrumbItems(currentLevel, context, navigateBack, executiveMode)}
              />
            </Col>
            <Col>
              <Space>
                {lastUpdate && (
                  <Tooltip title={`Última actualización: ${lastUpdate.toLocaleString()}`}>
                    <span style={{ fontSize: 11, color: '#666' }}>
                      <SyncOutlined spin={refreshing} style={{ marginRight: 4 }} />
                      {lastUpdate.toLocaleTimeString()}
                    </span>
                  </Tooltip>
                )}
                
                {availablePeriods.length > 0 && (
                  <Select
                    size="small"
                    value={currentPeriod}
                    onChange={setCurrentPeriod}
                    style={{ width: 100 }}
                  >
                    {availablePeriods.map(period => (
                      <Option key={period} value={period}>{period}</Option>
                    ))}
                  </Select>
                )}

                <Switch 
                  checkedChildren="Auto" 
                  unCheckedChildren="Manual"
                  checked={autoRefresh}
                  onChange={setAutoRefresh}
                  size="small"
                />
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Header Principal */}
        <Card 
          title={
            <Space>
              {LEVEL_CONFIG[currentLevel].icon}
              <span style={{ 
                color: LEVEL_CONFIG[currentLevel].color, 
                fontSize: executiveMode ? 20 : 18, 
                fontWeight: 600 
              }}>
                {renderTitle()}
              </span>
              {intelligentMode && <Badge status="processing" text="IA Activa" />}
              {dashboardType === 'control_gestion' && <Tag color="blue">Control Gestión</Tag>}
              {dashboardType === 'gestor' && <Tag color="green">Vista Gestor</Tag>}
            </Space>
          }
          extra={
            <Space>
              {/* Acciones especializadas */}
              {showIncentives && [DRILL_LEVELS.MANAGER, DRILL_LEVELS.CENTER].includes(currentLevel) && (
                <Button
                  icon={<GiftOutlined />}
                  onClick={handleIncentiveAnalysis}
                  size="small"
                  style={{ borderColor: '#eb2f96', color: '#eb2f96' }}
                >
                  Incentivos
                </Button>
              )}
              
              {showPricing && [DRILL_LEVELS.MANAGER, DRILL_LEVELS.CENTER, DRILL_LEVELS.CONSOLIDATED].includes(currentLevel) && (
                <Button
                  icon={<PercentageOutlined />}
                  onClick={handlePricingAnalysis}
                  size="small"
                  style={{ borderColor: '#fadb14', color: '#fa8c16' }}
                >
                  Precios
                </Button>
              )}

              <Button
                icon={<ReloadOutlined spin={refreshing} />}
                onClick={handleRefresh}
                loading={refreshing}
                size="small"
              >
                Actualizar
              </Button>
              
              <Button
                icon={<DownloadOutlined />}
                onClick={handleExport}
                loading={exportLoading}
                size="small"
                style={{ borderColor: '#52c41a' }}
              >
                Exportar
              </Button>

              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => {
                  const breadcrumbs = getBreadcrumbItems(currentLevel, context);
                  if (breadcrumbs.length > 1) {
                    const previousLevel = breadcrumbs[breadcrumbs.length - 2];
                    navigateBack(previousLevel.key);
                  }
                }}
                disabled={currentLevel === (executiveMode ? DRILL_LEVELS.EXECUTIVE : DRILL_LEVELS.CONSOLIDATED)}
                type={currentLevel === (executiveMode ? DRILL_LEVELS.EXECUTIVE : DRILL_LEVELS.CONSOLIDATED) ? 'text' : 'default'}
              >
                Volver
              </Button>
            </Space>
          }
          style={{ 
            borderRadius: 8,
            boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            marginBottom: 24,
            borderTop: `4px solid ${LEVEL_CONFIG[currentLevel].color}`
          }}
        >
          
          {/* Estadísticas del nivel */}
          {renderLevelStats()}

          {/* Información contextual */}
          {(selectedRecord || Object.keys(context).length > 0) && (
            <Descriptions 
              size="small" 
              column={{ xs: 1, sm: 2, md: 4 }} 
              style={{ marginTop: 16 }}
              bordered
            >
              <Descriptions.Item label="Período">{currentPeriod || 'Actual'}</Descriptions.Item>
              <Descriptions.Item label="Usuario">{userId}</Descriptions.Item>
              <Descriptions.Item label="Nivel Actual">{LEVEL_CONFIG[currentLevel].title}</Descriptions.Item>
              <Descriptions.Item label="Dashboard">{dashboardType === 'control_gestion' ? 'Control Gestión' : 'Gestor'}</Descriptions.Item>
              {context.centroName && (
                <Descriptions.Item label="Centro">{context.centroName}</Descriptions.Item>
              )}
              {context.gestorName && (
                <Descriptions.Item label="Gestor">{context.gestorName}</Descriptions.Item>
              )}
              {context.clienteName && (
                <Descriptions.Item label="Cliente">{context.clienteName}</Descriptions.Item>
              )}
              {context.contratoId && (
                <Descriptions.Item label="Contrato">{context.contratoId}</Descriptions.Item>
              )}
            </Descriptions>
          )}
        </Card>

        {/* Insights inteligentes */}
        {showInsights && insights.length > 0 && (
          <Card 
            title={
              <Space>
                <BulbOutlined style={{ color: '#faad14' }} />
                <span>Insights Inteligentes</span>
                <Badge count={insights.length} color="#faad14" />
              </Space>
            }
            size="small"
            style={{ marginBottom: 24 }}
            extra={
              <Switch 
                size="small"
                checked={showInsights}
                onChange={setShowInsights}
              />
            }
          >
            <Row gutter={[16, 16]}>
              {insights.map((insight, index) => (
                <Col xs={24} sm={12} lg={8} key={index}>
                  <Alert
                    message={
                      <Space>
                        {insight.icon}
                        <span style={{ fontWeight: 600 }}>{insight.title}</span>
                        {insight.trend && (
                          insight.trend === 'up' ? <ArrowUpOutlined style={{ color: '#52c41a' }} /> :
                          <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
                        )}
                      </Space>
                    }
                    description={insight.description}
                    type="info"
                    style={{ 
                      borderLeftColor: insight.color,
                      borderLeftWidth: 4,
                      borderLeftStyle: 'solid',
                      backgroundColor: insight.color + '08'
                    }}
                  />
                </Col>
              ))}
            </Row>
          </Card>
        )}

        {/* Controles y filtros */}
        <Card 
          title={
            <Space>
              <FilterOutlined />
              <span>Controles de Vista</span>
            </Space>
          }
          size="small"
          style={{ marginBottom: 24 }}
          extra={
            <Space>
              <Radio.Group 
                value={viewMode} 
                onChange={(e) => setViewMode(e.target.value)}
                size="small"
              >
                <Radio.Button value={VIEW_MODES.TABLE}>
                  <Space><AppstoreOutlined />Tabla</Space>
                </Radio.Button>
                <Radio.Button value={VIEW_MODES.CARDS}>
                  <Space><ProjectOutlined />Tarjetas</Space>
                </Radio.Button>
                <Radio.Button value={VIEW_MODES.CHART}>
                  <Space><BarChartOutlined />Gráfico</Space>
                </Radio.Button>
              </Radio.Group>
            </Space>
          }
        >
          <Row gutter={[16, 12]}>
            <Col xs={24} sm={12} lg={6}>
              <Search
                placeholder="Buscar en los datos..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: '100%' }}
                allowClear
                size="small"
              />
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Select
                placeholder="Filtrar por"
                value={filterBy}
                onChange={setFilterBy}
                style={{ width: '100%' }}
                size="small"
              >
                <Option value="all">Todos</Option>
                <Option value="high_performance">Alto Rendimiento</Option>
                <Option value="needs_attention">Requiere Atención</Option>
                <Option value="active">Activos</Option>
                {[DRILL_LEVELS.PRICING, DRILL_LEVELS.DEVIATION].includes(currentLevel) && (
                  <Option value="critical">Críticos</Option>
                )}
              </Select>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Select
                placeholder="Ordenar por"
                value={sortBy}
                onChange={setSortBy}
                style={{ width: '100%' }}
                size="small"
              >
                <Option value="default">Por Defecto</Option>
                <Option value="performance_desc">Performance ↓</Option>
                <Option value="performance_asc">Performance ↑</Option>
                <Option value="margin_desc">Margen ↓</Option>
                <Option value="margin_asc">Margen ↑</Option>
                <Option value="volume_desc">Volumen ↓</Option>
                <Option value="date_desc">Fecha ↓</Option>
                {currentLevel === DRILL_LEVELS.INCENTIVE && (
                  <Option value="incentive_desc">Incentivo ↓</Option>
                )}
                {[DRILL_LEVELS.PRICING, DRILL_LEVELS.DEVIATION].includes(currentLevel) && (
                  <Option value="deviation_desc">Desviación ↓</Option>
                )}
              </Select>
            </Col>

            <Col xs={24} sm={12} lg={6}>
              <Space>
                <span style={{ fontSize: 12, color: '#666' }}>
                  {filteredData.length} de {data.length} elementos
                </span>
                {compareMode && (
                  <Switch 
                    size="small"
                    checked={compareMode}
                    onChange={setCompareMode}
                    checkedChildren="Comparar"
                    unCheckedChildren="Normal"
                  />
                )}
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Visualización principal */}
        {loading ? (
          <Card style={{ textAlign: 'center', padding: 60 }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: '#666' }}>
              Cargando datos del nivel {LEVEL_CONFIG[currentLevel].title}...
            </div>
          </Card>
        ) : filteredData.length === 0 ? (
          <Card>
            <Empty 
              description={`No hay datos disponibles para ${LEVEL_CONFIG[currentLevel].title}`}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </Card>
        ) : (
          <>
            {/* Gráfico interactivo */}
            {chartData.length > 0 && [VIEW_MODES.CHART, VIEW_MODES.CARDS].includes(viewMode) && (
              <Card 
                title={`Análisis Visual - ${renderTitle()}`}
                style={{ marginBottom: 24 }}
              >
                <InteractiveCharts
                  data={chartData}
                  availableKpis={['MARGEN_NETO', 'ROE', 'TOTAL_INGRESOS', 'PERFORMANCE', 'INCENTIVO', 'DESVIACION']}
                  title={`Visualización del nivel ${LEVEL_CONFIG[currentLevel].title}`}
                  description={`Análisis visual interactivo de ${LEVEL_CONFIG[currentLevel].description}`}
                  executiveMode={executiveMode}
                  showTrends={intelligentMode}
                  height={400}
                />
              </Card>
            )}

            {/* Tabla principal */}
            {[VIEW_MODES.TABLE, VIEW_MODES.CARDS].includes(viewMode) && (
              <Card
                title={
                  <Space>
                    <span>{`Detalle de ${LEVEL_CONFIG[currentLevel].title} (${filteredData.length})`}</span>
                    {filteredData.length !== data.length && (
                      <Tag color="blue">Filtrados</Tag>
                    )}
                    {LEVEL_CONFIG[currentLevel].specialized && (
                      <Tag color="purple">Especializado</Tag>
                    )}
                  </Space>
                }
                extra={
                  intelligentMode && chatEnabled && (
                    <Button 
                      icon={<RobotOutlined />}
                      onClick={() => handleDeepAnalysis(filteredData[0])}
                      type="primary"
                      ghost
                      size="small"
                    >
                      Análisis IA
                    </Button>
                  )
                }
                style={{
                  borderRadius: 8,
                  boxShadow: '0 4px 16px rgba(0,0,0,0.08)'
                }}
              >
                <Table
                  columns={getTableColumns}
                  dataSource={filteredData}
                  loading={loading || refreshing}
                  pagination={{
                    pageSize: compactView ? 15 : (executiveMode ? 20 : 10),
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => 
                      `${range[0]}-${range[1]} de ${total} elementos`,
                    position: ['topRight', 'bottomRight']
                  }}
                  scroll={{ x: 'max-content' }}
                  size={compactView ? 'small' : 'middle'}
                  rowKey={(record) => 
                    record.key ||
                    record.GESTOR_ID || record.gestor_id ||
                    record.CLIENTE_ID || record.cliente_id || 
                    record.CONTRATO_ID || record.contrato_id || 
                    record.MOVIMIENTO_ID || record.movimiento_id ||
                    record.id || 
                    `drill-${currentLevel}-${Math.random()}`
                  }
                  rowClassName={(record, index) => {
                    let className = index % 2 === 0 ? 'table-row-light' : 'table-row-dark';
                    
                    // Resaltar filas críticas
                    if (record.severity === 'critical' || 
                        Math.abs(record.desviacion_porcentual || 0) > 15 ||
                        (record.performance_score || 0) < 60) {
                      className += ' table-row-critical';
                    }
                    
                    return className;
                  }}
                />
              </Card>
            )}
          </>
        )}

        {/* Modal de Análisis de Incentivos */}
        <Modal
          title={
            <Space>
              <GiftOutlined style={{ color: '#eb2f96' }} />
              <span>Análisis Detallado de Incentivos</span>
            </Space>
          }
          open={incentiveModalOpen}
          onCancel={() => setIncentiveModalOpen(false)}
          width={800}
          footer={null}
        >
          <Tabs defaultActiveKey="1">
            <TabPane tab="Cálculo Actual" key="1">
              {incentiveData.length > 0 ? (
                <Table
                  columns={[
                    {
                      title: 'Gestor',
                      key: 'gestor',
                      render: (_, record) => record.gestor_nombre || record.desc_gestor
                    },
                    {
                      title: 'Performance',
                      dataIndex: 'performance_score',
                      render: (value) => `${value?.toFixed(1)}%`
                    },
                    {
                      title: 'Objetivos',
                      dataIndex: 'cumplimiento_objetivos',
                      render: (value) => `${value?.toFixed(1)}%`
                    },
                    {
                      title: 'Incentivo',
                      dataIndex: 'incentivo_calculado',
                      render: (value) => (
                        <span style={{ fontWeight: 600, color: '#eb2f96' }}>
                          €{value?.toLocaleString()}
                        </span>
                      )
                    }
                  ]}
                  dataSource={incentiveData}
                  size="small"
                  pagination={false}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <Spin />
                  <div style={{ marginTop: 16 }}>Cargando datos de incentivos...</div>
                </div>
              )}
            </TabPane>
            <TabPane tab="Proyecciones" key="2">
              <Alert
                message="Proyecciones de Incentivos"
                description="Análisis predictivo basado en tendencias actuales y objetivos del período."
                type="info"
                style={{ marginBottom: 16 }}
              />
              {/* Aquí iría el contenido de proyecciones */}
            </TabPane>
          </Tabs>
        </Modal>

        {/* Modal de Análisis de Precios */}
        <Modal
          title={
            <Space>
              <PercentageOutlined style={{ color: '#fa8c16' }} />
              <span>Análisis de Precios: Real vs Estándar</span>
            </Space>
          }
          open={pricingModalOpen}
          onCancel={() => setPricingModalOpen(false)}
          width={1000}
          footer={null}
        >
          <Tabs defaultActiveKey="1">
            <TabPane tab="Comparativa General" key="1">
              {pricingData.length > 0 ? (
                <Table
                  columns={[
                    {
                      title: 'Producto',
                      key: 'producto',
                      render: (_, record) => (
                        <div>
                          <div style={{ fontWeight: 600 }}>{record.producto_desc}</div>
                          <div style={{ fontSize: 11, color: '#666' }}>{record.segmento_desc}</div>
                        </div>
                      )
                    },
                    {
                      title: 'Precio Real',
                      dataIndex: 'precio_real',
                      render: (value) => `€${value?.toLocaleString()}`
                    },
                    {
                      title: 'Precio Estándar',
                      dataIndex: 'precio_estandar',
                      render: (value) => `€${value?.toLocaleString()}`
                    },
                    {
                      title: 'Desviación',
                      key: 'deviation',
                      render: (_, record) => {
                        const deviation = record.desviacion_porcentual;
                        const color = Math.abs(deviation) > 15 ? '#ff4d4f' : 
                                     Math.abs(deviation) > 10 ? '#faad14' : '#52c41a';
                        return (
                          <div>
                            <div style={{ color, fontWeight: 600 }}>
                              {deviation > 0 ? '+' : ''}{deviation?.toFixed(1)}%
                            </div>
                            <div style={{ fontSize: 11 }}>
                              €{record.desviacion_absoluta?.toLocaleString()}
                            </div>
                          </div>
                        );
                      }
                    }
                  ]}
                  dataSource={pricingData.slice(0, 20)}
                  size="small"
                  pagination={{ pageSize: 10 }}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: 40 }}>
                  <Spin />
                  <div style={{ marginTop: 16 }}>Cargando datos de precios...</div>
                </div>
              )}
            </TabPane>
            <TabPane tab="Alertas Críticas" key="2">
              <Alert
                message="Precios con Desviación Crítica (>15%)"
                description="Productos que requieren revisión inmediata de pricing."
                type="warning"
                style={{ marginBottom: 16 }}
              />
              {/* Filtrar solo desviaciones críticas */}
              {pricingData.filter(item => Math.abs(item.desviacion_porcentual || 0) > 15).length > 0 ? (
                <Table
                  columns={getTableColumns}
                  dataSource={pricingData.filter(item => Math.abs(item.desviacion_porcentual || 0) > 15)}
                  size="small"
                  pagination={false}
                />
              ) : (
                <Empty description="No hay desviaciones críticas en precios" />
              )}
            </TabPane>
          </Tabs>
        </Modal>

        {/* Drawer de detalles */}
        <Drawer
          title="Información Detallada"
          open={detailsDrawerOpen}
          onClose={() => setDetailsDrawerOpen(false)}
          width={600}
        >
          {selectedRecord && (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Descriptions title="Datos Principales" bordered column={1}>
                {Object.entries(selectedRecord)
                  .filter(([key]) => !['key', 'timestamp', 'type'].includes(key))
                  .map(([key, value]) => (
                  <Descriptions.Item 
                    label={key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').toUpperCase()} 
                    key={key}
                  >
                    {typeof value === 'number' ? 
                      (key.includes('precio') || key.includes('importe') || key.includes('volumen') || key.includes('margen') || key.includes('incentivo') ? 
                        `€${value.toLocaleString()}` : 
                        key.includes('porcentual') || key.includes('performance') || key.includes('cumplimiento') ? 
                          `${value.toFixed(2)}%` : 
                          value.toLocaleString()
                      ) : 
                      String(value || 'N/A')
                    }
                  </Descriptions.Item>
                ))}
              </Descriptions>

              {LEVEL_CONFIG[currentLevel].canDrillDown && (
                <Button 
                  type="primary" 
                  block 
                  onClick={() => {
                    drillDown(selectedRecord);
                    setDetailsDrawerOpen(false);
                  }}
                  style={{
                    backgroundColor: LEVEL_CONFIG[currentLevel].color,
                    borderColor: LEVEL_CONFIG[currentLevel].color
                  }}
                >
                  Drill-Down a {LEVEL_CONFIG[LEVEL_CONFIG[currentLevel].nextLevel]?.title}
                </Button>
              )}

              {intelligentMode && chatEnabled && (
                <Button 
                  block 
                  icon={<RobotOutlined />}
                  onClick={() => {
                    handleDeepAnalysis(selectedRecord);
                    setDetailsDrawerOpen(false);
                  }}
                  style={{ borderColor: '#722ed1', color: '#722ed1' }}
                >
                  Análisis Profundo con IA
                </Button>
              )}
            </Space>
          )}
        </Drawer>

        {/* Drawer de análisis profundo */}
        <Drawer
          title="Análisis Profundo con IA"
          open={analysisDrawerOpen}
          onClose={() => setAnalysisDrawerOpen(false)}
          width={800}
        >
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Select
              placeholder="Tipo de análisis"
              value={selectedAnalysisType}
              onChange={setSelectedAnalysisType}
              style={{ width: '100%' }}
            >
              {Object.entries(ANALYSIS_TYPES).map(([key, value]) => (
                <Option key={value} value={value}>
                  {key.replace('_', ' ')}
                </Option>
              ))}
            </Select>

            {deepAnalysisData && (
              <Card title={`Análisis: ${selectedAnalysisType}`} size="small">
                <Tabs defaultActiveKey="1">
                  <TabPane tab="Resultados" key="1">
                    <div style={{ maxHeight: 400, overflow: 'auto' }}>
                      {deepAnalysisData.data && deepAnalysisData.data.map((item, index) => (
                        <div key={index} style={{ 
                          marginBottom: 16, 
                          padding: 12, 
                          backgroundColor: '#f9f9f9',
                          borderRadius: 4 
                        }}>
                          <pre style={{ 
                            fontSize: 12, 
                            whiteSpace: 'pre-wrap',
                            margin: 0
                          }}>
                            {JSON.stringify(item, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </TabPane>
                  
                  <TabPane tab="Recomendaciones" key="2">
                    {deepAnalysisData.recommendations && deepAnalysisData.recommendations.length > 0 ? (
                      <div>
                        {deepAnalysisData.recommendations.map((rec, index) => (
                          <Alert
                            key={index}
                            message={`Recomendación ${index + 1}`}
                            description={rec}
                            type="info"
                            style={{ marginBottom: 12 }}
                          />
                        ))}
                      </div>
                    ) : (
                      <Empty description="No hay recomendaciones disponibles" />
                    )}
                  </TabPane>
                </Tabs>
              </Card>
            )}

            <Button 
              type="primary" 
              block 
              onClick={() => loadAnalysisData(currentPeriod)}
              loading={loading}
              style={{
                backgroundColor: '#722ed1',
                borderColor: '#722ed1'
              }}
            >
              Ejecutar Análisis IA
            </Button>
          </Space>
        </Drawer>

        {/* Información del sistema */}
        <Card 
          title="Información del Sistema"
          size="small"
          style={{ marginTop: 24 }}
        >
          <Row gutter={[16, 8]}>
            <Col xs={24} sm={12} lg={8}>
              <strong>Ruta de navegación:</strong>
              <div style={{ fontSize: 11, color: '#666' }}>
                {getBreadcrumbItems(currentLevel, context).map(item => 
                  typeof item.title === 'object' ? LEVEL_CONFIG[item.key]?.title || 'Nivel' : item.title
                ).join(' → ')}
              </div>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <strong>Capacidades:</strong>
              <div style={{ fontSize: 11, color: '#666' }}>
                {LEVEL_CONFIG[currentLevel].canDrillDown ? 'Drill-down disponible' : 'Nivel máximo'}
                {intelligentMode && ' • IA habilitada'}
                {chatEnabled && ' • Chat disponible'}
                {showIncentives && ' • Incentivos activos'}
                {showPricing && ' • Pricing activo'}
              </div>
            </Col>
            <Col xs={24} sm={12} lg={8}>
              <strong>Performance:</strong>
              <div style={{ fontSize: 11, color: '#666' }}>
                Cache: {cacheRef.current.size} niveles
                • Historial: {navigationHistory.current.length} pasos
                • Datos: {data.length} elementos
              </div>
            </Col>
          </Row>
        </Card>

      </div>

      {/* Estilos adicionales - Usando CSS-in-JS */}
      <style dangerouslySetInnerHTML={{
        __html: `
          .table-row-light {
            background-color: #fafafa;
          }
          .table-row-dark {
            background-color: white;
          }
          .table-row-critical {
            background-color: #fff2f0 !important;
            border-left: 3px solid #ff4d4f;
          }
          .ant-table-tbody > tr.table-row-critical:hover > td {
            background-color: #fff1f0 !important;
          }
        `
      }} />

    </>
  );
};

DrillDownView.propTypes = {
  initialLevel: PropTypes.oneOf(Object.values(DRILL_LEVELS)),
  initialContext: PropTypes.object,
  dashboardType: PropTypes.oneOf(['gestor', 'control_gestion']),
  onLevelChange: PropTypes.func,
  userId: PropTypes.string,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  executiveMode: PropTypes.bool,
  intelligentMode: PropTypes.bool,
  chatEnabled: PropTypes.bool,
  showIncentives: PropTypes.bool,
  showPricing: PropTypes.bool,
  compactView: PropTypes.bool,
  autoRefresh: PropTypes.bool
};

export default DrillDownView;

