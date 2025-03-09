import streamlit as st
import os
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Page configuration
st.set_page_config(page_title="Confluence Knowledge Assistant", page_icon="🧠", layout="wide")

# Get secrets from Streamlit Cloud
if 'CONFLUENCE_USERNAME' in st.secrets:
    confluence_username = st.secrets['CONFLUENCE_USERNAME']
    confluence_api_key = st.secrets['CONFLUENCE_API_KEY']
    confluence_url = st.secrets['CONFLUENCE_URL']
else:
    # Local fallback
    from dotenv import load_dotenv
    load_dotenv()
    confluence_username = os.getenv("CONFLUENCE_USERNAME")
    confluence_api_key = os.getenv("CONFLUENCE_API_KEY")
    confluence_url = os.getenv("CONFLUENCE_URL")

# Create and cache the search index
@st.cache_resource
def create_search_index():
    # In cloud environment, we'd download data here
    if 'DOWNLOAD_ON_START' in st.secrets and st.secrets['DOWNLOAD_ON_START']:
        with st.spinner("Downloading fresh Confluence data..."):
            # Download code would go here
            pass
    
    # For now, let's use sample data
    sample_data = [
        {"title": "Sample Document 1", "text": "This is a sample document about learning technologies."},
        {"title": "Sample Document 2", "text": "Canvas is a learning management system used at ACU."}
    ]
    
    # Create documents and metadata
    documents = [item["text"] for item in sample_data]
    metadata = [{"title": item["title"], "url": "#"} for item in sample_data]
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    return vectorizer, tfidf_matrix, documents, metadata

# Search function
def search_documents(query, vectorizer, tfidf_matrix, documents, metadata, top_k=5):
    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    results = []
    for idx in top_indices:
        if similarities[idx] > 0:
            results.append({
                'text': documents[idx],
                'title': metadata[idx]['title'],
                'url': metadata[idx]['url'],
                'similarity': similarities[idx]
            })
    
    return results

# Main app
def main():
    st.title("🧠 Confluence Knowledge Assistant")
    st.subheader("Ask a question about Learning Technologies at ACU")
    
    # Initialize search index
    with st.spinner("Loading knowledge base..."):
        vectorizer, tfidf_matrix, documents, metadata = create_search_index()
    
    # Search interface
    query = st.text_input("What would you like to know?")
    
    search_button = st.button("Search")
    
    if search_button and query:
        with st.spinner("Searching knowledge base..."):
            results = search_documents(query, vectorizer, tfidf_matrix, documents, metadata, 5)
            
            if not results:
                st.warning("No results found. Try rephrasing your question.")
                return
        
        # Display results
        st.markdown("### Results")
        
        for i, result in enumerate(results):
            st.markdown(f"#### {i+1}. {result['title']}")
            st.markdown(f"**Relevance score:** {result['similarity']:.2f}")
            st.markdown(result['text'])
            st.markdown("---")

if __name__ == "__main__":
    main()