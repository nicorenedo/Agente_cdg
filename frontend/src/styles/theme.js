// src/styles/theme.js
// Colores corporativos oficiales de Banca March actualizados con mejoras para CDG

const theme = {
  colors: {
    // Colores corporativos exactos de Banca March
    bmGreenPrimary: '#1B5E55',
    bmGreenLight: '#229B8B', 
    bmGreenDark: '#123B36',
    
    // Colores de soporte
    background: '#FFFFFF',
    backgroundLight: '#FAFAFA',
    backgroundDark: '#F5F5F5',
    textPrimary: '#333333',
    textSecondary: '#666666',
    textLight: '#999999',
    border: '#E0E0E0',
    borderLight: '#F0F0F0',
    
    // Estados mejorados
    success: '#4CAF50',
    successLight: '#81C784',
    warning: '#FF9800',
    warningLight: '#FFB74D',
    error: '#D32F2F',
    errorLight: '#E57373',
    info: '#1976D2',
    infoLight: '#64B5F6',
    
    // Colores adicionales para gráficos y visualizaciones
    chart: {
      primary: '#1B5E55',
      secondary: '#229B8B',
      tertiary: '#123B36',
      accent1: '#4CAF50',
      accent2: '#FF9800',
      accent3: '#1976D2',
      accent4: '#9C27B0',
      accent5: '#607D8B'
    },
    
    // Gradientes corporativos
    gradients: {
      primary: 'linear-gradient(135deg, #1B5E55, #229B8B)',
      secondary: 'linear-gradient(135deg, #123B36, #1B5E55)',
      light: 'linear-gradient(135deg, #FAFAFA, #FFFFFF)'
    }
  },
  
  // Configuración mejorada para Ant Design
  token: {
    colorPrimary: '#1B5E55',
    colorSuccess: '#229B8B',
    colorWarning: '#FF9800',
    colorError: '#D32F2F',
    colorInfo: '#1976D2',
    borderRadius: 6,
    borderRadiusLG: 8,
    borderRadiusSM: 4,
    fontSize: 14,
    fontSizeLG: 16,
    fontSizeSM: 12,
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    // Mejoras para componentes específicos
    controlHeight: 32,
    controlHeightLG: 40,
    controlHeightSM: 24,
    lineHeight: 1.5,
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#FFFFFF',
    colorBorder: '#E0E0E0',
    colorText: '#333333',
    colorTextSecondary: '#666666',
    colorTextTertiary: '#999999',
    // Sombras
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
    boxShadowSecondary: '0 4px 12px rgba(0, 0, 0, 0.15)',
  },
  
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  
  // Breakpoints para responsive design
  breakpoints: {
    xs: '576px',
    sm: '768px',
    md: '992px',
    lg: '1200px',
    xl: '1600px',
  },
  
  // Z-indexes para layering
  zIndex: {
    base: 1,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modal: 1040,
    popover: 1050,
    tooltip: 1060,
    toast: 1070,
  },
  
  // Transiciones
  transitions: {
    fast: '0.15s ease-in-out',
    normal: '0.3s ease-in-out',
    slow: '0.5s ease-in-out',
  },
  
  // Tipografía
  typography: {
    fontWeights: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeights: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
  },
};

export default theme;
