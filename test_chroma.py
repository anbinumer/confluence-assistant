import chromadb

# Initialize ChromaDB client
chroma_client = chromadb.Client()

# Create a test collection
test_collection = chroma_client.create_collection(name="test_collection")

# Add a test document
test_collection.add(
    documents=["This is a test document"],
    ids=["test1"],
    metadatas=[{"source": "test"}]
)

# Verify the collection exists
collections = chroma_client.list_collections()
print("Available collections:")
for collection_name in collections:
    print(f"- {collection_name}")

# Query the test collection
results = test_collection.query(
    query_texts=["test"],
    n_results=1
)

print("\nQuery results:")
print(results)