import os
from llama_index.readers.confluence import ConfluenceReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
confluence_url = os.getenv("CONFLUENCE_URL")
confluence_username = os.getenv("CONFLUENCE_USERNAME")
confluence_api_key = os.getenv("CONFLUENCE_API_KEY")

# Use the confirmed space key for Learning Technologies
SPACE_KEY = "LT"

try:
    # Initialize the Confluence reader
    reader = ConfluenceReader(
        base_url=confluence_url,
        api_token=confluence_api_key,
        user_name=confluence_username,
        cloud=True
    )
    
    print(f"Attempting to load pages from '{SPACE_KEY}' (Learning Technologies)...")
    
    # Load pages from your space
    pages = reader.load_data(space_key=SPACE_KEY, max_num_results=5)
    
    print(f"\nSuccessfully loaded {len(pages)} pages!")
    for page in pages:
        print(f"- {page.metadata.get('title', 'Untitled')}")
    
    print("\nConnection successful!")
except Exception as e:
    print(f"\nError: {e}")