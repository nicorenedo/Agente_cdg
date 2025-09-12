// src/styles/theme.js
// Colores corporativos oficiales de Banca March

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
    
    // Colores adicionales para gráficos
    chart: {
      primary: '#1B5E55',
      secondary: '#229B8B',
      tertiary: '#123B36',
      accent1: '#4CAF50',
      accent2: '#FF9800',
      accent3: '#1976D2',
      accent4: '#9C27B0',
      accent5: '#607D8B'
    }
  },
  
  // Configuración para Ant Design
  token: {
    colorPrimary: '#1B5E55',
    colorSuccess: '#229B8B',
    colorWarning: '#FF9800',
    colorError: '#D32F2F',
    colorInfo: '#1976D2',
    borderRadius: 6,
    fontSize: 14,
    fontFamily: "'Inter', 'Segoe UI', sans-serif",
    controlHeight: 32,
    colorBgContainer: '#FFFFFF',
    colorBorder: '#E0E0E0',
    colorText: '#333333',
    colorTextSecondary: '#666666'
  },
  
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px'
  },
  
  transitions: {
    fast: '0.15s ease-in-out',
    normal: '0.3s ease-in-out'
  }
};

export default theme;
