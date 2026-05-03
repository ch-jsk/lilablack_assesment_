import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import get_match_index, load_specific_match, MAP_CONFIG
from PIL import Image

st.set_page_config(page_title="LILA BLACK Match Visualizer", layout="wide")

# Every event from the README is covered here
EVENT_COLORS = {
    'Position': '#3498db', 'BotPosition': '#9b59b6',
    'Kill': '#e74c3c', 'BotKill': '#f39c12',
    'Killed': '#c0392b', 'BotKilled': '#d35400',
    'KilledByStorm': '#2c3e50', 'Loot': '#27ae60'
}

st.title("🎯 LILA BLACK: Match Visualizer")
st.markdown("### Total Data Scope: 339 Players | 796 Matches")

# --- SIDEBAR ---
date_folder = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"])
folder_path = f"data/{date_folder}" # Ensure your folder on GitHub is named 'data'

# 1. Scan Filenames
match_index = get_match_index(folder_path)

if match_index.empty:
    st.error(f"No files found in {folder_path}. Please check your GitHub folder structure.")
else:
    # 2. Match Selection
    match_counts = match_index.groupby('match_id').size().sort_values(ascending=False)
    selected_match = st.sidebar.selectbox("Select Match ID", match_counts.index)
    
    # 3. Load specific files (RAM Optimization)
    match_filenames = match_index[match_index['match_id'] == selected_match]['filename'].tolist()
    
    @st.cache_data
    def get_match_data(path, files):
        return load_specific_match(path, files)
    
    match_data = get_match_data(folder_path, match_filenames).sort_values('ts')
    selected_map = match_data['map_id'].iloc[0]
    
    # Fix: Player Labeling (P1, B1...)
    humans = match_data[~match_data['is_bot']]['user_id'].unique()
    bots = match_data[match_data['is_bot']]['user_id'].unique()
    label_map = {uid: f"P{i+1}" for i, uid in enumerate(humans)}
    label_map.update({uid: f"B{i+1}" for i, uid in enumerate(bots)})
    match_data['label'] = match_data['user_id'].map(label_map)

    # 4. Timeline Slider (The Red Bar)
    # Convert ts to match-relative milliseconds to avoid Timestamp/int errors
    match_data['elapsed_ms'] = (match_data['ts'] - match_data['ts'].min()).dt.total_seconds() * 1000
    max_ms = int(match_data['elapsed_ms'].max())
    
    time_limit = st.slider("Match Timeline (ms from start)", 0, max_ms, max_ms)
    current_data = match_data[match_data['elapsed_ms'] <= time_limit]

    # --- MAIN VIEW ---
    col1, col2 = st.columns([4, 1])

    with col1:
        img = Image.open(MAP_CONFIG[selected_map]['img'])
        fig = go.Figure()

        # Draw Paths (growing tails)
        for uid in current_data['user_id'].unique():
            p_df = current_data[current_data['user_id'] == uid]
            is_b = p_df['is_bot'].iloc[0]
            label = p_df['label'].iloc[0]
            
            fig.add_trace(go.Scatter(
                x=p_df['px_x'], y=p_df['px_y'], mode='lines',
                line=dict(width=2, color='rgba(52, 152, 219, 0.4)' if not is_b else 'rgba(155, 89, 182, 0.2)'),
                showlegend=False, hoverinfo='none'
            ))
            
            last_pos = p_df.iloc[-1:]
            fig.add_trace(go.Scatter(
                x=last_pos['px_x'], y=last_pos['px_y'], mode='markers+text',
                text=label, textposition="top center",
                marker=dict(size=12, color='#2980b9' if not is_b else '#8e44ad', symbol='circle'),
                name=f"Player {label}", showlegend=False
            ))

        # Draw Action Icons (Loot, Kills, Deaths, Storm)
        actions = current_data[~current_data['event'].str.contains('Position')]
        for ev_type in actions['event'].unique():
            ev_df = actions[actions['event'] == ev_type]
            fig.add_trace(go.Scatter(
                x=ev_df['px_x'], y=ev_df['px_y'], mode='markers',
                marker=dict(size=10, color=EVENT_COLORS.get(ev_type, 'white'), symbol='diamond' if 'Loot' in ev_type else 'x'),
                name=ev_type
            ))

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(range=[0, 1024], visible=False), yaxis=dict(range=[1024, 0], visible=False),
            width=800, height=800, margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Match Intel")
        st.write(f"👥 Humans: {len(humans)} | 🤖 Bots: {len(bots)}")
        st.write("---")
        if st.checkbox("🔥 Map Kill Heatmap"):
            kill_data = match_data[match_data['event'].str.contains('Kill|Killed')]
            heat = px.density_heatmap(kill_data, x='px_x', y='px_y', nbinsx=30, nbinsy=30)
            heat.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))
            heat.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), coloraxis_showscale=False)
            st.plotly_chart(heat, width='stretch')
        
        st.write("---")
        st.write("**Recent Log**")
        st.table(actions[['label', 'event']].tail(5))