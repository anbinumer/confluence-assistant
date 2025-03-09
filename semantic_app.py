import streamlit as st
import chromadb
import os
import json
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Page configuration
st.set_page_config(page_title="Confluence Knowledge Assistant", page_icon="🧠", layout="wide")

# Create Tf-IDF based search index
@st.cache_resource
def create_search_index():
    # Load confluence data
    confluence_data = "confluence_data"
    json_files = [f for f in os.listdir(confluence_data) if f.endswith('.json') and f != "metadata.pickle"]
    
    documents = []
    metadata = []
    
    for file in json_files:
        with open(os.path.join(confluence_data, file), 'r', encoding='utf-8') as f:
            data = json.load(f)
            documents.append(data.get('text', ''))
            metadata.append({
                'title': data.get('title', ''),
                'url': data.get('url', ''),
                'id': data.get('id', '')
            })
    
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
        if similarities[idx] > 0:  # Only include if there's some similarity
            doc = documents[idx]
            meta = metadata[idx]
            results.append({
                'text': doc,
                'title': meta['title'],
                'url': meta['url'],
                'similarity': similarities[idx]
            })
    
    return results

# Function to generate an answer based on relevant documents
def generate_answer(query, results):
    if not results:
        return "No relevant information found."
    
    # Combine the relevant document texts
    combined_text = "\n\n".join([f"Document: {r['title']}\n{r['text'][:1000]}" for r in results])
    
    # Simple keyword extraction
    query_words = set(re.findall(r'\b\w+\b', query.lower()))
    query_words = {w for w in query_words if len(w) > 3}
    
    # Find relevant sentences
    sentences = re.split(r'(?<=[.!?])\s+', combined_text)
    relevant_sentences = []
    
    for sentence in sentences:
        sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
        overlap = query_words.intersection(sentence_words)
        if overlap and len(sentence.split()) > 5:
            relevant_sentences.append(sentence)
    
    # Format the answer
    if relevant_sentences:
        answer = "Based on the Confluence documents, here's what I found:\n\n"
        answer += "\n\n".join(relevant_sentences[:5])
    else:
        # Fall back to first few sentences of top documents
        answer = "Here is some information that might be relevant:\n\n"
        for r in results[:2]:
            first_sentences = " ".join(re.split(r'(?<=[.!?])\s+', r['text'])[:3])
            answer += f"• {first_sentences}\n\n"
    
    return answer

# Main app
def main():
    st.title("🧠 Confluence Knowledge Assistant")
    st.subheader("Ask a question about Learning Technologies at ACU")
    
    # Initialize search index
    with st.spinner("Loading knowledge base..."):
        vectorizer, tfidf_matrix, documents, metadata = create_search_index()
    
    # Search interface
    query = st.text_input("What would you like to know?")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        num_results = st.slider("Number of sources", 1, 10, 5)
        show_sources = st.checkbox("Show source documents", value=True)
    
    search_button = st.button("Search")
    
    # Process search
    if search_button and query:
        with st.spinner("Searching knowledge base..."):
            results = search_documents(query, vectorizer, tfidf_matrix, documents, metadata, num_results)
            
            if not results:
                st.warning("No results found. Try rephrasing your question.")
                return
        
        # Generate answer
        with st.spinner("Generating answer..."):
            answer = generate_answer(query, results)
        
        # Display answer
        st.markdown("### Answer")
        st.markdown(answer)
        
        # Display sources if requested
        if show_sources and results:
            st.markdown("### Sources")
            
            for i, result in enumerate(results):
                with st.expander(f"{i+1}. {result['title']}"):
                    st.markdown(f"**Relevance:** {result['similarity']:.2f}")
                    st.markdown(f"**URL:** [View in Confluence]({result['url']})")
                    
                    # Display content in a more readable format
                    paragraphs = result['text'].split('\n\n')
                    for para in paragraphs[:5]:  # Show first 5 paragraphs
                        if para.strip():
                            st.markdown(para)
                    
                    if len(paragraphs) > 5:
                        st.write("...")

if __name__ == "__main__":
    main()