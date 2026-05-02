import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import load_day_data, MAP_CONFIG
from PIL import Image

st.set_page_config(page_title="LILA BLACK Level Design Tool", layout="wide")

# --- COLORS & SYMBOLS ---
# Using distinct colors for different event types
EVENT_COLORS = {
    'Position': 'rgba(52, 152, 219, 0.4)',      # Light Blue path
    'BotPosition': 'rgba(155, 89, 182, 0.3)',   # Light Purple path
    'Kill': '#e74c3c',                          # Red X
    'BotKill': '#ff69b4',                       # Pink X
    'Killed': '#9b59b6',                        # Purple Square
    'KilledByStorm': '#e67e22',                 # Orange Cloud
    'Loot': '#f1c40f'                           # Yellow Star
}

st.title("🎯 LILA BLACK: Multi-Player Match Visualizer")

# --- DATA LOADING ---
date_folder = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"])

@st.cache_data
def get_cached_day(folder):
    # This loads EVERY player file in that folder into one big dataframe
    return load_day_data(f"data/{folder}")

full_day_df = get_cached_day(date_folder)

if not full_day_df.empty:
    selected_map = st.sidebar.selectbox("Select Map", sorted(full_day_df['map_id'].unique()))
    map_df = full_day_df[full_day_df['map_id'] == selected_map]
    
    # PRODUCT THINKING: Filter for matches with multiple humans to see real fights
    match_counts = map_df[map_df['is_bot'] == False].groupby('match_id')['user_id'].nunique()
    multiplayer_matches = match_counts[match_counts > 1].index.tolist()
    
    selected_match = st.sidebar.selectbox(
        "Select Match ID (Showing matches with 2+ Humans)", 
        multiplayer_matches if multiplayer_matches else map_df['match_id'].unique()
    )
    
    # RECONSTRUCTING THE MATCH: Grabbing all players (Humans + Bots) for this ID
    match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')
    
    # Labeling (P1, P2, B1, B2...)
    humans = match_data[~match_data['is_bot']]['user_id'].unique()
    bots = match_data[match_data['is_bot']]['user_id'].unique()
    label_map = {uid: f"P{i+1}" for i, uid in enumerate(humans)}
    label_map.update({uid: f"B{i+1}" for i, uid in enumerate(bots)})
    match_data['label'] = match_data['user_id'].map(label_map)

    # --- MAIN VIEW ---
    col1, col2 = st.columns([4, 1])

    with col1:
        # Create 20 "Time Steps" for smooth animation
        match_data['time_step'] = pd.cut(match_data['ts'], bins=20, labels=False)
        
        img = Image.open(MAP_CONFIG[selected_map]['img'])
        
        # Plotting everyone at once using animation_group="user_id"
        fig = px.scatter(
            match_data,
            x="px_x", y="px_y",
            animation_frame="time_step",
            animation_group="user_id", # This keeps each player's dot separate
            color="event",
            text="label",             # Shows P1, P2 next to the dots
            hover_data=['label', 'event'],
            color_discrete_map=EVENT_COLORS,
            range_x=[0, 1024], range_y=[1024, 0]
        )

        # ADDING THE PATHS (Tails): Loop through every player in this match
        for uid in match_data['user_id'].unique():
            p_df = match_data[match_data['user_id'] == uid]
            is_b = p_df['is_bot'].iloc[0]
            fig.add_trace(go.Scatter(
                x=p_df['px_x'], y=p_df['px_y'],
                mode='lines',
                line=dict(width=1, color='rgba(52, 152, 219, 0.2)' if not is_b else 'rgba(155, 89, 182, 0.1)'),
                showlegend=False, hoverinfo='none'
            ))

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            width=800, height=800,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Playback speed
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 600
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Match Intel")
        st.write(f"**Human Players (P):** {len(humans)}")
        st.write(f"**AI Bots (B):** {len(bots)}")
        
        st.write("---")
        # Heatmap Overlay
        if st.checkbox("🔥 Map-wide Heatmap"):
            kills = map_df[map_df['event'].str.contains('Kill')]
            heat_fig = px.density_heatmap(kills, x='px_x', y='px_y', nbinsx=30, nbinsy=30)
            heat_fig.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))
            heat_fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), coloraxis_showscale=False)
            st.plotly_chart(heat_fig, width='stretch')
        
        st.write("---")
        st.info("The labels (P1, B1) move in real-time. Use the 'Play' button below the map to watch the match unfold.")