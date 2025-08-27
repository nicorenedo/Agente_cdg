// src/components/Chat/ConversationalPivot.jsx
// Componente para modificación interactiva del dashboard - CORREGIDO para backend Banca March

import React, { useState, useEffect, useCallback } from 'react';
import { Input, Button, Typography, List, message, Space, Card } from 'antd';
import { SendOutlined, SyncOutlined, BarChartOutlined, CheckCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import InteractiveCharts from '../Dashboard/InteractiveCharts';
import theme from '../../styles/theme';

const { Title, Text } = Typography;
const { TextArea } = Input;

const ConversationalPivot = ({ 
  userId, 
  gestorId, 
  periodo, 
  initialData = [], 
  initialKpis = ['ROE', 'MARGEN_NETO', 'TOTAL_INGRESOS'], // ✅ CORREGIDO: KPIs en mayúsculas
  onChartUpdate
}) => {
  // Estados principales
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [chartConfig, setChartConfig] = useState({
    chartType: 'bar',
    selectedKpi: initialKpis[0] || 'ROE',
    data: initialData,
    availableKpis: initialKpis
  });

  // Función para añadir mensajes al chat
  const addMessage = useCallback((sender, text, charts = [], recommendations = []) => {
    setMessages(prev => [...prev, { 
      id: Date.now() + Math.random(),
      sender, 
      text, 
      charts, 
      recommendations,
      timestamp: new Date()
    }]);
  }, []);

  // Mensaje de bienvenida al montar
  useEffect(() => {
    addMessage('agent', 
      `Hola! Puedes pedirme cambios en la visualización usando lenguaje natural:

• "Cambia a gráfico circular"
• "Muestra el ROE en barras" 
• "Visualiza margen neto como líneas"
• "Compara total de ingresos"
• "Añade beneficio neto al gráfico"

¿Qué modificación deseas hacer?`
    );
  }, [addMessage]);

  // ✅ CORREGIDO: Función para interpretar comandos con KPIs actualizados
  const parseChartCommands = (text) => {
    const textLower = text.toLowerCase();
    let updates = {};

    // Detectar cambios de tipo de gráfico
    if (textLower.includes('circular') || textLower.includes('pastel') || textLower.includes('pie') || textLower.includes('torta')) {
      updates.chartType = 'pie';
    } else if (textLower.includes('línea') || textLower.includes('linea') || textLower.includes('evolución') || textLower.includes('tendencia')) {
      updates.chartType = 'line';
    } else if (textLower.includes('barra') || textLower.includes('barras') || textLower.includes('columna') || textLower.includes('columnas')) {
      updates.chartType = 'bar';
    } else if (textLower.includes('área') || textLower.includes('area') || textLower.includes('relleno')) {
      updates.chartType = 'area';
    }

    // ✅ CORREGIDO: Detectar cambios de KPI con mapeo actualizado para backend
    const kpiMappings = {
      'ROE': ['roe', 'rentabilidad', 'return on equity', 'retorno', 'return'],
      'MARGEN_NETO': ['margen', 'margen neto', 'margen_neto', 'beneficio', 'profit', 'margin'],
      'TOTAL_INGRESOS': ['ingresos', 'facturación', 'total ingresos', 'revenue', 'ventas', 'sales'],
      'TOTAL_GASTOS': ['gastos', 'costes', 'total gastos', 'costos', 'expenses', 'costs'],
      'BENEFICIO_NETO': ['beneficio neto', 'beneficio', 'resultado', 'ganancia', 'profit net']
    };

    for (const [kpi, keywords] of Object.entries(kpiMappings)) {
      if (keywords.some(keyword => textLower.includes(keyword))) {
        if (chartConfig.availableKpis.includes(kpi)) {
          updates.selectedKpi = kpi;
          break;
        }
      }
    }

    return updates;
  };

  // ✅ CORREGIDO: Verificar conexión con servicio de chat actualizado
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const isAvailable = await chatService.isServiceAvailable();
        setIsConnected(isAvailable);
      } catch (error) {
        console.warn('Chat service not available:', error);
        setIsConnected(false);
      }
    };

    if (userId) {
      checkConnection();
    }
  }, [userId]);

  // ✅ CORREGIDO: Enviar mensaje al chat con estructura actualizada
  const sendMessage = async () => {
    if (!inputValue.trim()) {
      message.warning('Por favor, escribe un comando o pregunta');
      return;
    }

    const userMessage = inputValue.trim();
    addMessage('user', userMessage);
    setInputValue('');
    setIsSending(true);

    try {
      // Interpretar comandos localmente primero
      const chartUpdates = parseChartCommands(userMessage);
      
      // Enviar al servicio de chat para procesamiento avanzado
      const response = await chatService.sendMessage(userId, userMessage, {
        gestorId,
        periodo,
        includeCharts: true,
        includeRecommendations: true,
        context: { 
          currentChart: chartConfig,
          conversationalPivot: true,
          requestedUpdates: chartUpdates
        }
      });

      if (response.error) {
        addMessage('agent', `Error procesando el comando: ${response.error}`, [], [
          'Intenta usar comandos más específicos',
          'Verifica que el KPI solicitado esté disponible',
          'Revisa la conexión con el sistema'
        ]);
      } else {
        // Añadir respuesta del agente
        addMessage('agent', 
          response.response || 'He procesado tu solicitud de cambio en la visualización.', 
          response.charts || [], 
          response.recommendations || []
        );

        // Aplicar actualizaciones de gráfico
        if (Object.keys(chartUpdates).length > 0) {
          const newConfig = { ...chartConfig, ...chartUpdates };
          setChartConfig(newConfig);
          
          // Notificar al componente padre si existe
          if (onChartUpdate) {
            onChartUpdate(newConfig);
          }
          
          const updateMessages = [];
          if (chartUpdates.chartType) {
            updateMessages.push(`Tipo: ${chartUpdates.chartType.toUpperCase()}`);
          }
          if (chartUpdates.selectedKpi) {
            updateMessages.push(`KPI: ${chartUpdates.selectedKpi.replace('_', ' ')}`);
          }
          
          if (updateMessages.length > 0) {
            message.success(`Gráfico actualizado - ${updateMessages.join(' | ')}`);
          }
        }

        // Procesar gráficos adicionales del agente si los hay
        if (response.charts && response.charts.length > 0) {
          addMessage('agent', 'He generado visualizaciones adicionales basadas en tu solicitud:', response.charts);
        }
      }

    } catch (error) {
      console.error('Error en ConversationalPivot:', error);
      addMessage('agent', `Error de comunicación: ${error.message}`, [], [
        'Verifica tu conexión a internet',
        'El servicio de chat puede estar temporalmente no disponible',
        'Intenta recargar la página si el problema persiste'
      ]);
      message.error('Error al procesar el comando');
      setIsConnected(false);
    } finally {
      setIsSending(false);
    }
  };

  // Manejar Enter para enviar
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSending && isConnected) {
        sendMessage();
      }
    }
  };

  // Función para sugerir comandos
  const suggestCommand = (command) => {
    setInputValue(command);
  };

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: theme.colors.background,
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      border: `1px solid ${theme.colors.border}`,
      padding: theme.spacing.md
    }}>
      
      {/* Header */}
      <div style={{ marginBottom: theme.spacing.md }}>
        <Title level={4} style={{ 
          color: theme.colors.bmGreenDark, 
          margin: 0,
          display: 'flex',
          alignItems: 'center',
          gap: theme.spacing.sm
        }}>
          <BarChartOutlined />
          Control Conversacional de Dashboard
          {!isConnected && (
            <span style={{ 
              fontSize: 12, 
              color: theme.colors.error, 
              fontWeight: 400 
            }}>
              (Sin conexión)
            </span>
          )}
        </Title>
        <Text style={{ color: theme.colors.textSecondary }}>
          Modifica visualizaciones usando lenguaje natural
        </Text>
      </div>

      {/* ✅ CORREGIDO: Comandos sugeridos con KPIs actualizados */}
      <Card size="small" style={{ marginBottom: theme.spacing.sm }}>
        <Text strong style={{ fontSize: 12, color: theme.colors.textSecondary }}>
          Comandos rápidos:
        </Text>
        <div style={{ marginTop: 4, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {[
            'Cambia a gráfico circular',
            'Muestra ROE en barras',
            'Visualiza margen neto'
          ].map(cmd => (
            <Button 
              key={cmd}
              size="small" 
              type="text"
              onClick={() => suggestCommand(cmd)}
              style={{ 
                fontSize: 11, 
                height: 'auto', 
                padding: '2px 6px',
                border: `1px solid ${theme.colors.border}`
              }}
            >
              {cmd}
            </Button>
          ))}
        </div>
      </Card>

      {/* Área de chat */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto',
        marginBottom: theme.spacing.md,
        maxHeight: '250px',
        border: `1px solid ${theme.colors.border}`,
        borderRadius: 6,
        backgroundColor: theme.colors.backgroundLight
      }}>
        <List
          dataSource={messages}
          renderItem={(item) => (
            <List.Item style={{ 
              justifyContent: item.sender === 'user' ? 'flex-end' : 'flex-start',
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              border: 'none'
            }}>
              <div style={{
                maxWidth: '85%',
                padding: theme.spacing.sm,
                borderRadius: 12,
                backgroundColor: item.sender === 'user' 
                  ? theme.colors.bmGreenPrimary 
                  : theme.colors.background,
                color: item.sender === 'user' ? 'white' : theme.colors.textPrimary,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                whiteSpace: 'pre-line',
                border: item.sender !== 'user' ? `1px solid ${theme.colors.border}` : 'none'
              }}>
                <Text style={{ 
                  color: item.sender === 'user' ? 'white' : theme.colors.textPrimary,
                  fontSize: '14px'
                }}>
                  {item.text}
                </Text>
                
                {/* Mostrar recomendaciones si existen */}
                {item.recommendations && item.recommendations.length > 0 && (
                  <div style={{ 
                    marginTop: theme.spacing.sm, 
                    padding: theme.spacing.xs,
                    backgroundColor: item.sender === 'user' ? 'rgba(255,255,255,0.1)' : theme.colors.bmGreenLight + '20',
                    borderRadius: 4,
                    fontSize: '12px'
                  }}>
                    <Text strong style={{ 
                      color: item.sender === 'user' ? 'white' : theme.colors.bmGreenDark,
                      fontSize: '11px'
                    }}>
                      Sugerencias:
                    </Text>
                    {item.recommendations.map((rec, idx) => (
                      <div key={idx} style={{ marginTop: 2 }}>
                        <CheckCircleOutlined style={{ marginRight: 4, fontSize: 10 }} />
                        {rec}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </List.Item>
          )}
        />
      </div>

      {/* Input para comandos */}
      <div style={{ display: 'flex', gap: theme.spacing.sm }}>
        <TextArea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isConnected ? 
            "Ejemplo: 'Cambia a gráfico circular y muestra ROE'" :
            "Servicio de chat no disponible"
          }
          autoSize={{ minRows: 2, maxRows: 4 }}
          disabled={isSending || !isConnected}
          maxLength={500}
          style={{ flex: 1 }}
        />
        <Button
          type="primary"
          icon={isSending ? <SyncOutlined spin /> : <SendOutlined />}
          onClick={sendMessage}
          disabled={isSending || !isConnected || !inputValue.trim()}
          style={{
            backgroundColor: theme.colors.bmGreenPrimary,
            borderColor: theme.colors.bmGreenPrimary,
            height: 'auto',
            minHeight: 60,
            width: 60,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
          title="Enviar comando"
        />
      </div>

      {/* Gráfico actualizable */}
      <div style={{ marginTop: theme.spacing.lg }}>
        <InteractiveCharts
          data={chartConfig.data}
          availableKpis={chartConfig.availableKpis}
          title="Vista Dinámica Conversacional"
          description="Gráfico modificable mediante comandos de chat"
          onChartChange={(config) => {
            const newConfig = { ...chartConfig, ...config };
            setChartConfig(newConfig);
            if (onChartUpdate) {
              onChartUpdate(newConfig);
            }
          }}
        />
      </div>

      {/* Estado actual */}
      <div style={{ 
        marginTop: theme.spacing.sm,
        padding: theme.spacing.sm,
        backgroundColor: theme.colors.backgroundLight,
        borderRadius: 4,
        fontSize: '12px',
        color: theme.colors.textSecondary,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Space split={<span>•</span>}>
          <span>Tipo: <strong>{chartConfig.chartType?.toUpperCase()}</strong></span>
          <span>KPI: <strong>{chartConfig.selectedKpi?.replace('_', ' ')}</strong></span>
          <span>Datos: <strong>{chartConfig.data.length}</strong> elementos</span>
        </Space>
        <div>
          {isConnected ? (
            <span style={{ color: theme.colors.success }}>Conectado</span>
          ) : (
            <span style={{ color: theme.colors.error }}>Sin conexión</span>
          )}
        </div>
      </div>
    </div>
  );
};

ConversationalPivot.propTypes = {
  userId: PropTypes.string.isRequired,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  initialData: PropTypes.array,
  initialKpis: PropTypes.array,
  onChartUpdate: PropTypes.func
};

export default ConversationalPivot;
