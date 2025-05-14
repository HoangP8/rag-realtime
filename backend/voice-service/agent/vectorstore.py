import os
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from datasets import load_dataset
from langchain_core.documents import Document
from tqdm import tqdm

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

def create_vector_store(model_name: str, chunk_size: int = 512, batch_size: int = 10000, split_ratio: float = 0.8) -> FAISS:
    """Create vector store from the training portion of medical_qa split of Vietnamese Healthcare dataset."""

    # Load dataset and training portion
    dataset = load_dataset("urnus11/Vietnamese-Healthcare")["medical_qa"]
    total_rows = len(dataset)
    train_size = int(total_rows * split_ratio)
    print(f"Using training subset: first {train_size}/{total_rows} rows")
    
    # Process the training set
    documents = []
    for idx in tqdm(range(train_size), desc="Processing documents"):
        item = dataset[idx]
        documents.append(Document(
            page_content=f"Question: {item['title']}\n\nAnswer: {item['content']}",
            metadata={
                "split": "medical_qa",
                "index": idx,
                "source": item['url'],
                "title": item['title'],
            }
        ))
    
    print(f"Documents extracted: {len(documents)}")
    
    # Set up text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
        keep_separator=False
    )
    
    # Split documents
    final_docs = []
    for doc in tqdm(documents, desc="Chunking documents", leave=False):
        content = doc.page_content
        
        # Skip chunking for documents shorter than chunk size
        if len(content) <= chunk_size:
            final_docs.append(doc)
            continue
        
        # Extract question and answer parts
        question_part = content[:content.find("Answer:")].strip()
        answer_part = content[content.find("Answer:") + 7:].strip()
        
        # Split answer into chunks
        answer_chunks = text_splitter.split_text(answer_part)
        
        # Create new documents with question + chunked answers
        for i, chunk in enumerate(answer_chunks):
            final_docs.append(Document(
                page_content=f"{question_part}\n\nAnswer: {chunk}",
                metadata={**doc.metadata, "chunk": i, "chunk_count": len(answer_chunks)}
            ))

    print(f"Created {len(final_docs)} chunks")

    # Set up embedding model in batches
    embeddings = OpenAIEmbeddings(model=model_name)
    model_folder = Path(__file__).parent / "faiss" / model_name / f"chunk_size_{chunk_size}"
    model_folder.mkdir(parents=True, exist_ok=True)
    
    # Create vectorstore in batches
    print(f"Creating vector store with chunk_size={chunk_size}, processing {len(final_docs)} chunks in batches of {batch_size}...")
    total_chunks = len(final_docs)
    
    vectorstore = None
    progress_bar = tqdm(total=total_chunks, desc="Processing", leave=True)
    start_time = time.time()

    for i in range(0, total_chunks, batch_size):
        batch_end = min(i + batch_size, total_chunks)
        batch = final_docs[i:batch_end]
        
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embeddings)
        else:
            vs_batch = FAISS.from_documents(batch, embeddings)
            vectorstore.merge_from(vs_batch)
        
        progress_bar.update(len(batch))
        
        # Save checkpoint every 5 batches
        if (i // batch_size) % 5 == 0 and i > 0:
            vectorstore.save_local(model_folder)
            elapsed = time.time() - start_time
            progress = f"{i+len(batch)}/{total_chunks}"
            print(f"\nUpdated checkpoint at {progress} chunks - {elapsed:.1f} seconds elapsed")
    progress_bar.close()
    
    return vectorstore, model_folder


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create vector store with different configurations")
    parser.add_argument("--model", type=str, default="text-embedding-3-small",
                        choices=["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
                        help="Embedding model to use")
    parser.add_argument("--chunk_size", type=int, default=1024,
                        help="Size of text chunks for splitting documents")
    parser.add_argument("--batch_size", type=int, default=10000,
                        help="Number of documents to process in each batch")
    parser.add_argument("--split_ratio", type=float, default=0.8,
                        help="Ratio for train data (default: 0.8)")
    
    args = parser.parse_args()
    total_start_time = time.time()
    
    # Create and save vector store
    print(f"Starting vector store creation for training data (first {args.split_ratio*100:.0f}% of data)...")
    vectorstore, model_folder = create_vector_store(
        args.model, args.chunk_size, args.batch_size, args.split_ratio
    )
    
    print(f"Saving final vector store to {model_folder}...")
    vectorstore.save_local(str(model_folder))
    print(f"Process completed in {time.time() - total_start_time:.1f} seconds")