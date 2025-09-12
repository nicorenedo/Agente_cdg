// frontend/src/services/reportService.js
/* eslint-disable no-console */

/**
 * Report Service v11.0 — Perfect Integration (Chat Agent v10.0 + CDG Agent v6.0)
 * -------------------------------------------------------------------------------
 * ✅ INTEGRADO: Todos los endpoints de reports v11.0 con Perfect Integration
 * ✅ NUEVO: Soporte para gestorAnalysis, reflection, feedback, integration
 * ✅ AMPLIADO: Generación de reportes con análisis complejo del CDG Agent v6.0
 * ✅ OPTIMIZADO: Validación/normalización de payloads mejorada
 * ✅ AÑADIDO: Utilidades de nombres de archivo y metadatos extendidas
 * ✅ MEJORADO: Descarga segura (blob/JSON) con fallback robusto
 * ✅ NUEVO: Reportes automáticos basados en insights de reflexión
 * ✅ NUEVO: Integración con feedback del usuario para mejora continua
 */

import api, { 
  ApiClientError,
  gestorAnalysis as gestorAnalysisAPI,
  reflection as reflectionAPI,
  feedback as feedbackAPI,
  integration as integrationAPI,
  agent as agentAPI,
  deviations as deviationsAPI
} from "./api";

/* =========================================
 * Constantes y utilidades básicas actualizadas v11.0
 * ========================================= */

const PERIOD_RE = /^\d{4}-\d{2}$/; // YYYY-MM

// ✅ ACTUALIZADAS: Opciones por defecto extendidas
const DEFAULT_BR_OPTIONS = Object.freeze({
  include_kpis: true,
  include_charts: true,
  include_comments: true,
  include_complex_analysis: true,    // ✅ NUEVO: CDG Agent v6.0
  include_reflection_insights: true, // ✅ NUEVO: Reflection
  include_deviations: true,          // ✅ NUEVO: Desviaciones críticas
  layout: "portrait", // o 'landscape'
  format_style: "executive",         // ✅ NUEVO: Estilos de formato
});

const DEFAULT_ES_OPTIONS = Object.freeze({
  include_overview: true,
  include_risks: true,
  include_actions: true,
  include_reflection_summary: true,  // ✅ NUEVO: Resumen de reflexión
  include_integration_status: true,  // ✅ NUEVO: Estado de integración
  layout: "portrait",
  format_style: "executive",         // ✅ NUEVO: Estilos de formato
});

// ✅ NUEVAS: Opciones para análisis de desviaciones
const DEFAULT_DEVIATION_OPTIONS = Object.freeze({
  include_critical: true,
  include_margen: true,
  include_volumen: true,
  umbral_critico: 15.0,
  z_score: 2.0,
  factor_volumen: 3.0,
  enhanced: true,
});

const DEFAULT_EXPORT_OPTIONS = Object.freeze({
  format: "pdf", // 'pdf' | 'xlsx' | 'json'
  include_metadata: true,            // ✅ NUEVO: Metadatos extendidos
  include_feedback_link: true,       // ✅ NUEVO: Link para feedback
  compression: "standard",           // ✅ NUEVO: Nivel de compresión
});

/**
 * ✅ MEJORADA: Sanitiza un objeto eliminando valores vacíos
 */
const clean = (obj = {}) =>
  Object.fromEntries(
    Object.entries(obj).filter(
      ([, v]) => v !== undefined && v !== null && v !== "" && v !== false
    )
  );

/**
 * Valida el formato de período.
 */
const assertPeriodo = (periodo, fieldName = "periodo") => {
  if (!periodo || !PERIOD_RE.test(periodo)) {
    throw new ApiClientError(
      `Formato inválido de ${fieldName}. Esperado 'YYYY-MM'.`,
      { status: 400, code: 400 }
    );
  }
  return periodo;
};

/**
 * ✅ MEJORADA: Crea nombres de archivos consistentes con timestamp
 */
const buildFileName = ({
  base = "cdg-report",
  periodo,
  gestorId,
  reportType,
  suffix,
  ext = "pdf",
  includeTimestamp = true,
} = {}) => {
  const parts = [base];
  if (reportType) parts.push(reportType);
  if (periodo) parts.push(periodo);
  if (gestorId) parts.push(`gestor-${gestorId}`);
  if (suffix) parts.push(suffix);
  
  // ✅ NUEVO: Timestamp opcional para evitar conflictos
  if (includeTimestamp) {
    const timestamp = new Date().toISOString().slice(0, 16).replace(/[:-]/g, '');
    parts.push(timestamp);
  }
  
  return `${parts.join("_")}.${ext}`.replace(/[/\\?%*:|"<> ]+/g, "_");
};

/**
 * Detecta si una respuesta axios es binaria.
 */
const isBlobResponse = (axiosResponse) => {
  const ct =
    axiosResponse?.headers?.["content-type"] ||
    axiosResponse?.headers?.["Content-Type"] ||
    "";
  return (
    axiosResponse?.data instanceof Blob ||
    ct.includes("application/pdf") ||
    ct.includes("application/octet-stream") ||
    ct.includes("application/vnd.openxmlformats") // xlsx
  );
};

/**
 * ✅ MEJORADA: Descarga client-side con validación robusta
 */
const triggerDownload = (blob, filename = "download.bin") => {
  try {
    // Validar que el blob es válido
    if (!(blob instanceof Blob) || blob.size === 0) {
      throw new Error('Invalid blob data');
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    // Cleanup con delay para asegurar la descarga
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
    
    console.log(`[ReportService] ✅ Download triggered: ${filename}`);
    return { success: true, filename };
  } catch (error) {
    console.error(`[ReportService] ❌ Download failed:`, error);
    return { success: false, error: error.message };
  }
};

/* =========================================
 * ✅ BUILDERS DE PAYLOAD ACTUALIZADOS v11.0
 * ========================================= */

const buildBusinessReviewPayload = ({
  user_id,
  gestor_id,
  periodo,
  options = {},
  report_type = "business_review",
} = {}) => {
  assertPeriodo(periodo, "periodo");
  if (!gestor_id) {
    throw new ApiClientError("gestor_id es requerido para Business Review.", {
      status: 400,
      code: 400,
    });
  }
  return {
    user_id: user_id || "anon",
    gestor_id,
    periodo,
    report_type,
    options: { ...DEFAULT_BR_OPTIONS, ...clean(options) },
  };
};

const buildExecutiveSummaryPayload = ({
  user_id,
  periodo,
  options = {},
} = {}) => {
  assertPeriodo(periodo, "periodo");
  return {
    user_id: user_id || "anon",
    periodo,
    options: { ...DEFAULT_ES_OPTIONS, ...clean(options) },
  };
};

// ✅ NUEVO: Builder para análisis de desviaciones extendido
const buildDeviationAnalysisPayload = ({
  periodo,
  options = {},
} = {}) => {
  assertPeriodo(periodo, "periodo");
  return {
    periodo,
    options: { ...DEFAULT_DEVIATION_OPTIONS, ...clean(options) },
  };
};

/* =========================================
 * ✅ NORMALIZADORES MEJORADOS v11.0
 * ========================================= */

const normalizeBusinessReview = (data) => {
  return {
    title: data?.title || "Business Review",
    review: data?.review || data || {},
    // ✅ NUEVOS: Metadatos extendidos
    complex_analysis: data?.complex_analysis || null,
    reflection_insights: data?.reflection_insights || null,
    performance_data: data?.performance_data || null,
    generation_metadata: {
      timestamp: data?.timestamp || new Date().toISOString(),
      version: data?.version || "11.0",
      chat_agent: data?.chat_agent || "v10.0",
      cdg_agent: data?.cdg_agent || "v6.0",
      integration: data?.integration || "Perfect Integration"
    }
  };
};

const normalizeExecutiveSummary = (data) => ({
  title: data?.title || "Executive Summary",
  summary: data?.summary || data || {},
  // ✅ NUEVOS: Metadatos extendidos
  reflection_summary: data?.reflection_summary || null,
  integration_status: data?.integration_status || null,
  generation_metadata: {
    timestamp: data?.timestamp || new Date().toISOString(),
    version: data?.version || "11.0",
    scope: data?.scope || "executive"
  }
});

// ✅ MEJORADO: Normalización de análisis de desviaciones
const normalizeDeviationAnalysis = (data) => ({
  title: "Deviation Analysis",
  periodo: data?.periodo || null,
  deviations: {
    critical: data?.deviations?.critical || [],
    margen: data?.deviations?.margen || [],
    volumen: data?.deviations?.volumen || [],
    pricing: data?.deviations?.pricing || []
  },
  summary: data?.summary || null,
  // ✅ NUEVO: Estadísticas consolidadas
  stats: {
    total_critical: data?.deviations?.critical?.length || 0,
    total_margen: data?.deviations?.margen?.length || 0,
    total_volumen: data?.deviations?.volumen?.length || 0,
    severity_distribution: data?.severity_distribution || {}
  },
  generation_metadata: {
    timestamp: data?.timestamp || new Date().toISOString(),
    enhanced: data?.enhanced || true,
    thresholds: data?.thresholds || {}
  }
});

/* =========================================
 * ✅ LLAMADAS PRINCIPALES ACTUALIZADAS v11.0
 * ========================================= */

/**
 * ✅ MEJORADA: Genera Business Review con análisis complejo integrado
 */
const businessReview = async (
  { user_id, gestor_id, periodo, options } = {},
  cfg = {}
) => {
  console.log(`[ReportService] 📊 Generating Business Review for gestor ${gestor_id}, period ${periodo}`);
  
  const payload = buildBusinessReviewPayload({
    user_id,
    gestor_id,
    periodo,
    options,
  });

  try {
    // ✅ NUEVO: Enriquecer con análisis complejo si está habilitado
    if (payload.options.include_complex_analysis) {
      try {
        console.log(`[ReportService] 🧠 Including complex analysis from CDG Agent v6.0`);
        const complexAnalysis = await agentAPI.complexAnalysis({
          user_message: `Análisis completo del gestor ${gestor_id} para el período ${periodo}`,
          gestor_id,
          periodo,
          analysis_depth: "deep"
        });
        payload.complex_analysis_data = complexAnalysis;
      } catch (analysisError) {
        console.warn(`[ReportService] ⚠️ Complex analysis failed:`, analysisError.message);
      }
    }

    // ✅ NUEVO: Incluir insights de reflexión si está habilitado
    if (payload.options.include_reflection_insights) {
      try {
        console.log(`[ReportService] 🔍 Including reflection insights`);
        const reflectionInsights = await reflectionAPI.insights();
        payload.reflection_insights_data = reflectionInsights;
      } catch (reflectionError) {
        console.warn(`[ReportService] ⚠️ Reflection insights failed:`, reflectionError.message);
      }
    }

    const data = await api.reports.businessReview(payload, cfg);
    const normalized = normalizeBusinessReview(data);
    
    console.log(`[ReportService] ✅ Business Review generated successfully`);
    return normalized;
  } catch (error) {
    console.error(`[ReportService] ❌ Error generating Business Review:`, error.message);
    throw error;
  }
};

/**
 * ✅ MEJORADA: Genera Executive Summary con estado de integración
 */
const executiveSummary = async ({ user_id, periodo, options } = {}, cfg = {}) => {
  console.log(`[ReportService] 📈 Generating Executive Summary for period ${periodo}`);
  
  const payload = buildExecutiveSummaryPayload({ user_id, periodo, options });

  try {
    // ✅ NUEVO: Incluir estado de integración si está habilitado
    if (payload.options.include_integration_status) {
      try {
        console.log(`[ReportService] 🔗 Including integration status`);
        const integrationStatus = await integrationAPI.agentCoordination();
        payload.integration_status_data = integrationStatus;
      } catch (integrationError) {
        console.warn(`[ReportService] ⚠️ Integration status failed:`, integrationError.message);
      }
    }

    const data = await api.reports.executiveSummary(payload, cfg);
    const normalized = normalizeExecutiveSummary(data);
    
    console.log(`[ReportService] ✅ Executive Summary generated successfully`);
    return normalized;
  } catch (error) {
    console.error(`[ReportService] ❌ Error generating Executive Summary:`, error.message);
    throw error;
  }
};

/**
 * ✅ COMPLETAMENTE REESCRITA: Genera análisis de desviaciones con nuevos endpoints v11.0
 */
const deviationAnalysis = async (periodo, options = {}, cfg = {}) => {
  assertPeriodo(periodo, "periodo");
  console.log(`[ReportService] 🚨 Generating comprehensive Deviation Analysis for period ${periodo}`);
  
  const cleanOptions = { ...DEFAULT_DEVIATION_OPTIONS, ...clean(options) };

  try {
    // ✅ NUEVO: Análisis paralelo de todos los tipos de desviaciones
    const analysisPromises = [];

    // Desviaciones críticas
    if (cleanOptions.include_critical) {
      analysisPromises.push(
        deviationsAPI.critical(periodo, cleanOptions.umbral_critico)
          .then(data => ({ type: 'critical', data }))
          .catch(error => ({ type: 'critical', error: error.message }))
      );
    }

    // Desviaciones de margen
    if (cleanOptions.include_margen) {
      analysisPromises.push(
        deviationsAPI.margen(periodo, { 
          z: cleanOptions.z_score, 
          enhanced: cleanOptions.enhanced 
        })
          .then(data => ({ type: 'margen', data }))
          .catch(error => ({ type: 'margen', error: error.message }))
      );
    }

    // Desviaciones de volumen
    if (cleanOptions.include_volumen) {
      analysisPromises.push(
        deviationsAPI.volumen(periodo, { 
          factor: cleanOptions.factor_volumen, 
          enhanced: cleanOptions.enhanced 
        })
          .then(data => ({ type: 'volumen', data }))
          .catch(error => ({ type: 'volumen', error: error.message }))
      );
    }

    // Análisis tradicional como fallback
    analysisPromises.push(
      api.reports.deviationAnalysis(periodo, cfg)
        .then(data => ({ type: 'traditional', data }))
        .catch(error => ({ type: 'traditional', error: error.message }))
    );

    const results = await Promise.all(analysisPromises);
    
    // Consolidar resultados
    const consolidatedData = {
      periodo,
      deviations: {},
      summary: null,
      enhanced: cleanOptions.enhanced,
      thresholds: {
        critical: cleanOptions.umbral_critico,
        z_score: cleanOptions.z_score,
        factor_volumen: cleanOptions.factor_volumen
      }
    };

    results.forEach(result => {
      if (result.error) {
        console.warn(`[ReportService] ⚠️ ${result.type} analysis failed:`, result.error);
        consolidatedData.deviations[result.type] = [];
      } else {
        consolidatedData.deviations[result.type] = result.data?.deviations || result.data || [];
      }
    });

    // ✅ NUEVO: Generar resumen consolidado
    const totalDeviations = Object.values(consolidatedData.deviations)
      .flat()
      .filter(Array.isArray)
      .reduce((sum, arr) => sum + arr.length, 0);

    consolidatedData.summary = {
      total_deviations: totalDeviations,
      critical_count: consolidatedData.deviations.critical?.length || 0,
      margen_count: consolidatedData.deviations.margen?.length || 0,
      volumen_count: consolidatedData.deviations.volumen?.length || 0,
      severity_level: totalDeviations > 10 ? 'HIGH' : totalDeviations > 5 ? 'MEDIUM' : 'LOW'
    };

    const normalized = normalizeDeviationAnalysis(consolidatedData);
    
    console.log(`[ReportService] ✅ Comprehensive Deviation Analysis completed:`, {
      total: totalDeviations,
      critical: normalized.stats.total_critical,
      margen: normalized.stats.total_margen,
      volumen: normalized.stats.total_volumen
    });
    
    return normalized;
  } catch (error) {
    console.error(`[ReportService] ❌ Error generating Deviation Analysis:`, error.message);
    throw error;
  }
};

/**
 * ✅ NUEVO: Genera reporte de performance de gestor usando gestorAnalysis
 */
const gestorPerformanceReport = async (gestorId, periodo, options = {}, cfg = {}) => {
  console.log(`[ReportService] 👤 Generating Gestor Performance Report for ${gestorId}`);
  
  try {
    const performanceData = await gestorAnalysisAPI.performance(gestorId, periodo, cfg);
    
    const report = {
      title: `Performance Report - Gestor ${gestorId}`,
      gestor_id: gestorId,
      periodo,
      performance: performanceData,
      generation_metadata: {
        timestamp: new Date().toISOString(),
        version: "11.0",
        source: "gestorAnalysis_v11"
      }
    };
    
    console.log(`[ReportService] ✅ Gestor Performance Report generated`);
    return report;
  } catch (error) {
    console.error(`[ReportService] ❌ Error generating Gestor Performance Report:`, error.message);
    throw error;
  }
};

/**
 * Obtiene metadatos de tipos y formatos soportados por el backend.
 */
const getMeta = (cfg = {}) => api.reports.meta(cfg);

/* =========================================
 * ✅ EXPORTACIÓN Y DESCARGA MEJORADA v11.0
 * ========================================= */

/**
 * ✅ MEJORADA: Exportación con soporte extendido y feedback
 */
const exportReport = async (
  { format = "pdf", filename, autoDownload = true, payload = {}, includeFeedback = true } = {},
  cfg = {}
) => {
  console.log(`[ReportService] 📥 Exporting report in format: ${format}`);
  
  // ✅ NUEVO: Enriquecer payload con metadatos de exportación
  const enrichedPayload = {
    format,
    ...clean(payload),
    export_metadata: {
      timestamp: new Date().toISOString(),
      version: "11.0",
      user_agent: navigator.userAgent,
      include_feedback: includeFeedback
    }
  };

  // Intentamos descarga binaria directa (cuando el backend la habilite)
  try {
    console.log(`[ReportService] 🔄 Attempting binary download...`);
    
    const res = await api.http.raw.post(
      "/reports/export",
      enrichedPayload,
      {
        ...cfg,
        responseType: "blob",
        timeout: 60000, // ✅ NUEVO: Timeout extendido para reportes grandes
        headers: {
          Accept:
            format === "pdf"
              ? "application/pdf"
              : format === "xlsx"
              ? "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              : "application/json",
        },
      }
    );

    const suggestedName =
      filename ||
      buildFileName({
        base: "cdg-report",
        reportType: payload.report_type || "general",
        ext: format === "xlsx" ? "xlsx" : format === "json" ? "json" : "pdf",
      });

    if (isBlobResponse(res)) {
      console.log(`[ReportService] ✅ Binary response received, size: ${res.data.size} bytes`);
      
      if (autoDownload) {
        const downloadResult = triggerDownload(res.data, suggestedName);
        if (!downloadResult.success) {
          throw new Error(`Download failed: ${downloadResult.error}`);
        }
      }
      
      return { 
        ok: true, 
        filename: suggestedName, 
        format, 
        size: res.data.size,
        type: 'binary' 
      };
    }

    console.log(`[ReportService] ℹ️ Response not binary, falling back to JSON...`);
  } catch (err) {
    console.warn("[ReportService] ⚠️ Binary export failed, falling back to JSON:", err?.message);
  }

  // Fallback: usar el wrapper del SDK (JSON)
  try {
    console.log(`[ReportService] 🔄 Using JSON fallback export...`);
    
    const json = await api.reports.export(enrichedPayload, cfg);
    const ext = format === "xlsx" ? "xlsx" : format === "json" ? "json" : "pdf";
    const safeName =
      filename ||
      buildFileName({
        base: "cdg-report",
        reportType: payload.report_type || "general",
        ext,
      });

    if (autoDownload) {
      // ✅ MEJORADO: JSON con formato más legible
      const formattedJson = JSON.stringify(json, null, 2);
      const blob = new Blob([formattedJson], {
        type: "application/json;charset=utf-8",
      });
      
      const finalName = safeName.endsWith(".json") ? safeName : `${safeName}.json`;
      const downloadResult = triggerDownload(blob, finalName);
      
      if (!downloadResult.success) {
        throw new Error(`JSON download failed: ${downloadResult.error}`);
      }
    }

    console.log(`[ReportService] ✅ JSON export completed successfully`);
    return { 
      ok: true, 
      filename: safeName, 
      format: 'json', 
      info: json, 
      type: 'json_fallback' 
    };
  } catch (jsonError) {
    console.error(`[ReportService] ❌ JSON export also failed:`, jsonError.message);
    throw new ApiClientError(`Export failed for format ${format}: ${jsonError.message}`, {
      status: 500,
      code: 500,
      detail: { format, originalError: jsonError.message }
    });
  }
};

/* =========================================
 * ✅ HELPERS DE ALTO NIVEL MEJORADOS v11.0
 * ========================================= */

/**
 * ✅ MEJORADA: Genera BR + Exporta con análisis complejo
 */
const generateAndExportBusinessReview = async (
  { user_id, gestor_id, periodo, options, exportFormat = "pdf", filename } = {},
  cfg = {}
) => {
  console.log(`[ReportService] 🚀 Complete Business Review workflow for gestor ${gestor_id}`);
  
  try {
    const report = await businessReview(
      { user_id, gestor_id, periodo, options },
      cfg
    );
    
    const exp = await exportReport(
      { 
        format: exportFormat, 
        filename,
        payload: { 
          report_type: "business_review",
          gestor_id,
          periodo
        }
      },
      cfg
    );
    
    console.log(`[ReportService] ✅ Complete Business Review workflow completed`);
    return { report, export: exp };
  } catch (error) {
    console.error(`[ReportService] ❌ Business Review workflow failed:`, error.message);
    throw error;
  }
};

/**
 * ✅ MEJORADA: Genera ES + Exporta con estado de integración
 */
const generateAndExportExecutiveSummary = async (
  { user_id, periodo, options, exportFormat = "pdf", filename } = {},
  cfg = {}
) => {
  console.log(`[ReportService] 🚀 Complete Executive Summary workflow for period ${periodo}`);
  
  try {
    const report = await executiveSummary({ user_id, periodo, options }, cfg);
    
    const exp = await exportReport(
      { 
        format: exportFormat, 
        filename,
        payload: { 
          report_type: "executive_summary",
          periodo
        }
      },
      cfg
    );
    
    console.log(`[ReportService] ✅ Complete Executive Summary workflow completed`);
    return { report, export: exp };
  } catch (error) {
    console.error(`[ReportService] ❌ Executive Summary workflow failed:`, error.message);
    throw error;
  }
};

/**
 * ✅ NUEVA: Genera análisis de desviaciones completo + Exporta
 */
const generateAndExportDeviationAnalysis = async (
  { periodo, options, exportFormat = "pdf", filename } = {},
  cfg = {}
) => {
  console.log(`[ReportService] 🚀 Complete Deviation Analysis workflow for period ${periodo}`);
  
  try {
    const report = await deviationAnalysis(periodo, options, cfg);
    
    const exp = await exportReport(
      { 
        format: exportFormat, 
        filename,
        payload: { 
          report_type: "deviation_analysis",
          periodo,
          enhanced: true
        }
      },
      cfg
    );
    
    console.log(`[ReportService] ✅ Complete Deviation Analysis workflow completed`);
    return { report, export: exp };
  } catch (error) {
    console.error(`[ReportService] ❌ Deviation Analysis workflow failed:`, error.message);
    throw error;
  }
};

/**
 * ✅ NUEVA: Procesa feedback del usuario sobre reportes
 */
const submitReportFeedback = async (feedbackData, cfg = {}) => {
  console.log(`[ReportService] 📝 Submitting report feedback`);
  
  try {
    const result = await feedbackAPI.process({
      ...feedbackData,
      category: 'report_generation',
      timestamp: new Date().toISOString()
    }, cfg);
    
    console.log(`[ReportService] ✅ Report feedback submitted successfully`);
    return result;
  } catch (error) {
    console.error(`[ReportService] ❌ Error submitting feedback:`, error.message);
    throw error;
  }
};

/* =========================================
 * ✅ EXPORTS ACTUALIZADOS v11.0
 * ========================================= */

const reportService = {
  // ✅ Builders / defaults actualizados
  DEFAULT_BR_OPTIONS,
  DEFAULT_ES_OPTIONS,
  DEFAULT_DEVIATION_OPTIONS,       // ✅ NUEVO
  DEFAULT_EXPORT_OPTIONS,
  buildBusinessReviewPayload,
  buildExecutiveSummaryPayload,
  buildDeviationAnalysisPayload,   // ✅ NUEVO
  buildFileName,

  // ✅ Core actualizado
  businessReview,
  executiveSummary,
  deviationAnalysis,
  gestorPerformanceReport,         // ✅ NUEVO
  getMeta,

  // ✅ Export/Download mejorado
  exportReport,
  generateAndExportBusinessReview,
  generateAndExportExecutiveSummary,
  generateAndExportDeviationAnalysis, // ✅ NUEVO

  // ✅ Feedback integration
  submitReportFeedback,            // ✅ NUEVO

  // ✅ Utilities
  triggerDownload,
  isBlobResponse,
  clean,
  assertPeriodo,
};

export default reportService;
export {
  reportService,
  // ✅ defaults + builders actualizados
  DEFAULT_BR_OPTIONS,
  DEFAULT_ES_OPTIONS,
  DEFAULT_DEVIATION_OPTIONS,
  DEFAULT_EXPORT_OPTIONS,
  buildBusinessReviewPayload,
  buildExecutiveSummaryPayload,
  buildDeviationAnalysisPayload,
  buildFileName,
  
  // ✅ core actualizado
  businessReview,
  executiveSummary,
  deviationAnalysis,
  gestorPerformanceReport,
  getMeta,
  
  // ✅ export mejorado
  exportReport,
  generateAndExportBusinessReview,
  generateAndExportExecutiveSummary,
  generateAndExportDeviationAnalysis,
  
  // ✅ nuevas funcionalidades
  submitReportFeedback,
  
  // ✅ utilities
  triggerDownload,
  isBlobResponse,
  clean,
  assertPeriodo,
};
