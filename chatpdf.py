import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import pickle

# Load env
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

EMBEDDINGS_DIR = "embeddings/"
DATA_DIR = "data/"

def process_and_save_pdfs(pdf_paths=None, index_name="docs_index"):
    """Process all PDFs in data folder and save FAISS embeddings"""
    docs = []
    
    # If no specific paths provided, process all PDFs in data folder
    if pdf_paths is None:
        if not os.path.exists(DATA_DIR):
            raise ValueError("Data directory does not exist")
        
        pdf_paths = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]
    else:
        # Also include existing PDFs in data folder
        existing_pdfs = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith('.pdf')]
        # Combine new uploads with existing files, remove duplicates
        all_pdfs = list(set(pdf_paths + existing_pdfs))
        pdf_paths = all_pdfs
    
    if not pdf_paths:
        raise ValueError("No PDF files found to process")
    
    # Load all PDFs
    for pdf_path in pdf_paths:
        if os.path.exists(pdf_path):
            try:
                loader = PyMuPDFLoader(pdf_path)
                docs.extend(loader.load())
            except Exception as e:
                print(f"Warning: Could not load {pdf_path}: {str(e)}")
                continue

    if not docs:
        raise ValueError("No content found in PDFs")

    # Split docs
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    # Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Vector DB
    vectordb = FAISS.from_documents(chunks, embedding=embeddings)

    # Save FAISS index
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    faiss_path = os.path.join(EMBEDDINGS_DIR, f"{index_name}.faiss")
    pkl_path = os.path.join(EMBEDDINGS_DIR, f"{index_name}.pkl")

    vectordb.save_local(faiss_path)
    with open(pkl_path, "wb") as f:
        pickle.dump(embeddings, f)

    print(f"Processed {len(pdf_paths)} PDF files and created embeddings for {len(chunks)} chunks")
    return faiss_path, pkl_path

def rebuild_embeddings_for_all_docs(index_name="docs_index"):
    """Rebuild embeddings for all documents in data folder"""
    return process_and_save_pdfs(pdf_paths=None, index_name=index_name)

def load_vectordb(index_name="docs_index"):
    """Load FAISS index"""
    faiss_path = os.path.join(EMBEDDINGS_DIR, f"{index_name}.faiss")
    pkl_path = os.path.join(EMBEDDINGS_DIR, f"{index_name}.pkl")

    if not os.path.exists(faiss_path) or not os.path.exists(pkl_path):
        raise FileNotFoundError("No embeddings found. Please upload PDFs in admin panel first.")

    with open(pkl_path, "rb") as f:
        embeddings = pickle.load(f)

    vectordb = FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
    return vectordb

def get_qa_chain(vectordb):
    """QA Chain with memory and custom prompt for natural responses"""
    llm = ChatGroq(
        model="llama3-70b-8192",
        groq_api_key=groq_api_key,
        temperature=0.1
    )

    # Custom prompt template for more natural responses
    custom_prompt = PromptTemplate(
        template="""You are a helpful AI assistant. Use the following context to answer the user's question naturally and conversationally. 

Don't mention "according to the document" or "the manual states" or similar phrases. Just provide clear, direct answers as if you're having a natural conversation.

If you don't know something based on the context, simply say you don't have that information.

Context: {context}

Chat History: {chat_history}

Question: {question}

Answer: """,
        input_variables=["context", "chat_history", "question"]
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": custom_prompt}
    )

    return qa_chain