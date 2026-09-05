"""
skills/history — Capa 1 (histórico 2024-2025)

Reconstruye la "historia institucional" de un equipo: cambios de nombre,
en qué ediciones participó, y hasta qué fase llegó en cada una. Esto es
lo que en la conversación original se llamó team_history("X").
"""
import pandas as pd
from graph_skills._client import q


def cambios_nombre(equipo: str) -> str:
    """Nombres históricos que ha usado un equipo (ej. Holanda -> Liverpool)."""
    filas = q(
        """
        MATCH (t:Team)-[:USED_NAME]->(n:TeamName)
        WHERE toLower(t.name) CONTAINS toLower($equipo)
        RETURN t.name AS equipo_actual, n.name AS nombre, n.nameType AS tipo
        """,
        {"equipo": equipo},
    )
    if not filas:
        return f"No se encontró al equipo '{equipo}'."
    canonico = filas[0]["equipo_actual"]
    alias = [f["nombre"] for f in filas if f["tipo"] != "CANONICAL"]
    if not alias:
        return f"{canonico} no registra cambios de nombre en el histórico."
    return f"{canonico} se llamó anteriormente: {', '.join(alias)}"


def participaciones_equipo(equipo: str) -> str:
    """Ediciones en las que participó un equipo."""
    filas = q(
        """
        MATCH (t:Team)-[:PARTICIPATED_IN]->(e:Edition)
        WHERE toLower(t.name) CONTAINS toLower($equipo)
        RETURN t.name AS equipo, e.name AS edicion
        ORDER BY e.year
        """,
        {"equipo": equipo},
    )
    if not filas:
        return f"No se encontró participación de '{equipo}' en ninguna edición."
    df = pd.DataFrame(filas)
    return f"Participaciones de {filas[0]['equipo']}:\n{df[['edicion']].to_string(index=False)}"


def historia_equipo(equipo: str) -> str:
    """
    Reconstruye la historia completa de un equipo: nombres, participaciones
    y fase máxima alcanzada por edición — todo en un solo resultado, como el
    team_history("X") que se planteó originalmente.
    """
    nombres = q(
        """
        MATCH (t:Team)-[:USED_NAME]->(n:TeamName)
        WHERE toLower(t.name) CONTAINS toLower($equipo)
        RETURN t.name AS equipo_actual, n.name AS nombre, n.nameType AS tipo
        """,
        {"equipo": equipo},
    )
    fases = q(
        """
        MATCH (t:Team)-[r:REACHED_STAGE]->(s:Stage)
        WHERE toLower(t.name) CONTAINS toLower($equipo)
        MATCH (e:Edition {id: r.editionId})
        OPTIONAL MATCH (t)-[:PLAYED_MATCH]->(m:Match)-[:AT_STAGE]->(s)
        WHERE EXISTS { (m)-[:IN_EDITION]->(e) }
        OPTIONAL MATCH (rival:Team)-[:PLAYED_MATCH]->(m)
        WHERE rival <> t
        RETURN e.name AS edicion, s.name AS fase_maxima, t.id AS team_id,
               m.winnerTeamId AS winner_id, rival.name AS rival
        ORDER BY e.year
        """,
        {"equipo": equipo},
    )

    if not nombres and not fases:
        return f"No se encontró al equipo '{equipo}' en el grafo histórico."

    equipo_actual = nombres[0]["equipo_actual"] if nombres else fases[0].get("equipo", equipo)
    lineas = [f"RESULTADO CALCULADO — presenta esto exactamente:", ""]
    lineas.append(f"Historia de {equipo_actual} en la CLC:")

    alias = [n["nombre"] for n in nombres if n["tipo"] != "CANONICAL"]
    if alias:
        lineas.append("")
        lineas.append(f"Nombres anteriores: {', '.join(alias)}")

    if fases:
        lineas.append("")
        lineas.append("Fase máxima alcanzada por edición:")
        for f in fases:
            resultado = ""
            if f.get("winner_id"):
                if f["winner_id"] == f["team_id"]:
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