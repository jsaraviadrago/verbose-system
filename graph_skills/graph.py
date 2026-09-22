"""
skills/graph — Capa 1 (histórico 2024-2025)

Exploración libre de conexiones — exclusiva del Narrador. A diferencia de
statistics/history (una pregunta = una consulta fija), estas skills no
tienen una ruta predeterminada: es el tipo de skill que un agente
"explorador" usa para investigar antes de decidir qué contar. El HECHO que
devuelven sigue siendo exacto (viene del grafo); lo no-determinista es
QUÉ camino explorar, nunca el dato en sí.

OJO — límite conocido, no cerrado todavía: a diferencia de statistics.py y
history.py, estas dos funciones siguen resolviendo nombres por CONTAINS
directo, sin pasar por resolver_jugador/resolver_equipo — porque pueden
matchear cualquier tipo de nodo (jugador, equipo, edición), no solo uno.
Si el nombre buscado es ambiguo, hoy devuelve el primer camino que
encuentre en vez de avisar. Pendiente de blindar con el mismo patrón.
"""
import pandas as pd
from graph_skills._client import q


def encontrar_conexiones(nombre1: str, nombre2: str, max_hops: int = 4) -> str:
    """
    Camino más corto entre dos entidades cualquiera del grafo (jugador,
    equipo, edición, etc.) — útil para preguntas tipo '¿cómo se conectan
    X e Y?' que no encajan en una skill fija.
    """
    filas = q(
        f"""
        MATCH (a), (b)
        WHERE (toLower(a.name) CONTAINS toLower($n1))
          AND (toLower(b.name) CONTAINS toLower($n2))
          AND a <> b
        MATCH path = shortestPath((a)-[*..{max_hops}]-(b))
        RETURN [n IN nodes(path) | coalesce(n.name, n.id)] AS nodos,
               [r IN relationships(path) | type(r)] AS relaciones
        LIMIT 1
        """,
        {"n1": nombre1, "n2": nombre2},
    )
    if not filas:
        return f"No se encontró conexión entre '{nombre1}' y '{nombre2}' en menos de {max_hops} saltos."

    nodos = filas[0]["nodos"]
    relaciones = filas[0]["relaciones"]
    pasos = []
    for i, rel in enumerate(relaciones):
        pasos.append(f"{nodos[i]} -[{rel}]-> {nodos[i+1]}")
    return (
        "Camino encontrado:\n" + "\n".join(pasos) +
        "\n\nREGLA: Este es el ÚNICO camino que devolvió la consulta — no agregues "
        "pasos intermedios ni inventes otras conexiones."
    )


def explorar_vecinos(nombre: str, tipos_relacion: list[str] | None = None) -> str:
    """
    Todo lo directamente conectado a una entidad — el punto de partida
    típico de un agente explorador antes de seguir un hilo específico.
    """
    filtro = ""
    params = {"nombre": nombre}
    if tipos_relacion:
        filtro = "WHERE type(r) IN $tipos"
        params["tipos"] = tipos_relacion

    filas = q(
        f"""
        MATCH (a)-[r]-(b)
        WHERE toLower(coalesce(a.name, a.id)) CONTAINS toLower($nombre)
        {filtro}
        RETURN DISTINCT type(r) AS relacion, coalesce(b.name, b.id) AS conectado_con,
               labels(b)[0] AS tipo
        LIMIT 30
        """,
        params,
    )
    if not filas:
        return f"No se encontraron conexiones para '{nombre}'."
    df = pd.DataFrame(filas)
    return (
        f"Conexiones directas de '{nombre}':\n{df.to_string(index=False)}\n\n"
        "REGLA: No inventes conexiones que no aparezcan en esta lista (limitada a 30)."
    )
