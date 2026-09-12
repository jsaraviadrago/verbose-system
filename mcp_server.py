"""
Servidor MCP para el grafo histórico de la Copa Lima de Clubes (2024-2025).

Expone las mismas funciones de graph_skills que ya usan los agentes
Historiador/Estadístico/Narrador en la app de Streamlit — mismo ajuar,
distinto protocolo de exposición. Cada tool ejecuta un Cypher fijo y
parametrizado; el cliente MCP (Claude Desktop, u otro) decide cuándo
llamar cada una, pero nunca genera Cypher libre.

Para correrlo localmente con Claude Desktop, agrega a tu
claude_desktop_config.json:

{
  "mcpServers": {
    "clc-grafo": {
      "command": "python3",
      "args": ["/ruta/completa/a/mcp_server.py"],
      "env": {
        "NEO4J_URI": "neo4j+s://TU_INSTANCIA.databases.neo4j.io",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "tu_password"
      }
    }
  }
}

Reinicia Claude Desktop después de guardar — debería aparecer "clc-grafo"
en el ícono de herramientas (🔨) del chat.
"""
from mcp.server.fastmcp import FastMCP

from graph_skills import (
    buscar_jugador,
    buscar_equipo,
    buscar_partido,
    buscar_torneo,
    historia_equipo,
    cambios_nombre,
    participaciones_equipo,
    jugador_perfil_historico,
    top_goleadores_historico,
    finales_por_equipo,
    premios_historicos,
    historial_entre_equipos,
    encontrar_conexiones,
    explorar_vecinos,
)
from wiki import get_wiki

mcp = FastMCP("CLC Grafo Historico")


@mcp.tool()
def buscar_jugador_tool(nombre: str) -> str:
    """Confirma si un jugador existe en el grafo histórico de la CLC (2024-2025) y devuelve coincidencias de nombre."""
    return buscar_jugador(nombre)


@mcp.tool()
def buscar_equipo_tool(nombre: str) -> str:
    """Resuelve un nombre de equipo, incluyendo nombres históricos/alias (ej. 'Holanda' -> 'Liverpool')."""
    return buscar_equipo(nombre)


@mcp.tool()
def buscar_partido_tool(equipo1: str, equipo2: str | None = None, edicion: str | None = None) -> str:
    """Encuentra partidos de un equipo, opcionalmente cruzado con otro equipo y/o edición."""
    return buscar_partido(equipo1, equipo2, edicion)


@mcp.tool()
def buscar_torneo_tool() -> str:
    """Lista los torneos y ediciones disponibles en el grafo histórico."""
    return buscar_torneo()


@mcp.tool()
def historia_equipo_tool(equipo: str) -> str:
    """Historia institucional completa de un equipo: nombres anteriores, participaciones y fase máxima por edición."""
    return historia_equipo(equipo)


@mcp.tool()
def cambios_nombre_tool(equipo: str) -> str:
    """Nombres históricos que ha usado un equipo."""
    return cambios_nombre(equipo)


@mcp.tool()
def participaciones_equipo_tool(equipo: str) -> str:
    """Ediciones en las que participó un equipo."""
    return participaciones_equipo(equipo)


@mcp.tool()
def jugador_perfil_historico_tool(nombre: str) -> str:
    """Perfil histórico completo de un jugador: goles por equipo/edición, tarjetas y premios."""
    return jugador_perfil_historico(nombre)


@mcp.tool()
def top_goleadores_historico_tool(n: int = 10) -> str:
    """Ranking histórico de goleadores, sumado correctamente por jugador+equipo (nunca entre equipos distintos)."""
    return top_goleadores_historico(n)


@mcp.tool()
def finales_por_equipo_tool() -> str:
    """Cuántas finales jugó cada equipo, histórico (2024-2025)."""
    return finales_por_equipo()


@mcp.tool()
def premios_historicos_tool(award_type: str) -> str:
    """Ganadores históricos de un premio. award_type debe ser exactamente 'GOLDEN_BOOT' (Botín de Oro), 'BEST_PLAYER' (Mejor Jugador) o 'BEST_GOALKEEPER' (Mejor Arquero)."""
    return premios_historicos(award_type)


@mcp.tool()
def historial_entre_equipos_tool(equipo1: str, equipo2: str) -> str:
    """Head-to-head: todos los partidos jugados entre dos equipos específicos."""
    return historial_entre_equipos(equipo1, equipo2)


@mcp.tool()
def encontrar_conexiones_tool(nombre1: str, nombre2: str) -> str:
    """Camino más corto en el grafo entre dos entidades cualquiera (jugadores, equipos, ediciones). Para descubrir relaciones no obvias."""
    return encontrar_conexiones(nombre1, nombre2)


@mcp.tool()
def explorar_vecinos_tool(nombre: str) -> str:
    """Todo lo directamente conectado a una entidad en el grafo — punto de partida para explorar antes de decidir qué contar."""
    return explorar_vecinos(nombre)


@mcp.tool()
def consultar_reglamento_tool() -> str:
    """Reglamento oficial (Bases Generales) del torneo: formato, sanciones, reglas de juego, desempates."""
    return get_wiki()


if __name__ == "__main__":
    mcp.run()
