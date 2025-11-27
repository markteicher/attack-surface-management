import os
import json
import csv
import time
import logging
import requests

# --- Configuration ---
BASE_URL = "https://asm.cloud.tenable.com/api/1.0/"  # Tenable ASM base API URL
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1IjoyMjcxMCwidiI6MCwiYyI6MzAwNjIsImYiOmZhbHNlLCJhIjpudWxsfQ.c4wP75bggVzMdE8Mgehl7tm0WW4g6x2rNidFMAIIsbw"  # 🔐 Replace this with your actual Tenable API key

# List of ASM API endpoints to extract data from
ENDPOINTS = [
    "assets", "tags", "sources", "alerts", "subscriptions",
    "txt-records", "global", "logs", "inventory", "suggestions"
]

# HTTP headers including API key
HEADERS = {
    "accept": "application/json",
    "X-Api-Key": API_KEY
}

# Output directory and log file path
OUTPUT_DIR = os.getcwd()
LOG_FILE = os.path.join(OUTPUT_DIR, "tenable_asm_export.log")

# --- Logging setup ---
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Helper function to flatten nested JSON into a flat dictionary
def flatten_json(y):
    out = {}
    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], f"{name}{a}_")
        elif isinstance(x, list):
            for i, a in enumerate(x):
                flatten(a, f"{name}{i}_")
        else:
            out[name[:-1]] = x
    flatten(y)
    return out

# Write list of records to CSV file with flattened structure
def write_csv(endpoint, records):
    csv_file = os.path.join(OUTPUT_DIR, f"{endpoint}.csv")
    if not records:
        return
    # Get union of all field names from all records
    fieldnames = sorted(set().union(*(flatten_json(r).keys() for r in records)))
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in records:
            writer.writerow(flatten_json(row))

# Fetch records from a given endpoint and save to .json and .csv
def fetch_and_save(endpoint):
    url = f"{BASE_URL}{endpoint}"
    all_records = []
    offset = 0
    limit = 1000  # Use pagination if needed

    while True:
        # Perform the API call
        response = requests.request("GET", url, headers=HEADERS, params={"limit": limit, "offset": offset})
        if response.status_code != 200:
            logging.error(f"Failed to fetch {endpoint}: {response.status_code} {response.text}")
            break

        # Extract items list from response
        data = response.json()
        items = data.get("items", data.get("data", []))
        if not isinstance(items, list):
            items = [items]

        all_records.extend(items)

        # Exit loop if less than one full page returned
        if len(items) < limit:
            break

        offset += limit
        time.sleep(1.1)  # Respect API rate limits

    # Write raw JSON output
    json_file = os.path.join(OUTPUT_DIR, f"{endpoint}.json")
    with open(json_file, "w", encoding="utf-8") as jf:
        json.dump(all_records, jf, indent=2)

    # Write CSV output
    write_csv(endpoint, all_records)

    logging.info(f"{endpoint}: {len(all_records)} records retrieved and written.")
    print(f"[✔] {endpoint}: {len(all_records)} records")

# Main function to iterate over all endpoints
def main():
    logging.info("=== Tenable ASM Export Started ===")
    start_time = time.time()

    # Fetch and save each endpoint
    for ep in ENDPOINTS:
        try:
            fetch_and_save(ep)
        except Exception as e:
            logging.exception(f"Error while processing {ep}: {e}")

    # Log and print total duration
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    logging.info(f"Export complete in {duration} seconds.")
    print(f"All data exported in {duration} seconds.")

# Entry point
if __name__ == "__main__":
    main()
