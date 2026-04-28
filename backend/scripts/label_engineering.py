import numpy as np
import pandas as pd
from pathlib import Path

print("All libraries imported successfully.")

SCRIPT_DIR = Path(__file__).parent.resolve()

PROJECT_ROOT = SCRIPT_DIR.parent.parent

CLEANED_DIR = PROJECT_ROOT / 'data' / 'cleaned'
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'

CLEANED_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)



# Load the raw merged dataset
df = pd.read_csv(RAW_DIR / 'smart_travel_dataset.csv') 

# Quick sanity check: Verify we have exactly 108 rows and check the exact column names
print(f"Dataset shape: {df.shape}")
print("\nColumns available for feature engineering:")
print(df.columns.tolist())

# Feature Engineering

# 1. Climate Features
# Define the seasonal columns to find the max and min temperatures across the year
seasonal_cols = ['Temp_DecJanFeb', 'Temp_MarAprMay', 'Temp_JunJulAug', 'Temp_SepOctNov']
df['Temp_Variance'] = df[seasonal_cols].max(axis=1) - df[seasonal_cols].min(axis=1)

# 2. Economic Features
# Average the general cost of living with restaurant prices (ignoring rent)
df['Tourist_Cost_Score'] = (df['Cost of Living Index'] + df['Restaurant Price Index']) / 2

# Ratio of eating out vs buying groceries. 
df['Dining_Out_Premium'] = df['Restaurant Price Index'] / df['Groceries Index']

# 3. Demographic Features
# Convert raw population into categorical bins
# Bins: 0 to 3M (Mid/Small), 3M to 10M (Large), 10M to 100M (Megacity)
bins = [0, 3000000, 10000000, 100000000]
labels = ['Mid/Small', 'Large', 'Megacity']
df['City_Scale'] = pd.cut(df['population'], bins=bins, labels=labels)

# 4. Cleanup
# Drop the columns that are just noise for tourists
cols_to_drop = ['Rent Index', 'Cost of Living Plus Rent Index', 'population']
df = df.drop(columns=cols_to_drop)

# Verify the changes
print("Shape after engineering:", df.shape)

# Auto-Labeling the Target Variable (Travel_Style) - TWEAKED

def assign_travel_style(row):
    # 1. Culture (Moved to Top): Catch massive hubs first so they don't get swallowed by Budget/Luxury
    if row['City_Scale'] == 'Megacity':
        return 'Culture'
        
    # 2. Relaxation (Broadened): Looser climate rules for warm, relatively stable destinations
    elif row['Temp_Variance'] <= 12 and row['Temp_YearAvg'] >= 22:
        return 'Relaxation'
        
    # 3. Luxury (Slightly Lowered): Capture upper-tier expensive cities
    elif row['Tourist_Cost_Score'] >= 70:
        return 'Luxury'
        
    # 4. Family (Slightly Lowered): High purchasing power (safety/infrastructure)
    elif row['Local Purchasing Power Index'] >= 65:
        return 'Family'
        
    # 5. Budget (Shrunken and Moved Down): Only catches genuinely low-cost places
    elif row['Tourist_Cost_Score'] <= 32:
        return 'Budget'
        
    # 6. Adventure: Fallback for everything else (usually places with distinct seasons or mid-tier costs)
    else:
        return 'Adventure'

# Apply the updated function
df['Travel_Style'] = df.apply(assign_travel_style, axis=1)

# Check the new distribution
print("NEW Class Distribution:\n")
print(df['Travel_Style'].value_counts())
print(f"\nTotal Labeled: {df['Travel_Style'].count()} / 108")

# Final Validation

print("--- Data Info ---")
df.info()

print("\n--- Missing Values Check ---")
# This will sum up any nulls. We want to see all zeros.
missing_values = df.isnull().sum()
print(missing_values[missing_values > 0] if missing_values.any() else "Perfect! No missing values found.")

print("\n--- Quick Look at Data Types ---")
# Ensuring our indices and temperatures are floats/ints, not strings
print(df.dtypes)

# Save to the data directory
df.to_csv(CLEANED_DIR / 'smart_travel_dataset_cleaned.csv', index=False)
print("Dataset Smart Travel Cleaned saved successfully!")