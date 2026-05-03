import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import load_day_data, MAP_CONFIG
from PIL import Image

# 1. Page Setup
st.set_page_config(page_title="LILA BLACK Forensic Tool", layout="wide")

# 2. Forensic Event Mapping (All 8 Types from README)
# We use specific colors: Blue/Red for Humans, Purple/Orange for Bots/Environment
EVENT_COLORS = {
    'Position':      '#3498db', # Human Path
    'BotPosition':   '#9b59b6', # Bot Path
    'Kill':          '#e74c3c', # Human vs Human
    'Killed':        '#c0392b', # Human Death
    'BotKill':       '#f39c12', # Human vs Bot
    'BotKilled':     '#d35400', # Death by Bot
    'KilledByStorm': '#2c3e50', # Environment Death
    'Loot':          '#27ae60'  # Rewards
}

st.title("🎯 LILA BLACK: Forensic Match Visualizer")

# --- 3. DATA INGESTION ---
date_folder = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"])

@st.cache_data
def get_cached_day(folder):
    return load_day_data(f"data/{folder}")

full_day_df = get_cached_day(date_folder)

if not full_day_df.empty:
    selected_map = st.sidebar.selectbox("Select Map", sorted(full_day_df['map_id'].unique()))
    map_df = full_day_df[full_day_df['map_id'] == selected_map]
    
    # PRODUCT THINKING: Find matches with multiple humans to see real combat interactions
    m_counts = map_df[map_df['is_bot'] == False].groupby('match_id')['user_id'].nunique()
    multi_player_matches = m_counts[m_counts > 1].index.tolist()
    
    selected_match = st.sidebar.selectbox(
        "Select Match ID (Showing matches with 2+ Humans)", 
        multi_player_matches if multi_player_matches else map_df['match_id'].unique()
    )
    
    # Reconstruct the match timeline
    match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')
    
    # Labeling (P1, P2... for Humans | B1, B2... for Bots)
    humans = match_data[~match_data['is_bot']]['user_id'].unique()
    bots = match_data[match_data['is_bot']]['user_id'].unique()
    label_map = {uid: f"P{i+1}" for i, uid in enumerate(humans)}
    label_map.update({uid: f"B{i+1}" for i, uid in enumerate(bots)})
    match_data['label'] = match_data['user_id'].map(label_map)

    # Convert ts to a stable animation frame (25 steps)
    match_data['time_step'] = pd.cut(match_data['ts'], bins=25, labels=False)

    # --- 4. MAIN VIEW ---
    col1, col2 = st.columns([4, 1])

    with col1:
        img = Image.open(MAP_CONFIG[selected_map]['img'])
        
        # Base Animation (Moving Heads)
        fig = px.scatter(
            match_data,
            x="px_x", y="px_y",
            animation_frame="time_step",
            animation_group="user_id",
            color="event",
            text="label",
            hover_data=['label', 'event', 'ts'],
            color_discrete_map=EVENT_COLORS,
            range_x=[0, 1024], range_y=[1024, 0]
        )

        # Static Paths (The "Tails" justice)
        for uid in match_data['user_id'].unique():
            p_df = match_data[match_data['user_id'] == uid]
            is_bot = p_df['is_bot'].iloc[0]
            fig.add_trace(go.Scatter(
                x=p_df['px_x'], y=p_df['px_y'],
                mode='lines',
                line=dict(width=1, color='rgba(52, 152, 219, 0.2)' if not is_bot else 'rgba(155, 89, 182, 0.1)'),
                showlegend=False, hoverinfo='none'
            ))

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            width=800, height=800,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Stable Animation settings (600ms per frame)
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 600
        
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Match Intel")
        st.write(f"👥 Humans: {len(humans)}")
        st.write(f"🤖 Bots: {len(bots)}")
        
        st.write("---")
        if st.checkbox("🔥 Map Kill Heatmap"):
            kills = map_df[map_df['event'].str.contains('Kill|Killed')]
            heat_fig = px.density_heatmap(kills, x='px_x', y='px_y', nbinsx=30, nbinsy=30)
            heat_fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))
            heat_fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), coloraxis_showscale=False)
            st.plotly_chart(heat_fig, width='stretch')
        
        st.write("---")
        st.write("**Event Legend:**")
        st.markdown("⭐ **Loot** | ❌ **Kill** | ☁️ **Storm**")
        st.info("Hit the 'Play' button under the map to see the match unfold in real-time.")

else:
    st.error("Data not found. Please verify your 'data/' folder structure on GitHub.")