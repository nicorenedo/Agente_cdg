// frontend/src/components/common/Loader.jsx
import React from 'react';
import { Spin } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import theme from '../../styles/theme';

/**
 * Loader corporativo CDG con spinner personalizado Banca March
 * Tres modos: spinner, skeleton y pantalla completa
 */
const Loader = ({
  spinning = true,
  tip = "Cargando...",
  size = "default",
  mode = "spinner", // "spinner" | "skeleton" | "fullscreen"
  style = {},
  children,
  delay = 0,
  ...rest
}) => {
  // Spinner personalizado con colores Banca March
  const customSpinner = (
    <LoadingOutlined 
      style={{ 
        fontSize: size === 'large' ? 32 : size === 'small' ? 16 : 24,
        color: theme.colors.bmGreenPrimary 
      }} 
      spin 
    />
  );

  const getLoaderStyle = () => {
    const baseStyle = {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      ...style,
    };

    switch (mode) {
      case 'fullscreen':
        return {
          ...baseStyle,
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          backdropFilter: 'blur(2px)',
          zIndex: 9999,
        };
      case 'skeleton':
        return {
          ...baseStyle,
          padding: theme.spacing.lg,
          minHeight: 200,
        };
      default:
        return {
          ...baseStyle,
          minHeight: children ? 'auto' : 100,
          padding: children ? theme.spacing.sm : theme.spacing.md,
        };
    }
  };

  const tipStyle = {
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.sm,
    fontSize: theme.token.fontSize,
    fontFamily: theme.token.fontFamily,
  };

  if (mode === 'fullscreen') {
    return spinning ? (
      <div style={getLoaderStyle()} {...rest}>
        <div style={{ textAlign: 'center' }}>
          <Spin 
            indicator={customSpinner} 
            size={size}
            delay={delay}
          />
          {tip && <div style={tipStyle}>{tip}</div>}
        </div>
      </div>
    ) : null;
  }

  return (
    <Spin
      spinning={spinning}
      tip={tip}
      size={size}
      indicator={customSpinner}
      delay={delay}
      style={getLoaderStyle()}
      {...rest}
    >
      <div style={{ minHeight: children ? 'auto' : 50 }}>
        {children}
      </div>
    </Spin>
  );
};

Loader.propTypes = {
  spinning: PropTypes.bool,
  tip: PropTypes.string,
  size: PropTypes.oneOf(['small', 'default', 'large']),
  mode: PropTypes.oneOf(['spinner', 'skeleton', 'fullscreen']),
  style: PropTypes.object,
  children: PropTypes.node,
  delay: PropTypes.number,
};

export default Loader;
