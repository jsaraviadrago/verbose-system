"""
Capa de 'tools' expuesta a los agentes vía function-calling de Groq.

Cada tool envuelve una función de graph_skills. El agente decide CUÁNDO
llamar cada una y con qué parámetros — esa es la parte probabilística.
El dato que regresa la tool es siempre exacto, tal cual sale del grafo;
eso nunca lo decide el LLM.
"""
from graph_skills import (
    buscar_jugador, buscar_equipo, buscar_partido, buscar_torneo, listar_equipos,
    historia_equipo, cambios_nombre, participaciones_equipo,
    jugador_perfil_historico, top_goleadores_historico, finales_por_equipo,
    premios_historicos, historial_entre_equipos,
    encontrar_conexiones, explorar_vecinos,
)
from wiki import get_wiki


def consultar_wiki() -> str:
    return get_wiki()


# Nombre de tool → función Python real que se ejecuta
TOOL_REGISTRY = {
    "buscar_jugador": buscar_jugador,
    "buscar_equipo": buscar_equipo,
    "buscar_partido": buscar_partido,
    "buscar_torneo": buscar_torneo,
    "listar_equipos": listar_equipos,
    "historia_equipo": historia_equipo,
    "cambios_nombre": cambios_nombre,
    "participaciones_equipo": participaciones_equipo,
    "jugador_perfil_historico": jugador_perfil_historico,
    "top_goleadores_historico": top_goleadores_historico,
    "finales_por_equipo": finales_por_equipo,
    "premios_historicos": premios_historicos,
    "historial_entre_equipos": historial_entre_equipos,
    "encontrar_conexiones": encontrar_conexiones,
    "explorar_vecinos": explorar_vecinos,
    "consultar_wiki": consultar_wiki,
}

# Esquemas estilo OpenAI/Groq function-calling
TOOL_SCHEMAS = {
    "buscar_jugador": {
        "type": "function",
        "function": {
            "name": "buscar_jugador",
            "description": "Confirma si un jugador existe en el grafo y devuelve coincidencias de nombre.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string", "description": "Nombre o parte del nombre"}},
                "required": ["nombre"],
            },
        },
    },
    "buscar_equipo": {
        "type": "function",
        "function": {
            "name": "buscar_equipo",
            "description": "Resuelve un nombre de equipo, incluyendo nombres históricos/alias (ej. 'Holanda' -> 'Liverpool').",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string", "description": "Nombre o alias del equipo"}},
                "required": ["nombre"],
            },
        },
    },
    "buscar_partido": {
        "type": "function",
        "function": {
            "name": "buscar_partido",
            "description": "Encuentra partidos de un equipo, opcionalmente cruzado con otro equipo y/o edición.",
            "parameters": {
                "type": "object",
                "properties": {
                    "equipo1": {"type": "string"},
                    "equipo2": {"type": "string"},
                    "edicion": {"type": "string"},
                },
                "required": ["equipo1"],
            },
        },
    },
    "buscar_torneo": {
        "type": "function",
        "function": {
            "name": "buscar_torneo",
            "description": "Lista los torneos y ediciones disponibles en el grafo histórico.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    "listar_equipos": {
        "type": "function",
        "function": {
            "name": "listar_equipos",
            "description": (
                "Lista TODOS los equipos reales que existen en este torneo. "
                "Llama esto SIEMPRE primero cuando vayas a explorar o contar algo "
                "sin tener un equipo específico en mente — para no adivinar nombres "
                "de clubes de fútbol real que no son parte de este torneo."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    "historia_equipo": {
        "type": "function",
        "function": {
            "name": "historia_equipo",
            "description": "Historia institucional completa de un equipo: nombres anteriores, participaciones y fase máxima por edición.",
            "parameters": {
                "type": "object",
                "properties": {"equipo": {"type": "string"}},
                "required": ["equipo"],
            },
        },
    },
    "cambios_nombre": {
        "type": "function",
        "function": {
            "name": "cambios_nombre",
            "description": "Nombres históricos que ha usado un equipo.",
            "parameters": {
                "type": "object",
                "properties": {"equipo": {"type": "string"}},
                "required": ["equipo"],
            },
        },
    },
    "participaciones_equipo": {
        "type": "function",
        "function": {
            "name": "participaciones_equipo",
            "description": "Ediciones en las que participó un equipo.",
            "parameters": {
                "type": "object",
                "properties": {"equipo": {"type": "string"}},
                "required": ["equipo"],
            },
        },
    },
    "jugador_perfil_historico": {
        "type": "function",
        "function": {
            "name": "jugador_perfil_historico",
            "description": "Perfil histórico completo de un jugador: goles por equipo/edición, tarjetas y premios.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string"}},
                "required": ["nombre"],
            },
        },
    },
    "top_goleadores_historico": {
        "type": "function",
        "function": {
            "name": "top_goleadores_historico",
            "description": "Ranking histórico de goleadores, sumado correctamente por jugador+equipo.",
            "parameters": {
                "type": "object",
                "properties": {"n": {"type": "integer", "description": "Cuántos mostrar, default 10"}},
            },
        },
    },
    "finales_por_equipo": {
        "type": "function",
        "function": {
            "name": "finales_por_equipo",
            "description": "Cuántas finales jugó cada equipo, histórico.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    "premios_historicos": {
        "type": "function",
        "function": {
            "name": "premios_historicos",
            "description": "Ganadores históricos de un premio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "award_type": {
                        "type": "string",
                        "enum": ["GOLDEN_BOOT", "BEST_PLAYER", "BEST_GOALKEEPER"],
                        "description": "GOLDEN_BOOT=Botín de Oro, BEST_PLAYER=Mejor Jugador, BEST_GOALKEEPER=Mejor Arquero",
                    }
                },
                "required": ["award_type"],
            },
        },
    },
    "historial_entre_equipos": {
        "type": "function",
        "function": {
            "name": "historial_entre_equipos",
            "description": "Head-to-head: todos los partidos jugados entre dos equipos específicos.",
            "parameters": {
                "type": "object",
                "properties": {"equipo1": {"type": "string"}, "equipo2": {"type": "string"}},
                "required": ["equipo1", "equipo2"],
            },
        },
    },
    "encontrar_conexiones": {
        "type": "function",
        "function": {
            "name": "encontrar_conexiones",
            "description": "Camino más corto en el grafo entre dos entidades cualquiera (jugadores, equipos, ediciones). Para descubrir relaciones no obvias.",
            "parameters": {
                "type": "object",
                "properties": {"nombre1": {"type": "string"}, "nombre2": {"type": "string"}},
                "required": ["nombre1", "nombre2"],
            },
        },
    },
    "explorar_vecinos": {
        "type": "function",
        "function": {
            "name": "explorar_vecinos",
            "description": "Todo lo directamente conectado a una entidad en el grafo — punto de partida para explorar antes de decidir qué contar.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string"}},
                "required": ["nombre"],
            },
        },
    },
    "consultar_wiki": {
        "type": "function",
        "function": {
            "name": "consultar_wiki",
            "description": "Información estática del torneo: formato, reglas, equipos participantes, temporadas disponibles.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
}
