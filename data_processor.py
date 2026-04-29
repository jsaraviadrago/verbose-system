import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self):
        pass

    def get_general_stats(self, df):
        promedio = df['Goles'].mean() * 2
        total_goles = df['Goles'].sum()
        
        gf_data_sum = df.groupby('Fecha').agg(
            Total_Goles=('Goles', 'sum'),
            Prom_Goles=('Goles', lambda x: x.mean() * 2)).reset_index()
        gf_data_sum['Fecha'] = gf_data_sum['Fecha'].astype(str)
        
        return promedio, total_goles, gf_data_sum

    def process_standings(self, df, grupo):
        df_filtered = df[df['Grupo'] == grupo].copy()
        if df_filtered.empty:
            return pd.DataFrame()

        df_filtered['g_count'] = (df_filtered['Resultado'] == 'G').astype(int)
        df_filtered['e_count'] = (df_filtered['Resultado'] == 'E').astype(int)
        df_filtered['p_count'] = (df_filtered['Resultado'] == 'P').astype(int)

        gf_data = df_filtered.groupby('Equipo')['Goles'].sum().reset_index().rename(columns={'Goles': 'GF'})

        match_goals = df_filtered.pivot_table(index='Partido', columns='Equipo_numero', values='Goles', aggfunc='sum').reset_index()
        match_goals.columns = ['Partido', 'Goals_Equipo1', 'Goals_Equipo2']
        match_teams = df_filtered.pivot_table(index='Partido', columns='Equipo_numero', values='Equipo', aggfunc='first').reset_index()
        match_teams.columns = ['Partido', 'Equipo1', 'Equipo2']
        full_match_info = pd.merge(match_teams, match_goals, on='Partido')

        gc1 = full_match_info[['Equipo1', 'Goals_Equipo2']].rename(columns={'Equipo1': 'Equipo', 'Goals_Equipo2': 'GC'})
        gc2 = full_match_info[['Equipo2', 'Goals_Equipo1']].rename(columns={'Equipo2': 'Equipo', 'Goals_Equipo1': 'GC'})
        gc_data = pd.concat([gc1, gc2]).groupby('Equipo')['GC'].sum().reset_index()

        stats = df_filtered.groupby('Equipo').agg(G=('g_count', 'sum'), E=('e_count', 'sum'), P=('p_count', 'sum')).reset_index()
        stats['PJ'] = stats['G'] + stats['E'] + stats['P']
        stats = stats.merge(gf_data, on='Equipo', how='left').merge(gc_data, on='Equipo', how='left').fillna(0)
        
        stats['GD'] = stats['GF'] - stats['GC']
        stats['Puntos'] = (stats['G'] * 3) + (stats['E'] * 1)
        stats['Prom_gol'] = (stats['GF'] / stats['PJ'])
        
        # Pythagorean Expectation
        gf_p, gc_p = stats['GF']**1.2, stats['GC']**1.2
        stats['PythEXP'] = (gf_p / (gf_p + gc_p)).fillna(0).round(2)

        return stats.sort_values(by=['Puntos', 'GD'], ascending=[False, False]).reset_index(drop=True)

    def process_match_results(self, df):
        df_temp = df.copy()
        df_temp['match_number'] = df_temp.groupby(['Fecha', 'Grupo']).cumcount() // 2
        df_temp['team_number'] = df_temp.groupby(['Fecha', 'Grupo', 'match_number']).cumcount() + 1
        
        match_details = df_temp[['Fecha', 'Grupo', 'match_number', 'Hora', 'Cancha']].drop_duplicates()
        pivoted = df_temp.pivot(index=['Fecha', 'Grupo', 'match_number'], columns='team_number', values=['Equipo', 'Goles'])
        pivoted.columns = [f'{col[0]}_{col[1]}' for col in pivoted.columns]
        pivoted = pivoted.reset_index().merge(match_details, on=['Fecha', 'Grupo', 'match_number'])
        
        pivoted = pivoted.rename(columns={'Equipo_1': 'Equipo_A', 'Equipo_2': 'Equipo_B', 'Goles_1': 'Goles_A', 'Goles_2': 'Goles_B'})
        return pivoted.sort_values(by='Fecha')[['Fecha', 'Hora', 'Cancha', 'Grupo', 'Equipo_A', 'Goles_A', 'Equipo_B', 'Goles_B']]

    def process_knockout_stage(self):
        # Carga directa del archivo para evitar hardcoding de Fecha 6 en adelante[cite: 1]
        df_csv = pd.read_csv("Partidos_clausura_2025_CLC_1.csv")
        knockout_df = df_csv[df_csv['Fecha'] >= 6].copy()
        
        # Procesar similar a match_results pero específico para llaves
        res = self.process_match_results(knockout_df)
        return res

    def process_cards_and_scorers(self, cards_df, scorers_df):
        # Procesamiento de Goleadores
        scorers = scorers_df.copy()
        scorers.columns = scorers.columns.str.strip().str.upper()
        scorers['EQUIPO'] = scorers['EQUIPO'].astype(str).str.strip().str.title()
        scorers['NOMBRE Y APELLIDO'] = scorers['NOMBRE Y APELLIDO'].astype(str).str.strip().str.title()
        scorers = scorers.drop_duplicates(subset=['NOMBRE Y APELLIDO']).sort_values(by='GOLES', ascending=False).head(8)
        
        # Procesamiento de Tarjetas (Simplificado para app)
        cards = cards_df.copy()
        cards.columns = cards.columns.str.strip().str.upper()
        cols_f = [col for col in cards.columns if 'F' in col and '1F' <= col <= '8F']
        
        # Lógica de agregación para el gráfico de equipos
        cards['Total_A'] = cards[cols_f].apply(lambda x: x.astype(str).str.contains('1A').sum() + (x.astype(str).str.contains('2A').sum() * 2), axis=1)
        team_cards = cards.groupby('EQUIPO')['Total_A'].sum().reset_index().sort_values(by='Total_A', ascending=False)
        team_cards.columns = ['Equipo', 'Total_A_Count']
        
        # Top 5 Jugadores Amarillas/Rojas
        cards['Amarillas'] = cards[cols_f].apply(lambda x: x.astype(str).str.contains('1A|2A').sum(), axis=1)
        cards['Rojas'] = cards[cols_f].apply(lambda x: x.astype(str).str.contains('1R').sum(), axis=1)
        
        top_y = cards[['JUGADOR', 'EQUIPO', 'Amarillas']].sort_values(by='Amarillas', ascending=False).head(5)
        top_r = cards[['JUGADOR', 'EQUIPO', 'Rojas']].sort_values(by='Rojas', ascending=False).head(5)
        
        return scorers[['NOMBRE Y APELLIDO', 'EQUIPO', 'GOLES']], team_cards, top_y, top_r
