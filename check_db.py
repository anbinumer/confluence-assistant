import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("confluence_kb")
print(f"Number of items in collection: {collection.count()}")