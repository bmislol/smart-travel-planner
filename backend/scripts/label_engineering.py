import os
import sys
import json
import asyncio
import pandas as pd
from pathlib import Path
from anthropic import AsyncAnthropic

# --- DYNAMIC PATHING & IMPORTS ---
# Resolve the absolute path to the backend directory
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Add backend directory to sys.path so we can import your FastAPI app modules
sys.path.append(str(BACKEND_DIR))

# Import your single source of truth for config!
from app.core.config import settings

# Initialize Claude Client using your pydantic settings
client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# Directory Setup
CLEANED_DIR = PROJECT_ROOT / 'data' / 'cleaned'
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'

async def generate_trip_profiles(row):
    """
    Sends city data to Claude and asks for 8 unique trip profiles in JSON format.
    """
    prompt = f"""
    You are an expert travel planner. I am building a machine learning dataset.
    Look at this destination and its cost metrics:
    - City: {row['city']}, {row['country']}
    - Cost of Living Index: {row['Cost of Living Index']}
    - Tourist Cost Score: {row['Tourist_Cost_Score']}
    - City Scale: {row['City_Scale']}

    Generate exactly 8 unique trip profiles for this city. 
    For each profile, provide:
    1. "Primary_Activity": A specific, real-world activity, landmark, or attraction in THIS specific city.
    2. "Trip_Pace": Choose either "Fast", "Moderate", or "Relaxed".
    3. "Travel_Style": You MUST classify the profile into exactly ONE of these strict labels: [Adventure, Relaxation, Culture, Budget, Luxury, Family]. Match the label logically to the activity.

    Return ONLY a raw JSON array of objects. Do not include markdown formatting or backticks.
    Example format:
    [
      {{"Primary_Activity": "...", "Trip_Pace": "...", "Travel_Style": "..."}}
    ]
    """

    try:
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_text = response.content[0].text.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.startswith("```"): raw_text = raw_text[3:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
            
        return json.loads(raw_text.strip())
        
    except Exception as e:
        print(f"Error generating profiles for {row['city']}: {e}")
        return None

async def main():
    print("Loading raw dataset...")
    df = pd.read_csv(RAW_DIR / 'smart_travel_dataset.csv') 
    
    # Feature Engineering
    df['Tourist_Cost_Score'] = (df['Cost of Living Index'] + df['Restaurant Price Index']) / 2
    df['Dining_Out_Premium'] = df['Restaurant Price Index'] / df['Groceries Index']

    bins = [0, 3000000, 10000000, 100000000]
    labels = ['Mid/Small', 'Large', 'Megacity']
    df['City_Scale'] = pd.cut(df['population'], bins=bins, labels=labels)

    # Aggressive Cleanup
    cols_to_drop = [
        'Rent Index', 'Cost of Living Plus Rent Index', 'population',
        'Temp_DecJanFeb', 'Temp_MarAprMay', 'Temp_JunJulAug', 'Temp_SepOctNov', 'Temp_YearAvg'
    ]
    cols_to_drop = [c for c in cols_to_drop if c in df.columns]
    df = df.drop(columns=cols_to_drop)

    df.to_csv(CLEANED_DIR / 'smart_travel_dataset_cleaned.csv', index=False)
    print("Dataset trimmed and base features saved.")

    # The Main Generation Loop
    expanded_rows = []
    print("\nStarting generation loop...")

    for index, row in df.iterrows():
        if index % 10 == 0:
            print(f"Processing city {index + 1} of {len(df)}...")
            
        profiles = await generate_trip_profiles(row)
        
        if profiles:
            for profile in profiles:
                new_row = row.to_dict()
                new_row.update(profile)
                expanded_rows.append(new_row)
        
        await asyncio.sleep(0.5)

    print(f"\nFinished! Generated a total of {len(expanded_rows)} trip profiles.")

    # Assembly & Export
    augmented_df = pd.DataFrame(expanded_rows)
    final_columns = [
        'city', 'country', 'lat', 'lng', 
        'Primary_Activity', 'Trip_Pace', 
        'Cost of Living Index', 'Tourist_Cost_Score', 'Dining_Out_Premium', 'City_Scale',
        'Travel_Style' 
    ]
    
    augmented_df = augmented_df[final_columns]
    output_path = CLEANED_DIR / 'smart_travel_dataset_augmented.csv'
    augmented_df.to_csv(output_path, index=False)
    print(f"Successfully saved augmented dataset to {output_path}")

# This tells Python to run the async main function when the script is executed
if __name__ == "__main__":
    asyncio.run(main())