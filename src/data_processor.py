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
    
    # Step 1: UV Coords
    u = (x - config["origin_x"]) / config["scale"]
    v = (z - config["origin_z"]) / config["scale"]
    
    # Step 2: Pixel Coords (1024x1024)
    px_x = u * 1024
    px_y = (1 - v) * 1024 # Inverted for top-left origin
    return px_x, px_y

def is_bot(user_id):
    # UUIDs contain hyphens and letters; Bots are numeric
    return str(user_id).isdigit()

def load_match_data(folder_path):
    all_files = [f for f in os.listdir(folder_path) if not f.startswith('.')]
    dfs = []
    for f in all_files:
        path = os.path.join(folder_path, f)
        table = pq.read_table(path)
        df = table.to_pandas()
        # Decode events
        df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
        # Identify Bots
        df['is_bot'] = df['user_id'].apply(is_bot)
        dfs.append(df)
    
    full_df = pd.concat(dfs, ignore_index=True)
    # Apply coordinate mapping
    full_df[['px_x', 'px_y']] = full_df.apply(
        lambda row: map_to_pixel(row['x'], row['z'], row['map_id']), 
        axis=1, result_type='expand'
    )
    return full_df