import os
import requests
from bs4 import BeautifulSoup
import json
import time
import datetime
import pickle
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
confluence_url = os.getenv("CONFLUENCE_URL")
confluence_username = os.getenv("CONFLUENCE_USERNAME")
confluence_api_key = os.getenv("CONFLUENCE_API_KEY")

# Space details
SPACE_KEY = "LT"
OUTPUT_DIR = "confluence_data"
METADATA_FILE = f"{OUTPUT_DIR}/metadata.pickle"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# API endpoints
content_url = f"{confluence_url}/wiki/rest/api/content"

def load_metadata():
    """Load metadata from previous runs"""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'rb') as f:
            return pickle.load(f)
    return {'last_update': None, 'page_ids': set()}

def save_metadata(metadata):
    """Save metadata for future runs"""
    with open(METADATA_FILE, 'wb') as f:
        pickle.dump(metadata, f)

def get_all_pages(space_key):
    """Fetch all pages from a Confluence space"""
    all_pages = []
    start = 0
    limit = 25
    
    print(f"Fetching pages from space '{space_key}'...")
    
    while True:
        print(f"  Retrieving batch starting at {start}...")
        response = requests.get(
            f"{content_url}?spaceKey={space_key}&limit={limit}&start={start}&expand=body.storage,version",
            auth=(confluence_username, confluence_api_key)
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        results = data.get('results', [])
        all_pages.extend(results)
        
        print(f"  Retrieved {len(results)} pages in this batch")
        
        # Check if we've reached the end
        if len(results) < limit:
            break
            
        start += limit
        time.sleep(1)  # Be nice to the API
    
    return all_pages

def extract_text(html_content):
    """Extract clean text from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.extract()
    
    # Get text
    text = soup.get_text()
    
    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text

# Main execution
# Load metadata from previous run
metadata = load_metadata()
last_update = metadata.get('last_update')
known_page_ids = metadata.get('page_ids', set())

if last_update:
    print(f"Last update: {last_update}")
    print(f"Previously known pages: {len(known_page_ids)}")

# Get all pages
pages = get_all_pages(SPACE_KEY)
print(f"\nTotal pages retrieved: {len(pages)}")

# Track new and updated pages
current_page_ids = set()
new_or_updated = 0

# Process and save each page
for i, page in enumerate(pages):
    page_id = page.get('id', 'unknown')
    current_page_ids.add(page_id)
    
    # Skip if we've seen this page before and we're doing an incremental update
    if last_update and page_id in known_page_ids:
        # Check if the page has been updated since last run
        last_modified = page.get('version', {}).get('when')
        if last_modified and last_modified <= last_update:
            continue
    
    title = page.get('title', 'Untitled')
    html_content = page.get('body', {}).get('storage', {}).get('value', '')
    
    # Extract text content
    text_content = extract_text(html_content)
    
    # Create page data with metadata
    page_data = {
        'id': page_id,
        'title': title,
        'text': text_content,
        'url': f"{confluence_url}/wiki/spaces/{SPACE_KEY}/pages/{page_id}"
    }
    
    # Save to file
    with open(f"{OUTPUT_DIR}/{page_id}.json", 'w', encoding='utf-8') as f:
        json.dump(page_data, f, ensure_ascii=False, indent=2)
    
    new_or_updated += 1
    if i % 10 == 0:
        print(f"Processed {i+1}/{len(pages)} pages")

# Update metadata for next run
metadata['last_update'] = datetime.datetime.now().isoformat()
metadata['page_ids'] = current_page_ids
save_metadata(metadata)

print(f"\nProcessed {len(pages)} pages total")
print(f"New or updated pages: {new_or_updated}")
print(f"\nSuccessfully downloaded content to {OUTPUT_DIR}/")