import numpy as np
import pandas as pd
from pathlib import Path

print("All libraries imported successfully.")

SCRIPT_DIR = Path(__file__).parent.resolve()

PROJECT_ROOT = SCRIPT_DIR.parent.parent

BROKEN_DIR = PROJECT_ROOT / 'data' / 'broken'
CLEANED_DIR = PROJECT_ROOT / 'data' / 'cleaned'
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'

CLEANED_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Load the Three Core Datasets
cities_df = pd.read_csv(BROKEN_DIR / 'worldcities.csv')
cost_df = pd.read_csv(BROKEN_DIR / 'costofliving.csv') 
weather_df = pd.read_csv(BROKEN_DIR / 'average_weather.csv') 

print("--- DATASET SHAPES ---")
print(f"1. World Cities: {cities_df.shape}")
print(f"2. Cost of Living: {cost_df.shape}")
print(f"3. Weather Data: {weather_df.shape}")

# Clean the Cost of Living Dataset

# 1. Drop the completely null 'Rank' column
clean_cost_df = cost_df.drop(columns=['Rank']).copy()

# 2. Split "City, Country" into two separate columns
# We use rsplit(n=1) to split only on the last comma, protecting cities with commas in their names
clean_cost_df[['city', 'country']] = clean_cost_df['City'].str.rsplit(', ', n=1, expand=True)

# 3. Clean up the remnants
clean_cost_df.drop(columns=['City'], inplace=True)
clean_cost_df['city'] = clean_cost_df['city'].str.strip()
clean_cost_df['country'] = clean_cost_df['country'].str.strip()

print("--- CLEANED COST OF LIVING ---")
print(f"Shape: {clean_cost_df.shape}")

clean_cost_df.to_csv(CLEANED_DIR / 'clean_cost_df.csv', index=False)
print("Dataset Clean Cost saved successfully!")

# Clean the Weather Data

# 1. Drop the useless Reference column
clean_weather_df = weather_df.drop(columns=['Ref.']).copy()

# 2. Define the columns containing the messy strings
temp_cols = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Year']

# 3. Split the string, fix the fake minus sign, and convert to float
for col in temp_cols:
    clean_weather_df[col] = (
        clean_weather_df[col]
        .astype(str)
        .str.split('\n').str[0]       # Keep only the Celsius part
        .str.replace('−', '-')        # Replace typographic minus with standard keyboard minus
        .str.strip()                  # Remove any lingering spaces
        .astype(float)                # Convert safely to float!
    )

print("--- CLEANED WEATHER DATA ---")
print(f"Shape: {clean_weather_df.shape}")

# Checking the datatypes to prove the conversion worked
print("\n--- DATA TYPES ---")
print(clean_weather_df[['Jul', 'Year']].dtypes)

clean_weather_df.to_csv(CLEANED_DIR / 'clean_weather_df.csv', index=False)
print("Dataset Clean Weather saved successfully!")

# Extract the Top 250 Target Destinations

# 1. Drop rows without population data and sort from largest to smallest
top_cities_df = cities_df.dropna(subset=['population']).sort_values(by='population', ascending=False)

# 2. Slice off exactly the top 250 cities
target_destinations = top_cities_df.head(600).copy()

# 3. Keep only the columns we actually need for the project
target_destinations = target_destinations[['city_ascii', 'country', 'lat', 'lng', 'population']]

# 4. Rename 'city_ascii' to 'city' to create a perfect match key for our other datasets
target_destinations.rename(columns={'city_ascii': 'city'}, inplace=True)

print("--- TARGET DESTINATIONS (THE ANCHOR) ---")
print(f"Shape: {target_destinations.shape}")

target_destinations.to_csv(CLEANED_DIR / 'target_destinations.csv', index=False)
print("Dataset Clean Target Destinations saved successfully!")

# The Intersection Test (Dry Run)

# 1. Create a standardized, lowercase matching column for all three dataframes
target_destinations['match_name'] = target_destinations['city'].str.lower()
clean_cost_df['match_name'] = clean_cost_df['city'].str.lower()
clean_weather_df['match_name'] = clean_weather_df['City'].str.lower()

# 2. Extract those columns into Python Sets
cities_set = set(target_destinations['match_name'])
cost_set = set(clean_cost_df['match_name'])
weather_set = set(clean_weather_df['match_name'])

# 3. The Intersection: Find the cities that exist in ALL THREE sets
survivors = cities_set & cost_set & weather_set

# 4. The Reveal
print("========== THE DRY RUN RESULTS ==========")
print(f"Target Cities Started With: {len(cities_set)}")
print(f"Cities Available in Cost Data: {len(cost_set)}")
print(f"Cities Available in Weather Data: {len(weather_set)}")
print("-" * 41)
print(f"🏆 TOTAL SURVIVORS (Perfect Match): {len(survivors)} 🏆")
print("-" * 41)

# Print a few of the winning cities just to verify they look correct
print(f"\nSample of surviving cities: {list(survivors)[:10]}")

# The Grand Merge (Execution)

# 1. Inner join target cities with the cost data 
# We drop 'city' and 'country' from the cost data before merging to prevent duplicate columns
master_df = target_destinations.merge(
    clean_cost_df.drop(columns=['city', 'country']), 
    on='match_name', 
    how='inner'
)

# 2. Inner join the result with the weather data
# We only need the July and Year averages for our feature engineering
# First, calculate our seasonal averages on the weather dataframe
clean_weather_df['Temp_DecJanFeb'] = clean_weather_df[['Dec', 'Jan', 'Feb']].mean(axis=1).round(1)
clean_weather_df['Temp_MarAprMay'] = clean_weather_df[['Mar', 'Apr', 'May']].mean(axis=1).round(1)
clean_weather_df['Temp_JunJulAug'] = clean_weather_df[['Jun', 'Jul', 'Aug']].mean(axis=1).round(1)
clean_weather_df['Temp_SepOctNov'] = clean_weather_df[['Sep', 'Oct', 'Nov']].mean(axis=1).round(1)

# Now, merge only these new engineered columns (plus the Year average)
master_df = master_df.merge(
    clean_weather_df[['match_name', 'Temp_DecJanFeb', 'Temp_MarAprMay', 'Temp_JunJulAug', 'Temp_SepOctNov', 'Year']].rename(columns={'Year': 'Temp_YearAvg'}),
    on='match_name',
    how='inner'
)

# 3. Final Cleanup
# Drop the temporary lowercase matching column and reset the index so it counts cleanly from 0 to 102
master_df.drop(columns=['match_name'], inplace=True)
master_df.reset_index(drop=True, inplace=True)

print("========== FINAL DATASET COMPLETED ==========")
print(f"Final Shape: {master_df.shape}")

# Save to the data directory
master_df.to_csv(RAW_DIR / 'smart_travel_dataset.csv', index=False)
print("Dataset Smart Travel saved successfully!")