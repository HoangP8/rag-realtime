from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import openai
from dotenv import load_dotenv
import os
import shutil
import time
import logging
import pypdf

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env.local')
load_dotenv(dotenv_path=dotenv_path)
openai.api_key = os.environ['OPENAI_API_KEY']
FAISS_PATH = "faiss"
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
breakpoint()
log_dir = 'result'
log_file = os.path.join(log_dir, 'chunk_latency.log')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(message)s',  
    filemode='a'
)

def main():
    """Main function to generate and store document chunks for multiple models."""
    
    documents = load_documents()
    chunks = split_text(documents)
    
    # Different embedding models
    models = [
        {"name": "text-embedding-ada-002", "type": "openai"},
        {"name": "text-embedding-3-small", "type": "openai"},
        {"name": "text-embedding-3-large", "type": "openai"},
        {"name": "sentence-transformers/all-MiniLM-L6-v2", "type": "huggingface"},
        {"name": "intfloat/multilingual-e5-large-instruct", "type": "huggingface"},
        {"name": "BAAI/BGE-M3", "type": "huggingface"},
    ]
    for model in models:
        save_to_faiss(chunks, model["name"], model["type"])

def load_documents():
    """Loads .pdf and .txt documents from the data directory."""
    documents = []
    
    # Load .pdf files
    pdf_files = [os.path.join(DATA_PATH, f) for f in os.listdir(DATA_PATH) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        with open(pdf_file, "rb") as f:
            pdf = pypdf.PdfReader(f)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            documents.append(Document(page_content=text, metadata={"source": pdf_file}))
    
    # Load .txt files
    txt_files = [os.path.join(DATA_PATH, f) for f in os.listdir(DATA_PATH) if f.endswith('.txt')]
    for txt_file in txt_files:
        with open(txt_file, "r", encoding="utf-8") as file:
            text = file.read()
            documents.append(Document(page_content=text, metadata={"source": txt_file}))
    
    return documents

def split_text(documents: list[Document]):
    """Splits documents into chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=250,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def save_to_faiss(chunks: list[Document], model_name: str, model_type: str):
    """Saves document chunks to a model-specific FAISS vector index and measures latency."""
    # FAISS path for each model
    faiss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'faiss', model_name.replace('/', '_'))
    
    if os.path.exists(faiss_path):
        shutil.rmtree(faiss_path)
    
    if model_type == "openai":
        embeddings = OpenAIEmbeddings(model=model_name)
    elif model_type == "huggingface":
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")
    
    start_time = time.time()
    db = FAISS.from_documents(chunks, embeddings)
    end_time = time.time()
    
    db.save_local(faiss_path)
    
    # Total and average time
    total_time = end_time - start_time
    num_chunks = len(chunks)
    average_time_per_chunk = total_time / num_chunks if num_chunks > 0 else 0
    
    # Log results
    logger = logging.getLogger()
    logger.info(f"Saved {num_chunks} chunks to FAISS index at {faiss_path}.")
    logger.info(f"Time to generate embeddings for {model_name}: {total_time:.2f} seconds")
    logger.info(f"Average time per chunk: {average_time_per_chunk:.4f} seconds")
    logger.info("")

if __name__ == "__main__":
    main()