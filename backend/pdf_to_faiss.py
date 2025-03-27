import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")


def create_vector_store(pdf_dir: Path, model_name: str) -> FAISS:
    """Create vector store from PDF documents using specified embedding model."""

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    pdf_dir = Path(pdf_dir)
    
    # Track PDF processing
    documents = []
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"\nProcessing {len(pdf_files)} PDF files...")
    
    for pdf_file in pdf_files:
        print(f"Loading: {pdf_file.name}")
        docs = PyPDFLoader(str(pdf_file)).load()
        documents.extend(docs)
        print(f"  - Pages: {len(docs)}")
    
    print(f"\nTotal pages across all PDFs: {len(documents)}")
    
    splits = text_splitter.split_documents(documents)
    print(f"Total chunks after splitting: {len(splits)}")
    print(f"Creating embeddings using model: {model_name}\n")
    
    embeddings = OpenAIEmbeddings(model=model_name)
    return FAISS.from_documents(splits, embeddings)


if __name__ == "__main__":
    # test different OpenAI embedding models
    model_names = [
        "text-embedding-ada-002",
        "text-embedding-3-small",
        "text-embedding-3-large"
    ]
    
    backend_dir = Path(__file__).parent.absolute()
    pdf_dir = os.path.join(backend_dir, "data")
    
    # Process each model
    for model_name in model_names:
        model_folder = os.path.join("faiss", model_name)
        os.makedirs(model_folder, exist_ok=True)
        
        # save vector store
        vectorstore = create_vector_store(pdf_dir, model_name)
        vectorstore.save_local(model_folder)
        print(f"Vector store for model '{model_name}' saved in '{model_folder}'")