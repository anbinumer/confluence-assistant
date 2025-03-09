import os
import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
confluence_url = os.getenv("CONFLUENCE_URL")
confluence_username = os.getenv("CONFLUENCE_USERNAME")
confluence_api_key = os.getenv("CONFLUENCE_API_KEY")

# Space details
SPACE_KEY = "LT"

# API endpoints
content_url = f"{confluence_url}/wiki/rest/api/content"

print(f"Retrieving content from '{SPACE_KEY}' (Learning Technologies)...")

try:
    # Get pages from the space
    response = requests.get(
        f"{content_url}?spaceKey={SPACE_KEY}&limit=5&expand=body.storage",
        auth=(confluence_username, confluence_api_key)
    )
    
    if response.status_code == 200:
        data = response.json()
        pages = data.get('results', [])
        
        print(f"\nSuccessfully retrieved {len(pages)} pages!")
        
        for page in pages:
            title = page.get('title', 'Untitled')
            page_id = page.get('id', 'Unknown')
            
            # Extract text content from HTML
            html_content = page.get('body', {}).get('storage', {}).get('value', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()[:150]  # First 150 chars
            
            print(f"\n- {title} (ID: {page_id})")
            print(f"  Content preview: {text_content}...")
        
        print("\nConnection successful!")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"Error: {e}")