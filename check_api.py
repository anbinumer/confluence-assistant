import os
from llama_index.readers.confluence import ConfluenceReader
from dotenv import load_dotenv
import inspect

# Load environment variables
load_dotenv()

# Get credentials from environment
confluence_url = os.getenv("CONFLUENCE_URL")
confluence_username = os.getenv("CONFLUENCE_USERNAME")
confluence_api_key = os.getenv("CONFLUENCE_API_KEY")

# Print the parameters accepted by ConfluenceReader
print(inspect.signature(ConfluenceReader.__init__))

print(f"URL: {confluence_url}")
print(f"Username: {confluence_username}")
print(f"API Key: {'*' * len(confluence_api_key) if confluence_api_key else 'Not set'}")