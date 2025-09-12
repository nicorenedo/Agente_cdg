// src/reportWebVitals.js
// ✅ Web Vitals para CDG v5.0 - Compatible con web-vitals v3+

const reportWebVitals = (onPerfEntry) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    // ✅ CORRECCIÓN: Usar los métodos correctos de web-vitals v3+
    import('web-vitals').then(({ onCLS, onFCP, onINP, onLCP, onTTFB }) => {
      // Core Web Vitals
      onCLS(onPerfEntry);  // Cumulative Layout Shift
      onFCP(onPerfEntry);  // First Contentful Paint
      onINP(onPerfEntry);  // Interaction to Next Paint (reemplaza FID en v3)
      onLCP(onPerfEntry);  // Largest Contentful Paint
      onTTFB(onPerfEntry); // Time to First Byte
    }).catch(error => {
      console.warn('Failed to load web-vitals:', error);
    });
  }
};

export default reportWebVitals;
