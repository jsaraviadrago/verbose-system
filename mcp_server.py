"""
Servidor MCP para el grafo histórico de la Copa Cambridge League (2024-2025).

Expone las mismas 26 skills de graph_skills que ya usan los agentes
Historiador/Estadístico/Narrador en la app de Streamlit — mismo ajuar,
distinto protocolo de exposición. Cada tool ejecuta un Cypher fijo y
parametrizado; el cliente MCP (Claude Desktop, u otro) decide cuándo
llamar cada una, pero nunca genera Cypher libre.

Para correrlo localmente con Claude Desktop, agrega a tu
claude_desktop_config.json:

{
  "mcpServers": {
    "clc-grafo": {
      "command": "/ruta/a/tu/venv/bin/python3",
      "args": ["/ruta/completa/a/mcp_server.py"],
      "env": {
        "NEO4J_URI": "neo4j+s://TU_INSTANCIA.databases.neo4j.io",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "tu_password"
      }
    }
  }
}

Reinicia Claude Desktop después de guardar.
"""
from mcp.server.mcpserver import MCPServer

from graph_skills import (
    buscar_jugador,
    buscar_equipo,
    buscar_partido,
    buscar_torneo,
    listar_equipos,
    historia_equipo,
    cambios_nombre,
    participaciones_equipo,
    ficha_equipo,
    jugador_perfil_historico,
    comparar_equipos,
    comparar_jugadores,
    top_goleadores_historico,
    finales_por_equipo,
    premios_historicos,
    historial_entre_equipos,
    enfrentamientos_entre_equipos,
    partidos_por_fecha,
    racha_historica,
    equipo_mas_dominante,
    jugador_amplitud_ediciones,
    equipo_mayor_variedad_rivales,
    equipo_mayor_variedad_goleadores,
    encontrar_conexiones,
    explorar_vecinos,
)
from wiki import get_wiki

mcp = MCPServer("CLC Grafo Historico")


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
    """Encuentra CUÁNDO se jugó un partido (fecha, edición) de un equipo — NO trae marcador. Para el resultado, usa historial_entre_equipos_tool."""
    return buscar_partido(equipo1, equipo2, edicion)


@mcp.tool()
def buscar_torneo_tool() -> str:
    """Lista los torneos y ediciones disponibles en el grafo histórico."""
    return buscar_torneo()


@mcp.tool()
def listar_equipos_tool() -> str:
    """Lista TODOS los equipos que existen en el grafo histórico, de un tiro — úsala siempre que necesites saber qué equipos hay, en vez de reconstruirlo explorando partido por partido."""
    return listar_equipos()


@mcp.tool()
def historia_equipo_tool(equipo: str) -> str:
    """Historia institucional de un equipo: nombres anteriores, participaciones y fase máxima por edición (con resultado y contra quién)."""
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
def ficha_equipo_tool(equipo: str) -> str:
    """Ficha CONSOLIDADA de un equipo: nombres anteriores, fase máxima por edición, finales jugadas, y su goleador histórico — todo en una sola llamada."""
    return ficha_equipo(equipo)


@mcp.tool()
def jugador_perfil_historico_tool(nombre: str) -> str:
    """Perfil histórico completo de un jugador: goles por equipo/edición, tarjetas y premios. Si el nombre es ambiguo (varias personas), pide que se aclare en vez de adivinar."""
    return jugador_perfil_historico(nombre)


@mcp.tool()
def comparar_equipos_tool(equipo1: str, equipo2: str) -> str:
    """Compara dos equipos lado a lado: finales jugadas/ganadas, récord general y goleador histórico. NO es head-to-head — para eso usa historial_entre_equipos_tool."""
    return comparar_equipos(equipo1, equipo2)


@mcp.tool()
def comparar_jugadores_tool(nombre1: str, nombre2: str) -> str:
    """Compara dos jugadores lado a lado: goles por equipo, tarjetas y premios."""
    return comparar_jugadores(nombre1, nombre2)


@mcp.tool()
def top_goleadores_historico_tool(n: int = 10) -> str:
    """Ranking histórico de goleadores, sumado correctamente por jugador+equipo (nunca entre equipos distintos)."""
    return top_goleadores_historico(n)


@mcp.tool()
def finales_por_equipo_tool() -> str:
    """Cuántas finales jugó cada equipo, histórico, con detalle de en qué edición fue cada una y si ganó o perdió."""
    return finales_por_equipo()


@mcp.tool()
def premios_historicos_tool(award_type: str) -> str:
    """Ganadores históricos de un premio. award_type debe ser exactamente 'GOLDEN_BOOT' (Botín de Oro), 'BEST_PLAYER' (Mejor Jugador) o 'BEST_GOALKEEPER' (Mejor Arquero)."""
    return premios_historicos(award_type)


@mcp.tool()
def historial_entre_equipos_tool(equipo1: str, equipo2: str) -> str:
    """Lista PARTIDO POR PARTIDO todos los enfrentamientos entre dos equipos, con fase y marcador exacto (incluye quién ganó, incluso si fue por penales)."""
    return historial_entre_equipos(equipo1, equipo2)


@mcp.tool()
def enfrentamientos_entre_equipos_tool(equipo1: str | None = None, equipo2: str | None = None) -> str:
    """Estadística AGREGADA de enfrentamientos (victorias-empates-derrotas). Sin ningún equipo, escanea TODO el grafo para '¿qué equipo siempre/nunca le ha ganado a otro?'."""
    return enfrentamientos_entre_equipos(equipo1, equipo2)


@mcp.tool()
def partidos_por_fecha_tool(numero_fecha: int, edicion: str | None = None) -> str:
    """Lista los partidos jugados en una fecha/jornada específica, opcionalmente filtrado por edición."""
    return partidos_por_fecha(numero_fecha, edicion)


@mcp.tool()
def racha_historica_tool(equipo: str | None = None) -> str:
    """Racha ganadora, perdedora y de empates más larga. Sin equipo, busca en TODA la historia quién tiene la más larga de todos (incluye empates entre varios equipos si los hay)."""
    return racha_historica(equipo)


@mcp.tool()
def equipo_mas_dominante_tool() -> str:
    """Ranking histórico de 'dominancia' (métrica compuesta, NO es un título oficial del torneo)."""
    return equipo_mas_dominante()


@mcp.tool()
def jugador_amplitud_ediciones_tool(n: int = 10) -> str:
    """Ranking de jugadores por AMPLITUD: en cuántas ediciones distintas anotó, no por total de goles."""
    return jugador_amplitud_ediciones(n)


@mcp.tool()
def equipo_mayor_variedad_rivales_tool(n: int = 10) -> str:
    """Ranking de equipos por VARIEDAD de rivales distintos enfrentados, no por cantidad total de partidos."""
    return equipo_mayor_variedad_rivales(n)


@mcp.tool()
def equipo_mayor_variedad_goleadores_tool(n: int = 10) -> str:
    """Ranking de equipos por VARIEDAD de goleadores distintos, no por total de goles del equipo."""
    return equipo_mayor_variedad_goleadores(n)


@mcp.tool()
def encontrar_conexiones_tool(nombre1: str, nombre2: str) -> str:
    """Camino más corto en el grafo entre dos entidades cualquiera (jugadores, equipos, ediciones). Para descubrir relaciones no obvias."""
    return encontrar_conexiones(nombre1, nombre2)


@mcp.tool()
def explorar_vecinos_tool(nombre: str) -> str:
    """Todo lo directamente conectado a una entidad en el grafo (limitado a 30 resultados) — punto de partida para explorar antes de decidir qué contar."""
    return explorar_vecinos(nombre)


@mcp.tool()
def consultar_reglamento_tool() -> str:
    """Reglamento oficial (Bases Generales) del torneo: formato, sanciones, reglas de juego, desempates."""
    return get_wiki()


if __name__ == "__main__":
    mcp.run()
