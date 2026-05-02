import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processor import load_match_data, MAP_CONFIG
from PIL import Image

st.set_page_config(page_title="LILA BLACK: Level Design Tool", layout="wide")

st.title("🎯 LILA BLACK Player Journey Visualizer")
st.sidebar.header("Filters")

# 1. Select Date
date_folder = st.sidebar.selectbox("Select Date", 
    ["February_10", "February_11", "February_12", "February_13", "February_14"])

@st.cache_data
def get_data(folder):
    return load_match_data(f"player_data/{folder}")

df = get_data(date_folder)

# 2. Select Map
map_name = st.sidebar.selectbox("Select Map", df['map_id'].unique())
map_df = df[df['map_id'] == map_name]

# 3. Select Match
match_id = st.sidebar.selectbox("Select Match ID", map_df['match_id'].unique())
match_data = map_df[map_df['match_id'] == match_id].sort_values('ts')

# 4. Filter Bots
show_bots = st.sidebar.checkbox("Show Bots", value=True)
if not show_bots:
    match_data = match_data[match_data['is_bot'] == False]

# 5. Timeline Slider
max_ts = int(match_data['ts'].max())
time_range = st.slider("Match Timeline (ms)", 0, max_ts, max_ts)
current_data = match_data[match_data['ts'] <= time_range]

# --- VISUALIZATION ---
st.subheader(f"Map Analysis: {map_name}")

# Load background image
img_path = MAP_CONFIG[map_name]['img']
img = Image.open(img_path)

# Create Plotly Figure
fig = px.scatter(
    current_data, 
    x='px_x', y='px_y', 
    color='event', 
    symbol='is_bot',
    hover_data=['user_id', 'ts', 'y'],
    title=f"Match ID: {match_id}"
)

# Add paths (lines) for players
for player in current_data['user_id'].unique():
    p_data = current_data[current_data['user_id'] == player]
    fig.add_scatter(x=p_data['px_x'], y=p_data['px_y'], mode='lines', 
                    line=dict(width=1), opacity=0.3, showlegend=False)

# Overlay on the Minimap
fig.update_layout(
    images=[dict(
        source=img,
        xref="x", yref="y",
        x=0, y=0,
        sizex=1024, sizey=1024,
        sizing="stretch",
        layer="below")],
    xaxis=dict(range=[0, 1024], visible=False),
    yaxis=dict(range=[1024, 0], visible=False), # Flip Y axis to match 0,0 at top-left
    width=800, height=800,
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# Heatmap Section (Requirement)
if st.checkbox("Show Heatmap of Kill Zones"):
    kill_data = map_df[map_df['event'].isin(['Kill', 'BotKill'])]
    heat_fig = px.density_heatmap(kill_data, x='px_x', y='px_y', nbinsx=50, nbinsy=50, 
                                 title="Aggregated Kill Heatmap (All Matches)")
    st.plotly_chart(heat_fig)