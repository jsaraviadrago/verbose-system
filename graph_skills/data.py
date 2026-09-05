"""
skills/data — Capa 1 (histórico 2024-2025)

Búsquedas básicas de "¿existe esto, y qué id tiene?". Estas son las skills
que usan las demás capas (history, statistics, graph) para resolver nombres
escritos por el usuario (a veces parciales, con errores de tilde, etc.)
contra los ids reales del grafo — nunca inventan datos, solo resuelven
identidad.
"""
from graph_skills._client import q


def buscar_jugador(nombre: str) -> str:
    """Confirma si un jugador existe en el grafo y devuelve su nombre canónico."""
    filas = q(
        "MATCH (p:Player) WHERE toLower(p.name) CONTAINS toLower($nombre) "
        "RETURN p.name AS nombre LIMIT 10",
        {"nombre": nombre},
    )
    if not filas:
        return f"No se encontró ningún jugador que coincida con '{nombre}'."
    nombres = [f["nombre"] for f in filas]
    return "Coincidencias encontradas: " + ", ".join(nombres)


def buscar_equipo(nombre: str) -> str:
    """
    Resuelve un nombre de equipo contra el nombre canónico actual,
    incluyendo si el nombre buscado es en realidad un alias histórico
    (ej. 'Holanda' -> resuelve a 'Liverpool').
    """
    filas = q(
        """
        MATCH (t:Team)-[:USED_NAME]->(n:TeamName)
        WHERE toLower(n.name) CONTAINS toLower($nombre)
        RETURN DISTINCT t.name AS equipo_actual, n.name AS coincidio_con, n.nameType AS tipo
        """,
        {"nombre": nombre},
    )
    if not filas:
        return f"No se encontró ningún equipo que coincida con '{nombre}'."
    lineas = [f"Equipo actual: {filas[0]['equipo_actual']}"]
    alias = [f["coincidio_con"] for f in filas if f["tipo"] != "CANONICAL"]
    if alias:
        lineas.append(f"(coincidió por nombre histórico: {', '.join(alias)})")
    return "\n".join(lineas)


def buscar_partido(equipo1: str, equipo2: str | None = None, edicion: str | None = None) -> str:
    """Encuentra partido(s) que involucran a un equipo, opcionalmente cruzado con otro y/o una edición."""
    cypher = """
        MATCH (t1:Team)-[:PLAYED_MATCH]->(m:Match)-[:IN_EDITION]->(e:Edition)
        WHERE toLower(t1.name) CONTAINS toLower($equipo1)
    """
    params = {"equipo1": equipo1}
    if equipo2:
        cypher += """
        MATCH (t2:Team)-[:PLAYED_MATCH]->(m)
        WHERE toLower(t2.name) CONTAINS toLower($equipo2) AND t1 <> t2
        """
        params["equipo2"] = equipo2
    if edicion:
        cypher += " AND toLower(e.name) CONTAINS toLower($edicion)"
        params["edicion"] = edicion
    cypher += " RETURN DISTINCT m.partido AS partido, m.fecha AS fecha, e.name AS edicion ORDER BY m.fecha"

    filas = q(cypher, params)
    if not filas:
        return f"No se encontraron partidos para esa combinación."
    lineas = [f"{f['partido']} — {f['edicion']} (fecha {f['fecha']})" for f in filas]
    return "\n".join(lineas)


def buscar_torneo() -> str:
    """Lista los torneos/ediciones disponibles en el grafo."""
    filas = q(
        "MATCH (e:Edition)-[:PART_OF]->(t:Tournament) "
        "RETURN t.name AS torneo, e.name AS edicion, e.year AS anio "
        "ORDER BY e.year"
    )
    if not filas:
        return "No hay torneos cargados en el grafo."
    lineas = [f"{f['edicion']} ({f['torneo']}, {f['anio']})" for f in filas]
    return "\n".join(lineas)
