import chromadb

# Initialize ChromaDB client
chroma_client = chromadb.Client()

# List all collections
collections = chroma_client.list_collections()
print("Available collections:")
for collection_name in collections:
    print(f"- {collection_name}")