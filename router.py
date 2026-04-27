from groq import Groq
from agents import agent_goleadores, agent_tarjetas, agent_partidos, agent_wiki
from skills import goles_jugador_todas_temporadas, top_goleadores_todas_temporadas

MODEL = "llama-3.1-8b-instant"

def _is_multi_season(question: str) -> bool:
    """Detecta si la pregunta es sobre todas las temporadas."""
    q = question.lower()
    return any(w in q for w in [
        "todas", "total", "histórico", "historico",
        "todas las temporadas", "en total", "acumulado",
        "siempre", "carrera", "historia"
    ])

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


def route(client: Groq, question: str, temporada: str, messages: list) -> tuple[str, str]:
    """Enruta la pregunta al agente correcto."""
    intent = detect_intent(question)
    multi = _is_multi_season(question)

    # Multi-temporada — maneja directo el router
    if intent == "goleadores" and multi:
        q = question.lower()
        # Detectar si pregunta por jugador específico o ranking general
        palabras = [w for w in question.split() if len(w) > 3]
        data = None
        for palabra in palabras:
            if palabra.lower() not in ["goles", "todas", "total", "temporadas",
                                        "histórico", "cuántos", "tiene", "hizo"]:
                result = goles_jugador_todas_temporadas(palabra)
                if "No se encontró" not in result:
                    data = result
                    break

        if not data:
            data = top_goleadores_todas_temporadas()

        system = f"""Eres el agente experto en goleadores históricos de la Copa Lima de Clubes.
Responde SIEMPRE en español, claro y conciso.
Solo usa los datos proporcionados.

{data}
"""
        return _call_groq(client, system, messages), "⚽ Agente Goleadores — Todas las temporadas"

    # Temporada específica
    if intent == "goleadores":
        return agent_goleadores(client, question, temporada, messages), "⚽ Agente Goleadores"
    elif intent == "tarjetas":
        return agent_tarjetas(client, question, temporada, messages), "🟨 Agente Tarjetas"
    elif intent == "partidos":
        return agent_partidos(client, question, temporada, messages), "🏟️ Agente Partidos"
    elif intent == "wiki":
        return agent_wiki(client, question, messages), "📖 Agente Wiki"

    return agent_goleadores(client, question, temporada, messages), "⚽ Agente Goleadores"
