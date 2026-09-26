from functools import lru_cache
from neo4j_client import run_query


@lru_cache(maxsize=512)
def _cached_query(cypher: str, params_tuple: tuple) -> tuple:
    # lru_cache necesita resultado hasheable -> tuple de tuples en vez de
    # list[dict]. Se reconvierte a list[dict] en q(). Funciona igual dentro
    # de Streamlit que en un proceso standalone (servidor MCP, scripts, etc.)
    filas = run_query(cypher, dict(params_tuple))
    return tuple(tuple(sorted(fila.items())) for fila in filas)


def q(cypher: str, params: dict | None = None) -> list[dict]:
    """Punto único de entrada al grafo para todas las skills. SIEMPRE parametrizado."""
    params_tuple = tuple(sorted((params or {}).items()))
    cacheado = _cached_query(cypher, params_tuple)
    return [dict(fila) for fila in cacheado]


def resolver_jugador(nombre: str) -> tuple[str | None, str | None, list[str]]:
    """
    Resuelve un nombre de jugador a un PLAYER_ID único antes de dejar que
    una skill calcule algo sobre él.

    OJO: el chequeo es por ID de jugador, NO por texto del nombre. Hay
    casos reales donde 4 personas DISTINTAS comparten el nombre EXACTO
    'Jose Garcia' (mismo texto, PLAYER_ID distinto) — comparar solo el
    texto no alcanza para detectar esa ambigüedad, porque 'DISTINCT
    nombre' los colapsa a 1 aunque sean 4 personas.

    Devuelve (player_id, nombre, []) si hay exactamente una persona.
    Devuelve (None, None, opciones) si hay 0 o 2+ personas — cada opción
    incluye el equipo, para poder distinguir casos de nombre idéntico.
    """
    filas = q(
        """
        MATCH (p:Player) WHERE toLower(p.name) CONTAINS toLower($nombre)
        OPTIONAL MATCH (p)-[:PLAYED_FOR]->(t:Team)
        RETURN p.id AS id, p.name AS nombre, collect(DISTINCT t.name) AS equipos
        """,
        {"nombre": nombre},
    )
    if len(filas) == 1:
        return filas[0]["id"], filas[0]["nombre"], []
    opciones = []
    for f in filas:
        equipos = ", ".join(e for e in f["equipos"] if e) or "sin equipo registrado"
        opciones.append(f"{f['nombre']} (equipos: {equipos})")
    return None, None, sorted(opciones)


def resolver_equipo(nombre: str) -> tuple[str | None, str | None, list[str]]:
    """
    Resuelve un nombre de equipo (incluye alias históricos vía USED_NAME) a
    un TEAM_ID único. Mismo patrón que resolver_jugador: compara por ID de
    equipo, no por texto.

    Devuelve (team_id, nombre_canonico, []) si hay exactamente un equipo.
    Devuelve (None, None, opciones) si hay 0 o 2+ equipos.
    """
    filas = q(
        """
        MATCH (t:Team)-[:USED_NAME]->(n:TeamName)
        WHERE toLower(n.name) CONTAINS toLower($nombre)
        RETURN DISTINCT t.id AS id, t.name AS nombre
        """,
        {"nombre": nombre},
    )
    if len(filas) == 1:
        return filas[0]["id"], filas[0]["nombre"], []
    opciones = sorted({f["nombre"] for f in filas})
    return None, None, opciones


def resolver_entidad(nombre: str) -> tuple[str | None, str | None, list[str]]:
    """
    Igual que resolver_jugador/resolver_equipo, pero para CUALQUIER tipo de
    nodo del grafo (Player, Team, Edition, Stage, Match, Award...) — usado
    por encontrar_conexiones y explorar_vecinos, que a propósito no están
    limitadas a un solo tipo de entidad.

    Compara por elementId (identidad real del nodo), no por texto — mismo
    principio que los otros resolvers: dos entidades distintas nunca deben
    tratarse como una sola solo porque comparten nombre visible.

    Devuelve (element_id, nombre, []) si hay exactamente una entidad.
    Devuelve (None, None, opciones) si hay 0 o 2+ — cada opción incluye el
    tipo de nodo, para poder distinguir (ej. un jugador y un equipo con
    nombres parecidos).
    """
    filas = q(
        """
        MATCH (a)
        WHERE toLower(coalesce(a.name, a.id)) CONTAINS toLower($nombre)
        RETURN DISTINCT elementId(a) AS eid, coalesce(a.name, a.id) AS nombre, labels(a)[0] AS tipo
        """,
        {"nombre": nombre},
    )
    if len(filas) == 1:
        return filas[0]["eid"], filas[0]["nombre"], []
    opciones = sorted({f"{f['nombre']} ({f['tipo']})" for f in filas})
    return None, None, opciones
