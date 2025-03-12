import argparse
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from livekit.plugins import openai as livekit_openai


CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

def main():
    """Handles CLI input and processes the query."""
    parser = argparse.ArgumentParser()
    parser.add_argument("embedding_model", type=str, help="The embedding model name.")
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    process_query(args.embedding_model, args.query_text)


def process_query(embedding_model: str, query_text: str):
    """Processes the query by searching the vector database and generating a response."""
    db = load_chroma_db(embedding_model)
    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    
    if not results or results[0][1] < 0.7:
        print("Unable to find matching results.")
        return
    
    response = generate_response(query_text, results)
    print(response)


def load_chroma_db(embedding_model: str):
    """Loads the Chroma vector database for the specified embedding model."""
    chroma_path = f"chroma/{embedding_model.replace('/', '_')}"
    embedding_function = get_embedding_function(embedding_model)
    return Chroma(persist_directory=chroma_path, embedding_function=embedding_function)

def get_embedding_function(model_name: str):
    """Returns the appropriate embedding function based on the model name."""
    if '/' in model_name:
        return HuggingFaceEmbeddings(model_name=model_name)  # Hugging Face model
    else:
        return OpenAIEmbeddings(model=model_name)

def generate_response(query_text: str, results):
    """Generates a response based on retrieved documents using the realtime model."""
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    model = livekit_openai.realtime.RealtimeModel(
        instructions="You are a helpful assistant that is specialized for medical queries. Please start the conversation with the user by asking them how they are feeling.",
        voice="echo",
        temperature=0.8,
        modalities=["audio", "text"],
    )
    response_text = model.predict(prompt)  # Assuming predict method exists; adjust if needed
    sources = [doc.metadata.get("source", "Unknown") for doc, _ in results]
    
    return f"Response: {response_text}\nSources: {sources}"

if __name__ == "__main__":
    main()
