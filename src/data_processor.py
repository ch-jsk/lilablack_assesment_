import pandas as pd
import os
import pyarrow.parquet as pq

# Map Configurations from README
MAP_CONFIG = {
    "AmbroseValley": {"scale": 900, "origin_x": -370, "origin_z": -473, "img": "minimaps/AmbroseValley_Minimap.png"},
    "GrandRift": {"scale": 581, "origin_x": -290, "origin_z": -290, "img": "minimaps/GrandRift_Minimap.png"},
    "Lockdown": {"scale": 1000, "origin_x": -500, "origin_z": -500, "img": "minimaps/Lockdown_Minimap.jpg"}
}

def map_to_pixel(x, z, map_id):
    config = MAP_CONFIG.get(map_id)
    if not config: return 0, 0
    u = (x - config["origin_x"]) / config["scale"]
    v = (z - config["origin_z"]) / config["scale"]
    px_x = u * 1024
    px_y = (1 - v) * 1024 
    return px_x, px_y

def get_match_index(folder_path):
    """Scans filenames to get match/player metadata without loading heavy data into RAM"""
    if not os.path.exists(folder_path): return pd.DataFrame()
    files = [f for f in os.listdir(folder_path) if not f.startswith('.')]
    meta = []
    for f in files:
        parts = f.split('_')
        if len(parts) >= 2:
            u_id = parts[0]
            m_id = parts[1]
            meta.append({'filename': f, 'user_id': u_id, 'match_id': m_id})
    return pd.DataFrame(meta)

def load_specific_match(folder_path, filenames):
    """Only loads the specific parquet files for the selected match to save RAM"""
    dfs = []
    for f in filenames:
        path = os.path.join(folder_path, f)
        table = pq.read_table(path)
        df = table.to_pandas()
        # Decode bytes to string
        df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
        # Identify bots (Short numeric IDs)
        df['is_bot'] = df['user_id'].apply(lambda x: str(x).isdigit())
        if not df.empty:
            map_id = df['map_id'].iloc[0]
            df[['px_x', 'px_y']] = df.apply(lambda r: map_to_pixel(r['x'], r['z'], map_id), axis=1, result_type='expand')
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()