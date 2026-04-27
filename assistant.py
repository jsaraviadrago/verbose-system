import streamlit as st
from groq import Groq
from router import route
from skills import LOADERS


def configure_client() -> Groq:
    api_key = st.secrets["groq"]["api_key"]
    return Groq(api_key=api_key)


def show_assistant():
    st.subheader("🤖 Asistente CLC")

    # Selector de temporada
    temporada = st.selectbox(
        "📅 Temporada (para preguntas específicas):",
        options=list(LOADERS.keys()),
        index=0,
    )

    st.caption(
        "💡 Para una temporada usa el selector. "
        "Para historial completo pregunta **'en total'**, **'por torneo'** o **'en todas las temporadas'**."
    )

    client = configure_client()

    # Historial por temporada
    session_key = f"messages_{temporada}"
    if session_key not in st.session_state:
        st.session_state[session_key] = []
    messages = st.session_state[session_key]

    # Mostrar historial
    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "agent" in msg:
                st.caption(msg["agent"])
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input(f"Pregunta sobre {temporada} o el historial completo..."):

        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consultando agente..."):
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in messages
                ]
                answer, agent_used = route(client, prompt, temporada, history)

            st.caption(agent_used)
            st.markdown(answer)
            messages.append({
                "role": "assistant",
                "content": answer,
                "agent": agent_used,
            })

    # Limpiar chat
    if messages:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state[session_key] = []
            st.rerun()
