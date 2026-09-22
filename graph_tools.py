"""
Capa de 'tools' expuesta a los agentes vía function-calling de Groq.

Cada tool envuelve una función de graph_skills. El agente decide CUÁNDO
llamar cada una y con qué parámetros — esa es la parte probabilística.
El dato que regresa la tool es siempre exacto, tal cual sale del grafo.
"""
from graph_skills import (
    buscar_jugador, buscar_equipo, buscar_partido, buscar_torneo, listar_equipos,
    historia_equipo, cambios_nombre, participaciones_equipo,
    jugador_perfil_historico, top_goleadores_historico, finales_por_equipo,
    premios_historicos, historial_entre_equipos, enfrentamientos_entre_equipos,
    ficha_equipo, comparar_equipos, comparar_jugadores, partidos_por_fecha, racha_historica, equipo_mas_dominante,
    encontrar_conexiones, explorar_vecinos,
    jugador_amplitud_ediciones, equipo_mayor_variedad_rivales, equipo_mayor_variedad_goleadores,
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
    "enfrentamientos_entre_equipos": enfrentamientos_entre_equipos,
    "ficha_equipo": ficha_equipo,
    "comparar_equipos": comparar_equipos,
    "comparar_jugadores": comparar_jugadores,
    "partidos_por_fecha": partidos_por_fecha,
    "racha_historica": racha_historica,
    "equipo_mas_dominante": equipo_mas_dominante,
    "encontrar_conexiones": encontrar_conexiones,
    "explorar_vecinos": explorar_vecinos,
    "jugador_amplitud_ediciones": jugador_amplitud_ediciones,
    "equipo_mayor_variedad_rivales": equipo_mayor_variedad_rivales,
    "equipo_mayor_variedad_goleadores": equipo_mayor_variedad_goleadores,
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
                    "equipo2": {"type": ["string", "null"]},
                    "edicion": {"type": ["string", "null"]},
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
            "description": "Historia institucional de un equipo: nombres anteriores, participaciones y fase máxima por edición (con resultado). Para una ficha más completa (incluye goleador del equipo), usa ficha_equipo.",
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
    "ficha_equipo": {
        "type": "function",
        "function": {
            "name": "ficha_equipo",
            "description": (
                "Ficha CONSOLIDADA de un equipo: nombres anteriores, fase máxima por edición "
                "con resultado, cuántas finales jugó, y su goleador histórico — todo en una sola "
                "llamada. Úsala para preguntas abiertas tipo 'cuéntame todo sobre X equipo' o "
                "'características de X equipo', en vez de llamar varias tools sueltas."
            ),
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
            "description": "Perfil histórico completo de un jugador: goles por equipo/edición, tarjetas (con rival y fecha) y premios.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string"}},
                "required": ["nombre"],
            },
        },
    },
    "comparar_equipos": {
        "type": "function",
        "function": {
            "name": "comparar_equipos",
            "description": (
                "Compara dos equipos lado a lado: finales jugadas/ganadas, récord general "
                "(victorias-empates-derrotas en TODA su historia) y su goleador histórico. "
                "NO es head-to-head entre ellos — para saber cómo les ha ido jugando entre sí, "
                "usa enfrentamientos_entre_equipos o historial_entre_equipos."
            ),
            "parameters": {
                "type": "object",
                "properties": {"equipo1": {"type": "string"}, "equipo2": {"type": "string"}},
                "required": ["equipo1", "equipo2"],
            },
        },
    },
    "comparar_jugadores": {
        "type": "function",
        "function": {
            "name": "comparar_jugadores",
            "description": "Compara dos jugadores lado a lado: goles por equipo, tarjetas y premios. Úsala cuando te pidan comparar a dos jugadores en vez de llamar jugador_perfil_historico dos veces.",
            "parameters": {
                "type": "object",
                "properties": {"nombre1": {"type": "string"}, "nombre2": {"type": "string"}},
                "required": ["nombre1", "nombre2"],
            },
        },
    },
    "top_goleadores_historico": {
        "type": "function",
        "function": {
            "name": "top_goleadores_historico",
            "description": "Ranking histórico de goleadores, sumado correctamente por jugador+equipo (nunca entre equipos distintos).",
            "parameters": {
                "type": "object",
                "properties": {"n": {"type": ["integer", "null"], "description": "Cuántos mostrar, default 10"}},
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
            "description": (
                "Lista PARTIDO POR PARTIDO todos los enfrentamientos entre dos equipos, "
                "cada uno con su fase (grupos, cuartos, semifinal, final, etc.) y marcador "
                "exacto. Cada fila es un partido independiente — nunca combines marcadores "
                "de dos filas distintas. Para un RESUMEN agregado (cuántas veces ganó cada "
                "uno en total), usa mejor enfrentamientos_entre_equipos."
            ),
            "parameters": {
                "type": "object",
                "properties": {"equipo1": {"type": "string"}, "equipo2": {"type": "string"}},
                "required": ["equipo1", "equipo2"],
            },
        },
    },
    "enfrentamientos_entre_equipos": {
        "type": "function",
        "function": {
            "name": "enfrentamientos_entre_equipos",
            "description": (
                "Estadística AGREGADA de enfrentamientos (victorias-empates-derrotas totales), "
                "no partido por partido. Tres usos: (1) equipo1+equipo2 -> resumen agregado entre "
                "esos dos; (2) solo equipo1 -> su récord agregado contra CADA rival que ha enfrentado "
                "(incluye contra quién nunca ha ganado o nunca ha perdido); (3) sin ningún equipo -> "
                "escanea TODO el grafo y devuelve pares de equipos donde uno nunca le ha ganado al "
                "otro (0 victorias, puede incluir empates) Y por separado los casos de DOMINIO "
                "ABSOLUTO donde el otro equipo ganó TODOS los partidos sin ningún empate — estas "
                "son categorías DISTINTAS, no la misma cosa vista al revés. 'Nunca ha ganado' NO "
                "implica que el rival 'siempre ha ganado' si hubo empates de por medio. El resultado "
                "ya viene separado en ambas categorías con su conteo — úsalo tal cual, no infieras "
                "una de la otra. Usa este modo (3) para preguntas abiertas sobre quién nunca ha "
                "ganado o quién siempre ha ganado, sin nombre de equipo específico."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "equipo1": {"type": ["string", "null"], "description": "Opcional. Omite (o manda null) junto con equipo2 para el escaneo global."},
                    "equipo2": {"type": ["string", "null"], "description": "Opcional, solo válido si ya diste equipo1."},
                },
            },
        },
    },
    "partidos_por_fecha": {
        "type": "function",
        "function": {
            "name": "partidos_por_fecha",
            "description": "Lista los partidos jugados en una fecha/jornada específica (número), opcionalmente filtrado por edición. Úsala para preguntas sobre qué pasó en una fecha concreta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_fecha": {"type": "integer", "description": "Número de fecha/jornada"},
                    "edicion": {"type": ["string", "null"], "description": "Opcional, ej. 'Apertura 2024'"},
                },
                "required": ["numero_fecha"],
            },
        },
    },
    "racha_historica": {
        "type": "function",
        "function": {
            "name": "racha_historica",
            "description": (
                "Racha ganadora, perdedora Y DE EMPATES más larga, calculado partido a partido "
                "(se reinicia entre ediciones distintas). Dos usos: (1) con equipo -> rachas de "
                "ESE equipo; (2) sin equipo -> busca en TODA la historia quién tiene la racha "
                "ganadora/perdedora/de-empates más larga de todos. Usa el modo (2) para preguntas "
                "abiertas tipo '¿qué equipo tiene la mayor racha de partidos ganados?' sin nombre "
                "de equipo específico."
            ),
            "parameters": {
                "type": "object",
                "properties": {"equipo": {"type": ["string", "null"], "description": "Opcional. Omite (o manda null) para buscar en toda la historia."}},
            },
        },
    },
    "equipo_mas_dominante": {
        "type": "function",
        "function": {
            "name": "equipo_mas_dominante",
            "description": (
                "Ranking histórico agregado de equipos por una métrica compuesta de 'dominancia' "
                "(fase máxima alcanzada + bonus por ganarla). ACLARA SIEMPRE al usuario que esta "
                "métrica es compuesta y no un título oficial del torneo. Úsala para '¿quién ha sido "
                "el mejor equipo de la historia?'."
            ),
            "parameters": {"type": "object", "properties": {}},
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
    "jugador_amplitud_ediciones": {
        "type": "function",
        "function": {
            "name": "jugador_amplitud_ediciones",
            "description": (
                "Ranking de jugadores por AMPLITUD: en cuántas ediciones DISTINTAS anotó al menos "
                "un gol, no por total de goles. Úsala para preguntas tipo '¿qué jugador ha anotado "
                "en más ediciones distintas?' — NO confundir con top_goleadores_historico."
            ),
            "parameters": {
                "type": "object",
                "properties": {"n": {"type": ["integer", "null"], "description": "Cuántos mostrar, default 10"}},
            },
        },
    },
    "equipo_mayor_variedad_rivales": {
        "type": "function",
        "function": {
            "name": "equipo_mayor_variedad_rivales",
            "description": (
                "Ranking de equipos por VARIEDAD de rivales distintos enfrentados, no por cantidad "
                "total de partidos jugados. Úsala para '¿qué equipo ha enfrentado a más rivales "
                "distintos?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {"n": {"type": ["integer", "null"], "description": "Cuántos mostrar, default 10"}},
            },
        },
    },
    "equipo_mayor_variedad_goleadores": {
        "type": "function",
        "function": {
            "name": "equipo_mayor_variedad_goleadores",
            "description": (
                "Ranking de equipos por VARIEDAD de goleadores distintos (cuántos jugadores "
                "diferentes anotaron para ese equipo), no por el total de goles ni por el máximo "
                "goleador. Úsala para '¿qué equipo ha tenido más goleadores distintos?'."
            ),
            "parameters": {
                "type": "object",
                "properties": {"n": {"type": ["integer", "null"], "description": "Cuántos mostrar, default 10"}},
            },
        },
    },
    "consultar_wiki": {
        "type": "function",
        "function": {
            "name": "consultar_wiki",
            "description": "Reglamento oficial del torneo: formato, sanciones, reglas de juego, desempates. NO sirve para preguntas de datos/estadísticas — solo para reglas.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
}
