# Player Behavior Insights - LILA BLACK

### 1. Bottleneck at Extraction (Ambrose Valley)
*   **Observation:** In Match `b71aaad8...`, 4 out of 6 human players died within the same 50-pixel radius near the bridge.
*   **Data Back-up:** The Kill event density at coordinates `(X, Z)` is 400% higher than the map average.
*   **Actionable:** The "Storm" forces players through a single choke point too early. We should add a secondary path (a tunnel or shallow water crossing) to reduce "camping" at the bridge.
*   **Metric Affected:** Player Retention (reducing frustration deaths).

### 2. The "Dead" North-East Corner
*   **Observation:** Across 5 days of data, only 2% of Loot events occur in the NE quadrant of Grand Rift.
*   **Data Back-up:** Heatmap analysis shows high travel (lines) but zero interaction markers (dots) in this area.
*   **Actionable:** Level Designers should move a "High Tier Loot" crate to this area to encourage players to use the full map.
*   **Why care:** It prevents the match from becoming too "centralized" and repetitive.

### 3. Bot Pathing vs. Human Intuition
*   **Observation:** Bots (`is_bot: True`) move in perfect straight lines, while humans zig-zag near cover.
*   **Data Back-up:** Compare paths in Lockdown; bots are dying to the Storm more often because they don't navigate around obstacles.
*   **Actionable:** Improve Bot NavMesh near the map edges. 
*   **Why care:** If bots die to the environment, they don't provide a challenge to players, making the "Extraction" feel too easy/empty.