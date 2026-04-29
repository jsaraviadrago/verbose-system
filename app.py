import streamlit as st
import altair as alt
from firestore_client import get_partidos_clausura_2025, get_tarjetas_clausura_2025, get_goleadores_clausura_2025
from data_processor import DataProcessor
from assistant import show_assistant

# Inicialización y Configuración
dp = DataProcessor()
st.set_page_config(page_title="Cambridge College Lima", layout="wide")

st.markdown("<h1 style='text-align: center; '>Campeonato Cambridge College Lima </h1>", unsafe_allow_html=True)

# Botón del asistente
if st.button("🤖 Asistente CLC"):
    st.session_state.show_assistant = not st.session_state.get("show_assistant", False)

if st.session_state.get("show_assistant", False):
    show_assistant()
    st.stop()

st.divider()

# --- Logos de Equipos ---
st.markdown("### Equipos Participantes")
st.markdown("""
<div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;">
    <img src="https://static.cdnlogo.com/logos/l/92/liverpool-fc.svg" width="70">
    <img src="https://static.cdnlogo.com/logos/r/38/real-madrid-club-de-futbol.svg" width="70">
    <img src="https://static.cdnlogo.com/logos/b/29/borussia-dortmund.svg" width="70">
    <img src="https://static.cdnlogo.com/logos/m/41/manchester-city-fc.png" width="70">
    <img src="https://static.cdnlogo.com/logos/b/36/bayern-munich.png" width="85">
    <img src="https://static.cdnlogo.com/logos/f/14/fc-barcelona.svg" width="70">
    <img src="https://static.cdnlogo.com/logos/j/15/juventus.svg" width="70">
    <img src="https://static.cdnlogo.com/logos/f/80/fioren-1.svg" width="70">
    <img src="https://static.cdnlogo.com/logos/a/47/ac-milan.svg" width="70">
    <img src="https://static.cdnlogo.com/logos/c/24/chelsea-fc.svg" width="70">
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Carga y Procesamiento de Datos ---
df1 = get_partidos_clausura_2025()
promedio, total_goles, stats_fecha = dp.get_general_stats(df1)

# Métricas Principales
col_m1, col_m2 = st.columns(2)
box_style = "<div style='padding:1.5rem; background-color:{bg}; border-radius:12px; text-align:center; font-weight:bold; color:black;'>{content}</div>"

with col_m1:
    st.markdown(box_style.format(bg="#e0f7fa", content=f"⚽ Promedio de Goles:<br>{promedio:.2f}"), unsafe_allow_html=True)

with col_m2:
    st.markdown(box_style.format(bg="#ffffff", content=f"🔢 Total de Goles:<br>{total_goles}"), unsafe_allow_html=True)

st.subheader("Estadísticas por Fecha")
st.line_chart(stats_fecha.set_index('Fecha')['Total_Goles'])

# --- Tablas de Posiciones ---
st.divider()
st.subheader("Tabla de Posiciones")
for g in [1, 2]:
    st.write(f"**Grupo {g}**")
    tabla = dp.process_standings(df1, g)
    st.dataframe(tabla, use_container_width=True, hide_index=True)

# --- Resultados y Playoffs ---
st.divider()
st.subheader("Resultados por Fecha")
resultados = dp.process_match_results(df1)
st.dataframe(resultados, use_container_width=True, hide_index=True)

st.subheader("Fase Final (Playoffs)")
playoffs = dp.process_knockout_stage() # Dinámico desde Fecha 6 del CSV[cite: 1]
st.dataframe(playoffs, use_container_width=True, hide_index=True)

# --- Goleadores y Disciplina ---
st.divider()
df_cards = get_tarjetas_clausura_2025()
df_scorers = get_goleadores_clausura_2025()
goleadores, team_cards, top_y, top_r = dp.process_cards_and_scorers(df_cards, df_scorers)

st.subheader("Máximos Goleadores")
st.dataframe(goleadores, use_container_width=True, hide_index=True)

st.subheader("Tarjetas Amarillas por Equipo")
chart = alt.Chart(team_cards).mark_bar().encode(
    x=alt.X('Equipo:N', sort='-y', title=""),
    y=alt.Y('Total_A_Count:Q', title="Total Amarillas"),
    tooltip=['Equipo', 'Total_A_Count']
)
st.altair_chart(chart, use_container_width=True)

# Tablas de Jugadores sancionados
col_y, col_r = st.columns(2)

with col_y:
    st.subheader("Top Amarillas 🟨")
    st.dataframe(top_y, use_container_width=True, hide_index=True)

with col_r:
    st.subheader("Top Rojas 🟥")
    st.dataframe(top_r, use_container_width=True, hide_index=True)
