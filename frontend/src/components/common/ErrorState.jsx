// frontend/src/components/common/ErrorState.jsx
import React, { useState } from 'react';
import { Button, Typography, Space } from 'antd';
import { ExclamationCircleOutlined, ReloadOutlined, BugOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';
import theme from '../../styles/theme';

const { Title, Paragraph, Text } = Typography;

/**
 * ErrorState corporativo CDG - Manejo de errores con estilo Banca March
 * Soporte para ApiClientError y errores genéricos
 */
const ErrorState = ({
  error = null,
  message = 'Ha ocurrido un error inesperado',
  description = null,
  onRetry = null,
  showDetails = false,
  size = 'default', // 'small' | 'default' | 'large'
  style = {},
  className = '',
  ...rest
}) => {
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  // Extraer información del error (compatible con ApiClientError)
  const getErrorInfo = () => {
    if (!error) return { message, description };
    
    if (error.name === 'ApiClientError') {
      return {
        message: error.message || 'Error de API',
        description: error.detail || description,
        status: error.status,
        code: error.code,
      };
    }

    return {
      message: error.message || message,
      description: error.stack || description,
    };
  };

  const errorInfo = getErrorInfo();
  const isSmall = size === 'small';
  const isLarge = size === 'large';

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    padding: isSmall ? theme.spacing.md : isLarge ? theme.spacing.xl : theme.spacing.lg,
    textAlign: 'center',
    minHeight: isSmall ? 120 : isLarge ? 300 : 200,
    backgroundColor: `${theme.colors.error}05`,
    borderRadius: theme.token.borderRadius,
    border: `1px solid ${theme.colors.errorLight}20`,
    ...style,
  };

  const iconStyle = {
    fontSize: isSmall ? 32 : isLarge ? 64 : 48,
    color: theme.colors.error,
    marginBottom: theme.spacing.md,
  };

  return (
    <div 
      className={`cdg-error-state ${className}`}
      style={containerStyle} 
      {...rest}
    >
      <ExclamationCircleOutlined style={iconStyle} />
      
      <Space direction="vertical" align="center" size={theme.spacing.sm}>
        <Title 
          level={isSmall ? 5 : isLarge ? 3 : 4} 
          style={{ 
            color: theme.colors.error, 
            margin: 0,
            fontWeight: 600
          }}
        >
          {errorInfo.message}
        </Title>
        
        {errorInfo.description && (
          <Paragraph 
            style={{ 
              maxWidth: isSmall ? 300 : isLarge ? 600 : 450,
              color: theme.colors.textSecondary,
              margin: 0,
              fontSize: isSmall ? 13 : theme.token.fontSize
            }}
          >
            {typeof errorInfo.description === 'string' 
              ? errorInfo.description 
              : 'Error técnico detectado'
            }
          </Paragraph>
        )}

        {(errorInfo.status || errorInfo.code) && (
          <Text 
            type="secondary" 
            style={{ fontSize: 12, fontFamily: 'monospace' }}
          >
            {errorInfo.status && `HTTP ${errorInfo.status}`}
            {errorInfo.code && errorInfo.code !== errorInfo.status && ` • Code ${errorInfo.code}`}
          </Text>
        )}
      </Space>

      <Space 
        style={{ marginTop: theme.spacing.lg }}
        size={theme.spacing.sm}
      >
        {onRetry && (
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={onRetry}
            style={{
              backgroundColor: theme.colors.bmGreenPrimary,
              borderColor: theme.colors.bmGreenPrimary,
            }}
            size={isSmall ? 'small' : 'default'}
          >
            Reintentar
          </Button>
        )}

        {showDetails && error && (
          <Button
            type="text"
            icon={<BugOutlined />}
            onClick={() => setShowErrorDetails(!showErrorDetails)}
            size={isSmall ? 'small' : 'default'}
            style={{ color: theme.colors.textSecondary }}
          >
            {showErrorDetails ? 'Ocultar' : 'Ver'} detalles
          </Button>
        )}
      </Space>

      {showErrorDetails && error && (
        <div
          style={{
            marginTop: theme.spacing.md,
            padding: theme.spacing.sm,
            backgroundColor: theme.colors.backgroundDark,
            borderRadius: theme.token.borderRadius,
            maxWidth: '100%',
            overflow: 'auto',
          }}
        >
          <Text 
            code 
            style={{ 
              fontSize: 11, 
              color: theme.colors.textSecondary,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}
          >
            {error.stack || JSON.stringify(error, null, 2)}
          </Text>
        </div>
      )}
    </div>
  );
};

ErrorState.propTypes = {
  error: PropTypes.oneOfType([PropTypes.object, PropTypes.string]),
  message: PropTypes.string,
  description: PropTypes.oneOfType([PropTypes.string, PropTypes.node]),
  onRetry: PropTypes.func,
  showDetails: PropTypes.bool,
  size: PropTypes.oneOf(['small', 'default', 'large']),
  style: PropTypes.object,
  className: PropTypes.string,
};

export default ErrorState;
