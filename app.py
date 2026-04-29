import streamlit as st
import altair as alt
from firestore_client import get_partidos_clausura_2025, get_tarjetas_clausura_2025, get_goleadores_clausura_2025
from data_processor import DataProcessor
from assistant import show_assistant

# Inicialización
dp = DataProcessor()
st.set_page_config(page_title="Cambridge College Lima", layout="wide")

st.markdown("<h1 style='text-align: center; '>Campeonato Cambridge College Lima </h1>", unsafe_allow_html=True)

if st.button("🤖 Asistente CLC"):
    st.session_state.show_assistant = not st.session_state.get("show_assistant", False)

if st.session_state.get("show_assistant", False):
    show_assistant()
    st.stop()

st.divider()

# --- Logos section ---
st.markdown("### Equipos Participantes")
st.markdown("""
<div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
    <img src="https://static.cdnlogo.com/logos/l/92/liverpool-fc.svg" width="80">
    <img src="https://static.cdnlogo.com/logos/r/38/real-madrid-club-de-futbol.svg" width="80">
    <img src="https://static.cdnlogo.com/logos/b/29/borussia-dortmund.svg" width="80">
    <img src="https://static.cdnlogo.com/logos/m/41/manchester-city-fc.png" width="80">
    <img src="https://static.cdnlogo.com/logos/b/36/bayern-munich.png" width="80">
    <img src="https://static.cdnlogo.com/logos/f/14/fc-barcelona.svg" width="80">
    <img src="https://static.cdnlogo.com/logos/j/15/juventus.svg" width="80">
    <img src="https://static.cdnlogo.com/logos/f/80/fioren-1.svg" width="80">
    <img src="https://static.cdnlogo.com/logos/a/47/ac-milan.svg" width="80">
    <img src="https://static.cdnlogo.com/logos/c/24/chelsea-fc.svg" width="80">
</div>
""", unsafe_allow_html=True)

st.divider()

# Obtener Data
df1 = get_partidos_clausura_2025()
promedio, total_goles, stats_fecha = dp.get_general_stats(df1)

# Métricas Principales
col1, col2 = st.columns(2)
box_style = "<div style='padding:1.5rem; background-color:{bg}; border-radius:12px; text-align:center; font-weight:bold; color:black;'>{content}</div>"

col1.markdown(box_style.format(bg="#e0f7fa", content=f"⚽ Promedio de Goles:<br>{promedio:.2f}"), unsafe_allow_html=True)
col2.markdown(box_style.format(bg="#ffffff", content=f"🔢 Total de Goles:<br>{total_goles}"), unsafe_allow_html=True)

st.subheader("Estadísticas por Fecha")
st.line_chart(stats_fecha.set_index('Fecha')['Total_Goles'])

# Tablas de Posiciones
st.divider()
st.subheader("Tablas de Posiciones")
for g in [1, 2]:
    st.write(f"**Grupo {g}**")
    tabla = dp.process_standings(df1, g)
    st.dataframe(tabla, use_container_width=True, hide_index=True)

# Resultados y Eliminatorias
st.divider()
st.subheader("Resultados por Fecha")
resultados = dp.process_match_results(df1)
st.dataframe(resultados, use_container_width=True, hide_index=True)

st.subheader("Fase Final (Playoffs)")
playoffs = dp.process_knockout_stage() # Lee automáticamente Fecha 6+ del CSV[cite: 1]
st.dataframe(playoffs, use_container_width=True, hide_index=True)

# Goleadores y Tarjetas
st.divider()
df_cards = get_tarjetas_clausura_2025()
df_scorers = get_goleadores_clausura_2025()
goleadores, team_cards, top_y, top_r = dp.process_cards_and_scorers(df_cards, df_scorers)

st.subheader("Máximos Goleadores")
st.dataframe(goleadores, use_container_width=True, hide_index=True)

st.subheader("Disciplina por Equipo")
chart = alt.Chart(team_cards).mark_bar().encode(
    x=alt.X('Equipo:N', sort='-y'),
    y='Total_A_Count:Q',
    tooltip=['Equipo', 'Total_A_Count']
)
st.altair_chart(chart, use_container_width=True)

col_y, col_r = st.columns(2)
col_y.subheader("Líderes Amarillas 🟨")
col_y.dataframe(top_y, hide_index=True)
col_r.subheader("Líderes Rojas 🟥")
col_r.dataframe(top_r, hide_index=True)
        column_config=column_config_1R
    )

