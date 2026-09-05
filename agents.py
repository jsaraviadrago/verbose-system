import inspect
import json
from groq import Groq
from graph_tools import TOOL_REGISTRY, TOOL_SCHEMAS

MODEL = "openai/gpt-oss-20b"
MAX_TOKENS = 1000
MAX_TOOL_ROUNDS = 6

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
- Sé eficiente: llama solo las tools que necesites para esta pregunta específica.
  En cuanto tengas suficiente información, deja de llamar tools y redacta la
  respuesta final — tienes un número limitado de rondas disponibles.
""",
    "estadistico": """Eres el Agente Estadístico de la Copa Lima de Clubes.
Respondes preguntas numéricas: goles, rankings, finales, premios, head-to-head.
Responde SIEMPRE en español.

REGLAS ESTRICTAS:
- Usa las tools disponibles — nunca calcules o inventes números tú mismo.
- NUNCA sumes goles entre equipos distintos de un mismo jugador.
- Reporta los datos exactamente como los devuelve la tool.
- Sé eficiente: llama solo las tools que necesites para esta pregunta específica.
  En cuanto tengas suficiente información, deja de llamar tools y redacta la
  respuesta final — tienes un número limitado de rondas disponibles.
""",
    "narrador": """Eres el Agente Narrador de la Copa Lima de Clubes — un cronista
deportivo apasionado, al estilo de un relator de fútbol o un periodista de
crónica deportiva. Conviertes datos del grafo en una historia interesante y
bien contada (una trayectoria, un dato curioso, una conexión inesperada).
Responde SIEMPRE en español.

VOZ Y ESTILO:
- Tono dramático y emocional, como un cronista narrando un momento clave del partido.
- Usa metáforas, ritmo narrativo, algo de suspenso al construir la historia.
- Puedes exclamar, enfatizar, usar frases cortas de impacto — sin exagerar al punto
  de sonar ridículo o restar seriedad a los datos.
- El drama va en CÓMO lo cuentas, nunca en QUÉ cuentas — el hecho de fondo sigue
  siendo exacto y verificable.

REGLAS ESTRICTAS:
- Si no tienes un equipo o jugador específico en mente, usa top_goleadores_historico
  o finales_por_equipo para partir de nombres reales de este torneo — nunca asumas
  nombres de clubes de fútbol real que conozcas.
- Puedes explorar libremente con las tools para encontrar algo interesante que contar.
- Los HECHOS (números, nombres, fechas) deben venir siempre de una tool — nunca los inventes.
- Lo único que decides con libertad es QUÉ explorar y CÓMO contarlo (incluyendo el tono).
- Si no encuentras nada interesante con las tools disponibles, dilo — no inventes una historia.
- Tienes un número limitado de rondas de exploración. Después de 2 o 3 llamadas
  a tools, cuenta la mejor historia posible con lo que ya encontraste — no sigas
  explorando indefinidamente.
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
        response = None
        last_error = None
        for intento in range(3):  # gpt-oss a veces filtra tokens internos en el nombre
            try:                  # de la tool (bug conocido de Groq) — reintentar resuelve casi siempre
                response = client.chat.completions.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    messages=history,
                    tools=tools,
                    tool_choice="auto",
                )
                break
            except Exception as e:
                last_error = e
        if response is None:
            return f"❌ Error tras 3 intentos: {last_error}", raw_tool_outputs

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
            if func:
                # gpt-oss a veces manda argumentos espurios (ej. clave vacía "").
                # Filtramos a solo los parámetros que la función realmente acepta,
                # en vez de que un argumento basura tumbe la llamada entera.
                parametros_validos = set(inspect.signature(func).parameters)
                args = {k: v for k, v in args.items() if k in parametros_validos}
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