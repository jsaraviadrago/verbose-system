import streamlit as st
import altair as alt
from firestore_client import get_partidos_clausura_2025, get_tarjetas_clausura_2025, get_goleadores_clausura_2025
from data_processor import DataProcessor
from assistant import show_assistant

dp = DataProcessor()
st.set_page_config(page_title="Cambridge College Lima", layout="wide")

st.markdown("<h1 style='text-align: center; '>Campeonato Cambridge College Lima </h1>", unsafe_allow_html=True)

if st.button("🤖 Asistente CLC"):
    st.session_state.show_assistant = not st.session_state.get("show_assistant", False)

if st.session_state.get("show_assistant", False):
    show_assistant()
    st.stop()

st.divider()

# Carga de datos
df1 = get_partidos_clausura_2025()
promedio, total_goles, stats_fecha = dp.get_general_stats(df1)

# Métricas
col_m1, col_m2 = st.columns(2)
box_style = "<div style='padding:1.5rem; background-color:{bg}; border-radius:12px; text-align:center; font-weight:bold; color:black;'>{content}</div>"

with col_m1:
    st.markdown(box_style.format(bg="#e0f7fa", content=f"⚽ Promedio de Goles:<br>{promedio:.2f}"), unsafe_allow_html=True)
with col_m2:
    st.markdown(box_style.format(bg="#ffffff", content=f"🔢 Total de Goles:<br>{total_goles}"), unsafe_allow_html=True)

# Restauración de las dos gráficas
st.subheader("Estadísticas del Campeonato por Fecha")
st.write("**Total de Goles por Fecha**")
st.line_chart(stats_fecha.set_index('Fecha')['Total_Goles'])

st.write("**Promedio de Goles por Fecha**")
st.line_chart(stats_fecha.set_index('Fecha')['Prom_Goles'])

# Posiciones
st.divider()
st.subheader("Tabla de Posiciones")
for g in [1, 2]:
    st.write(f"**Grupo {g}**")
    tabla = dp.process_standings(df1, g)
    st.dataframe(tabla, use_container_width=True, hide_index=True)

# Resultados y Fase Final
st.divider()
st.subheader("Resultados por Fecha")
st.dataframe(dp.process_match_results(df1), use_container_width=True, hide_index=True)

st.subheader("Fase Final (Playoffs)")
# CAMBIO: Ahora pasamos df1 como argumento para evitar buscar el CSV inexistente
playoffs_df = dp.process_knockout_stage(df1)
st.dataframe(playoffs_df, use_container_width=True, hide_index=True)

# Disciplina y Goleadores
st.divider()
goleadores, team_cards, top_y, top_r = dp.process_cards_and_scorers(get_tarjetas_clausura_2025(), get_goleadores_clausura_2025())

st.subheader("Máximos Goleadores")
st.dataframe(goleadores, use_container_width=True, hide_index=True)

st.subheader("Tarjetas Amarillas por Equipo")
chart = alt.Chart(team_cards).mark_bar().encode(
    x=alt.X('Equipo:N', sort='-y', title=""),
    y=alt.Y('Total_A_Count:Q', title="Amarillas"),
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
