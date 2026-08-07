from __future__ import annotations

import os

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from google.cloud import firestore

app = Flask(__name__)

# "Partido" is deliberately NOT required in Google Sheets.
# It may remain as a visible/hidden informational column, but the pipeline ignores it.
REQUIRED_SHEET_COLUMNS = [
    "Fecha",
    "Equipo_1",
    "Goles_1",
    "Equipo_2",
    "Goles_2",
]

FIXTURE_COLUMNS = [
    "Fecha",
    "Partido",
    "Cancha",
    "Hora",
    "Equipo_numero",
    "Equipo",
]

FIXTURE_KEYS = ["Fecha", "Partido", "Equipo_numero"]


def env(name: str, default: str | None = None) -> str:
    """Read a required environment variable, optionally with a default."""
    value = os.getenv(name, default)
    if value is None or not str(value).strip():
        raise RuntimeError(f"Falta variable de entorno: {name}")
    return str(value).strip()


def normalize_name(s: pd.Series) -> pd.Series:
    """
    Normalize team names so known aliases do not break matching.

    Add new aliases here if future fixture/source files use other variants.
    """
    aliases = {
        "CITY": "MANCHESTER CITY",
        "CETIC": "CELTIC",
    }

    return (
        s.astype("string")
        .str.strip()
        .str.upper()
        .replace(aliases)
    )


def add_pair_key(
    df: pd.DataFrame,
    team_1_col: str,
    team_2_col: str,
) -> pd.DataFrame:
    """
    Add an order-independent pair key.

    CITY vs CELTIC and CELTIC vs CITY therefore identify the same fixture.
    The original team columns are retained so goals can later be assigned
    to the correct fixture side.
    """
    out = df.copy()

    left = out[team_1_col].astype("string")
    right = out[team_2_col].astype("string")

    out["_PAIR_A"] = left.where(left <= right, right)
    out["_PAIR_B"] = right.where(left <= right, left)

    return out


def read_fixture(path: str) -> pd.DataFrame:
    """Read and validate the static current-tournament fixture."""
    # sep=None lets pandas detect comma or semicolon, which makes the file
    # robust to how it was exported.
    df = pd.read_csv(path, sep=None, engine="python")
    df.columns = df.columns.astype(str).str.strip()

    missing = set(FIXTURE_COLUMNS).difference(df.columns)
    if missing:
        raise ValueError(
            f"Fixture incompleto. Faltan: {sorted(missing)}"
        )

    # Ignore accidental extra columns. The fixture is static metadata only.
    df = df[FIXTURE_COLUMNS].copy()

    df["Fecha"] = pd.to_numeric(
        df["Fecha"], errors="raise"
    ).astype(int)

    df["Partido"] = pd.to_numeric(
        df["Partido"], errors="raise"
    ).astype(int)

    df["Equipo_numero"] = pd.to_numeric(
        df["Equipo_numero"], errors="raise"
    ).astype(int)

    if not df["Equipo_numero"].isin([1, 2]).all():
        raise ValueError(
            "Equipo_numero del fixture solo puede ser 1 o 2."
        )

    # Every fixture match must have exactly two rows: team 1 and team 2.
    match_sizes = (
        df.groupby(["Fecha", "Partido"])
        .size()
    )
    if not match_sizes.eq(2).all():
        bad = match_sizes[~match_sizes.eq(2)]
        raise ValueError(
            "Cada partido del fixture debe tener exactamente 2 filas. "
            f"Problemas: {bad.to_dict()}"
        )

    side_counts = (
        df.groupby(["Fecha", "Partido"])["Equipo_numero"]
        .nunique()
    )
    if not side_counts.eq(2).all():
        bad = side_counts[~side_counts.eq(2)]
        raise ValueError(
            "Cada partido debe contener Equipo_numero 1 y 2. "
            f"Problemas: {bad.to_dict()}"
        )

    df["Equipo_norm"] = normalize_name(df["Equipo"])

    if df["Equipo_norm"].isna().any() or df["Equipo_norm"].eq("").any():
        raise ValueError("Hay equipos vacios en el fixture.")

    return df


def fixture_as_matches(fixture: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the two-row-per-match fixture into one row per match.

    The returned table contains the authoritative Partido, Cancha, Hora
    and both teams.
    """
    team_1 = (
        fixture.loc[
            fixture["Equipo_numero"].eq(1),
            [
                "Fecha",
                "Partido",
                "Cancha",
                "Hora",
                "Equipo",
                "Equipo_norm",
            ],
        ]
        .rename(
            columns={
                "Equipo": "Fixture_Equipo_1",
                "Equipo_norm": "Fixture_Equipo_1_norm",
            }
        )
    )

    team_2 = (
        fixture.loc[
            fixture["Equipo_numero"].eq(2),
            [
                "Fecha",
                "Partido",
                "Equipo",
                "Equipo_norm",
            ],
        ]
        .rename(
            columns={
                "Equipo": "Fixture_Equipo_2",
                "Equipo_norm": "Fixture_Equipo_2_norm",
            }
        )
    )

    matches = team_1.merge(
        team_2,
        on=["Fecha", "Partido"],
        how="inner",
        validate="one_to_one",
    )

    matches = add_pair_key(
        matches,
        "Fixture_Equipo_1_norm",
        "Fixture_Equipo_2_norm",
    )

    # Within one date, a pair of teams must identify exactly one match.
    duplicated_pairs = matches.duplicated(
        ["Fecha", "_PAIR_A", "_PAIR_B"],
        keep=False,
    )

    if duplicated_pairs.any():
        bad = matches.loc[
            duplicated_pairs,
            [
                "Fecha",
                "Partido",
                "Fixture_Equipo_1",
                "Fixture_Equipo_2",
            ],
        ]
        raise ValueError(
            "El fixture contiene una pareja de equipos duplicada "
            "dentro de la misma fecha:\n"
            + bad.to_string(index=False)
        )

    return matches


def read_google_sheet(
    spreadsheet_id: str,
    range_name: str,
) -> pd.DataFrame:
    """Read the results capture sheet using Cloud Run credentials."""
    import google.auth
    from googleapiclient.discovery import build

    creds, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly"
        ]
    )

    service = build(
        "sheets",
        "v4",
        credentials=creds,
        cache_discovery=False,
    )

    values = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        )
        .execute()
        .get("values", [])
    )

    if not values:
        raise ValueError(
            "La Google Sheet no devolvio datos."
        )

    header = [str(x).strip() for x in values[0]]

    if len(header) != len(set(header)):
        raise ValueError(
            "La Google Sheet contiene encabezados duplicados."
        )

    rows = [
        r + [""] * (len(header) - len(r))
        for r in values[1:]
    ]

    df = pd.DataFrame(rows, columns=header)

    missing = [
        c
        for c in REQUIRED_SHEET_COLUMNS
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"La Sheet no tiene estas columnas: {missing}"
        )

    # Extra columns such as "Partido" are allowed and ignored.
    return df[REQUIRED_SHEET_COLUMNS].copy()


def validate_and_transform(
    sheet: pd.DataFrame,
    fixture: pd.DataFrame,
    target_date: int | None = None,
):
    """
    Validate the Google Sheet and convert it to the Firestore row format.

    The match is resolved by:
        Fecha + unordered pair of teams

    Therefore:
    - Sheet row order does not matter.
    - The optional Partido column does not matter.
    - Equipo_1 / Equipo_2 may even be swapped and goals still map correctly.
    """
    s = sheet.copy()

    # Remove fully blank rows only.
    nonempty = (
        s[REQUIRED_SHEET_COLUMNS]
        .astype("string")
        .fillna("")
        .apply(lambda col: col.str.strip())
        .ne("")
        .any(axis=1)
    )
    s = s.loc[nonempty].copy()

    if s.empty:
        raise ValueError(
            "La Google Sheet no contiene partidos."
        )

    s["Fecha"] = pd.to_numeric(
        s["Fecha"],
        errors="raise",
    ).astype(int)

    s["Goles_1"] = pd.to_numeric(
        s["Goles_1"],
        errors="coerce",
    )

    s["Goles_2"] = pd.to_numeric(
        s["Goles_2"],
        errors="coerce",
    )

    if target_date is not None:
        s = s.loc[
            s["Fecha"].eq(target_date)
        ].copy()

        if s.empty:
            raise ValueError(
                f"No existe la Fecha {target_date} en la Sheet."
            )

    # Validate any goals that have actually been entered.
    filled = pd.concat(
        [s["Goles_1"], s["Goles_2"]]
    ).dropna()

    if (
        (filled < 0)
        | filled.mod(1).ne(0)
    ).any():
        raise ValueError(
            "Los goles deben ser enteros mayores o iguales a 0."
        )

    s["Equipo_1_norm"] = normalize_name(
        s["Equipo_1"]
    )
    s["Equipo_2_norm"] = normalize_name(
        s["Equipo_2"]
    )

    invalid_teams = (
        s["Equipo_1_norm"].isna()
        | s["Equipo_2_norm"].isna()
        | s["Equipo_1_norm"].eq("")
        | s["Equipo_2_norm"].eq("")
        | s["Equipo_1_norm"].eq(
            s["Equipo_2_norm"]
        )
    )

    if invalid_teams.any():
        bad = s.loc[
            invalid_teams,
            ["Fecha", "Equipo_1", "Equipo_2"],
        ]
        raise ValueError(
            "Hay filas con equipos vacios o iguales:\n"
            + bad.to_string(index=False)
        )

    s = add_pair_key(
        s,
        "Equipo_1_norm",
        "Equipo_2_norm",
    )

    # No pair should appear twice in the same date in the capture sheet.
    duplicated_sheet_pairs = s.duplicated(
        ["Fecha", "_PAIR_A", "_PAIR_B"],
        keep=False,
    )

    if duplicated_sheet_pairs.any():
        bad = s.loc[
            duplicated_sheet_pairs,
            ["Fecha", "Equipo_1", "Equipo_2"],
        ]
        raise ValueError(
            "La Sheet contiene partidos duplicados:\n"
            + bad.to_string(index=False)
        )

    fixture_scope = (
        fixture
        if target_date is None
        else fixture.loc[
            fixture["Fecha"].eq(target_date)
        ].copy()
    )

    if fixture_scope.empty:
        raise ValueError(
            "El fixture no contiene la fecha solicitada."
        )

    fixture_matches = fixture_as_matches(
        fixture_scope
    )

    # Resolve every Sheet row to the authoritative fixture match.
    resolved = s.merge(
        fixture_matches,
        on=["Fecha", "_PAIR_A", "_PAIR_B"],
        how="left",
        validate="one_to_one",
    )

    not_found = resolved["Partido"].isna()

    if not_found.any():
        bad = resolved.loc[
            not_found,
            ["Fecha", "Equipo_1", "Equipo_2"],
        ]
        raise ValueError(
            "Hay partidos en la Sheet que no existen "
            "en el fixture:\n"
            + bad.to_string(index=False)
        )

    # Ensure the Sheet has every fixture match exactly once.
    expected_matches = fixture_matches[
        ["Fecha", "Partido"]
    ].drop_duplicates()

    actual_matches = resolved[
        ["Fecha", "Partido"]
    ].drop_duplicates()

    if (
        len(expected_matches) != len(actual_matches)
        or len(resolved) != len(expected_matches)
    ):
        expected_ids = set(
            map(
                tuple,
                expected_matches[
                    ["Fecha", "Partido"]
                ].to_numpy(),
            )
        )
        actual_ids = set(
            map(
                tuple,
                actual_matches[
                    ["Fecha", "Partido"]
                ].to_numpy(),
            )
        )

        missing_matches = sorted(
            expected_ids - actual_ids
        )
        extra_matches = sorted(
            actual_ids - expected_ids
        )

        raise ValueError(
            "Faltan o sobran partidos en la Sheet. "
            f"Faltantes: {missing_matches}. "
            f"Sobrantes: {extra_matches}."
        )

    # A fixture can be written in either direction in the Sheet.
    # Reorient goals to the fixture's official Equipo_numero 1 / 2.
    sheet_team_1_is_fixture_1 = (
        resolved["Equipo_1_norm"]
        .eq(resolved["Fixture_Equipo_1_norm"])
    )

    sheet_team_2_is_fixture_1 = (
        resolved["Equipo_2_norm"]
        .eq(resolved["Fixture_Equipo_1_norm"])
    )

    orientation_valid = (
        sheet_team_1_is_fixture_1
        | sheet_team_2_is_fixture_1
    )

    if not orientation_valid.all():
        bad = resolved.loc[
            ~orientation_valid,
            [
                "Fecha",
                "Equipo_1",
                "Equipo_2",
                "Fixture_Equipo_1",
                "Fixture_Equipo_2",
            ],
        ]
        raise ValueError(
            "No se pudo orientar uno o mas partidos:\n"
            + bad.to_string(index=False)
        )

    resolved["Goles_fixture_1"] = np.where(
        sheet_team_1_is_fixture_1,
        resolved["Goles_1"],
        resolved["Goles_2"],
    )

    resolved["Goles_fixture_2"] = np.where(
        sheet_team_1_is_fixture_1,
        resolved["Goles_2"],
        resolved["Goles_1"],
    )

    both = (
        resolved["Goles_fixture_1"].notna()
        & resolved["Goles_fixture_2"].notna()
    )

    any_goal = (
        resolved[
            ["Goles_fixture_1", "Goles_fixture_2"]
        ]
        .notna()
        .any(axis=1)
    )

    date_state = (
        resolved.assign(
            _both=both,
            _any=any_goal,
        )
        .groupby("Fecha")
        .agg(
            tiene_datos=("_any", "any"),
            completa=("_both", "all"),
        )
    )

    ready_dates = (
        date_state.index[
            date_state["tiene_datos"]
            & date_state["completa"]
        ]
        .astype(int)
        .tolist()
    )

    partial_dates = (
        date_state.index[
            date_state["tiene_datos"]
            & ~date_state["completa"]
        ]
        .astype(int)
        .tolist()
    )

    # Vectorized G/P/E calculation.
    result_1 = np.select(
        [
            resolved["Goles_fixture_1"].gt(
                resolved["Goles_fixture_2"]
            ),
            resolved["Goles_fixture_1"].lt(
                resolved["Goles_fixture_2"]
            ),
            both,
        ],
        ["G", "P", "E"],
        default="",
    )

    result_2 = np.select(
        [
            resolved["Goles_fixture_2"].gt(
                resolved["Goles_fixture_1"]
            ),
            resolved["Goles_fixture_2"].lt(
                resolved["Goles_fixture_1"]
            ),
            both,
        ],
        ["G", "P", "E"],
        default="",
    )

    team_1_scores = resolved[
        ["Fecha", "Partido", "Goles_fixture_1"]
    ].rename(
        columns={
            "Goles_fixture_1": "Goles"
        }
    )

    team_1_scores["Equipo_numero"] = 1
    team_1_scores["Resultado"] = result_1

    team_2_scores = resolved[
        ["Fecha", "Partido", "Goles_fixture_2"]
    ].rename(
        columns={
            "Goles_fixture_2": "Goles"
        }
    )

    team_2_scores["Equipo_numero"] = 2
    team_2_scores["Resultado"] = result_2

    scores = pd.concat(
        [team_1_scores, team_2_scores],
        ignore_index=True,
    )

    static = fixture_scope[
        [
            "Fecha",
            "Partido",
            "Cancha",
            "Hora",
            "Equipo_numero",
            "Equipo",
        ]
    ].copy()

    final = (
        static.merge(
            scores,
            on=FIXTURE_KEYS,
            how="left",
            validate="one_to_one",
        )
        .sort_values(FIXTURE_KEYS)
        .reset_index(drop=True)
    )

    final["Goles"] = pd.to_numeric(
        final["Goles"],
        errors="coerce",
    ).astype("Int64")

    final["Resultado"] = (
        final["Resultado"]
        .fillna("")
        .astype(str)
    )

    return (
        final,
        ready_dates,
        partial_dates,
    )


def firestore_payload(row) -> dict:
    """
    Create a Firestore document compatible with the historical
    column naming expected by DataProcessor.
    """
    if pd.isna(row.Goles):
        raise ValueError(
            "Se intento publicar un partido sin goles."
        )

    return {
        "FECHA": int(row.Fecha),
        "PARTIDO": int(row.Partido),
        "CANCHA": (
            int(row.Cancha)
            if pd.notna(row.Cancha)
            else None
        ),
        "HORA": str(row.Hora),
        "EQUIPO_NUMERO": int(row.Equipo_numero),
        "EQUIPO": str(row.Equipo),
        "GOLES": int(row.Goles),
        "RESULTADO": str(row.Resultado),
    }


def publish_changed_rows(
    final: pd.DataFrame,
    ready_dates: list[int],
    collection: str,
) -> tuple[int, int]:
    """
    Publish only changed documents.

    Deterministic document IDs make the operation idempotent:
    rerunning the same date does not create duplicates.
    """
    if not ready_dates:
        return 0, 0

    db = firestore.Client(
        project=(
            os.getenv("GOOGLE_CLOUD_PROJECT")
            or None
        )
    )

    publish = final.loc[
        final["Fecha"].isin(ready_dates)
    ].copy()

    changes = []
    reads = 0

    # Firestore reads/writes are network operations, so iteration is
    # appropriate here; calculation above remains vectorized.
    for row in publish.itertuples(index=False):
        doc_id = (
            f"f{int(row.Fecha):02d}_"
            f"p{int(row.Partido):03d}_"
            f"e{int(row.Equipo_numero)}"
        )

        ref = (
            db.collection(collection)
            .document(doc_id)
        )

        payload = firestore_payload(row)
        snap = ref.get()
        reads += 1

        if (
            not snap.exists
            or snap.to_dict() != payload
        ):
            changes.append(
                (ref, payload)
            )

    if not changes:
        return 0, reads

    batch = db.batch()

    for ref, payload in changes:
        batch.set(
            ref,
            payload,
            merge=False,
        )

    batch.commit()

    return len(changes), reads


def run_pipeline(
    target_date: int | None = None,
) -> dict:
    """Execute one complete Sheet -> validation -> Firestore sync."""
    fixture = read_fixture(
        env(
            "FIXTURE_PATH",
            "/app/CurrentTournament/fixture.csv",
        )
    )

    sheet = read_google_sheet(
        env("GOOGLE_SHEET_ID"),
        env(
            "GOOGLE_SHEET_RANGE",
            "Resultados!A1:F",
        ),
    )

    final, ready_dates, partial_dates = (
        validate_and_transform(
            sheet,
            fixture,
            target_date,
        )
    )

    # A request from Apps Script targets one date.
    # Never publish it until every match in that date has both scores.
    if (
        target_date is not None
        and target_date not in ready_dates
    ):
        return {
            "status": "incomplete",
            "fecha": target_date,
            "ready_dates": ready_dates,
            "partial_dates": partial_dates,
            "writes": 0,
            "firestore_reads": 0,
        }

    writes, reads = publish_changed_rows(
        final,
        ready_dates,
        env(
            "FIRESTORE_COLLECTION",
            "partidos_clausura_2026",
        ),
    )

    return {
        "status": "ok",
        "fecha": target_date,
        "ready_dates": ready_dates,
        "partial_dates": partial_dates,
        "writes": writes,
        "firestore_reads": reads,
    }


@app.get("/health")
def health():
    return jsonify(
        {"status": "ok"}
    )


@app.post("/sync")
def sync():
    try:
        payload = (
            request.get_json(silent=True)
            or {}
        )

        target_date = payload.get("fecha")

        if target_date is not None:
            target_date = int(target_date)

            if target_date <= 0:
                raise ValueError(
                    "fecha debe ser un entero positivo."
                )

        result = run_pipeline(
            target_date
        )

        return jsonify(result), 200

    except Exception as exc:
        app.logger.exception(
            "Pipeline error"
        )

        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(exc),
                }
            ),
            400,
        )


if __name__ == "__main__":
    port = int(
        os.getenv(
            "PORT",
            "8080",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )
