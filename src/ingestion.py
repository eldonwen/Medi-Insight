import os
import shutil
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

import warnings
# Suppress LangChainDeprecationWarning for Chroma
from langchain_core._api import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

load_dotenv()

DATA_PATH = "CPG"
CHROMA_PATH = "chroma_db"

def load_documents():
    documents = []
    if not os.path.exists(DATA_PATH):
        print(f"Directory {DATA_PATH} not found.")
        return []
    
    for filename in os.listdir(DATA_PATH):
        if filename.endswith(".pdf"):
            file_path = os.path.join(DATA_PATH, filename)
            try:
                print(f"Loading {file_path}...")
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return documents

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def create_vector_db(chunks):
    if not chunks:
        print("No documents to process.")
        return

    # Clear existing DB to avoid duplicates during testing
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    embedding_function = OpenAIEmbeddings()
    
    print(f"Creating Vector DB with {len(chunks)} chunks...")
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=CHROMA_PATH
    )
    print(f"Vector DB created at {CHROMA_PATH}")

if __name__ == "__main__":
    try:
        docs = load_documents()
        chunks = split_documents(docs)
        create_vector_db(chunks)
    except Exception as e:
        import traceback
        traceback.print_exc()
