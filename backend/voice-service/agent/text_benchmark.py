import time
import argparse
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
from tqdm.asyncio import tqdm_asyncio
import random
from typing import List, Dict, Tuple
import numpy as np

from datasets import load_dataset, Dataset
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.documents import Document
from ragas import evaluate
from ragas.metrics import AnswerRelevancy, AnswerCorrectness, ContextRecall, ContextPrecision, Faithfulness

# Basic setup
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env.local")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logs_dir = Path(__file__).parent / "logs" / "text_benchmark_logs"
logs_dir.mkdir(parents=True, exist_ok=True)

PARAPHRASE_PROMPTS = {
    "vietnamese": """
Viết lại câu hỏi sau bằng TIẾNG VIỆT với cách diễn đạt khác nhưng giữ nguyên ý nghĩa.
Có thể thay đổi từ ngữ, cấu trúc câu, hoặc thêm bối cảnh cụ thể.

Câu gốc: {question}

Câu viết lại:""",
    
    "english": """
Rewrite this question in ENGLISH using different words or structure while keeping the same meaning.
You may use synonyms, change grammar, or add specific context.

Original: {question}

Rewritten:"""
}

SYSTEM_PROMPT = """
You are a HEALTHCARE ASSISTANT.
Your ONLY purpose is to provide healthcare and medical information.
"""

# Fixed Self-RAG prompts
SELF_RAG_REFLECTION_PROMPT = """
You are evaluating the relevance of retrieved medical information for answering a healthcare question.

Question: {question}

Retrieved Context: {context}

Evaluate this context's relevance and respond with EXACTLY one of these:
- RELEVANT: The context directly addresses the question and provides useful medical information
- PARTIALLY_RELEVANT: The context is related to the medical topic but doesn't fully answer the question
- IRRELEVANT: The context is not related to the question or medical topic

Evaluation:"""

SELF_RAG_GENERATION_PROMPT = """
You are a healthcare assistant. Answer the question using only the relevant medical information provided below.

Question: {question}

Relevant Medical Information:
{evaluated_contexts}

Instructions:
- Base your answer strictly on the provided medical information
- If the information is insufficient, clearly state this limitation
- Provide accurate, evidence-based healthcare guidance
- Do not make assumptions beyond the provided context

Answer:"""

def load_dataset_split(split_ratio: float, max_samples: int = None) -> Dataset:
    """Load dataset samples from train split."""
    dataset = load_dataset("urnus11/Vietnamese-Healthcare")["medical_qa"]
    total_rows = len(dataset)
    train_size = int(total_rows * split_ratio)
    train_dataset = dataset.select(range(train_size))
    
    if max_samples and max_samples < len(train_dataset):
        indices = random.sample(range(len(train_dataset)), max_samples)
        return train_dataset.select(indices)
    return train_dataset

def load_vectorstore(model_name: str, chunk_size: int) -> Tuple[FAISS, OpenAIEmbeddings]:
    """Load FAISS vector store from disk."""
    backend_dir = Path(__file__).parent.absolute()
    model_folder = backend_dir / "faiss" / model_name / f"chunk_size_{chunk_size}"
    
    logger.info(f"Loading vectorstore from: {model_folder}")
    embeddings = OpenAIEmbeddings(model=model_name)
    vectorstore = FAISS.load_local(str(model_folder), embeddings, allow_dangerous_deserialization=True)
    logger.info("Vector store loaded successfully")
    return vectorstore, embeddings

def paraphrase_logging(model_dir: Path) -> logging.Logger:
    """Setup logger for paraphrases."""
    paraphrase_logger = logging.getLogger('paraphrase_logger')
    paraphrase_logger.setLevel(logging.INFO)
    
    for handler in paraphrase_logger.handlers[:]:
        paraphrase_logger.removeHandler(handler)
    
    log_file = model_dir / "paraphrase_log.log"
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    paraphrase_logger.addHandler(file_handler)
    paraphrase_logger.propagate = False 
    return paraphrase_logger

async def generate_paraphrases(dataset: Dataset, llm: ChatOpenAI, paraphrase_logger: logging.Logger) -> Dataset:
    paraphrased_data = []
    
    for item in dataset:
        original_question = item['title']
        ground_truth = item['content']
        
        paraphrase_logger.info(f"\n{'='*80}")
        paraphrase_logger.info(f"ORIGINAL QUESTION: {original_question}")
        paraphrase_logger.info(f"GROUND TRUTH: {ground_truth}")
        paraphrase_logger.info(f"{'='*80}")
        
        for language in ["vietnamese", "english"]:
            paraphrase_logger.info(f"\n--- {language.upper()} PARAPHRASES ---")
            
            for i in range(3):
                prompt = PARAPHRASE_PROMPTS[language].format(question=original_question)
                response = await llm.ainvoke([{"role": "user", "content": prompt}])
                paraphrased_question = response.content.strip()
                
                paraphrase_logger.info(f"Paraphrase {i+1}: {paraphrased_question}")
                
                paraphrased_data.append({
                    'title': paraphrased_question,
                    'content': ground_truth,
                    'original_question': original_question,
                    'language': language,
                    'paraphrase_id': i + 1
                })
    return Dataset.from_list(paraphrased_data)


class RAGRetriever:
    """RAG retrieval methods."""
    
    def __init__(self, vectorstore: FAISS, embeddings: OpenAIEmbeddings, llm: ChatOpenAI):
        self.vectorstore = vectorstore
        self.embeddings = embeddings
        self.llm = llm
        self._setup_bm25()
    
    def _setup_bm25(self):
        """Setup BM25 retriever for hybrid search."""
        all_docs = [
            self.vectorstore.docstore._dict[str(i)] 
            for i in range(self.vectorstore.index.ntotal)
            if str(i) in self.vectorstore.docstore._dict
        ]
        self.bm25_retriever = BM25Retriever.from_documents(all_docs or [Document(page_content="dummy")])
    
    async def _evaluate_context_relevance(self, question: str, context: str) -> str:
        """Evaluate context relevance for Self-RAG with improved prompting."""
        prompt = SELF_RAG_REFLECTION_PROMPT.format(question=question, context=context)
        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        
        evaluation = response.content.strip().upper()
        if "RELEVANT" in evaluation and "PARTIALLY" not in evaluation and "IRRELEVANT" not in evaluation:
            return "RELEVANT"
        elif "PARTIALLY_RELEVANT" in evaluation or "PARTIALLY RELEVANT" in evaluation:
            return "PARTIALLY_RELEVANT"
        else:
            return "IRRELEVANT"
    
    async def retrieve(self, question: str, method: str, k: int = 3) -> Tuple[List[str], float]:
        """Retrieve contexts using specified method."""
        start_time = time.time()
        
        if method == "baseline":
            # Baseline: no retrieval, empty context
            contexts = []
        
        elif method == "basic":
            docs = self.vectorstore.similarity_search(question, k=k)
            contexts = [doc.page_content for doc in docs]
        
        elif method == "mmr":
            docs = self.vectorstore.max_marginal_relevance_search(question, k=k, fetch_k=10)
            contexts = [doc.page_content for doc in docs]
        
        elif method == "hybrid":
            vector_retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            self.bm25_retriever.k = k
            ensemble = EnsembleRetriever(
                retrievers=[vector_retriever, self.bm25_retriever],
                weights=[0.5, 0.5]
            )
            docs = await ensemble.ainvoke(question)
            contexts = [doc.page_content for doc in docs[:k]]
        
        elif method == "multi_query":
            base_retriever = self.vectorstore.as_retriever(search_kwargs={"k": k})
            multi_retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=self.llm)
            docs = await multi_retriever.ainvoke(question)
            contexts = [doc.page_content for doc in docs[:k]]
        
        elif method == "self_rag":
            initial_k = max(k * 3, 10)
            docs = self.vectorstore.similarity_search(question, k=initial_k)
            
            # Evaluate each context for relevance
            evaluation_tasks = []
            for doc in docs:
                evaluation_tasks.append(self._evaluate_context_relevance(question, doc.page_content))
            
            relevance_scores = await asyncio.gather(*evaluation_tasks)
            
            # Create evaluated contexts with scores
            evaluated_contexts = []
            for doc, relevance in zip(docs, relevance_scores):
                evaluated_contexts.append({
                    'content': doc.page_content,
                    'relevance': relevance
                })
            
            # Filter and prioritize relevant contexts
            relevant_contexts = [
                ctx for ctx in evaluated_contexts 
                if ctx['relevance'] in ['RELEVANT', 'PARTIALLY_RELEVANT']
            ]
            
            # Sort by relevance priority and take top k
            relevant_contexts.sort(key=lambda x: 0 if x['relevance'] == 'RELEVANT' else 1)            
            contexts = [ctx['content'] for ctx in relevant_contexts[:k]]
            
            # If not enough relevant contexts, pad with irrelevant ones
            if len(contexts) < k:
                irrelevant_contexts = [
                    ctx['content'] for ctx in evaluated_contexts 
                    if ctx['relevance'] == 'IRRELEVANT'
                ]
                contexts.extend(irrelevant_contexts[:k - len(contexts)])
        
        else:
            contexts = []
        
        latency = time.time() - start_time
        return contexts, latency

async def generate_answers(dataset: Dataset, rag_retriever: RAGRetriever, llm: ChatOpenAI, k: int = 3) -> Dict[str, Dataset]:
    """Generate answers using different RAG methods."""
    
    methods = ["baseline", "basic", "mmr", "hybrid", "multi_query", "self_rag"]
    results = {}
    
    for method in methods:
        method_results = []
        
        async def process_item(item):
            question = item['title']
            ground_truth = item['content']
            
            # Retrieve contexts
            contexts, retrieval_latency = await rag_retriever.retrieve(question, method, k)
            
            # Prepare prompt based on method
            if method == "self_rag" and contexts:
                # Use specialized Self-RAG generation prompt
                context_str = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])
                user_content = SELF_RAG_GENERATION_PROMPT.format(
                    question=question, 
                    evaluated_contexts=context_str
                )
                messages = [{"role": "user", "content": user_content}]
            else:
                # Standard RAG approach
                system_content = SYSTEM_PROMPT
                if contexts:
                    context_str = "\n\n---\n\n".join([f"Context {i+1}:\n{ctx}" for i, ctx in enumerate(contexts)])
                    system_content += f"\n\nRelevant information:\n{context_str}"
                messages = [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": question}
                ]
            
            # Generate answer
            gen_start = time.time()
            response = await llm.ainvoke(messages)
            generation_latency = time.time() - gen_start
            
            return {
                "question": question,
                "answer": response.content,
                "contexts": contexts,
                "ground_truth": ground_truth,
                "original_question": item['original_question'],
                "language": item['language'],
                "paraphrase_id": item['paraphrase_id'],
                "retrieval_latency": retrieval_latency,
                "generation_latency": generation_latency,
                "total_latency": retrieval_latency + generation_latency,
                "method": method
            }
        
        tasks = [process_item(item) for item in dataset]
        method_results = await tqdm_asyncio.gather(*tasks, desc=f"{method} method")
        results[method] = Dataset.from_list(method_results)
    
    return results

async def evaluate_method(dataset: Dataset, method_name: str) -> Dict:
    """Evaluate dataset with RAGAS metrics and retrieval latency statistics."""
    logger.info(f"Evaluating {method_name}...")
    
    # RAGAS evaluation
    metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall(), AnswerCorrectness()]
    ragas_result = evaluate(dataset=dataset, metrics=metrics)
    
    # Only retrieval latency statistics
    retrieval_latencies = [item['retrieval_latency'] for item in dataset]
    
    latency_stats = {
        'avg_retrieval_latency': np.mean(retrieval_latencies),
    }
    
    return {
        'ragas_metrics': ragas_result,
        'latency_stats': latency_stats
    }

def summary_csv(all_results: Dict, model_dir: Path):
    """Create a focused summary CSV with only requested metrics."""
    summary_data = []
    
    for method_name, result in all_results.items():
        row = {'method': method_name}
        
        # Add RAGAS metrics
        ragas_df = result['evaluation']['ragas_metrics'].to_pandas()
        if len(ragas_df) > 0:
            for metric, value in ragas_df.iloc[0].to_dict().items():
                if isinstance(value, (int, float)):
                    row[f'{metric}'] = value
        
        row.update(result['evaluation']['latency_stats'])
        summary_data.append(row)
    
    # Format summary data into DataFrame
    summary_df = pd.DataFrame(summary_data)
    column_order = ['method']
    ragas_columns = [col for col in summary_df.columns if col not in ['method', 'avg_retrieval_latency']]
    column_order.extend(ragas_columns)
    column_order.append('avg_retrieval_latency')
    summary_df = summary_df.reindex(columns=column_order)
    
    # Save to CSV
    csv_path = model_dir / "summary.csv"
    summary_df.to_csv(csv_path, index=False, float_format='%.4f')
    return summary_df

async def run_benchmark(args):
    """Main benchmarking function."""
    start_time = time.time()
    
    # Setup logging
    model_dir = logs_dir / f"k_{args.k}_chunk_{args.chunk_size}_{args.model}"
    model_dir.mkdir(exist_ok=True)
    paraphrase_logger = paraphrase_logging(model_dir)
    
    # Load data and models
    dataset = load_dataset_split(args.split_ratio, args.max_samples)
    llm = ChatOpenAI(model=args.llm, temperature=0.7)
    vectorstore, embeddings = load_vectorstore(args.model, args.chunk_size)
    
    # Generate paraphrases
    paraphrased_dataset = await generate_paraphrases(dataset, llm, paraphrase_logger)
    
    # Initialize RAG retriever
    rag_retriever = RAGRetriever(vectorstore, embeddings, llm)
    
    # Generate answers with all methods
    method_datasets = await generate_answers(paraphrased_dataset, rag_retriever, llm, args.k)
    
    # Evaluate all methods
    all_results = {}
    for method_name, method_dataset in method_datasets.items():
        evaluation = await evaluate_method(method_dataset, method_name)
        all_results[method_name] = {
            'dataset': method_dataset,
            'evaluation': evaluation
        }    
    summary_df = summary_csv(all_results, model_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enhanced RAG Benchmark with Self-RAG and Focused Logging")
    parser.add_argument("--model", type=str, default="text-embedding-3-small",
                        choices=["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"],
                        help="Embedding model for vector store")
    parser.add_argument("--chunk_size", type=int, default=1024,
                        help="Chunk size for vector store")
    parser.add_argument("--split_ratio", type=float, default=0.8,
                        help="Train split ratio")
    parser.add_argument("--llm", type=str, default="gpt-4o",
                        help="OpenAI model for generation and paraphrasing")
    parser.add_argument("--k", type=int, default=1,
                        help="Number of documents to retrieve")
    parser.add_argument("--max_samples", type=int, default=1,
                        help="Maximum samples to use (0 for all)")

    args = parser.parse_args()
    random.seed(0)
    asyncio.run(run_benchmark(args))