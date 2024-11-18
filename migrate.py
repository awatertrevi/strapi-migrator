import requests 
import os
from urllib.parse import urljoin
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
STRAPI_3_BASE_URL = os.getenv("STRAPI_3_BASE_URL")
STRAPI_4_BASE_URL = os.getenv("STRAPI_4_BASE_URL")
STRAPI_4_API_KEY = os.getenv("STRAPI_4_API_KEY")
STRAPI_3_EMAIL = os.getenv("STRAPI_3_EMAIL")
STRAPI_3_PASSWORD = os.getenv("STRAPI_3_PASSWORD")
STRAPI_3_MODEL = os.getenv("STRAPI_3_MODEL")
STRAPI_4_MODEL = os.getenv("STRAPI_4_MODEL")
RELATIONSHIP_FIELDS = os.getenv("RELATIONSHIP_FIELDS", "").split(",")  # Convert to list
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

# Headers for Strapi 4
HEADERS_4 = {"Authorization": f"Bearer {STRAPI_4_API_KEY}"}

def get_strapi_3_token():
    """Fetch JWT token for Strapi 3."""
    response = requests.post(
        f"{STRAPI_3_BASE_URL}/admin/login",
        json={"email": STRAPI_3_EMAIL, "password": STRAPI_3_PASSWORD},
    )
    response.raise_for_status()
    return response.json()["data"]["token"]


def download_media(media_url):
    """Download media file from a URL."""
    response = requests.get(media_url, stream=True)
    response.raise_for_status()
    file_name = media_url.split("/")[-1]
    with open(file_name, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    return file_name


def upload_media_to_strapi_4(file_path):
    """Upload a media file to Strapi 4."""
    with open(file_path, "rb") as file:
        response = requests.post(
            f"{STRAPI_4_BASE_URL}/api/upload",
            headers=HEADERS_4,
            files={"files": file},
        )
    response.raise_for_status()
    os.remove(file_path)  # Clean up the local file after upload
    return response.json()[0]  # Return uploaded media metadata


def map_relationships(entry):
    """
    Map relationships for entries and components to Strapi 4's `connect` format.
    """
    for field, value in entry.items():
        if field not in RELATIONSHIP_FIELDS:
            continue

        if isinstance(value, dict) and "id" in value:  # Single relationship
            related_model = field  # Assuming the field name is the model name
            related_id = fetch_related_id_in_strapi_4(related_model, value["id"])
            entry[field] = {"connect": [{"id": related_id}]}
        elif isinstance(value, list) and all("id" in v for v in value):  # Multiple relationships
            related_model = field  # Assuming the field name is the model name
            related_ids = [
                fetch_related_id_in_strapi_4(related_model, v["id"]) for v in value
            ]
            entry[field] = {"connect": [{"id": rid} for rid in related_ids]}
    return entry



def fetch_related_id_in_strapi_4(model_name, old_id):
    """Fetch the corresponding ID in Strapi 4 for a related entity."""
    response = requests.get(
        f"{STRAPI_4_BASE_URL}/api/{model_name}s",
        headers=HEADERS_4,
        params={"filters[old_id][$eq]": old_id},  # Assuming old_id is stored
    )
    response.raise_for_status()
    data = response.json()["data"]
    if data:
        return data[0]["id"]  # Return the first match
    else:
        raise ValueError(f"Related entity with old_id {old_id} not found in Strapi 4.")
    

def handle_components(entry, token):
    """
    Recursively process components, handling nested media and relationships.
    """
    for field, value in entry.items():
        # Check if the field is a component array
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            # Process each component
            for component in value:
                # Handle media fields in the component
                handle_media_fields(component)
                # Map relationships in the component
                map_relationships(component)
        elif isinstance(value, dict):  # Single component or nested structure
            handle_media_fields(value)
            map_relationships(value)

    return entry


def handle_media_fields(entry):
    """Handle media fields for both entry and component-level media."""
    for field, value in entry.items():
        if isinstance(value, dict) and value.get("url"):  # Single media
            media_url = urljoin(STRAPI_3_BASE_URL, value["url"])
            file_path = download_media(media_url)
            uploaded_media = upload_media_to_strapi_4(file_path)
            entry[field] = uploaded_media["id"]

        elif isinstance(value, list) and all(isinstance(item, dict) and item.get("url") for item in value):  # Multiple media
            media_ids = []
            for media_item in value:
                media_url = urljoin(STRAPI_3_BASE_URL, media_item["url"])
                file_path = download_media(media_url)
                uploaded_media = upload_media_to_strapi_4(file_path)
                media_ids.append(uploaded_media["id"])
            entry[field] = media_ids
    return entry


def fetch_entries_from_strapi_3(model_name, token):
    """Fetch all entries from Strapi 3."""
    headers = {"Authorization": f"Bearer {token}"}
    entries = []
    page = 1
    while True:
        response = requests.get(
            f"{STRAPI_3_BASE_URL}/{model_name}",
            headers=headers,
            params={"_limit": BATCH_SIZE, "_start": (page - 1) * BATCH_SIZE},
        )

        print ("Fetching page: " + str(page))

        response.raise_for_status()
        data = response.json()
        if not data:
            break
        entries.extend(data)
        page += 1
    return entries


def create_entries_in_strapi_4(model_name, entries):
    """Create entries in Strapi 4, processing components."""
    for entry in entries:
        # Store the old ID for reference
        entry["old_id"] = entry["id"]

        # Remove Strapi 3-specific metadata
        entry.pop("id", None)
        entry.pop("created_at", None)
        entry.pop("updated_at", None)

        # Handle media and relationships for the main entry
        entry = handle_media_fields(entry)
        entry = map_relationships(entry)

        # Handle components (like meta_tags)
        entry = handle_components(entry, HEADERS_4)

        response = requests.post(
            f"{STRAPI_4_BASE_URL}/api/{model_name}",
            headers=HEADERS_4,
            json={"data": entry},
        )
        if response.status_code != 200 and response.status_code != 201:
            print(f"Failed to create entry: {entry}")
            print(f"Response: {response.text}")
        else:
            print(f"Successfully migrated entry: {entry}")

def main():
    print(f"Authenticating with Strapi 3...")
    token = get_strapi_3_token()
    print(f"Fetching entries for model '{STRAPI_3_MODEL}' from Strapi 3...")
    entries = fetch_entries_from_strapi_3(STRAPI_3_MODEL, token)
    print(f"Fetched {len(entries)} entries.")

    print(f"Creating entries in Strapi 4...")
    create_entries_in_strapi_4(STRAPI_4_MODEL, entries)
    print("Migration complete.")

if __name__ == "__main__":
    main()