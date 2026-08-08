from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from urllib.parse import quote

import pandas as pd
from google.cloud import firestore


CARD_SLOTS = {
    1: ("Jugador1", "Tarjeta1", ("Cantidad1",)),
    # Google Forms creó "Cantidad" en tu hoja actual para el segundo bloque.
    # También aceptamos "Cantidad2" por si luego corriges el encabezado.
    2: ("Jugador2", "Tarjeta2", ("Cantidad2", "Cantidad")),
    3: ("Jugador3", "Tarjeta3", ("Cantidad3",)),
    4: ("Jugador4", "Tarjeta4", ("Cantidad4",)),
    5: ("Jugador5", "Tarjeta5", ("Cantidad5",)),
    6: ("Jugador6", "Tarjeta6", ("Cantidad6",)),
    7: ("Jugador7", "Tarjeta7", ("Cantidad7",)),
}

TEAM_ALIASES = {
    "CITY": "MANCHESTER CITY",
    "CETIC": "CELTIC",
}

PLACEHOLDER_PATTERNS = (
    r"^JUGADOR\s*\d+$",
    r"^PLAYER\s*\d+$",
    r"^NN$",
    r"^N/N$",
    r"^DESCONOCIDO$",
    r"^PENDIENTE$",
    r"^POR\s+DEFINIR$",
)


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not str(value).strip():
        raise RuntimeError(f"Falta variable de entorno: {name}")
    return str(value).strip()


def _strip_accents(value: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(ch)
    )


def normalize_team(value: object) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"\s+", " ", text)
    return TEAM_ALIASES.get(text, text)


def normalize_player_key(value: object) -> str:
    text = str(value or "").strip()
    text = _strip_accents(text).upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def display_player_name(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text.title()


def is_placeholder_player(value: object) -> bool:
    key = normalize_player_key(value)
    if not key:
        return False
    return any(re.fullmatch(pattern, key) for pattern in PLACEHOLDER_PATTERNS)


def normalize_card_type(value: object) -> str:
    text = _strip_accents(str(value or "")).strip().upper()
    text = re.sub(r"\s+", " ", text)

    aliases = {
        "AMARILLA": "AMARILLA",
        "AMARILLAS": "AMARILLA",
        "YELLOW": "AMARILLA",
        "ROJA": "ROJA",
        "ROJAS": "ROJA",
        "RED": "ROJA",
    }

    if text not in aliases:
        raise ValueError(
            f"Tipo de tarjeta no reconocido: {value!r}. "
            "Usa Amarilla o Roja."
        )

    return aliases[text]


def read_public_sheet(spreadsheet_id: str, sheet_name: str) -> pd.DataFrame:
    encoded_sheet = quote(sheet_name)
    url = (
        "https://docs.google.com/spreadsheets/d/"
        f"{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet}"
    )

    try:
        df = pd.read_csv(url)
    except Exception as exc:
        raise ValueError(
            "No se pudo leer la hoja de tarjetas. "
            "Compártela como 'Cualquier persona con el enlace - Lector'."
        ) from exc

    df.columns = df.columns.astype(str).str.strip()
    return df


def _quantity_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise ValueError(
        "Falta columna de cantidad. Se esperaba una de: "
        + ", ".join(candidates)
    )


def validate_sheet_structure(df: pd.DataFrame) -> dict[int, str]:
    base = ["Fecha", "Equipo"]
    missing = [col for col in base if col not in df.columns]

    resolved_quantity: dict[int, str] = {}

    for slot, (player_col, card_col, quantity_candidates) in CARD_SLOTS.items():
        if player_col not in df.columns:
            missing.append(player_col)
        if card_col not in df.columns:
            missing.append(card_col)
        try:
            resolved_quantity[slot] = _quantity_column(df, quantity_candidates)
        except ValueError:
            missing.append("/".join(quantity_candidates))

    if missing:
        raise ValueError(
            f"La hoja Tarjetas no tiene estas columnas: {missing}"
        )

    return resolved_quantity


def load_official_team_dates(
    project_id: str,
    collection_name: str,
) -> pd.DataFrame:
    """Fecha + Equipo publicados oficialmente en resultados."""
    db = firestore.Client(project=project_id)
    docs = [doc.to_dict() for doc in db.collection(collection_name).stream()]

    if not docs:
        return pd.DataFrame(columns=["FECHA", "EQUIPO", "EQUIPO_NORM"])

    df = pd.DataFrame(docs)
    required = ["FECHA", "EQUIPO"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"La colección {collection_name} no tiene campos: {missing}"
        )

    df = df[required].copy()
    df["FECHA"] = pd.to_numeric(df["FECHA"], errors="raise").astype(int)
    df["EQUIPO_NORM"] = df["EQUIPO"].map(normalize_team)

    return df.drop_duplicates(["FECHA", "EQUIPO_NORM"])


def sheet_to_long(
    sheet: pd.DataFrame,
    quantity_columns: dict[int, str],
) -> pd.DataFrame:
    """Convierte las 7 ternas Jugador/Tarjeta/Cantidad a formato largo."""
    data = sheet.copy().dropna(how="all")

    columns = [
        "FECHA",
        "EQUIPO",
        "EQUIPO_NORM",
        "JUGADOR",
        "PLAYER_KEY",
        "TARJETA",
        "CANTIDAD",
    ]

    if data.empty:
        return pd.DataFrame(columns=columns)

    data["Fecha"] = pd.to_numeric(data["Fecha"], errors="raise").astype(int)
    data["Equipo"] = data["Equipo"].astype(str).str.strip()
    data["EQUIPO_NORM"] = data["Equipo"].map(normalize_team)

    parts: list[pd.DataFrame] = []

    for slot, (player_col, card_col, _) in CARD_SLOTS.items():
        quantity_col = quantity_columns[slot]

        part = data[
            ["Fecha", "Equipo", "EQUIPO_NORM", player_col, card_col, quantity_col]
        ].copy()
        part.columns = [
            "FECHA",
            "EQUIPO",
            "EQUIPO_NORM",
            "JUGADOR",
            "TARJETA",
            "CANTIDAD",
        ]

        player_present = (
            part["JUGADOR"].notna()
            & part["JUGADOR"].astype(str).str.strip().ne("")
        )
        card_present = (
            part["TARJETA"].notna()
            & part["TARJETA"].astype(str).str.strip().ne("")
        )
        quantity_present = (
            part["CANTIDAD"].notna()
            & part["CANTIDAD"].astype(str).str.strip().ne("")
        )

        any_present = player_present | card_present | quantity_present
        complete = player_present & card_present & quantity_present
        mismatch = any_present & ~complete

        if mismatch.any():
            bad = part.loc[
                mismatch,
                ["FECHA", "EQUIPO", "JUGADOR", "TARJETA", "CANTIDAD"],
            ]
            raise ValueError(
                f"Bloque Jugador{slot}/Tarjeta{slot}/Cantidad{slot}: "
                "los tres campos deben completarse juntos:\n"
                + bad.to_string(index=False)
            )

        part = part.loc[complete].copy()
        if part.empty:
            continue

        part["CANTIDAD"] = pd.to_numeric(part["CANTIDAD"], errors="raise")
        invalid_quantity = (
            part["CANTIDAD"].le(0)
            | part["CANTIDAD"].mod(1).ne(0)
        )

        if invalid_quantity.any():
            bad = part.loc[
                invalid_quantity,
                ["FECHA", "EQUIPO", "JUGADOR", "TARJETA", "CANTIDAD"],
            ]
            raise ValueError(
                "Cantidad de tarjetas debe ser un entero mayor a 0:\n"
                + bad.to_string(index=False)
            )

        part["CANTIDAD"] = part["CANTIDAD"].astype(int)
        part["TARJETA"] = part["TARJETA"].map(normalize_card_type)
        part["PLAYER_KEY"] = part["JUGADOR"].map(normalize_player_key)
        part["JUGADOR"] = part["JUGADOR"].map(display_player_name)

        parts.append(part)

    if not parts:
        return pd.DataFrame(columns=columns)

    return pd.concat(parts, ignore_index=True)[columns]


def validate_and_prepare(
    long_df: pd.DataFrame,
    official: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    """
    - Placeholders quedan pendientes y no se publican.
    - Fecha + Equipo debe existir en resultados oficiales.
    - Se permiten múltiples respuestas del mismo equipo/fecha.
    """
    if long_df.empty:
        return long_df.copy(), [], []

    official_keys = set(
        map(tuple, official[["FECHA", "EQUIPO_NORM"]].to_numpy())
    )

    pending: list[dict] = []
    invalid: list[dict] = []
    keep = pd.Series(True, index=long_df.index)

    placeholder_mask = long_df["JUGADOR"].map(is_placeholder_player)
    for row in long_df.loc[placeholder_mask].itertuples(index=False):
        pending.append(
            {
                "fecha": int(row.FECHA),
                "equipo": str(row.EQUIPO),
                "jugador": str(row.JUGADOR),
                "motivo": "jugador pendiente de identificar",
            }
        )
    keep &= ~placeholder_mask

    official_mask = long_df.apply(
        lambda row: (int(row["FECHA"]), row["EQUIPO_NORM"]) in official_keys,
        axis=1,
    )

    for row in long_df.loc[~official_mask].itertuples(index=False):
        invalid.append(
            {
                "fecha": int(row.FECHA),
                "equipo": str(row.EQUIPO),
                "jugador": str(row.JUGADOR),
                "motivo": "Fecha + Equipo no tiene resultado oficial publicado",
            }
        )
    keep &= official_mask

    return long_df.loc[keep].copy(), pending, invalid


def calculate_cards_by_date(valid: pd.DataFrame) -> pd.DataFrame:
    """
    Regla disciplinaria:

    - Todas las amarillas se cuentan.
    - Todas las rojas directas se cuentan.
    - Si un jugador acumula 2 amarillas EN LA MISMA FECHA,
      además genera 1 roja.
    - Amarillas de fechas distintas NO generan roja entre sí.

    Ejemplo en una fecha:
      2 amarillas => AMARILLAS=2, ROJAS_DERIVADAS=1.
    """
    cols = [
        "FECHA",
        "EQUIPO_NORM",
        "PLAYER_KEY",
        "EQUIPO",
        "JUGADOR",
        "AMARILLAS",
        "ROJAS",
    ]

    if valid.empty:
        return pd.DataFrame(columns=cols)

    work = valid.copy()
    work["AMARILLAS_RAW"] = work["CANTIDAD"].where(
        work["TARJETA"].eq("AMARILLA"),
        0,
    )
    work["ROJAS_DIRECTAS"] = work["CANTIDAD"].where(
        work["TARJETA"].eq("ROJA"),
        0,
    )

    grouped = (
        work.groupby(
            ["FECHA", "EQUIPO_NORM", "PLAYER_KEY"],
            as_index=False,
        )
        .agg(
            AMARILLAS=("AMARILLAS_RAW", "sum"),
            ROJAS_DIRECTAS=("ROJAS_DIRECTAS", "sum"),
        )
    )

    # Dos amarillas en la misma fecha generan una roja adicional,
    # pero las dos amarillas siguen contando.
    grouped["ROJAS_DERIVADAS"] = grouped["AMARILLAS"] // 2
    grouped["ROJAS"] = (
        grouped["ROJAS_DIRECTAS"] + grouped["ROJAS_DERIVADAS"]
    ).astype(int)
    grouped["AMARILLAS"] = grouped["AMARILLAS"].astype(int)

    visible = (
        work.sort_values(["FECHA"])
        .groupby(["FECHA", "EQUIPO_NORM", "PLAYER_KEY"], as_index=False)
        .tail(1)[
            ["FECHA", "EQUIPO_NORM", "PLAYER_KEY", "EQUIPO", "JUGADOR"]
        ]
    )

    result = grouped.merge(
        visible,
        on=["FECHA", "EQUIPO_NORM", "PLAYER_KEY"],
        how="left",
        validate="one_to_one",
    )

    return result[cols]


def aggregate_tournament(cards_by_date: pd.DataFrame) -> pd.DataFrame:
    cols = ["PLAYER_KEY", "JUGADOR", "EQUIPO", "AMARILLAS", "ROJAS"]

    if cards_by_date.empty:
        return pd.DataFrame(columns=cols)

    totals = (
        cards_by_date.groupby(
            ["EQUIPO_NORM", "PLAYER_KEY"],
            as_index=False,
        )
        .agg(
            AMARILLAS=("AMARILLAS", "sum"),
            ROJAS=("ROJAS", "sum"),
        )
    )

    visible = (
        cards_by_date.sort_values(["FECHA"])
        .groupby(["EQUIPO_NORM", "PLAYER_KEY"], as_index=False)
        .tail(1)[["EQUIPO_NORM", "PLAYER_KEY", "EQUIPO", "JUGADOR"]]
    )

    result = totals.merge(
        visible,
        on=["EQUIPO_NORM", "PLAYER_KEY"],
        how="left",
        validate="one_to_one",
    )

    return (
        result[cols]
        .sort_values(
            ["AMARILLAS", "ROJAS", "JUGADOR", "EQUIPO"],
            ascending=[False, False, True, True],
        )
        .reset_index(drop=True)
    )


def _doc_id(team: str, player_key: str) -> str:
    raw = f"{normalize_team(team)}|{player_key}".encode("utf-8")
    return "t_" + hashlib.sha1(raw).hexdigest()[:20]


def reconcile_firestore(
    aggregated: pd.DataFrame,
    project_id: str,
    collection_name: str,
) -> dict:
    db = firestore.Client(project=project_id)
    collection = db.collection(collection_name)

    existing_snaps = list(collection.stream())
    existing = {snap.id: snap.to_dict() for snap in existing_snaps}

    desired: dict[str, dict] = {}
    for row in aggregated.to_dict(orient="records"):
        doc_id = _doc_id(row["EQUIPO"], row["PLAYER_KEY"])
        desired[doc_id] = {
            "PLAYER_KEY": str(row["PLAYER_KEY"]),
            "JUGADOR": str(row["JUGADOR"]),
            "EQUIPO": str(row["EQUIPO"]),
            "AMARILLAS": int(row["AMARILLAS"]),
            "ROJAS": int(row["ROJAS"]),
        }

    to_set = {
        doc_id: payload
        for doc_id, payload in desired.items()
        if existing.get(doc_id) != payload
    }
    to_delete = sorted(set(existing) - set(desired))

    if not to_set and not to_delete:
        return {
            "writes": 0,
            "deletes": 0,
            "existing_reads": len(existing),
        }

    batch = db.batch()

    for doc_id, payload in to_set.items():
        batch.set(collection.document(doc_id), payload, merge=False)

    for doc_id in to_delete:
        batch.delete(collection.document(doc_id))

    batch.commit()

    return {
        "writes": len(to_set),
        "deletes": len(to_delete),
        "existing_reads": len(existing),
    }


def run_tarjetas_pipeline() -> dict:
    project_id = env("GOOGLE_CLOUD_PROJECT", "futbol-ccl")
    sheet_id = env("TARJETAS_SHEET_ID")
    sheet_name = env("TARJETAS_SHEET_NAME", "Tarjetas")
    results_collection = env(
        "FIRESTORE_RESULTS_COLLECTION",
        "partidos_clausura_2026",
    )
    cards_collection = env(
        "FIRESTORE_CARDS_COLLECTION",
        "tarjetas_clausura_2026",
    )

    sheet = read_public_sheet(sheet_id, sheet_name)
    quantity_columns = validate_sheet_structure(sheet)

    official = load_official_team_dates(project_id, results_collection)
    if official.empty:
        return {
            "status": "waiting_results",
            "records": 0,
            "players": 0,
            "pending": [],
            "invalid": [],
            "writes": 0,
            "deletes": 0,
        }

    long_df = sheet_to_long(sheet, quantity_columns)
    if long_df.empty:
        return {
            "status": "no_cards",
            "records": 0,
            "players": 0,
            "pending": [],
            "invalid": [],
            "writes": 0,
            "deletes": 0,
        }

    valid, pending, invalid = validate_and_prepare(long_df, official)
    cards_by_date = calculate_cards_by_date(valid)
    aggregated = aggregate_tournament(cards_by_date)

    # Seguridad: si todo lo ingresado está pendiente/inválido, no vaciar
    # una colección existente por accidente.
    if aggregated.empty:
        return {
            "status": "no_valid_cards",
            "records": int(len(long_df)),
            "players": 0,
            "pending": pending,
            "invalid": invalid,
            "writes": 0,
            "deletes": 0,
        }

    sync = reconcile_firestore(aggregated, project_id, cards_collection)

    return {
        "status": "ok",
        "records": int(len(valid)),
        "players": int(len(aggregated)),
        "pending": pending,
        "invalid": invalid,
        **sync,
    }
