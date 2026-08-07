import pandas as pd
import numpy as np


class DataProcessor:
    def __init__(self):
        pass

    @staticmethod
    def _played(df):
        data = df.copy()
        data.columns = data.columns.str.strip().str.upper()
        data["GOLES"] = pd.to_numeric(data["GOLES"], errors="coerce")
        return data[data["RESULTADO"].isin(["G", "E", "P"]) & data["GOLES"].notna()].copy()

    def get_general_stats(self, df):
        """Metricas solo sobre partidos ya jugados."""
        data = self._played(df)
        if data.empty:
            return 0.0, 0, pd.DataFrame(columns=["FECHA", "Total_Goles", "Prom_Goles"])

        # Cada partido aparece dos veces, una fila por equipo.
        total_goles = data["GOLES"].sum()
        partidos = data["PARTIDO"].nunique()
        promedio = total_goles / partidos if partidos else 0.0

        stats = data.groupby("FECHA").agg(
            Total_Goles=("GOLES", "sum"),
            Partidos=("PARTIDO", "nunique")
        ).reset_index()
        stats["Prom_Goles"] = stats["Total_Goles"] / stats["Partidos"]
        stats["FECHA"] = stats["FECHA"].astype(str)
        return promedio, int(total_goles), stats[["FECHA", "Total_Goles", "Prom_Goles"]]

    def process_standings(self, df):
        """Tabla unica de posiciones para Clausura 2026, sin grupos."""
        data = self._played(df)
        if data.empty:
            return pd.DataFrame(columns=["EQUIPO", "G", "E", "P", "PJ", "GF", "GC", "GD", "Puntos", "PythEXP"])

        data["g_count"] = data["RESULTADO"].eq("G").astype(int)
        data["e_count"] = data["RESULTADO"].eq("E").astype(int)
        data["p_count"] = data["RESULTADO"].eq("P").astype(int)

        gf = data.groupby("EQUIPO")["GOLES"].sum().rename("GF").reset_index()

        goals = data.pivot(index="PARTIDO", columns="EQUIPO_NUMERO", values="GOLES").rename(columns={1: "G1", 2: "G2"}).reset_index()
        teams = data.pivot(index="PARTIDO", columns="EQUIPO_NUMERO", values="EQUIPO").rename(columns={1: "E1", 2: "E2"}).reset_index()
        matches = teams.merge(goals, on="PARTIDO", validate="one_to_one")
        gc = pd.concat([
            matches[["E1", "G2"]].rename(columns={"E1": "EQUIPO", "G2": "GC"}),
            matches[["E2", "G1"]].rename(columns={"E2": "EQUIPO", "G1": "GC"}),
        ], ignore_index=True).groupby("EQUIPO")["GC"].sum().reset_index()

        stats = data.groupby("EQUIPO").agg(G=("g_count", "sum"), E=("e_count", "sum"), P=("p_count", "sum")).reset_index()
        stats["PJ"] = stats["G"] + stats["E"] + stats["P"]
        stats = stats.merge(gf, on="EQUIPO", how="left").merge(gc, on="EQUIPO", how="left").fillna(0)
        stats["GD"] = stats["GF"] - stats["GC"]
        stats["Puntos"] = stats["G"] * 3 + stats["E"]
        gf_p, gc_p = stats["GF"] ** 1.2, stats["GC"] ** 1.2
        stats["PythEXP"] = (gf_p / (gf_p + gc_p)).fillna(0).round(2)
        return stats.sort_values(["Puntos", "GD", "GF", "GC"], ascending=[False, False, False, True]).reset_index(drop=True)

    def process_match_results(self, df):
        """Todos los resultados de Clausura 2026, sin grupos."""
        data = self._played(df)
        if data.empty:
            return pd.DataFrame(columns=["FECHA", "CANCHA", "HORA", "Equipo A", "Goles A", "Equipo B", "Goles B"])

        info = data[["FECHA", "PARTIDO", "CANCHA", "HORA"]].drop_duplicates()
        teams = data.pivot(index=["FECHA", "PARTIDO"], columns="EQUIPO_NUMERO", values="EQUIPO").rename(columns={1: "Equipo A", 2: "Equipo B"}).reset_index()
        goals = data.pivot(index=["FECHA", "PARTIDO"], columns="EQUIPO_NUMERO", values="GOLES").rename(columns={1: "Goles A", 2: "Goles B"}).reset_index()
        out = teams.merge(goals, on=["FECHA", "PARTIDO"]).merge(info, on=["FECHA", "PARTIDO"])
        return out[["FECHA", "CANCHA", "HORA", "Equipo A", "Goles A", "Equipo B", "Goles B"]].sort_values(["FECHA", "HORA", "CANCHA"])

    def process_cards_and_scorers(self, cards_df, scorers_df):
        """Se conserva para tus historicos de disciplina/goleadores."""
        scorers = scorers_df.copy()
        scorers.columns = scorers.columns.str.strip().str.upper()
        nombre_col = "NOMBRE Y APELLIDO" if "NOMBRE Y APELLIDO" in scorers.columns else "JUGADOR"
        scorers["GOLES"] = pd.to_numeric(scorers["GOLES"], errors="coerce").fillna(0).astype(int)
        scorers[nombre_col] = scorers[nombre_col].str.title()
        goleadores_sorted = scorers.sort_values("GOLES", ascending=False).head(10)

        cards = cards_df.copy()
        cards.columns = cards.columns.str.strip().str.upper()
        cols_f = [c for c in cards.columns if "F" in c and len(c) <= 3]
        for col in cols_f:
            cards[col] = cards[col].astype(str).str.upper().str.strip()
        cards["Amarillas"] = cards[cols_f].apply(lambda x: x.str.contains("A", na=False).sum(), axis=1)
        cards["Rojas"] = cards[cols_f].apply(lambda x: x.str.contains("1R", na=False).sum(), axis=1)
        cards["Puntos_Sancion"] = cards[cols_f].apply(
            lambda x: x.str.contains("1A", na=False).sum()
            + x.str.contains("2A", na=False).sum() * 2
            + x.str.contains("1R", na=False).sum() * 3,
            axis=1,
        )
        team_cards = cards.groupby("EQUIPO")["Puntos_Sancion"].sum().reset_index().sort_values("Puntos_Sancion", ascending=False)
        team_cards.columns = ["Equipo", "Total_Sancion"]
        top_y = cards[cards["Amarillas"] > 0][["JUGADOR", "EQUIPO", "Amarillas"]].sort_values("Amarillas", ascending=False).head(8)
        top_r = cards[cards["Rojas"] > 0][["JUGADOR", "EQUIPO", "Rojas"]].sort_values("Rojas", ascending=False).head(8)
        return goleadores_sorted[[nombre_col, "EQUIPO", "GOLES"]], team_cards, top_y, top_r
