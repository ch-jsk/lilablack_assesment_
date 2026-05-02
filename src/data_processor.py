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

def is_bot(user_id):
    # Based on README: UUIDs (with hyphens) are humans, short numbers are bots
    return str(user_id).isdigit()

def load_day_data(folder_path):
    """Loads all files for a specific day and combines them"""
    if not os.path.exists(folder_path):
        return pd.DataFrame()

    all_files = [f for f in os.listdir(folder_path) if not f.startswith('.')]
    dfs = []
    
    for f in all_files:
        path = os.path.join(folder_path, f)
        try:
            # Pyarrow reads these even without .parquet extension
            table = pq.read_table(path)
            df = table.to_pandas()
            
            # 1. Clean Event column (bytes to string)
            df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)
            
            # 2. Identify Bots vs Humans
            df['is_bot'] = df['user_id'].apply(is_bot)
            
            # 3. Apply coordinate mapping
            if not df.empty:
                map_id = df['map_id'].iloc[0]
                df[['px_x', 'px_y']] = df.apply(
                    lambda row: map_to_pixel(row['x'], row['z'], map_id), 
                    axis=1, result_type='expand'
                )
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue
    
    if not dfs:
        return pd.DataFrame()
        
    return pd.concat(dfs, ignore_index=True)