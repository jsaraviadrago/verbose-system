from __future__ import annotations

from pathlib import Path

import pandas as pd


DEFAULT_FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "CurrentTournament"
    / "fixture_schedule.csv"
)


def get_pending_fixture(
    df_partidos: pd.DataFrame,
    fixture_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Devuelve únicamente los partidos del fixture que todavía no han sido
    publicados en Firestore.

    La llave de comparación es FECHA_NUM + PARTIDO contra FECHA + PARTIDO
    de la colección partidos_clausura_2026.
    """
    path = Path(fixture_path) if fixture_path else DEFAULT_FIXTURE_PATH

    fixture = pd.read_csv(
        path,
        dtype={
            "FECHA_NUM": "int64",
            "PARTIDO": "int64",
            "HORA": "string",
            "EQUIPO_1": "string",
            "EQUIPO_2": "string",
        },
        parse_dates=["FECHA"],
    )

    if df_partidos is not None and not df_partidos.empty:
        played = df_partidos.copy()
        played.columns = (
            played.columns
            .astype(str)
            .str.strip()
            .str.upper()
        )

        if {"FECHA", "PARTIDO"}.issubset(played.columns):
            played = played[["FECHA", "PARTIDO"]].copy()
            played["FECHA"] = pd.to_numeric(
                played["FECHA"], errors="coerce"
            )
            played["PARTIDO"] = pd.to_numeric(
                played["PARTIDO"], errors="coerce"
            )
            played = (
                played.dropna()
                .astype({"FECHA": int, "PARTIDO": int})
                .drop_duplicates()
                .rename(columns={"FECHA": "FECHA_NUM"})
            )
            played["JUGADO"] = True

            fixture = fixture.merge(
                played,
                on=["FECHA_NUM", "PARTIDO"],
                how="left",
                validate="one_to_one",
            )
            fixture = fixture.loc[fixture["JUGADO"].isna()].copy()

    fixture = fixture.sort_values(
        ["FECHA", "HORA", "PARTIDO"]
    ).reset_index(drop=True)

    # Solo las cuatro columnas que debe ver el usuario.
    output = fixture[
        ["FECHA", "HORA", "EQUIPO_1", "EQUIPO_2"]
    ].copy()

    output["FECHA"] = output["FECHA"].dt.strftime("%d/%m/%Y")

    return output.rename(
        columns={
            "FECHA": "Fecha",
            "HORA": "Hora",
            "EQUIPO_1": "Equipo 1",
            "EQUIPO_2": "Equipo 2",
        }
    )
