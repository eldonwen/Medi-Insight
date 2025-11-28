from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "chroma_db"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

def get_qa_chain():
    embedding_function = OpenAIEmbeddings()
    # Ensure the directory exists or handle error if not ingested yet
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Create a retriever
    retriever = db.as_retriever(search_kwargs={"k": 5})
    
    model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    return retriever, model

def query_rag(query_text):
    retriever, model = get_qa_chain()
    
    results = retriever.invoke(query_text)
    if not results:
        return "I couldn't find any relevant information in the provided documents.", []

    context_text = "\n\n---\n\n".join([doc.page_content for doc in results])
    
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | model
    
    response = chain.invoke({"context": context_text, "question": query_text})
    
    sources = [doc.metadata.get("source", None) for doc in results]
    
    return response.content, sources
