import streamlit as st
import altair as alt
from firestore_client import get_partidos_clausura_2025, get_tarjetas_clausura_2025, get_goleadores_clausura_2025
from data_processor import DataProcessor
from assistant import show_assistant

# Inicialización
dp = DataProcessor()
st.set_page_config(page_title="Cambridge College Lima", layout="wide")

# --- Encabezado ---
st.markdown("<h1 style='text-align: center;'>Campeonato Cambridge College Lima</h1>", unsafe_allow_html=True)

if st.button("🤖 Asistente CLC"):
    st.session_state.show_assistant = not st.session_state.get("show_assistant", False)

if st.session_state.get("show_assistant", False):
    show_assistant()
    st.stop()

st.divider()

# --- Logos de Equipos ---
st.markdown("### Equipos Participantes")
st.markdown("""
<div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-bottom: 20px;">
    <img src="https://static.cdnlogo.com/logos/l/92/liverpool-fc.svg" width="60">
    <img src="https://static.cdnlogo.com/logos/r/38/real-madrid-club-de-futbol.svg" width="60">
    <img src="https://static.cdnlogo.com/logos/b/29/borussia-dortmund.svg" width="60">
    <img src="https://static.cdnlogo.com/logos/m/41/manchester-city-fc.png" width="60">
    <img src="https://static.cdnlogo.com/logos/b/36/bayern-munich.png" width="75">
    <img src="https://static.cdnlogo.com/logos/f/14/fc-barcelona.svg" width="60">
    <img src="https://static.cdnlogo.com/logos/j/15/juventus.svg" width="60">
    <img src="https://static.cdnlogo.com/logos/f/80/fioren-1.svg" width="60">
    <img src="https://static.cdnlogo.com/logos/a/47/ac-milan.svg" width="60">
    <img src="https://static.cdnlogo.com/logos/c/24/chelsea-fc.svg" width="60">
</div>
""", unsafe_allow_html=True)

st.divider()

# --- Carga de Datos y Métricas ---
df_partidos = get_partidos_clausura_2025()
promedio, total_goles, stats_fecha = dp.get_general_stats(df_partidos)

col_m1, col_m2 = st.columns(2)
box_style = "<div style='padding:1.5rem; background-color:{bg}; border-radius:12px; text-align:center; font-weight:bold; color:black;'>{content}</div>"

with col_m1:
    st.markdown(box_style.format(bg="#e0f7fa", content=f"⚽ Promedio de Goles:<br>{promedio:.2f}"), unsafe_allow_html=True)
with col_m2:
    st.markdown(box_style.format(bg="#ffffff", content=f"🔢 Total de Goles:<br>{total_goles}"), unsafe_allow_html=True)

st.subheader("Estadísticas del Campeonato")
col_g1, col_g2 = st.columns(2)
with col_g1:
    st.write("**Total de Goles por Fecha**")
    st.line_chart(stats_fecha.set_index('Fecha')['Total_Goles'])
with col_g2:
    st.write("**Promedio de Goles por Fecha**")
    st.line_chart(stats_fecha.set_index('Fecha')['Prom_Goles'])

# --- Tablas de Posiciones ---
st.divider()
st.subheader("Tabla de Posiciones")
tab1, tab2 = st.tabs(["Grupo 1", "Grupo 2"])
with tab1:
    st.dataframe(dp.process_standings(df_partidos, 1), use_container_width=True, hide_index=True)
with tab2:
    st.dataframe(dp.process_standings(df_partidos, 2), use_container_width=True, hide_index=True)

# --- FASE FINAL (PLAYOFFS) ---
st.divider()
st.subheader("🏆 Fase Final")
playoffs = dp.process_knockout_stage(df_partidos)

if not playoffs.empty:
    for fase in ["Cuartos de Final", "Semifinal", "Gran Final"]:
        fase_df = playoffs[playoffs['Fase'] == fase]
        if not fase_df.empty:
            st.write(f"#### {fase}")
            st.dataframe(fase_df.drop(columns=['Fase']), use_container_width=True, hide_index=True)
else:
    st.info("La fase final se habilitará automáticamente al registrar la Fecha 6.")

# --- Resultados Fase de Grupos ---
st.divider()
st.subheader("Resultados Fase de Grupos")
st.dataframe(dp.process_match_results(df_partidos), use_container_width=True, hide_index=True)

# --- Disciplina y Goleadores ---
st.divider()
goleadores, team_cards, top_y, top_r = dp.process_cards_and_scorers(
    get_tarjetas_clausura_2025(), get_goleadores_clausura_2025()
)

st.subheader("Máximos Goleadores")
st.dataframe(goleadores, use_container_width=True, hide_index=True)

st.subheader("Fair Play: Tarjetas por Equipo")
chart = alt.Chart(team_cards).mark_bar().encode(
    x=alt.X('Equipo:N', sort='-y', title=""),
    y=alt.Y('Total_A_Count:Q', title="Puntos de Sanción (1A=1, 2A=2)"),
    tooltip=['Equipo', 'Total_A_Count']
)
st.altair_chart(chart, use_container_width=True)

col_y, col_r = st.columns(2)
with col_y:
    st.subheader("Top Amarillas 🟨")
    st.dataframe(top_y, use_container_width=True, hide_index=True)
with col_r:
    st.subheader("Top Rojas 🟥")
    st.dataframe(top_r, use_container_width=True, hide_index=True)
