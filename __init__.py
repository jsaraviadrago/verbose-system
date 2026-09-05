"""
Paquete graph_skills — Capa 1 (histórico 2024-2025), organizado por categoría
según la arquitectura de skill library planeada:

    graph_skills/data.py        → resolución de entidades (buscar_*)
    graph_skills/history.py     → trayectoria institucional (historia_equipo, cambios_nombre)
    graph_skills/statistics.py  → números duros (goleadores, finales, premios, head-to-head)
    graph_skills/graph.py       → exploración libre (encontrar_conexiones, explorar_vecinos)

skills/narrative todavía no existe: las historias emergentes (rachas,
rivalidades, jugador protagonista) necesitan datos por partido individual,
que solo va a existir en la Capa 2 (CLC 2026 en vivo). Se agrega cuando
esa capa tenga datos reales que contar.
"""
from graph_skills.data import buscar_jugador, buscar_equipo, buscar_partido, buscar_torneo
from graph_skills.history import historia_equipo, cambios_nombre, participaciones_equipo
from graph_skills.statistics import (
    jugador_perfil_historico,
    top_goleadores_historico,
    finales_por_equipo,
    premios_historicos,
    historial_entre_equipos,
)
from graph_skills.graph import encontrar_conexiones, explorar_vecinos

__all__ = [
    "buscar_jugador", "buscar_equipo", "buscar_partido", "buscar_torneo",
    "historia_equipo", "cambios_nombre", "participaciones_equipo",
    "jugador_perfil_historico", "top_goleadores_historico", "finales_por_equipo",
    "premios_historicos", "historial_entre_equipos",
    "encontrar_conexiones", "explorar_vecinos",
]