import streamlit as st
import chromadb

# Page configuration
st.set_page_config(
    page_title="Confluence Knowledge Assistant",
    page_icon="🧠",
    layout="wide"
)

# Initialize ChromaDB
@st.cache_resource
def load_vector_db():
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("confluence_kb")
        return collection
    except Exception as e:
        st.error(f"Error loading vector database: {e}")
        return None

# Search function
def search_confluence(query, collection, num_results=5):
    results = collection.query(
        query_texts=[query],
        n_results=num_results
    )
    return results

# Main app
def main():
    st.title("🧠 Confluence Knowledge Assistant")
    st.subheader("Ask a question about Learning Technologies at ACU")
    
    # Initialize resources
    with st.spinner("Loading resources..."):
        collection = load_vector_db()
    
    if collection is None:
        st.error("Failed to load vector database. Check the error message above.")
        return
    
    # Search interface
    query = st.text_input("What would you like to know?")
    
    num_results = st.slider("Number of results", 1, 10, 5)
    
    search_button = st.button("Search")
    
    # Process search
    if search_button and query:
        with st.spinner("Searching knowledge base..."):
            results = search_confluence(query, collection, num_results)
            
            if len(results['documents'][0]) == 0:
                st.warning("No results found. Try rephrasing your question.")
                return
        
        # Display results
        st.markdown("### Results")
        
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            st.markdown(f"#### Result {i+1}: {metadata['title']}")
            st.markdown(f"**URL:** [View in Confluence]({metadata['url']})")
            st.markdown("**Content:**")
            st.text_area(f"Content {i+1}", value=doc, height=200)
            st.markdown("---")

if __name__ == "__main__":
    main()