from __future__ import annotations
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv(dotenv_path=".env.local")

def test_rag_with_pdf():
    # Load PDFs directly from your repo
    pdf_folder = "medical_pdfs"
    print(f"Loading PDFs from {pdf_folder}")
    loader = PyPDFDirectoryLoader(pdf_folder)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} PDFs into {len(chunks)} chunks")

    # Create in-memory vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Define retrieval function
    def retrieve_medical_info(query: str) -> str:
        docs = retriever.get_relevant_documents(query)
        print(f"Retrieved {len(docs)} documents for query: '{query}'")
        for i, doc in enumerate(docs, 1):
            print(f"Document {i}: {doc.page_content[:500]}...")
        return "\n\n".join([doc.page_content for doc in docs])

    # Test with a sample query
    test_query = "What’s the treatment for a headache?"  # Adjust based on your PDF content
    result = retrieve_medical_info(test_query)
    print(f"Full result passed to model:\n{result}")

if __name__ == "__main__":
    test_rag_with_pdf()