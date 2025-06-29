import streamlit as st
import pandas as pd
import altair as alt


st.markdown("<h1 style='text-align: center; '>Campeonato Apertura Cambridge Lima College 2025</h1>", unsafe_allow_html=True)
st.divider()

# --- Logos section ---
st.markdown("### Equipos Participantes")


st.markdown("""
<!-- Row 1 -->
<div style="display: flex; justify-content: center; gap: 40px; margin-bottom: 30px;">
    <div><img src="https://static.cdnlogo.com/logos/l/92/liverpool-fc.svg" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/r/38/real-madrid-club-de-futbol.svg" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/b/29/borussia-dortmund.svg" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/m/41/manchester-city-fc.png" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/b/36/bayern-munich.png" width="115" height="115"></div>
</div>

<!-- Row 2 -->
<div style="display: flex; justify-content: center; gap: 40px;">
    <div><img src="https://static.cdnlogo.com/logos/f/14/fc-barcelona.svg" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/j/15/juventus.svg" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/f/80/fioren-1.svg" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/a/47/ac-milan.svg" width="100" height="100"></div>
    <div><img src="https://static.cdnlogo.com/logos/c/24/chelsea-fc.svg" width="100" height="100"></div>
</div>
""", unsafe_allow_html=True)

st.divider()

csv_file_path1 = 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/refs/heads/main/Partidos_apertura_2025_CLC_1.csv'
df1 = pd.read_csv(csv_file_path1)

# Calculated values
Promedio_total = df1['Goles'].mean() * 2
Gol_total = df1['Goles'].sum()

# Create two equal columns
col1, col2 = st.columns(2)

# Common style with fixed height
box_style = """
    <div style="
        padding: 1.5rem;
        background-color: {bg_color};
        border-radius: 12px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
        font-size: 20px;
        text-align: center;
        font-weight: bold;
        color: black;
        height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        {content}
    </div>
"""

# Box 1
with col1:
    st.markdown(box_style.format(
        bg_color="#e0f7fa",
        content=f"⚽ Promedio de Goles por Partido:<br>{Promedio_total:.2f}"
    ), unsafe_allow_html=True)

# Box 2
with col2:
    st.markdown(box_style.format(
        bg_color="#ffffff",
        content=f"🔢 Total de Goles:<br>{Gol_total}"
    ), unsafe_allow_html=True)

#Promedio y total por fecha
gf_data_sum1 = df1.groupby('Fecha').agg(
        Total_Goles=('Goles', 'sum'),
        Prom_Goles=('Goles', lambda x: x.mean() * 2)).reset_index()

gf_data_sum1['Fecha'] = gf_data_sum1['Fecha'].astype(str)

st.divider()


st.subheader("Estadísticas del Campeonato por Fecha")

st.write("**Total de Goles por Fecha**")
st.line_chart(gf_data_sum1.set_index('Fecha')['Total_Goles'])


st.write("**Promedio de Goles por Fecha**")
st.line_chart(gf_data_sum1.set_index('Fecha')['Prom_Goles'])


#######################################################################
#Tabla de posiciones grupo 1
#######################################################################

# --- initial grouping ---

# Filter the DataFrame to include only rows where 'Grupo' is 1
# Using the column name 'Grupo' as provided in your corrected code
df_filtered1 = df1[df1['Grupo'] == 1].copy()

if df_filtered1.empty:
    print("\nNo data found for 'Grupo' = 1 after filtering. Cannot proceed with calculations.")
else:
    # Create new temporary columns to count 'G', 'E', and 'P' in 'Resultado'
    df_filtered1['g_count'] = (df_filtered1['Resultado'] == 'G').astype(int)
    df_filtered1['e_count'] = (df_filtered1['Resultado'] == 'E').astype(int)
    df_filtered1['p_count'] = (df_filtered1['Resultado'] == 'P').astype(int)

    # --- Corrected Calculation for GF (Goals For) and GC (Goals Conceded) ---

    # 1. Calculate GF (Goals For): This is the sum of 'Goles' scored by each team.
    #    The 'Goles' column is assumed to be goals scored by the 'Equipo' in that row.
    gf_data1 = df_filtered1.groupby('Equipo')['Goles'].sum().reset_index()
    gf_data1.rename(columns={'Goles': 'GF'}, inplace=True)

    # 2. Calculate GC: This requires matching opponents' goals within each match.
    #    First, create a temporary DataFrame with goals for both Equipo_numero 1 and 2 per Partido.
    match_goals1 = df_filtered1.pivot_table(
        index='Partido',
        columns='Equipo_numero',
        values='Goles',
        aggfunc='sum'
    ).reset_index()
    match_goals1.columns = ['Partido', 'Goals_Equipo1', 'Goals_Equipo2']

    #    Second, create a temporary DataFrame with Equipo names for both Equipo_numero 1 and 2 per Partido.
    match_teams1 = df_filtered1.pivot_table(
        index='Partido',
        columns='Equipo_numero',
        values='Equipo',
        aggfunc='first' 
    ).reset_index()
    match_teams1.columns = ['Partido', 'Equipo1', 'Equipo2']

    #    Merge the goals and teams data for each match
    full_match_info1 = pd.merge(match_teams1, match_goals1, on='Partido')

    #    Now, identify conceded goals for each team:
    #    If a team was Equipo1, its conceded goals are Goals_Equipo2.
    #    If a team was Equipo2, its conceded goals are Goals_Equipo1.
    conceded_goals_part11 = full_match_info1[['Equipo1', 'Goals_Equipo2']].rename(columns={'Equipo1': 'Equipo', 'Goals_Equipo2': 'GC'})
    conceded_goals_part21 = full_match_info1[['Equipo2', 'Goals_Equipo1']].rename(columns={'Equipo2': 'Equipo', 'Goals_Equipo1': 'GC'})

    #    Combine and sum all conceded goals for each Equipo
    gc_data1 = pd.concat([conceded_goals_part11, conceded_goals_part21]).groupby('Equipo')['GC'].sum().reset_index()

    # --- Combine all calculated stats ---

    # Start with g, e, p counts from your previous calculation
    final_stats1 = df_filtered1.groupby('Equipo').agg(
        G=('g_count', 'sum'),
        E=('e_count', 'sum'),
        P=('p_count', 'sum')
    ).reset_index()

    # Count the amount of games playeed
    final_stats1['PJ'] = final_stats1['G'] + final_stats1['E'] + final_stats1['P']

    # Merge GF data
    final_stats1 = pd.merge(final_stats1, gf_data1, on='Equipo', how='left')

    # Merge GC data
    final_stats1 = pd.merge(final_stats1, gc_data1, on='Equipo', how='left')

    # Fill any NaN values (e.g., if a team has no matches as equipo_numero 1 or 2, which shouldn't happen
    # if they played in group 1, but for robustness) with 0
    final_stats1['GF'] = final_stats1['GF'].fillna(0).astype(int)
    final_stats1['GC'] = final_stats1['GC'].fillna(0).astype(int)

    # Calculate GD (Goal Difference)
    final_stats1['GD'] = final_stats1['GF'] - final_stats1['GC']

    # --- New code to calculate "Puntos" (Points) ---
    final_stats1['Puntos'] = (final_stats1['G'] * 3) + (final_stats1['E'] * 1) + (final_stats1['P'] * 0)

    # Mean of goals
    final_stats1['Prom_gol'] = (final_stats1['GF'] / final_stats1['PJ'])

    # Calculate GF and GC raised to the power of 1.2
gf_power1 = final_stats1['GF']**1.2
gc_power1 = final_stats1['GC']**1.2

# Calculate the Pythagorean Expectation
# Add a small epsilon to the denominator to avoid division by zero if both GF and GC are 0
# For teams with GF=0 and GC=0, Pythagorean Expectation is typically considered 0 or undefined.
# This approach will result in 0 for such cases if the numerator is 0 and denominator is 0.
final_stats1['PythEXP'] = gf_power1 / (gf_power1 + gc_power1)

# Handle cases where both GF and GC were 0 (leading to NaN due to 0/0)
# If GF and GC are both 0, the team essentially hasn't played or scored/conceded.
# In such scenarios, Pythagorean Expectation is often set to 0.
final_stats1['PythEXP'] = final_stats1['PythEXP'].fillna(0)
final_stats1['PythEXP'] = final_stats1['PythEXP'].round(2)

  # Sort the DataFrame by 'Puntos' in descending order, then by 'GF' in descending order for ties
final_stats_sorted1 = final_stats1.sort_values(by=['Puntos', 'GD'], ascending=[False, False])

# Reset index of my dataframe
final_stats_sorted1 = final_stats_sorted1.reset_index(drop=True)

# Organize columns in logical order
column_order1 = ['Equipo', 'PJ', 'G', 'E', 'P', 'Puntos', 'GF', 'GC', 'GD', 'Prom_gol', 'PythEXP']
final_stats_sorted1 = final_stats_sorted1[column_order1]

####################################### Streamlit ################################
#### Grupo 1 ###############

st.divider()

# Display dataframe nicely formatted
st.subheader("Tabla de posiciones")


st.markdown("""
⚽ **Reglas de Desempate en Tablas de Liga de Fútbol**

En caso de que dos o más equipos terminen una liga de fútbol con la misma cantidad de puntos, las reglas de desempate suelen aplicarse en el siguiente orden, aunque pueden variar ligeramente según la competición:

1.  **Diferencia de Goles General:** El equipo con la mayor diferencia entre los goles marcados y los goles recibidos en todos los partidos de la liga.
2.  **Goles a Favor General:** El equipo que haya marcado el mayor número de goles en todos los partidos de la liga.
3.  **Puntos en Enfrentamientos Directos:** Si los equipos empatados han jugado entre sí, se considera el número de puntos obtenidos en los partidos disputados solo entre ellos.
4.  **Diferencia de Goles en Enfrentamientos Directos:** Si sigue el empate, se toma la diferencia de goles en los partidos disputados solo entre los equipos empatados.
5.  **Goles a Favor en Enfrentamientos Directos:** Si aún hay empate, se considera el número de goles marcados en los partidos disputados solo entre los equipos empatados.
6.  **Goles de Visitante en Enfrentamientos Directos:** En algunas ligas, los goles marcados como visitante en los partidos entre los equipos empatados pueden ser un criterio adicional.
7.  **Fair Play (Juego Limpio):** En algunas competiciones, el equipo con menos tarjetas (amarillas y rojas) puede tener ventaja.
8.  **Sorteo:** Como último recurso, si todos los criterios anteriores no logran romper el empate, se puede realizar un sorteo.
""")

st.write("**Grupo 1**")

# Display with custom formatting and column names
st.dataframe(
    final_stats_sorted1,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Equipo": st.column_config.TextColumn("Equipo", width=130),
        "PJ": st.column_config.NumberColumn("PJ", format="%d", help="Partidos Jugados"),
        "G": st.column_config.NumberColumn("G", format="%d", help="Ganados"),
        "E": st.column_config.NumberColumn("E", format="%d", help="Empatados"),
        "P": st.column_config.NumberColumn("P", format="%d", help="Perdidos"),
        "Puntos": st.column_config.NumberColumn("Puntos", format="%d"),
        "GF": st.column_config.NumberColumn("GF", format="%d", help="Goles a Favor"),
        "GC": st.column_config.NumberColumn("GC", format="%d", help="Goles en Contra"),
        "GD": st.column_config.NumberColumn("GD", format="%+d", help="Diferencia de Goles"),
        "Prom_gol": st.column_config.NumberColumn("Prom. Gol", format="%.2f", help="Promedio de Goles"),
        "PythEXP": st.column_config.NumberColumn("Pyth EXP", format="%.3f", help="Pythagorean Expectation")})

#######################################################################
#Tabla de posiciones grupo 2
#######################################################################

# --- Start of your previous corrected code for initial grouping ---

# Filter the DataFrame to include only rows where 'Grupo' is 2
# Using the column name 'Grupo' as provided in your corrected code
df_filtered = df1[df1['Grupo'] == 2].copy()

if df_filtered.empty:
    print("\nNo data found for 'Grupo' = 1 after filtering. Cannot proceed with calculations.")
else:
    # Create new temporary columns to count 'G', 'E', and 'P' in 'Resultado'
    df_filtered['g_count'] = (df_filtered['Resultado'] == 'G').astype(int)
    df_filtered['e_count'] = (df_filtered['Resultado'] == 'E').astype(int)
    df_filtered['p_count'] = (df_filtered['Resultado'] == 'P').astype(int)

    # --- Corrected Calculation for GF (Goals For) and GC (Goals Conceded) ---

    # 1. Calculate GF (Goals For): This is the sum of 'Goles' scored by each team.
    #    The 'Goles' column is assumed to be goals scored by the 'Equipo' in that row.
    gf_data = df_filtered.groupby('Equipo')['Goles'].sum().reset_index()
    gf_data.rename(columns={'Goles': 'GF'}, inplace=True)

    # 2. Calculate GC (Goals Conceded): This requires matching opponents' goals within each match.
    #    First, create a temporary DataFrame with goals for both Equipo_numero 1 and 2 per Partido.
    match_goals = df_filtered.pivot_table(
        index='Partido',
        columns='Equipo_numero',
        values='Goles',
        aggfunc='sum'
    ).reset_index()
    match_goals.columns = ['Partido', 'Goals_Equipo1', 'Goals_Equipo2']

    #    Second, create a temporary DataFrame with Equipo names for both Equipo_numero 1 and 2 per Partido.
    match_teams = df_filtered.pivot_table(
        index='Partido',
        columns='Equipo_numero',
        values='Equipo',
        aggfunc='first' # 'first' or 'last' works here as there's only one Equipo name per Equipo_numero per Partido
    ).reset_index()
    match_teams.columns = ['Partido', 'Equipo1', 'Equipo2']

    #    Merge the goals and teams data for each match
    full_match_info = pd.merge(match_teams, match_goals, on='Partido')

    #    Now, identify conceded goals for each team:
    #    If a team was Equipo1, its conceded goals are Goals_Equipo2.
    #    If a team was Equipo2, its conceded goals are Goals_Equipo1.
    conceded_goals_part1 = full_match_info[['Equipo1', 'Goals_Equipo2']].rename(columns={'Equipo1': 'Equipo', 'Goals_Equipo2': 'GC'})
    conceded_goals_part2 = full_match_info[['Equipo2', 'Goals_Equipo1']].rename(columns={'Equipo2': 'Equipo', 'Goals_Equipo1': 'GC'})

    #    Combine and sum all conceded goals for each Equipo
    gc_data = pd.concat([conceded_goals_part1, conceded_goals_part2]).groupby('Equipo')['GC'].sum().reset_index()

    # --- Combine all calculated stats ---

    # Start with g, e, p counts from your previous calculation
    final_stats = df_filtered.groupby('Equipo').agg(
        G=('g_count', 'sum'),
        E=('e_count', 'sum'),
        P=('p_count', 'sum')
    ).reset_index()

    # Count the amount of games playeed
    final_stats['PJ'] = final_stats['G'] + final_stats['E'] + final_stats['P']

    # Merge GF data
    final_stats = pd.merge(final_stats, gf_data, on='Equipo', how='left')

    # Merge GC data
    final_stats = pd.merge(final_stats, gc_data, on='Equipo', how='left')

    # Fill any NaN values (e.g., if a team has no matches as equipo_numero 1 or 2, which shouldn't happen
    # if they played in group 1, but for robustness) with 0
    final_stats['GF'] = final_stats['GF'].fillna(0).astype(int)
    final_stats['GC'] = final_stats['GC'].fillna(0).astype(int)

    # Calculate GD (Goal Difference)
    final_stats['GD'] = final_stats['GF'] - final_stats['GC']

    # --- New code to calculate "Puntos" (Points) ---
    final_stats['Puntos'] = (final_stats['G'] * 3) + (final_stats['E'] * 1) + (final_stats['P'] * 0)

    # Mean of goals
    final_stats['Prom_gol'] = (final_stats['GF'] / final_stats['PJ'])

    # Calculate GF and GC raised to the power of 1.2
gf_power = final_stats['GF']**1.2
gc_power = final_stats['GC']**1.2

# Calculate the Pythagorean Expectation
# Add a small epsilon to the denominator to avoid division by zero if both GF and GC are 0
# For teams with GF=0 and GC=0, Pythagorean Expectation is typically considered 0 or undefined.
# This approach will result in 0 for such cases if the numerator is 0 and denominator is 0.
final_stats['PythEXP'] = gf_power / (gf_power + gc_power)

# Handle cases where both GF and GC were 0 (leading to NaN due to 0/0)
# If GF and GC are both 0, the team essentially hasn't played or scored/conceded.
# In such scenarios, Pythagorean Expectation is often set to 0.
final_stats['PythEXP'] = final_stats['PythEXP'].fillna(0)
final_stats['PythEXP'] = final_stats['PythEXP'].round(2)



  # Sort the DataFrame by 'Puntos' in descending order, then by 'GF' in descending order for ties
final_stats_sorted = final_stats.sort_values(by=['Puntos', 'GD'], ascending=[False, False])

# Reset index of my dataframe
final_stats_sorted = final_stats_sorted.reset_index(drop=True)

# Organize columns in logical order
column_order = ['Equipo', 'PJ', 'G', 'E', 'P', 'Puntos', 'GF', 'GC', 'GD', 'Prom_gol', 'PythEXP']
final_stats_sorted = final_stats_sorted[column_order]

####################################### Streamlit ################################
#### Grupo 2 ###############


st.write("**Grupo 2**")


st.dataframe(
    final_stats_sorted,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Equipo": st.column_config.TextColumn("Equipo", width=130),
        "PJ": st.column_config.NumberColumn("PJ", format="%d", help="Partidos Jugados"),
        "G": st.column_config.NumberColumn("G", format="%d", help="Ganados"),
        "E": st.column_config.NumberColumn("E", format="%d", help="Empatados"),
        "P": st.column_config.NumberColumn("P", format="%d", help="Perdidos"),
        "Puntos": st.column_config.NumberColumn("Puntos", format="%d"),
        "GF": st.column_config.NumberColumn("GF", format="%d", help="Goles a Favor"),
        "GC": st.column_config.NumberColumn("GC", format="%d", help="Goles en Contra"),
        "GD": st.column_config.NumberColumn("GD", format="%+d", help="Diferencia de Goles"),
        "Prom_gol": st.column_config.NumberColumn("Prom. Gol", format="%.2f", help="Promedio de Goles"),
        "PythEXP": st.column_config.NumberColumn("Pyth EXP", format="%.3f", help="Pythagorean Expectation")
    }
)

###########################################################################
###### Resultados por fecha #################################
###########################################################################

st.divider()

st.subheader("Resultados por Fecha")

# Create a match_id for each match by grouping by 'Fecha' and 'Grupo'
# Then, divide the cumcount by 2 to create unique match numbers within each group
df1['match_number'] = df1.groupby(['Fecha', 'Grupo']).cumcount() // 2

# Create a team_number (1 or 2) within each match to distinguish between team 1 and team 2
df1['team_number'] = df1.groupby(['Fecha', 'Grupo', 'match_number']).cumcount() + 1

# Before pivoting, extract the 'Hora' and 'Cancha' details for each unique match.
# These columns are associated with 'Fecha', 'Grupo', and 'match_number'.
match_details = df1[['Fecha', 'Grupo', 'match_number', 'Hora', 'Cancha']].drop_duplicates().copy()

# Pivot the table to create separate columns for Equipo and Goles for each team
pivoted_df = df1.pivot(index=['Fecha', 'Grupo', 'match_number'], columns='team_number', values=['Equipo', 'Goles'])

# Flatten the multi-level columns
pivoted_df.columns = [f'{col[0]}_{col[1]}' for col in pivoted_df.columns]

# Reset the index to make 'Fecha', 'Grupo' and 'match_number' regular columns
pivoted_df = pivoted_df.reset_index()

# --- End of your original code ---

# Merge the 'Hora' and 'Cancha' details back into the pivoted DataFrame.
# We use 'Fecha', 'Grupo', and 'match_number' as the keys for merging.
pivoted_df = pd.merge(pivoted_df, match_details, on=['Fecha', 'Grupo', 'match_number'], how='left')

# Drop the 'match_number' column as it is no longer needed for the final output.
pivoted_df = pivoted_df.drop(columns='match_number')

# Rename the columns to match the desired output format (Equipo_A, Goles_A, etc.).
pivoted_df = pivoted_df.rename(columns={
    'Equipo_1': 'Equipo_A',
    'Equipo_2': 'Equipo_B',
    'Goles_1': 'Goles_A',
    'Goles_2': 'Goles_B'
})

# Sort the DataFrame by the 'Fecha' column to ensure chronological order based on integer values.
# The previous date conversion steps have been removed as 'Fecha' is now an integer.
pivoted_df = pivoted_df.sort_values(by='Fecha')

# Convert 'Fecha' back to string format after sorting,
# ensuring the row order remains chronological based on the integer values.
pivoted_df['Fecha'] = pivoted_df['Fecha'].astype(str)

# Reorder the columns to place 'Hora' and 'Cancha' immediately after 'Fecha'.
pivoted_df = pivoted_df[['Fecha', 'Hora', 'Cancha', 'Grupo', 'Equipo_A', 'Goles_A', 'Equipo_B', 'Goles_B']]

# Define the column configuration for pivoted_df for Streamlit
column_config_pivoted = {
    "Fecha": st.column_config.NumberColumn("Fecha", width=50, format="%d", help="Fecha del partido"),
    "Grupo": st.column_config.NumberColumn("Grupo", width=50, format="%d", help="Grupo al que pertenecen los equipos"),
    "Hora": st.column_config.TextColumn("Hora", width=70, help="Hora del partido"),
    "Cancha": st.column_config.TextColumn("Cancha", width=100, help="Cancha donde se juega el partido"),
    "Equipo_A": st.column_config.TextColumn("Equipo A", width=100, help="Nombre del primer equipo"),
    "Goles_A": st.column_config.NumberColumn("Goles A", format="%d", help="Goles del primer equipo"),
    "Equipo_B": st.column_config.TextColumn("Equipo B", width=100, help="Nombre del segundo equipo"),
    "Goles_B": st.column_config.NumberColumn("Goles B", format="%d", help="Goles del segundo equipo"),
}

# Display the DataFrame as a Streamlit table with the new configuration
st.dataframe(
    pivoted_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config_pivoted
)

####################################################################
#### Cuartos de final##############
###################################################################

# Resultados de Cuartos de final

# 1 Grupo 1 vs 4 Grupo 2
# 1 Grupo 2 vs 4 Grupo 1
# 2 Grupo 1 vs 3 Grupo 2
# 2 Grupo 2 vs 3 Grupo 1

st.divider()

#st.subheader("Cuartos de final")
st.markdown("## <span style='color: #ADD8E6;'>Cuartos de final</span>", unsafe_allow_html=True) # Changed to light blue

# Extract specific 'Equipo' values for the 'Equipo A' column
equipo_a_values = [
    final_stats_sorted1['Equipo'].iloc[0],  # First value from final_stats_sorted1
    final_stats_sorted['Equipo'].iloc[0],   # First value from final_stats_sorted
    final_stats_sorted1['Equipo'].iloc[1],  # Second value from final_stats_sorted1
    final_stats_sorted['Equipo'].iloc[1]    # Second value from final_stats_sorted
]

# Extract specific 'Equipo' values for the 'Equipo B' column
equipo_b_values = [
    final_stats_sorted['Equipo'].iloc[3],   # Fourth value from final_stats_sorted
    final_stats_sorted1['Equipo'].iloc[3],  # Fourth value from final_stats_sorted1
    final_stats_sorted['Equipo'].iloc[2],   # Third value from final_stats_sorted
    final_stats_sorted1['Equipo'].iloc[2]   # Third value from final_stats_sorted1
]

# Define values for the new 'Hora' and 'Cancha' columns
hora_values = ['8:50', '9:50', '8:50', '9:50']
cancha_values = [1, 1, 2, 2]

goles_a = [5,1,4, 2]
goles_b = [2, 1, 1, 0]


# Create the new DataFrame with the added columns and specified order
new_df = pd.DataFrame({
    'Hora': hora_values,    # New 'Hora' column
    'Cancha': cancha_values, # New 'Cancha' column
    'Equipo A': equipo_a_values,
    'Goles A': goles_a,  # Blank column 'Goles A'
    'Equipo B': equipo_b_values,
    'Goles B': goles_b    # Blank column 'Goles B'
})

# Define the column configuration for new_df for Streamlit
column_config_new_df = {
    "Hora": st.column_config.TextColumn("Hora", width=70, help="Hora del partido"),
    "Cancha": st.column_config.NumberColumn("Cancha", width=100, format="%d", help="Cancha donde se juega el partido"),
    "Equipo A": st.column_config.TextColumn("Equipo A", width=100, help="Nombre del primer equipo"),
    "Goles A": st.column_config.NumberColumn("Goles A", format="%d", help="Goles del primer equipo"), # Changed to NumberColumn
    "Equipo B": st.column_config.TextColumn("Equipo B", width=100, help="Nombre del segundo equipo"),
    "Goles B": st.column_config.NumberColumn("Goles B", format="%d", help="Goles del segundo equipo"), # Changed to NumberColumn
}

# Display the DataFrame as a Streamlit table with the new configuration

st.dataframe(
    new_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config_new_df
)

####################################################################
#### Semifinal##############
###################################################################

# Ganador CF1 vs Ganador CF4
# Gnador CF2 vs Ganador CF3

# Helper function to determine the winner based on scores
def get_winner(goles_a, goles_b, equipo_a_name, equipo_b_name):
    if goles_a > goles_b:
        return equipo_a_name
    elif goles_b > goles_a:
        return equipo_b_name
    else:
        return " " # Or you can choose one team in case of a tie

# Helper function to determine the loser based on scores
def get_loser(goles_a, goles_b, equipo_a_name, equipo_b_name):
    if goles_a < goles_b:
        return equipo_a_name
    elif goles_b < goles_a:
        return equipo_b_name
    else:
        return " " # Or you can choose one team in case of a tie

# Initialize lists for the new DataFrame's 'Equipo A' and 'Equipo B' columns
winners_equipo_a_new_df = []
winners_equipo_b_new_df = []

# Row 1 of the new DataFrame (Semifinal 1)
# Equipo A: winner of the first row of new_df
winner_row0_equipo_a = get_winner(
    new_df['Goles A'].iloc[0],
    new_df['Goles B'].iloc[0],
    new_df['Equipo A'].iloc[0],
    new_df['Equipo B'].iloc[0]
)
winners_equipo_a_new_df.append(winner_row0_equipo_a)

# Equipo B: winner of the fourth row of new_df
winner_row3_equipo_b = get_winner(
    new_df['Goles A'].iloc[3],
    new_df['Goles B'].iloc[3],
    new_df['Equipo A'].iloc[3],
    new_df['Equipo B'].iloc[3]
)
winners_equipo_b_new_df.append(winner_row3_equipo_b)

# Row 2 of the new DataFrame (Semifinal 2)
# Equipo A: winner of the second row of new_df
winner_row1_equipo_a = get_winner(
    new_df['Goles A'].iloc[1],
    new_df['Goles B'].iloc[1],
    new_df['Equipo A'].iloc[1],
    new_df['Equipo B'].iloc[1]
)
winners_equipo_a_new_df.append(winner_row1_equipo_a)

# Equipo B: winner of the third row of new_df
winner_row2_equipo_b = get_winner(
    new_df['Goles A'].iloc[2],
    new_df['Goles B'].iloc[2],
    new_df['Equipo A'].iloc[2],
    new_df['Equipo B'].iloc[2]
)
winners_equipo_b_new_df.append(winner_row2_equipo_b)

# Dummy scores for Semifinal matches to allow winner/loser determination
goles_a_semi = [0, 0] # Example scores for Semifinal Team A
goles_b_semi = [0, 0] # Example scores for Semifinal Team B

# Create the 'winners_df' (Semifinal matches)
winners_df = pd.DataFrame({
    'Hora': ['8:50', '9:50'], # Filled with specified values
    'Cancha': [1, 2], # Filled with specified values
    'Equipo A': winners_equipo_a_new_df,
    'Goles A': goles_a_semi, # Now contains dummy numerical values for semi-finals
    'Equipo B': winners_equipo_b_new_df,
    'Goles B': goles_b_semi  # Now contains dummy numerical values for semi-finals
})

#Define column configuration for the new winners_df
column_config_winners_df = {
    "Hora": st.column_config.TextColumn("Hora", width=70, help="Hora del partido"),
    "Cancha": st.column_config.TextColumn("Cancha", width=100, help="Cancha donde se juega el partido"),
    "Equipo A": st.column_config.TextColumn("Equipo A", width=100, help="Nombre del equipo ganador"),
    "Goles A": st.column_config.TextColumn("Goles A", help=""),
    "Equipo B": st.column_config.TextColumn("Equipo B", width=100, help="Nombre del equipo ganador"),
    "Goles B": st.column_config.TextColumn("Goles B", help=""),
}

# Display the new DataFrame
st.markdown("## <span style='color: #008000;'>Semifinal</span>", unsafe_allow_html=True) # Changed to green
st.dataframe(
    winners_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config_winners_df
)




####################################################################
#### Final##############
###################################################################

# --- Create winners_winners_df (Finalists) ---
finalists_equipo_a = get_winner(
    winners_df['Goles A'].iloc[0],
    winners_df['Goles B'].iloc[0],
    winners_df['Equipo A'].iloc[0],
    winners_df['Equipo B'].iloc[0]
)

finalists_equipo_b = get_winner(
    winners_df['Goles A'].iloc[1],
    winners_df['Goles B'].iloc[1],
    winners_df['Equipo A'].iloc[1],
    winners_df['Equipo B'].iloc[1]
)

winners_winners_df = pd.DataFrame({
    'Hora': ['9:50'],
    'Cancha': [1],
    'Equipo A': [finalists_equipo_a],
    'Goles A': [0],
    'Equipo B': [finalists_equipo_b],
    'Goles B': [0]
})

# Define column configuration for winners_winners_df (Final)
column_config_winners_winners_df = {
    "Hora": st.column_config.TextColumn("Hora", width=70, help="Hora del partido"),
    "Cancha": st.column_config.NumberColumn("Cancha", width=100, format="%d", help="Cancha donde se juega el partido"),
    "Equipo A": st.column_config.TextColumn("Equipo A", width=100, help="Nombre del primer equipo finalista"),
    "Goles A": st.column_config.NumberColumn("Goles A", format="%d", help="Goles del primer equipo finalista"),
    "Equipo B": st.column_config.TextColumn("Equipo B", width=100, help="Nombre del segundo equipo finalista"),
    "Goles B": st.column_config.NumberColumn("Goles B", format="%d", help="Goles del segundo equipo finalista"),
}

# Display the Finalists DataFrame
st.markdown("## <span style='color: #FF0000;'>Final</span>", unsafe_allow_html=True) # Changed to green
st.dataframe(
    winners_winners_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config_winners_winners_df)


####################################################################
#### 3rd Place Playoff##############
###################################################################



# --- Create losers_losers_df (3rd Place Playoff) ---
losers_equipo_a = get_loser(
    winners_df['Goles A'].iloc[0],
    winners_df['Goles B'].iloc[0],
    winners_df['Equipo A'].iloc[0],
    winners_df['Equipo B'].iloc[0]
)

losers_equipo_b = get_loser(
    winners_df['Goles A'].iloc[1],
    winners_df['Goles B'].iloc[1],
    winners_df['Equipo A'].iloc[1],
    winners_df['Equipo B'].iloc[1]
)

losers_losers_df = pd.DataFrame({
    'Hora': ['8:50'],
    'Cancha': [2],
    'Equipo A': [losers_equipo_a],
    'Goles A': [0],
    'Equipo B': [losers_equipo_b],
    'Goles B': [0]
})

# Define column configuration for losers_losers_df (3rd Place Playoff)
column_config_losers_losers_df = {
    "Hora": st.column_config.TextColumn("Hora", width=70, help="Hora del partido"),
    "Cancha": st.column_config.NumberColumn("Cancha", width=100, format="%d", help="Cancha donde se juega el partido"),
    "Equipo A": st.column_config.TextColumn("Equipo A", width=100, help="Nombre del primer equipo perdedor"),
    "Goles A": st.column_config.NumberColumn("Goles A", format="%d", help="Goles del primer equipo perdedor"),
    "Equipo B": st.column_config.TextColumn("Equipo B", width=100, help="Nombre del segundo equipo perdedor"),
    "Goles B": st.column_config.NumberColumn("Goles B", format="%d", help="Goles del segundo equipo perdedor"),
}

# Display the 3rd Place Playoff DataFrame
st.subheader("Tercer y cuarto puesto")
st.dataframe(
    losers_losers_df,
    use_container_width=True,
    hide_index=True,
    column_config=column_config_losers_losers_df
)

########################################################################
###### Tarjetas por equipo #########################################
###################################################################

st.divider()

st.subheader("Tarjetas amarillas por Equipo")

csv_file_path = 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/refs/heads/main/Tarjetas_apertura_2025_CLC.csv'
df2 = pd.read_csv(csv_file_path)

# --- Debugging and Data Standardization Start ---

df2.columns = df2.columns.str.strip().str.upper()
df2['EQUIPO'] = df2['EQUIPO'].astype(str).str.strip().str.title()
df2['JUGADOR'] = df2['JUGADOR'].astype(str).str.strip().str.title()

# Print unique values of 'Equipo' to identify potential inconsistencies (e.g., extra spaces)
# st.write(df2['EQUIPO'].unique()) # Commented out as this is for debugging and not meant for final display

# Standardize the 'Equipo' column: strip whitespace and convert to title case
# This ensures that variations like "Real Madrid " or "real madrid" are treated as "Real Madrid"
df2['EQUIPO'] = df2['EQUIPO'].astype(str).str.strip().str.title()

# Print unique values of 'Equipo' after standardization
# st.write(df2['EQUIPO'].unique()) # Commented out as this is for debugging and not meant for final display

# Using .str.contains() with case=False to find 'Real Madrid' regardless of initial case
# df2[df2['EQUIPO'].str.contains('Real Madrid', na=False, case=False)][['EQUIPO', '2F']] # Commented out

# --- Debugging and Data Standardization End ---


# Identify columns from '1F' to '8F'
# This list comprehension dynamically finds columns that contain 'F' and are alphabetically between '1F' and '8F'.
columns_to_check = [col for col in df2.columns if 'F' in col and '1F' <= col <= '8F']

# Initialize dictionaries to store counts for '1A', '1R', and '2A'
# Each dictionary will store team names as keys and another dictionary (column-wise counts) as values.
counts_1A = {}
counts_1R = {}
counts_2A = {}

# Iterate over each unique team name in the 'Equipo' column
for team in df2['EQUIPO'].unique():
    # Filter the DataFrame to get data only for the current team
    team_df = df2[df2['EQUIPO'] == team]

    # Initialize column-wise counts for the current team for each type ('1A', '1R', '2A')
    # All columns in 'columns_to_check' are initialized with a count of 0.
    team_counts_1A = {col: 0 for col in columns_to_check}
    team_counts_1R = {col: 0 for col in columns_to_check}
    team_counts_2A = {col: 0 for col in columns_to_check}

    # Iterate over each column that needs to be checked (from '1F' to '8F')
    for col in columns_to_check:
        # Convert the column to string type to ensure accurate comparison with '1A', '1R', '2A'.
        # .str.contains() works on string data.
        # na=False ensures that NaN values are treated as empty strings and do not cause errors
        # or match the search patterns.
        team_counts_1A[col] = team_df[col].astype(str).str.contains('1A', na=False).sum()
        team_counts_1R[col] = team_df[col].astype(str).str.contains('1R', na=False).sum()
        team_counts_2A[col] = team_df[col].astype(str).str.contains('2A', na=False).sum()

    # Store the calculated counts for the current team in the main dictionaries
    counts_1A[team] = team_counts_1A
    counts_1R[team] = team_counts_1R
    counts_2A[team] = team_counts_2A

# Convert the dictionaries of counts into pandas DataFrames for a structured and readable output.
# orient='index' makes the dictionary keys (team names) the DataFrame index.
df_counts_1A = pd.DataFrame.from_dict(counts_1A, orient='index')
df_counts_1R = pd.DataFrame.from_dict(counts_1R, orient='index')
df_counts_2A = pd.DataFrame.from_dict(counts_2A, orient='index')

# Add a new column 'Total_F_Count' to each DataFrame, summing values from '1F' to '8F'
df_counts_1A['Total_1A_Count'] = df_counts_1A[columns_to_check].sum(axis=1)
df_counts_1R['Total_1R_Count'] = df_counts_1R[columns_to_check].sum(axis=1)
df_counts_2A['Total_2A_Count'] = df_counts_2A[columns_to_check].sum(axis=1)

# Multiply by two the 2A total count
df_counts_2A['Total_2A_Count'] = df_counts_2A['Total_2A_Count'] * 2

# Drop the individual '1F' to '8F' columns from each DataFrame
df_counts_1A = df_counts_1A.drop(columns=columns_to_check)
df_counts_1R = df_counts_1R.drop(columns=columns_to_check)
df_counts_2A = df_counts_2A.drop(columns=columns_to_check)

# Assign the index as a variable called Equipo and the index reset it
df_counts_1R.index.name = 'Equipo'
df_counts_1R = df_counts_1R.reset_index()

# Join the DataFrames into a new DataFrame by their index (Equipo)
# The 'join' method performs a left join by default on the index.
# We are joining df_counts_1A with df_counts_2A
final_counts_df = df_counts_1A.join(df_counts_2A)

# Assign the index as a variable called Equipo and the index reset it
final_counts_df.index.name = 'Equipo'
final_counts_df = final_counts_df.reset_index()

# adding up column Total_1A_Count with Total_2A_Count
final_counts_df = final_counts_df.assign(Total_A_Count=final_counts_df['Total_1A_Count'] + final_counts_df['Total_2A_Count'])

# Drop columns Total_1A_Count, Total_2A_Count
final_counts_df = final_counts_df.drop(columns=['Total_1A_Count', 'Total_2A_Count'])


# Sort the final_counts_df by 'Total_A_Count' in descending order for the bar chart
final_counts_df = final_counts_df.sort_values(by='Total_A_Count', ascending=False)

# Create the bar chart for yellow cards per team
chart_yellow_cards = alt.Chart(final_counts_df).mark_bar().encode(
    x=alt.X('Equipo:N', sort='-y', title=''), # Sort by y-axis (Total_A_Count) descending
    y=alt.Y('Total_A_Count:Q', title='Tarjetas Amarillas 🟨'),
    tooltip=['Equipo', 'Total_A_Count']
).properties(
)

# Display the chart in Streamlit
st.altair_chart(chart_yellow_cards, use_container_width=True)

###########################################################################
###### Tabla de goleadores #################################
###########################################################################

st.divider()

st.subheader("Tabla de goleadores")



csv_file_path3 = 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/refs/heads/main/Goleadores_apertura_2025_CLC.csv'
df3 = pd.read_csv(csv_file_path3)


df3.columns = df3.columns.str.strip().str.upper()
df3['EQUIPO'] = df3['EQUIPO'].astype(str).str.strip().str.title()
df3['NOMBRE Y APELLIDO'] = df3['NOMBRE Y APELLIDO'].astype(str).str.strip().str.title()
df3['GOLES'] = df3['GOLES'].astype(int)
df3 = df3.sort_values(by='GOLES', ascending=False)
df_goleador = df3.head(8)


# Define the column configuration for df_goleador
    # Column names here must match the actual uppercase column names in df_goleador
column_config_goleador = {
        "NOMBRE Y APELLIDO": st.column_config.TextColumn("Nombre", width = 100, help="Name of the goal scorer"),
        "EQUIPO": st.column_config.TextColumn("Equipo", width = 100,  help="Team of the player"),
        "GOLES": st.column_config.NumberColumn("Goles ⚽", format="%d", help="Number of goals scored"),
        # Add configurations for other columns in df_goleador as needed
    }

# Display the DataFrame as a Streamlit table with the new configuration
st.dataframe(
        df_goleador,
        use_container_width=True,
        hide_index=True,
        column_config=column_config_goleador
    )

###########################################################################
###### Tarjetas amarillas por jugadores #################################
###########################################################################

st.divider()

csv_file_path2 = 'https://raw.githubusercontent.com/jsaraviadrago/verbose-system/refs/heads/main/Tarjetas_apertura_2025_CLC.csv'
df2 = pd.read_csv(csv_file_path2)

df2.columns = df2.columns.str.strip().str.upper()
df2['EQUIPO'] = df2['EQUIPO'].astype(str).str.strip().str.title()
df2['JUGADOR'] = df2['JUGADOR'].astype(str).str.strip().str.title()

# --- Debugging and Data Standardization Start ---

#Identify columns from '1F' to '8F'
columns_to_check_Jug = [col for col in df2.columns if 'F' in col and '1F' <= col <= '8F']

# Initialize dictionaries to store counts for '1A', '1R', and '2A'
counts_1A_Jug = {}
counts_1R_Jug = {}
counts_2A_Jug = {}

# Iterate over each unique player in the 'JUGADOR' column
for player in df2['JUGADOR'].unique():
    # Filter the DataFrame to get data only for the current player
    player_df = df2[df2['JUGADOR'] == player]

    # Initialize column-wise counts for the current player for each type ('1A', '1R', '2A')
    player_counts_1A = {col: 0 for col in columns_to_check_Jug}
    player_counts_1R = {col: 0 for col in columns_to_check_Jug}
    player_counts_2A = {col: 0 for col in columns_to_check_Jug}

    # Iterate over each column that needs to be checked (from '1F' to '8F')
    for col in columns_to_check_Jug:
        player_counts_1A[col] = player_df[col].astype(str).str.contains('1A', na=False).sum()
        player_counts_1R[col] = player_df[col].astype(str).str.contains('1R', na=False).sum()
        player_counts_2A[col] = player_df[col].astype(str).str.contains('2A', na=False).sum()

    # Store the calculated counts for the current player in the main dictionaries
    counts_1A_Jug[player] = player_counts_1A
    counts_1R_Jug[player] = player_counts_1R
    counts_2A_Jug[player] = player_counts_2A

# Convert the dictionaries of counts into pandas DataFrames
df_counts_1A_Jug = pd.DataFrame.from_dict(counts_1A_Jug, orient='index')
df_counts_1R_Jug = pd.DataFrame.from_dict(counts_1R_Jug, orient='index')
df_counts_2A_Jug = pd.DataFrame.from_dict(counts_2A_Jug, orient='index')

# Add a new column 'TOTAL_F_COUNT' to each DataFrame, summing values from '1F' to '8F'
df_counts_1A_Jug['TOTAL_1A_COUNT'] = df_counts_1A_Jug[columns_to_check_Jug].sum(axis=1)
df_counts_1R_Jug['TOTAL_1R_COUNT'] = df_counts_1R_Jug[columns_to_check_Jug].sum(axis=1)
df_counts_2A_Jug['TOTAL_2A_COUNT'] = df_counts_2A_Jug[columns_to_check_Jug].sum(axis=1)

# Multiply by two the 2A total count
df_counts_2A_Jug['TOTAL_2A_COUNT'] = df_counts_2A_Jug['TOTAL_2A_COUNT'] * 2

# Drop the individual '1F' to '8F' columns from each DataFrame
df_counts_1A_Jug = df_counts_1A_Jug.drop(columns=columns_to_check_Jug)
df_counts_1R_Jug = df_counts_1R_Jug.drop(columns=columns_to_check_Jug)
df_counts_2A_Jug = df_counts_2A_Jug.drop(columns=columns_to_check_Jug)

# Join the DataFrames into a new DataFrame by their index (JUGADOR)
final_counts_df_Jug = df_counts_1A_Jug.join(df_counts_2A_Jug)

# Assign the index as a variable called JUGADOR and reset it
final_counts_df_Jug.index.name = 'JUGADOR'
final_counts_df_Jug = final_counts_df_Jug.reset_index()

# Assign the index as a variable called JUGADOR and reset it
df_counts_1R_Jug.index.name = 'JUGADOR'
df_counts_1R_Jug = df_counts_1R_Jug.reset_index()

# Adding up column TOTAL_1A_COUNT with TOTAL_2A_COUNT
final_counts_df_Jug = final_counts_df_Jug.assign(TOTAL_A_COUNT=final_counts_df_Jug['TOTAL_1A_COUNT'] + final_counts_df_Jug['TOTAL_2A_COUNT'])

# Drop columns TOTAL_1A_COUNT, TOTAL_2A_COUNT
final_counts_df_Jug = final_counts_df_Jug.drop(columns=['TOTAL_1A_COUNT', 'TOTAL_2A_COUNT'])

# Merge df_counts_1R_Jug and final_counts_df_Jug with df2 to get the 'EQUIPO' column
df_counts_1R_Jug = pd.merge(df_counts_1R_Jug, df2[['JUGADOR', 'EQUIPO']], on='JUGADOR', how='left').drop_duplicates(subset=['JUGADOR'])
final_counts_df_Jug = pd.merge(final_counts_df_Jug, df2[['JUGADOR', 'EQUIPO']], on='JUGADOR', how='left').drop_duplicates(subset=['JUGADOR'])

# Rename columns for df_counts_1R_Jug
df_counts_1R_Jug = df_counts_1R_Jug.rename(columns={'JUGADOR': 'Nombre', 'EQUIPO': 'Equipo', 'TOTAL_1R_COUNT': 'Tarjetas'})

# Rename columns for final_counts_df_Jug
final_counts_df_Jug = final_counts_df_Jug.rename(columns={'JUGADOR': 'Nombre', 'EQUIPO': 'Equipo', 'TOTAL_A_COUNT': 'Tarjetas'})

# Select and reorder columns for display
df_counts_1R_Jug = df_counts_1R_Jug[['Nombre', 'Equipo', 'Tarjetas']]
final_counts_df_Jug = final_counts_df_Jug[['Nombre', 'Equipo', 'Tarjetas']]

# Sort the DataFrames by 'Tarjetas' in descending order
df_counts_1R_Jug = df_counts_1R_Jug.sort_values(by='Tarjetas', ascending=False)
final_counts_df_Jug = final_counts_df_Jug.sort_values(by='Tarjetas', ascending=False)

# Reset the index for both DataFrames
df_counts_1R_Jug = df_counts_1R_Jug.reset_index(drop=True)
final_counts_df_Jug = final_counts_df_Jug.reset_index(drop=True)

# Get only the first five
final_counts_df_Jug = final_counts_df_Jug.head(5)
df_counts_1R_Jug = df_counts_1R_Jug.head(5)


# Define column configurations for df_counts_1R_Jug
column_config_1R = {
    "Nombre": st.column_config.TextColumn("Nombre", width=130, help="Name of the player"),
    "Equipo": st.column_config.TextColumn("Equipo", width=120, help="Team of the player"),
    "Tarjetas": st.column_config.NumberColumn("🟥", width=80, format="%d", help="Number of red cards"),
}

# Define column configurations for final_counts_df_Jug
column_config_A = {
    "Nombre": st.column_config.TextColumn("Nombre", width=130, help="Name of the player"),
    "Equipo": st.column_config.TextColumn("Equipo", width=120, help="Team of the player"),
    "Tarjetas": st.column_config.NumberColumn("🟨", width=80, format="%d", help="Number of yellow cards"),
}

# Streamlit code to display tables side by side
col2, col1 = st.columns(2)

with col2:
    st.subheader("Tarjetas Amarillas")
    st.dataframe(
        final_counts_df_Jug,
        use_container_width=True,
        hide_index=True,
        column_config=column_config_A
    )

with col1:
    st.subheader("Tarjetas Rojas")
    st.dataframe(
        df_counts_1R_Jug,
        use_container_width=True,
        hide_index=True,
        column_config=column_config_1R
    )



