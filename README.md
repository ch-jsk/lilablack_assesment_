<<<<<<< HEAD
# 🎯 LILA BLACK – Match Visualizer
=======
# LILA BLACK – Match Visualizer
>>>>>>> 1fea3c73f48d3d13cf0aa33da8b57c90e725de0f

## What is this?

This is a web-based visualization tool that helps **Level Designers understand player behavior** in LILA BLACK.

Instead of raw data, this tool shows:
- Player movement paths
- Kill & death events
- Loot pickups
- Storm deaths
- Heatmaps for hotspots

Everything is shown directly on the **game minimap**, making it easy to understand gameplay patterns.

Link to streamlit app: https://lilablack-assessment.streamlit.app/
---

## Features

### 1. Player Movement Tracking
- Shows **real movement paths** of players
- Humans and bots are visually different
- Current position is highlighted with labels (P1, B1, etc.)

---

### 2. Event Visualization
Different events are shown using different markers:

| Event | Meaning |
|------|--------|
| Kill / BotKill | Player kills |
| Killed / BotKilled | Deaths |
| KilledByStorm | Storm deaths |
| Loot | Item pickups |

---

### 3. Timeline Slider (Manual Playback)
- Move the slider to see how the match progresses
- Shows only events **up to that moment**

⚠️ Note:
A full autoplay timeline was initially planned but removed due to:
- Frequent **503 errors (server overload)**
- High memory usage when continuously updating frames
- Streamlit limitations with real-time animation

So instead, a **manual slider** is used for stability and control.

---

### 4. Heatmap (Kill Zones)
- Shows areas where most fights happen
- Helps identify:
  - High-risk zones
  - Popular combat areas

---

### 5. Filters
- Select by **Date**
- Select by **Map**
- Select by **Match**

---

## 🛠️ Tech Stack

- **Frontend + Backend:** Streamlit
- **Data Processing:** Pandas + PyArrow
- **Visualization:** Plotly
- **Images:** PIL

---

## 📂 Project Structure
project/
│
├── app.py # Main Streamlit app
├── src/
│ └──__init__.py
│ └── data_processor.py # Data loading & mapping logic
├── data/ # Parquet files (by date)
└── minimaps/ # Map images

---

## ⚙️ How to Run

pip install -r requirements.txt

streamlit run app.py

