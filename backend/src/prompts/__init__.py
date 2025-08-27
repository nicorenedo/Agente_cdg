# backend/src/prompts/__init__.py

"""
Módulo de prompts para el sistema CDG de Banca March
=====================================================

Este módulo contiene todos los prompts especializados para:
- System prompts para agentes CDG
- User prompts para interacciones
- Templates para diferentes tipos de análisis

Estructura:
- system_prompts.py: Prompts principales para agentes CDG
- user_prompts.py: Templates para interacciones con usuarios
"""

# Importaciones principales para facilitar el uso
from .system_prompts import (
    FINANCIAL_ANALYST_SYSTEM_PROMPT,
    FINANCIAL_REPORT_SYSTEM_PROMPT,
    COMPARATIVE_ANALYSIS_SYSTEM_PROMPT,
    DEVIATION_ANALYSIS_SYSTEM_PROMPT
)

__all__ = [
    'FINANCIAL_ANALYST_SYSTEM_PROMPT',
    'FINANCIAL_REPORT_SYSTEM_PROMPT', 
    'COMPARATIVE_ANALYSIS_SYSTEM_PROMPT',
    'DEVIATION_ANALYSIS_SYSTEM_PROMPT'
]

__version__ = '1.0.0'
__author__ = 'Agente CDG Development Team'
