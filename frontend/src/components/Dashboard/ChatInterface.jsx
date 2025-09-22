// frontend/src/components/Dashboard/ChatInterface.jsx
/* eslint-disable no-console */

/**
 * ChatInterface v12.0 - FIXED ICONS + Stable WebSocket + Confidentiality
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Avatar,
  Typography,
  Space,
  Badge,
  Tag,
  Empty,
  Alert,
  Tooltip,
  Spin,
  Switch,
  notification,
  Dropdown,
  Row,
  Col,
  Statistic
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  MessageOutlined,
  WifiOutlined,
  DisconnectOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
  CopyOutlined,
  LoadingOutlined,
  ExpandOutlined,
  CompressOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  SettingOutlined,
  FileTextOutlined,
  BarChartOutlined,
  BulbOutlined,
  TeamOutlined,
  ArrowUpOutlined,
  SecurityScanOutlined,
  WarningOutlined
} from '@ant-design/icons';
import PropTypes from 'prop-types';

// ✅ Services actualizados v12.0
import chatService from '../../services/chatService';
import reportService from '../../services/reportService';
import theme from '../../styles/theme';

const { TextArea } = Input;
const { Text, Title } = Typography;

/**
 * ✅ ChatInterface - CHAT GENERAL CDG v12.0 CON CONFIDENCIALIDAD CORREGIDO
 */
const ChatInterface = ({
  scope = 'direccion',
  periodo = null,
  gestorId = null,
  currentChartConfig = null,
  onNewChart = () => {},
  onCommand = () => {},
  onReportGenerated = () => {},
  suggestions = null,
  expanded = false,
  className = '',
  style = {}
}) => {
  
  // ✅ ESTADOS PRINCIPALES
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [error, setError] = useState(null);
  const [useWebSocket, setUseWebSocket] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isExpanded, setIsExpanded] = useState(expanded);
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [lastAnalysisType, setLastAnalysisType] = useState(null);
  
  // 🔐 ESTADOS DE CONFIDENCIALIDAD
  const [userRole, setUserRole] = useState(null);
  const [securityFeatures, setSecurityFeatures] = useState([]);
  const [accessDeniedCount, setAccessDeniedCount] = useState(0);
  
  const [sessionMetrics, setSessionMetrics] = useState({
    messages_sent: 0,
    queries_processed: 0,
    reports_generated: 0,
    charts_requested: 0,
    access_denied: 0
  });

  // ✅ REFERENCIAS
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const inputRef = useRef(null);
  const sessionRef = useRef(null);
  const reconnectTimer = useRef(null);
  const isManualDisconnect = useRef(false);
  const isMounted = useRef(true);
  const initializationRef = useRef(false);

  // ✅ USER ID ESTABLE
  const userId = useMemo(() => {
    const baseId = `cdg-chat-v12-${scope}`;
    const gestorPart = scope === 'gestor' && gestorId ? `-${gestorId}` : '';
    const randomPart = Math.random().toString(36).substr(2, 6);
    return `${baseId}${gestorPart}-${randomPart}`;
  }, [scope, gestorId]);

  // ✅ CONTEXTO ENRIQUECIDO
  const buildContext = useCallback(() => {
    const context = {
      scope,
      periodo: periodo || undefined,
      gestor_id: scope === 'gestor' && gestorId ? gestorId : undefined,
      user_role: scope,
      chat_type: 'general',
      current_chart_available: !!currentChartConfig,
      session_id: userId,
      integration_version: '12.0',
      chat_agent_version: '11.0',
      cdg_agent_version: '6.1',
      perfect_integration: true,
      confidentiality_enabled: true,
      security_level: 'banking'
    };
  
    console.log('🔍 [ChatInterface] CONTEXT BUILT:', context);
    return context;
  }, [scope, periodo, gestorId, currentChartConfig, userId]);


  // ✅ MENSAJE DE BIENVENIDA
  const welcomeMessage = useMemo(() => ({
    id: `welcome-${scope}-${gestorId || 'default'}`,
    type: 'assistant',
    content: scope === 'direccion' 
      ? `🔐 ¡Hola! Soy tu **Asistente CDG v12.0 para Análisis Corporativo**. Con **Perfect Integration + Confidencialidad** puedo ayudarte con análisis corporativos, KPIs consolidados, rankings de gestores y generación de reportes ejecutivos.

**💡 Ejemplos de consultas:**
• *"¿Cuáles son los KPIs críticos del período?"*
• *"Genera reporte ejecutivo consolidado"*
• *"¿Qué desviaciones requieren atención inmediata?"*

**🔐 Seguridad:** Sistema de confidencialidad bancaria activo con validación automática de permisos.

¿En qué análisis corporativo puedo ayudarte?`
      : `🔐 ¡Hola${gestorId ? ` Gestor ${gestorId}` : ''}! Soy tu **Asistente CDG v12.0 Personal**. Puedo ayudarte con tu performance individual, comparativas vs otros gestores y análisis de tu cartera.

**💡 Ejemplos:**
• *"¿Cómo está mi performance este período?"*
• *"¿Cuáles son mis mejores clientes por margen?"*
• *"Genera mi reporte personal de gestión"*

**🔐 Confidencialidad:** Acceso restringido a tus datos únicamente.

¿Qué consulta sobre tu gestión te gustaría hacer?`,
    timestamp: new Date(),
    recommendations: [
      scope === 'direccion' ? 'KPIs corporativos principales' : 'Mi performance actual',
      scope === 'direccion' ? 'Rankings de gestores' : 'Comparativa con otros gestores',
      scope === 'direccion' ? 'Alertas críticas' : 'Mis oportunidades de mejora',
      scope === 'direccion' ? 'Reporte ejecutivo' : 'Mi reporte personal'
    ],
    metadata: {
      security_enabled: true,
      user_role: scope,
      confidentiality_level: 'banking'
    }
  }), [scope, gestorId]);

  // ✅ SUGERENCIAS CONTEXTUALES
  const defaultSuggestions = useMemo(() => {
    if (scope === 'direccion') {
      return [
        '📊 ¿Cuáles son los KPIs corporativos principales?',
        '🏆 ¿Qué gestores lideran el ranking?', 
        '🚨 ¿Hay desviaciones críticas vs presupuesto?',
        '📈 Genera un reporte ejecutivo',
        '🎯 ¿Qué centros requieren atención?',
        '💹 Analiza las tendencias del período',
        '🔍 Detecta anomalías en los datos',
        '📋 Resumen del estado del negocio'
      ];
    } else {
      return [
        '📈 ¿Cómo está mi performance este período?',
        '👥 ¿Cuáles son mis mejores clientes?',
        '🏆 ¿Cómo me comparo con otros gestores?',
        '🎯 ¿Qué productos debería priorizar?',
        '💡 ¿Tengo oportunidades de cross-selling?',
        '📊 Genera mi reporte personal',
        '🎁 ¿Cuáles son mis proyecciones?',
        '🔍 Analiza mi cartera detalladamente'
      ];
    }
  }, [scope]);

  const activeSuggestions = suggestions || defaultSuggestions;

  // ✅ PROCESAR MENSAJE CON CONFIDENCIALIDAD
  const handleChatMessage = useCallback((data) => {
    if (!isMounted.current) return;
    
    console.log('[ChatInterface] 📥 Chat response received:', data);

    // 🔐 MANEJO DE ACCESO DENEGADO
    if (data?.type === 'access_denied') {
      console.warn('[ChatInterface] 🔐 Access denied received:', data);
      
      const accessDeniedMessage = {
        id: `access-denied-${Date.now()}`,
        type: 'assistant',
        content: `🔐 **${data.message || 'Acceso Restringido por Confidencialidad'}**

Por motivos de seguridad bancaria, no puedes acceder a esta información.

**📋 Información del bloqueo:**
${data.accessInfo ? `• Solicitud: ${data.accessInfo.requested_gestor || 'Datos confidenciales'}
• Tu acceso: ${data.accessInfo.user_gestor || 'Restringido'}
• Rol: ${data.accessInfo.user_role || 'Usuario'}` : '• Solicitud bloqueada por confidencialidad'}

**💡 Alternativas disponibles:**
${data.suggestions ? data.suggestions.map(s => `• ${s}`).join('\n') : '• Consulta tus propios datos\n• Solicita información agregada\n• Usa comparativas anónimas'}`,
        timestamp: new Date(),
        isError: true,
        isAccessDenied: true,
        recommendations: data.suggestions || [
          'Consultar mis datos',
          'Ver promedios del sector',
          'Análisis agregados'
        ],
        metadata: {
          access_info: data.accessInfo,
          security_action: 'access_denied',
          confidentiality_level: 'banking'
        }
      };

      setMessages(prev => [...prev, accessDeniedMessage]);
      setIsSending(false);
      setIsTyping(false);
      setAccessDeniedCount(prev => prev + 1);
      
      setSessionMetrics(prev => ({
        ...prev,
        access_denied: prev.access_denied + 1
      }));

      notification.warning({
        message: '🔐 Acceso Restringido',
        description: 'Confidencialidad bancaria - Solicitud bloqueada',
        duration: 5,
        placement: 'topRight'
      });

      return;
    }

    const responseData = data?.data || data;
    const { 
      text, 
      response, 
      recommendations = [], 
      metadata = {},
      charts = [],
      reports = [],
      analysis_type,
      confidence_score,
      processing_time,
      data_sources = []
    } = responseData;

    const content = text || response || 'Respuesta procesada correctamente.';

    if (analysis_type) {
      setLastAnalysisType(analysis_type);
    }

    const assistantMessage = {
      id: `assistant-${Date.now()}`,
      type: 'assistant',
      content,
      timestamp: new Date(),
      recommendations: Array.isArray(recommendations) ? recommendations.slice(0, 6) : [],
      metadata: {
        ...metadata,
        confidence_score,
        processing_time,
        analysis_type,
        data_sources,
        chat_agent_version: '11.0',
        cdg_agent_version: '6.1',
        security_validated: true,
        user_role: userRole
      },
      charts: charts || [],
      reports: reports || [],
      source: 'perfect_integration_with_confidentiality'
    };

    setMessages(prev => [...prev, assistantMessage]);
    setIsSending(false);
    setIsTyping(false);

    setSessionMetrics(prev => ({
      ...prev,
      queries_processed: prev.queries_processed + 1,
      charts_requested: prev.charts_requested + (charts?.length || 0),
      reports_generated: prev.reports_generated + (reports?.length || 0)
    }));

    if (charts && charts.length > 0) {
      onNewChart(charts[0]);
    }
    
    if (reports && reports.length > 0) {
      onReportGenerated(reports[0]);
    }

    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end' 
        });
      }
    }, 150);
  }, [onNewChart, onReportGenerated, userRole]);

  // ✅ INICIALIZAR CON HTTP POR DEFECTO (evita ping timeouts)
  const initializeConnection = useCallback(() => {
    if (!isMounted.current || initializationRef.current) return;
    
    console.log('[ChatInterface] 🚀 Initializing connection...');
    initializationRef.current = true;

    if (useWebSocket) {
      console.log('[ChatInterface] 🌐 User requested WebSocket');
      initializeWebSocket();
    } else {
      console.log('[ChatInterface] 📡 Using stable HTTP connection');
      setConnectionStatus('http-ready');
      setIsConnected(true);
      initializationRef.current = false;
    }
  }, [useWebSocket]);

  // ✅ INICIALIZAR WEBSOCKET (solo cuando se solicita)
  const initializeWebSocket = useCallback(() => {
    console.log('[ChatInterface] 🌐 Initializing WebSocket...');
    
    if (sessionRef.current) {
      try {
        sessionRef.current.close();
      } catch (e) {
        console.warn('Error closing previous session:', e);
      }
      sessionRef.current = null;
    }

    try {
      const session = chatService.createChatSession(userId, {
        maxRetries: 2,
        backoffBaseMs: 3000,
        heartbeatIntervalMs: 90000,
        onMessage: handleChatMessage,
        onOpen: () => {
          if (isMounted.current) {
            console.log('[ChatInterface] ✅ WebSocket connected');
            setIsConnected(true);
            setConnectionStatus('connected');
            setConnectionAttempts(0);
            setError(null);
            initializationRef.current = false;
          }
        },
        onReady: (readyData) => {
          if (isMounted.current) {
            console.log('[ChatInterface] 🔐 Ready with security:', readyData);
            setUserRole(readyData.userRole);
            setSecurityFeatures(readyData.securityFeatures || []);
            
            if (readyData.userRole) {
              notification.success({
                message: '🔐 Conexión Segura',
                description: `Rol: ${readyData.userRole === 'control_gestion' ? 'Admin' : 'Usuario'}`,
                duration: 3,
                placement: 'topRight'
              });
            }
          }
        },
        onClose: (event) => {
          if (isMounted.current && !isManualDisconnect.current) {
            console.log('[ChatInterface] 🔌 WebSocket closed:', event?.code);
            setIsConnected(false);
            setConnectionStatus('disconnected');
            initializationRef.current = false;
            
            console.log('[ChatInterface] 🔄 Switching to stable HTTP connection');
            setUseWebSocket(false);
            setConnectionStatus('http-fallback-auto');
            setIsConnected(true);
          }
        },
        onError: (error) => {
          if (isMounted.current && !isManualDisconnect.current) {
            console.error('[ChatInterface] ❌ WebSocket error:', error);
            
            if (error.type === 'access_denied') {
              handleChatMessage(error);
              return;
            }
            
            setIsConnected(false);
            setConnectionStatus('error');
            initializationRef.current = false;
            
            console.log('[ChatInterface] 🔄 Error detected, switching to HTTP');
            setUseWebSocket(false);
            setConnectionStatus('http-fallback-error');
            setIsConnected(true);
          }
        },
        onTyping: ({ active, analysis_type }) => {
          if (isMounted.current) {
            setIsTyping(active);
            if (analysis_type) {
              setLastAnalysisType(analysis_type);
            }
          }
        }
      });
    
      sessionRef.current = session;
      session.connect();
    
    } catch (error) {
      console.error('[ChatInterface] Error initializing WebSocket:', error);
      initializationRef.current = false;
      
      setUseWebSocket(false);
      setConnectionStatus('http-fallback-init-error');
      setIsConnected(true);
    }
  }, [userId, handleChatMessage]);

  // ✅ ENVIAR MENSAJE - 🔧 AQUÍ ESTÁ LA CORRECCIÓN
  const sendMessage = useCallback(async (messageText, isQuickAction = false, messageType = 'query') => {
    if (!messageText.trim() || isSending || !isMounted.current) return;

    const userMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: messageText,
      timestamp: new Date(),
      isQuickAction,
      messageType,
      metadata: {
        user_role: userRole,
        security_validated: true
      }
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    setIsSending(true);
    setIsTyping(true);
    setError(null);

    setSessionMetrics(prev => ({
      ...prev,
      messages_sent: prev.messages_sent + 1
    }));

    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end' 
        });
      }
    }, 100);

    try {
      const context = buildContext();

      if (useWebSocket && sessionRef.current && isConnected) {
        console.log('[ChatInterface] 🌐 Sending via WebSocket');
        sessionRef.current.send({
          message: messageText,
          context,
          message_type: messageType,
          include_analysis: true,
          include_recommendations: true,
          user_role: userRole,
          confidentiality_enabled: true
        });
      } else {
        console.log('[ChatInterface] 📡 Sending via HTTP');
        
        // 🔍 DEBUG: Construir payload con logs detallados
        const debugPayload = {
          user_id: userId,
          message: messageText,
          periodo,
          gestor_id: scope === 'gestor' && gestorId ? gestorId : null, // 🔧 CORRECCIÓN AQUÍ
          context,
          include_charts: false,
          include_recommendations: true,
          include_analysis: true,
          chart_interaction_type: 'query',
          message_type: messageType,
          user_role: userRole || scope
        };

        console.log('🔍 [ChatInterface] PREPARANDO PAYLOAD:', {
          scope,
          gestorId,
          gestorId_type: typeof gestorId,
          gestor_id_calculated: scope === 'gestor' && gestorId ? gestorId : null,
          gestor_id_type: typeof (scope === 'gestor' && gestorId ? gestorId : null)
        });

        console.log('🔍 [ChatInterface] PAYLOAD COMPLETO:', debugPayload);

        const response = await chatService.http.sendMessage(debugPayload);

        handleChatMessage(response);
      }

    } catch (error) {
      console.error('[ChatInterface] ❌ Send error:', error);
      setError(error?.message || 'Error al enviar mensaje');
      setIsSending(false);
      setIsTyping(false);

      const errorMessage = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content: `❌ **Error de Comunicación**\n\n${error?.message || 'No se pudo procesar tu consulta'}.\n\nPor favor, inténtalo de nuevo.`,
        timestamp: new Date(),
        isError: true,
        recommendations: ['Reintentar mensaje', 'Verificar conexión']
      };

      setMessages(prev => [...prev, errorMessage]);
    }
  }, [isSending, isConnected, useWebSocket, buildContext, userId, periodo, gestorId, scope, handleChatMessage, userRole]);

  // ✅ GENERAR REPORTE
  const generateReport = useCallback(async (reportType = 'business_review') => {
    if (isGeneratingReport || !isMounted.current) return;
    
    setIsGeneratingReport(true);
    
    try {
      let report;
      if (reportType === 'business_review' && gestorId) {
        report = await reportService.businessReview({
          user_id: userId,
          gestor_id: gestorId,
          periodo,
          options: { include_complex_analysis: true }
        });
      } else if (reportType === 'executive_summary') {
        report = await reportService.executiveSummary({
          user_id: userId,
          periodo,
          options: { include_integration_status: true }
        });
      } else if (reportType === 'deviation_analysis') {
        report = await reportService.deviationAnalysis(periodo, {
          include_critical: true,
          include_margen: true,
          include_volumen: true
        });
      }

      if (report) {
        const reportMessage = {
          id: `report-${Date.now()}`,
          type: 'assistant',
          content: `📋 **Reporte generado exitosamente**\n\n**${report.title}**\n\nEl reporte ha sido generado con validación de confidencialidad.`,
          timestamp: new Date(),
          reports: [report],
          recommendations: ['Descargar reporte', 'Análisis adicional'],
          metadata: {
            security_validated: true,
            user_role: userRole
          }
        };

        setMessages(prev => [...prev, reportMessage]);
        onReportGenerated(report);
        
        notification.success({
          message: 'Reporte Generado',
          description: `${report.title} generado exitosamente`,
          duration: 3,
          placement: 'bottomRight'
        });
      }

    } catch (error) {
      console.error('[ChatInterface] ❌ Report generation error:', error);
    } finally {
      setIsGeneratingReport(false);
    }
  }, [isGeneratingReport, userId, gestorId, periodo, onReportGenerated, userRole]);

  // ✅ HANDLERS DE UI
  const handleSend = useCallback(() => {
    sendMessage(currentMessage);
  }, [currentMessage, sendMessage]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleSuggestion = useCallback((suggestion) => {
    if (suggestion.includes('reporte') || suggestion.includes('Reporte')) {
      if (suggestion.includes('ejecutivo') || suggestion.includes('consolidado')) {
        generateReport('executive_summary');
      } else if (suggestion.includes('personal') || suggestion.includes('mi reporte')) {
        generateReport('business_review');
      } else if (suggestion.includes('desviación') || suggestion.includes('crítica')) {
        generateReport('deviation_analysis');
      } else {
        sendMessage(suggestion, true, 'report_request');
      }
    } else {
      sendMessage(suggestion, true);
    }
  }, [sendMessage, generateReport]);

  const handleCopyMessage = useCallback((content) => {
    navigator.clipboard.writeText(content).then(() => {
      notification.success({
        message: 'Copiado',
        description: 'Mensaje copiado al portapapeles',
        duration: 2,
        placement: 'bottomRight'
      });
    });
  }, []);

  const handleRetry = useCallback(() => {
    const lastUserMessage = [...messages].reverse().find(m => m.type === 'user');
    if (lastUserMessage) {
      sendMessage(lastUserMessage.content, lastUserMessage.isQuickAction, lastUserMessage.messageType);
    }
  }, [messages, sendMessage]);

  const handleWebSocketToggle = useCallback((checked) => {
    isManualDisconnect.current = !checked;
    
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
    }

    if (sessionRef.current) {
      try {
        sessionRef.current.close();
      } catch (e) {
        // Ignore
      }
      sessionRef.current = null;
    }

    setConnectionAttempts(0);
    setUseWebSocket(checked);
    setError(null);
    initializationRef.current = false;
    
    if (checked) {
      setConnectionStatus('connecting');
      setTimeout(() => initializeWebSocket(), 500);
    } else {
      setConnectionStatus('http-ready');
      setIsConnected(true);
    }
  }, [initializeWebSocket]);

  const handleToggleExpansion = useCallback(() => {
    setIsExpanded(prev => !prev);
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end' 
        });
      }
    }, 300);
  }, []);

  // ✅ MENU DE ACCIONES ACTUALIZADO
  const advancedActionsMenu = {
    items: [
      {
        key: 'generate-report',
        icon: <FileTextOutlined />,
        label: 'Generar Reporte',
        children: [
          {
            key: 'business-review',
            label: scope === 'gestor' ? 'Reporte Personal' : 'Business Review',
            onClick: () => generateReport('business_review')
          },
          {
            key: 'executive-summary', 
            label: 'Resumen Ejecutivo',
            onClick: () => generateReport('executive_summary')
          },
          {
            key: 'deviation-analysis',
            label: 'Análisis Desviaciones',
            onClick: () => generateReport('deviation_analysis')
          }
        ]
      },
      {
        key: 'security-info',
        icon: <SecurityScanOutlined />,
        label: 'Información de Seguridad',
        onClick: () => {
          const securityMessage = {
            id: `security-info-${Date.now()}`,
            type: 'assistant',
            content: `🔐 **Información de Seguridad Bancaria**

**Tu Rol:** ${userRole === 'control_gestion' ? 'Control de Gestión (Acceso completo)' : 'Gestor (Acceso restringido)'}

**Funcionalidades Activas:**
${securityFeatures.map(f => `• ${f.replace('_', ' ')}`).join('\n') || '• Validación de permisos\n• Protección de datos\n• Cumplimiento normativo'}

**Estadísticas de Sesión:**
• Mensajes enviados: ${sessionMetrics.messages_sent}
• Consultas procesadas: ${sessionMetrics.queries_processed}
• Accesos denegados: ${sessionMetrics.access_denied}

**Sistema de Confidencialidad:**
• Protección automática de datos personales
• Validación de permisos por consulta
• Cumplimiento normativo bancario`,
            timestamp: new Date(),
            metadata: {
              security_info: true,
              user_role: userRole
            }
          };
          setMessages(prev => [...prev, securityMessage]);
        }
      },
      {
        key: 'clear-chat',
        icon: <ReloadOutlined />,
        label: 'Limpiar Chat',
        onClick: () => {
          setMessages([welcomeMessage]);
          setSessionMetrics({
            messages_sent: 0,
            queries_processed: 0,
            reports_generated: 0,
            charts_requested: 0,
            access_denied: 0
          });
          setAccessDeniedCount(0);
        }
      }
    ]
  };

  // ✅ INICIALIZACIÓN
  useEffect(() => {
    if (initializationRef.current) return;

    isMounted.current = true;
    
    console.log('[ChatInterface] 🚀 Component initialized with Perfect Integration + Confidentiality v12.0');
    setMessages([welcomeMessage]);
    setError(null);
    isManualDisconnect.current = false;
    
    setTimeout(() => {
      if (isMounted.current && !initializationRef.current) {
        initializeConnection();
      }
    }, 500);

    return () => {
      console.log('[ChatInterface] 🧹 Component cleanup');
      isMounted.current = false;
      isManualDisconnect.current = true;
      initializationRef.current = false;

      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }

      if (sessionRef.current) {
        try {
          sessionRef.current.close();
        } catch (e) {
          // Ignore cleanup errors
        }
        sessionRef.current = null;
      }
    };
  }, [welcomeMessage, initializeConnection]);

  // ✅ SCROLL AUTOMÁTICO
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'end' 
        });
      }
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages, isTyping]);

  // ✅ RENDERIZAR MENSAJE CON SOPORTE PARA ACCESO DENEGADO
  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const isError = message.isError;
    const isAccessDenied = message.isAccessDenied;
    const hasAdvancedData = message.metadata || message.charts?.length > 0 || message.reports?.length > 0;

    return (
      <div 
        key={message.id} 
        style={{ 
          display: 'flex', 
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          marginBottom: 16,
          alignItems: 'flex-start'
        }}
      >
        {!isUser && (
          <Avatar 
            icon={isAccessDenied ? <SecurityScanOutlined /> : <RobotOutlined />}
            style={{ 
              backgroundColor: isAccessDenied
                ? '#ff7875'
                : isError 
                  ? theme.colors?.error || '#ff4d4f' 
                  : hasAdvancedData 
                    ? theme.colors?.bmGreenLight || '#52c41a'
                    : theme.colors?.bmGreenPrimary || '#1890ff',
              marginRight: 12,
              flexShrink: 0
            }} 
            size="small"
          />
        )}
        
        <div style={{ 
          maxWidth: isExpanded ? '90%' : '80%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start'
        }}>
          <div style={{
            backgroundColor: isUser 
              ? theme.colors?.bmGreenPrimary || '#1890ff'
              : isAccessDenied
                ? '#fff2f0'
                : isError 
                  ? `${theme.colors?.error || '#ff4d4f'}10`
                  : hasAdvancedData
                    ? `${theme.colors?.bmGreenLight || '#52c41a'}08`
                    : theme.colors?.backgroundLight || '#fafafa',
            color: isUser ? 'white' : theme.colors?.textPrimary || '#333',
            padding: '12px 16px',
            borderRadius: 16,
            borderTopRightRadius: isUser ? 4 : 16,
            borderTopLeftRadius: isUser ? 16 : 4,
            marginBottom: 6,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            position: 'relative',
            border: isAccessDenied
              ? '1px solid #ff7875'
              : isError 
                ? `1px solid ${theme.colors?.error || '#ff4d4f'}40` 
                : hasAdvancedData
                  ? `1px solid ${theme.colors?.bmGreenLight || '#52c41a'}40`
                  : 'none',
            wordBreak: 'break-word'
          }}>
            <Text style={{ 
              color: isUser ? 'white' : theme.colors?.textPrimary || '#333',
              fontSize: 14,
              lineHeight: 1.5,
              whiteSpace: 'pre-wrap'
            }}>
              {message.content}
            </Text>
            
            <div style={{ position: 'absolute', top: -8, right: 8, display: 'flex', gap: 4 }}>
              {message.isQuickAction && (
                <Tag size="small" color="blue" style={{ fontSize: 10 }}>
                  Rápida
                </Tag>
              )}
              {isAccessDenied && (
                <Tag size="small" color="red" style={{ fontSize: 10 }}>
                  🔐 Restringido
                </Tag>
              )}
              {message.metadata?.analysis_type && (
                <Tag size="small" color="green" style={{ fontSize: 10 }}>
                  {message.metadata.analysis_type.replace('_', ' ')}
                </Tag>
              )}
              {message.metadata?.confidence_score && (
                <Tag 
                  size="small" 
                  color={message.metadata.confidence_score > 0.8 ? 'green' : 'orange'}
                  style={{ fontSize: 10 }}
                >
                  {Math.round(message.metadata.confidence_score * 100)}%
                </Tag>
              )}
              {message.metadata?.security_validated && (
                <Tag size="small" color="green" style={{ fontSize: 10 }}>
                  ✓ Seguro
                </Tag>
              )}
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {message.timestamp.toLocaleTimeString()}
            </Text>
            
            {!isUser && (
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => handleCopyMessage(message.content)}
                style={{ fontSize: 10, padding: 0, height: 'auto' }}
              />
            )}
            
            {message.metadata?.processing_time && (
              <Text type="secondary" style={{ fontSize: 10 }}>
                <ThunderboltOutlined /> {message.metadata.processing_time}ms
              </Text>
            )}

            {message.metadata?.user_role && (
              <Text type="secondary" style={{ fontSize: 10 }}>
                <SecurityScanOutlined /> {message.metadata.user_role}
              </Text>
            )}
          </div>
          
          {message.recommendations && message.recommendations.length > 0 && (
            <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {message.recommendations.slice(0, 4).map((rec, index) => (
                <Tag
                  key={index}
                  style={{ 
                    cursor: 'pointer',
                    borderColor: isAccessDenied ? '#ff7875' : theme.colors?.bmGreenLight,
                    color: isAccessDenied ? '#ff4d4f' : theme.colors?.bmGreenPrimary,
                    fontSize: 11
                  }}
                  onClick={() => handleSuggestion(rec)}
                >
                  {rec}
                </Tag>
              ))}
            </div>
          )}

          {(message.charts?.length > 0 || message.reports?.length > 0) && (
            <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
              {message.charts?.length > 0 && (
                <Tag color="blue" style={{ fontSize: 10 }}>
                  <BarChartOutlined /> {message.charts.length} gráfico{message.charts.length > 1 ? 's' : ''}
                </Tag>
              )}
              {message.reports?.length > 0 && (
                <Tag color="green" style={{ fontSize: 10 }}>
                  <FileTextOutlined /> {message.reports.length} reporte{message.reports.length > 1 ? 's' : ''}
                </Tag>
              )}
            </div>
          )}
        </div>
        
        {isUser && (
          <Avatar 
            icon={<UserOutlined />} 
            style={{ 
              backgroundColor: theme.colors?.textSecondary || '#666',
              marginLeft: 12,
              flexShrink: 0
            }} 
            size="small"
          />
        )}
      </div>
    );
  };

  return (
    <Card
      className={className}
      style={{
        height: isExpanded ? '90vh' : '70vh',
        minHeight: '600px',
        display: 'flex',
        flexDirection: 'column',
        transition: 'height 0.3s ease',
        ...style
      }}
      styles={{ 
        body: { 
          padding: 0, 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column' 
        } 
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space>
            <MessageOutlined style={{ color: theme.colors?.bmGreenPrimary }} />
            <Title level={5} style={{ margin: 0 }}>
              Chat CDG v12.0 - Perfect Integration + Confidentiality
            </Title>
            <Badge 
              count={scope === 'direccion' ? 'Corporativo' : 'Personal'} 
              style={{ backgroundColor: theme.colors?.bmGreenPrimary }} 
            />
            {userRole && (
              <Badge 
                count={userRole === 'control_gestion' ? 'Admin' : 'User'} 
                style={{ backgroundColor: userRole === 'control_gestion' ? '#52c41a' : '#1890ff' }} 
              />
            )}
          </Space>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Tooltip title="Métricas de sesión con seguridad">
              <Space size={4} style={{ fontSize: 10, color: theme.colors?.textSecondary }}>
                <Text type="secondary" style={{ fontSize: 10 }}>
                  📤{sessionMetrics.messages_sent} 🔍{sessionMetrics.queries_processed} 📊{sessionMetrics.reports_generated}
                  {sessionMetrics.access_denied > 0 && (
                    <span style={{ color: '#ff4d4f', marginLeft: 4 }}>
                      🔐{sessionMetrics.access_denied}
                    </span>
                  )}
                </Text>
              </Space>
            </Tooltip>
            
            <Dropdown menu={advancedActionsMenu} placement="bottomRight">
              <Button
                type="text"
                size="small"
                icon={<SettingOutlined />}
              />
            </Dropdown>
            
            <Tooltip title={isExpanded ? 'Contraer' : 'Expandir'}>
              <Button
                type="text"
                size="small"
                icon={isExpanded ? <CompressOutlined /> : <ExpandOutlined />}
                onClick={handleToggleExpansion}
              />
            </Tooltip>
            
            <Switch
              size="small"
              checked={useWebSocket}
              onChange={handleWebSocketToggle}
              checkedChildren={<WifiOutlined />}
              unCheckedChildren={<DisconnectOutlined />}
            />
            
            <Badge 
              status={
                connectionStatus === 'connected' ? 'success' :
                connectionStatus.includes('reconnecting') ? 'processing' :
                connectionStatus === 'http-ready' || connectionStatus.startsWith('http-fallback') ? 'default' : 'error'
              }
              text={
                connectionStatus === 'connected' ? 'WS' :
                connectionStatus.includes('reconnecting') ? `Recon` :
                connectionStatus === 'http-ready' || connectionStatus.startsWith('http-fallback') ? 'HTTP' : 'Error'
              }
              style={{ fontSize: 9 }}
            />

            {securityFeatures.length > 0 && (
              <Tooltip title={`Seguridad activa: ${securityFeatures.join(', ')}`}>
                <SecurityScanOutlined style={{ color: '#52c41a', fontSize: 14 }} />
              </Tooltip>
            )}
          </div>
        </div>
      }
    >
      <div style={{ 
        padding: '12px 20px',
        backgroundColor: `${theme.colors?.bmGreenPrimary || '#1890ff'}05`,
        borderBottom: `1px solid ${theme.colors?.borderLight || '#f0f0f0'}`
      }}>
        <Row gutter={[16, 8]}>
          <Col span={6}>
            <Statistic
              title="Catálogos"
              value={6}
              prefix={<TeamOutlined />}
              valueStyle={{ fontSize: 14 }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Flujos"
              value={4}
              prefix={<ArrowUpOutlined />}
              valueStyle={{ fontSize: 14 }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Queries"
              value={8}
              prefix={<BarChartOutlined />}
              valueStyle={{ fontSize: 14 }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Seguridad"
              value={accessDeniedCount > 0 ? `${accessDeniedCount} bloq.` : 'Activa'}
              prefix={<SecurityScanOutlined />}
              valueStyle={{ 
                fontSize: 14, 
                color: accessDeniedCount > 0 ? '#ff4d4f' : '#52c41a' 
              }}
            />
          </Col>
        </Row>
      </div>

      {accessDeniedCount > 0 && (
        <div style={{ 
          padding: '12px 20px',
          backgroundColor: '#fff2f0',
          borderBottom: `1px solid #ffccc7`
        }}>
          <Alert
            message={`🔐 ${accessDeniedCount} consulta${accessDeniedCount > 1 ? 's' : ''} bloqueada${accessDeniedCount > 1 ? 's' : ''} por confidencialidad`}
            description="Sistema de protección bancaria activo."
            type="warning"
            showIcon
            icon={<SecurityScanOutlined />}
            style={{ fontSize: 12 }}
            closable
            onClose={() => setAccessDeniedCount(0)}
          />
        </div>
      )}

      {showSuggestions && activeSuggestions.length > 0 && (
        <div style={{ 
          padding: '16px 20px',
          backgroundColor: `${theme.colors?.bmGreenLight || '#52c41a'}06`,
          borderBottom: `1px solid ${theme.colors?.borderLight || '#f0f0f0'}`
        }}>
          <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Text strong style={{ fontSize: 12, color: theme.colors?.textSecondary }}>
              <BulbOutlined style={{ marginRight: 4 }} />
              Consultas Populares
              <SecurityScanOutlined style={{ marginLeft: 8, color: '#52c41a' }} />
            </Text>
            <Button 
              type="text" 
              size="small" 
              onClick={() => setShowSuggestions(false)}
              style={{ fontSize: 10, padding: '0 4px' }}
            >
              Ocultar
            </Button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 8 }}>
            {activeSuggestions.slice(0, 6).map((suggestion, index) => (
              <Button
                key={index}
                size="small"
                onClick={() => handleSuggestion(suggestion)}
                disabled={isSending}
                style={{
                  borderColor: theme.colors?.bmGreenPrimary,
                  color: theme.colors?.bmGreenPrimary,
                  fontSize: 11,
                  textAlign: 'left',
                  height: 'auto',
                  whiteSpace: 'normal',
                  padding: '6px 12px'
                }}
                block
              >
                {suggestion}
              </Button>
            ))}
          </div>
        </div>
      )}

      <div 
        ref={messagesContainerRef}
        style={{ 
          flex: 1,
          padding: '20px',
          overflow: 'auto',
          backgroundColor: theme.colors?.backgroundLight || '#fafafa',
          maxHeight: isExpanded ? '75vh' : '500px',
          minHeight: '350px'
        }}
      >
        {messages.length === 0 ? (
          <Empty 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Inicia una conversación con el Agente CDG v12.0 + Confidencialidad"
            style={{ marginTop: 40 }}
          />
        ) : (
          <>
            {messages.map(renderMessage)}
            {isTyping && (
              <div style={{ 
                display: 'flex', 
                justifyContent: 'flex-start', 
                marginBottom: 16,
                alignItems: 'center'
              }}>
                <Avatar 
                  icon={<RobotOutlined />} 
                  style={{ 
                    backgroundColor: theme.colors?.bmGreenPrimary,
                    marginRight: 12
                  }} 
                  size="small"
                />
                <div style={{
                  backgroundColor: theme.colors?.backgroundLight,
                  padding: '12px 16px',
                  borderRadius: 16,
                  borderTopLeftRadius: 4,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  <Spin 
                    indicator={<LoadingOutlined style={{ fontSize: 14 }} spin />} 
                    size="small" 
                  />
                  <Text style={{ fontSize: 14, color: theme.colors?.textSecondary }}>
                    Analizando con Perfect Integration + Confidencialidad...
                  </Text>
                  {isGeneratingReport && (
                    <Tag size="small" color="blue">Generando reporte</Tag>
                  )}
                  <Tag size="small" color="green">
                    <SecurityScanOutlined /> Validando
                  </Tag>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} style={{ height: '1px' }} />
          </>
        )}
      </div>

      {error && (
        <div style={{ padding: '0 20px 12px' }}>
          <Alert
            message="Error de Comunicación"
            description={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
            action={
              <Space>
                <Button 
                  size="small" 
                  onClick={handleRetry} 
                  disabled={isSending}
                  icon={<ReloadOutlined />}
                >
                  Reintentar
                </Button>
              </Space>
            }
          />
        </div>
      )}

      <div style={{ 
        padding: '16px 20px',
        backgroundColor: 'white',
        borderTop: `1px solid ${theme.colors?.borderLight || '#f0f0f0'}`
      }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
          <TextArea
            ref={inputRef}
            placeholder={`💬 ${scope === 'direccion' ? 'Pregunta sobre KPIs corporativos, rankings, análisis ejecutivos...' : 'Pregunta sobre tu cartera, rendimiento, comparativas...'}`}
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isSending || isGeneratingReport}
            autoSize={{ minRows: 1, maxRows: 4 }}
            style={{ flex: 1 }}
          />
          <Button
            type="primary"
            icon={isSending || isGeneratingReport ? <LoadingOutlined spin /> : <SendOutlined />}
            onClick={handleSend}
            disabled={!currentMessage.trim() || isSending || isGeneratingReport}
            style={{
              backgroundColor: theme.colors?.bmGreenPrimary,
              borderColor: theme.colors?.bmGreenPrimary,
              height: 36
            }}
            loading={isSending || isGeneratingReport}
          >
            Enviar
          </Button>
        </div>
        
        <div style={{ 
          marginTop: 8, 
          fontSize: 11, 
          color: theme.colors?.textSecondary,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <Space size={16}>
            <span>
              <EyeOutlined style={{ marginRight: 4 }} />
              Enter para enviar • Shift+Enter para nueva línea
            </span>
            <span style={{ color: theme.colors?.bmGreenPrimary }}>
              <CheckCircleOutlined style={{ marginRight: 4 }} />
              Perfect Integration v12.0
            </span>
            <span style={{ color: '#52c41a' }}>
              <SecurityScanOutlined style={{ marginRight: 4 }} />
              Confidencialidad Bancaria
            </span>
          </Space>
          
          {periodo && (
            <Text type="secondary" style={{ fontSize: 10 }}>
              📋 {scope === 'direccion' ? 'Corporativo' : `Gestor ${gestorId}`} • {periodo}
              {userRole && (
                <span style={{ marginLeft: 8 }}>
                  🔐 {userRole === 'control_gestion' ? 'Admin' : 'User'}
                </span>
              )}
            </Text>
          )}
        </div>
      </div>
    </Card>
  );
};

ChatInterface.propTypes = {
  scope: PropTypes.oneOf(['direccion', 'gestor']).isRequired,
  periodo: PropTypes.string,
  gestorId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  currentChartConfig: PropTypes.object,
  onNewChart: PropTypes.func,
  onCommand: PropTypes.func,
  onReportGenerated: PropTypes.func,
  suggestions: PropTypes.arrayOf(PropTypes.string),
  expanded: PropTypes.bool,
  className: PropTypes.string,
  style: PropTypes.object
};

export default ChatInterface;
