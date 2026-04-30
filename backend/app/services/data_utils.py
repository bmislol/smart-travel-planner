import pandas as pd
from typing import List, Dict, Any

def load_and_chunk_csv(file_path: str) -> List[Dict[str, Any]]:
    """Loads the expanded dataset and prepares it for embedding."""
    df = pd.read_csv(file_path)
    chunks = []
    
    for _, row in df.iterrows():
        # Using your 'feature row' strategy for the grounding string
        content = (
            f"Destination: {row['city']}, {row['country']}\n"
            f"Vibe: {row['label']}\n"
            f"Features: {row['what_this_country_offers']}"
        )
        chunks.append({
            "text": content,
            "metadata": {
                "city": row["city"],
                "country": row["country"],
                "label": row["label"]
            }
        })
    return chunks