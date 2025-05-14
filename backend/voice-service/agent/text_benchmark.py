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
from ragas.metrics import AnswerRelevancy, AnswerCorrectness, ContextRecall, ContextPrecision, Faithfulness

# Basic setup
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logs_dir = Path(__file__).parent / "logs" / "text_benchmark_logs"
logs_dir.mkdir(parents=True, exist_ok=True)
metrics_logger = logging.getLogger("metrics")
metrics_logger.setLevel(logging.INFO)
qa_logger = logging.getLogger("qa_logs")
qa_logger.setLevel(logging.INFO)

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
    """Split max_samples from the dataset, split by train/test"""
    dataset = load_dataset("urnus11/Vietnamese-Healthcare")["medical_qa"]
    
    # Split the dataset 
    total_rows = len(dataset)
    train_size = int(total_rows * split_ratio)
    split_dataset = dataset.select(range(train_size)) if is_train else dataset.select(range(train_size, total_rows))
    
    # Randomly sample max_samples
    if max_samples is not None and max_samples > 0 and max_samples < len(split_dataset):
        indices = random.sample(range(len(split_dataset)), min(max_samples, len(split_dataset)))
        return split_dataset.select(indices)
    return split_dataset


def load_vectorstore(model_name: str, chunk_size: int):
    """Load FAISS vector store from disk."""
    start_time = time.time()
    backend_dir = Path(__file__).parent.absolute()
    model_folder = os.path.join(backend_dir, "faiss", f"{model_name}", f"chunk_size_{chunk_size}")

    logger.info(f"Loading vectorstore from: {model_folder}")
    embeddings = OpenAIEmbeddings(model=model_name)
    vectorstore = FAISS.load_local(model_folder, embeddings, allow_dangerous_deserialization=True)
    logger.info(f"Vector store loaded in {time.time() - start_time:.2f}s")
    return vectorstore, embeddings


async def generate_answers(dataset: Dataset, vectorstore: FAISS = None, llm: ChatOpenAI = None, 
                           k: int = 3, score_threshold: float = 0.35, use_rag: bool = True):
    """
    Answer generation function for both RAG and non-RAG approaches
    Return:
    - Dataset with with keys: 'question', 'answer', 'contexts', 'ground_truth'
    """
    
    results = []
    async def process_item(item):
        question = item['title']
        ground_truth = item['content']
        
        # Only retrieve contexts if using RAG
        contexts = []
        if use_rag and vectorstore:
            retrieved_docs = vectorstore.similarity_search_with_relevance_scores(
                question, k=k, score_threshold=score_threshold
            )
            contexts = [doc.page_content for doc, score in retrieved_docs]
        
        # Prepare prompt based on whether we have contexts
        system_prompt = template_prompt
        if contexts != []:
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
        if contexts != []:
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


async def evaluate_dataset(dataset: Dataset, dataset_name: str):
    """Evaluate a dataset with RAGAS metrics."""
    logger.info(f"Starting RAGAS evaluation for {dataset_name}...")
    evaluation_start_time = time.time()
    
    # Define metrics
    metrics = [
        Faithfulness(),        # Answer's factual consistency with the contexts.
        AnswerRelevancy(),     # Answer's relevance to the question
        ContextPrecision(),    # Relevance of retrieved context
        ContextRecall(),       # Coverage of ground truth by context
        AnswerCorrectness(),   # Factual accuracy compared to ground truth
    ]
    
    # Run evaluation
    result = evaluate(dataset=dataset, metrics=metrics)
    evaluation_time = time.time() - evaluation_start_time
    logger.info(f"RAGAS evaluation for {dataset_name} completed in {evaluation_time:.2f} seconds.")
    return result


async def run_benchmark(args):
    """Main benchmarking function."""
    start_run_time = time.time()

    # Create directory for logs
    model_dir = logs_dir / f"k_{args.k}_chunk_size_{args.chunk_size}_{args.model}"
    model_dir.mkdir(exist_ok=True)
    
    metrics_handler = logging.FileHandler(model_dir / "text_metrics.log", encoding="utf-8")
    metrics_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    metrics_logger.addHandler(metrics_handler)

    qa_handler = logging.FileHandler(model_dir / "text_qa_results.log", encoding="utf-8")
    qa_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    qa_logger.addHandler(qa_handler)

    metrics_logger.info(f"BENCHMARK RUN - Parameters: model={args.model}, chunk_size={args.chunk_size}, "
                       f"split_ratio={args.split_ratio}, llm={args.llm}, "
                       f"k={args.k}, score_threshold={args.score_threshold}, max_samples={args.max_samples}")
    
    # Load Train (ID) and Test (OOD) Data
    train_dataset = load_dataset_split(args.split_ratio, max_samples=args.max_samples, is_train=True)
    test_dataset = load_dataset_split(args.split_ratio, max_samples=args.max_samples, is_train=False)
    
    # Load Vector Store
    vectorstore, embeddings = load_vectorstore(args.model, args.chunk_size)

    # Initialize LLM
    llm = ChatOpenAI(model=args.llm, temperature=0.7) 

    # Run experiments
    datasets = {
        "train_baseline": await generate_answers(train_dataset, llm=llm, use_rag=False),
        "test_baseline": await generate_answers(test_dataset, llm=llm, use_rag=False),
        "train_rag": await generate_answers(train_dataset, llm=llm, vectorstore=vectorstore, 
                                         k=args.k, score_threshold=args.score_threshold, use_rag=True),
        "test_rag": await generate_answers(test_dataset, llm=llm, vectorstore=vectorstore, 
                                        k=args.k, score_threshold=args.score_threshold, use_rag=True)
    }
    
    # Evaluate all datasets
    results = {name: await evaluate_dataset(dataset, name) for name, dataset in datasets.items()}

    # Log results
    for name, result in results.items():
        metrics_logger.info(f"RESULTS - {name}: {result}")
    
    # Create summary dataframe
    summary_data = {}
    for name, result in results.items():
        numeric_df = result.to_pandas().select_dtypes(include=['number'])
        for metric, score in numeric_df.iloc[0].to_dict().items():
            summary_data.setdefault(metric, {})[name] = score
    
    # Save summary in csv file
    summary_df = pd.DataFrame(summary_data)
    summary_path = model_dir / "summary.csv"
    summary_df.to_csv(summary_path) 
    logger.info(f"Summary comparison saved to: {summary_path}")
    metrics_logger.info(f"SUMMARY SAVED: {summary_path}")

    # Log completion
    total_run_time = time.time() - start_run_time
    logger.info(f"Benchmarking finished in {total_run_time:.2f} seconds.")
    metrics_logger.info(f"BENCHMARK COMPLETED - Total runtime: {total_run_time:.2f} seconds")
    metrics_logger.removeHandler(metrics_handler)
    qa_logger.removeHandler(qa_handler)

if __name__ == "__main__":
    # Configuration
    parser = argparse.ArgumentParser(description="Benchmark RAG system using RAGAS")
    parser.add_argument("--model", type=str, default="text-embedding-3-small",
                        choices=["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
                        help="Embedding model used for vector store.")
    parser.add_argument("--chunk_size", type=int, default=1024,
                        help="Chunk size used for vector store.")
    parser.add_argument("--split_ratio", type=float, default=0.8,
                        help="Train/test split ratio.")
    parser.add_argument("--llm", type=str, default="gpt-4o",
                        help="OpenAI model used to generate answers.")
    parser.add_argument("--k", type=int, default=3,
                        help="Number of documents to retrieve.")
    parser.add_argument("--score_threshold", type=float, default=0.35,
                        help="Relevance score threshold for retrieved documents.")
    parser.add_argument("--max_samples", type=int, default=100,
                        help="Maximum number of test samples to run. Set to 0 for all.")

    args = parser.parse_args()
    random.seed(0)
    
    # Run the benchmark
    asyncio.run(run_benchmark(args))