"""
Orquestador — reemplaza a router.py.

Decide qué agente responde una pregunta. Primero intenta por palabras clave
(rápido, gratis, determinista). Si no hay match claro, se lo pregunta al LLM
con una clasificación de una sola palabra — ahí vive la capa "probabilística"
de selección de agente que no existía en el router anterior (ese solo hacía
matching de keywords, sin fallback).
"""
from groq import Groq
from agents import agent_historiador, agent_estadistico, agent_narrador
from verificador import verificar_respuesta

MODEL = "openai/gpt-oss-20b"

AGENT_LABELS = {
    "historiador": "🏛️ Agente Historiador",
    "estadistico": "📊 Agente Estadístico",
    "narrador": "📖 Agente Narrador",
}

AGENT_FUNCS = {
    "historiador": agent_historiador,
    "estadistico": agent_estadistico,
    "narrador": agent_narrador,
}

_KEYWORDS = {
    "historiador": [
        "historia", "cambió de nombre", "cambio de nombre", "antes se llamaba",
        "participó", "participo", "fase alcanzó", "trayectoria institucional",
        "reglas", "formato", "cómo funciona",
    ],
    "estadistico": [
        "gol", "goles", "goleador", "botín", "botin", "ranking", "final", "finales",
        "premio", "mejor jugador", "mejor arquero", "cuántos", "cuantos", " vs ", "contra",
    ],
    "narrador": [
        "sorpréndeme", "sorprendeme", "cuéntame algo", "cuentame algo",
        "qué historia", "que historia", "dato curioso", "algo interesante",
    ],
}


def _detectar_por_palabras(pregunta: str) -> str | None:
    q = f" {pregunta.lower()} "
    puntajes = {agente: sum(1 for kw in kws if kw in q) for agente, kws in _KEYWORDS.items()}
    mejor = max(puntajes, key=puntajes.get)
    return mejor if puntajes[mejor] > 0 else None


def _clasificar_con_llm(client: Groq, pregunta: str) -> str:
    """Fallback cuando las palabras clave no bastan."""
    system = """Clasifica la pregunta del usuario sobre un campeonato de fútbol en UNA sola palabra:
- historiador: historia de equipos, cambios de nombre, participaciones, reglas del torneo
- estadistico: goles, rankings, finales, premios, comparaciones numéricas
- narrador: pedidos abiertos de una historia, curiosidad, "sorpréndeme"

Responde ÚNICAMENTE con una de esas tres palabras, nada más."""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=10,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": pregunta}],
        )
        respuesta = (response.choices[0].message.content or "").strip().lower()
        for agente in AGENT_FUNCS:
            if agente in respuesta:
                return agente
    except Exception:
        pass
    return "estadistico"  # default razonable: la mayoría de preguntas CLC son numéricas


def handle(client: Groq, pregunta: str, messages: list) -> tuple[str, str, list[str]]:
    """Punto de entrada único (reemplaza a router.route). Devuelve también los
    resultados crudos de las tools llamadas, para poder mostrarlos en modo debug."""
    agente = _detectar_por_palabras(pregunta) or _clasificar_con_llm(client, pregunta)
    respuesta, tool_outputs = AGENT_FUNCS[agente](client, messages)
    respuesta_verificada = verificar_respuesta(respuesta, tool_outputs)
    return respuesta_verificada, AGENT_LABELS[agente], tool_outputs