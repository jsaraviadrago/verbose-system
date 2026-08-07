from __future__ import annotations

import os
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from google.cloud import firestore

app = Flask(__name__)

REQUIRED_SHEET_COLUMNS = [
    "Fecha", "Partido", "Equipo_1", "Goles_1", "Equipo_2", "Goles_2"
]
FIXTURE_KEYS = ["Fecha", "Partido", "Equipo_numero"]


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not str(value).strip():
        raise RuntimeError(f"Falta variable de entorno: {name}")
    return str(value).strip()


def normalize_name(s: pd.Series) -> pd.Series:
    aliases = {"CITY": "MANCHESTER CITY", "CETIC": "CELTIC"}
    return s.astype("string").str.strip().str.upper().replace(aliases)


def read_fixture(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    expected = {
        "Fecha", "Partido", "Cancha", "Hora", "Equipo_numero", "Equipo"
    }
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Fixture incompleto. Faltan: {sorted(missing)}")
    df["Fecha"] = pd.to_numeric(df["Fecha"], errors="raise").astype(int)
    df["Partido"] = pd.to_numeric(df["Partido"], errors="raise").astype(int)
    df["Equipo_numero"] = pd.to_numeric(df["Equipo_numero"], errors="raise").astype(int)
    df["Equipo_norm"] = normalize_name(df["Equipo"])
    return df


def read_google_sheet(spreadsheet_id: str, range_name: str) -> pd.DataFrame:
    import google.auth
    from googleapiclient.discovery import build

    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    values = (
        service.spreadsheets().values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute().get("values", [])
    )
    if not values:
        raise ValueError("La Google Sheet no devolvio datos.")

    header = [str(x).strip() for x in values[0]]
    rows = [r + [""] * (len(header) - len(r)) for r in values[1:]]
    df = pd.DataFrame(rows, columns=header)
    missing = [c for c in REQUIRED_SHEET_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"La Sheet no tiene estas columnas: {missing}")
    return df[REQUIRED_SHEET_COLUMNS].copy()


def validate_and_transform(sheet: pd.DataFrame, fixture: pd.DataFrame, target_date: int | None = None):
    s = sheet.copy()
    s = s.loc[~s["Partido"].astype("string").str.strip().eq("")].copy()

    s["Fecha"] = pd.to_numeric(s["Fecha"], errors="raise").astype(int)
    s["Partido"] = pd.to_numeric(s["Partido"], errors="raise").astype(int)
    s["Goles_1"] = pd.to_numeric(s["Goles_1"], errors="coerce")
    s["Goles_2"] = pd.to_numeric(s["Goles_2"], errors="coerce")

    if target_date is not None:
        s = s.loc[s["Fecha"].eq(target_date)].copy()
        if s.empty:
            raise ValueError(f"No existe la Fecha {target_date} en la Sheet.")

    filled = pd.concat([s["Goles_1"], s["Goles_2"]]).dropna()
    if ((filled < 0) | filled.mod(1).ne(0)).any():
        raise ValueError("Los goles deben ser enteros mayores o iguales a 0.")

    s["Equipo_1_norm"] = normalize_name(s["Equipo_1"])
    s["Equipo_2_norm"] = normalize_name(s["Equipo_2"])

    fixture_scope = fixture if target_date is None else fixture.loc[fixture["Fecha"].eq(target_date)]
    f1 = fixture_scope.loc[fixture_scope["Equipo_numero"].eq(1), ["Fecha", "Partido", "Equipo_norm"]].rename(columns={"Equipo_norm": "Esperado_1"})
    f2 = fixture_scope.loc[fixture_scope["Equipo_numero"].eq(2), ["Fecha", "Partido", "Equipo_norm"]].rename(columns={"Equipo_norm": "Esperado_2"})
    check = s.merge(f1, on=["Fecha", "Partido"], how="left").merge(f2, on=["Fecha", "Partido"], how="left")
    bad = (
        check["Esperado_1"].isna() | check["Esperado_2"].isna()
        | check["Equipo_1_norm"].ne(check["Esperado_1"])
        | check["Equipo_2_norm"].ne(check["Esperado_2"])
    )
    if bad.any():
        cols = ["Fecha", "Partido", "Equipo_1", "Equipo_2", "Esperado_1", "Esperado_2"]
        raise ValueError("La Sheet fue modificada en equipos/partidos:\n" + check.loc[bad, cols].to_string(index=False))

    # Debe existir exactamente una fila de captura por partido del fixture.
    expected_matches = fixture_scope[["Fecha", "Partido"]].drop_duplicates()
    actual_matches = s[["Fecha", "Partido"]].drop_duplicates()
    if len(expected_matches) != len(actual_matches):
        raise ValueError("Faltan o sobran partidos en la Sheet para la fecha solicitada.")

    both = s["Goles_1"].notna() & s["Goles_2"].notna()
    date_state = s.assign(_both=both, _any=s[["Goles_1", "Goles_2"]].notna().any(axis=1)).groupby("Fecha").agg(
        tiene_datos=("_any", "any"), completa=("_both", "all")
    )
    ready_dates = date_state.index[date_state["tiene_datos"] & date_state["completa"]].tolist()
    partial_dates = date_state.index[date_state["tiene_datos"] & ~date_state["completa"]].tolist()

    r1 = np.select(
        [s["Goles_1"].gt(s["Goles_2"]), s["Goles_1"].lt(s["Goles_2"]), both],
        ["G", "P", "E"], default=""
    )
    r2 = np.select(
        [s["Goles_2"].gt(s["Goles_1"]), s["Goles_2"].lt(s["Goles_1"]), both],
        ["G", "P", "E"], default=""
    )

    one = s[["Fecha", "Partido", "Goles_1"]].rename(columns={"Goles_1": "Goles"})
    one["Equipo_numero"] = 1
    one["Resultado"] = r1
    two = s[["Fecha", "Partido", "Goles_2"]].rename(columns={"Goles_2": "Goles"})
    two["Equipo_numero"] = 2
    two["Resultado"] = r2
    scores = pd.concat([one, two], ignore_index=True)

    static = fixture_scope[["Fecha", "Partido", "Cancha", "Hora", "Equipo_numero", "Equipo"]].copy()
    final = static.merge(scores, on=FIXTURE_KEYS, how="left", validate="one_to_one").sort_values(FIXTURE_KEYS)
    final["Goles"] = pd.to_numeric(final["Goles"], errors="coerce").astype("Int64")
    final["Resultado"] = final["Resultado"].fillna("")
    return final, ready_dates, partial_dates


def firestore_payload(row) -> dict:
    # Mayusculas para mantener compatibilidad con tus historicos y DataProcessor.
    return {
        "FECHA": int(row.Fecha),
        "PARTIDO": int(row.Partido),
        "CANCHA": int(row.Cancha) if pd.notna(row.Cancha) else None,
        "HORA": str(row.Hora),
        "EQUIPO_NUMERO": int(row.Equipo_numero),
        "EQUIPO": str(row.Equipo),
        "GOLES": int(row.Goles),
        "RESULTADO": str(row.Resultado),
    }


def publish_changed_rows(final: pd.DataFrame, ready_dates: list[int], collection: str) -> tuple[int, int]:
    if not ready_dates:
        return 0, 0

    db = firestore.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT") or None)
    publish = final.loc[final["Fecha"].isin(ready_dates)].copy()

    # Una fecha tiene solo 10 documentos. Leemos IDs deterministas para escribir solo cambios.
    changes = []
    reads = 0
    for row in publish.itertuples(index=False):
        doc_id = f"f{int(row.Fecha):02d}_p{int(row.Partido):03d}_e{int(row.Equipo_numero)}"
        ref = db.collection(collection).document(doc_id)
        payload = firestore_payload(row)
        snap = ref.get()
        reads += 1
        if (not snap.exists) or snap.to_dict() != payload:
            changes.append((ref, payload))

    if not changes:
        return 0, reads

    batch = db.batch()
    for ref, payload in changes:
        batch.set(ref, payload, merge=False)
    batch.commit()
    return len(changes), reads


def run_pipeline(target_date: int | None = None) -> dict:
    fixture = read_fixture(env("FIXTURE_PATH", "/app/CurrentTournament/fixture.csv"))
    sheet = read_google_sheet(env("GOOGLE_SHEET_ID"), env("GOOGLE_SHEET_RANGE", "Resultados!A1:F"))
    final, ready_dates, partial_dates = validate_and_transform(sheet, fixture, target_date)

    if target_date is not None and target_date not in ready_dates:
        return {
            "status": "incomplete",
            "fecha": target_date,
            "ready_dates": ready_dates,
            "partial_dates": partial_dates,
            "writes": 0,
        }

    writes, reads = publish_changed_rows(final, ready_dates, env("FIRESTORE_COLLECTION", "partidos_clausura_2026"))
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
    return jsonify({"status": "ok"})


@app.post("/sync")
def sync():
    try:
        payload = request.get_json(silent=True) or {}
        target_date = payload.get("fecha")
        if target_date is not None:
            target_date = int(target_date)
        return jsonify(run_pipeline(target_date)), 200
    except Exception as exc:
        app.logger.exception("Pipeline error")
        return jsonify({"status": "error", "error": str(exc)}), 400


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
