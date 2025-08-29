module.exports = {
  extends: [
    'react-app',
    'react-app/jest'
  ],
  plugins: ['react', 'react-hooks'],
  rules: {
    // Desactivar reglas problemáticas para React 17+
    'react/react-in-jsx-scope': 'off',
    'react/jsx-uses-react': 'off',
    
    // Configurar reglas de hooks más flexibles
    'react-hooks/exhaustive-deps': 'warn',
    'react-hooks/rules-of-hooks': 'error',
    
    // Permitir console.log en desarrollo
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off'
  },
  settings: {
    react: {
      version: 'detect'
    }
  },
  env: {
    browser: true,
    es6: true,
    node: true
  }
};
