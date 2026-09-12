import pandas as pd
import streamlit as st
import altair as alt

from fixture_service import get_pending_fixture
from pathlib import Path

from firestore_client import (
    get_partidos_clausura_2026,
    get_goleadores_clausura_2026,
    get_tarjetas_clausura_2026,
)
from data_processor import DataProcessor
from assistant import show_assistant

dp = DataProcessor()

LOGO_PATH = (
    Path(__file__).parent
    / "assets"
    / "logos_equipos.png"
)

ICONOS_RACHA = {"G": "🟢", "E": "🟡", "P": "🔴"}


def formatear_racha(resultados):
    if not resultados:
        return ""
    return " ".join(ICONOS_RACHA.get(r, "⚪") for r in resultados)


def tabla_cruce(cruces, columnas=("Local", "Visitante")):
    """Convierte una lista de tuplas (equipo_a, equipo_b) en un DataFrame,
    con el orden: Equipo, Resultado, Equipo, Resultado."""
    local_col, visitante_col = columnas
    tabla = pd.DataFrame(cruces, columns=[local_col, visitante_col])
    tabla["Goles " + local_col] = ""
    tabla["Goles " + visitante_col] = ""
    return tabla[[local_col, "Goles " + local_col, visitante_col, "Goles " + visitante_col]]


st.set_page_config(
    page_title="Cambridge College Lima",
    layout="wide",
)

st.markdown(
    "<h1 style='text-align: center;'>"
    "Campeonato Cambridge College Lima - Clausura 2026"
    "</h1>",
    unsafe_allow_html=True,
)

if st.button("🤖 Asistente CLC en construccion"):
    st.session_state.show_assistant = not st.session_state.get(
        "show_assistant",
        False,
    )

if st.session_state.get("show_assistant", False):
    show_assistant()
    st.stop()

# ── Logos de los equipos ─────────────────────────────────────────────
# Cargar resultados una sola vez
df_partidos = get_partidos_clausura_2026()

st.image(
    str(LOGO_PATH),
    use_container_width=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE PENDIENTE
# ─────────────────────────────────────────────────────────────────────────────
if df_partidos.empty:
    st.info(
        "Todavia no hay resultados publicados para Clausura 2026."
    )
    st.stop()

st.subheader("📅 Próximos Partidos")

fixture_pendiente = get_pending_fixture(df_partidos)

if fixture_pendiente.empty:
    st.success("🏆 No quedan partidos pendientes.")
else:
    standings_preview = dp.process_standings(df_partidos)
    try:
        fixture_pendiente = dp.resolver_equipos_pendientes(
            fixture_pendiente,
            standings_preview,
        )
    except Exception as e:
        st.warning(f"No se pudo proyectar equipos de playoff pendientes: {e}")
    st.dataframe(
        fixture_pendiente,
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────────────────────────────────────
promedio, total_goles, stats_fecha = dp.get_general_stats(
    df_partidos
)

col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(
        "⚽ Promedio goles por partido",
        f"{promedio:.2f}",
    )
with col_m2:
    st.metric(
        "🔢 Total goles",
        int(total_goles),
    )

# ─────────────────────────────────────────────────────────────────────────────
# ESTADÍSTICAS POR FECHA
# ─────────────────────────────────────────────────────────────────────────────
if not stats_fecha.empty:
    st.subheader("Estadísticas por Fecha")
    st.write("**Goles Totales**")
    st.line_chart(
        stats_fecha
        .set_index("FECHA")["Total_Goles"]
    )

# ─────────────────────────────────────────────────────────────────────────────
# TABLA DE POSICIONES
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Tabla de Posiciones")

standings = dp.process_standings(df_partidos)
standings_display = standings.copy()
standings_display["Racha"] = standings_display["Racha"].apply(formatear_racha)

columnas_orden = ["EQUIPO", "Puntos", "Racha", "PJ", "G", "E", "P", "GF", "GC", "GD"]

st.dataframe(
    standings_display[columnas_orden],
    use_container_width=True,
    hide_index=True,
)
st.caption(
    "Nota: la Racha muestra los últimos 3 partidos de cada equipo, "
    "de izquierda a derecha del más antiguo al más reciente "
    "(🟢 ganó · 🟡 empató · 🔴 perdió)."
)

# ─────────────────────────────────────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Resultados")

st.dataframe(
    dp.process_match_results(df_partidos),
    use_container_width=True,
    hide_index=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# PLAYOFFS (PROYECCIÓN)
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🏆 Playoffs — Proyección según tabla actual")
st.caption(
    "⚠️ Cruces estimados asumiendo que el mejor sembrado avanza en cada ronda. "
    "No son oficiales hasta que se jueguen los partidos reales."
)

POR_DEFINIR = ("Por definir", "Por definir")

if len(standings) >= 8:
    cuartos = dp.calcular_cuartos_proyectados(standings)
else:
    cuartos = [POR_DEFINIR] * 4

semifinal = [POR_DEFINIR] * 2
final = [POR_DEFINIR]
tercer_puesto = [POR_DEFINIR]

st.markdown("#### Cuartos de Final")
st.dataframe(
    tabla_cruce(cuartos),
    use_container_width=True,
    hide_index=True,
)

st.markdown("#### Semifinal")
st.dataframe(
    tabla_cruce(semifinal),
    use_container_width=True,
    hide_index=True,
)

col_final, col_tercer = st.columns(2)
with col_final:
    st.markdown("#### Final")
    st.dataframe(
        tabla_cruce(final),
        use_container_width=True,
        hide_index=True,
    )
with col_tercer:
    st.markdown("#### Tercer y Cuarto Puesto")
    st.dataframe(
        tabla_cruce(tercer_puesto),
        use_container_width=True,
        hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# ESTADÍSTICAS POR EQUIPO
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Estadísticas por Equipo")

# ── 🎯 Scatter Ataque vs Defensa (cuadrantes por mediana) ──────────────────
if standings.empty:
    st.info("Todavía no hay suficientes partidos jugados para este gráfico.")
else:
    med_gf, med_gc = dp.calcular_medianas_ataque_defensa(standings)

    base = alt.Chart(standings)

    puntos = base.mark_circle(size=220, color="#1f77b4").encode(
        x=alt.X(
            "GC:Q",
            title="Goles recibidos (menos → mejor defensa)",
            scale=alt.Scale(reverse=True),
        ),
        y=alt.Y("GF:Q", title="Goles anotados"),
        tooltip=[
            alt.Tooltip("EQUIPO:N", title="Equipo"),
            alt.Tooltip("GF:Q", title="Goles a favor"),
            alt.Tooltip("GC:Q", title="Goles en contra"),
            alt.Tooltip("GD:Q", title="Diferencia"),
        ],
    )

    etiquetas = base.mark_text(
        align="left", dx=9, dy=-9, fontSize=11, color="#1f77b4", fontWeight="bold"
    ).encode(
        x="GC:Q",
        y="GF:Q",
        text="EQUIPO:N",
    )

    linea_h = (
        alt.Chart(pd.DataFrame({"y": [med_gf]}))
        .mark_rule(strokeDash=[4, 4], color="gray")
        .encode(y="y:Q")
    )
    linea_v = (
        alt.Chart(pd.DataFrame({"x": [med_gc]}))
        .mark_rule(strokeDash=[4, 4], color="gray")
        .encode(x="x:Q")
    )

    cuadrantes = (linea_h + linea_v + puntos + etiquetas).properties(height=420)

    st.altair_chart(cuadrantes, use_container_width=True)
    st.caption(
        "Cuanto más arriba y a la derecha, mejor: ataca y defiende bien. "
        "Abajo a la izquierda, el que más necesita mejorar en ambos frentes."
    )

# ── 📊 Detalle en barras (goleadores, defensas, amarillas) ─────────────────
with st.expander("📊 Ver más estadísticas por equipo (goleadores, defensas y amarillas)"):
    graf_col1, graf_col2, graf_col3 = st.columns(3)

    goles_equipos = dp.ordenar_para_grafico_goleadores(standings)

    with graf_col1:
        st.markdown("### ⚽ Equipos más goleadores")
        chart_goles = (
            alt.Chart(goles_equipos)
            .mark_bar()
            .encode(
                x=alt.X(
                    "EQUIPO:N",
                    sort="-y",
                    title="",
                ),
                y=alt.Y(
                    "GF:Q",
                    title="Goles",
                ),
                tooltip=[
                    alt.Tooltip(
                        "EQUIPO:N",
                        title="Equipo",
                    ),
                    alt.Tooltip(
                        "GF:Q",
                        title="Goles",
                    ),
                ],
            )
        )
        st.altair_chart(
            chart_goles,
            use_container_width=True,
        )

    with graf_col2:
        st.markdown("### 🛡️ Mejores defensas")
        defensas = dp.ordenar_para_grafico_defensas(standings)
        chart_defensas = (
            alt.Chart(defensas)
            .mark_bar()
            .encode(
                x=alt.X("EQUIPO:N", sort="y", title=""),
                y=alt.Y("GC:Q", title="Goles en contra"),
                tooltip=[
                    alt.Tooltip("EQUIPO:N", title="Equipo"),
                    alt.Tooltip("GC:Q", title="Goles en contra"),
                ],
            )
        )
        st.altair_chart(chart_defensas, use_container_width=True)

    df_tarjetas_grafico = get_tarjetas_clausura_2026()
    amarillas_equipos = dp.agrupar_amarillas_por_equipo(df_tarjetas_grafico)

    with graf_col3:
        st.markdown("### 🟨 Equipos con más amarillas")
        if amarillas_equipos.empty:
            st.info(
                "Todavía no hay tarjetas registradas."
            )
        else:
            chart_amarillas = (
                alt.Chart(amarillas_equipos)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "EQUIPO:N",
                        sort="-y",
                        title="",
                    ),
                    y=alt.Y(
                        "AMARILLAS:Q",
                        title="Amarillas",
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "EQUIPO:N",
                            title="Equipo",
                        ),
                        alt.Tooltip(
                            "AMARILLAS:Q",
                            title="Amarillas",
                        ),
                    ],
                )
            )
            st.altair_chart(
                chart_amarillas,
                use_container_width=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
# GOLEADORES
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("⚽ Máximos Goleadores")

df_goleadores = get_goleadores_clausura_2026()
top_8 = dp.procesar_top_goleadores(df_goleadores)

if top_8.empty:
    st.info(
        "Todavía no hay goleadores publicados."
    )
else:
    st.dataframe(
        top_8,
        use_container_width=True,
        hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# DISCIPLINA
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Disciplina")

df_tarjetas = get_tarjetas_clausura_2026()
amarillas, rojas = dp.procesar_disciplina_jugadores(df_tarjetas)

left, right = st.columns(2)

with left:
    st.markdown("### 🟨 Amarillas")
    st.dataframe(
        amarillas,
        use_container_width=True,
        hide_index=True,
    )
with right:
    st.markdown("### 🟥 Rojas")
    st.dataframe(
        rojas,
        use_container_width=True,
        hide_index=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# ANALÍTICA
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📊 Analítica")

with st.expander("Expectativa pitagórica (puntos reales vs. esperados)"):
    st.dataframe(
        dp.calcular_puntos_esperados(standings),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "**Pyth**: expectativa pitagórica. Compara los goles a favor y en contra de un equipo "
        "para estimar qué proporción de sus partidos 'debería' haber ganado, más allá del resultado real "
        "de cada partido puntual.\n\n"
        "**Puntos Esperados**: son los puntos que le tocarían al equipo si hubiera ganado exactamente esa "
        "proporción (Pyth) de todos sus partidos jugados, en vez de los resultados reales.\n\n"
        "**Diferencia**: Puntos Reales menos Puntos Esperados. "
        "Si es positiva, el equipo está sacando más puntos de los que su rendimiento en goles sugiere "
        "(le está yendo mejor en el marcador final de lo que 'merece' por juego). "
        "Si es negativa, es al revés: rinde bien en goles pero no lo está traduciendo en puntos."
    )