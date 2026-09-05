import streamlit as st
from groq import Groq
from orchestrator import handle


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
                history = [{"role": m["role"], "content": m["content"]} for m in messages]
                answer, agent_used = handle(client, prompt, history)

            st.caption(agent_used)
            st.markdown(answer)
            messages.append({"role": "assistant", "content": answer, "agent": agent_used})

    if messages:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state[session_key] = []
            st.rerun()
