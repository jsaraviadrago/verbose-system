import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self):
        pass

    def get_general_stats(self, df):
        """Calcula métricas generales y estadísticas por fecha."""
        promedio = df['Goles'].mean() * 2
        total_goles = df['Goles'].sum() / 2
        
        gf_data_sum = df.groupby('Fecha').agg(
            Total_Goles=('Goles', 'sum'),
            Prom_Goles=('Goles', lambda x: x.mean() * 2)).reset_index()
        gf_data_sum['Fecha'] = gf_data_sum['Fecha'].astype(str)
        
        return promedio, total_goles, gf_data_sum

    def process_standings(self, df, grupo):
        """Genera la tabla de posiciones para la fase de grupos (Fechas 1-5)."""
        df_filtered = df[(df['Grupo'] == grupo) & (df['Fecha'] <= 5)].copy()
        if df_filtered.empty: return pd.DataFrame()

        df_filtered['g_count'] = (df_filtered['Resultado'] == 'G').astype(int)
        df_filtered['e_count'] = (df_filtered['Resultado'] == 'E').astype(int)
        df_filtered['p_count'] = (df_filtered['Resultado'] == 'P').astype(int)

        gf_data = df_filtered.groupby('Equipo')['Goles'].sum().reset_index().rename(columns={'Goles': 'GF'})
        
        # Cálculo de Goles en Contra (GC) cruzando datos de partidos
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
        
        # Expectativa Pitagórica
        gf_p, gc_p = stats['GF']**1.2, stats['GC']**1.2
        stats['PythEXP'] = (gf_p / (gf_p + gc_p)).fillna(0).round(2)

        return stats.sort_values(by=['Puntos', 'GD', 'GF'], ascending=[False, False, False]).reset_index(drop=True)

    def process_match_results(self, df):
        """Resultados de la fase de grupos con orden de columnas específico."""
        df_temp = df[df['Fecha'] <= 5].copy()
        if df_temp.empty: return pd.DataFrame()
        
        df_temp['match_idx'] = df_temp.groupby(['Fecha', 'Grupo']).cumcount() // 2
        df_temp['team_idx'] = df_temp.groupby(['Fecha', 'Grupo', 'match_idx']).cumcount() + 1
        
        match_details = df_temp[['Fecha', 'Grupo', 'match_idx', 'Hora', 'Cancha']].drop_duplicates()
        pivoted = df_temp.pivot(index=['Fecha', 'Grupo', 'match_idx'], columns='team_idx', values=['Equipo', 'Goles'])
        pivoted.columns = [f'{col[0]}_{col[1]}' for col in pivoted.columns]
        pivoted = pivoted.reset_index().merge(match_details, on=['Fecha', 'Grupo', 'match_idx'])
        
        pivoted = pivoted.rename(columns={
            'Equipo_1': 'Equipo A', 'Equipo_2': 'Equipo B', 
            'Goles_1': 'Goles A', 'Goles_2': 'Goles B'
        })
        
        cols = ['Fecha', 'Grupo', 'Cancha', 'Hora', 'Equipo A', 'Goles A', 'Equipo B', 'Goles B']
        return pivoted[cols].sort_values(by=['Fecha', 'Grupo'])

    def process_knockout_stage(self, df):
        """Procesa Fechas 6, 7 y 8 como Cuartos, Semis y Final."""
        knockout_df = df[df['Fecha'] >= 6].copy()
        if knockout_df.empty: return pd.DataFrame()
        
        knockout_df['match_idx'] = knockout_df.groupby('Fecha').cumcount() // 2
        knockout_df['team_idx'] = knockout_df.groupby(['Fecha', 'match_idx']).cumcount() + 1
        
        match_info = knockout_df[['Fecha', 'match_idx', 'Hora', 'Cancha']].drop_duplicates()
        pivoted = knockout_df.pivot(index=['Fecha', 'match_idx'], columns='team_idx', values=['Equipo', 'Goles'])
        pivoted.columns = [f'{col[0]}_{col[1]}' for col in pivoted.columns]
        pivoted = pivoted.reset_index().merge(match_info, on=['Fecha', 'match_idx'])
        
        pivoted = pivoted.rename(columns={
            'Equipo_1': 'Equipo A', 'Equipo_2': 'Equipo B', 
            'Goles_1': 'Goles A', 'Goles_2': 'Goles B', 'Fecha': 'Fecha_Num'
        })

        fase_map = {6: "Cuartos de Final", 7: "Semifinal", 8: "Gran Final"}
        pivoted['Fase'] = pivoted['Fecha_Num'].map(fase_map)

        column_order = ['Fase', 'Cancha', 'Hora', 'Equipo A', 'Goles A', 'Equipo B', 'Goles B']
        return pivoted[column_order]

    def process_cards_and_scorers(self, cards_df, scorers_df):
        """Lógica de goleadores y disciplina (Fair Play)."""
        scorers = scorers_df.copy()
        scorers.columns = scorers.columns.str.strip().str.upper()
        scorers['NOMBRE Y APELLIDO'] = scorers['NOMBRE Y APELLIDO'].str.title()
        
        cards = cards_df.copy()
        cards.columns = cards.columns.str.strip().str.upper()
        cols_f = [c for c in cards.columns if 'F' in c and len(c) <= 3]
        
        # 1A = 1 punto, 2A = 2 puntos
        cards['Total_A'] = cards[cols_f].apply(lambda x: x.astype(str).str.contains('1A').sum() + (x.astype(str).str.contains('2A').sum() * 2), axis=1)
        cards['Amarillas'] = cards[cols_f].apply(lambda x: x.astype(str).str.contains('1A|2A').sum(), axis=1)
        cards['Rojas'] = cards[cols_f].apply(lambda x: x.astype(str).str.contains('1R').sum(), axis=1)
        
        team_cards = cards.groupby('EQUIPO')['Total_A'].sum().reset_index().sort_values(by='Total_A', ascending=False)
        team_cards.columns = ['Equipo', 'Total_A_Count']
        
        top_y = cards[cards['Amarillas'] > 0][['JUGADOR', 'EQUIPO', 'Amarillas']].sort_values(by='Amarillas', ascending=False).head(5)
        top_r = cards[cards['Rojas'] > 0][['JUGADOR', 'EQUIPO', 'Rojas']].sort_values(by='Rojas', ascending=False).head(5)
        
        return scorers[['NOMBRE Y APELLIDO', 'EQUIPO', 'GOLES']].head(10), team_cards, top_y, top_r
