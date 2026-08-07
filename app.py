import streamlit as st
from firestore_client import get_partidos_clausura_2026
from data_processor import DataProcessor
from assistant import show_assistant


dp = DataProcessor()
st.set_page_config(page_title="Cambridge College Lima", layout="wide")
st.markdown("<h1 style='text-align: center;'>Campeonato Cambridge College Lima - Clausura 2026</h1>", unsafe_allow_html=True)

if st.button("🤖 Asistente CLC en construccion"):
    st.session_state.show_assistant = not st.session_state.get("show_assistant", False)
if st.session_state.get("show_assistant", False):
    show_assistant()
    st.stop()

st.divider()

df_partidos = get_partidos_clausura_2026()
if df_partidos.empty:
    st.info("Todavia no hay resultados publicados para Clausura 2026.")
    st.stop()

promedio, total_goles, stats_fecha = dp.get_general_stats(df_partidos)
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric("⚽ Promedio goles por partido", f"{promedio:.2f}")
with col_m2:
    st.metric("🔢 Total goles", int(total_goles))

if not stats_fecha.empty:
    st.subheader("Estadísticas por Fecha")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Goles Totales**")
        st.line_chart(stats_fecha.set_index("FECHA")["Total_Goles"])
    with c2:
        st.write("**Promedio de Goles**")
        st.line_chart(stats_fecha.set_index("FECHA")["Prom_Goles"])

st.divider()
st.subheader("Tabla de Posiciones")
st.dataframe(dp.process_standings(df_partidos), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Resultados")
st.dataframe(dp.process_match_results(df_partidos), use_container_width=True, hide_index=True)
