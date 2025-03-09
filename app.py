import streamlit as st
import chromadb
import textwrap
from transformers import pipeline
import time

# Page configuration
st.set_page_config(
    page_title="Confluence Knowledge Assistant",
    page_icon="🧠",
    layout="wide"
)

# Initialize ChromaDB
@st.cache_resource
def load_vector_db():
    chroma_client = chromadb.Client()
    try:
        collection = chroma_client.get_collection(name="confluence_kb")
        return collection
    except Exception as e:
        st.error(f"Error loading vector database: {e}")
        return None

# Initialize language model
@st.cache_resource
def load_language_model():
    try:
        # Load a smaller model with fewer requirements
        model = pipeline(
            "text-generation",
            model="distilgpt2",
            low_cpu_mem_usage=True
        )
        return model
    except Exception as e:
        st.error(f"Error loading language model: {e}")
        return None

# Search function
def search_confluence(query, collection, num_results=5):
    results = collection.query(
        query_texts=[query],
        n_results=num_results
    )
    return results

# Answer generation function
def generate_answer(query, context, model):
    prompt = f"""
Please answer the following question based on the provided information.
If you can't find a good answer in the context, say you don't know.

Question: {query}

Context information:
{context}

Answer:
"""
    
    result = model(
        prompt,
        max_length=512,
        temperature=0.7,
        num_return_sequences=1
    )
    
    # Extract the generated text
    answer = result[0]['generated_text']
    
    # Remove the prompt part
    answer = answer.replace(prompt, "").strip()
    
    # Some models repeat the question, let's clean that
    if answer.startswith(query):
        answer = answer[len(query):].strip()
    
    return answer

# Main app
def main():
    st.title("🧠 Confluence Knowledge Assistant")
    st.subheader("Ask a question about Learning Technologies at ACU")
    
    # Initialize resources
    with st.spinner("Loading resources..."):
        collection = load_vector_db()
        model = load_language_model()
    
    if collection is None or model is None:
        st.error("Failed to load required resources. Check the error messages above.")
        return
    
    # Search interface
    query = st.text_input("What would you like to know?")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        num_results = st.slider("Number of sources to consider", 1, 10, 5)
        show_sources = st.checkbox("Show source chunks", value=False)
    
    search_button = st.button("Search")
    
    # Process search
    if search_button and query:
        with st.spinner("Searching knowledge base..."):
            results = search_confluence(query, collection, num_results)
            
            if len(results['documents'][0]) == 0:
                st.warning("No results found. Try rephrasing your question.")
                return
        
        # Prepare context for the language model
        context = "\n\n".join([f"Source {i+1}: {doc}" for i, doc in enumerate(results['documents'][0])])
        
        # Generate answer
        with st.spinner("Generating answer..."):
            answer = generate_answer(query, context, model)
        
        # Display answer
        st.markdown("### Answer")
        st.markdown(answer)
        
        # Display sources if requested
        if show_sources:
            st.markdown("### Sources")
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                with st.expander(f"Source {i+1}: {metadata['title']}"):
                    st.markdown(f"**Page:** {metadata['title']}")
                    st.markdown(f"**URL:** [View in Confluence]({metadata['url']})")
                    st.markdown("**Content:**")
                    st.text(textwrap.fill(doc, width=100))

if __name__ == "__main__":
    main()