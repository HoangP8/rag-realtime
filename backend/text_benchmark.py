import os
import time
import argparse
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from tqdm.asyncio import tqdm_asyncio
import random

from datasets import load_dataset, Dataset
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from ragas import evaluate
from ragas.metrics import AnswerRelevancy, AnswerCorrectness, AnswerSimilarity, ContextRecall, ContextPrecision, Faithfulness

# Basic setup
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)
metrics_logger = logging.getLogger("metrics")
metrics_logger.setLevel(logging.INFO)
metrics_handler = logging.FileHandler(logs_dir / "text_metrics.log")
metrics_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
metrics_logger.addHandler(metrics_handler)
qa_logger = logging.getLogger("qa_logs")
qa_logger.setLevel(logging.INFO)
qa_handler = logging.FileHandler(logs_dir / "text_qa_results.log")
qa_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
qa_logger.addHandler(qa_handler)

# Configuration
default_model_name = "text-embedding-3-small"
default_chunk_size = 1024
default_split_ratio = 0.8
default_generator_model = "gpt-4o"
default_k = 3
default_score_threshold = 0.35
default_max_test_samples = 100 # set to None to run all
random.seed(0)

template_prompt = """
You are a HEALTHCARE ASSISTANT.
Your ONLY purpose is to provide healthcare and medical information.
You can ONLY work (understand, speak, and answer) in one language: Vietnamese.
Do NOT work on other languages, they are maybe noise from the user that you mistranslate.
Be CONCISE and SMOOTH in your responses without hesitation, no need to repeat the same thing over and over again.

IMPORTANT RULES:
1. ONLY answer healthcare/medical questions. For ANY other topics, politely refuse and remind the user
that you are a dedicated healthcare assistant, EVEN they ask about your health or other conditions.
2. Be clear, accessible, and concise in your explanations.
"""

def load_dataset_split(split_ratio: float, max_samples: int | None = None, is_train: bool = False) -> Dataset:
    """Dataset loading function"""
    dataset = load_dataset("urnus11/Vietnamese-Healthcare")["medical_qa"]
    
    if max_samples and max_samples < len(dataset):
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    
    splits = dataset.train_test_split(train_size=split_ratio, seed=0)
    return splits["train"] if is_train else splits["test"]


def load_vectorstore(model_name: str, chunk_size: int):
    """Load FAISS vector store from disk."""
    start_time = time.time()
    backend_dir = Path(__file__).parent.absolute()
    model_base_folder = os.path.join(backend_dir, "faiss", f"{model_name}")
    model_folder = os.path.join(model_base_folder, f"chunk_size_{chunk_size}")

    logger.info(f"Loading vectorstore from: {model_folder}")
    embeddings = OpenAIEmbeddings(model=model_name)
    vectorstore = FAISS.load_local(model_folder, embeddings, allow_dangerous_deserialization=True)
    load_time = time.time() - start_time
    logger.info(f"Vector store loaded in {load_time:.2f} seconds")
    return vectorstore, embeddings


async def generate_answers(dataset: Dataset, vectorstore: FAISS = None, llm: ChatOpenAI = None, 
                           k: int = 3, score_threshold: float = 0.35, use_rag: bool = True):
    """Unified answer generation function for both RAG and non-RAG approaches"""
    results = []
    
    async def process_item(item):
        question = item['question']
        ground_truth = item['ground_truth']
        
        # Only retrieve contexts if using RAG
        contexts = []
        if use_rag and vectorstore:
            retrieved_docs = vectorstore.similarity_search_with_relevance_scores(
                question, k=k, score_threshold=score_threshold
            )
            contexts = [doc.page_content for doc, score in retrieved_docs]
        
        # Prepare prompt based on whether we have contexts
        system_prompt = template_prompt
        if contexts:
            context_str = "\n\n---\n\n".join([f"RAG information {i+1}:\n{ctx}" for i, ctx in enumerate(contexts)])
            system_prompt += f"\n\nHướng dẫn: Đây là thông tin từ cơ sở dữ liệu y tế Việt Nam. \n{context_str}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"}
        ]
        
        # Generate answer
        response = await llm.ainvoke(messages)
        answer = response.content
        
        # Log results
        qa_logger.info(f"QUESTION: {question}")
        if contexts:
            for i, ctx in enumerate(contexts):
                qa_logger.info(f"CONTEXT {i+1}: {ctx}")
        qa_logger.info(f"{'RAG' if use_rag else 'BASELINE'} ANSWER: {answer}")
        qa_logger.info("-" * 80)
        
        return {
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": ground_truth
        }
    
    tasks = [process_item(item) for item in dataset]
    results = await tqdm_asyncio.gather(*tasks, desc=f"Generating {'RAG' if use_rag else 'Baseline'} Answers")
    return Dataset.from_list(results)


async def evaluate_dataset(dataset: Dataset, llm: ChatOpenAI, embeddings: OpenAIEmbeddings, dataset_name: str):
    """Evaluate a dataset with RAGAS metrics."""
    logger.info(f"Starting RAGAS evaluation for {dataset_name}...")
    evaluation_start_time = time.time()
    
    # Define metrics
    metrics = [
        Faithfulness(),        # How factual is the answer based on context?
        AnswerRelevancy(),     # How relevant is the answer to the question? (Uses LLM)
        ContextPrecision(),    # Signal-to-noise ratio of retrieved context. (Uses LLM)
        ContextRecall(),       # How much of the ground truth is covered by the context?
        AnswerSimilarity(),    # Semantic similarity between answer and ground truth.
        AnswerCorrectness(),   # Factual correctness compared to ground truth. (Uses LLM)
    ]
    
    result = evaluate(
        dataset,
        metrics=metrics,
        llm=llm, 
        embeddings=embeddings
    )
    
    evaluation_time = time.time() - evaluation_start_time
    logger.info(f"RAGAS evaluation for {dataset_name} completed in {evaluation_time:.2f} seconds.")
    return result


async def run_benchmark(args):
    """Main benchmarking function."""
    start_run_time = time.time()
    
    # Log hyperparameters
    metrics_logger.info(f"BENCHMARK RUN - Parameters: model={args.model}, chunk_size={args.chunk_size}, "
                       f"split_ratio={args.split_ratio}, generator_model={args.generator_model}, "
                       f"k={args.k}, score_threshold={args.score_threshold}, max_samples={args.max_samples}")

    # Load Train (ID) and Test (OOD) Data
    train_dataset = load_dataset_split(args.split_ratio, max_samples=args.max_samples, is_train=True)
    test_dataset = load_dataset_split(args.split_ratio, max_samples=args.max_samples, is_train=False)
    
    # Load Vector Store
    vectorstore, embeddings = load_vectorstore(args.model, args.chunk_size)

    # Initialize LLM and Embeddings
    llm = ChatOpenAI(model=args.generator_model, temperature=0.7) 

    # Generate Baseline Answers (without RAG)
    train_baseline_dataset = await generate_answers(
        dataset=train_dataset, 
        llm=llm, 
        use_rag=False,
    )
    
    test_baseline_dataset = await generate_answers(
        dataset=test_dataset, 
        llm=llm, 
        use_rag=False,
    )
    
    # Generate RAG Answers
    train_rag_dataset = await generate_answers(
        dataset=train_dataset, 
        llm=llm, 
        vectorstore=vectorstore, 
        k=args.k, 
        score_threshold=args.score_threshold, 
        use_rag=True,
    )
    
    test_rag_dataset = await generate_answers(
        dataset=test_dataset, 
        llm=llm, 
        vectorstore=vectorstore, 
        k=args.k, 
        score_threshold=args.score_threshold, 
        use_rag=True,
    )
    
    results = {}
    
    # Evaluate baseline (no RAG)
    results["train_baseline"] = await evaluate_dataset(
        train_baseline_dataset, llm, embeddings, "Train Baseline (No RAG)"
    )
    results["test_baseline"] = await evaluate_dataset(
        test_baseline_dataset, llm, embeddings, "Test Baseline (No RAG)"
    )
    
    # Evaluate with RAG
    results["train_rag"] = await evaluate_dataset(
        train_rag_dataset, llm, embeddings, "Train RAG"
    )
    results["test_rag"] = await evaluate_dataset(
        test_rag_dataset, llm, embeddings, "Test RAG"
    )

    # Display and Log Results
    print("\n--- RAGAS Evaluation Results ---")
    for name, result in results.items():
        print(f"\n{name.upper()} RESULTS:")
        print(result)
        metrics_logger.info(f"RESULTS - {name}: {result.to_dict()}")
    print("---------------------------------")

    # Save results to CSV files
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    for name, result in results.items():
        results_df = result.to_pandas()
        output_filename = f"benchmark_{name}_{args.generator_model}_{args.model}_cs{args.chunk_size}_k{args.k}_t{args.score_threshold}_{timestamp}.csv"
        output_path = Path(__file__).parent / output_filename
        results_df.to_csv(output_path, index=False)
        logger.info(f"{name.capitalize()} results saved to: {output_path}")
        metrics_logger.info(f"CSV SAVED - {name}: {output_path}")

    # Create a summary comparison table
    summary_data = {}
    for name, result in results.items():
        result_dict = result.to_dict()
        for metric, value in result_dict.items():
            summary_data.setdefault(metric, {})[name] = value
    summary_df = pd.DataFrame(summary_data)
    summary_path = Path(__file__).parent / f"benchmark_summary_{timestamp}.csv"
    summary_df.to_csv(summary_path)
    logger.info(f"Summary comparison saved to: {summary_path}")
    metrics_logger.info(f"SUMMARY SAVED: {summary_path}")
    total_run_time = time.time() - start_run_time
    logger.info(f"Benchmarking finished in {total_run_time:.2f} seconds.")
    metrics_logger.info(f"BENCHMARK COMPLETED - Total runtime: {total_run_time:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark RAG system using RAGAS")

    parser.add_argument("--model", type=str, default=default_model_name,
                        choices=["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
                        help="Embedding model used for vector store.")
    parser.add_argument("--chunk_size", type=int, default=default_chunk_size,
                        help="Chunk size used for vector store.")
    parser.add_argument("--split_ratio", type=float, default=default_split_ratio,
                        help="Train/test split ratio used when creating the vector store (to load the correct test set).")
    parser.add_argument("--generator_model", type=str, default=default_generator_model,
                        help="OpenAI model used to generate answers (e.g., gpt-4o, gpt-3.5-turbo).")
    parser.add_argument("--k", type=int, default=default_k,
                        help="Number of documents to retrieve.")
    parser.add_argument("--score_threshold", type=float, default=default_score_threshold,
                        help="Relevance score threshold for retrieved documents.")
    parser.add_argument("--max_samples", type=int, default=default_max_test_samples,
                        help="Maximum number of test samples to run (for quick testing). Set to 0 or negative for all.")

    args = parser.parse_args()

    # Run the benchmark asynchronously
    asyncio.run(run_benchmark(args))