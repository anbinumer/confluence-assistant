import chromadb

# Initialize ChromaDB
chroma_client = chromadb.Client()

# List all collections
collections = chroma_client.list_collections()

print("Available collections:")
for collection in collections:
    print(f"- {collection.name}")