"""
skills/statistics — Capa 1 (histórico 2024-2025)

Números duros: goles, finales, premios, head-to-head. Mismo contrato que
skills.py (Firestore): cada función devuelve un string ya formateado y
listo para presentar — el LLM no calcula nada, solo lo redacta.
"""
import pandas as pd
from graph_skills._client import q


def jugador_perfil_historico(nombre: str) -> str:
    """
    Perfil completo de un jugador: goles por equipo/edición, tarjetas y premios.
    Igual que goles_jugador_todas_temporadas en skills.py: nunca suma goles
    entre equipos distintos.
    """
    goles = q(
        """
        MATCH (p:Player)-[r:SCORED_IN]->(e:Edition)
        WHERE toLower(p.name) CONTAINS toLower($nombre)
        MATCH (t:Team {id: r.teamId})
        RETURN p.name AS jugador, e.name AS edicion, t.name AS equipo, r.goals AS goles
        ORDER BY e.year, e.name
        """,
        {"nombre": nombre},
    )
    tarjetas = q(
        """
        MATCH (p:Player)-[r:CARDED_IN]->(m:Match)
        WHERE toLower(p.name) CONTAINS toLower($nombre)
        MATCH (t:Team {id: r.teamId})
        OPTIONAL MATCH (rival:Team)-[:PLAYED_MATCH]->(m)
        WHERE rival <> t
        RETURN t.name AS equipo, m.fecha AS fecha, m.partido AS partido,
               rival.name AS rival, r.yellowCards AS amarillas, r.redCards AS rojas
        """,
        {"nombre": nombre},
    )
    premios = q(
        """
        MATCH (p:Player)-[:WON]->(a:Award)-[:IN_EDITION]->(e:Edition)
        WHERE toLower(p.name) CONTAINS toLower($nombre)
        RETURN a.name AS premio, e.name AS edicion
        ORDER BY e.year
        """,
        {"nombre": nombre},
    )

    if not goles and not tarjetas and not premios:
        return f"No se encontró a '{nombre}' en el grafo histórico."

    nombre_real = goles[0]["jugador"] if goles else nombre.title()
    lineas = [f"RESULTADO CALCULADO — presenta esto exactamente, sin sumar entre equipos:", ""]
    lineas.append(f"Historial de {nombre_real} en la CLC (fuente: grafo histórico):")

    if goles:
        por_equipo: dict[str, list] = {}
        for g in goles:
            por_equipo.setdefault(g["equipo"], []).append((g["edicion"], g["goles"]))
        lineas.append("")
        lineas.append("GOLES:")
        for equipo, registros in por_equipo.items():
            lineas.append(f"  {equipo}:")
            for edicion, goles_ed in registros:
                lineas.append(f"    - {edicion}: {goles_ed} goles")
            total = sum(g for _, g in registros)
            lineas.append(f"    Total en {equipo}: {total} goles")
    else:
        lineas.append("")
        lineas.append("GOLES: sin registros.")

    if tarjetas:
        lineas.append("")
        lineas.append("TARJETAS:")
        for t in tarjetas:
            partes = []
            if t["amarillas"]:
                partes.append(f"{t['amarillas']} amarilla(s)")
            if t["rojas"]:
                partes.append(f"{t['rojas']} roja(s)")
            rival = f" vs {t['rival']}" if t.get("rival") else ""
            lineas.append(
                f"  - Fecha {t['fecha']}, Partido {t['partido']}{rival} ({t['equipo']}): "
                f"{', '.join(partes) or 'sin sanción registrada'}"
            )

    if premios:
        lineas.append("")
        lineas.append("PREMIOS:")
        for p in premios:
            lineas.append(f"  - {p['premio']} ({p['edicion']})")

    lineas.append("")
    lineas.append("REGLA: Muestra cada equipo por separado en goles. NO sumes totales entre equipos distintos.")
    return "\n".join(lineas)


def top_goleadores_historico(n: int = 10) -> str:
    """
    Ranking real sumado entre ediciones DEL MISMO EQUIPO — a diferencia de
    top_goleadores_todas_temporadas (Firestore), que solo puede rankear por
    mejor temporada individual.
    """
    filas = q(
        """
        MATCH (p:Player)-[r:SCORED_IN]->(e:Edition)
        MATCH (t:Team {id: r.teamId})
        RETURN p.name AS jugador, t.name AS equipo, sum(r.goals) AS goles
        ORDER BY goles DESC
        LIMIT $n
        """,
        {"n": n},
    )
    if not filas:
        return "No hay datos de goles en el grafo."
    df = pd.DataFrame(filas)
    return (
        f"Top {n} goleadores CLC — histórico, por jugador+equipo (grafo):\n"
        f"{df.to_string(index=False)}\n"
        f"DATOS EXACTOS — no hagas cálculos adicionales, no sumes entre equipos distintos."
    )


def finales_por_equipo() -> str:
    """Cuántas finales jugó cada equipo, histórico."""
    filas = q(
        """
        MATCH (t:Team)-[r:REACHED_STAGE]->(s:Stage {id: 'stage_final'})
        RETURN t.name AS equipo, count(r) AS finales_jugadas
        ORDER BY finales_jugadas DESC
        """
    )
    if not filas:
        return "No hay datos de finales en el grafo."
    df = pd.DataFrame(filas)
    return f"Finales jugadas por equipo (histórico):\n{df.to_string(index=False)}"


def premios_historicos(award_type: str) -> str:
    """award_type: 'GOLDEN_BOOT' | 'BEST_PLAYER' | 'BEST_GOALKEEPER'"""
    filas = q(
        """
        MATCH (p:Player)-[:WON]->(a:Award {type: $award_type})-[:IN_EDITION]->(e:Edition)
        RETURN e.name AS edicion, p.name AS jugador, a.name AS premio
        ORDER BY e.year
        """,
        {"award_type": award_type},
    )
    if not filas:
        return f"No hay ganadores registrados para '{award_type}'."
    df = pd.DataFrame(filas)
    nombre_premio = filas[0]["premio"]
    return f"Ganadores históricos — {nombre_premio}:\n{df[['edicion', 'jugador']].to_string(index=False)}"


def historial_entre_equipos(equipo1: str, equipo2: str) -> str:
    """Head-to-head: todos los partidos jugados entre dos equipos."""
    filas = q(
        """
        MATCH (t1:Team)-[r1:PLAYED_MATCH]->(m:Match)<-[r2:PLAYED_MATCH]-(t2:Team)
        WHERE toLower(t1.name) CONTAINS toLower($equipo1)
          AND toLower(t2.name) CONTAINS toLower($equipo2)
          AND t1 <> t2
        MATCH (m)-[:IN_EDITION]->(e:Edition)
        RETURN e.name AS edicion, m.partido AS partido,
               t1.name AS equipo1, r1.goals AS goles1,
               t2.name AS equipo2, r2.goals AS goles2
        ORDER BY e.year
        """,
        {"equipo1": equipo1, "equipo2": equipo2},
    )
    if not filas:
        return f"No se encontraron partidos entre '{equipo1}' y '{equipo2}'."
    df = pd.DataFrame(filas)
    return f"Historial {equipo1} vs {equipo2}:\n{df.to_string(index=False)}"