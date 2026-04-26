import streamlit as st
from groq import Groq
from firestore_client import (
    get_partidos_clausura_2025, get_partidos_apertura_2025,
    get_goleadores_clausura_2025, get_goleadores_apertura_2025,
    get_tarjetas_clausura_2025, get_tarjetas_apertura_2025,
)


# ── Configure Groq ─────────────────────────────────────────────────────────────
def configure_client():
    api_key = st.secrets["groq"]["api_key"]
    return Groq(api_key=api_key)


# ── Load all data as context ───────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_context() -> str:
    sections = []

    try:
        df = get_partidos_clausura_2025()
        sections.append(f"PARTIDOS CLAUSURA 2025:\n{df.to_string(index=False)}")
    except Exception:
        pass

    try:
        df = get_partidos_apertura_2025()
        sections.append(f"PARTIDOS APERTURA 2025:\n{df.to_string(index=False)}")
    except Exception:
        pass

    try:
        df = get_goleadores_clausura_2025()
        sections.append(f"GOLEADORES CLAUSURA 2025:\n{df.to_string(index=False)}")
    except Exception:
        pass

    try:
        df = get_goleadores_apertura_2025()
        sections.append(f"GOLEADORES APERTURA 2025:\n{df.to_string(index=False)}")
    except Exception:
        pass

    try:
        df = get_tarjetas_clausura_2025()
        sections.append(f"TARJETAS CLAUSURA 2025:\n{df.to_string(index=False)}")
    except Exception:
        pass

    try:
        df = get_tarjetas_apertura_2025()
        sections.append(f"TARJETAS APERTURA 2025:\n{df.to_string(index=False)}")
    except Exception:
        pass

    return "\n\n".join(sections)


# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un asistente experto en fútbol de la Copa Lima de Clubes (CLC).
Tienes acceso a los datos oficiales de la liga: partidos, resultados, goleadores y tarjetas.
Responde SIEMPRE en español, de forma clara y concisa.
Si te preguntan algo que no está en los datos, dilo honestamente.
No inventes resultados ni estadísticas.

Aquí están los datos actuales de la liga:

{context}
"""


# ── Assistant UI ───────────────────────────────────────────────────────────────
def show_assistant():
    st.subheader("🤖 Asistente CLC")
    st.caption("Consulta resultados, goleadores y tarjetas de la liga")

    client = configure_client()
    context = get_context()
    system = SYSTEM_PROMPT.format(context=context)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input box
    if prompt := st.chat_input("¿Quién lidera los goles? ¿Cuál fue el resultado del último partido?"):

        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build conversation history for Groq
        history = [{"role": "system", "content": system}]
        for msg in st.session_state.messages:
            history.append({"role": msg["role"], "content": msg["content"]})

        # Get Groq response
        with st.chat_message("assistant"):
            with st.spinner("Consultando datos..."):
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        max_tokens=1000,
                        messages=history,
                    )
                    answer = response.choices[0].message.content
                except Exception as e:
                    answer = f"❌ Error al consultar el asistente: {e}"

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.messages = []
            st.rerun()
