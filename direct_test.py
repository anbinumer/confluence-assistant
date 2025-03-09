import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
confluence_url = os.getenv("CONFLUENCE_URL")
confluence_username = os.getenv("CONFLUENCE_USERNAME")
confluence_api_key = os.getenv("CONFLUENCE_API_KEY")

# Construct proper API URL
api_url = f"{confluence_url}/wiki/rest/api/space"
if not confluence_url.startswith("https://"):
    api_url = f"https://{confluence_url}/wiki/rest/api/space"

# Print connection info
print(f"Testing connection to: {api_url}")
print(f"Using username: {confluence_username}")

# Make direct API request
try:
    # Get all spaces (paginated)
    all_spaces = []
    start = 0
    limit = 100
    
    while True:
        response = requests.get(
            f"{api_url}?start={start}&limit={limit}",
            auth=(confluence_username, confluence_api_key)
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
            
        spaces_page = response.json()
        results = spaces_page.get('results', [])
        all_spaces.extend(results)
        
        # Check if we've reached the end
        if len(results) < limit:
            break
            
        start += limit
    
    # Search for Learning Technologies space
    print(f"\nTotal spaces found: {len(all_spaces)}")
    print("\nSearching for 'Learning Technologies' space...")
    
    lt_spaces = []
    for space in all_spaces:
        name = space.get('name', '')
        key = space.get('key', '')
        
        if 'learning' in name.lower() or 'technology' in name.lower() or key == 'LT':
            lt_spaces.append(space)
    
    # Print potential matches
    if lt_spaces:
        print("\nPotential Learning Technologies spaces:")
        for space in lt_spaces:
            print(f"- {space.get('name')} (Key: {space.get('key')})")
    else:
        print("\nNo spaces found matching 'Learning Technologies'")
        
    # Also check if LT space exists specifically
    lt_space = next((s for s in all_spaces if s.get('key') == 'LT'), None)
    if lt_space:
        print(f"\nSpace with key 'LT' exists: {lt_space.get('name')}")
    else:
        print("\nNo space with key 'LT' found")
    
except Exception as e:
    print(f"Error: {e}")