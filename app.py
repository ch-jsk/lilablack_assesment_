import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processor import load_day_data, MAP_CONFIG
from PIL import Image

st.set_page_config(page_title="LILA BLACK Level Design Tool", layout="wide")

st.title("LILA BLACK Player Journey Visualizer")
st.markdown("Reconstructing match telemetry for Level Designers.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Global Filters")
date_folder = st.sidebar.selectbox("Select Date", 
    ["February_10", "February_11", "February_12", "February_13", "February_14"])

@st.cache_data(show_spinner="Loading day telemetry...")
def get_cached_data(folder):
    return load_day_data(f"data/{folder}") # Ensure your folder is named 'data'

full_day_df = get_cached_data(date_folder)

if full_day_df.empty:
    st.error("No data found in the selected folder.")
else:
    # Select Map
    map_list = sorted(full_day_df['map_id'].unique())
    selected_map = st.sidebar.selectbox("Select Map", map_list)
    map_df = full_day_df[full_day_df['map_id'] == selected_map]

    # Select Match (This combines all players in that match)
    match_list = sorted(map_df['match_id'].unique())
    selected_match = st.sidebar.selectbox("Select Match ID", match_list)
    
    # Reconstruct the match
    match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')
    
    # Bot Toggle
    show_bots = st.sidebar.checkbox("Include Bots", value=True)
    if not show_bots:
        match_data = match_data[match_data['is_bot'] == False]

    # --- MAIN UI ---
    col1, col2 = st.columns([3, 1])

    with col1:
      # --- UPDATED TIMELINE SLIDER ---
    if not match_data.empty:
        # 1. Convert the 'ts' column to a numeric value (milliseconds from start of match)
        # This handles the case where Parquet loads 'ts' as a Datetime
        match_data['elapsed_ms'] = (match_data['ts'] - match_data['ts'].min())
        
        # If it's a timedelta (common with Parquet), convert to total milliseconds
        if hasattr(match_data['elapsed_ms'].dt, 'total_seconds'):
            match_data['elapsed_ms'] = match_data['elapsed_ms'].dt.total_seconds() * 1000
        
        # 2. Get the max time safely
        max_ms = int(match_data['elapsed_ms'].max())
        
        # 3. Create the slider using the numeric milliseconds
        time_limit = st.slider("Match Progress (ms from start)", 0, max_ms, max_ms)
        
        # 4. Filter data for the visualization
        current_data = match_data[match_data['elapsed_ms'] <= time_limit]
    else:
        st.warning("No data found for this selection. Try including bots or selecting a different match.")
        current_data = pd.DataFrame()
        # Draw the Map
        img = Image.open(MAP_CONFIG[selected_map]['img'])
        
        fig = px.scatter(
            current_data, 
            x='px_x', y='px_y', 
            color='event',
            symbol='is_bot',
            hover_data=['user_id', 'event', 'ts'],
            color_discrete_map={
                'Position': '#3498db',
                'BotPosition': '#95a5a6',
                'Kill': '#e74c3c',
                'Killed': '#9b59b6',
                'Loot': '#f1c40f',
                'KilledByStorm': '#e67e22'
            }
        )

        # Draw paths for each player
        for uid in current_data['user_id'].unique():
            p_path = current_data[current_data['user_id'] == uid]
            fig.add_scatter(x=p_path['px_x'], y=p_path['px_y'], mode='lines', 
                            line=dict(width=1, color='white'), opacity=0.2, showlegend=False)

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(range=[0, 1024], visible=False),
            yaxis=dict(range=[1024, 0], visible=False),
            width=900, height=900,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Match Stats")
        st.metric("Total Players", len(match_data['user_id'].unique()))
        st.metric("Total Events", len(current_data))
        
        st.write("### Event Legend")
        st.info("Dots represent discrete events (Kills, Loot). Lines represent movement paths.")
        
        if st.checkbox("Show Kill Heatmap"):
            # Heatmap of ALL matches on this map for context
            st.write("Aggregated Kill Zones")
            kills = map_df[map_df['event'].str.contains('Kill', na=False)]
            heat = px.density_heatmap(kills, x='px_x', y='px_y', nbinsx=30, nbinsy=30)
            st.plotly_chart(heat, use_container_width=True)