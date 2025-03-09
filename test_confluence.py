import os
from llama_index.readers.confluence import ConfluenceReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
confluence_url = os.getenv("CONFLUENCE_URL")
confluence_username = os.getenv("CONFLUENCE_USERNAME")
confluence_api_key = os.getenv("CONFLUENCE_API_KEY")

# Print info (for debugging)
print(f"URL: {confluence_url}")
print(f"Username: {confluence_username}")
print(f"API Key: {'*' * len(confluence_api_key) if confluence_api_key else 'Not set'}")

try:
    # Initialize the Confluence reader with correct parameters
    reader = ConfluenceReader(
        base_url=confluence_url,
        api_token=confluence_api_key,
        user_name=confluence_username,
        cloud=True
    )
    
    print("\nAttempting to connect to Confluence...")
    
    # Try to load pages directly, using your space key
    # Note: Verify if "LT" is the correct space key for your Learning Technologies space
    pages = reader.load_data(space_key="LT", max_num_results=5)
    
    print(f"\nSuccessfully loaded {len(pages)} pages!")
    for page in pages:
        print(f"- {page.get_content()[:100]}...")  # Print first 100 chars of content
    
    print("\nConnection successful!")
except Exception as e:
    print(f"\nError connecting to Confluence: {e}")
    print("\nTroubleshooting tips:")
    print("1. Check if 'LT' is the correct space key for your Learning Technologies space")
    print("2. Verify your Confluence URL (should be the base URL, not including /wiki/spaces)")
    print("3. Make sure your API token has appropriate permissions")
    print("4. Try using a different space key if you're not sure about 'LT'")