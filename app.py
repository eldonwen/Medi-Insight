import streamlit as st
import os
from src.retrieval import query_rag
from src.ingestion import load_documents, split_documents, create_vector_db

st.set_page_config(page_title="Medi-Insight", page_icon="🩺")

st.title("🩺 Medi-Insight: Diabetes Guidelines RAG")

with st.sidebar:
    st.header("Project Info")
    st.write("This tool queries the Diabetes Canada Clinical Practice Guidelines.")
    
    if st.button("Re-ingest Knowledge Base"):
        with st.spinner("Ingesting documents..."):
            docs = load_documents()
            chunks = split_documents(docs)
            create_vector_db(chunks)
            st.success("Ingestion complete!")

    openai_api_key = st.text_input("OpenAI API Key", type="password")
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question about diabetes guidelines..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("Please enter your OpenAI API Key in the sidebar.")
            st.stop()
            
        with st.spinner("Thinking..."):
            try:
                response, sources = query_rag(prompt)
                st.markdown(response)
                
                if sources:
                    st.markdown("---")
                    st.markdown("**Sources:**")
                    for source in set(sources):
                        st.markdown(f"- {os.path.basename(source)}")
                
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"An error occurred: {e}")
