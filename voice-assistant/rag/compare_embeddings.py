from langchain_openai import OpenAIEmbeddings
from langchain.evaluation import load_evaluator
from dotenv import load_dotenv
import openai
import os

load_dotenv()
openai.api_key = os.environ['OPENAI_API_KEY']

def main():
    """Generates and evaluates embeddings for words."""
    generate_embeddings()
    compare_embeddings("apple", "iphone")

def generate_embeddings():
    """Gets and prints the embedding vector for a word."""
    embedding_function = OpenAIEmbeddings()
    vector = embedding_function.embed_query("apple")
    print(f"Vector for 'apple': {vector}")
    print(f"Vector length: {len(vector)}")

def compare_embeddings(word1: str, word2: str):
    """Compares embeddings of two words using pairwise distance."""
    evaluator = load_evaluator("pairwise_embedding_distance")
    similarity_score = evaluator.evaluate_string_pairs(prediction=word1, prediction_b=word2)
    print(f"Comparing ({word1}, {word2}): {similarity_score}")

if __name__ == "__main__":
    main()
