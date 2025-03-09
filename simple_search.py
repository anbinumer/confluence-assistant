import streamlit as st
import chromadb
import json
import os

st.title("🧠 Simple Confluence Search")

# Direct text search
confluence_data = "confluence_data"
json_files = [f for f in os.listdir(confluence_data) if f.endswith('.json')]

query = st.text_input("Search:")
if st.button("Search") and query:
    results = []
    for file in json_files:
        with open(os.path.join(confluence_data, file), 'r') as f:
            data = json.load(f)
            if query.lower() in data.get('text', '').lower() or query.lower() in data.get('title', '').lower():
                results.append(data)
    
    if results:
        st.success(f"Found {len(results)} results")
        for res in results[:5]:
            st.subheader(res.get('title'))
            st.markdown(f"[Open in Confluence]({res.get('url')})")
            st.text_area("Preview", res.get('text')[:500] + "...", height=150)
    else:
        st.warning("No results found")