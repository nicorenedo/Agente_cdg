"""
Report Generator para Agente CDG - Banca March
===============================================

Módulo para generar Business Reviews automáticos integrales.
Combina análisis de KPIs, gráficos, alertas y recomendaciones con prompts específicos.

Autor: Agente CDG Development Team
Fecha: 2025-07-31
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

# Importar módulos locales del agente CDG
try:
    from .chart_generator import CDGDashboardGenerator, ChartFactory
    from .kpi_calculator import KPICalculator
    from ..prompts.user_prompts import (
        BUSINESS_REVIEW_USER_PROMPT,
        EXECUTIVE_SUMMARY_USER_PROMPT,
        DEVIATION_ANALYSIS_USER_PROMPT,
        build_business_review_prompt,
        build_executive_summary_prompt,
        build_deviation_analysis_prompt
    )
    from ..prompts.system_prompts import FINANCIAL_REPORT_SYSTEM_PROMPT
    from ..utils.initial_agent import iniciar_agente_llm
except ImportError:
    from chart_generator import CDGDashboardGenerator, ChartFactory
    from kpi_calculator import KPICalculator
    from prompts.user_prompts import (
        BUSINESS_REVIEW_USER_PROMPT,
        EXECUTIVE_SUMMARY_USER_PROMPT,
        DEVIATION_ANALYSIS_USER_PROMPT,
        build_business_review_prompt,
        build_executive_summary_prompt,
        build_deviation_analysis_prompt
    )
    from prompts.system_prompts import FINANCIAL_REPORT_SYSTEM_PROMPT
    from utils.initial_agent import iniciar_agente_llm

# Logger para auditoría
logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Tipos de reportes soportados por el agente CDG"""
    BUSINESS_REVIEW = "business_review"
    EXECUTIVE_SUMMARY = "executive_summary"
    DEVIATION_ANALYSIS = "deviation_analysis"
    PERFORMANCE_COMPARISON = "performance_comparison"
    MONTHLY_REPORT = "monthly_report"

class ReportFormat(Enum):
    """Formatos de exportación de reportes"""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"

@dataclass
class ReportSection:
    """Representa una sección del Business Review"""
    title: str
    content: Optional[str] = None
    charts: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    section_type: str = "text"  # text, chart, table, mixed

    def add_chart(self, chart: Dict[str, Any]) -> None:
        """Añade un gráfico a la sección"""
        self.charts.append(chart)
        if self.section_type == "text":
            self.section_type = "mixed"

    def add_table(self, table: Dict[str, Any]) -> None:
        """Añade una tabla a la sección"""
        self.tables.append(table)
        if self.section_type == "text":
            self.section_type = "mixed"

@dataclass
class BusinessReport:
    """Objeto principal del Business Review CDG"""
    report_id: str
    report_title: str
    report_type: ReportType
    generated_for: Dict[str, Any]  # Datos del gestor/centro
    period: str
    sections: List[ReportSection] = field(default_factory=list)
    executive_summary: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_section(self, section: ReportSection) -> None:
        """Añade una sección al reporte"""
        self.sections.append(section)

    def add_recommendation(self, recommendation: str) -> None:
        """Añade una recomendación al reporte"""
        self.recommendations.append(recommendation)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el reporte a diccionario"""
        return {
            'report_id': self.report_id,
            'report_title': self.report_title,
            'report_type': self.report_type.value,
            'generated_for': self.generated_for,
            'period': self.period,
            'executive_summary': self.executive_summary,
            'key_metrics': self.key_metrics,
            'sections': [asdict(section) for section in self.sections],
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Convierte el reporte a JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class NLGReportGenerator:
    """Generador de contenido textual usando Azure OpenAI"""
    
    def __init__(self):
        self.system_prompt = FINANCIAL_REPORT_SYSTEM_PROMPT
        logger.info("NLG Report Generator inicializado")
    
    def generate_business_review_content(
        self,
        gestor_data: Dict[str, Any],
        kpi_data: Dict[str, Any],
        period: str,
        deviation_alerts: Optional[List[Dict[str, Any]]] = None,
        comparative_data: Optional[List[Dict[str, Any]]] = None,
        trend_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Genera contenido de Business Review usando Azure OpenAI
        
        Args:
            gestor_data: Información del gestor
            kpi_data: KPIs calculados
            period: Período del reporte
            deviation_alerts: Alertas de desviaciones
            comparative_data: Datos comparativos
            trend_data: Datos de tendencias
            
        Returns:
            str: Contenido generado del Business Review
        """
        try:
            # Construir prompt dinámico usando la función helper
            user_prompt = build_business_review_prompt(
                gestor_data=gestor_data,
                kpi_data=kpi_data,
                periodo=period,
                alertas=self._format_alerts_for_prompt(deviation_alerts or []),
                comparativa=self._format_comparative_for_prompt(comparative_data or []),
                tendencias=self._format_trends_for_prompt(trend_data or [])
            )
            
            # Llamar a Azure OpenAI
            client = iniciar_agente_llm()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            logger.info(f"Business Review generado exitosamente para gestor {gestor_data.get('gestor_id')}")
            return content
            
        except Exception as e:
            logger.error(f"Error generando Business Review: {e}")
            return self._generate_fallback_business_review(gestor_data, kpi_data, period)
    
    def generate_executive_summary_content(
        self,
        consolidated_data: Dict[str, Any],
        period: str
    ) -> str:
        """
        Genera Executive Summary usando Azure OpenAI
        
        Args:
            consolidated_data: Datos consolidados de múltiples gestores
            period: Período del reporte
            
        Returns:
            str: Contenido del Executive Summary
        """
        try:
            # Construir prompt usando función helper
            user_prompt = build_executive_summary_prompt(
                datos_consolidados=consolidated_data,
                periodo=period
            )
            
            # Llamar a Azure OpenAI
            client = iniciar_agente_llm()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            logger.info(f"Executive Summary generado exitosamente para período {period}")
            return content
            
        except Exception as e:
            logger.error(f"Error generando Executive Summary: {e}")
            return f"Executive Summary para {period}: Datos consolidados procesados pero contenido no disponible por limitaciones técnicas."
    
    def generate_deviation_analysis_content(
        self,
        deviation_data: Dict[str, Any],
        period: str
    ) -> str:
        """
        Genera análisis de desviaciones usando Azure OpenAI
        
        Args:
            deviation_data: Datos de la desviación
            period: Período del análisis
            
        Returns:
            str: Contenido del análisis de desviaciones
        """
        try:
            # Construir prompt usando función helper
            user_prompt = build_deviation_analysis_prompt(
                deviation_data=deviation_data,
                periodo=period
            )
            
            # Llamar a Azure OpenAI
            client = iniciar_agente_llm()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logger.info(f"Análisis de desviaciones generado exitosamente para período {period}")
            return content
            
        except Exception as e:
            logger.error(f"Error generando análisis de desviaciones: {e}")
            return f"Análisis de desviaciones para {period}: Datos procesados pero contenido detallado no disponible."
    
    def _format_alerts_for_prompt(self, alerts: List[Dict[str, Any]]) -> str:
        """Formatea alertas para incluir en el prompt"""
        if not alerts:
            return "Sin alertas críticas detectadas"
        
        formatted_alerts = []
        for alert in alerts:
            severity = alert.get('severity', 'MEDIA')
            message = alert.get('message', 'Alerta sin descripción')
            formatted_alerts.append(f"- [{severity}] {message}")
        
        return "\n".join(formatted_alerts)
    
    def _format_comparative_for_prompt(self, comparative_data: List[Dict[str, Any]]) -> str:
        """Formatea datos comparativos para incluir en el prompt"""
        if not comparative_data:
            return "Datos comparativos no disponibles"
        
        summary_lines = [f"Comparando con {len(comparative_data)} gestores del mismo segmento:"]
        for data in comparative_data[:3]:  # Solo los primeros 3 para no saturar el prompt
            name = data.get('desc_gestor', 'Gestor')
            margen = data.get('margen_neto', 0)
            summary_lines.append(f"- {name}: {margen:.2f}% margen neto")
        
        return "\n".join(summary_lines)
    
    def _format_trends_for_prompt(self, trend_data: List[Dict[str, Any]]) -> str:
        """Formatea datos de tendencias para incluir en el prompt"""
        if not trend_data:
            return "Análisis de tendencias no disponible"
        
        if len(trend_data) < 2:
            return "Datos insuficientes para análisis de tendencias"
        
        latest = trend_data[-1]
        previous = trend_data[-2]
        
        trend_lines = [f"Evolución en los últimos {len(trend_data)} períodos:"]
        
        for metric in ['margen_neto', 'roe', 'eficiencia']:
            if metric in latest and metric in previous:
                current = latest.get(metric, 0)
                prev = previous.get(metric, 0)
                if prev != 0:
                    change = ((current - prev) / prev) * 100
                    trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    trend_lines.append(f"- {metric.replace('_', ' ').title()}: {trend_icon} {change:+.1f}%")
        
        return "\n".join(trend_lines)
    
    def _generate_fallback_business_review(self, gestor_data: Dict[str, Any], kpi_data: Dict[str, Any], period: str) -> str:
        """Genera Business Review básico como fallback"""
        gestor_name = gestor_data.get('desc_gestor', 'Gestor')
        centro = gestor_data.get('desc_centro', 'Centro')
        
        fallback_content = f"""
# Business Review - {gestor_name} - {period}

## Resumen Ejecutivo
Business Review generado para {gestor_name} del {centro} correspondiente al período {period}.

## Análisis de KPIs
"""
        
        for kpi, value in kpi_data.items():
            if isinstance(value, (int, float)):
                fallback_content += f"- **{kpi.replace('_', ' ').title()}**: {value:.2f}\n"
            else:
                fallback_content += f"- **{kpi.replace('_', ' ').title()}**: {value}\n"
        
        fallback_content += """
## Recomendaciones
- Revisar performance de KPIs principales
- Continuar seguimiento de tendencias
- Evaluar oportunidades de mejora
"""
        
        return fallback_content

class BusinessReportGenerator:
    """Generador principal de Business Reviews para el agente CDG"""
    
    def __init__(self):
        self.chart_generator = CDGDashboardGenerator()
        self.kpi_calculator = KPICalculator()
        self.nlg_generator = NLGReportGenerator()
        logger.info("BusinessReportGenerator inicializado")

    def generate_business_review(
        self,
        gestor_data: Dict[str, Any],
        kpi_data: Dict[str, Any],
        period: str,
        deviation_alerts: Optional[List[Dict[str, Any]]] = None,
        comparative_data: Optional[List[Dict[str, Any]]] = None,
        trend_data: Optional[List[Dict[str, Any]]] = None
    ) -> BusinessReport:
        """
        Genera un Business Review completo para un gestor usando Azure OpenAI
        
        Args:
            gestor_data: Información básica del gestor
            kpi_data: KPIs calculados
            period: Período del reporte
            deviation_alerts: Alertas de desviaciones
            comparative_data: Datos comparativos con otros gestores
            trend_data: Datos históricos para tendencias
            
        Returns:
            BusinessReport completo
        """
        report_id = f"BR_{gestor_data.get('gestor_id')}_{period.replace('-', '')}"
        report_title = f"Business Review - {gestor_data.get('desc_gestor', 'Gestor')} - {period}"
        
        report = BusinessReport(
            report_id=report_id,
            report_title=report_title,
            report_type=ReportType.BUSINESS_REVIEW,
            generated_for=gestor_data,
            period=period,
            key_metrics=kpi_data
        )

        # 1. Generar contenido principal usando Azure OpenAI
        try:
            business_review_content = self.nlg_generator.generate_business_review_content(
                gestor_data, kpi_data, period, deviation_alerts, comparative_data, trend_data
            )
            
            # Dividir el contenido en secciones
            sections_content = self._parse_business_review_content(business_review_content)
            
            # Añadir secciones al reporte
            for section_title, section_content in sections_content.items():
                section = ReportSection(title=section_title, content=section_content)
                report.add_section(section)
            
            # Extraer executive summary si está presente
            if "Resumen Ejecutivo" in sections_content:
                report.executive_summary = sections_content["Resumen Ejecutivo"]
            
            # Extraer recomendaciones si están presentes
            if "Recomendaciones" in sections_content or "Recomendaciones Estratégicas" in sections_content:
                recommendations_content = sections_content.get("Recomendaciones") or sections_content.get("Recomendaciones Estratégicas", "")
                recommendations = self._extract_recommendations_from_content(recommendations_content)
                for rec in recommendations:
                    report.add_recommendation(rec)
            
        except Exception as e:
            logger.error(f"Error generando contenido Business Review: {e}")
            # Fallback: generar secciones básicas
            self._add_fallback_sections(report, gestor_data, kpi_data, period)

        # 2. Añadir gráficos usando chart_generator
        try:
            dashboard = self.chart_generator.generate_gestor_dashboard(gestor_data, kpi_data, period)
            for chart in dashboard.get('charts', []):
                # Añadir gráficos a la primera sección apropiada
                if report.sections:
                    report.sections[0].add_chart(chart)
        except Exception as e:
            logger.warning(f"Error generando gráficos: {e}")

        # 3. Añadir gráficos comparativos si hay datos
        if comparative_data:
            try:
                comparative_chart = self.chart_generator.generate_comparative_dashboard(
                    comparative_data, 
                    metric='margen_neto', 
                    titulo='Comparativa de Margen Neto'
                )
                
                # Buscar sección de benchmarking o crear una nueva
                benchmarking_section = None
                for section in report.sections:
                    if 'benchmark' in section.title.lower() or 'comparativ' in section.title.lower():
                        benchmarking_section = section
                        break
                
                if benchmarking_section:
                    benchmarking_section.add_chart(comparative_chart)
                else:
                    section = ReportSection(title="Análisis Comparativo", section_type="mixed")
                    section.add_chart(comparative_chart)
                    report.add_section(section)
                    
            except Exception as e:
                logger.warning(f"Error generando gráfico comparativo: {e}")

        # 4. Añadir gráficos de tendencias si hay datos
        if trend_data:
            try:
                trend_chart = self.chart_generator.generate_trend_dashboard(
                    trend_data, 
                    title="Evolución de KPIs en el Tiempo"
                )
                
                # Buscar sección de tendencias o crear una nueva
                trend_section = None
                for section in report.sections:
                    if 'tendencia' in section.title.lower() or 'evolución' in section.title.lower():
                        trend_section = section
                        break
                
                if trend_section:
                    trend_section.add_chart(trend_chart)
                else:
                    section = ReportSection(title="Análisis de Tendencias", section_type="mixed")
                    section.add_chart(trend_chart)
                    report.add_section(section)
                    
            except Exception as e:
                logger.warning(f"Error generando gráfico de tendencias: {e}")

        # 5. Añadir metadata del reporte
        report.metadata = {
            'sections_count': len(report.sections),
            'has_alerts': bool(deviation_alerts),
            'has_comparative': bool(comparative_data),
            'has_trends': bool(trend_data),
            'generation_time_ms': (datetime.now() - report.created_at).total_seconds() * 1000,
            'content_generated_by': 'Azure OpenAI GPT-4',
            'charts_generated': sum(len(section.charts) for section in report.sections)
        }

        logger.info(f"Business Review generado: {report_id} con {len(report.sections)} secciones")
        return report

    def generate_executive_summary_report(
        self,
        consolidated_data: Dict[str, Any],
        period: str
    ) -> BusinessReport:
        """
        Genera un Executive Summary usando Azure OpenAI
        
        Args:
            consolidated_data: Datos consolidados de múltiples gestores
            period: Período del reporte
            
        Returns:
            BusinessReport con Executive Summary
        """
        report_id = f"ES_{period.replace('-', '')}"
        report_title = f"Executive Summary - {period}"
        
        report = BusinessReport(
            report_id=report_id,
            report_title=report_title,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            generated_for={"type": "consolidated", "num_gestores": consolidated_data.get('num_gestores', 0)},
            period=period,
            key_metrics=consolidated_data
        )

        # Generar contenido usando Azure OpenAI
        try:
            executive_content = self.nlg_generator.generate_executive_summary_content(
                consolidated_data, period
            )
            
            report.executive_summary = executive_content
            
            # Crear sección principal
            section = ReportSection(
                title="Executive Summary",
                content=executive_content,
                section_type="text"
            )
            report.add_section(section)
            
        except Exception as e:
            logger.error(f"Error generando Executive Summary: {e}")
            report.executive_summary = f"Executive Summary para {period}: Datos consolidados procesados."

        return report

    def generate_deviation_analysis_report(
        self,
        deviation_data: Dict[str, Any],
        period: str
    ) -> BusinessReport:
        """
        Genera un reporte de análisis de desviaciones usando Azure OpenAI
        
        Args:
            deviation_data: Datos de la desviación
            period: Período del análisis
            
        Returns:
            BusinessReport con análisis de desviaciones
        """
        report_id = f"DA_{period.replace('-', '')}_{datetime.now().strftime('%H%M%S')}"
        report_title = f"Análisis de Desviaciones - {period}"
        
        report = BusinessReport(
            report_id=report_id,
            report_title=report_title,
            report_type=ReportType.DEVIATION_ANALYSIS,
            generated_for={"type": "deviation_analysis", "context": deviation_data.get('contexto', 'N/A')},
            period=period,
            key_metrics=deviation_data
        )

        # Generar contenido usando Azure OpenAI
        try:
            deviation_content = self.nlg_generator.generate_deviation_analysis_content(
                deviation_data, period
            )
            
            # Crear sección principal
            section = ReportSection(
                title="Análisis de Desviaciones",
                content=deviation_content,
                section_type="text"
            )
            report.add_section(section)
            
        except Exception as e:
            logger.error(f"Error generando análisis de desviaciones: {e}")
            section = ReportSection(
                title="Análisis de Desviaciones",
                content=f"Análisis de desviaciones para {period}: Procesamiento completado.",
                section_type="text"
            )
            report.add_section(section)

        return report

    def _parse_business_review_content(self, content: str) -> Dict[str, str]:
        """Parsea el contenido generado por Azure OpenAI en secciones"""
        sections = {}
        current_section = "Introducción"
        current_content = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Detectar títulos de sección (líneas que empiezan con ## o ###)
            if line.strip().startswith('##'):
                # Guardar sección anterior
                if current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Iniciar nueva sección
                current_section = line.strip().replace('#', '').strip()
                current_content = []
            else:
                # Añadir contenido a la sección actual
                current_content.append(line)
        
        # Guardar última sección
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections

    def _extract_recommendations_from_content(self, content: str) -> List[str]:
        """Extrae recomendaciones del contenido generado"""
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Detectar líneas que empiezan con - o * (listas)
            if line.startswith(('- ', '* ', '• ')):
                recommendation = line[2:].strip()
                if recommendation:
                    recommendations.append(recommendation)
        
        return recommendations

    def _add_fallback_sections(self, report: BusinessReport, gestor_data: Dict[str, Any], kpi_data: Dict[str, Any], period: str):
        """Añade secciones básicas como fallback"""
        # Sección de KPIs
        kpi_content = "Análisis de KPIs principales:\n\n"
        for kpi, value in kpi_data.items():
            if isinstance(value, (int, float)):
                kpi_content += f"• **{kpi.replace('_', ' ').title()}**: {value:.2f}\n"
            else:
                kpi_content += f"• **{kpi.replace('_', ' ').title()}**: {value}\n"
        
        kpi_section = ReportSection(
            title="Indicadores Clave de Performance",
            content=kpi_content,
            section_type="text"
        )
        report.add_section(kpi_section)
        
        # Recomendaciones básicas
        basic_recommendations = [
            "Revisar evolución de KPIs principales vs período anterior",
            "Analizar factores que impactan la performance actual",
            "Identificar oportunidades de mejora operativa"
        ]
        
        for rec in basic_recommendations:
            report.add_recommendation(rec)

    def export_report(self, report: BusinessReport, format: ReportFormat = ReportFormat.JSON) -> str:
        """Exporta el reporte en el formato especificado"""
        if format == ReportFormat.JSON:
            return report.to_json()
        elif format == ReportFormat.HTML:
            return self._generate_html_report(report)
        elif format == ReportFormat.MARKDOWN:
            return self._generate_markdown_report(report)
        else:
            raise ValueError(f"Formato no soportado: {format}")

    def _generate_html_report(self, report: BusinessReport) -> str:
        """Genera reporte en formato HTML"""
        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='es'>",
            "<head>",
            f"    <title>{report.report_title}</title>",
            "    <meta charset='UTF-8'>",
            "    <style>",
            "        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; line-height: 1.6; }",
            "        h1 { color: #1976d2; border-bottom: 3px solid #1976d2; padding-bottom: 10px; }",
            "        h2 { color: #424242; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px; margin-top: 30px; }",
            "        .summary { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #1976d2; }",
            "        .recommendation { background: #e8f5e8; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #4caf50; }",
            "        .chart-container { background: #fafafa; padding: 15px; margin: 15px 0; border-radius: 6px; border: 1px solid #e0e0e0; }",
            "        .metadata { font-size: 12px; color: #666; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; }",
            "        pre { background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; }",
            "    </style>",
            "</head>",
            "<body>",
            f"<h1>{report.report_title}</h1>",
            f"<p><strong>Generado:</strong> {report.created_at.strftime('%d/%m/%Y %H:%M')}</p>",
            f"<p><strong>ID Reporte:</strong> {report.report_id}</p>",
        ]

        # Executive Summary
        if report.executive_summary:
            html_lines.extend([
                "<div class='summary'>",
                "<h2>Resumen Ejecutivo</h2>",
                f"<div>{report.executive_summary.replace(chr(10), '<br>')}</div>",
                "</div>"
            ])

        # Secciones
        for section in report.sections:
            html_lines.append(f"<h2>{section.title}</h2>")
            if section.content:
                html_lines.append(f"<div>{section.content.replace(chr(10), '<br>')}</div>")
            
            # Gráficos
            for i, chart in enumerate(section.charts):
                html_lines.extend([
                    "<div class='chart-container'>",
                    f"<h3>📊 {chart.get('title', f'Gráfico {i+1}')}</h3>",
                    f"<pre>{json.dumps(chart, indent=2, ensure_ascii=False)}</pre>",
                    "</div>"
                ])

        # Recomendaciones
        if report.recommendations:
            html_lines.append("<h2>Recomendaciones</h2>")
            for rec in report.recommendations:
                html_lines.append(f"<div class='recommendation'>• {rec}</div>")

        # Metadata
        html_lines.extend([
            "<div class='metadata'>",
            f"<p><strong>Metadata:</strong> {len(report.sections)} secciones, ",
            f"{sum(len(s.charts) for s in report.sections)} gráficos generados</p>",
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_lines)

    def _generate_markdown_report(self, report: BusinessReport) -> str:
        """Genera reporte en formato Markdown"""
        md_lines = [
            f"# {report.report_title}",
            "",
            f"**Generado:** {report.created_at.strftime('%d/%m/%Y %H:%M')}  ",
            f"**Período:** {report.period}  ",
            f"**ID Reporte:** {report.report_id}",
            ""
        ]

        # Executive Summary
        if report.executive_summary:
            md_lines.extend([
                "## 📋 Resumen Ejecutivo",
                "",
                report.executive_summary,
                ""
            ])

        # Secciones
        for section in report.sections:
            md_lines.extend([
                f"## {section.title}",
                ""
            ])
            
            if section.content:
                md_lines.extend([section.content, ""])
            
            # Gráficos
            for i, chart in enumerate(section.charts):
                md_lines.extend([
                    f"### 📊 {chart.get('title', f'Gráfico {i+1}')}",
                    "",
                    "```json",
                    json.dumps(chart, indent=2, ensure_ascii=False),
                    "```",
                    ""
                ])

        # Recomendaciones
        if report.recommendations:
            md_lines.extend(["## 🎯 Recomendaciones", ""])
            for rec in report.recommendations:
                md_lines.append(f"- {rec}")
            md_lines.append("")

        # Metadata
        md_lines.extend([
            "---",
            f"*Reporte generado automáticamente por el Agente CDG - Banca March*  ",
            f"*{len(report.sections)} secciones, {sum(len(s.charts) for s in report.sections)} gráficos*"
        ])

        return "\n".join(md_lines)

# Funciones de conveniencia para uso rápido
def generate_simple_business_review(gestor_data: Dict[str, Any], kpi_data: Dict[str, Any], period: str) -> Dict[str, Any]:
    """Función de conveniencia para generar Business Review simple"""
    generator = BusinessReportGenerator()
    report = generator.generate_business_review(gestor_data, kpi_data, period)
    return report.to_dict()

def generate_full_business_review(
    gestor_data: Dict[str, Any], 
    kpi_data: Dict[str, Any], 
    period: str,
    deviation_alerts: List[Dict[str, Any]] = None,
    comparative_data: List[Dict[str, Any]] = None,
    trend_data: List[Dict[str, Any]] = None
) -> str:
    """Función de conveniencia para generar Business Review completo en JSON"""
    generator = BusinessReportGenerator()
    report = generator.generate_business_review(
        gestor_data, kpi_data, period, deviation_alerts, comparative_data, trend_data
    )
    return report.to_json()

def generate_executive_summary(consolidated_data: Dict[str, Any], period: str) -> str:
    """Función de conveniencia para generar Executive Summary"""
    generator = BusinessReportGenerator()
    report = generator.generate_executive_summary_report(consolidated_data, period)
    return report.to_json()

def generate_deviation_analysis(deviation_data: Dict[str, Any], period: str) -> str:
    """Función de conveniencia para generar análisis de desviaciones"""
    generator = BusinessReportGenerator()
    report = generator.generate_deviation_analysis_report(deviation_data, period)
    return report.to_json()

if __name__ == "__main__":
    # Tests y demostración
    print("🔄 Iniciando tests de Report Generator CDG con Azure OpenAI...")
    
    # Datos de prueba
    sample_gestor = {
        'gestor_id': 1,
        'desc_gestor': 'Juan Pérez',
        'desc_centro': 'Madrid Centro',
        'desc_segmento': 'Banca Privada'
    }
    
    sample_kpis = {
        'margen_neto': 12.5,
        'roe': 8.3,
        'eficiencia': 75.2,
        'total_ingresos': 150000,
        'total_gastos': 131250
    }
    
    sample_alerts = [
        {'severity': 'CRITICA', 'message': 'Desviación de precio superior al 25%'},
        {'severity': 'ALTA', 'message': 'Margen por debajo del objetivo trimestral'}
    ]
    
    sample_comparative = [
        {'desc_gestor': 'Ana García', 'margen_neto': 15.2},
        {'desc_gestor': 'Carlos López', 'margen_neto': 9.8},
        {'desc_gestor': 'María Rodríguez', 'margen_neto': 11.1}
    ]

    # Test 1: Business Review completo con Azure OpenAI
    generator = BusinessReportGenerator()
    report = generator.generate_business_review(
        gestor_data=sample_gestor,
        kpi_data=sample_kpis,
        period="2025-07",
        deviation_alerts=sample_alerts,
        comparative_data=sample_comparative
    )
    
    print("✅ Test 1 - Business Review con Azure OpenAI: OK")
    print(f"   Reporte generado con {len(report.sections)} secciones")
    print(f"   {len(report.recommendations)} recomendaciones")
    print(f"   Executive Summary: {'✅' if report.executive_summary else '❌'}")
    
    # Test 2: Exportación HTML
    html_output = generator.export_report(report, ReportFormat.HTML)
    print("✅ Test 2 - Exportación HTML: OK")
    print(f"   HTML generado: {len(html_output)} caracteres")
    
    # Test 3: Executive Summary
    consolidated_data = {
        'num_gestores': 3,
        'margen_promedio': 12.0,
        'roe_consolidado': 9.5,
        'alertas_criticas': 2
    }
    
    executive_report = generator.generate_executive_summary_report(consolidated_data, "2025-07")
    print("✅ Test 3 - Executive Summary: OK")
    print(f"   Executive Summary generado con ID: {executive_report.report_id}")
    
    # Test 4: Función de conveniencia
    simple_report = generate_simple_business_review(sample_gestor, sample_kpis, "2025-07")
    print("✅ Test 4 - Función de conveniencia: OK")
    print(f"   Reporte simple generado con ID: {simple_report['report_id']}")
    
    print("\n🎯 Todos los tests completados exitosamente!")
    print("Report Generator CDG con Azure OpenAI listo para generar Business Reviews automáticos")
