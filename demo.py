import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="Snooker Elo Dashboard", layout="wide")

# Map your display names to your actual CSV file names
ELO_FILES = {
    "Method A (Standard)": "players_score_history.csv",
    "Method B (Option 3 + Decay)": "O3players_score_history.csv"
}

# Cache the data loading so switching toggles is instant
@st.cache_data
def load_data(filename):
    # Load the specific CSV based on the toggle choice
    df = pd.read_csv(filename)
    df['date'] = pd.to_datetime(df['date'])
    return df

# --- 2. SIDEBAR CONTROLS ---
st.sidebar.title("Navigation & Filters")

# NEW: Toggle for the Elo calculation method
selected_method = st.sidebar.radio("Select Elo Calculation:", list(ELO_FILES.keys()))

# Load the data for the currently selected method
current_file = ELO_FILES[selected_method]
try:
    df = load_data(current_file)
except FileNotFoundError:
    st.error(f"Could not find {current_file}. Please ensure your CSV files are in the same folder as app.py and named correctly.")
    st.stop()

# Toggle for the view mode
app_mode = st.sidebar.radio("Choose a view:", ["Daily Rankings", "Score Trajectories"])
st.sidebar.markdown("---")

# --- 3. VIEW 1: DAILY RANKINGS ---
if app_mode == "Daily Rankings":
    st.title(f"Player Rankings - {selected_method}")
    
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    target_date = st.date_input("Select Date for Rankings:", max_date, min_value=min_date, max_value=max_date)
    target_date = pd.to_datetime(target_date)
    
    historical_data = df[df['date'] <= target_date]
    
    if not historical_data.empty:
        rankings = (historical_data.sort_values('date')
                                   .groupby('name')
                                   .tail(1)
                                   .sort_values('score', ascending=False)
                                   .reset_index(drop=True))
        
        rankings.index = rankings.index + 1
        rankings.index.name = "Rank"
        
        # Display the dataframe cleanly
        st.dataframe(rankings[['name', 'score', 'date']], use_container_width=True)
    else:
        st.warning("No data available on or before this date.")

# --- 4. VIEW 2: SCORE TRAJECTORIES ---
elif app_mode == "Score Trajectories":
    st.title(f"Score Trajectories - {selected_method}")
    
    all_players = sorted(df['name'].unique())
    default_players = all_players[:3] if len(all_players) >= 3 else all_players
    
    selected_players = st.multiselect("Select Players to Compare:", all_players, default=default_players)
    
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    date_range = st.date_input("Select Timeframe:", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    if selected_players and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        
        mask = (df['name'].isin(selected_players)) & (df['date'] >= start_date) & (df['date'] <= end_date)
        df_filtered = df[mask]
        
        if not df_filtered.empty:
            fig = px.line(df_filtered,
                          x='date',
                          y='score',
                          color='name',
                          markers=True,
                          title=f"Rating Over Time ({selected_method})")
            
            fig.update_layout(xaxis_title="Date", yaxis_title="Elo Score", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No match data found for these players in the selected timeframe.")