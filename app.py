import streamlit as st
import sys
import os

import pandas as pd

# 1. Page Config
st.set_page_config(
    page_title="Medi-Insight | Diabetes Assistant",
    page_icon="🩺",
    layout="wide"
)

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.rag_chain import get_answer

# Load Source Lookup
@st.cache_data
def load_source_lookup():
    try:
        df = pd.read_excel("Source_lookup.xlsx")
        # Create a dictionary mapping FileName to (Title, URL, PDF_Link)
        # Assuming columns: 'FileName', 'Guideline Title', 'HTML', 'Document Link'
        lookup = {}
        for _, row in df.iterrows():
            fname = str(row['FileName']).strip()
            title = str(row['Guideline Title']).strip()
            url = str(row['HTML']).strip()
            pdf_link = str(row['Document Link']).strip() if 'Document Link' in row else "#"
            lookup[fname] = (title, url, pdf_link)
        return lookup
    except Exception as e:
        st.error(f"Failed to load source lookup: {e}")
        return {}

source_lookup = load_source_lookup()

# 4. Styling
st.markdown("""
<style>
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        color: #31333F; /* Ensure dark text */
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #e8f0fe;
        border-color: #d2e3fc;
        color: #31333F; /* Ensure dark text */
    }
    .main .block-container {
        padding-top: 2rem;
    }
    /* Force text color inside markdown elements within chat messages */
    .stChatMessage p, .stChatMessage li, .stChatMessage h1, .stChatMessage h2, .stChatMessage h3 {
        color: #31333F !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("About this Project")
    st.info(
        "Medi-Insight uses OpenAI and LangChain to index the official [Diabetes Canada Clinical Practice Guidelines](https://guidelines.diabetes.ca/cpg). "
        "It provides accurate, evidence-based answers for healthcare professionals."
    )
    
    st.markdown("---")
    st.subheader("Try these questions:")
    example_questions = [
        "What is the first-line therapy for Type 2 diabetes?",
        "What are the A1C targets for frail elderly?",
        "Screening criteria for gestational diabetes?"
    ]
    
    # Use buttons to trigger questions
    for q in example_questions:
        if st.button(q):
            st.session_state.messages.append({"role": "user", "content": q})
            # We need to rerun to process the message in the main loop immediately
            # But st.rerun() might reset the button state, so we append to history and let the main loop handle it.
            # A slight hack is needed to auto-submit: set a flag or just let the user see it in history and hit enter?
            # Better UX: Append to history and force a rerun so the main loop picks it up as the last message to process?
            # Actually, the main loop processes input from st.chat_input. 
            # To programmatically trigger, we can set a session state variable 'trigger_query'
            st.session_state.trigger_query = q

    st.markdown("---")
    st.markdown("### Created By")
    st.markdown(
        """
        **Eldon Wen**  
        [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/)  
        [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/eldonwen/Medi-Insight)
        """
    )

# 2. Header Image
if os.path.exists("banner.jpg"):
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.image("banner.jpg", width="stretch")

# 3. Title & Subtitle
st.title("Diabetes Canada Clinical Guidelines Assistant")
st.markdown("### An AI-powered tool for healthcare professionals to query evidence-based protocols.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Handle Example Question Trigger
if "trigger_query" in st.session_state and st.session_state.trigger_query:
    prompt = st.session_state.trigger_query
    del st.session_state.trigger_query # Clear it so it doesn't loop
    # Add to history if not already the last message (to avoid dupes if rerun happens weirdly)
    if not st.session_state.messages or st.session_state.messages[-1]["content"] != prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Force a rerun to ensure the UI updates and then we process the response
    # Actually, we can just proceed to process it below if we structure the loop right.
    # But standard Streamlit flow is input -> rerun.
    # Let's just set a variable 'process_now' = True
    process_now = True
else:
    process_now = False
    prompt = None

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
input_prompt = st.chat_input("Ask a question about Diabetes Canada Guidelines...")

if input_prompt:
    prompt = input_prompt
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    process_now = True

if process_now and prompt:
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                stream, source_documents = get_answer(prompt)
                
                # Stream the response
                answer_text = st.write_stream(stream)
                
                # Display Source Evidence
                with st.expander("🔍 View Source Evidence (Pages & Excerpts)"):
                    for i, doc in enumerate(source_documents):
                        page_num = doc.metadata.get("page", "Unknown")
                        # Get filename from path
                        full_source = doc.metadata.get("source", "Unknown")
                        source_file = os.path.basename(full_source)
                        
                        # Lookup Title and URL
                        title, url, pdf_link = source_lookup.get(source_file, (source_file, "https://guidelines.diabetes.ca/cpg", "#"))
                        
                        excerpt = doc.page_content[:200] + "..."
                        
                        link_md = title
                        if url != "#" and url.lower() != "nan":
                            link_md = f"[{title}]({url})"
                        
                        pdf_md = ""
                        if pdf_link != "#" and pdf_link.lower() != "nan":
                             pdf_md = f" | [📥 Download PDF]({pdf_link})"

                        st.markdown(f"**Source {i+1}:** {link_md} (Page {page_num}){pdf_md}")
                            
                        st.caption(f"\"{excerpt}\"")
                        st.text("") # Small spacer instead of divider

                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer_text})
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Disclaimer
st.markdown("---")
st.warning("Disclaimer: This tool is for informational purposes only and does not constitute medical advice. Always verify with the original Diabetes Canada Guidelines.")
