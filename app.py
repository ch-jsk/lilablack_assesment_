import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import get_match_index, load_specific_match, MAP_CONFIG
from PIL import Image

st.set_page_config(page_title="LILA BLACK Forensic Tool", layout="wide")

# Colors
EVENT_COLORS = {
    'Position': '#3498db', 'BotPosition': '#9b59b6',
    'Kill': '#e74c3c', 'BotKill': '#f39c12',
    'Killed': '#c0392b', 'BotKilled': '#d35400',
    'KilledByStorm': '#2c3e50', 'Loot': '#27ae60'
}

st.title("🎯 LILA BLACK: Forensic Match Visualizer")

# Sidebar
date_folder = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"])
folder_path = f"data/{date_folder}"

# 1. Scan filenames (High Speed, Low RAM)
match_index = get_match_index(folder_path)

if match_index.empty:
    st.error("No files found. Check your 'data/' folder structure.")
else:
    # 2. Match Selection
    # To show "Multiple Players", we prioritize matches with the most files
    match_counts = match_index.groupby('match_id').size().sort_values(ascending=False)
    selected_match = st.sidebar.selectbox("Select Match ID (Sorted by Player Count)", match_counts.index)
    
    # 3. Load ONLY the relevant files
    match_filenames = match_index[match_index['match_id'] == selected_match]['filename'].tolist()
    
    @st.cache_data
    def get_match_data(path, files):
        return load_specific_match(path, files)
    
    match_data = get_match_data(folder_path, match_filenames).sort_values('ts')
    selected_map = match_data['map_id'].iloc[0]
    
    # Labeling
    h = match_data[~match_data['is_bot']]['user_id'].unique()
    b = match_data[match_data['is_bot']]['user_id'].unique()
    label_map = {uid: f"P{i+1}" for i, uid in enumerate(h)}
    label_map.update({uid: f"B{i+1}" for i, uid in enumerate(b)})
    match_data['label'] = match_data['user_id'].map(label_map)

    # Animation steps
    match_data['time_step'] = pd.cut(match_data['ts'], bins=25, labels=False)

    col1, col2 = st.columns([4, 1])

    with col1:
        img = Image.open(MAP_CONFIG[selected_map]['img'])
        
        # Base Animation
        fig = px.scatter(
            match_data, x="px_x", y="px_y", animation_frame="time_step", animation_group="user_id",
            color="event", text="label", color_discrete_map=EVENT_COLORS,
            range_x=[0, 1024], range_y=[1024, 0]
        )

        # Paths
        for uid in match_data['user_id'].unique():
            p_df = match_data[match_data['user_id'] == uid]
            is_bot = p_df['is_bot'].iloc[0]
            fig.add_trace(go.Scatter(
                x=p_df['px_x'], y=p_df['px_y'], mode='lines',
                line=dict(width=1, color='rgba(52, 152, 219, 0.2)' if not is_bot else 'rgba(155, 89, 182, 0.1)'),
                showlegend=False, hoverinfo='none'
            ))

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(visible=False), yaxis=dict(visible=False), width=800, height=800,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 600
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Match Intel")
        st.write(f"👥 Humans: {len(h)} | 🤖 Bots: {len(b)}")
        st.write("---")
        st.write("**Event Legend:**")
        st.markdown("⭐ **Loot** | ❌ **Kill** | ☁️ **Storm**")
        st.info("The match list is sorted by player count. Matches at the top will show the most interaction!")