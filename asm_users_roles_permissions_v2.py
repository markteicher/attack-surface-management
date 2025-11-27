
import requests
import csv

# === Configuration ===
BASE_URL = "https://asm.cloud.tenable.com/api/1.0"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1IjoyMjcxMCwidiI6MCwiYyI6MzAwNjIsImYiOmZhbHNlLCJhIjpudWxsfQ.c4wP75bggVzMdE8Mgehl7tm0WW4g6x2rNidFMAIIsbw"  # Replace with your actual API key

HEADERS = {
    "Accept": "application/json",
    "Authorization": API_KEY
}

def fetch_all_users():
    all_users = []
    page = 1
    while True:
        url = f"{BASE_URL}/users?page={page}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        users = data.get("users", [])
        if not users:
            break
        all_users.extend(users)
        print(f"[+] Page {page}: Retrieved {len(users)} users")
        page += 1
    return all_users

def save_users_csv(users):
    with open("asm_users.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["user", "email", "role"])
        writer.writeheader()
        for u in users:
            writer.writerow({
                "user": u.get("user", ""),
                "email": u.get("email", ""),
                "role": u.get("role", "")
            })

def build_permissions_matrix(users):
    role_permissions = {}
    for user in users:
        role = user.get("role")
        perms = user.get("permissions", [])
        if role not in role_permissions:
            role_permissions[role] = set(perms)
        else:
            role_permissions[role].update(perms)

    all_perms = sorted({p for perms in role_permissions.values() for p in perms})
    matrix_rows = []
    for role, perms in role_permissions.items():
        row = {"role": role}
        for perm in all_perms:
            row[perm] = "✅" if perm in perms else "❌"
        matrix_rows.append(row)

    fieldnames = ["role"] + all_perms
    with open("asm_role_permissions.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matrix_rows)

if __name__ == "__main__":
    try:
        users = fetch_all_users()
        print(f"[✓] Total users retrieved: {len(users)}")
        save_users_csv(users)
        print("[✓] asm_users.csv written")
        build_permissions_matrix(users)
        print("[✓] asm_role_permissions.csv written")
    except Exception as e:
        print(f"[!] Error: {e}")
