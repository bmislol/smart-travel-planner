# Smart Travel Planner

## 1. Data Architecture & Feature Engineering

### The Dataset
To build a defensible machine learning pipeline, this project utilizes a custom-compiled dataset engineered from three separate Kaggle sources:
1. **World Cities Database:** Served as the geographic anchor to ensure standardized city names, countries, and coordinates.
2. **World Famous Places:** Aggregated to provide cultural and historical metrics.
3. **Tourist Destinations:** Provided baseline metrics for tourist popularity and costs.

### Labeling Rules & Feature Justification
To classify destinations into specific travel styles (Adventure, Relaxation, Culture, Budget, Luxury, Family), the following raw features were engineered and utilized:

* **[Feature 1 - e.g., Cost of Living Index]:** Utilized to mathematically distinguish "Budget" vs. "Luxury" classifications.
* **[Feature 2 - e.g., Annual Visitors]:** Used to filter for the user's "not too touristy" constraint and identify high-traffic generic destinations.
* **[Feature 3 - e.g., UNESCO Site Count]:** Grouped by city from attraction-level data to provide concrete evidence for "Culture" labels.

*(More features to be documented as data cleaning progresses)*