import numpy as np
import pandas as pd
from pathlib import Path
import os
import joblib
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from sklearn.base import clone
from sklearn.model_selection import cross_val_predict
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, recall_score,
    classification_report, confusion_matrix,
    roc_curve, precision_recall_curve, average_precision_score,
)
from sklearn.model_selection import (
    GridSearchCV, 
    StratifiedKFold, 
    cross_validate, 
    cross_val_predict
)
from sklearn.calibration import CalibrationDisplay

print('All libraries imported successfully.')

# 1. Load your clean dataset
SCRIPT_DIR = Path(__file__).parent.resolve()

PROJECT_ROOT = SCRIPT_DIR.parent.parent

CLEANED_DIR = PROJECT_ROOT / 'data' / 'cleaned'

df = pd.read_csv(CLEANED_DIR / 'smart_travel_dataset_cleaned.csv')
print(f'Raw shape: {df.shape}')

# 2. Prevent Data Leakage: Drop geographic identifiers
# If the model sees city names or coordinates, it memorizes instead of learning patterns.
columns_to_drop = ['city', 'country', 'lat', 'lng']
df_model = df.drop(columns=columns_to_drop).copy()

print(f'Working shape (no leakage columns): {df_model.shape}')
print(f'Features available for modeling: {list(df_model.columns)}')

# 3. Separate Features (X) and Target (y)
X = df_model.drop(columns=['Travel_Style'])
y = df_model['Travel_Style']

print(f'\nTarget distribution:\n{y.value_counts()}')

# 1. Identify feature types for the pipeline
categorical_cols = ['City_Scale']
# All other columns in X are numerical
numerical_cols = [col for col in X.columns if col not in categorical_cols]

print(f"Numerical features ({len(numerical_cols)}): {numerical_cols}")
print(f"Categorical features ({len(categorical_cols)}): {categorical_cols}")

# 2. Build the Preprocessor (The first step of our Scikit-Learn Pipeline)
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numerical_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols)
    ]
)

# 3. Setup Stratified K-Fold Cross Validation
# 5 splits means it will train on ~86 rows and test on ~22 rows, 5 separate times.
# We use a fixed random_state to satisfy the "Fix your seeds" requirement.
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print("\nPreprocessor and Cross-Validation strategy successfully defined!")

# 1. Define the three classifiers (Requirement: "Compare at least three classifiers")
# We use random_state=42 to fix the seeds (Requirement: "Fix your seeds")
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
    'Random Forest': RandomForestClassifier(random_state=42, class_weight='balanced'),
    'HistGradient Boosting': HistGradientBoostingClassifier(random_state=42)
}

experiment_logs = []

print("Starting 5-Fold Cross Validation...\n")

# 2. Run the K-Fold comparison
for name, clf in models.items():
    # Build the strict pipeline linking our preprocessor directly to the model
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', clf)
    ])
    
    # Evaluate using the exact metrics requested by the rubric
    scores = cross_validate(model_pipeline, X, y, cv=cv, 
                            scoring=['accuracy', 'f1_macro'])
    
    acc_mean = scores['test_accuracy'].mean()
    acc_std = scores['test_accuracy'].std()
    f1_mean = scores['test_f1_macro'].mean()
    f1_std = scores['test_f1_macro'].std()
    
    print(f"=== {name} ===")
    print(f"Accuracy: {acc_mean:.4f} ± {acc_std:.4f}")
    print(f"Macro F1: {f1_mean:.4f} ± {f1_std:.4f}\n")
    
    # Save the data for the CSV
    experiment_logs.append({
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'model': name,
        'params': 'default_baseline',
        'accuracy_mean': round(acc_mean, 4),
        'accuracy_std': round(acc_std, 4),
        'f1_macro_mean': round(f1_mean, 4),
        'f1_macro_std': round(f1_std, 4)
    })

# 3. Save to results.csv (Requirement: "Track every experiment in a results.csv")
os.makedirs(PROJECT_ROOT / 'data' / 'ml', exist_ok=True)
results_path = PROJECT_ROOT / 'data' / 'ml' / 'results.csv'
results_df = pd.DataFrame(experiment_logs)

# Append if exists, write new if it doesn't
if os.path.exists(results_path):
    results_df.to_csv(results_path, mode='a', index=False, header=False)
else:
    results_df.to_csv(results_path, index=False)

print(f"Baseline experiments logged to: {results_path}")

print("Generating per-class metrics for the winning model (HistGradient Boosting)...\n")

# 1. Rebuild the winning pipeline
winning_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', HistGradientBoostingClassifier(random_state=42))
])

# 2. Generate out-of-fold predictions for the entire dataset
# This ensures every prediction was made by a model that had NEVER seen that specific row before
y_pred_cv = cross_val_predict(winning_pipeline, X, y, cv=cv)

# 3. Print the detailed classification report
print("=== Cross-Validated Classification Report ===")
report = classification_report(y, y_pred_cv)
print(report)


print("Starting Hyperparameter Tuning for HistGradient Boosting...\n")

# 1. Define the search space
# We prefix with 'classifier__' because the model is inside our Scikit-Learn Pipeline
param_grid = {
    'classifier__learning_rate': [0.05, 0.1, 0.2],  # How fast the model learns
    'classifier__max_iter': [100, 150, 200],        # Number of trees
    'classifier__l2_regularization': [0.0, 0.5, 1.0] # Penalty to prevent overfitting
}

# 2. Setup the Grid Search
# We optimize for 'f1_macro' to stay consistent with our imbalance handling
grid_search = GridSearchCV(
    estimator=winning_pipeline, 
    param_grid=param_grid,
    cv=cv,                 # Our 5-fold cross validation strategy
    scoring='f1_macro',    
    n_jobs=-1,             # Use all available CPU cores
    verbose=1
)

# 3. Execute the search across the entire dataset
grid_search.fit(X, y)

print("\n=== Tuning Results ===")
print(f"Best Parameters: {grid_search.best_params_}")
print(f"Best Cross-Validated Macro F1: {grid_search.best_score_:.4f}\n")

# 4. Save the absolute best pipeline (Preprocessor + Tuned Classifier)
model_path = PROJECT_ROOT / 'data' / 'ml' / 'travel_style_classifier.joblib'
joblib.dump(grid_search.best_estimator_, model_path)

print(f"✅ Tuned model successfully saved to: {model_path}")
print("This is the exact file your FastAPI backend will load!")