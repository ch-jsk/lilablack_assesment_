import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import load_day_data, MAP_CONFIG
from PIL import Image
import time

st.set_page_config(page_title="LILA BLACK Player Journey Visualizer", layout="wide")

# --- CUSTOM THEME & SYMBOLS ---
COLORS = {
    'HumanPath': 'rgba(52, 152, 219, 0.4)', # Light Blue
    'HumanHead': '#1a5276',               # Dark Blue
    'BotPath': 'rgba(155, 89, 182, 0.3)',   # Light Purple
    'BotHead': '#7d3c98',                 # Dark Purple
    'Loot': '#f1c40f',                    # Yellow
    'Kill': '#e74c3c',                    # Red
    'Storm': '#e67e22'                    # Orange
}

SYMBOLS = {
    'Kill': 'x',
    'Loot': 'star',
    'Storm': 'cloud', # Emoji-like cloud
    'Position': 'circle'
}

st.title("🎯 LILA BLACK: Player Journey Tool")

# --- DATA LOADING ---
date_folder = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"])

@st.cache_data
def get_cached_data(folder):
    return load_day_data(f"data/{folder}")

full_day_df = get_cached_data(date_folder)

if not full_day_df.empty:
    # Filter only matches with multiple players for action
    multiplayer_matches = full_day_df.groupby('match_id')['user_id'].nunique()
    multiplayer_matches = multiplayer_matches[multiplayer_matches > 1].index.tolist()
    
    selected_map = st.sidebar.selectbox("Select Map", sorted(full_day_df['map_id'].unique()))
    selected_match = st.sidebar.selectbox("Select Match ID (Multi-player)", multiplayer_matches)
    
    match_data = full_day_df[full_day_df['match_id'] == selected_match].sort_values('ts')
    match_data['elapsed_ms'] = (match_data['ts'] - match_data['ts'].min())
    if hasattr(match_data['elapsed_ms'].dt, 'total_seconds'):
        match_data['elapsed_ms'] = match_data['elapsed_ms'].dt.total_seconds() * 1000
    
    # --- PLAYER NUMBERING (P1, P2, B1...) ---
    humans = match_data[~match_data['is_bot']]['user_id'].unique()
    bots = match_data[match_data['is_bot']]['user_id'].unique()
    player_map = {uid: f"P{i+1}" for i, uid in enumerate(humans)}
    player_map.update({uid: f"B{i+1}" for i, uid in enumerate(bots)})
    match_data['label'] = match_data['user_id'].map(player_map)

    # --- AUTO-PLAY CONTROLS ---
    st.sidebar.subheader("Playback Controls")
    max_ms = int(match_data['elapsed_ms'].max())
    
    # Initialize session state for the slider
    if 'current_ms' not in st.session_state:
        st.session_state.current_ms = max_ms

    col_a, col_b = st.sidebar.columns(2)
    if col_a.button("▶️ Play"):
        for i in range(0, max_ms, max_ms // 40): # 40 frames of animation
            st.session_state.current_ms = i
            time.sleep(0.1)
            st.rerun()

    if col_b.button("⏹️ Reset"):
        st.session_state.current_ms = 0
        st.rerun()

    current_ms = st.sidebar.slider("Timeline (ms)", 0, max_ms, st.session_state.current_ms)
    current_data = match_data[match_data['elapsed_ms'] <= current_ms]

    # --- MAP VISUALIZATION ---
    col1, col2 = st.columns([4, 1])

    with col1:
        img = Image.open(MAP_CONFIG[selected_map]['img'])
        fig = go.Figure()

        # 1. Draw Paths (Light Blue Tails)
        for uid in current_data['user_id'].unique():
            p_data = current_data[current_data['user_id'] == uid]
            is_bot = p_data['is_bot'].iloc[0]
            label = p_data['label'].iloc[0]
            
            # The Tail
            fig.add_trace(go.Scatter(
                x=p_data['px_x'], y=p_data['px_y'],
                mode='lines',
                line=dict(width=2, color=COLORS['BotPath'] if is_bot else COLORS['HumanPath']),
                hoverinfo='none', showlegend=False
            ))

            # The Head (Current Pos + Label)
            last_pos = p_data.iloc[-1:]
            fig.add_trace(go.Scatter(
                x=last_pos['px_x'], y=last_pos['px_y'],
                mode='markers+text',
                text=label, textposition="top center",
                marker=dict(size=12, color=COLORS['BotHead'] if is_bot else COLORS['HumanHead'], symbol='circle'),
                name=label
            ))

        # 2. Add Special Events
        events = current_data[~current_data['event'].str.contains('Position')]
        for ev in events['event'].unique():
            ev_df = events[events['event'] == ev]
            color = COLORS['Kill'] if 'Kill' in ev else COLORS['Loot']
            if 'Storm' in ev: color = COLORS['Storm']
            
            fig.add_trace(go.Scatter(
                x=ev_df['px_x'], y=ev_df['px_y'],
                mode='markers',
                marker=dict(size=14, color=color, symbol=SYMBOLS.get(ev.replace('Bot',''), 'circle')),
                name=ev
            ))

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(range=[0, 1024], visible=False),
            yaxis=dict(range=[1024, 0], visible=False),
            width=850, height=850, margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Match Intel")
        # Q9: Transparent Heatmap Overlay
        if st.checkbox("🔥 Kill Heatmap Overlay"):
            st.write("Visualizing Choke Points")
            # Filter all kills for this map
            all_kills = full_day_df[full_day_df['map_id'] == selected_map]
            all_kills = all_kills[all_kills['event'].str.contains('Kill')]
            
            heat_fig = px.density_heatmap(
                all_kills, x='px_x', y='px_y', 
                nbinsx=40, nbinsy=40,
                color_continuous_scale="YlOrRd", # Yellow to Red
                range_x=[0, 1024], range_y=[1024, 0]
            )
            # Remove white background to make it transparent overlay
            heat_fig.update_traces(opacity=0.6) 
            heat_fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))
            heat_fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), coloraxis_showscale=False, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(heat_fig, use_container_width=True)
            
        st.write("---")
        st.write("**Player Roles**")
        st.dataframe(match_data.groupby(['label', 'is_bot'])['event'].count().rename("Total Events"))