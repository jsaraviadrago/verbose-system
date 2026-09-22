"""
skills/history — Capa 1 (histórico 2024-2025)

Reconstruye la "historia institucional" de un equipo: cambios de nombre,
en qué ediciones participó, y hasta qué fase llegó en cada una.
"""
from graph_skills._client import q, resolver_equipo


def cambios_nombre(equipo: str) -> str:
    """Nombres históricos que ha usado un equipo (ej. Holanda -> Liverpool)."""
    equipo_id, nombre_real, opciones = resolver_equipo(equipo)
    if equipo_id is None:
        if not opciones:
            return f"No se encontró al equipo '{equipo}'."
        return (
            f"Hay {len(opciones)} equipos que coinciden con '{equipo}': {', '.join(opciones)}. "
            "Pregúntale al usuario a cuál se refiere antes de dar un resultado."
        )

    alias = q(
        "MATCH (t:Team {id: $id})-[:USED_NAME]->(n:TeamName) WHERE n.nameType <> 'CANONICAL' "
        "RETURN n.name AS nombre",
        {"id": equipo_id},
    )
    if not alias:
        return f"{nombre_real} no registra cambios de nombre en el histórico."
    return (
        f"{nombre_real} se llamó anteriormente: {', '.join(a['nombre'] for a in alias)}\n"
        "REGLA: No inventes otros nombres anteriores que no aparezcan en esta lista."
    )


def participaciones_equipo(equipo: str) -> str:
    """Ediciones en las que participó un equipo."""
    equipo_id, nombre_real, opciones = resolver_equipo(equipo)
    if equipo_id is None:
        if not opciones:
            return f"No se encontró al equipo '{equipo}'."
        return (
            f"Hay {len(opciones)} equipos que coinciden con '{equipo}': {', '.join(opciones)}. "
            "Pregúntale al usuario a cuál se refiere antes de dar un resultado."
        )

    filas = q(
        "MATCH (t:Team {id: $id})-[:PARTICIPATED_IN]->(e:Edition) "
        "RETURN e.name AS edicion ORDER BY e.year",
        {"id": equipo_id},
    )
    if not filas:
        return f"No se encontró participación de '{nombre_real}' en ninguna edición."
    lineas = [f"Participaciones de {nombre_real}:"] + [f"  - {f['edicion']}" for f in filas]
    lineas.append("")
    lineas.append("REGLA: No inventes participaciones en ediciones que no aparezcan en esta lista.")
    return "\n".join(lineas)


def historia_equipo(equipo: str) -> str:
    """
    Reconstruye la historia completa de un equipo: nombres, participaciones
    y fase máxima alcanzada por edición (con resultado y contra quién) —
    todo en un solo resultado.
    """
    equipo_id, nombre_real, opciones = resolver_equipo(equipo)
    if equipo_id is None:
        if not opciones:
            return f"No se encontró al equipo '{equipo}' en el grafo histórico."
        return (
            f"Hay {len(opciones)} equipos que coinciden con '{equipo}': {', '.join(opciones)}. "
            "Pregúntale al usuario a cuál se refiere antes de dar un resultado."
        )

    alias = q(
        "MATCH (t:Team {id: $id})-[:USED_NAME]->(n:TeamName) WHERE n.nameType <> 'CANONICAL' "
        "RETURN n.name AS nombre",
        {"id": equipo_id},
    )
    fases = q(
        """
        MATCH (t:Team {id: $id})-[r:REACHED_STAGE]->(s:Stage)
        MATCH (e:Edition {id: r.editionId})
        OPTIONAL MATCH (t)-[:PLAYED_MATCH]->(m:Match)-[:AT_STAGE]->(s)
        WHERE EXISTS { (m)-[:IN_EDITION]->(e) }
        OPTIONAL MATCH (rival:Team)-[:PLAYED_MATCH]->(m) WHERE rival <> t
        RETURN e.name AS edicion, s.name AS fase_maxima, m.winnerTeamId AS winner_id, rival.name AS rival
        ORDER BY e.year
        """,
        {"id": equipo_id},
    )

    if not alias and not fases:
        return f"No se encontró historia registrada para '{nombre_real}' en el grafo."

    lineas = ["RESULTADO CALCULADO — presenta esto exactamente:", ""]
    lineas.append(f"Historia de {nombre_real} en la CLC:")

    if alias:
        lineas.append("")
        lineas.append(f"Nombres anteriores: {', '.join(a['nombre'] for a in alias)}")

    if fases:
        lineas.append("")
        lineas.append("Fase máxima alcanzada por edición:")
        for f in fases:
            resultado = ""
            if f.get("winner_id"):
                if f["winner_id"] == equipo_id:
                    resultado = " (ganó ese partido)"
                elif f.get("rival"):
                    resultado = f" (perdió ante {f['rival']})"
            lineas.append(f"  - {f['edicion']}: {f['fase_maxima']}{resultado}")
    else:
        lineas.append("")
        lineas.append("Sin registro de fases alcanzadas.")

    lineas.append("")
    lineas.append("REGLA: No inventes datos de ediciones que no aparezcan arriba.")
    return "\n".join(lineas)
