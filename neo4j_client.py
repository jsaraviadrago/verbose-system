import os
from functools import lru_cache
from neo4j import GraphDatabase


def _get_credentials() -> dict:
    """
    Variables de entorno primero (para el servidor MCP, GitHub Actions, o
    cualquier proceso standalone). Si no están, cae a st.secrets — así la
    app de Streamlit sigue funcionando exactamente igual que antes, sin
    tener que configurar nada nuevo.
    """
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER")
    password = os.environ.get("NEO4J_PASSWORD")
    if uri and user and password:
        return {"uri": uri, "user": user, "password": password}

    try:
        import streamlit as st
        cfg = st.secrets["neo4j"]
        return {"uri": cfg["uri"], "user": cfg["user"], "password": cfg["password"]}
    except Exception as e:
        raise RuntimeError(
            "No se encontraron credenciales de Neo4j. Define NEO4J_URI, "
            "NEO4J_USER y NEO4J_PASSWORD como variables de entorno, o "
            "configura la sección [neo4j] en secrets.toml."
        ) from e


@lru_cache(maxsize=1)
def get_driver():
    """Conexión cacheada a Neo4j AuraDB (una sola vez por proceso)."""
    cfg = _get_credentials()
    return GraphDatabase.driver(cfg["uri"], auth=(cfg["user"], cfg["password"]))


def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    """
    Corre una consulta Cypher parametrizada y devuelve una lista de dicts.
    SIEMPRE usa parámetros ($nombre, $equipo, etc.) — nunca f-strings dentro
    del Cypher — para evitar inyección y para que esta función sea segura
    de exponer como tool de un agente/MCP.

    NOTA: a propósito NO se traga excepciones aquí. Un except silencioso que
    devuelva [] hace que un fallo de conexión se vea idéntico a "no hay datos".
    Si algo falla, que se vea el error real.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, params or {})
        return [record.data() for record in result]
