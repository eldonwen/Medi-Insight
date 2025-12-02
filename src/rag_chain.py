import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

import warnings
# Suppress LangChainDeprecationWarning for Chroma
from langchain_core._api import LangChainDeprecationWarning
warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)

load_dotenv()

CHROMA_PATH = "chroma_db"

def get_answer(query):
    # 1. Initialize Embeddings
    embedding_function = OpenAIEmbeddings()

    # 2. Load ChromaDB
    # We only need to provide the persist_directory and embedding_function
    # to load an existing database.
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # 3. Create Retriever
    retriever = db.as_retriever()

    # 4. Initialize LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # 5. Create Prompt
    prompt = ChatPromptTemplate.from_template("""
    Answer the following question based only on the provided context:

    <context>
    {context}
    </context>

    Question: {input}
    """)

    # 6. Create Chain
    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    # 7. Invoke Chain
    response = retrieval_chain.invoke({"input": query})
    
    return response["answer"]

if __name__ == "__main__":
    test_query = "What recommendations are provided regarding exercise in hot environments for people with diabetes?"
    print(f"Query: {test_query}")
    try:
        answer = get_answer(test_query)
        print(f"Answer: {answer}")
    except Exception as e:
        print(f"Error: {e}")
