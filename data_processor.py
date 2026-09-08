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

    def calcular_racha(self, match_results, equipo, n=3):
        """Ultimos n partidos de un equipo, ordenados de mas antiguo a mas reciente.
        Devuelve la lista de resultados ('G', 'E', 'P'); la visualizacion
        (emojis, colores, etc.) se hace en app.py."""
        partidos = match_results[
            (match_results["Equipo A"] == equipo) | (match_results["Equipo B"] == equipo)
        ].sort_values(["FECHA", "HORA"]).tail(n)

        resultados = []
        for _, p in partidos.iterrows():
            es_a = p["Equipo A"] == equipo
            gf = p["Goles A"] if es_a else p["Goles B"]
            gc = p["Goles B"] if es_a else p["Goles A"]
            resultados.append("G" if gf > gc else "E" if gf == gc else "P")
        return resultados

    def process_standings(self, df):
        """Tabla unica de posiciones para Clausura 2026, sin grupos."""
        data = self._played(df)
        if data.empty:
            return pd.DataFrame(columns=["EQUIPO", "G", "E", "P", "PJ", "GF", "GC", "GD", "Puntos", "PythEXP", "Racha"])

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

        stats = stats.sort_values(["Puntos", "GD", "GF", "GC"], ascending=[False, False, False, True]).reset_index(drop=True)

        match_results = self.process_match_results(df)
        stats["Racha"] = stats["EQUIPO"].apply(lambda e: self.calcular_racha(match_results, e))

        return stats

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

    def calcular_puntos_esperados(self, standings_df):
        """Compara puntos reales vs. esperados segun expectativa pitagorica (PythEXP)."""
        tabla = standings_df[["EQUIPO", "Puntos", "PJ", "PythEXP"]].copy()
        tabla["Puntos_Esperados"] = (tabla["PythEXP"] * tabla["PJ"] * 3).round(1)
        tabla["Diferencia"] = (tabla["Puntos"] - tabla["Puntos_Esperados"]).round(1)
        tabla = tabla.rename(columns={
            "EQUIPO": "Equipo",
            "Puntos": "Puntos Reales",
            "PythEXP": "Pyth",
        })
        return tabla[["Equipo", "Puntos Reales", "Pyth", "Puntos_Esperados", "Diferencia"]] \
            .sort_values("Puntos Reales", ascending=False)

    def calcular_cuartos_proyectados(self, standings_df):
        """Cruces de cuartos segun posicion actual: 1v8, 2v7, 3v6, 4v5."""
        top8 = standings_df.head(8).reset_index(drop=True)
        cruces = [(0, 7), (1, 6), (2, 5), (3, 4)]
        return [(top8.loc[a, "EQUIPO"], top8.loc[b, "EQUIPO"]) for a, b in cruces]

    def calcular_semifinal_proyectada(self, standings_df):
        """Asume que el mejor sembrado de cada cruce de cuartos avanza."""
        cuartos = self.calcular_cuartos_proyectados(standings_df)
        # cuartos[0]=1v8, cuartos[1]=2v7, cuartos[2]=3v6, cuartos[3]=4v5
        # SF1: ganador(1v8) vs ganador(4v5) | SF2: ganador(2v7) vs ganador(3v6)
        return [
            (cuartos[0][0], cuartos[3][0]),  # 1 vs 4
            (cuartos[1][0], cuartos[2][0]),  # 2 vs 3
        ]

    def calcular_final_proyectada(self, standings_df):
        """Asume que el mejor sembrado de cada semifinal avanza."""
        semis = self.calcular_semifinal_proyectada(standings_df)
        return (semis[0][0], semis[1][0])  # 1 vs 2

    def calcular_tercer_puesto_proyectado(self, standings_df):
        """Asume que el peor sembrado de cada semifinal cae a este partido."""
        semis = self.calcular_semifinal_proyectada(standings_df)
        return (semis[0][1], semis[1][1])  # 4 vs 3

    def resolver_equipos_pendientes(self, fixture_df, standings_df):
        """Completa equipos vacios en el fixture pendiente (filas de playoffs
        aun sin definir) usando la proyeccion actual de la tabla, en vez de
        nombres hardcodeados. Si el partido no matchea ninguna ronda de
        playoff reconocida, o no hay suficientes equipos jugados todavia
        para proyectar, se deja 'Por definir'.

        Asume que la columna con el nombre/identificador del partido se
        llama 'PARTIDO' y que ahi aparece una palabra clave: CUARTO,
        SEMIFINAL, TERCER o FINAL (sin SEMI ni TERCER). Ajusta las
        palabras clave si tu fixture usa otra nomenclatura.
        """
        data = fixture_df.copy()
        data.columns = data.columns.str.strip().str.upper()

        col_e1 = "EQUIPO_1" if "EQUIPO_1" in data.columns else "EQUIPO A"
        col_e2 = "EQUIPO_2" if "EQUIPO_2" in data.columns else "EQUIPO B"

        if col_e1 not in data.columns or col_e2 not in data.columns or "PARTIDO" not in data.columns:
            return fixture_df  # esquema inesperado, no tocar nada

        vacio = data[col_e1].isna() | (data[col_e1].astype(str).str.strip() == "") \
            | data[col_e2].isna() | (data[col_e2].astype(str).str.strip() == "")

        if not vacio.any():
            return fixture_df

        puede_proyectar = len(standings_df) >= 8

        cuartos = self.calcular_cuartos_proyectados(standings_df) if puede_proyectar else []
        semifinal = self.calcular_semifinal_proyectada(standings_df) if puede_proyectar else []
        final = self.calcular_final_proyectada(standings_df) if puede_proyectar else None
        tercer_puesto = self.calcular_tercer_puesto_proyectado(standings_df) if puede_proyectar else None

        def resolver_fila(row):
            if not vacio.loc[row.name]:
                return row[col_e1], row[col_e2]
            if not puede_proyectar:
                return "Por definir", "Por definir"

            nombre = str(row["PARTIDO"]).upper()

            if "CUARTO" in nombre:
                # Extrae el numero del cruce si viene en el nombre (ej. "Cuartos 1")
                digitos = "".join(c for c in nombre if c.isdigit())
                idx = int(digitos) - 1 if digitos and 0 <= int(digitos) - 1 < len(cuartos) else None
                if idx is not None:
                    return cuartos[idx]
                return "Por definir", "Por definir"

            if "SEMIFINAL" in nombre or "SEMI" in nombre:
                digitos = "".join(c for c in nombre if c.isdigit())
                idx = int(digitos) - 1 if digitos and 0 <= int(digitos) - 1 < len(semifinal) else None
                if idx is not None:
                    return semifinal[idx]
                return "Por definir", "Por definir"

            if "TERCER" in nombre:
                return tercer_puesto if tercer_puesto else ("Por definir", "Por definir")

            if "FINAL" in nombre:
                return final if final else ("Por definir", "Por definir")

            return "Por definir", "Por definir"

        resueltos = data.apply(resolver_fila, axis=1, result_type="expand")
        data[col_e1] = resueltos[0]
        data[col_e2] = resueltos[1]

        return data