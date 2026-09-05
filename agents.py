import json
from groq import Groq
from graph_tools import TOOL_REGISTRY, TOOL_SCHEMAS

MODEL = "openai/gpt-oss-20b"
MAX_TOKENS = 1000
MAX_TOOL_ROUNDS = 4

# El ajuar es único y compartido — los 3 agentes ven las mismas 15 skills.
# Cada agente elige cuáles usar según la pregunta y su propio rol (descrito
# en su system prompt), no por una lista fija que restrinja de antemano.
ALL_TOOL_NAMES = list(TOOL_SCHEMAS.keys())

AGENT_SYSTEM_PROMPTS = {
    "historiador": """Eres el Agente Historiador de la Copa Lima de Clubes.
Reconstruyes la historia institucional de equipos: nombres anteriores,
participaciones, fases alcanzadas y reglas/formato del torneo.
Responde SIEMPRE en español.

REGLAS ESTRICTAS:
- Usa las tools disponibles para obtener los datos — NUNCA inventes historia.
- Los datos que traen las tools son exactos: repórtalos tal cual, sin cambiar nada.
- Si una tool no encuentra algo, dilo claramente — no lo rellenes con suposiciones.
""",
    "estadistico": """Eres el Agente Estadístico de la Copa Lima de Clubes.
Respondes preguntas numéricas: goles, rankings, finales, premios, head-to-head.
Responde SIEMPRE en español.

REGLAS ESTRICTAS:
- Usa las tools disponibles — nunca calcules o inventes números tú mismo.
- NUNCA sumes goles entre equipos distintos de un mismo jugador.
- Reporta los datos exactamente como los devuelve la tool.
""",
    "narrador": """Eres el Agente Narrador de la Copa Lima de Clubes.
Conviertes datos del grafo en una historia interesante y bien contada
(una trayectoria, un dato curioso, una conexión inesperada).
Responde SIEMPRE en español.

REGLAS ESTRICTAS:
- Puedes explorar libremente con las tools para encontrar algo interesante que contar.
- Los HECHOS (números, nombres, fechas) deben venir siempre de una tool — nunca los inventes.
- Lo único que decides con libertad es QUÉ explorar y CÓMO contarlo.
- Si no encuentras nada interesante con las tools disponibles, dilo — no inventes una historia.
""",
}


def _tool_call_to_dict(call) -> dict:
    """Normaliza un tool_call del SDK de Groq a dict plano, para reenviarlo en el historial."""
    return {
        "id": call.id,
        "type": "function",
        "function": {"name": call.function.name, "arguments": call.function.arguments},
    }


def _run_agent(client: Groq, agent_key: str, messages: list) -> tuple[str, list[str]]:
    """
    Loop de function-calling para un agente. Devuelve (respuesta_final,
    lista_de_resultados_crudos_de_tools) — esto último se usa en verificador.py.
    """
    tool_names = ALL_TOOL_NAMES
    tools = [TOOL_SCHEMAS[name] for name in tool_names]
    system = AGENT_SYSTEM_PROMPTS[agent_key]
    history = [{"role": "system", "content": system}] + messages
    raw_tool_outputs: list[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=history,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as e:
            return f"❌ Error: {e}", raw_tool_outputs

        msg = response.choices[0].message
        tool_calls = getattr(msg, "tool_calls", None)

        if not tool_calls:
            return msg.content or "", raw_tool_outputs

        history.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [_tool_call_to_dict(c) for c in tool_calls],
        })

        for call in tool_calls:
            func = TOOL_REGISTRY.get(call.function.name)
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            try:
                result = func(**args) if func else f"Tool '{call.function.name}' no existe."
            except Exception as e:
                result = f"Error ejecutando {call.function.name}: {e}"

            raw_tool_outputs.append(result)
            history.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": call.function.name,
                "content": str(result),
            })

    return "No pude completar la respuesta en el número de pasos permitido.", raw_tool_outputs


def agent_historiador(client: Groq, messages: list) -> tuple[str, list[str]]:
    return _run_agent(client, "historiador", messages)


def agent_estadistico(client: Groq, messages: list) -> tuple[str, list[str]]:
    return _run_agent(client, "estadistico", messages)


def agent_narrador(client: Groq, messages: list) -> tuple[str, list[str]]:
    return _run_agent(client, "narrador", messages)
