import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

# Create TF-IDF search index
@st.cache_resource
def create_search_index():
    # Download data
    documents_data = download_confluence_data()
    
    if not documents_data:
        # Fallback to sample data if download fails
        documents_data = [
            {"title": "Sample 1", "text": "This is a sample document about Canvas.", "url": "#"},
            {"title": "Sample 2", "text": "LICs can be enrolled in Canvas courses.", "url": "#"}
        ]
    
    # Create TF-IDF vectorizer
    documents = [item["text"] for item in documents_data]
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    return vectorizer, tfidf_matrix, documents_data

# Search function
def search_documents(query, vectorizer, tfidf_matrix, documents_data, top_k=5):
    # Transform query to TF-IDF vector
    query_vector = vectorizer.transform([query])
    
    # Calculate similarity
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    
    # Get top matches
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.1:  # Minimum relevance threshold
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
    
    # Split into paragraphs and find relevant ones
    all_paragraphs = []
    for text in relevant_texts:
        paragraphs = re.split(r'\n+', text)
        all_paragraphs.extend([p for p in paragraphs if len(p.strip()) > 30])
    
    # Find paragraphs with query terms
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    query_words = {w for w in query_words if len(w) > 3}  # Only meaningful words
    
    relevant_paragraphs = []
    for para in all_paragraphs:
        para_lower = para.lower()
        matches = sum(1 for word in query_words if word in para_lower)
        if matches > 0:
            relevant_paragraphs.append((para, matches))
    
    # Sort by relevance
    relevant_paragraphs.sort(key=lambda x: x[1], reverse=True)
    
    # Build answer from most relevant paragraphs
    if relevant_paragraphs:
        answer_parts = [p[0] for p in relevant_paragraphs[:3]]
        answer = "\n\n".join(answer_parts)
    else:
        # Fallback to first paragraph
        answer = all_paragraphs[0] if all_paragraphs else "No specific information found."
    
    return answer

# Main app
def main():
    st.title("🧠 Confluence Knowledge Assistant")
    st.subheader("Ask a question about Learning Technologies at ACU")
    
    # Initialize search index
    with st.spinner("Loading knowledge base..."):
        vectorizer, tfidf_matrix, documents_data = create_search_index()
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
            results = search_documents(query, vectorizer, tfidf_matrix, documents_data, num_results)
            
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
                
                # Format text into paragraphs for readability
                paragraphs = re.split(r'\n+', result['text'])
                for para in paragraphs:
                    if len(para.strip()) > 0:
                        st.markdown(para)
                        st.markdown("")

if __name__ == "__main__":
    main()