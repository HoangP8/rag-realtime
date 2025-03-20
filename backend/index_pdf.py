import os
import fitz
import numpy as np
import faiss
import pickle
import openai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF."""
    doc = fitz.open(pdf_path)
    return "".join(page.get_text("text") for page in doc)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list:
    """Split text into chunks with overlap."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]

def generate_embedding(text: str, model_name: str) -> np.ndarray:
    """Generate embedding for text using OpenAI's embedding API."""
    response = openai.embeddings.create(input=[text], model=model_name)
    embedding = response.data[0].embedding
    return np.array(embedding)

def index_documents(pdf_dir: str, model_name: str) -> tuple[faiss.IndexFlatL2, list[str]]:
    """Index all PDFs in the directory and return FAISS index and texts."""
    embeddings, texts = [], []
    for pdf_file in os.listdir(pdf_dir):
        if pdf_file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, pdf_file)
            pdf_text = extract_text_from_pdf(pdf_path)
            chunks = chunk_text(pdf_text)
            texts.extend(chunks)
            embeddings.extend([generate_embedding(chunk, model_name) for chunk in chunks])
    
    embeddings = np.array(embeddings).astype('float32')
    faiss_index = faiss.IndexFlatL2(embeddings.shape[1])
    faiss_index.add(embeddings)
    return faiss_index, texts


if __name__ == "__main__":
    # list of openai embedding models
    model_names = ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"] 
    pdf_dir = os.path.join(os.path.dirname(__file__), "data")

    for model_name in model_names:
        
        model_folder = os.path.join("faiss", model_name)
        os.makedirs(model_folder, exist_ok=True)

        faiss_index, texts = index_documents(pdf_dir, model_name)

        # save the FAISS index
        faiss.write_index(faiss_index, os.path.join(model_folder, f"faiss_index_{model_name}.bin"))
        with open(os.path.join(model_folder, f"texts_{model_name}.pkl"), "wb") as f: 
            pickle.dump(texts, f)

        print(f"Vector database saved in '{model_folder}' as 'faiss_index_{model_name}.bin' and 'texts_{model_name}.pkl'.")
