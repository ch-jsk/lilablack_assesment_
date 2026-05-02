Architecture: Player Journey Visualization Tool

1. Tech Stack & Rationale

  - Language: Python 3.10+
  - Framework: Streamlit.
      - Why: As a PM, I chose Streamlit to maximize "time-to-insight." It allows
        for rapid building of interactive data UI without the overhead of a
        separate frontend/backend repo. It natively handles the dataframes and
        sliders needed for match playback.
  - Data Processing: Pandas + PyArrow.
      - Why: Essential for high-performance reading of Parquet files and
        efficient filtering of ~89,000 rows.
  - Visualization: Plotly.
      - Why: Provides out-of-the-box zoom, pan, and hover tooltips, which are
        critical for Level Designers to inspect specific death locations or loot
        drops.
  - Deployment: Streamlit Community Cloud / Vercel.
      - Why: Provides a stable, shareable URL with zero-config CI/CD from
        GitHub.

2. Data Flow

1.  Ingestion: The tool crawls the player_data/ directory.
2.  Preprocessing:
      - Decodes event column from bytes to UTF-8.
      - Identifies is_bot status based on user_id format (Numeric vs. UUID).
3.  Filtering: User selects Map/Date/Match via the sidebar. Data is sliced in
    memory to keep the UI snappy.
4.  Transformation: World coordinates (x, z) are converted to pixel coordinates
    (px_x, px_z) using map-specific constants.
5.  Rendering: The minimap image is used as a background layout for a Plotly
    scatter/line plot.

3. Coordinate Mapping Logic

To ensure the telemetry overlays perfectly on the 1024x1024 minimaps, I
implemented the following transformation:

1.  UV Conversion: Translate world coordinates to a 0-1 range.
      - u = (x - origin_x) / scale
      - v = (z - origin_z) / scale
2.  Pixel Mapping:
      - pixel_x = u * 1024
      - pixel_y = (1 - v) * 1024
      - Note: The v axis is inverted (1-v) because game engines often treat the
        bottom-left as (0,0), while browser images treat the top-left as (0,0).

4. Key Assumptions

  - Elevation (y): I assumed y (verticality) is secondary for a 2D minimap tool.
    I have excluded it from the primary visualization but included it in hover
    tooltips to help designers identify if a kill happened on a roof or ground
    floor.
  - Session Continuity: I assumed a "Match" is the primary unit of analysis. The
    tool combines multiple parquet files sharing a match_id to show the full
    "story" of the game session.
  - Bot Detection: Based on the README, I assumed any user_id that is purely
    numeric (e.g., "1440") is a bot.

5. Trade-offs & Decisions

| Decision                | Pros                                                         | Cons                                                                                |
| :---------------------- | :----------------------------------------------------------- | :---------------------------------------------------------------------------------- |
| **In-Memory Filtering** | Extremely fast interaction for the user once data is loaded. | Memory usage scales with data size; might lag if dataset grows to millions of rows. |
| **Plotly vs. Canvas**   | Richer interactivity (zoom/hover) and faster development.    | Slightly heavier "feel" compared to a lightweight custom JS canvas.                 |
| **Flattening Files**    | Combining all players into one view helps see "clashes."     | Initial load time is longer than loading a single player file.                      |

