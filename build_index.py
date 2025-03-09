import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm
import textwrap

# Directory settings
DATA_DIR = "confluence_data"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Character overlap between chunks

# Initialize the embedding model
print("Loading the embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Chroma DB
print("Initializing the vector database...")
chroma_client = chromadb.Client()

# Create a new collection (or get existing one)
COLLECTION_NAME = "confluence_kb"
print(f"Creating collection: {COLLECTION_NAME}")

# Check if collection exists first
collections = chroma_client.list_collections()
if COLLECTION_NAME in collections:
    print(f"Collection '{COLLECTION_NAME}' already exists, deleting it first...")
    chroma_client.delete_collection(COLLECTION_NAME)

# Create the collection
collection = chroma_client.create_collection(name=COLLECTION_NAME)
print(f"Collection created successfully")

# Function to chunk text into smaller pieces
def chunk_text(text, title, page_id, url):
    chunks = []
    chunk_ids = []
    metadatas = []
    
    # If text is shorter than chunk size, keep it as one chunk
    if len(text) <= CHUNK_SIZE:
        chunks.append(text)
        chunk_ids.append(f"{page_id}-0")
        metadatas.append({"title": title, "page_id": page_id, "url": url})
        return chunks, chunk_ids, metadatas
    
    # Split into overlapping chunks
    for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk = text[i:i + CHUNK_SIZE]
        if len(chunk) < 100:  # Skip very small chunks at the end
            continue
            
        chunk_id = f"{page_id}-{i//(CHUNK_SIZE - CHUNK_OVERLAP)}"
        chunks.append(chunk)
        chunk_ids.append(chunk_id)
        metadatas.append({
            "title": title,
            "page_id": page_id,
            "url": url,
            "chunk_index": i//(CHUNK_SIZE - CHUNK_OVERLAP)
        })
    
    return chunks, chunk_ids, metadatas

# Process each file in the data directory
print("Processing Confluence pages...")
all_chunks = []
all_chunk_ids = []
all_metadatas = []

# Get all JSON files
json_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json') and not f == 'metadata.pickle']
print(f"Found {len(json_files)} JSON files to process")

# Process each file
for file_name in tqdm(json_files):
    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        page_data = json.load(f)
    
    # Get page details
    page_id = page_data.get('id')
    title = page_data.get('title')
    text = page_data.get('text')
    url = page_data.get('url')
    
    # Chunk the text
    chunks, chunk_ids, metadatas = chunk_text(text, title, page_id, url)
    
    all_chunks.extend(chunks)
    all_chunk_ids.extend(chunk_ids)
    all_metadatas.extend(metadatas)

# Add the data to the collection in smaller batches to avoid issues
print(f"Adding {len(all_chunks)} chunks to the vector database...")
BATCH_SIZE = 100
for i in range(0, len(all_chunks), BATCH_SIZE):
    end = min(i + BATCH_SIZE, len(all_chunks))
    print(f"Adding batch {i//BATCH_SIZE + 1}/{(len(all_chunks) + BATCH_SIZE - 1)//BATCH_SIZE}...")
    
    try:
        collection.add(
            documents=all_chunks[i:end],
            ids=all_chunk_ids[i:end],
            metadatas=all_metadatas[i:end]
        )
    except Exception as e:
        print(f"Error adding batch: {e}")
        # Continue with next batch

print("Vector index built successfully!")

# Test the search functionality
def search_confluence(query, num_results=3):
    # Get embeddings for the query
    results = collection.query(
        query_texts=[query],
        n_results=num_results
    )
    
    return results

print("\nTesting search functionality with a sample query...")
test_query = "How do I use Canvas?"
results = search_confluence(test_query)

print(f"Query: '{test_query}'")
print(f"Found {len(results['documents'][0])} matching chunks:")

for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"\nResult {i+1}:")
    print(f"Title: {metadata['title']}")
    print(f"URL: {metadata['url']}")
    print("Content preview:")
    print(textwrap.fill(doc[:300] + "...", width=80))

print("\nVector search is ready to use!")
print(f"Use collection name '{COLLECTION_NAME}' in your app.py")