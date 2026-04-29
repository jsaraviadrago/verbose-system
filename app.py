import streamlit as st
import altair as alt
from firestore_client import get_partidos_clausura_2025, get_tarjetas_clausura_2025, get_goleadores_clausura_2025
from data_processor import DataProcessor
from assistant import show_assistant

dp = DataProcessor()
st.set_page_config(page_title="Cambridge College Lima", layout="wide")

st.markdown("<h1 style='text-align: center;'>Campeonato Cambridge College Lima</h1>", unsafe_allow_html=True)

if st.button("🤖 Asistente CLC"):
    st.session_state.show_assistant = not st.session_state.get("show_assistant", False)

if st.session_state.get("show_assistant", False):
    show_assistant()
    st.stop()

st.divider()

# --- Logos ---
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

# --- Carga de Datos ---
df_partidos = get_partidos_clausura_2025()
promedio, total_goles, stats_fecha = dp.get_general_stats(df_partidos)

# Métricas
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.markdown(f"<div style='padding:1.5rem; background-color:#e0f7fa; border-radius:12px; text-align:center; color:black;'><b>⚽ Promedio Goles:</b><br>{promedio:.2f}</div>", unsafe_allow_html=True)
with col_m2:
    st.markdown(f"<div style='padding:1.5rem; background-color:#ffffff; border-radius:12px; text-align:center; color:black; border:1px solid #ddd;'><b>🔢 Total Goles:</b><br>{total_goles}</div>", unsafe_allow_html=True)

# Gráficas (Corregido para usar FECHA en mayúsculas)
st.subheader("Estadísticas por Fecha")
c1, c2 = st.columns(2)
with c1:
    st.write("**Goles Totales**")
    st.line_chart(stats_fecha.set_index('FECHA')['Total_Goles'])
with c2:
    st.write("**Promedio de Goles**")
    st.line_chart(stats_fecha.set_index('FECHA')['Prom_Goles'])

# --- Tablas de Posiciones ---
st.divider()
st.subheader("Tabla de Posiciones")
t1, t2 = st.tabs(["Grupo 1", "Grupo 2"])
with t1: st.dataframe(dp.process_standings(df_partidos, 1), use_container_width=True, hide_index=True)
with t2: st.dataframe(dp.process_standings(df_partidos, 2), use_container_width=True, hide_index=True)

# --- Playoffs (Corregido para manejar las columnas de Fase Final)
st.divider()
st.subheader("🏆 Fase Final")
playoffs = dp.process_knockout_stage(df_partidos)
if not playoffs.empty:
    for fase in ["Cuartos de Final", "Semifinal", "Gran Final"]:
        # Se asegura de filtrar por la columna 'Fase' que genera el DataProcessor
        f_df = playoffs[playoffs['Fase'] == fase]
        if not f_df.empty:
            st.write(f"#### {fase}")
            st.dataframe(f_df.drop(columns=['Fase']), use_container_width=True, hide_index=True)
else:
    st.info("Fase final pendiente de inicio.")

st.divider()
st.subheader("Resultados Fase de Grupos")
st.dataframe(dp.process_match_results(df_partidos), use_container_width=True, hide_index=True)

# --- Disciplina ---
st.divider()
# Llamada a procesamiento de disciplina
goleadores, team_cards, top_y, top_r = dp.process_cards_and_scorers(
    get_tarjetas_clausura_2025(), get_goleadores_clausura_2025()
)

st.subheader("Máximos Goleadores")
st.dataframe(goleadores, use_container_width=True, hide_index=True)

st.subheader("Puntos de Sanción por Equipo")
# Altair es sensible a mayúsculas: usamos 'Equipo' y 'Total_Sancion' como lo devuelve el DP
chart = alt.Chart(team_cards).mark_bar().encode(
    x=alt.X('Equipo:N', sort='-y'),
    y=alt.Y('Total_Sancion:Q', title="Puntos Acumulados"),
    tooltip=['Equipo', 'Total_Sancion']
)
st.altair_chart(chart, use_container_width=True)

cy, cr = st.columns(2)
with cy:
    st.subheader("Top Amarillas 🟨")
    if not top_y.empty:
        st.dataframe(top_y, use_container_width=True, hide_index=True)
    else:
        st.write("Sin amarillas registradas.")
with cr:
    st.subheader("Top Rojas 🟥")
    if not top_r.empty:
        # Aquí es donde aparecerá la roja de Alvaro Galarreta una vez sincronizada
        st.dataframe(top_r, use_container_width=True, hide_index=True)
    else:
        st.write("Cero rojas hasta el momento. ✅")