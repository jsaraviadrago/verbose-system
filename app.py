import streamlit as st
import pandas as pd

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

# Pivot the table to create separate columns for Equipo and Goles for each team
pivoted_df = df1.pivot(index=['Fecha', 'Grupo', 'match_number'], columns='team_number', values=['Equipo', 'Goles'])

# Flatten the multi-level columns
pivoted_df.columns = [f'{col[0]}_{col[1]}' for col in pivoted_df.columns]

# Reset the index to make 'Fecha', 'Grupo' and 'match_number' regular columns
pivoted_df = pivoted_df.reset_index()

# Drop the match_number column as it is no longer needed
pivoted_df = pivoted_df.drop(columns='match_number')

# Rename the columns to match the desired output
pivoted_df = pivoted_df.rename(columns={
    'Equipo_1': 'Equipo_A',
    'Equipo_2': 'Equipo_B',
    'Goles_1': 'Goles_A',
    'Goles_2': 'Goles_B'
})

# Re order columns
pivoted_df = pivoted_df[['Fecha', 'Grupo', 'Equipo_A', 'Goles_A', 'Equipo_B', 'Goles_B']]

# Define the column configuration for pivoted_df
column_config_pivoted = {
    "Fecha": st.column_config.NumberColumn("Fecha", width=50, format="%d", help="Fecha del partido"),
    "Grupo": st.column_config.NumberColumn("Grupo", width=50, format="%d", help="Grupo al que pertenecen los equipos"),
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

