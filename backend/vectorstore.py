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

    # Load dataset
    dataset = load_dataset("urnus11/Vietnamese-Healthcare")
    documents = []
    split_name = "medical_qa"
    split_data = dataset[split_name]
    total_rows = len(split_data)
    train_size = int(total_rows * split_ratio)
    print(f"Using training subset of {split_name}: first {train_size}/{total_rows} rows")
    
    # Process the training set (first split_ratio portion of data)
    for idx in tqdm(range(train_size), desc="Processing documents", leave=False):
        item = split_data[idx]
        title = item['title']
        content = item['content']
        source = item['url']
        
        doc = Document(
            page_content=f"Question: {title}\n\nAnswer: {content}",
            metadata={
                "split": split_name,
                "index": idx,
                "source": source,
                "title": title,
            }
        )
        documents.append(doc)
    
    print(f"Documents extracted: {len(documents)}")
    
    # Use a text splitter to preserve question-answer relationships
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
        keep_separator=False
    )
    
    final_docs = []
    
    # Split documents
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
            new_doc = Document(
                page_content=f"{question_part}\n\nAnswer: {chunk}",
                metadata={
                    **doc.metadata,
                    "chunk": i,
                    "chunk_count": len(answer_chunks)
                }
            )
            final_docs.append(new_doc)

    print(f"Created {len(final_docs)} chunks")

    embeddings = OpenAIEmbeddings(model=model_name)
    
    # Create vector store output directory
    backend_dir = Path(__file__).parent.absolute()
    model_base_folder = os.path.join(backend_dir, "faiss", f"{model_name}")
    model_folder = os.path.join(model_base_folder, f"chunk_size_{chunk_size}")
    os.makedirs(model_folder, exist_ok=True)
    
    # Create vectorstore
    print(f"Creating vector store with chunk_size={chunk_size}, processing {len(final_docs)} chunks in batches of {batch_size}...")
    total_chunks = len(final_docs)
    
    # Batch processing
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
        
        # Save intermediate results
        if (i // batch_size) % 5 == 0 and i > 0:
            vectorstore.save_local(model_folder)
            elapsed = time.time() - start_time
            progress = f"{i+len(batch)}/{total_chunks}"
            print(f"\n✓ Updated checkpoint at {progress} chunks - {elapsed:.1f} seconds elapsed")
    
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
    
    model_name = args.model
    chunk_size = args.chunk_size
    batch_size = args.batch_size
    split_ratio = args.split_ratio
    total_start_time = time.time()
    
    # Create vector store
    print(f"Starting vector store creation for training data (first {split_ratio*100:.0f}% of data)...")
    vectorstore, model_folder = create_vector_store(model_name, chunk_size, batch_size, split_ratio)
    
    # Save final vector store
    print(f"Saving final vector store to {model_folder}...")
    vectorstore.save_local(model_folder)
    total_time = time.time() - total_start_time
    print(f"Process completed in {total_time:.1f} seconds")