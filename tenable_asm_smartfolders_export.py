
import requests
import csv
import logging
from datetime import datetime
from tqdm import tqdm
import os

# === CONFIG ===
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1IjoyMjcxMCwidiI6MCwiYyI6MzAwNjIsImYiOmZhbHNlLCJhIjpudWxsfQ.c4wP75bggVzMdE8Mgehl7tm0WW4g6x2rNidFMAIIsbw"
OUTPUT_CSV = "smartfolders.csv"
LOG_FILE = "smartfolders_export.log"
API_URL = "https://asm.cloud.tenable.com/api/1.0/smartfolders"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"{API_KEY}"
}

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# === FETCH SMARTFOLDERS ===
def fetch_smartfolders():
    logging.info("Fetching smartfolders from Tenable ASM...")
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        return response.json()  # returns a list, not a dict
    except Exception as e:
        logging.error(f"Error fetching smartfolders: {e}")
        return []

# === FLATTEN EACH SMARTFOLDER ===
def flatten_record(record):
    flat = record.copy()

    # Normalize timestamp
    for field in ['created_at', 'updated_at', 'processed_at']:
        if field in flat and flat[field]:
            try:
                dt = datetime.fromisoformat(flat[field].replace("Z", ""))
                flat[field] = dt.strftime('%Y-%m-%d-%H:%M:%S')
            except Exception:
                flat[field] = flat[field]

    # Flatten filters (if any)
    filters = flat.get("filters", [])
    if isinstance(filters, list):
        flat["filters_normalized"] = "; ".join(
            [f"{f.get('column')} {f.get('type')} {f.get('value')}" for f in filters]
        )
    else:
        flat["filters_normalized"] = "N/A"

    return flat

# === EXPORT TO CSV ===
def export_csv(records, filename):
    if not records:
        logging.warning("No records to export.")
        return

    keys = sorted(set().union(*(r.keys() for r in records)))
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    logging.info(f"Wrote {len(records)} records to {filename}")

# === MAIN ===
def main():
    logging.info("=== Tenable ASM Smartfolders Export Script ===")
    start = datetime.now()

    raw = fetch_smartfolders()
    flattened = []

    for record in tqdm(raw, desc="Processing records"):
        flattened.append(flatten_record(record))

    export_csv(flattened, OUTPUT_CSV)

    end = datetime.now()
    duration = (end - start).total_seconds()
    logging.info(f"Completed in {duration:.2f} seconds.")

if __name__ == "__main__":
    main()
