from comunicado_broma import mostrar_comunicado_si_corresponde
mostrar_comunicado_si_corresponde()

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import altair as alt

from fixture_service import get_pending_fixture
from pathlib import Path

from firestore_client import (
    get_partidos_clausura_2026,
    get_goleadores_clausura_2026,
    get_goleadores_detalle_clausura_2026,
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

