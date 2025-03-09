import streamlit as st
import requests
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer
import re

# Page configuration
st.set_page_config(page_title="Confluence Knowledge Assistant", page_icon="🧠", layout="wide")

# Get secrets
if 'CONFLUENCE_USERNAME' in st.secrets:
    confluence_username = st.secrets['CONFLUENCE_USERNAME']
    confluence_api_key = st.secrets['CONFLUENCE_API_KEY']
    confluence_url = st.secrets['CONFLUENCE_URL']
else:
    from dotenv import load_dotenv
    load_dotenv()
    import os
    confluence_username = os.getenv("CONFLUENCE_USERNAME")
    confluence_api_key = os.getenv("CONFLUENCE_API_KEY")
    confluence_url = os.getenv("CONFLUENCE_URL")

# Download and process Confluence data
@st.cache_resource
def download_confluence_data():
    content_url = f"{confluence_url}/wiki/rest/api/content"
    
    try:
        response = requests.get(
            f"{content_url}?spaceKey=LT&limit=100&expand=body.storage",
            auth=(confluence_username, confluence_api_key)
        )
        
        if response.status_code != 200:
            st.error(f"Error accessing Confluence: {response.status_code}")
            return []
            
        data = response.json()
        pages = data.get('results', [])
        
        documents = []
        for page in pages:
            title = page.get('title', 'Untitled')
            page_id = page.get('id', 'Unknown')
            url = f"{confluence_url}/wiki/spaces/LT/pages/{page_id}"
            
            # Extract text content from HTML
            html_content = page.get('body', {}).get('storage', {}).get('value', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            text_content = soup.get_text()
            
            # Split into chunks for better search
            chunks = split_into_chunks(text_content, title, url)
            documents.extend(chunks)
        
        return documents
    except Exception as e:
        st.error(f"Error fetching Confluence data: {e}")
        return []

def split_into_chunks(text, title, url, chunk_size=1000, overlap=200):
    # Split long text into smaller chunks with overlap
    chunks = []
    
    # If text is short, keep as one chunk
    if len(text) <= chunk_size:
        return [{"title": title, "text": text, "url": url}]
    
    # Split into chunks
    for i in range(0, len(text), chunk_size - overlap):
        chunk_text = text[i:i + chunk_size]
        if len(chunk_text) < 100:  # Skip very small chunks
            continue
        
        chunk_title = f"{title} (Part {i//(chunk_size-overlap) + 1})"
        chunks.append({"title": chunk_title, "text": chunk_text, "url": url})
    
    return chunks

# Load embeddings model and create search index
@st.cache_resource
def create_embeddings_index():
    # Download data
    documents_data = download_confluence_data()
    
    if not documents_data:
        # Fallback to sample data if download fails
        documents_data = [
            {"title": "Sample 1", "text": "This is a sample document about Canvas.", "url": "#"},
            {"title": "Sample 2", "text": "LICs can be enrolled in Canvas courses.", "url": "#"}
        ]
    
    # Load embeddings model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Create embeddings for all documents
    documents = [item["text"] for item in documents_data]
    embeddings = model.encode(documents)
    
    return model, embeddings, documents_data

# Search function using embeddings
def search_documents(query, model, embeddings, documents_data, top_k=5):
    # Create query embedding
    query_embedding = model.encode([query])[0]
    
    # Calculate similarity to all documents
    similarities = []
    for doc_embedding in embeddings:
        similarity = np.dot(query_embedding, doc_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
        )
        similarities.append(similarity)
    
    # Find top matches
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.2:  # Minimum relevance threshold
            results.append({
                "text": documents_data[idx]["text"],
                "title": documents_data[idx]["title"],
                "url": documents_data[idx]["url"],
                "similarity": similarities[idx]
            })
    
    return results

# Generate answer from relevant documents
def generate_answer(query, results):
    if not results:
        return "I couldn't find relevant information about this topic in the Knowledge Base."
    
    # Extract most relevant content
    relevant_texts = [r["text"] for r in results]
    combined_text = " ".join(relevant_texts)
    
    # Find paragraphs that might contain answers
    paragraphs = re.split(r'\n+', combined_text)
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    
    # Score paragraphs by relevance to query
    scored_paragraphs = []
    for para in paragraphs:
        if len(para.strip()) < 30:
            continue
            
        para_words = set(re.findall(r'\b\w+\b', para.lower()))
        relevance = len(query_words.intersection(para_words)) / len(query_words) if query_words else 0
        scored_paragraphs.append((para, relevance))
    
    # Sort by relevance
    scored_paragraphs.sort(key=lambda x: x[1], reverse=True)
    
    # Construct answer from most relevant paragraphs
    answer_parts = []
    for para, score in scored_paragraphs[:3]:
        if score > 0.1:  # Minimum relevance threshold
            answer_parts.append(para)
    
    if answer_parts:
        answer = "\n\n".join(answer_parts)
    else:
        # Fallback to first paragraph of top result
        answer = results[0]["text"].split("\n")[0]
        
    return answer

# Format a document for display
def format_document(doc):
    # Clean up and format content for display
    text = doc["text"]
    
    # Format paragraphs
    paragraphs = re.split(r'\n+', text)
    formatted_text = ""
    
    for para in paragraphs:
        if len(para.strip()) > 0:
            formatted_text += f"{para.strip()}\n\n"
    
    return formatted_text

# Main app
def main():
    st.title("🧠 Confluence Knowledge Assistant")
    st.subheader("Ask a question about Learning Technologies at ACU")
    
    # Initialize search index
    with st.spinner("Loading knowledge base..."):
        model, embeddings, documents_data = create_embeddings_index()
        st.success(f"Loaded {len(documents_data)} documents from Confluence")
    
    # Search interface
    query = st.text_input("What would you like to know?")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        num_results = st.slider("Number of sources", 1, 10, 5)
        generate_answers = st.checkbox("Generate answer summary", value=True)
    
    search_button = st.button("Search")
    
    if search_button and query:
        with st.spinner("Searching knowledge base..."):
            results = search_documents(query, model, embeddings, documents_data, num_results)
            
            if not results:
                st.warning("No relevant results found. Try rephrasing your question.")
                return
        
        # Generate answer if requested
        if generate_answers:
            with st.spinner("Generating answer..."):
                answer = generate_answer(query, results)
            
            st.markdown("### Answer")
            st.markdown(answer)
            st.markdown("---")
        
        # Display results
        st.markdown("### Source Documents")
        
        for i, result in enumerate(results):
            with st.expander(f"{i+1}. {result['title']} (Relevance: {result['similarity']:.2f})"):
                st.markdown(f"**[View in Confluence]({result['url']})**")
                
                # Format and display content in a readable way
                formatted_text = format_document(result)
                
                # Display in paragraphs
                st.markdown(formatted_text)

if __name__ == "__main__":
    main()