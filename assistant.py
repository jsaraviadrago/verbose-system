import streamlit as st
from groq import Groq
from router import route
from skills import LOADERS

# ── Configure Groq ─────────────────────────────────────────────────────────────
def configure_client() -> Groq:
    api_key = st.secrets["groq"]["api_key"]
    return Groq(api_key=api_key)


# ── Assistant UI ───────────────────────────────────────────────────────────────
def show_assistant():
    st.subheader("🤖 Asistente CLC")
    st.caption("Consulta resultados, goleadores, tarjetas e info del torneo")

    # Season selector
    temporada = st.selectbox(
        "📅 Selecciona la temporada:",
        options=list(LOADERS.keys()),
        index=0,
    )

    client = configure_client()

    # Chat history per season
    session_key = f"messages_{temporada}"
    if session_key not in st.session_state:
        st.session_state[session_key] = []
    messages = st.session_state[session_key]

    # Display chat history
    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and "agent" in msg:
                st.caption(msg["agent"])
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input(f"Pregunta sobre {temporada}..."):

        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Route to correct agent
        with st.chat_message("assistant"):
            with st.spinner("Consultando agente..."):
                # Pass only user/assistant messages to LLM
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

    # Clear chat
    if messages:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state[session_key] = []
            st.rerun()
