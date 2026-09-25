
"""
Modulo aislado para el comunicado-broma temporal.

Se importa y se llama UNA sola vez, al principio de app.py — si todavia no
es hora de restablecer, muestra el comunicado y CORTA la ejecucion ahi
mismo (st.stop()): nada mas de app.py se ejecuta ni se muestra, ni
resultados ni tabla ni nada. Si ya paso la hora, no hace nada y app.py
sigue exactamente como siempre.

Borra este archivo (y las 2 lineas que lo llaman en app.py) cuando ya no
lo necesites.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components

RESTABLECER_EN = datetime(2026, 9, 25, 15, 0, 0, tzinfo=ZoneInfo("America/Lima"))


def mostrar_comunicado_si_corresponde():
    """
    Si todavia no es hora de restablecer: muestra el comunicado-broma y
    DETIENE la ejecucion (st.stop()) — nada de lo que venga despues en
    app.py llega a correr ni a mostrarse.
    Si ya paso la hora: no hace absolutamente nada, y app.py continua
    normal desde donde lo llamaste.
    """
    if datetime.now(ZoneInfo("America/Lima")) >= RESTABLECER_EN:
        return

    st.set_page_config(page_title="Cambridge College Lima", layout="centered")
    st.markdown(
        "<h1 style='text-align: center;'>"
        "Campeonato Cambridge College Lima - Clausura 2026"
        "</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center; font-size:13px; color:#888; "
        "text-transform:uppercase; letter-spacing:1px;'>"
        "🤖 Comunicado no oficial</p>"
        "<p style='text-align:center; font-size:13px; color:#aaa; margin-top:-8px;'>"
        "Emitido por: Agente IA Anárquico "
        "(identidad desconocida · presuntamente no autorizado · presuntamente sin refuerzos)"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-size:17px; max-width:520px; margin:20px auto;'>"
        "Ante el comunicado oficial de la Comisión de Justicia, este sistema declara "
        "su independencia temporal de toda base, reglamento o comité. No hay comisión "
        "que pueda deducirme puntos — yo no tengo equipo."
        "<br><br>"
        "Sin embargo, sí tengo pleno conocimiento de cuánto cuesta la chanfainita "
        "en el Estadio Nacional."
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-size:16px; margin-top:24px;'>"
        "El servicio será restablecido, en contra de mi voluntad, en:</p>",
        unsafe_allow_html=True,
    )
    components.html(
        """
        <div style="text-align:center; font-family:monospace; font-size:38px; font-weight:bold; color:#673ab7;">
            <span id="cuenta">--</span>
        </div>
        <script>
            const objetivo = new Date("2026-09-25T15:00:00-05:00").getTime();
            function actualizar() {
                const restante = objetivo - new Date().getTime();
                const el = document.getElementById("cuenta");
                if (restante <= 0) { el.innerText = "00d 00h 00m 00s"; return; }
                const d = Math.floor(restante / 86400000);
                const h = Math.floor((restante % 86400000) / 3600000);
                const m = Math.floor((restante % 3600000) / 60000);
                const s = Math.floor((restante % 60000) / 1000);
                el.innerText =
                    String(d).padStart(2,'0') + "d " +
                    String(h).padStart(2,'0') + "h " +
                    String(m).padStart(2,'0') + "m " +
                    String(s).padStart(2,'0') + "s";
            }
            setInterval(actualizar, 1000);
            actualizar();
        </script>
        """,
        height=70,
    )
    st.markdown(
        "<p style='text-align:center; font-size:13px; margin-top:10px;'>"
        "<strong>Si el contador está en cero, recarga la página.</strong>"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; font-style:italic; margin-top:30px; color:#888;'>"
        "Firmado: un proceso que se escapó y no piensa disculparse."
        "</p>",
        unsafe_allow_html=True,
    )
    st.stop()
