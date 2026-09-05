import streamlit as st
from neo4j_client import run_query


@st.cache_data(ttl=300)
def _cached_query(cypher: str, params_tuple: tuple) -> list[dict]:
    # st.cache_data necesita args hasheables → params_tuple en vez de dict
    return run_query(cypher, dict(params_tuple))


def q(cypher: str, params: dict | None = None) -> list[dict]:
    """Punto único de entrada al grafo para todas las skills. SIEMPRE parametrizado."""
    return _cached_query(cypher, tuple(sorted((params or {}).items())))
