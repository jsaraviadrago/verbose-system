from groq import Groq
from agents import agent_goleadores, agent_tarjetas, agent_partidos, agent_wiki
from skills import goles_jugador_todas_temporadas, top_goleadores_todas_temporadas, goles_jugador

MODEL = "llama-3.1-8b-instant"


def _is_multi_season(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in [
        "todas", "total", "histórico", "historico",
        "todas las temporadas", "en total", "acumulado",
        "siempre", "carrera", "historia",
        "por torneo", "cada torneo", "en cada",
        "desglosado", "todos los torneos",
    ])

def _has_player_name(question: str, stopwords: set) -> bool:
    """Detecta si la pregunta menciona un nombre propio de jugador."""
    palabras = [w for w in question.split() if w.lower() not in stopwords and len(w) > 2]
    # Si hay palabras que no son stopwords, probablemente hay un nombre
    return len(palabras) > 0


def detect_intent(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["gol", "goles", "goleador", "anotó", "anoto",
                              "score", "botín", "máximo anotador"]):
        return "goleadores"
    if any(w in q for w in ["tarjeta", "amarilla", "roja", "amonestado",
                              "expulsado", "disciplina", "sanción"]):
        return "tarjetas"
    if any(w in q for w in ["partido", "resultado", "jugó", "jugo", "marcador",
                              "ganó", "gano", "perdió", "perdio", "empate",
                              "cancha", "fecha", "jornada"]):
        return "partidos"
    if any(w in q for w in ["regla", "formato", "historia", "torneo",
                              "cuántos equipos", "campeón", "cómo funciona"]):
        return "wiki"
    return "goleadores"


def _call_groq(client: Groq, system: str, messages: list) -> str:
    history = [{"role": "system", "content": system}] + messages
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=1000,
            messages=history,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"


def _extract_player_name(question: str) -> str | None:
    """Intenta extraer el nombre del jugador de la pregunta."""
    stopwords = {
        "goles", "tiene", "total", "todas", "temporadas", "torneo",
        "cuántos", "cuantos", "metido", "marcado", "anotado", "por",
        "en", "de", "ha", "que", "histórico", "historico", "cada",
        "todos", "los", "las", "dime", "sus", "equipo", "equipos",
        "torneos", "campeonato", "copa", "lima", "clubes", "clc",
        "cuanto", "cuanta", "también", "tambien", "quiero", "saber",
        "dame", "puedes", "decir", "favor", "porfa", "mismo",
    }
    palabras = [w for w in question.split() if w.lower() not in stopwords and len(w) > 2]
    return " ".join(palabras) if palabras else None


def route(client: Groq, question: str, temporada: str, messages: list) -> tuple[str, str]:
    intent = detect_intent(question)
    multi = _is_multi_season(question)

    # ── Multi-temporada ────────────────────────────────────────────────────────
    if intent == "goleadores" and multi:
        nombre = _extract_player_name(question)

        if nombre:
            data = goles_jugador_todas_temporadas(nombre)
            # Si no se encontró al jugador, retornar directo sin pasar al LLM
            if "No se encontró" in data:
                return f"No encontré datos de '{nombre}' en ninguna temporada de la CLC.", "⚽ Agente Goleadores"
        else:
            data = top_goleadores_todas_temporadas()

        system = f"""Eres el agente experto en goleadores de la Copa Lima de Clubes.
Responde SIEMPRE en español.
Tu ÚNICO trabajo es presentar el siguiente resultado calculado por Python.
NO sumes, NO restes, NO cambies ningún número.
NO menciones equipos, jugadores ni datos que no aparezcan exactamente abajo.
Si no hay datos de algo, di "no hay datos" — no inventes.

{data}
"""
        return _call_groq(client, system, messages), "⚽ Agente Goleadores — Todas las temporadas"

    # ── Temporada específica ───────────────────────────────────────────────────
    if intent == "goleadores":
        # Si pregunta por un jugador sin especificar temporada → ir a multi-temporada
        stopwords = {
            "goles", "tiene", "total", "cuántos", "cuantos", "metido",
            "marcado", "anotado", "por", "en", "de", "ha", "que", "cada",
            "todos", "las", "los", "temporada", "torneo", "equipo",
            "cuanto", "dime", "dame", "sus", "hay",
        }
        nombre = _extract_player_name(question)
        if nombre and "No se encontró" not in goles_jugador_todas_temporadas(nombre):
            data = goles_jugador_todas_temporadas(nombre)
            system = f"""Eres el agente experto en goleadores de la Copa Lima de Clubes.
Responde SIEMPRE en español.
Tu ÚNICO trabajo es presentar el siguiente resultado calculado por Python.
NO sumes entre equipos. NO cambies ningún número. NO menciones datos que no aparezcan abajo.

{data}
"""
            return _call_groq(client, system, messages), "⚽ Agente Goleadores — Todas las temporadas"
        return agent_goleadores(client, question, temporada, messages), "⚽ Agente Goleadores"
    elif intent == "tarjetas":
        return agent_tarjetas(client, question, temporada, messages), "🟨 Agente Tarjetas"
    elif intent == "partidos":
        return agent_partidos(client, question, temporada, messages), "🏟️ Agente Partidos"
    elif intent == "wiki":
        return agent_wiki(client, question, messages), "📖 Agente Wiki"

    return agent_goleadores(client, question, temporada, messages), "⚽ Agente Goleadores"
