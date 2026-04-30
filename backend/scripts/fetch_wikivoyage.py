import asyncio
import json
import os
import pandas as pd
import httpx
from typing import List, Dict

# Paths
CSV_PATH = os.path.join(os.path.dirname(__file__), "../../data/cleaned/smart_travel_dataset_augmented.csv")
OUTPUT_JSON_PATH = os.path.join(os.path.dirname(__file__), "../../data/raw/travel_guides.json")

async def fetch_wikivoyage_extract(client: httpx.AsyncClient, city: str) -> str:
    """
    Fetches the plain-text content of a Wikivoyage article for a given city.
    """
    url = "https://en.wikivoyage.org/w/api.php"
    params = {
        "action": "query",
        "prop": "extracts",
        "titles": city,
        "explaintext": 1, # Return plain text instead of HTML
        "redirects": 1,   # Automatically handle redirects (e.g., "NYC" -> "New York City")
        "format": "json"
    }
    
    try:
        response = await client.get(url, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        
        # The API returns pages in a dictionary keyed by page ID. We just grab the first one.
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_info in pages.items():
            if page_id == "-1":
                print(f"  [!] Wikivoyage page not found for: {city}")
                return ""
            return page_info.get("extract", "")
            
    except Exception as e:
        print(f"  [!] Error fetching data for {city}: {e}")
        return ""

async def generate_rag_data():
    print(f"Reading dataset from {CSV_PATH}...")
    if not os.path.exists(CSV_PATH):
        print("Error: CSV file not found!")
        return

    # 1. Read the CSV and find the top 20 unique destinations
    df = pd.read_csv(CSV_PATH)
    
    # Get the 20 most frequent cities
    top_cities = df['city'].value_counts().head(20).index.tolist()
    print(f"Top 20 cities identified: {', '.join(top_cities)}\n")

    rag_dataset: List[Dict] = []

    # 2. Setup Async HTTP Client with a Custom User-Agent
    # Wikimedia requires a descriptive User-Agent or it throws a 403 Forbidden
    headers = {
        "User-Agent": "SmartTravelPlannerBot/1.0 (Charbel Ghanem; Educational Project)"
    }
    
    async with httpx.AsyncClient(headers=headers) as client:
        for city in top_cities:
            print(f"Fetching guide for {city}...")
            
            # Find the most common 'Travel_Style' associated with this city in the CSV
            most_common_style = df[df['city'] == city]['Travel_Style'].mode()[0]
            
            # Fetch the text from Wikivoyage
            description = await fetch_wikivoyage_extract(client, city)
            
            if description:
                # Cap the text at the first ~5000 characters to prevent DB bloat
                description = description[:5000].strip()
                
                rag_dataset.append({
                    "name": city,
                    "travel_style": most_common_style,
                    "description": description
                })
                print(f"  -> Success! Gathered {len(description)} characters.")
            
            # Small pause to be polite to the Wikipedia API
            await asyncio.sleep(0.5)

    # 3. Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(rag_dataset, f, indent=4, ensure_ascii=False)
        
    print(f"\nSaved {len(rag_dataset)} destination guides to {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    asyncio.run(generate_rag_data())