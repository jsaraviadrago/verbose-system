import pandas as pd
import streamlit as st
from firestore_client import (
    get_partidos_clausura_2025, get_partidos_apertura_2025,
    get_partidos_clausura_2024, get_partidos_apertura_2024,
    get_goleadores_clausura_2025, get_goleadores_apertura_2025,
    get_goleadores_clausura_2024, get_goleadores_apertura_2024,
    get_tarjetas_clausura_2025, get_tarjetas_apertura_2025,
)

# ── Data loaders por temporada ─────────────────────────────────────────────────
LOADERS = {
    "Clausura 2025": {
        "goleadores": get_goleadores_clausura_2025,
        "tarjetas":   get_tarjetas_clausura_2025,
        "partidos":   get_partidos_clausura_2025,
    },
    "Apertura 2025": {
        "goleadores": get_goleadores_apertura_2025,
        "tarjetas":   get_tarjetas_apertura_2025,
        "partidos":   get_partidos_apertura_2025,
    },
    "Clausura 2024": {
        "goleadores": get_goleadores_clausura_2024,
        "tarjetas":   None,
        "partidos":   get_partidos_clausura_2024,
    },
    "Apertura 2024": {
        "goleadores": get_goleadores_apertura_2024,
        "tarjetas":   None,
        "partidos":   get_partidos_apertura_2024,
    },
}


@st.cache_data(ttl=300)
def _load(temporada: str, tipo: str) -> pd.DataFrame:
    func = LOADERS.get(temporada, {}).get(tipo)
    if func is None:
        return pd.DataFrame()
    try:
        return func()
    except Exception:
        return pd.DataFrame()


def _clean_goleadores(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina duplicados por nombre y equipo."""
    if df.empty:
        return df
    return df.drop_duplicates(subset=["NOMBRE Y APELLIDO", "EQUIPO"])


# ── Skills de Goleadores — temporada específica ────────────────────────────────
def top_goleadores(temporada: str, n: int = 10) -> str:
    df = _clean_goleadores(_load(temporada, "goleadores"))
    if df.empty:
        return f"No hay datos de goleadores para {temporada}."
    cols = [c for c in ["NOMBRE Y APELLIDO", "EQUIPO", "GOLES"] if c in df.columns]
    df = df[cols].sort_values("GOLES", ascending=False).head(n)
    return df.to_string(index=False)


def goles_jugador(nombre: str, temporada: str) -> str:
    df = _clean_goleadores(_load(temporada, "goleadores"))
    if df.empty:
        return f"No hay datos para {temporada}."
    mask = df["NOMBRE Y APELLIDO"].astype(str).str.lower().str.contains(nombre.lower())
    result = df[mask]
    if result.empty:
        return f"No se encontró a '{nombre}' en {temporada}."
    cols = [c for c in ["NOMBRE Y APELLIDO", "EQUIPO", "GOLES"] if c in result.columns]
    return result[cols].to_string(index=False)


def goles_equipo(equipo: str, temporada: str) -> str:
    df = _clean_goleadores(_load(temporada, "goleadores"))
    if df.empty:
        return f"No hay datos para {temporada}."
    mask = df["EQUIPO"].astype(str).str.lower().str.contains(equipo.lower())
    result = df[mask]
    if result.empty:
        return f"No se encontró al equipo '{equipo}' en {temporada}."
    cols = [c for c in ["NOMBRE Y APELLIDO", "EQUIPO", "GOLES"] if c in result.columns]
    return result[cols].sort_values("GOLES", ascending=False).to_string(index=False)


# ── Skills de Goleadores — todas las temporadas ────────────────────────────────
def goles_jugador_todas_temporadas(nombre: str) -> str:
    """
    Busca a un jugador en TODAS las temporadas.
    - Python calcula todo: desglose por temporada y total por equipo
    - El LLM solo presenta el resultado formateado — no calcula nada
    """
    registros = []

    for temporada in LOADERS.keys():
        df = _clean_goleadores(_load(temporada, "goleadores"))
        if df.empty:
            continue
        mask = df["NOMBRE Y APELLIDO"].astype(str).str.lower().str.contains(nombre.lower())
        result = df[mask]
        if result.empty:
            continue
        for _, row in result.iterrows():
            equipo = str(row.get("EQUIPO", "—")).strip()
            goles = int(row.get("GOLES", 0))
            registros.append((temporada, equipo, goles))

    if not registros:
        return f"No se encontró a '{nombre}' en ninguna temporada."

    # Deduplicar filas exactamente iguales
    seen = set()
    registros_limpios = []
    for temporada, equipo, goles in registros:
        key = (temporada, equipo, goles)
        if key not in seen:
            seen.add(key)
            registros_limpios.append((temporada, equipo, goles))
    registros = registros_limpios

    # ── Python calcula todo ────────────────────────────────────────────────────
    por_equipo = {}
    for temporada, equipo, goles in registros:
        if equipo not in por_equipo:
            por_equipo[equipo] = []
        por_equipo[equipo].append((temporada, goles))

    # Construir respuesta ya calculada
    nombre_jugador = nombre.title().replace("?", "").strip()
    lineas = [f"RESULTADO CALCULADO — presenta esto exactamente, sin sumar entre equipos:"]
    lineas.append(f"")
    lineas.append(f"Historial de {nombre_jugador} en la CLC:")

    for equipo, temporadas in por_equipo.items():
        lineas.append(f"")
        lineas.append(f"  {equipo}:")
        for temp, goles in temporadas:
            lineas.append(f"    - {temp}: {goles} goles")
        total = sum(g for _, g in temporadas)
        lineas.append(f"    Total en {equipo}: {total} goles")

    lineas.append(f"")
    lineas.append(f"REGLA: Muestra cada equipo por separado. NO sumes totales entre equipos distintos.")
    return "\n".join(lineas)


def top_goleadores_todas_temporadas(n: int = 10) -> str:
    """Ranking por mejor temporada individual — no suma entre equipos distintos."""
    filas = []
    for temporada in LOADERS.keys():
        df = _clean_goleadores(_load(temporada, "goleadores"))
        if df.empty:
            continue
        cols = [c for c in ["NOMBRE Y APELLIDO", "EQUIPO", "GOLES"] if c in df.columns]
        df = df[cols].copy()
        df["TEMPORADA"] = temporada
        filas.append(df)

    if not filas:
        return "No hay datos disponibles."

    combined = pd.concat(filas)
    ranking = (
        combined.sort_values("GOLES", ascending=False)
        .drop_duplicates(subset=["NOMBRE Y APELLIDO"])
        .head(n)[["NOMBRE Y APELLIDO", "EQUIPO", "TEMPORADA", "GOLES"]]
    )
    return (
        f"Top {n} goleadores CLC (mejor temporada individual):\n"
        f"{ranking.to_string(index=False)}\n"
        f"DATOS EXACTOS — no hagas cálculos adicionales."
    )


# ── Skills de Tarjetas ─────────────────────────────────────────────────────────
def tarjetas_jugador(nombre: str, temporada: str) -> str:
    df = _load(temporada, "tarjetas")
    if df.empty:
        return f"No hay datos de tarjetas para {temporada}."
    col_jugador = next((c for c in df.columns if "jugador" in c.lower() or "nombre" in c.lower()), None)
    if not col_jugador:
        return "No se encontró columna de jugador."
    mask = df[col_jugador].astype(str).str.lower().str.contains(nombre.lower())
    result = df[mask]
    if result.empty:
        return f"No se encontró a '{nombre}' en tarjetas de {temporada}."
    return result.to_string(index=False)


def tarjetas_equipo(equipo: str, temporada: str) -> str:
    df = _load(temporada, "tarjetas")
    if df.empty:
        return f"No hay datos de tarjetas para {temporada}."
    mask = df["EQUIPO"].astype(str).str.lower().str.contains(equipo.lower())
    result = df[mask]
    if result.empty:
        return f"No se encontró al equipo '{equipo}' en tarjetas de {temporada}."
    return result.to_string(index=False)


# ── Skills de Partidos ─────────────────────────────────────────────────────────
def resultados_equipo(equipo: str, temporada: str) -> str:
    df = _load(temporada, "partidos")
    if df.empty:
        return f"No hay datos de partidos para {temporada}."
    mask = pd.Series([False] * len(df), index=df.index)
    for col in df.select_dtypes(include="object").columns:
        mask |= df[col].astype(str).str.lower().str.contains(equipo.lower())
    result = df[mask]
    if result.empty:
        return f"No se encontraron partidos de '{equipo}' en {temporada}."
    cols = [c for c in ["Fecha", "Partido", "Resultado", "Equipo", "Goles"] if c in result.columns]
    return result[cols].to_string(index=False)


def todos_los_partidos(temporada: str) -> str:
    df = _load(temporada, "partidos")
    if df.empty:
        return f"No hay datos de partidos para {temporada}."
    cols = [c for c in ["Fecha", "Partido", "Resultado"] if c in df.columns]
    return df[cols].drop_duplicates().to_string(index=False)
