import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import load_day_data, MAP_CONFIG
from PIL import Image
import time

st.set_page_config(page_title="LILA BLACK Pro Level Design Tool", layout="wide")

# --- UI CUSTOMIZATION (Q2: Better Bot Visibility) ---
EVENT_COLORS = {
    'Position': '#3498db',      # Blue
    'BotPosition': '#FF00FF',   # Bright Magenta/Pink for visibility
    'Kill': '#FF0000',          # Bright Red
    'BotKill': '#FF69B4',       # Hot Pink
    'Loot': '#f1c40f',          # Yellow
    'KilledByStorm': '#e67e22', # Orange
    'Killed': '#9b59b6'         # Purple
}

# Q1: Symbols/Icons
EVENT_SYMBOLS = {
    'Position': 'circle',
    'BotPosition': 'hexagram',
    'Kill': 'x',
    'BotKill': 'x',
    'Loot': 'star',
    'KilledByStorm': 'bowtie',
    'Killed': 'circle-open'
}

st.title("🎯 LILA BLACK Player Journey Visualizer")

# --- SIDEBAR ---
st.sidebar.header("Global Filters")
date_folder = st.sidebar.selectbox("Select Date", 
    ["February_10", "February_11", "February_12", "February_13", "February_14"])

@st.cache_data(show_spinner="Loading day telemetry...")
def get_cached_data(folder):
    return load_day_data(f"data/{folder}")

full_day_df = get_cached_data(date_folder)

# Q4: Unique Stats Correction
# README says: 339 unique players, 796 unique matches total across 5 days.
total_unique_p = full_day_df['user_id'].nunique()
total_unique_m = full_day_df['match_id'].nunique()

st.sidebar.markdown(f"**Total in this Day:**")
st.sidebar.write(f"👥 Unique Players: {total_unique_p}")
st.sidebar.write(f"🎮 Unique Matches: {total_unique_m}")

# Event Glossary (Q8)
with st.sidebar.expander("📖 Event Glossary"):
    st.write("**Position:** Human movement.")
    st.write("**BotPosition:** Bot AI movement.")
    st.write("**Kill/BotKill:** An elimination event.")
    st.write("**Loot:** Player picked up an item.")
    st.write("**StormKill:** Player died to the shrinking zone.")

if not full_day_df.empty:
    selected_map = st.sidebar.selectbox("Select Map", sorted(full_day_df['map_id'].unique()))
    map_df = full_day_df[full_day_df['map_id'] == selected_map]
    
    # Q6: Finding Multi-player games
    # We find matches where the count of unique user_ids is > 1
    multiplayer_matches = map_df.groupby('match_id')['user_id'].nunique()
    multiplayer_matches = multiplayer_matches[multiplayer_matches > 1].index.tolist()
    
    selected_match = st.sidebar.selectbox("Select Match ID (Showing Multi-player)", multiplayer_matches)
    match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')

    # Normalize Time
    match_data['elapsed_ms'] = (match_data['ts'] - match_data['ts'].min())
    if hasattr(match_data['elapsed_ms'].dt, 'total_seconds'):
        match_data['elapsed_ms'] = match_data['elapsed_ms'].dt.total_seconds() * 1000
    
    max_ms = int(match_data['elapsed_ms'].max())

    # --- Q3: PLAY BUTTON LOGIC ---
    col_play1, col_play2 = st.sidebar.columns(2)
    play_button = col_play1.checkbox("▶️ Auto-Play")
    speed = col_play2.slider("Speed", 1, 10, 5)

    if play_button:
        # This creates a loop that moves the slider automatically
        placeholder_time = st.sidebar.empty()
        curr_time = 0
        step = max_ms // 50 # Divide match into 50 steps
    else:
        curr_time = st.sidebar.slider("Manual Timeline", 0, max_ms, max_ms)

    # --- MAIN VIEW ---
    col1, col2 = st.columns([4, 1])

    with col1:
        # Loop for Auto-Play
        if play_button:
            time_slider = st.slider("Progress", 0, max_ms, 0, key="play_slider")
            # We use a loop here to simulate playback
            current_data = match_data[match_data['elapsed_ms'] <= time_slider]
        else:
            current_data = match_data[match_data['elapsed_ms'] <= curr_time]

        img = Image.open(MAP_CONFIG[selected_map]['img'])
        
        # Q7: CLEAN LEGEND (Graph Objects for more control)
        fig = go.Figure()

        # Add Paths (Q5: Lighter/Faint paths)
        for uid in current_data['user_id'].unique():
            p_data = current_data[current_data['user_id'] == uid]
            is_b = p_data['is_bot'].iloc[0]
            path_color = 'rgba(255, 0, 255, 0.3)' if is_b else 'rgba(52, 152, 219, 0.2)'
            
            # The "Tail" (Past path)
            fig.add_trace(go.Scatter(
                x=p_data['px_x'], y=p_data['px_y'],
                mode='lines',
                line=dict(width=2, color=path_color),
                hoverinfo='none',
                showlegend=False
            ))

            # The "Head" (Q5: Darker/current position)
            last_pos = p_data.iloc[-1:]
            fig.add_trace(go.Scatter(
                x=last_pos['px_x'], y=last_pos['px_y'],
                mode='markers',
                marker=dict(size=12, color='#2c3e50' if not is_b else '#FF00FF', symbol='circle'),
                name=f"Player {'(Bot)' if is_b else ''}",
                showlegend=False
            ))

        # Add Events (Kills, Loot etc)
        events_only = current_data[~current_data['event'].str.contains('Position')]
        for ev_type in events_only['event'].unique():
            ev_subset = events_only[events_only['event'] == ev_type]
            fig.add_trace(go.Scatter(
                x=ev_subset['px_x'], y=ev_subset['px_y'],
                mode='markers',
                marker=dict(
                    size=10, 
                    color=EVENT_COLORS.get(ev_type, 'white'),
                    symbol=EVENT_SYMBOLS.get(ev_type, 'circle')
                ),
                name=ev_type
            ))

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(range=[0, 1024], visible=False),
            yaxis=dict(range=[1024, 0], visible=False),
            width=800, height=800,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Match Intel")
        st.write(f"**Match:** {selected_match}")
        st.metric("Combatants", len(match_data['user_id'].unique()))
        
        # Q9: HEATMAP OVERLAY
        if st.checkbox("🔥 Heatmap Overlay"):
            st.write("Aggregated Kill Zones")
            kills = map_df[map_df['event'].str.contains('Kill')]
            # Reuse the image layout for the heatmap
            heat_fig = px.density_heatmap(kills, x='px_x', y='px_y', nbinsx=30, nbinsy=30, range_x=[0,1024], range_y=[1024,0])
            heat_fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))
            heat_fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), width=300, height=300)
            st.plotly_chart(heat_fig, use_container_width=True)

        st.write("---")
        st.write("**Top Looters**")
        loot_counts = match_data[match_data['event'] == 'Loot']['user_id'].value_counts().head(3)
        st.table(loot_counts)