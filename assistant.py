import streamlit as st
import google.generativeai as genai
from firestore_client import (
    get_partidos_clausura_2025, get_partidos_apertura_2025,
    get_goleadores_clausura_2025, get_goleadores_apertura_2025,
    get_tarjetas_clausura_2025, get_tarjetas_apertura_2025,
)


# ── Configure Gemini ───────────────────────────────────────────────────────────
def configure_gemini():
    api_key = st.secrets["gemini"]["api_key"]
    if not api_key:
        st.error("⚠️ No se encontró GEMINI_API_KEY en los secrets.")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


# ── Load all data as context ───────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_context() -> str:
    """Load all Firestore data and format it as text context for Gemini."""
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

    model = configure_gemini()
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
    if prompt := st.chat_input("¿Quién va primero en goles? ¿Cuál fue el resultado del último partido?"):

        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build conversation history for Gemini
        history = []
        for msg in st.session_state.messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})

        # Get Gemini response
        with st.chat_message("assistant"):
            with st.spinner("Consultando datos..."):
                try:
                    chat = model.start_chat(history=history)
                    full_prompt = f"{system}\n\nPregunta: {prompt}"
                    response = chat.send_message(full_prompt)
                    answer = response.text
                except Exception as e:
                    answer = f"❌ Error al consultar el asistente: {e}"

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.messages = []
            st.rerun()
