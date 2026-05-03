import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import load_day_data, MAP_CONFIG
from PIL import Image

st.set_page_config(page_title="LILA BLACK : Match Visualizer", layout="wide")

# --- 1. ENHANCED EVENT MAPPING (All 8 Types from README) ---
# We use specific symbols: x for deaths, stars for loot, circles for movement
EVENT_META = {
    'Position':      {'color': '#3498db', 'symbol': 'circle', 'label': 'Human Move'},
    'BotPosition':   {'color': '#9b59b6', 'symbol': 'circle', 'label': 'Bot Move'},
    'Kill':          {'color': '#e74c3c', 'symbol': 'x',      'label': 'Kill (Human vs Human)'},
    'Killed':        {'color': '#c0392b', 'symbol': 'x-open', 'label': 'Death (by Human)'},
    'BotKill':       {'color': '#f39c12', 'symbol': 'x',      'label': 'Kill (vs Bot)'},
    'BotKilled':     {'color': '#d35400', 'symbol': 'x-open', 'label': 'Death (by Bot)'},
    'KilledByStorm': {'color': '#2c3e50', 'symbol': 'cloud',  'label': 'Storm Death'},
    'Loot':          {'color': '#27ae60', 'symbol': 'star',   'label': 'Loot Picked Up'}
}

st.title("🎯 LILA BLACK: Match Visualizer")

# --- DATA LOADING ---
date_folder = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"])

@st.cache_data
def get_cached_day(folder):
    return load_day_data(f"data/{folder}")

full_day_df = get_cached_day(date_folder)

if not full_day_df.empty:
    selected_map = st.sidebar.selectbox("Select Map", sorted(full_day_df['map_id'].unique()))
    map_df = full_day_df[full_day_df['map_id'] == selected_map]
    
    # Logic to find matches with actual human interaction
    match_counts = map_df[map_df['is_bot'] == False].groupby('match_id')['user_id'].nunique()
    multi_matches = match_counts[match_counts > 1].index.tolist()
    
    selected_match = st.sidebar.selectbox("Select Match ID", multi_matches if multi_matches else map_df['match_id'].unique())
    
    # Reconstruct the full match timeline
    match_data = map_df[map_df['match_id'] == selected_match].sort_values('ts')
    
    # Human-friendly labels
    humans = match_data[~match_data['is_bot']]['user_id'].unique()
    bots = match_data[match_data['is_bot']]['user_id'].unique()
    label_map = {uid: f"P{i+1}" for i, uid in enumerate(humans)}
    label_map.update({uid: f"B{i+1}" for i, uid in enumerate(bots)})
    match_data['label'] = match_data['user_id'].map(label_map)

    # Convert ts to match-relative milliseconds for the slider
    match_data['elapsed_ms'] = (match_data['ts'] - match_data['ts'].min()).dt.total_seconds() * 1000
    max_ms = int(match_data['elapsed_ms'].max())

    # --- LAYOUT ---
    col1, col2 = st.columns([4, 1])

    with col1:
        # TIMELINE SLIDER (Manual Playback)
        time_limit = st.slider("Match Timeline (ms)", 0, max_ms, max_ms)
        
        # Filter data to only show what has happened UP TO THIS POINT
        current_data = match_data[match_data['elapsed_ms'] <= time_limit]
        
        img = Image.open(MAP_CONFIG[selected_map]['img'])
        fig = go.Figure()

        # A. DRAW GROWING PATHS ( जस्टिस for "Path Line" )
        # We only draw the path up to the current time_limit
        for uid in current_data['user_id'].unique():
            p_df = current_data[current_data['user_id'] == uid]
            is_b = p_df['is_bot'].iloc[0]
            
            # The "Tail" (Line showing where they've been)
            fig.add_trace(go.Scatter(
                x=p_df['px_x'], y=p_df['px_y'],
                mode='lines',
                line=dict(width=2, color='rgba(52, 152, 219, 0.4)' if not is_b else 'rgba(155, 89, 182, 0.2)'),
                showlegend=False, hoverinfo='none'
            ))
            
            # The "Head" (Current position marker with label)
            last_pos = p_df.iloc[-1:]
            fig.add_trace(go.Scatter(
                x=last_pos['px_x'], y=last_pos['px_y'],
                mode='markers+text',
                text=last_pos['label'], textposition="top center",
                marker=dict(size=12, color='#2980b9' if not is_b else '#8e44ad', symbol='circle'),
                name=f"Current: {last_pos['label'].iloc[0]}",
                showlegend=False
            ))

        # B. DRAW EVENTS ( जस्टिस for "Kills/Loot/Storm" )
        # Events "pop up" on the map as the slider moves
        events_only = current_data[~current_data['event'].str.contains('Position')]
        for ev_type in events_only['event'].unique():
            ev_df = events_only[events_only['event'] == ev_type]
            meta = EVENT_META.get(ev_type, {'color': 'white', 'symbol': 'circle', 'label': ev_type})
            
            fig.add_trace(go.Scatter(
                x=ev_df['px_x'], y=ev_df['px_y'],
                mode='markers',
                marker=dict(size=10, color=meta['color'], symbol=meta['symbol'], line=dict(width=1, color='white')),
                name=meta['label']
            ))

        fig.update_layout(
            images=[dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below")],
            xaxis=dict(range=[0, 1024], visible=False),
            yaxis=dict(range=[1024, 0], visible=False),
            width=800, height=800,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, width='stretch')

    with col2:
        st.subheader("Match Intel")
        st.write(f"**Humans:** {len(humans)} | **Bots:** {len(bots)}")
        
        st.write("---")
        # JUSTIC for Heatmap (Death Zones)
        if st.checkbox("🔥 Show Kill Heatmap"):
            st.caption("Aggregated death zones for this map")
            kill_data = map_df[map_df['event'].str.contains('Kill|Killed')]
            heat = px.density_heatmap(kill_data, x='px_x', y='px_y', nbinsx=30, nbinsy=30)
            heat.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))
            heat.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), coloraxis_showscale=False, width=250, height=250)
            st.plotly_chart(heat, width='stretch')

        st.write("---")
        st.write("**Event Log (Real-time)**")
        # Show a list of important events that happened up to the slider point
        log_data = events_only[['label', 'event', 'elapsed_ms']].tail(10).sort_values('elapsed_ms', ascending=False)
        st.table(log_data)