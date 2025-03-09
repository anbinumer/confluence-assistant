import chromadb
import os
import shutil

# Remove any existing ChromaDB data
if os.path.exists("./chroma_db"):
    shutil.rmtree("./chroma_db")

# Create a persistent client
print("Creating ChromaDB client...")
client = chromadb.PersistentClient(path="./chroma_db")

# Create a new collection
print("Creating test collection...")
collection = client.create_collection(name="test_collection")

# Add some test data
print("Adding test data...")
collection.add(
    documents=["This is a test document about Confluence", 
               "Another document about searching knowledge bases",
               "Learning Technologies at ACU uses various tools"],
    ids=["doc1", "doc2", "doc3"],
    metadatas=[
        {"source": "test", "title": "Test Document 1"},
        {"source": "test", "title": "Test Document 2"},
        {"source": "test", "title": "Test Document 3"},
    ]
)

# Query the collection
print("Querying test collection...")
results = collection.query(
    query_texts=["confluence knowledge"],
    n_results=2
)

print("\nQuery results:")
for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"Result {i+1}: {metadata['title']}")
    print(f"Content: {doc}")

# List all collections
print("\nListing all collections:")
collections = client.list_collections()
for collection in collections:
    print(f"- {collection.name}")

print("\nTest completed successfully!")