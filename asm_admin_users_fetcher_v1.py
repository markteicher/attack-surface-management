
import time
import requests
import json
import csv

# Secure token should be stored in an environment variable or external config
API_TOKEN = "REPLACE_WITH_YOUR_TOKEN"
API_URL = "https://asm.cloud.tenable.com/api/1.0/admin/users"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def fetch_users_data():
    for attempt in range(3):
        try:
            print(f"Attempt {attempt + 1}: Fetching user data...")
            response = requests.get(API_URL, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            time.sleep(3)
    print("Failed to fetch data after 3 attempts.")
    return None

def flatten_user_record(user):
    flat = {
        "id": user.get("id"),
        "authid": user.get("authid"),
        "email": user.get("email"),
        "access_level": user.get("access_level"),
        "created_at": user.get("created_at"),
        "mfa": user.get("mfa"),
        "user_inventories_limit": user.get("user_inventories_limit"),
        "workspace": user.get("workspace"),
    }
    # Flatten company names
    if "companies" in user:
        flat["companies"] = "; ".join([c["name"] for c in user["companies"] if "name" in c])
    return flat

def save_to_csv(data, output_file="asm_admin_users.csv"):
    if not data or "list" not in data:
        print("No valid data to write.")
        return

    users = data["list"]
    flat_users = [flatten_user_record(user) for user in users]

    fieldnames = list(flat_users[0].keys())
    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_users)

    print(f"✔️ {len(flat_users)} users written to {os.path.abspath(output_file)}")

if __name__ == "__main__":
    data = fetch_users_data()
    save_to_csv(data)
