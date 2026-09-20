import streamlit as st
from groq import Groq
from orchestrator import handle

# Cuántos intercambios (pregunta+respuesta) recientes se mandan COMPLETOS al
# modelo. Los más viejos que esto solo mandan la pregunta del usuario, sin su
# respuesta — para no saturar a un modelo chico (gpt-oss-20b) con demasiado
# contexto, y evitar que números de respuestas viejas se mezclen con la
# respuesta nueva (esto fue justo el patrón que causó el bug de Milan-Barcelona
# en una conversación larga). Es una ventana fija, 100% determinista — no hay
# ningún LLM decidiendo qué podar o resumir. Ajusta el número si hace falta.
ULTIMAS_N_COMPLETAS = 3


def _construir_historial_podado(messages: list, ultimas_n: int = ULTIMAS_N_COMPLETAS) -> list:
    """
    Arma el historial que se manda al modelo: las ultimas_n preguntas van
    completas (con su respuesta), las anteriores solo mandan la pregunta del
    usuario, sin la respuesta vieja. Lógica puramente determinista (índices
    y conteo), sin ningún componente probabilístico.
    """
    pares = []
    i = 0
    while i < len(messages):
        user_msg = messages[i] if messages[i]["role"] == "user" else None
        asst_msg = None
        if user_msg and i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
            asst_msg = messages[i + 1]
            i += 2
        else:
            i += 1
        pares.append((user_msg, asst_msg))

    total = len(pares)
    historial = []
    for idx, (user_msg, asst_msg) in enumerate(pares):
        es_reciente = idx >= total - ultimas_n
        if user_msg:
            historial.append({"role": "user", "content": user_msg["content"]})
        if asst_msg and es_reciente:
            historial.append({"role": "assistant", "content": asst_msg["content"]})
    return historial


def configure_client() -> Groq:
    api_key = st.secrets["groq"]["api_key"]
    return Groq(api_key=api_key)


def show_assistant():
    st.subheader("🤖 Asistente CLC — Historiador · Estadístico · Narrador")

    st.caption(
        "💡 Pregunta sobre la historia, estadísticas o curiosidades del campeonato "
        "(cubre 2024-2025). Ejemplos: 'cuéntame la historia de Barcelona', "
        "'cuántos goles tiene Figari', 'sorpréndeme'."
    )

    client = configure_client()

    session_key = "messages_grafo"
    if session_key not in st.session_state:
        st.session_state[session_key] = []
    messages = st.session_state[session_key]

    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "agent" in msg:
                st.caption(msg["agent"])
            st.markdown(msg["content"])

    if prompt := st.chat_input("Pregunta sobre el campeonato..."):
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando el grafo..."):
                history = _construir_historial_podado(messages)
                answer, agent_used, tool_outputs = handle(client, prompt, history)

            st.caption(agent_used)
            st.markdown(answer)
            with st.expander("🔍 Debug: tools llamadas"):
                if tool_outputs:
                    for i, out in enumerate(tool_outputs, 1):
                        st.text(f"--- resultado {i} ---\n{out}")
                else:
                    st.text("El agente no llamó ninguna tool para esta respuesta.")
            messages.append({"role": "assistant", "content": answer, "agent": agent_used})

    if messages:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state[session_key] = []
            st.rerun()
