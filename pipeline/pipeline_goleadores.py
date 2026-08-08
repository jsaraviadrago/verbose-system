from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from urllib.parse import quote

import pandas as pd
from google.cloud import firestore


PLAYER_PAIRS = [(f"Jugador{i}", f"Goles{i}") for i in range(1, 8)]

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
    """
    Clave conservadora para reconocer al mismo jugador.

    Unifica:
      José Pérez / JOSE  PEREZ / Jose Perez

    No hace fuzzy matching:
      Perez != Peres
    """
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
            "No se pudo leer la hoja de goleadores. "
            "Compártela como 'Cualquier persona con el enlace - Lector'."
        ) from exc

    df.columns = df.columns.astype(str).str.strip()
    return df


def validate_sheet_structure(df: pd.DataFrame) -> None:
    required = ["Fecha", "Equipo"]
    for player_col, goals_col in PLAYER_PAIRS:
        required.extend([player_col, goals_col])

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"La hoja Goleadores no tiene estas columnas: {missing}"
        )


def load_official_results(
    project_id: str,
    collection_name: str,
) -> pd.DataFrame:
    db = firestore.Client(project=project_id)
    docs = [doc.to_dict() for doc in db.collection(collection_name).stream()]

    if not docs:
        return pd.DataFrame(columns=["FECHA", "EQUIPO", "GOLES"])

    df = pd.DataFrame(docs)
    needed = ["FECHA", "EQUIPO", "GOLES"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(
            f"La colección {collection_name} no tiene campos: {missing}"
        )

    df = df[needed].copy()
    df["FECHA"] = pd.to_numeric(df["FECHA"], errors="raise").astype(int)
    df["GOLES"] = pd.to_numeric(df["GOLES"], errors="raise").astype(int)
    df["EQUIPO_NORM"] = df["EQUIPO"].map(normalize_team)

    duplicate = df.duplicated(["FECHA", "EQUIPO_NORM"], keep=False)
    if duplicate.any():
        raise ValueError(
            "Resultados oficiales contienen más de una fila para "
            "la misma Fecha + Equipo."
        )

    return df


def sheet_to_long(sheet: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Devuelve:
      responses: una fila por Fecha + Equipo enviado en el Form
      scorers: una fila por jugador con goles
    """
    data = sheet.copy()
    data = data.dropna(how="all")

    if data.empty:
        return (
            pd.DataFrame(columns=["FECHA", "EQUIPO", "EQUIPO_NORM"]),
            pd.DataFrame(
                columns=[
                    "FECHA",
                    "EQUIPO",
                    "EQUIPO_NORM",
                    "JUGADOR",
                    "PLAYER_KEY",
                    "GOLES",
                ]
            ),
        )

    data["Fecha"] = pd.to_numeric(data["Fecha"], errors="raise").astype(int)
    data["Equipo"] = data["Equipo"].astype(str).str.strip()
    data["EQUIPO_NORM"] = data["Equipo"].map(normalize_team)

    duplicated = data.duplicated(["Fecha", "EQUIPO_NORM"], keep=False)
    if duplicated.any():
        bad = data.loc[duplicated, ["Fecha", "Equipo"]]
        raise ValueError(
            "Hay más de una respuesta para el mismo equipo en una fecha. "
            "Corrige la hoja y deja una sola fila por Fecha + Equipo:\n"
            + bad.to_string(index=False)
        )

    parts: list[pd.DataFrame] = []

    for player_col, goals_col in PLAYER_PAIRS:
        part = data[
            ["Fecha", "Equipo", "EQUIPO_NORM", player_col, goals_col]
        ].copy()

        part.columns = [
            "FECHA",
            "EQUIPO",
            "EQUIPO_NORM",
            "JUGADOR",
            "GOLES",
        ]

        player_present = (
            part["JUGADOR"].notna()
            & part["JUGADOR"].astype(str).str.strip().ne("")
        )
        goals_present = part["GOLES"].notna() & part["GOLES"].astype(str).str.strip().ne("")

        mismatch = player_present ^ goals_present
        if mismatch.any():
            bad = part.loc[mismatch, ["FECHA", "EQUIPO", "JUGADOR", "GOLES"]]
            raise ValueError(
                f"{player_col}/{goals_col}: jugador y goles deben "
                "completarse juntos:\n"
                + bad.to_string(index=False)
            )

        part = part.loc[player_present & goals_present].copy()
        if part.empty:
            continue

        part["GOLES"] = pd.to_numeric(part["GOLES"], errors="raise")

        invalid_goals = (
            part["GOLES"].le(0)
            | part["GOLES"].mod(1).ne(0)
        )
        if invalid_goals.any():
            bad = part.loc[
                invalid_goals,
                ["FECHA", "EQUIPO", "JUGADOR", "GOLES"],
            ]
            raise ValueError(
                "Los goles de un goleador deben ser enteros mayores a 0:\n"
                + bad.to_string(index=False)
            )

        part["GOLES"] = part["GOLES"].astype(int)
        part["PLAYER_KEY"] = part["JUGADOR"].map(normalize_player_key)
        part["JUGADOR"] = part["JUGADOR"].map(display_player_name)

        parts.append(part)

    scorers = (
        pd.concat(parts, ignore_index=True)
        if parts
        else pd.DataFrame(
            columns=[
                "FECHA",
                "EQUIPO",
                "EQUIPO_NORM",
                "JUGADOR",
                "GOLES",
                "PLAYER_KEY",
            ]
        )
    )

    responses = data[["Fecha", "Equipo", "EQUIPO_NORM"]].rename(
        columns={"Fecha": "FECHA", "Equipo": "EQUIPO"}
    )

    return responses, scorers


def validate_teams(
    responses: pd.DataFrame,
    scorers: pd.DataFrame,
    official: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict], list[dict]]:
    """
    Valida independientemente cada Fecha + Equipo.

    Un equipo inválido queda pendiente, pero no bloquea a los demás.
    """
    official_lookup = {
        (int(row.FECHA), row.EQUIPO_NORM): int(row.GOLES)
        for row in official.itertuples(index=False)
    }

    response_keys = set(
        map(
            tuple,
            responses[["FECHA", "EQUIPO_NORM"]].to_numpy(),
        )
    )

    pending: list[dict] = []
    invalid: list[dict] = []
    valid_keys: set[tuple[int, str]] = set()

    # Equipos con resultado oficial pero sin respuesta en el Form.
    for row in official.itertuples(index=False):
        key = (int(row.FECHA), row.EQUIPO_NORM)
        if key not in response_keys:
            pending.append(
                {
                    "fecha": int(row.FECHA),
                    "equipo": str(row.EQUIPO),
                    "motivo": "sin respuesta en el Form",
                }
            )

    for response in responses.itertuples(index=False):
        key = (int(response.FECHA), response.EQUIPO_NORM)

        if key not in official_lookup:
            invalid.append(
                {
                    "fecha": int(response.FECHA),
                    "equipo": str(response.EQUIPO),
                    "motivo": "no existe resultado oficial publicado",
                }
            )
            continue

        team_rows = scorers.loc[
            scorers["FECHA"].eq(int(response.FECHA))
            & scorers["EQUIPO_NORM"].eq(response.EQUIPO_NORM)
        ].copy()

        placeholders = team_rows["JUGADOR"].map(is_placeholder_player)
        if placeholders.any():
            names = team_rows.loc[placeholders, "JUGADOR"].tolist()
            pending.append(
                {
                    "fecha": int(response.FECHA),
                    "equipo": str(response.EQUIPO),
                    "motivo": "jugadores pendientes de identificar",
                    "jugadores": names,
                }
            )
            continue

        official_goals = official_lookup[key]
        assigned_goals = int(team_rows["GOLES"].sum()) if not team_rows.empty else 0

        if assigned_goals != official_goals:
            pending.append(
                {
                    "fecha": int(response.FECHA),
                    "equipo": str(response.EQUIPO),
                    "motivo": "suma de goleadores no coincide",
                    "goles_oficiales": official_goals,
                    "goles_asignados": assigned_goals,
                }
            )
            continue

        valid_keys.add(key)

    if not valid_keys:
        valid = scorers.iloc[0:0].copy()
    else:
        key_index = pd.MultiIndex.from_tuples(
            sorted(valid_keys),
            names=["FECHA", "EQUIPO_NORM"],
        )
        current_index = pd.MultiIndex.from_frame(
            scorers[["FECHA", "EQUIPO_NORM"]]
        )
        valid = scorers.loc[current_index.isin(key_index)].copy()

    return valid, pending, invalid


def aggregate_scorers(valid: pd.DataFrame) -> pd.DataFrame:
    if valid.empty:
        return pd.DataFrame(
            columns=[
                "PLAYER_KEY",
                "NOMBRE Y APELLIDO",
                "EQUIPO",
                "GOLES",
            ]
        )

    # Dentro del mismo equipo, nombre normalizado identifica al jugador.
    # La grafía visible se toma del último registro disponible.
    visible = (
        valid.sort_values(["FECHA"])
        .groupby(["EQUIPO_NORM", "PLAYER_KEY"], as_index=False)
        .tail(1)[
            ["EQUIPO_NORM", "PLAYER_KEY", "EQUIPO", "JUGADOR"]
        ]
    )

    totals = (
        valid.groupby(
            ["EQUIPO_NORM", "PLAYER_KEY"],
            as_index=False,
        )["GOLES"]
        .sum()
    )

    result = totals.merge(
        visible,
        on=["EQUIPO_NORM", "PLAYER_KEY"],
        how="left",
        validate="one_to_one",
    )

    result = result.rename(
        columns={"JUGADOR": "NOMBRE Y APELLIDO"}
    )

    return (
        result[
            ["PLAYER_KEY", "NOMBRE Y APELLIDO", "EQUIPO", "GOLES"]
        ]
        .sort_values(
            ["GOLES", "NOMBRE Y APELLIDO", "EQUIPO"],
            ascending=[False, True, True],
        )
        .reset_index(drop=True)
    )


def _doc_id(team: str, player_key: str) -> str:
    raw = f"{normalize_team(team)}|{player_key}".encode("utf-8")
    return "g_" + hashlib.sha1(raw).hexdigest()[:20]


def reconcile_firestore(
    aggregated: pd.DataFrame,
    project_id: str,
    collection_name: str,
) -> dict:
    db = firestore.Client(project=project_id)
    collection = db.collection(collection_name)

    existing_snaps = list(collection.stream())
    existing = {
        snap.id: snap.to_dict()
        for snap in existing_snaps
    }

    desired: dict[str, dict] = {}

    for row in aggregated.to_dict(orient="records"):
        doc_id = _doc_id(row["EQUIPO"], row["PLAYER_KEY"])
        desired[doc_id] = {
            "PLAYER_KEY": str(row["PLAYER_KEY"]),
            "NOMBRE Y APELLIDO": str(row["NOMBRE Y APELLIDO"]),
            "EQUIPO": str(row["EQUIPO"]),
            "GOLES": int(row["GOLES"]),
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


def run_goleadores_pipeline() -> dict:
    project_id = env("GOOGLE_CLOUD_PROJECT", "futbol-ccl")
    sheet_id = env("GOLEADORES_SHEET_ID")
    sheet_name = env("GOLEADORES_SHEET_NAME", "Goleadores")
    results_collection = env(
        "FIRESTORE_RESULTS_COLLECTION",
        "partidos_clausura_2026",
    )
    scorers_collection = env(
        "FIRESTORE_SCORERS_COLLECTION",
        "goleadores_clausura_2026",
    )

    sheet = read_public_sheet(sheet_id, sheet_name)
    validate_sheet_structure(sheet)

    official = load_official_results(
        project_id,
        results_collection,
    )

    if official.empty:
        return {
            "status": "waiting_results",
            "valid_team_entries": 0,
            "pending": [],
            "invalid": [],
            "players": 0,
            "writes": 0,
            "deletes": 0,
        }

    responses, scorers = sheet_to_long(sheet)

    valid, pending, invalid = validate_teams(
        responses,
        scorers,
        official,
    )

    aggregated = aggregate_scorers(valid)

    # Medida de seguridad: si existen resultados oficiales pero ninguna
    # entrada válida, no vaciar una colección que ya pudiera tener datos.
    if aggregated.empty:
        return {
            "status": "no_valid_scorers",
            "valid_team_entries": 0,
            "pending": pending,
            "invalid": invalid,
            "players": 0,
            "writes": 0,
            "deletes": 0,
        }

    sync = reconcile_firestore(
        aggregated,
        project_id,
        scorers_collection,
    )

    valid_team_entries = int(
        valid[["FECHA", "EQUIPO_NORM"]]
        .drop_duplicates()
        .shape[0]
    )

    return {
        "status": "ok",
        "valid_team_entries": valid_team_entries,
        "pending": pending,
        "invalid": invalid,
        "players": int(len(aggregated)),
        **sync,
    }
