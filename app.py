import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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

NUMERO_YAPE = "980424164"  # reemplaza con el número real de la cuenta de donaciones
LINK_APP = "https://futbol-ccl-apafa.streamlit.app/"

YAPE_LOGO_SVG_PATH = Path(__file__).parent / "assets" / "yape_logo.svg"
YAPE_LOGO_PNG_PATH = Path(__file__).parent / "assets" / "yape_logo.png"
YAPE_LOGO_WEBP_PATH = Path(__file__).parent / "assets" / "yape_logo.webp"


def _logo_tag():
    import base64
    if YAPE_LOGO_SVG_PATH.exists():
        svg_code = YAPE_LOGO_SVG_PATH.read_text(encoding="utf-8")
        return f'<span style="height:16px; width:16px; display:inline-block; vertical-align:middle; margin-right:6px;">{svg_code}</span>'
    if YAPE_LOGO_WEBP_PATH.exists():
        b64 = base64.b64encode(YAPE_LOGO_WEBP_PATH.read_bytes()).decode()
        return f'<img src="data:image/webp;base64,{b64}" style="height:16px; vertical-align:middle; margin-right:6px;">'
    if YAPE_LOGO_PNG_PATH.exists():
        b64 = base64.b64encode(YAPE_LOGO_PNG_PATH.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" style="height:16px; vertical-align:middle; margin-right:6px;">'
    return "📲 "


yape_img_tag = _logo_tag()

_, col_botones = st.columns([8, 2.6])

with col_botones:
    components.html(
        f"""
        <div style="display:flex; gap:6px; justify-content:flex-end; position:relative; font-family:sans-serif;">
            <button id="btn-yape" style="
                display:flex; align-items:center; justify-content:center;
                background-color:#4B2E83; color:white; border:none;
                padding:7px 12px; border-radius:8px; font-size:13px;
                font-weight:600; cursor:pointer;
            ">{yape_img_tag}Yape</button>

            <button id="btn-compartir" style="
                background-color:#1a73e8; color:white; border:none;
                padding:7px 12px; border-radius:8px; font-size:13px;
                font-weight:600; cursor:pointer;
            ">🔗 Compartir</button>

            <div id="panel-yape" style="
                display:none; position:absolute; top:38px; right:90px;
                background:#ffffff; border:1px solid #ddd; border-radius:10px;
                box-shadow:0 4px 12px rgba(0,0,0,0.15); padding:14px; width:200px; text-align:center; z-index:999;
            ">
                <p style="color:#555555; margin:0 0 4px 0; font-size:12px;">CELULAR</p>
                <p style="color:#1a1a1a; font-size:20px; font-weight:bold; margin:0 0 10px 0;">{NUMERO_YAPE}</p>
                <button id="btn-copiar" style="
                    background-color:#4B2E83; color:#ffffff; border:none;
                    padding:8px 16px; border-radius:8px; font-size:13px;
                    font-weight:bold; cursor:pointer; width:100%;
                ">Copiar número</button>
            </div>
        </div>
        <script>
            const btnYape = document.getElementById("btn-yape");
            const panel = document.getElementById("panel-yape");
            const btnCopiar = document.getElementById("btn-copiar");
            const btnShare = document.getElementById("btn-compartir");

            btnYape.addEventListener("click", () => {{
                panel.style.display = panel.style.display === "none" ? "block" : "none";
            }});

            btnCopiar.addEventListener("click", () => {{
                navigator.clipboard.writeText("{NUMERO_YAPE.replace(" ", "")}");
                btnCopiar.innerText = "¡Copiado! ✅";
                setTimeout(() => {{ btnCopiar.innerText = "Copiar número"; }}, 2000);
            }});

            btnShare.addEventListener("click", async () => {{
                const shareData = {{
                    title: "Cambridge College Lima - Clausura 2026",
                    text: "Mira los resultados y la tabla de posiciones del campeonato:",
                    url: "{LINK_APP}"
                }};
                try {{
                    if (navigator.share) {{
                        await navigator.share(shareData);
                    }} else {{
                        await navigator.clipboard.writeText(shareData.url);
                        btnShare.innerText = "¡Copiado! ✅";
                        setTimeout(() => {{ btnShare.innerText = "🔗 Compartir"; }}, 2000);
                    }}
                }} catch (err) {{
                    // el usuario cerro el menu de compartir, no hacer nada
                }}
            }});
        </script>
        """,
        height=210,
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
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Goles Totales**")
        st.line_chart(
            stats_fecha
            .set_index("FECHA")["Total_Goles"]
        )
    with c2:
        st.write("**Promedio de Goles**")
        st.line_chart(
            stats_fecha
            .set_index("FECHA")["Prom_Goles"]
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

# Semifinal, Final y Tercer/Cuarto puesto quedan vacios hasta que se jueguen
# los cuartos reales -- no se proyectan en cascada asumiendo ganadores.
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

graf_col1, graf_col2, graf_col3 = st.columns(3)

# ⚽ EQUIPOS MÁS GOLEADORES
goles_equipos = df_partidos.copy()
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
    .groupby(
        "EQUIPO",
        as_index=False,
    )["GOLES"]
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
                title="",
            ),
            y=alt.Y(
                "GOLES:Q",
                title="Goles",
            ),
            tooltip=[
                alt.Tooltip(
                    "EQUIPO:N",
                    title="Equipo",
                ),
                alt.Tooltip(
                    "GOLES:Q",
                    title="Goles",
                ),
            ],
        )
    )
    st.altair_chart(
        chart_goles,
        use_container_width=True,
    )

# 🛡️ MEJORES DEFENSAS
with graf_col2:
    st.markdown("### 🛡️ Mejores defensas")
    defensas = standings.sort_values("GC", ascending=True)
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

# 🟨 EQUIPOS CON MÁS AMARILLAS
df_tarjetas_grafico = get_tarjetas_clausura_2026()

with graf_col3:
    st.markdown("### 🟨 Equipos con más amarillas")
    if df_tarjetas_grafico.empty:
        st.info(
            "Todavía no hay tarjetas registradas."
        )
    else:
        amarillas_equipos = (
            df_tarjetas_grafico.copy()
        )
        amarillas_equipos.columns = (
            amarillas_equipos.columns
            .astype(str)
            .str.strip()
            .str.upper()
        )
        if "AMARILLAS" not in amarillas_equipos.columns:
            amarillas_equipos["AMARILLAS"] = 0
        amarillas_equipos["AMARILLAS"] = pd.to_numeric(
            amarillas_equipos["AMARILLAS"],
            errors="coerce",
        ).fillna(0)
        amarillas_equipos = (
            amarillas_equipos
            .groupby(
                "EQUIPO",
                as_index=False,
            )["AMARILLAS"]
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

if df_goleadores.empty:
    st.info(
        "Todavía no hay goleadores publicados."
    )
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
            [
                "GOLES",
                "NOMBRE Y APELLIDO",
                "EQUIPO",
            ],
            ascending=[
                False,
                True,
                True,
            ],
        )
        .head(8)
        [
            [
                "NOMBRE Y APELLIDO",
                "EQUIPO",
                "GOLES",
            ]
        ]
        .rename(
            columns={
                "NOMBRE Y APELLIDO": "Jugador",
                "EQUIPO": "Equipo",
                "GOLES": "Goles",
            }
        )
        .reset_index(drop=True)
    )

    top_8.insert(
        0,
        "Pos.",
        range(
            1,
            len(top_8) + 1,
        ),
    )
    top_8["Pos."] = top_8["Pos."].replace(
        {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }
    )

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

left, right = st.columns(2)

if df_tarjetas.empty:
    amarillas = pd.DataFrame(
        columns=[
            "Pos.",
            "Jugador",
            "Equipo",
            "Amarillas",
        ]
    )
    rojas = pd.DataFrame(
        columns=[
            "Pos.",
            "Jugador",
            "Equipo",
            "Rojas",
        ]
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
        cards
        .loc[
            cards["AMARILLAS"].gt(0)
        ]
        .sort_values(
            [
                "AMARILLAS",
                "JUGADOR",
                "EQUIPO",
            ],
            ascending=[
                False,
                True,
                True,
            ],
        )
        .head(8)
        [
            [
                "JUGADOR",
                "EQUIPO",
                "AMARILLAS",
            ]
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
        cards
        .loc[
            cards["ROJAS"].gt(0)
        ]
        .sort_values(
            [
                "ROJAS",
                "JUGADOR",
                "EQUIPO",
            ],
            ascending=[
                False,
                True,
                True,
            ],
        )
        .head(8)
        [
            [
                "JUGADOR",
                "EQUIPO",
                "ROJAS",
            ]
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

    amarillas.insert(
        0,
        "Pos.",
        range(
            1,
            len(amarillas) + 1,
        ),
    )
    amarillas["Pos."] = amarillas["Pos."].replace(
        {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }
    )

    rojas.insert(
        0,
        "Pos.",
        range(
            1,
            len(rojas) + 1,
        ),
    )
    rojas["Pos."] = rojas["Pos."].replace(
        {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }
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
        "**Tasa_Empate**: proporción de los partidos jugados por el equipo que terminaron en empate.\n\n"
        "**Puntos Esperados**: se calculan asumiendo que el equipo empata en esa misma proporción de "
        "partidos (Tasa_Empate), y que el resto de partidos los gana o pierde según su expectativa "
        "pitagórica (Pyth). Es una estimación más realista que solo mirar 'gana o pierde', porque toma en "
        "cuenta que un equipo que empata seguido no puede estar sacando puntos como si siempre ganara o "
        "perdiera.\n\n"
        "**Diferencia**: Puntos Reales menos Puntos Esperados. "
        "Si es positiva, el equipo está sacando más puntos de los que su rendimiento en goles sugiere "
        "(le está yendo mejor en el marcador final de lo que 'merece' por juego). "
        "Si es negativa, es al revés: rinde bien en goles pero no lo está traduciendo en puntos."
    )