// src/styles/theme.js
// Identidad visual Accenture — CDG Intelligence

const theme = {
  colors: {
    // Paleta Accenture
    bmGreenPrimary: '#A100FF',   // Accenture purple (alias mantenido por compatibilidad)
    bmGreenLight:   '#CC66FF',   // Accenture purple light
    bmGreenDark:    '#7B00CC',   // Accenture purple dark
    accent:         '#00B8F5',   // Accenture cyan
    headerBg:       '#1A0033',   // Dark header

    // Fondos
    background:      '#FFFFFF',
    backgroundLight: '#F8F5FF',
    backgroundDark:  '#F0E8FF',

    // Tipografía
    textPrimary:   '#1A1A2E',
    textSecondary: '#6B6B8A',
    textLight:     '#9999BB',

    // Bordes
    border:      '#E8E0F5',
    borderLight: '#F0E8FF',

    // Estados semáforo Accenture
    success:      '#A100FF',   // Excelente → púrpura
    successLight: '#CC66FF',
    warning:      '#F5A623',   // Regular → ámbar
    warningLight: '#FFD480',
    error:        '#E5002B',   // Crítico → rojo Accenture
    errorLight:   '#FF6680',
    info:         '#00B8F5',   // Info → cyan
    infoLight:    '#80DBFA',

    // Paleta Accenture para gráficos — monocromática púrpura
    chart: {
      primary:  '#A100FF',
      secondary:'#7B00CC',
      tertiary: '#CC66FF',
      accent1:  '#5500AA',
      accent2:  '#E600C8',
      accent3:  '#DD99FF',
      accent4:  '#380080',
      accent5:  '#F0CCFF'
    }
  },

  // Configuración para Ant Design
  token: {
    colorPrimary:          '#A100FF',
    colorSuccess:          '#A100FF',
    colorWarning:          '#F5A623',
    colorError:            '#E5002B',
    colorInfo:             '#00B8F5',
    borderRadius:          8,
    fontSize:              14,
    fontFamily:            "'Inter', 'Segoe UI', sans-serif",
    controlHeight:         32,
    colorBgContainer:      '#FFFFFF',
    colorBorder:           '#E8E0F5',
    colorText:             '#1A1A2E',
    colorTextSecondary:    '#6B6B8A'
  },

  spacing: {
    xs:  4,
    sm:  8,
    md:  16,
    lg:  24,
    xl:  32,
    xxl: 40
  },

  shadows: {
    card:     '0 2px 8px rgba(161,0,255,0.08)',
    elevated: '0 4px 16px rgba(161,0,255,0.12)',
    overlay:  '0 8px 32px rgba(161,0,255,0.16)'
  },

  transitions: {
    fast:   '0.15s ease-in-out',
    normal: '0.2s ease',
    slow:   '0.3s ease-in-out'
  }
};

export default theme;
