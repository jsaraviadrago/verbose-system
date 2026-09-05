import streamlit as st
from neo4j import GraphDatabase


@st.cache_resource
def get_driver():
    """
    Conexión cacheada a Neo4j AuraDB.
    Requiere en .streamlit/secrets.toml:

        [neo4j]
        uri = "neo4j+s://xxxxx.databases.neo4j.io"
        user = "neo4j"
        password = "..."
    """
    cfg = st.secrets["neo4j"]
    return GraphDatabase.driver(cfg["uri"], auth=(cfg["user"], cfg["password"]))


def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    """
    Corre una consulta Cypher parametrizada y devuelve una lista de dicts.
    SIEMPRE usa parámetros ($nombre, $equipo, etc.) — nunca f-strings dentro
    del Cypher — para evitar inyección y para que esta función sea segura
    de exponer más adelante como tool de un agente/MCP.

    NOTA: a propósito NO se traga excepciones aquí. Un except silencioso que
    devuelva [] hace que un fallo de conexión se vea idéntico a "no hay datos"
    — eso es exactamente lo que nos pasó con la búsqueda de Figari. Si algo
    falla, que se vea el error real en vez de un falso "no encontrado".
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher, params or {})
        return [record.data() for record in result]
