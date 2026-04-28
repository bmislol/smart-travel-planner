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

## 🏷️ 2. Feature & Label Engineering

To prepare the dataset for multi-class classification, raw data was transformed into targeted predictive features, and a deterministic heuristic pipeline was designed to assign ground-truth labels.

### 1. Feature Construction (The Predictors)
To prevent multicollinearity and provide the machine learning model with stronger signals, raw columns were synthesized into engineered features. Irrelevant data (such as the *Rent Index*) was dropped to eliminate noise.
* **Tourist Cost Score:** An aggregated average of the *Cost of Living* and *Restaurant Price* indices. Rent was intentionally excluded as travelers prioritize daily activity and dining costs over long-term apartment leases.
* **Temperature Variance:** Calculated by subtracting the minimum seasonal temperature from the maximum. High variance indicates distinct seasons, while low variance signals a highly stable (often tropical) climate.
* **City Scale:** Raw population numbers were binned into categorical tiers (`Mid/Small`, `Large`, `Megacity`) to help the model better group similar urban environments without over-fitting to exact population counts.

### 2. Heuristic Target Generation (The Labels)
The architecture requires classifying destinations into exactly six specific travel styles: *Culture, Relaxation, Luxury, Family, Budget,* and *Adventure*. 

To establish a balanced ground truth across the 108 destinations, an ordered heuristic function was applied. The strict order of operations is critical to prevent broad categories from swallowing more nuanced ones:

1. **Culture (Top Priority):** Destinations classified as `Megacity` are tagged here first. This ensures massive, historically rich global hubs are correctly classified regardless of how cheap or expensive they are.
2. **Relaxation:** Captures destinations with warm, highly stable climates (`Temp_Variance` <= 12 and `Temp_YearAvg` >= 22).
3. **Luxury:** Captures the upper echelon of expensive cities utilizing a high `Tourist_Cost_Score` (>= 70).
4. **Family:** Utilizes the *Local Purchasing Power Index* (>= 65), which strongly correlates with highly developed infrastructure, healthcare, and baseline safety.
5. **Budget:** Placed lower in the pipeline to catch genuinely low-cost destinations (`Tourist_Cost_Score` <= 32) that did not trigger earlier, more specific biome rules.
6. **Adventure (Fallback):** Captures the remaining destinations, which predominantly feature extreme distinct seasons, remote locations, or mid-tier economic profiles.

By tuning the thresholds and intentionally ordering the pipeline, this methodology successfully eliminated class imbalance. The resulting target variable (`Travel_Style`) is highly distributed, with every class maintaining a healthy volume of 15 to 26 destinations to ensure unbiased model training.

## 🤖 3. Machine Learning Classification

The core intelligence of the agent relies on a multi-class classification model designed to map a set of numeric and categorical constraints (budget, weather, scale) into one of the six defined `Travel_Style` classes.

### 1. Leakage Prevention & Preprocessing
To ensure the model learns generalized travel patterns rather than memorizing specific locations, strict data leakage prevention was enforced. Geographic identifiers (`city`, `country`, `lat`, `lng`) were completely dropped from the feature space (`X`) prior to training.

To satisfy strict engineering standards, all preprocessing was encapsulated within a `scikit-learn` **Pipeline** utilizing a `ColumnTransformer`:
* **Numerical Features:** (e.g., temperatures, cost indices) transformed via `StandardScaler`.
* **Categorical Features:** (`City_Scale`) transformed via `OneHotEncoder`.
Because these steps live *inside* the pipeline, transformations occur independently on each fold during cross-validation, guaranteeing zero data leakage from the validation sets.

### 2. Model Comparison & K-Fold Cross Validation
To identify the strongest architecture, three distinct algorithms were evaluated using a **Stratified 5-Fold Cross-Validation** strategy. Because some travel styles are naturally rarer, models were evaluated strictly on **Macro F1** and **Accuracy** to ensure minority classes were treated equally to majority classes.

| Classifier | Architecture Type | CV Accuracy | CV Macro F1 |
| :--- | :--- | :--- | :--- |
| **Logistic Regression** | Linear Baseline | 0.7948 ± 0.1148 | 0.7716 ± 0.1183 |
| **Random Forest** | Bagged Ensemble | 0.8978 ± 0.0686 | 0.8864 ± 0.0748 |
| **HistGradient Boosting** | Gradient Boosting | **0.9169 ± 0.0602** | **0.9039 ± 0.0643** |

* **Why HistGradient Boosting?** Tabular data heavily favors tree-based models. Random Forest performed well, but HistGradient Boosting's iterative error-correction sequence allowed it to perfectly map the deterministic boundaries established during our label engineering phase, making it the clear winner.

### 3. Hyperparameter Tuning & Serialization
The winning HistGradient Boosting pipeline was fine-tuned using `GridSearchCV` (optimizing for `f1_macro` across 5 folds). The search space included learning rates, tree depth (`max_iter`), and `l2_regularization`. 
* **Tuned Results:** The optimal parameters (`learning_rate`: 0.05, `max_iter`: 150, `l2_regularization`: 0.0) pushed the final Cross-Validated Macro F1 to **0.9240**.

A permutation importance analysis confirmed the model relies most heavily on `City_Scale` and `Tourist_Cost_Score`—proving it logically groups destinations identically to human intuition. The final, tuned pipeline was serialized via `joblib` and is injected as a dependency singleton into the FastAPI backend during the application lifespan loop.