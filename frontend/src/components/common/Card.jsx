// frontend/src/components/common/Card.jsx
import React from 'react';
import { Card as AntCard, Alert } from 'antd';
import PropTypes from 'prop-types';
import theme from '../../styles/theme';

/**
 * Card corporativa CDG - Wrapper de Ant Design Card con tema Banca March
 * Perfecta para KPIs, gráficos y contenido dashboard
 */
const Card = ({
  title,
  children,
  extra,
  loading = false,
  error = null,
  style = {},
  bordered = true,
  hoverable = false,
  className = '',
  ...rest
}) => {
  const cardStyle = {
    borderRadius: theme.token.borderRadius,
    boxShadow: '0 2px 8px rgba(27, 94, 85, 0.08)',
    backgroundColor: theme.colors.background,
    border: bordered ? `1px solid ${theme.colors.border}` : 'none',
    transition: hoverable ? 'box-shadow 0.3s ease, transform 0.2s ease' : 'none',
    ...style,
  };

  const hoverStyle = hoverable ? {
    ':hover': {
      boxShadow: '0 4px 16px rgba(27, 94, 85, 0.12)',
      transform: 'translateY(-2px)',
    }
  } : {};

  return (
    <AntCard
      title={title}
      extra={extra}
      loading={loading}
      style={cardStyle}
      className={`cdg-card ${className}`}
      bordered={bordered}
      hoverable={hoverable}
      {...rest}
    >
      {error ? (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          style={{ 
            marginBottom: theme.spacing.md,
            borderColor: theme.colors.errorLight,
            backgroundColor: `${theme.colors.error}10`
          }}
        />
      ) : (
        children
      )}
    </AntCard>
  );
};

Card.propTypes = {
  title: PropTypes.node,
  children: PropTypes.node,
  extra: PropTypes.node,
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.node]),
  style: PropTypes.object,
  bordered: PropTypes.bool,
  hoverable: PropTypes.bool,
  className: PropTypes.string,
};

export default Card;
