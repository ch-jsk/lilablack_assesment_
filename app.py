import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_processor import get_match_index, load_specific_match, MAP_CONFIG
from PIL import Image

st.set_page_config(page_title="LILA BLACK Forensic Tool", layout="wide")

# Justice for Events: Symbols and Colors
EVENT_META = {
    'Position':      {'color': '#3498db', 'symbol': 'circle', 'label': 'Human Move'},
    'BotPosition':   {'color': '#9b59b6', 'symbol': 'circle', 'label': 'Bot Move'},
    'Kill':          {'color': '#e74c3c', 'symbol': 'x',      'label': 'Kill (Human)'},
    'Killed':        {'color': '#c0392b', 'symbol': 'x-open', 'label': 'Death (by Human)'},
    'BotKill':       {'color': '#f39c12', 'symbol': 'x',      'label': 'Kill (Bot)'},
    'BotKilled':     {'color': '#d35400', 'symbol': 'x-open', 'label': 'Death (by Bot)'},
    'KilledByStorm': {'color': '#2c3e50', 'symbol': 'cloud',  'label': 'Storm Death'},
    'Loot':          {'color': '#27ae60', 'symbol': 'star',   'label': 'Loot Picked Up'}
}

st.title("🎯 LILA BLACK: Forensic Match Visualizer")

# --- SIDEBAR ---
date_folder = st.sidebar.selectbox("Select Date", ["February_10", "February_11", "February_12", "February_13", "February_14"])
folder_path = f"data/{date_folder}"

match_index = get_match_index(folder_path)

if match_index.empty:
    st.error("No data found. Please check your GitHub folder structure (should be data/February_10/...).")
else:
    # 1. Map Selection (Fixed the KeyError here)
    if 'map_id' in match_index.columns:
        available_maps = sorted([m for m in match_index['map_id'].unique() if m != "Unknown"])
        selected_map = st.sidebar.selectbox("Select Map", available_maps)
        
        # 2. Match Selection (Filtered by Map)
        map_matches = match_index[match_index['map_id'] == selected_map]
        selected_match = st.sidebar.selectbox("Select Match ID", map_matches['match_id'].unique())
        
        # 3. Load Match Data
        match_filenames = match_index[match_index['match_id'] == selected_match]['filename'].tolist()
        
        @st.cache_data
        def get_match_data(path, files):
            return load_specific_match(path, files)
        
        match_data = get_match_data(folder_path, match_filenames).sort_values('ts')
        
        # Player Labels (P1, B1...)
        humans = match_data[~match_data['is_bot']]['user_id'].unique()
        bots = match_data[match_data['is_bot']]['user_id'].unique()
        label_map = {uid: f"P{i+1}" for i, uid in enumerate(humans)}
        label_map.update({uid: f"B{i+1}" for i, uid in enumerate(bots)})
        match_data['label'] = match_data['user_id'].map(label_map)

        # Timeline Slider
        match_data['elapsed_ms'] = (match_data['ts'] - match_data['ts'].min()).dt.total_seconds() * 1000
        max_ms = int(match_data['elapsed_ms'].max())
        time_limit = st.slider("Match Timeline (ms from start)", 0, max_ms, max_ms)
        
        current_data = match_data[match_data['elapsed_ms'] <= time_limit]

        # --- MAIN VIEW ---
        col1, col2 = st.columns([4, 1])

        with col1:
            img = Image.open(MAP_CONFIG[selected_map]['img'])
            fig = go.Figure()

            # Growing Paths (Justice for Path Line)
            for uid in current_data['user_id'].unique():
                p_df = current_data[current_data['user_id'] == uid]
                is_b = p_df['is_bot'].iloc[0]
                label = p_df['label'].iloc[0]
                
                # Tail
                fig.add_trace(go.Scatter(
                    x=p_df['px_x'], y=p_df['px_y'], mode='lines',
                    line=dict(width=2, color='rgba(52, 152, 219, 0.4)' if not is_b else 'rgba(155, 89, 182, 0.2)'),
                    showlegend=False, hoverinfo='none'
                ))
                
                # Head
                last_pos = p_df.iloc[-1:]
                fig.add_trace(go.Scatter(
                    x=last_pos['px_x'], y=last_pos['px_y'], mode='markers+text',
                    text=label, textposition="top center",
                    marker=dict(size=12, color='#2980b9' if not is_b else '#8e44ad', symbol='circle'),
                    name=label, showlegend=False
                ))

            # Action Icons (Stars for Loot, X for Kills)
            actions = current_data[~current_data['event'].str.contains('Position')]
            for ev in actions['event'].unique():
                ev_df = actions[actions['event'] == ev]
                meta = EVENT_META.get(ev, {'color': 'white', 'symbol': 'circle'})
                fig.add_trace(go.Scatter(
                    x=ev_df['px_x'], y=ev_df['px_y'], mode='markers',
                    marker=dict(size=12, color=meta['color'], symbol=meta['symbol'], line=dict(width=1, color='white')),
                    name=meta.get('label', ev)
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
            if st.checkbox("🔥 Show Map Kill Density"):
                kills = match_data[match_data['event'].str.contains('Kill|Killed')]
                if not kills.empty:
                    heat = px.density_heatmap(kills, x='px_x', y='px_y', nbinsx=30, nbinsy=30)
                    heat.add_layout_image(dict(source=img, xref="x", yref="y", x=0, y=0, sizex=1024, sizey=1024, sizing="stretch", layer="below"))
                    heat.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), coloraxis_showscale=False)
                    st.plotly_chart(heat, width='stretch')
                else:
                    st.caption("No kills in this match yet.")

            st.write("---")
            st.write("**Recent Activity Log**")
            log = actions[['label', 'event', 'elapsed_ms']].tail(7).sort_values('elapsed_ms', ascending=False)
            if not log.empty:
                st.table(log)
            else:
                st.caption("No events yet.")
    else:
        st.warning("Could not identify map data. Verify the parquet files contain 'map_id'.")