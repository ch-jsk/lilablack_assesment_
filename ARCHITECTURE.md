## 1. Overview

This system converts raw parquet gameplay data into an interactive visualization tool.

Flow:
Parquet Files → Data Processing → Streamlit App → Plotly Visualization

---

## 2. Tech Choices

| Component | Tool | Reason |
|----------|------|--------|
| UI + Backend | Streamlit | Fast development and deployment |
| Data Processing | Pandas + PyArrow | Efficient parquet handling |
| Visualization | Plotly | Interactive and flexible |
| Images | PIL | Simple minimap handling |

---

## 3. Data Flow

### Step 1: Load Data
- Load all parquet files from selected date folder
- Each file represents one player in one match
    pq.read_table(path)
---

### Step 2: Data Cleaning
- Decode event column (bytes → string)
- Identify bots using numeric user_id
   df['event'] = decode
   df['is_bot'] = user_id.isdigit()
---

### Step 3: Coordinate Mapping

Game uses 3D world coordinates (x, z).  
We convert them into 2D minimap pixel coordinates.

Formula:

u = (x - origin_x) / scale  
v = (z - origin_z) / scale  

px_x = u * 1024  
px_y = (1 - v) * 1024  

This ensures correct alignment with the minimap.

---

### Step 4: Match Reconstruction
- Combine all players with same match_id
- Sort by timestamp
   match_data.sort_values('ts')
---

### Step 5: Filtering
User selects:
- Date
- Map
- Match

Only relevant data is processed and displayed.

---

### Step 6: Visualization

#### Player Paths
- Lines show movement history
- Marker shows current position

#### Events
- Non-movement events plotted as markers
- Plot markers (kills, loot, etc.)

#### Heatmap
- Density map of kill events

---

## 4. Performance Decisions

### Caching (Lazy Loading)

Using:
@st.cache_data

Benefits:
- Avoids repeated file reads
- Reduces computation
- Improves response time

---

### Timeline Tradeoff

Initially implemented autoplay timeline.

Issues faced:
- Frequent 503 server errors
- High memory usage
- Too many UI re-renders in Streamlit

Decision:
- Replaced with manual timeline slider
- More stable and controllable

---

## 5. Assumptions

| Area          | Assumption |
|-----          |----------|
| Bot detection | Numeric user_id = bot |
| Timestamp     | Relative within match |
| Map config    | Fixed values per map |

---

## 6. Tradeoffs

| Decision                  | Tradeoff |
|---------                  |---------|
| Streamlit vs React        | Faster dev, less flexibility |
| Manual slider vs autoplay | Stable but less dynamic |
| Full dataset loading      | Simpler but heavier |

---

## 7. Limitations

- Limited filtering options
- Large datasets may slow initial load

---

