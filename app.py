import pandas as pd
import streamlit as st
import altair as alt

from firestore_client import (
    get_partidos_clausura_2026,
get_goleadores_clausura_2026,
get_tarjetas_clausura_2026
)
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

# ── Gráficos por equipo ──────────────────────────────────────────────────────
st.divider()
st.subheader("Estadísticas por Equipo")

graf_col1, graf_col2 = st.columns(2)

# ⚽ Equipos más goleadores
goles_equipos = (
    df_partidos
    .copy()
)

goles_equipos.columns = (
    goles_equipos.columns
    .astype(str)
    .str.strip()
    .str.upper()
)

goles_equipos["GOLES"] = pd.to_numeric(
    goles_equipos["GOLES"],
    errors="coerce",
).fillna(0)

goles_equipos = (
    goles_equipos
    .groupby("EQUIPO", as_index=False)["GOLES"]
    .sum()
    .sort_values(
        ["GOLES", "EQUIPO"],
        ascending=[False, True],
    )
)

with graf_col1:
    st.markdown("### ⚽ Equipos más goleadores")

    chart_goles = (
    alt.Chart(goles_equipos)
    .mark_bar()
    .encode(
        x=alt.X(
            "EQUIPO:N",
            sort="-y",
            title=""
        ),
        y=alt.Y(
            "GOLES:Q",
            title="Goles"
        ),
        tooltip=["EQUIPO", "GOLES"]
    )
)

st.altair_chart(
    chart_goles,
    use_container_width=True,
)


# 🟨 Equipos con más amarillas
df_tarjetas_grafico = get_tarjetas_clausura_2026()

with graf_col2:
    st.markdown("### 🟨 Equipos con más amarillas")

    if df_tarjetas_grafico.empty:
        st.info("Todavía no hay tarjetas registradas.")

    else:
        amarillas_equipos = df_tarjetas_grafico.copy()

        amarillas_equipos.columns = (
            amarillas_equipos.columns
            .astype(str)
            .str.strip()
            .str.upper()
        )

        amarillas_equipos["AMARILLAS"] = pd.to_numeric(
            amarillas_equipos["AMARILLAS"],
            errors="coerce",
        ).fillna(0)

        amarillas_equipos = (
            amarillas_equipos
            .groupby("EQUIPO", as_index=False)["AMARILLAS"]
            .sum()
            .sort_values(
                ["AMARILLAS", "EQUIPO"],
                ascending=[False, True],
            )
        )

        chart_amarillas = (
    alt.Chart(amarillas_equipos)
    .mark_bar()
    .encode(
        x=alt.X(
            "EQUIPO:N",
            sort="-y",
            title=""
        ),
        y=alt.Y(
            "AMARILLAS:Q",
            title="Amarillas"
        ),
        tooltip=["EQUIPO", "AMARILLAS"]
    )
)

st.altair_chart(
    chart_amarillas,
    use_container_width=True,
)

st.divider()
st.subheader("⚽ Máximos Goleadores")

df_goleadores = get_goleadores_clausura_2026()

if df_goleadores.empty:
    st.info("Todavía no hay goleadores publicados.")
else:
    goleadores = df_goleadores.copy()

    goleadores.columns = (
        goleadores.columns
        .astype(str)
        .str.strip()
        .str.upper()
    )

    goleadores["GOLES"] = pd.to_numeric(
        goleadores["GOLES"],
        errors="coerce",
    ).fillna(0).astype(int)

    goleadores["NOMBRE Y APELLIDO"] = (
        goleadores["NOMBRE Y APELLIDO"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    top_8 = (
        goleadores
        .sort_values(
            ["GOLES", "NOMBRE Y APELLIDO", "EQUIPO"],
            ascending=[False, True, True],
        )
        .head(8)
        [["NOMBRE Y APELLIDO", "EQUIPO", "GOLES"]]
        .rename(
            columns={
                "NOMBRE Y APELLIDO": "Jugador",
                "EQUIPO": "Equipo",
                "GOLES": "Goles",
            }
        )
        .reset_index(drop=True)
    )

    top_8.index = top_8.index + 1
    top_8.index.name = "Pos."

    st.dataframe(
        top_8,
        use_container_width=True,
    )


st.divider()
st.subheader("Disciplina")

df_tarjetas = get_tarjetas_clausura_2026()

left, right = st.columns(2)

if df_tarjetas.empty:
    amarillas = pd.DataFrame(
        columns=["Jugador", "Equipo", "Amarillas"]
    )
    rojas = pd.DataFrame(
        columns=["Jugador", "Equipo", "Rojas"]
    )

else:
    cards = df_tarjetas.copy()

    cards.columns = (
        cards.columns
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if "AMARILLAS" not in cards.columns:
        cards["AMARILLAS"] = 0

    if "ROJAS" not in cards.columns:
        cards["ROJAS"] = 0

    cards["AMARILLAS"] = pd.to_numeric(
        cards["AMARILLAS"],
        errors="coerce",
    ).fillna(0).astype(int)

    cards["ROJAS"] = pd.to_numeric(
        cards["ROJAS"],
        errors="coerce",
    ).fillna(0).astype(int)

    cards["JUGADOR"] = (
        cards["JUGADOR"]
        .astype(str)
        .str.strip()
        .str.title()
    )

    amarillas = (
        cards.loc[cards["AMARILLAS"].gt(0)]
        .sort_values(
            ["AMARILLAS", "JUGADOR", "EQUIPO"],
            ascending=[False, True, True],
        )
        .head(8)[
            ["JUGADOR", "EQUIPO", "AMARILLAS"]
        ]
        .rename(
            columns={
                "JUGADOR": "Jugador",
                "EQUIPO": "Equipo",
                "AMARILLAS": "Amarillas",
            }
        )
        .reset_index(drop=True)
    )

    rojas = (
        cards.loc[cards["ROJAS"].gt(0)]
        .sort_values(
            ["ROJAS", "JUGADOR", "EQUIPO"],
            ascending=[False, True, True],
        )
        .head(8)[
            ["JUGADOR", "EQUIPO", "ROJAS"]
        ]
        .rename(
            columns={
                "JUGADOR": "Jugador",
                "EQUIPO": "Equipo",
                "ROJAS": "Rojas",
            }
        )
        .reset_index(drop=True)
    )

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