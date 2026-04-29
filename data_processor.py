import pandas as pd
import numpy as np


class DataProcessor:
    def __init__(self):
        pass

    def get_general_stats(self, df):
        """Calcula métricas generales y estadísticas por fecha."""
        # Normalización de columnas
        df.columns = df.columns.str.strip().str.upper()

        promedio = df['GOLES'].mean() * 2
        total_goles = df['GOLES'].sum() / 2

        gf_data_sum = df.groupby('FECHA').agg(
            Total_Goles=('GOLES', 'sum'),
            Prom_Goles=('GOLES', lambda x: x.mean() * 2)).reset_index()
        gf_data_sum['FECHA'] = gf_data_sum['FECHA'].astype(str)

        return promedio, total_goles, gf_data_sum

    def process_standings(self, df, grupo):
        """Genera la tabla de posiciones para la fase de grupos (Fechas 1-5)."""
        df.columns = df.columns.str.strip().str.upper()

        df_filtered = df[(df['GRUPO'] == grupo) & (df['FECHA'] <= 5)].copy()
        if df_filtered.empty: return pd.DataFrame()

        df_filtered['g_count'] = (df_filtered['RESULTADO'] == 'G').astype(int)
        df_filtered['e_count'] = (df_filtered['RESULTADO'] == 'E').astype(int)
        df_filtered['p_count'] = (df_filtered['RESULTADO'] == 'P').astype(int)

        gf_data = df_filtered.groupby('EQUIPO')['GOLES'].sum().reset_index().rename(columns={'GOLES': 'GF'})

        match_goals = df_filtered.pivot_table(index='PARTIDO', columns='EQUIPO_NUMERO', values='GOLES',
                                              aggfunc='sum').reset_index()
        match_goals.columns = ['PARTIDO', 'Goals_Equipo1', 'Goals_Equipo2']
        match_teams = df_filtered.pivot_table(index='PARTIDO', columns='EQUIPO_NUMERO', values='EQUIPO',
                                              aggfunc='first').reset_index()
        match_teams.columns = ['PARTIDO', 'Equipo1', 'Equipo2']

        full_match_info = pd.merge(match_teams, match_goals, on='PARTIDO')
        gc1 = full_match_info[['Equipo1', 'Goals_Equipo2']].rename(columns={'Equipo1': 'EQUIPO', 'Goals_Equipo2': 'GC'})
        gc2 = full_match_info[['Equipo2', 'Goals_Equipo1']].rename(columns={'Equipo2': 'EQUIPO', 'Goals_Equipo1': 'GC'})
        gc_data = pd.concat([gc1, gc2]).groupby('EQUIPO')['GC'].sum().reset_index()

        stats = df_filtered.groupby('EQUIPO').agg(G=('g_count', 'sum'), E=('e_count', 'sum'),
                                                  P=('p_count', 'sum')).reset_index()
        stats['PJ'] = stats['G'] + stats['E'] + stats['P']
        stats = stats.merge(gf_data, on='EQUIPO', how='left').merge(gc_data, on='EQUIPO', how='left').fillna(0)
        stats['GD'] = stats['GF'] - stats['GC']
        stats['Puntos'] = (stats['G'] * 3) + (stats['E'] * 1)

        gf_p, gc_p = stats['GF'] ** 1.2, stats['GC'] ** 1.2
        stats['PythEXP'] = (gf_p / (gf_p + gc_p)).fillna(0).round(2)

        return stats.sort_values(by=['Puntos', 'GD', 'GF'], ascending=[False, False, False]).reset_index(drop=True)

    def process_match_results(self, df):
        """Resultados de la fase de grupos con orden de columnas específico."""
        df.columns = df.columns.str.strip().str.upper()
        df_temp = df[df['FECHA'] <= 5].copy()
        if df_temp.empty: return pd.DataFrame()

        df_temp['match_idx'] = df_temp.groupby(['FECHA', 'GRUPO']).cumcount() // 2
        df_temp['team_idx'] = df_temp.groupby(['FECHA', 'GRUPO', 'match_idx']).cumcount() + 1

        match_details = df_temp[['FECHA', 'GRUPO', 'match_idx', 'HORA', 'CANCHA']].drop_duplicates()
        pivoted = df_temp.pivot(index=['FECHA', 'GRUPO', 'match_idx'], columns='team_idx', values=['EQUIPO', 'GOLES'])
        pivoted.columns = [f'{col[0]}_{col[1]}' for col in pivoted.columns]
        pivoted = pivoted.reset_index().merge(match_details, on=['FECHA', 'GRUPO', 'match_idx'])

        pivoted = pivoted.rename(columns={
            'EQUIPO_1': 'Equipo A', 'EQUIPO_2': 'Equipo B',
            'GOLES_1': 'Goles A', 'GOLES_2': 'Goles B'
        })

        cols = ['FECHA', 'GRUPO', 'CANCHA', 'HORA', 'Equipo A', 'Goles A', 'Equipo B', 'Goles B']
        return pivoted[cols].sort_values(by=['FECHA', 'GRUPO'])

    def process_knockout_stage(self, df):
        """Procesa Fechas 6, 7 y 8 como Cuartos, Semis y Final."""
        df.columns = df.columns.str.strip().str.upper()
        knockout_df = df[df['FECHA'] >= 6].copy()
        if knockout_df.empty: return pd.DataFrame()

        knockout_df['match_idx'] = knockout_df.groupby('FECHA').cumcount() // 2
        knockout_df['team_idx'] = knockout_df.groupby(['FECHA', 'match_idx']).cumcount() + 1

        match_info = knockout_df[['FECHA', 'match_idx', 'HORA', 'CANCHA']].drop_duplicates()
        pivoted = knockout_df.pivot(index=['FECHA', 'match_idx'], columns='team_idx', values=['EQUIPO', 'GOLES'])
        pivoted.columns = [f'{col[0]}_{col[1]}' for col in pivoted.columns]
        pivoted = pivoted.reset_index().merge(match_info, on=['FECHA', 'match_idx'])

        pivoted = pivoted.rename(columns={
            'EQUIPO_1': 'Equipo A', 'EQUIPO_2': 'Equipo B',
            'GOLES_1': 'Goles A', 'GOLES_2': 'Goles B', 'FECHA': 'Fecha_Num'
        })

        fase_map = {6: "Cuartos de Final", 7: "Semifinal", 8: "Gran Final"}
        pivoted['Fase'] = pivoted['Fecha_Num'].map(fase_map)

        column_order = ['Fase', 'CANCHA', 'HORA', 'Equipo A', 'Goles A', 'Equipo B', 'Goles B']
        return pivoted[column_order]

    def process_cards_and_scorers(self, cards_df, scorers_df):
        """Lógica de goleadores y disciplina corregida para detectar Rojas y Mayúsculas."""
        # --- Goleadores ---
        scorers = scorers_df.copy()
        scorers.columns = scorers.columns.str.strip().str.upper()

        # Ajuste de nombre de columna para goleadores
        nombre_col = 'NOMBRE Y APELLIDO' if 'NOMBRE Y APELLIDO' in scorers.columns else 'JUGADOR'

        scorers['GOLES'] = pd.to_numeric(scorers['GOLES'], errors='coerce').fillna(0).astype(int)
        scorers[nombre_col] = scorers[nombre_col].str.title()

        goleadores_sorted = scorers.sort_values(by='GOLES', ascending=False).head(10)

        # --- Tarjetas ---
        cards = cards_df.copy()
        cards.columns = cards.columns.str.strip().str.upper()
        cols_f = [c for c in cards.columns if 'F' in c and len(c) <= 3]

        for col in cols_f:
            cards[col] = cards[col].astype(str).str.upper().str.strip()

        # Detección precisa de sanciones
        cards['Amarillas'] = cards[cols_f].apply(lambda x: x.str.contains('A', na=False).sum(), axis=1)
        cards['Rojas'] = cards[cols_f].apply(lambda x: x.str.contains('1R', na=False).sum(), axis=1)

        # Puntos Fair Play
        cards['Puntos_Sancion'] = cards[cols_f].apply(
            lambda x: x.str.contains('1A', na=False).sum() +
                      (x.str.contains('2A', na=False).sum() * 2) +
                      (x.str.contains('1R', na=False).sum() * 3),
            axis=1
        )

        team_cards = cards.groupby('EQUIPO')['Puntos_Sancion'].sum().reset_index().sort_values(by='Puntos_Sancion',
                                                                                               ascending=False)
        team_cards.columns = ['Equipo', 'Total_Sancion']

        top_y = cards[cards['Amarillas'] > 0][['JUGADOR', 'EQUIPO', 'Amarillas']].sort_values(by='Amarillas',
                                                                                              ascending=False).head(8)
        top_r = cards[cards['Rojas'] > 0][['JUGADOR', 'EQUIPO', 'Rojas']].sort_values(by='Rojas', ascending=False).head(
            8)

        return goleadores_sorted[[nombre_col, 'EQUIPO', 'GOLES']], team_cards, top_y, top_r