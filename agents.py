from groq import Groq
import streamlit as st
from skills import (
    top_goleadores, goles_jugador, goles_equipo,
    tarjetas_jugador, tarjetas_equipo,
    resultados_equipo, todos_los_partidos,
)
from wiki import get_wiki

MODEL = "llama-3.1-8b-instant"
MAX_TOKENS = 1000

EQUIPOS = ["barcelona", "chelsea", "liverpool", "juventus", "manchester city", "real madrid"]


def _call_groq(client: Groq, system: str, messages: list) -> str:
    history = [{"role": "system", "content": system}] + messages
    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            messages=history,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"


# ── Agente Goleadores ──────────────────────────────────────────────────────────
def agent_goleadores(client: Groq, question: str, temporada: str, messages: list) -> str:
    q = question.lower()
    equipo = next((e for e in EQUIPOS if e in q), None)

    if any(w in q for w in ["top", "mejores", "más goles", "tabla", "ranking", "todos"]):
        data = top_goleadores(temporada)
    elif equipo:
        data = goles_equipo(equipo, temporada)
    else:
        # Busca por nombre de jugador
        stopwords = {"goles", "tiene", "cuántos", "cuantos", "metió", "marcó", "anotó"}
        data = top_goleadores(temporada)
        for word in question.split():
            if len(word) > 3 and word.lower() not in stopwords:
                result = goles_jugador(word, temporada)
                if "No se encontró" not in result:
                    data = result
                    break

    system = f"""Eres el agente experto en goleadores de la Copa Lima de Clubes.
Responde SIEMPRE en español, claro y conciso.
CRÍTICO: Reporta los datos exactamente como aparecen. NO hagas cálculos propios.

Datos de goleadores — {temporada}:
{data}
"""
    return _call_groq(client, system, messages)


# ── Agente Tarjetas ────────────────────────────────────────────────────────────
def agent_tarjetas(client: Groq, question: str, temporada: str, messages: list) -> str:
    q = question.lower()
    equipo = next((e for e in EQUIPOS if e in q), None)

    if equipo:
        data = tarjetas_equipo(equipo, temporada)
    else:
        from firestore_client import get_tarjetas_clausura_2025, get_tarjetas_apertura_2025
        func = get_tarjetas_clausura_2025 if "clausura" in temporada.lower() else get_tarjetas_apertura_2025
        try:
            data = func().to_string(index=False)
        except Exception:
            data = "No hay datos de tarjetas disponibles."

    system = f"""Eres el agente experto en tarjetas y disciplina de la Copa Lima de Clubes.
Responde SIEMPRE en español, claro y conciso.
CRÍTICO: Reporta los datos exactamente como aparecen. NO hagas cálculos propios.

Datos de tarjetas — {temporada}:
{data}
"""
    return _call_groq(client, system, messages)


# ── Agente Partidos ────────────────────────────────────────────────────────────
def agent_partidos(client: Groq, question: str, temporada: str, messages: list) -> str:
    q = question.lower()
    equipo = next((e for e in EQUIPOS if e in q), None)

    if equipo:
        data = resultados_equipo(equipo, temporada)
    else:
        data = todos_los_partidos(temporada)

    system = f"""Eres el agente experto en partidos y resultados de la Copa Lima de Clubes.
Responde SIEMPRE en español, claro y conciso.
CRÍTICO: Reporta los datos exactamente como aparecen. NO inventes resultados.

Datos de partidos — {temporada}:
{data}
"""
    return _call_groq(client, system, messages)


# ── Agente Wiki ────────────────────────────────────────────────────────────────
def agent_wiki(client: Groq, question: str, messages: list) -> str:
    system = f"""Eres el agente experto en la historia y reglas de la Copa Lima de Clubes.
Responde SIEMPRE en español, claro y conciso.
Solo usa la información del torneo proporcionada.

Información del torneo:
{get_wiki()}
"""
    return _call_groq(client, system, messages)
