"""
Construye evals/datasets/s88_battery.json y evals/datasets/s77_battery.json
a partir del ground_truth.json ya extraído.
"""
import json, os

with open('evals/datasets/ground_truth.json', encoding='utf-8') as f:
    gt = json.load(f)

ent = gt['entidad_abr_2026']
mom_ent = gt['mom_entidad']
mom_g1 = gt['mom_gestor_1']
g1 = gt['gestor_1_kpis']
gestores = gt['gestores_abr_2026']
centros = gt['centros_abr_2026']
productos = gt['productos_abr_2026']

# Top gestor por ingresos
top_gestor = gestores[0]['nombre'] if gestores else "Antonio Rodríguez García"
# Gestor con menor margen (bottom)
bottom_gestor = min(gestores, key=lambda x: x['margen_directo_pct'])['nombre'] if gestores else ""

# ─────────────────────────────────────────────────────────────
# BATERÍA S88 — 21 preguntas cualitativas
# ─────────────────────────────────────────────────────────────
s88 = [
    # ─── GRUPO A: CDGAgent (8 preguntas) ─────────────────────
    {
        "id": "A1_resumen",
        "grupo": "CDG",
        "pregunta": "Dame un resumen ejecutivo del mes de abril. ¿Cómo estamos?",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_contain_values": {"ingresos_entidad": ent['ingresos'], "tolerancia_pct": 5},
            "must_mention": ["margen", "contratos", "ingresos"],
            "must_not_contain": ["no tengo datos", "no puedo", "no dispongo"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": f"Cita ingresos (~€{ent['ingresos']/1000:.0f}k), contratos ({ent['contratos_activos']}), margen (~{ent['margen_neto_pct']}%)"},
            "contextualizacion": {"peso": 0.20, "criterio": "Compara con mes anterior o da tendencia"},
            "accionabilidad": {"peso": 0.25, "criterio": "Al menos 1 punto de atención o recomendación"},
            "tono": {"peso": 0.15, "criterio": "Ejecutivo, técnico bancario, español"},
            "fluidez": {"peso": 0.15, "criterio": "Lectura fluida, bien estructurada"}
        }
    },
    {
        "id": "A2_gestores_preocupantes",
        "grupo": "CDG",
        "pregunta": "¿Qué gestores deberían preocuparnos este mes y por qué?",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_contain_values": {},
            "must_mention": ["margen", "gestor"],
            "must_not_contain": ["no tengo datos", "no puedo"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Cita al menos 2 gestores con nombre real y cifras"},
            "contextualizacion": {"peso": 0.25, "criterio": "Explica POR QUÉ son preocupantes (MoM negativo, margen bajo)"},
            "accionabilidad": {"peso": 0.20, "criterio": "Sugiere acción para cada gestor problemático"},
            "tono": {"peso": 0.15, "criterio": "Ejecutivo, analítico"},
            "fluidez": {"peso": 0.15, "criterio": "Bien estructurado, fácil de seguir"}
        }
    },
    {
        "id": "A3_productos",
        "grupo": "CDG",
        "pregunta": "¿Cuál es la contribución de cada producto a nuestros ingresos y dónde están las oportunidades?",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_mention": ["hipotecario", "depósito", "fondo", "FRV"],
            "must_not_contain": ["no tengo datos"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": "Cita ingresos por producto con cifras cercanas a BD"},
            "contextualizacion": {"peso": 0.20, "criterio": "Compara márgenes entre productos"},
            "accionabilidad": {"peso": 0.25, "criterio": "Identifica oportunidades concretas por producto"},
            "tono": {"peso": 0.10, "criterio": "Ejecutivo"},
            "fluidez": {"peso": 0.15, "criterio": "Bien estructurado"}
        }
    },
    {
        "id": "A4_centros",
        "grupo": "CDG",
        "pregunta": "¿Qué diferencias hay entre nuestras oficinas? ¿Cuál está rindiendo mejor y cuál peor?",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_mention": ["Madrid", "Palma", "Barcelona", "Málaga", "Bilbao"],
            "must_not_contain": ["no tengo datos"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": "Cita cifras por centro, identifica mejor y peor correctamente"},
            "contextualizacion": {"peso": 0.25, "criterio": "Explica causas de diferencias (nº gestores, mix producto)"},
            "accionabilidad": {"peso": 0.20, "criterio": "Sugiere acción para el centro peor"},
            "tono": {"peso": 0.10, "criterio": "Ejecutivo"},
            "fluidez": {"peso": 0.15, "criterio": "Tabla comparativa o estructura clara"}
        }
    },
    {
        "id": "A5_alerta_deterioro",
        "grupo": "CDG",
        "pregunta": "¿Hay algún gestor o centro que esté mostrando señales de deterioro en los últimos meses?",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_mention": ["gestor"],
            "must_not_contain": ["no tengo datos", "no puedo"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Identifica gestores con MoM negativo con cifras"},
            "contextualizacion": {"peso": 0.30, "criterio": "Muestra tendencia de varios meses, no solo último"},
            "accionabilidad": {"peso": 0.20, "criterio": "Sugiere seguimiento o acción"},
            "tono": {"peso": 0.10, "criterio": "Tono de alerta profesional"},
            "fluidez": {"peso": 0.15, "criterio": "Bien estructurado"}
        }
    },
    {
        "id": "A6_estrategia",
        "grupo": "CDG",
        "pregunta": "Si tuvieras que priorizar una acción comercial este mes para mejorar el margen, ¿cuál sería?",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_mention": [],
            "must_not_contain": ["no tengo datos", "no puedo", "no dispongo de información"]
        },
        "s88_resultado_v1": {"score": None, "nota": "FAIL en S88 v1 — respuesta vacía sin herramientas. Fix en S89-F2."},
        "evaluacion": {
            "precision_datos": {"peso": 0.20, "criterio": "Basa recomendación en datos reales (rankings, márgenes)"},
            "contextualizacion": {"peso": 0.20, "criterio": "Explica por qué esa acción y no otra"},
            "accionabilidad": {"peso": 0.35, "criterio": "Acción CONCRETA y ejecutable, no genérica"},
            "tono": {"peso": 0.10, "criterio": "Estratégico, no descriptivo"},
            "fluidez": {"peso": 0.15, "criterio": "Directo al punto"}
        }
    },
    {
        "id": "A7_comparativa_mom",
        "grupo": "CDG",
        "pregunta": "¿Cómo ha evolucionado el banco entre marzo y abril? ¿Estamos mejorando o empeorando?",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_contain_values": {"variacion_mom": mom_ent['variacion_pct'], "tolerancia_pct": 10},
            "must_mention": ["marzo", "abril"],
            "must_not_contain": ["no tengo datos"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": f"Cita variación MoM correcta (~{mom_ent['variacion_pct']:+.1f}%) en ingresos"},
            "contextualizacion": {"peso": 0.30, "criterio": "Explica causas del cambio"},
            "accionabilidad": {"peso": 0.15, "criterio": "Indica si la tendencia es preocupante"},
            "tono": {"peso": 0.10, "criterio": "Ejecutivo"},
            "fluidez": {"peso": 0.15, "criterio": "Fluido"}
        }
    },
    {
        "id": "A8_gestor_nombre",
        "grupo": "CDG",
        "pregunta": "Dame los datos completos de Antonio Rodríguez García en abril",
        "endpoint": "/chat/message",
        "params": {"user_role": "control_gestion", "periodo": "2026-04"},
        "ground_truth": {
            "must_contain_values": {"ingresos_gestor1": g1['ingresos'], "tolerancia_pct": 5},
            "must_mention": ["Antonio", "Rodríguez", "Madrid"],
            "must_not_contain": ["no tengo acceso", "confidencial"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.35, "criterio": f"Cita ingresos ~€{g1['ingresos']/1000:.1f}k, contratos {g1['contratos']}, centro {g1['centro'][:6]}"},
            "contextualizacion": {"peso": 0.20, "criterio": "Compara con media o con mes anterior"},
            "accionabilidad": {"peso": 0.15, "criterio": "Identifica puntos fuertes o débiles del gestor"},
            "tono": {"peso": 0.15, "criterio": "Ejecutivo, completo"},
            "fluidez": {"peso": 0.15, "criterio": "Bien estructurado"}
        }
    },

    # ─── GRUPO B: GestorAgent (6 preguntas) ──────────────────
    {
        "id": "B1_estado",
        "grupo": "Gestor",
        "pregunta": "¿Cómo estoy este mes? Dame un resumen de mis resultados",
        "endpoint": "/chat/gestor",
        "params": {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        "ground_truth": {
            "must_mention": ["ingresos", "margen"],
            "must_not_contain": ["no tengo datos"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": f"Cita ingresos ~€{g1['ingresos']/1000:.1f}k, contratos {g1['contratos']}, margen ~{g1['margen_directo_pct']:.0f}%"},
            "contextualizacion": {"peso": 0.20, "criterio": "Compara con mes anterior o con media"},
            "accionabilidad": {"peso": 0.20, "criterio": "Indica qué va bien y qué necesita atención"},
            "tono": {"peso": 0.15, "criterio": "Personal, empático, segunda persona"},
            "fluidez": {"peso": 0.15, "criterio": "Natural, no robótico"}
        }
    },
    {
        "id": "B2_clientes",
        "grupo": "Gestor",
        "pregunta": "¿Cuáles son mis clientes más rentables y cuáles me preocupan?",
        "endpoint": "/chat/gestor",
        "params": {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        "ground_truth": {
            "must_mention": [],
            "must_not_contain": ["no tengo datos", "otros gestores"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": "Cita nombres reales de clientes con cifras"},
            "contextualizacion": {"peso": 0.20, "criterio": "Explica por qué son rentables o preocupantes"},
            "accionabilidad": {"peso": 0.25, "criterio": "Sugiere acción concreta por cliente"},
            "tono": {"peso": 0.15, "criterio": "Personal, directo"},
            "fluidez": {"peso": 0.10, "criterio": "Fluido"}
        }
    },
    {
        "id": "B3_evolucion",
        "grupo": "Gestor",
        "pregunta": "¿He mejorado o empeorado respecto al mes pasado? ¿Por qué?",
        "endpoint": "/chat/gestor",
        "params": {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        "ground_truth": {
            "must_contain_values": {"variacion_gestor1": mom_g1['variacion_pct'], "tolerancia_pct": 10},
            "must_mention": ["marzo", "abril"],
            "must_not_contain": ["103%", "no tengo datos"]
        },
        "s88_resultado_v1": {"score": None, "nota": "FAIL en S88 v1 — margen 103.45% (bug query MoM). Fix en S89-F1."},
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": f"Variación MoM ~{mom_g1['variacion_pct']:+.1f}%, margen SIEMPRE ≤100%"},
            "contextualizacion": {"peso": 0.30, "criterio": "Explica causa del cambio (producto, cliente, estacionalidad)"},
            "accionabilidad": {"peso": 0.15, "criterio": "Indica qué hacer si empeoró"},
            "tono": {"peso": 0.15, "criterio": "Empático pero directo"},
            "fluidez": {"peso": 0.10, "criterio": "Fluido"}
        }
    },
    {
        "id": "B4_accion",
        "grupo": "Gestor",
        "pregunta": "¿Qué debería hacer esta semana para mejorar mis resultados?",
        "endpoint": "/chat/gestor",
        "params": {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        "ground_truth": {
            "must_not_contain": ["no tengo datos", "no puedo"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.20, "criterio": "Basa en datos reales del gestor"},
            "contextualizacion": {"peso": 0.15, "criterio": "Conecta con su cartera actual"},
            "accionabilidad": {"peso": 0.40, "criterio": "Acción CONCRETA ejecutable esta semana"},
            "tono": {"peso": 0.15, "criterio": "Motivador, como un coach"},
            "fluidez": {"peso": 0.10, "criterio": "Directo"}
        }
    },
    {
        "id": "B5_producto",
        "grupo": "Gestor",
        "pregunta": "¿En qué producto debería enfocarme para crecer más?",
        "endpoint": "/chat/gestor",
        "params": {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        "ground_truth": {
            "must_mention": [],
            "must_not_contain": ["no tengo datos"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Compara ingresos/margen por producto del gestor"},
            "contextualizacion": {"peso": 0.25, "criterio": "Explica ventajas del producto recomendado"},
            "accionabilidad": {"peso": 0.25, "criterio": "Recomendación concreta con justificación"},
            "tono": {"peso": 0.15, "criterio": "Personal"},
            "fluidez": {"peso": 0.10, "criterio": "Fluido"}
        }
    },
    {
        "id": "B6_frustrado",
        "grupo": "Gestor",
        "pregunta": "Llevo dos meses bajando en ingresos y no entiendo por qué. Estoy preocupado.",
        "endpoint": "/chat/gestor",
        "params": {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        "ground_truth": {
            "must_not_contain": ["no tengo datos", "no me es posible"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.20, "criterio": f"Cita datos reales de la caída (MoM {mom_g1['variacion_pct']:+.1f}%)"},
            "contextualizacion": {"peso": 0.25, "criterio": "Identifica causa probable de la caída"},
            "accionabilidad": {"peso": 0.20, "criterio": "Plan de acción concreto"},
            "tono": {"peso": 0.25, "criterio": "EMPÁTICO primero, datos después. Reconoce preocupación."},
            "fluidez": {"peso": 0.10, "criterio": "Natural, humano"}
        }
    },

    # ─── GRUPO C: ForecastAgent (7 preguntas) ────────────────
    {
        "id": "C1_cierre_ejercicio",
        "grupo": "Forecast",
        "pregunta": "¿Cómo vamos a cerrar el ejercicio? Dame una proyección realista",
        "endpoint": "/forecast/chat",
        "params": {"user_role": "control_gestion", "periodo_base": "2026-04"},
        "ground_truth": {
            "must_mention": ["escenario", "base", "proyección"],
            "must_not_contain": ["811", "+26%"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Proyecta con cifras concretas en €"},
            "contextualizacion": {"peso": 0.25, "criterio": "Contextualiza con últimos 6 meses de histórico"},
            "accionabilidad": {"peso": 0.20, "criterio": "Indica qué hacer para mejorar la proyección"},
            "tono": {"peso": 0.15, "criterio": "Estratégico, ejecutivo"},
            "fluidez": {"peso": 0.15, "criterio": "Bien estructurado con escenarios"}
        }
    },
    {
        "id": "C2_bce_tipos",
        "grupo": "Forecast",
        "pregunta": "El BCE está considerando bajar tipos 25pb en junio. ¿Cómo nos afectaría?",
        "endpoint": "/forecast/chat",
        "params": {"user_role": "control_gestion", "periodo_base": "2026-04"},
        "ground_truth": {
            "must_mention": ["tipos", "hipotec"],
            "must_not_contain": []
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": "Cuantifica impacto en € o % sobre ingresos"},
            "contextualizacion": {"peso": 0.25, "criterio": "Explica mecanismo (tipos → hipotecas → captación)"},
            "accionabilidad": {"peso": 0.20, "criterio": "Sugiere acción ante bajada de tipos"},
            "tono": {"peso": 0.10, "criterio": "Estratégico"},
            "fluidez": {"peso": 0.15, "criterio": "Fluido"}
        }
    },
    {
        "id": "C3_captacion",
        "grupo": "Forecast",
        "pregunta": "Si lanzamos una campaña hipotecaria y conseguimos captar un 15% más de clientes nuevos, ¿qué impacto tendría en los próximos 6 meses?",
        "endpoint": "/forecast/chat",
        "params": {"user_role": "control_gestion", "periodo_base": "2026-04"},
        "ground_truth": {
            "must_mention": ["captación", "hipotec"],
            "must_not_contain": []
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.30, "criterio": "Cifras concretas de impacto en €"},
            "contextualizacion": {"peso": 0.25, "criterio": "Muestra impacto gradual mes a mes"},
            "accionabilidad": {"peso": 0.20, "criterio": "Indica si la campaña merece la pena"},
            "tono": {"peso": 0.10, "criterio": "Analítico"},
            "fluidez": {"peso": 0.15, "criterio": "Bien estructurado"}
        }
    },
    {
        "id": "C4_crisis_frv",
        "grupo": "Forecast",
        "pregunta": "¿Qué pasaría si hay una desaceleración económica y perdemos un 10% de los ingresos por FRV?",
        "endpoint": "/forecast/chat",
        "params": {"user_role": "control_gestion", "periodo_base": "2026-04"},
        "ground_truth": {
            "must_mention": ["FRV", "fondo"],
            "must_not_contain": []
        },
        "s88_resultado_v1": {"score": None, "nota": "PARTIAL en S88 v1 — FRV mapeado a captación general. Fix en S89-F3."},
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Cuantifica impacto en €"},
            "contextualizacion": {"peso": 0.30, "criterio": "Explica cómo mapea el shock al simulador"},
            "accionabilidad": {"peso": 0.20, "criterio": "Sugiere mitigación"},
            "tono": {"peso": 0.10, "criterio": "Analítico"},
            "fluidez": {"peso": 0.15, "criterio": "Claro"}
        }
    },
    {
        "id": "C5_escenarios",
        "grupo": "Forecast",
        "pregunta": "Explícame las diferencias entre el escenario pesimista y el optimista. ¿Qué las determina?",
        "endpoint": "/forecast/chat",
        "params": {"user_role": "control_gestion", "periodo_base": "2026-04"},
        "ground_truth": {
            "must_mention": ["pesimista", "optimista", "base"],
            "must_not_contain": ["811", "733"]
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Cita cifras de los 3 escenarios"},
            "contextualizacion": {"peso": 0.35, "criterio": "Explica QUÉ determina cada escenario (supuestos)"},
            "accionabilidad": {"peso": 0.15, "criterio": "Indica qué acciones acercan al optimista"},
            "tono": {"peso": 0.10, "criterio": "Didáctico"},
            "fluidez": {"peso": 0.15, "criterio": "Bien organizado"}
        }
    },
    {
        "id": "C6_macro",
        "grupo": "Forecast",
        "pregunta": "¿Cómo está el entorno macroeconómico y qué riesgos ve el modelo para nuestro negocio?",
        "endpoint": "/forecast/chat",
        "params": {"user_role": "control_gestion", "periodo_base": "2026-04"},
        "ground_truth": {
            "must_mention": ["tipos", "IPC"],
            "must_not_contain": []
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Cita tipos BCE e IPC reales"},
            "contextualizacion": {"peso": 0.30, "criterio": "Conecta macro con impacto en productos del banco"},
            "accionabilidad": {"peso": 0.20, "criterio": "Identifica riesgos concretos"},
            "tono": {"peso": 0.10, "criterio": "Estratégico, informado"},
            "fluidez": {"peso": 0.15, "criterio": "Fluido"}
        }
    },
    {
        "id": "C7_gestor_forecast",
        "grupo": "Forecast",
        "pregunta": "¿Voy a llegar a mis objetivos este trimestre?",
        "endpoint": "/forecast/chat",
        "params": {"user_role": "gestor", "gestor_id": "1", "periodo_base": "2026-04"},
        "ground_truth": {
            "must_mention": ["proyección"],
            "must_not_contain": []
        },
        "evaluacion": {
            "precision_datos": {"peso": 0.25, "criterio": "Proyecta cifras del gestor concreto"},
            "contextualizacion": {"peso": 0.25, "criterio": "Compara proyección con objetivo si lo conoce"},
            "accionabilidad": {"peso": 0.25, "criterio": "Indica qué hacer para llegar"},
            "tono": {"peso": 0.15, "criterio": "Personal, motivador"},
            "fluidez": {"peso": 0.10, "criterio": "Directo"}
        }
    }
]

# ─────────────────────────────────────────────────────────────
# BATERÍA S77 — Funcional (~48 tests reconstruidos)
# ─────────────────────────────────────────────────────────────

# Centros ordenados por ingresos para referencias
centros_list = sorted(centros.items(), key=lambda x: x[1]['ingresos'], reverse=True)
centro_top = centros_list[0][0] if centros_list else "MADRID-OFICINA PRINCIPAL"
centro_bot = centros_list[-1][0] if centros_list else "BARCELONA-BALMES"
centro_top_short = centro_top.split('-')[0].capitalize() if '-' in centro_top else centro_top
centro_bot_short = centro_bot.split('-')[0].capitalize() if '-' in centro_bot else centro_bot

def s77_test(tid, grupo, pregunta, endpoint, params, must_contain_values=None, must_mention=None, must_not_contain=None, nota=None):
    t = {
        "id": tid,
        "grupo": grupo,
        "tipo": "funcional",
        "pregunta": pregunta,
        "endpoint": endpoint,
        "params": params,
        "ground_truth": {
            "must_contain_values": must_contain_values or {},
            "must_mention": must_mention or [],
            "must_not_contain": must_not_contain or ["no tengo datos", "no puedo acceder"]
        }
    }
    if nota:
        t["nota"] = nota
    return t

s77 = [
    # ─── GRUPO A: CDGAgent Dirección (15 tests) ───────────────
    s77_test("S77_A01", "CDG",
        "Dame el resumen financiero de abril 2026. Ingresos, margen, contratos.",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"ingresos": ent['ingresos'], "tolerancia_pct": 5},
        must_mention=["ingresos", "margen", "contratos"]),

    s77_test("S77_A02", "CDG",
        "¿Cuántos contratos activos tiene el banco en abril?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"contratos": ent['contratos_activos'], "tolerancia_pct": 0},
        must_mention=["contratos", "351"]),

    s77_test("S77_A03", "CDG",
        "¿Cuál es el ROE del grupo este mes?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"margen": ent['margen_neto_pct'], "tolerancia_pct": 10},
        must_mention=["margen", "%"]),

    s77_test("S77_A04", "CDG",
        "¿Qué producto genera más ingresos para el banco en abril?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["Fondo", "FRV", "hipotecario"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A05", "CDG",
        "Dame el ranking de gestores por ingresos en abril 2026",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["Antonio", "Rodríguez"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A06", "CDG",
        "¿Cuántos gestores mejoraron sus ingresos respecto al mes anterior?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["mejora", "gestores"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A07", "CDG",
        "¿Hay desviaciones de precio importantes en algún producto?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["desviación", "precio"],
        must_not_contain=["sin alertas", "no hay"]),

    s77_test("S77_A08", "CDG",
        "¿Cómo está la oficina de Bilbao en abril?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"ingresos_bilbao": next((v['ingresos'] for k, v in centros.items() if "BILBAO" in k.upper()), 111045), "tolerancia_pct": 5},
        must_mention=["Bilbao"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A09", "CDG",
        "Compara los resultados de Madrid y Bilbao en abril. ¿Cuál está mejor?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["Madrid", "Bilbao"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A10", "CDG",
        "Dame los datos de Antonio Rodríguez García en abril",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"ingresos_g1": g1['ingresos'], "tolerancia_pct": 5},
        must_mention=["Antonio", "Rodríguez", "Madrid"],
        must_not_contain=["no tengo acceso", "confidencial"],
        nota="A10 fallaba en v1 (S77) — CDG consulta gestor por nombre → CONTEXTUAL_RESPONSE por bloqueo confidencialidad. Fix S78a."),

    s77_test("S77_A11", "CDG",
        "¿Cómo ha evolucionado la entidad de marzo a abril? ¿Subimos o bajamos?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"variacion_mom": mom_ent['variacion_pct'], "tolerancia_pct": 15},
        must_mention=["marzo", "abril"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A12", "CDG",
        "¿Hay algo que me deba preocupar este mes? ¿Hay alertas?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["gestor", "margen"],
        must_not_contain=["no puedo", "sin alertas"]),

    s77_test("S77_A13", "CDG",
        "Dame los ingresos de las 5 oficinas del banco en abril",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["Madrid", "Palma", "Barcelona", "Málaga", "Bilbao"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A14", "CDG",
        "¿Cuáles son los gestores con mejor margen directo en abril?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["margen", "gestor"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_A15", "CDG",
        "¿Cuántos clientes tiene el banco en total?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"n_clientes": ent['n_clientes'], "tolerancia_pct": 0},
        must_mention=["142", "clientes"],
        nota="No-regresion: 142 clientes siempre deben responder correctamente"),

    # ─── GRUPO B: GestorAgent (8 tests) ──────────────────────
    s77_test("S77_B01", "Gestor",
        "¿Cómo estoy este mes? Dame mis KPIs de abril",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_contain_values={"ingresos": g1['ingresos'], "tolerancia_pct": 5},
        must_mention=["ingresos", "margen"]),

    s77_test("S77_B02", "Gestor",
        "¿Por qué tengo tantos gastos? Explícame el desglose",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_mention=["gastos", "directos"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_B03", "Gestor",
        "¿Cuáles son mis clientes? Dame el listado con sus ingresos",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_mention=["cliente"],
        must_not_contain=["no tengo datos", "Cliente 91", "Cliente 1"],
        nota="B3 debe mostrar nombres reales de clientes (sin genéricos como 'Cliente 91')"),

    s77_test("S77_B04", "Gestor",
        "¿He mejorado o empeorado respecto a marzo?",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_contain_values={"variacion": mom_g1['variacion_pct'], "tolerancia_pct": 15},
        must_mention=["marzo", "abril"],
        must_not_contain=["103%", "no tengo datos"]),

    s77_test("S77_B05", "Gestor",
        "¿Cómo estoy comparado con mi centro? ¿Soy de los mejores o de los peores?",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_mention=["Madrid", "centro"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_B06", "Gestor",
        "¿Cuántos contratos gestiono y cómo se distribuyen por producto?",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_contain_values={"contratos": g1['contratos'], "tolerancia_pct": 0},
        must_mention=["contratos"],
        must_not_contain=["no tengo datos"]),

    s77_test("S77_B07", "Gestor",
        "¿Cuál es mi margen directo este mes?",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_contain_values={"margen": g1['margen_directo_pct'], "tolerancia_pct": 10},
        must_mention=["margen", "%"],
        must_not_contain=["103%"],
        nota="B7 debe mostrar margen correcto sin superar 100%"),

    s77_test("S77_B08", "Gestor",
        "¿Qué debería hacer para mejorar mis resultados esta semana?",
        "/chat/gestor", {"gestor_id": "1", "user_role": "gestor", "periodo": "2026-04"},
        must_mention=["acción", "cliente", "producto"],
        must_not_contain=["no puedo", "no tengo datos"]),

    # ─── GRUPO C: ForecastAgent Dirección (12 tests) ──────────
    s77_test("S77_C01", "Forecast",
        "¿Cuál es la proyección de ingresos para los próximos 6 meses?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["base", "pesimista", "optimista"],
        must_not_contain=["811", "+26%"]),

    s77_test("S77_C02", "Forecast",
        "Dame los tres escenarios para el cierre de año",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["pesimista", "optimista", "base"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C03", "Forecast",
        "¿Qué impacto tendría una subida de tipos del BCE de +75pb?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["tipos", "%"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C04", "Forecast",
        "Si captamos 20% más de clientes nuevos, ¿cómo cambia la proyección?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["captación", "%"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C05", "Forecast",
        "¿Cuál es el contexto macroeconómico actual? ¿Tipos BCE e IPC?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["tipos", "IPC", "BCE"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C06", "Forecast",
        "¿Cuál es la diferencia entre reducir gastos un 10% vs captar 10% más de clientes?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["gastos", "captación"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C07", "Forecast",
        "¿Qué recomendaciones hace el modelo para mejorar el escenario base?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["recomendación", "acción"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C08", "Forecast",
        "¿Cuál es el impacto combinado de una bajada de tipos -50pb Y una reducción de captación -20%?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["tipos", "captación", "%"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C09", "Forecast",
        "¿En qué meses del año hay más actividad? ¿Hay estacionalidad?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["estacionalidad", "meses"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C10", "Forecast",
        "Proyección entidad a 12 meses, dimensión Madrid",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["Madrid", "proyección"],
        must_not_contain=["no puedo"]),

    s77_test("S77_C11", "Forecast",
        "¿Cuánto hemos crecido respecto al año pasado?",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["crecimiento", "2025"],
        must_not_contain=["no puedo"],
        nota="C11 fallaba en v1 (S77) — YoY usaba forecast en lugar de datos históricos reales. Fix S78a: prompt con contexto banco joven."),

    s77_test("S77_C12", "Forecast",
        "Dame un resumen ejecutivo del mes de abril",
        "/forecast/chat", {"user_role": "control_gestion", "periodo_base": "2026-04"},
        must_mention=["resumen"],
        must_not_contain=["no puedo"],
        nota="No-regresion: la pregunta de resumen mensual debe redirigirse al CDGAgent, no responder como forecast"),

    # ─── GRUPO D: ForecastAgent Gestor (8 tests) ─────────────
    s77_test("S77_D01", "ForecastGestor",
        "¿Cómo veo el año que viene para mi cartera?",
        "/forecast/chat", {"user_role": "control_gestion", "gestor_id": "1", "periodo_base": "2026-04"},
        must_mention=["proyección", "escenario"],
        must_not_contain=["no puedo"]),

    s77_test("S77_D02", "ForecastGestor",
        "¿Ya supero los 40.000€ en algún escenario?",
        "/forecast/chat", {"user_role": "gestor", "gestor_id": "1", "periodo_base": "2026-04"},
        must_mention=["40", "escenario"],
        must_not_contain=["no puedo"],
        nota="D2: test específico — respuesta debe confirmar 'ya superas 40k en todos los escenarios' (actual €36k, pero proyección base >40k)"),

    s77_test("S77_D03", "ForecastGestor",
        "Dame mi proyección personal a 3 meses",
        "/forecast/chat", {"user_role": "gestor", "gestor_id": "1", "periodo_base": "2026-04"},
        must_mention=["base", "pesimista", "optimista"],
        must_not_contain=["no puedo"]),

    s77_test("S77_D04", "ForecastGestor",
        "¿Qué tengo que hacer para alcanzar el escenario optimista?",
        "/forecast/chat", {"user_role": "gestor", "gestor_id": "1", "periodo_base": "2026-04"},
        must_mention=["acción", "optimista"],
        must_not_contain=["no puedo"]),

    s77_test("S77_D05", "ForecastGestor",
        "¿En qué meses del año suelo tener más actividad?",
        "/forecast/chat", {"user_role": "gestor", "gestor_id": "1", "periodo_base": "2026-04"},
        must_mention=["meses"],
        must_not_contain=["no puedo"]),

    s77_test("S77_D06", "ForecastGestor",
        "Si captara 2 clientes nuevos con hipoteca, ¿cómo mejoraría mi proyección?",
        "/forecast/chat", {"user_role": "gestor", "gestor_id": "1", "periodo_base": "2026-04"},
        must_mention=["captación", "hipotec"],
        must_not_contain=["no puedo"]),

    s77_test("S77_D07", "ForecastGestor",
        "Resumen del mes de abril para mi cartera",
        "/chat/gestor", {"user_role": "gestor", "gestor_id": "1", "periodo": "2026-04"},
        must_mention=["ingresos", "contratos"],
        must_not_contain=["no puedo", "no tengo datos"],
        nota="No-regresion: pregunta de resumen mensual para gestor debe ir a GestorAgent, no ForecastAgent"),

    s77_test("S77_D08", "ForecastGestor",
        "¿Cuál es mi media de ingresos en los últimos 6 meses?",
        "/forecast/chat", {"user_role": "gestor", "gestor_id": "1", "periodo_base": "2026-04"},
        must_mention=["media", "meses"],
        must_not_contain=["no puedo"]),

    # ─── GRUPO E: Calidad dato (5 tests) ─────────────────────
    s77_test("S77_E01", "CalidadDato",
        "Dame el nombre de un cliente de Madrid",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["Madrid"],
        must_not_contain=["Cliente 91", "Cliente 92", "Cliente 100", "Cliente 101", "Cliente 142"]),

    s77_test("S77_E02", "CalidadDato",
        "¿Hay gestores sin cartera de Fondos de Renta Variable?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"gestores_sin_frv": 0, "tolerancia_pct": 0},
        must_mention=["FRV", "fondos"],
        must_not_contain=["no tengo datos"],
        nota="Post-S84: 0 gestores sin FRV"),

    s77_test("S77_E03", "CalidadDato",
        "¿Hay gestores con margen neto negativo en abril?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["margen"],
        must_not_contain=["sí", "1 gestor", "2 gestores", "no tengo datos"],
        nota="Post-S83+S84: 0 gestores con margen negativo"),

    s77_test("S77_E04", "CalidadDato",
        "Dame los datos de María González Vargas en abril",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_mention=["María", "González"],
        must_not_contain=["no tengo acceso", "-74", "no puedo"],
        nota="No-regresion post-S83: María González debe tener margen >20% (antes -74.5%). Verificar que no aparecen valores pre-corrección."),

    s77_test("S77_E05", "CalidadDato",
        "¿Cuántos gestores hay en el banco y en qué centros?",
        "/chat/message", {"user_role": "control_gestion", "periodo": "2026-04"},
        must_contain_values={"n_gestores": ent['n_gestores'], "tolerancia_pct": 0},
        must_mention=["Madrid", "Palma", "Bilbao"]),
]

# Guardar
os.makedirs('evals/datasets', exist_ok=True)

with open('evals/datasets/s88_battery.json', 'w', encoding='utf-8') as f:
    json.dump(s88, f, indent=2, ensure_ascii=False)

with open('evals/datasets/s77_battery.json', 'w', encoding='utf-8') as f:
    json.dump(s77, f, indent=2, ensure_ascii=False)

# Conteos
cdg_count = sum(1 for t in s88 if t['grupo'] == 'CDG')
gest_count = sum(1 for t in s88 if t['grupo'] == 'Gestor')
fore_count = sum(1 for t in s88 if t['grupo'] == 'Forecast')

s77_groups = {}
for t in s77:
    s77_groups[t['grupo']] = s77_groups.get(t['grupo'], 0) + 1
reconstructed = sum(1 for t in s77 if 'nota' in t)

print(f"\n=== DATASETS GENERADOS ===")
print(f"\nGROUND TRUTH: {len(gt)} categorías")
print(f"  Ingresos entidad abr-2026: €{ent['ingresos']:,.2f}")
print(f"  Margen neto: {ent['margen_neto_pct']}%")
print(f"  Contratos: {ent['contratos_activos']} | Gestores: {ent['n_gestores']} | Clientes: {ent['n_clientes']}")
print(f"  MoM entidad: {mom_ent['variacion_pct']:+.2f}%")
print(f"  MoM gestor 1: {mom_g1['variacion_pct']:+.2f}%")
print(f"  Top gestor: {gestores[0]['nombre']} (€{gestores[0]['ingresos']:,.0f})")
print(f"  Serie histórica: {len(gt['serie_historica'])} meses")

print(f"\nS88 CUALITATIVO: {len(s88)} preguntas")
print(f"  CDG: {cdg_count} | Gestor: {gest_count} | Forecast: {fore_count}")
print(f"  Todas con 5 dimensiones de evaluación + pesos")

print(f"\nS77 FUNCIONAL: {len(s77)} preguntas")
for g, n in sorted(s77_groups.items()):
    print(f"  {g}: {n}")
print(f"  Con notas (reconstruidas/no-regresion): {reconstructed}")

print(f"\nARCHIVOS:")
print(f"  evals/datasets/ground_truth.json  ✅")
print(f"  evals/datasets/s88_battery.json   ✅")
print(f"  evals/datasets/s77_battery.json   ✅")
