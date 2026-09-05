"""
skills/graph — Capa 1 (histórico 2024-2025)

A diferencia de statistics/history (una pregunta = una consulta fija),
estas skills exploran el grafo sin una ruta predeterminada — es el tipo
de skill que un agente "Historiador" o "Scout" usaría para investigar
antes de decidir qué contar. El HECHO que devuelven sigue siendo exacto
(viene del grafo), pero QUÉ camino explorar puede variar según lo que el
agente le pida (max_hops, tipo de nodo, etc.) — ahí es donde entra lo
no-determinista, no en los datos mismos.
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
    return "Camino encontrado:\n" + "\n".join(pasos)


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
    return f"Conexiones directas de '{nombre}':\n{df.to_string(index=False)}"
