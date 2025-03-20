import os
import fitz
import numpy as np
import faiss
import pickle
import openai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF."""
    doc = fitz.open(pdf_path)
    return "".join(page.get_text("text") for page in doc)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list:
    """Split text into chunks with overlap."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

def generate_embedding(text: str) -> np.ndarray:
    """Generate embedding for text using OpenAI's new API."""
    response = openai.embeddings.create(input=[text], model="text-embedding-ada-002")
    embedding = response.data[0].embedding
    return np.array(embedding)

def index_documents(pdf_dir: str) -> tuple[faiss.IndexFlatL2, list[str]]:
    """Index all PDFs in the directory and return FAISS index and texts."""
    embeddings, texts = [], []
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            pdf_text = extract_text_from_pdf(pdf_path)
            chunks = chunk_text(pdf_text)
            texts.extend(chunks)
            embeddings.extend([generate_embedding(chunk) for chunk in chunks])
    
    embeddings = np.array(embeddings).astype('float32')
    faiss_index = faiss.IndexFlatL2(embeddings.shape[1])
    faiss_index.add(embeddings)
    return faiss_index, texts

if __name__ == "__main__":
    pdf_dir = os.path.join(os.path.dirname(__file__), "data")
    faiss_index, texts = index_documents(pdf_dir)
    faiss.write_index(faiss_index, "faiss_index.bin")
    with open("texts.pkl", "wb") as f:
        pickle.dump(texts, f)
    print("Vector database saved as 'faiss_index.bin' and 'texts.pkl'.")
