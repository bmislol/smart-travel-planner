# Smart Travel Planner

## 🛠️ 1. Data Architecture & Feature Engineering

Rather than relying on synthetic or pre-labeled Kaggle datasets, the data pipeline aggregates:

* **Geographic Hub (World Cities):** Serves as the geographic anchor, providing standardized city names, country ISO codes, exact geographic coordinates (Lat/Lng) for map plotting, and population metrics (to gauge urban density for "Culture" and "Family" suitability).
* **Economic Reality (Numbeo Cost of Living Index):** Provides real-world economic metrics (e.g., Restaurant Price Index, Groceries Index, Rent). This mathematical foundation allows the model to definitively distinguish between "Budget" and "Luxury" destinations without subjective bias.
* **Meteorological Baselines (Global City Climate Data):** Provides historical average temperatures by month. This addresses physical user constraints (e.g., "I want somewhere warm in July") and correlates strongly with "Relaxation" or "Adventure" biomes.

### 2. The Data Engineering Pipeline
The dataset was constructed using a custom Python backend script (`backend/scripts/dataset_merger.py`) with the following methodology:
1. **The Anchor Extraction:** Filtered a global database of 48,000+ cities down to the top 600 most populated global hubs to ensure recognizable, highly-trafficked tourist destinations.
2. **Data Sanitization:** * Parsed combined `"City, Country"` string arrays into atomic columns.
   * Cleansed scraped meteorological data by stripping extraneous Fahrenheit conversions, newline characters, and typographic Unicode minus signs (`−`) to ensure pure `float64` compatibility.
3. **The Grand Merge (Inner Join):** Utilized rigorous lowercase string matching and Python Set intersections to perform an inner join across all three disparate datasets.

### 3. The Final Dataset
The pipeline resulted in a pristine, `NaN`-free dataset of exactly **108 global destinations**, perfectly satisfying the project's strict 100-to-200 destination requirement. This curated matrix provides robust, uncorrupted feature vectors (`X`) ready for label engineering and machine learning classification.
*(More features to be documented as data cleaning progresses)*