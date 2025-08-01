// src/components/Chat/ConversationalPivot.jsx
// Componente crítico para modificación interactiva del dashboard mediante conversación

import React, { useState, useEffect, useCallback } from 'react';
import { Input, Button, Typography, List, Tooltip, message, Space } from 'antd';
import { SendOutlined, SyncOutlined, BarChartOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import chatService from '../../services/chatService';
import InteractiveCharts from '../Dashboard/InteractiveCharts';
import theme from '../../styles/theme';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const ConversationalPivot = ({ 
  userId, 
  gestorId, 
  periodo, 
  initialData = [], 
  initialKpis = ['roe', 'margen_neto', 'eficiencia'] 
}) => {
  // Estados principales
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [chartConfig, setChartConfig] = useState({
    chartType: 'bar',
    selectedKpi: initialKpis[0] || 'roe',
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
      `¡Hola! Puedes pedirme cambios en la visualización usando lenguaje natural:

• "Cambia a gráfico circular"
• "Muestra el ROE en barras" 
• "Visualiza margen neto como líneas"
• "Compara eficiencia operativa"

¿Qué modificación deseas hacer?`
    );
  }, [addMessage]);

  // Función para interpretar comandos de gráficos
  const parseChartCommands = (text) => {
    const textLower = text.toLowerCase();
    let updates = {};

    // Detectar cambios de tipo de gráfico
    if (textLower.includes('circular') || textLower.includes('pastel') || textLower.includes('pie')) {
      updates.chartType = 'pie';
    } else if (textLower.includes('línea') || textLower.includes('linea') || textLower.includes('evolución')) {
      updates.chartType = 'line';
    } else if (textLower.includes('barra') || textLower.includes('barras') || textLower.includes('columna')) {
      updates.chartType = 'bar';
    }

    // Detectar cambios de KPI
    const kpiMappings = {
      'roe': ['roe', 'rentabilidad', 'return on equity'],
      'margen_neto': ['margen', 'margen neto', 'margen_neto', 'beneficio'],
      'eficiencia': ['eficiencia', 'eficiencia operativa', 'ratio eficiencia'],
      'total_ingresos': ['ingresos', 'facturación', 'total ingresos'],
      'total_gastos': ['gastos', 'costes', 'total gastos']
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

  // Enviar mensaje al chat
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
      // Enviar al servicio de chat
      const response = await chatService.sendMessage(userId, userMessage, {
        gestorId,
        periodo,
        context: { 
          currentChart: chartConfig,
          conversationalPivot: true 
        }
      });

      if (response.error) {
        addMessage('agent', `Error: ${response.error}`);
      } else {
        // Añadir respuesta del agente
        addMessage('agent', 
          response.response || 'Procesando tu solicitud...', 
          response.charts || [], 
          response.recommendations || []
        );

        // Interpretar comandos de gráficos en la respuesta
        const chartUpdates = parseChartCommands(userMessage);
        
        if (Object.keys(chartUpdates).length > 0) {
          setChartConfig(prev => ({ ...prev, ...chartUpdates }));
          
          const updateMessages = [];
          if (chartUpdates.chartType) {
            updateMessages.push(`Tipo de gráfico cambiado a: ${chartUpdates.chartType}`);
          }
          if (chartUpdates.selectedKpi) {
            updateMessages.push(`KPI seleccionado: ${chartUpdates.selectedKpi.replace('_', ' ').toUpperCase()}`);
          }
          
          if (updateMessages.length > 0) {
            message.success(updateMessages.join(' | '));
          }
        }
      }

    } catch (error) {
      addMessage('agent', `Error de comunicación: ${error.message}`);
      message.error('Error al procesar el comando');
    } finally {
      setIsSending(false);
    }
  };

  // Manejar Enter para enviar
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isSending) {
        sendMessage();
      }
    }
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
        </Title>
        <Text style={{ color: theme.colors.textSecondary }}>
          Modifica visualizaciones usando lenguaje natural
        </Text>
      </div>

      {/* Área de chat */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto',
        marginBottom: theme.spacing.md,
        maxHeight: '200px',
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
                maxWidth: '80%',
                padding: theme.spacing.sm,
                borderRadius: 12,
                backgroundColor: item.sender === 'user' 
                  ? theme.colors.bmGreenPrimary 
                  : theme.colors.background,
                color: item.sender === 'user' ? 'white' : theme.colors.textPrimary,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                whiteSpace: 'pre-line'
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
                    fontSize: '12px',
                    fontStyle: 'italic',
                    opacity: 0.9
                  }}>
                    {item.recommendations.map((rec, idx) => (
                      <div key={idx}>• {rec}</div>
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
          placeholder="Ejemplo: 'Cambia a gráfico circular y muestra ROE'"
          autoSize={{ minRows: 2, maxRows: 4 }}
          disabled={isSending}
          maxLength={500}
          style={{ flex: 1 }}
        />
        <Button
          type="primary"
          icon={isSending ? <SyncOutlined spin /> : <SendOutlined />}
          onClick={sendMessage}
          disabled={isSending || !inputValue.trim()}
          style={{
            backgroundColor: theme.colors.bmGreenPrimary,
            borderColor: theme.colors.bmGreenPrimary,
            height: 'auto'
          }}
        >
          Enviar
        </Button>
      </div>

      {/* Gráfico actualizable */}
      <div style={{ marginTop: theme.spacing.lg }}>
        <InteractiveCharts
          data={chartConfig.data}
          availableKpis={chartConfig.availableKpis}
          title="Vista Dinámica Conversacional"
          description="Gráfico modificable mediante comandos de chat"
          onChartChange={(config) => {
            setChartConfig(prev => ({ ...prev, ...config }));
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
        color: theme.colors.textSecondary
      }}>
        <Space split={<span>•</span>}>
          <span>Tipo: {chartConfig.chartType}</span>
          <span>KPI: {chartConfig.selectedKpi?.replace('_', ' ').toUpperCase()}</span>
          <span>Datos: {chartConfig.data.length} elementos</span>
        </Space>
      </div>
    </div>
  );
};

ConversationalPivot.propTypes = {
  userId: PropTypes.string.isRequired,
  gestorId: PropTypes.string,
  periodo: PropTypes.string,
  initialData: PropTypes.array,
  initialKpis: PropTypes.array
};

export default ConversationalPivot;
