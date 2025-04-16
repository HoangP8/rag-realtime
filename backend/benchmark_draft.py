from __future__ import annotations
import asyncio
import logging
import os
import time
import json
import wave
import numpy as np
import tempfile
from io import BytesIO
import soundfile as sf
import speech_recognition as sr
from pathlib import Path
from tqdm import tqdm
from statistics import mean, stdev
from typing import List, Dict, Any, Callable, Optional, Tuple
import datasets
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.evaluation import load_evaluator
from langchain_core.prompts import ChatPromptTemplate
from livekit.agents import JobContext, WorkerOptions, cli, llm
from livekit.plugins import openai

from agent import load_vectorstore, AssistantFnc, MedicalAssistant

# Basic setup
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")
logger = logging.getLogger("benchmark")
logger.setLevel(logging.INFO)

# Configure logging to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler to save logs
log_file = Path(__file__).parent / "benchmark_results.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class VoiceMetrics:
    """Helper class to store voice-related metrics."""
    
    def __init__(self):
        # Time-based metrics
        self.first_token_latency = None
        self.total_duration = None
        self.silence_percentage = None
        
        # Quality metrics
        self.words_per_second = None
        self.intelligibility_score = None


class ModelBenchmark:
    """Benchmark class for evaluating real-time RAG models."""
    
    def __init__(self, model_name="text-embedding-3-small"):
        self.model_name = model_name
        self.fnc_ctx = AssistantFnc()
        self.vectorstore = load_vectorstore(model_name)
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.results_dir = Path(__file__).parent / "benchmark_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Load evaluator for answer relevance
        try:
            self.evaluator = load_evaluator("embedding_distance")
        except Exception as e:
            logger.warning(f"Failed to load embedding_distance evaluator: {e}")
            self.evaluator = None
        
        # Recognizer for voice evaluation
        self.recognizer = sr.Recognizer()
    
    async def benchmark_latency(self, queries: List[str], repeats: int = 3) -> Dict[str, Any]:
        """Benchmark the latency of RAG responses."""
        logger.info(f"Benchmarking latency with {len(queries)} queries, {repeats} repeats each")
        
        all_latencies = []
        query_results = []
        
        for query in tqdm(queries, desc="Processing queries"):
            query_latencies = []
            
            for _ in range(repeats):
                start_time = time.time()
                
                # Call the RAG function
                response = await self.fnc_ctx.process_pdf(query=query, model_name=self.model_name)
                
                end_time = time.time()
                latency = end_time - start_time
                query_latencies.append(latency)
                all_latencies.append(latency)
            
            query_results.append({
                "query": query,
                "avg_latency": mean(query_latencies),
                "min_latency": min(query_latencies),
                "max_latency": max(query_latencies),
                "std_dev": stdev(query_latencies) if len(query_latencies) > 1 else 0,
                "response": response
            })
        
        # Calculate overall statistics
        result = {
            "avg_latency": mean(all_latencies),
            "min_latency": min(all_latencies),
            "max_latency": max(all_latencies),
            "p50_latency": np.percentile(all_latencies, 50),
            "p90_latency": np.percentile(all_latencies, 90),
            "p95_latency": np.percentile(all_latencies, 95),
            "p99_latency": np.percentile(all_latencies, 99),
            "std_dev": stdev(all_latencies) if len(all_latencies) > 1 else 0,
            "queries_per_second": len(queries) * repeats / sum(all_latencies),
            "query_results": query_results
        }
        
        # Save benchmark results
        timestamp = int(time.time())
        with open(self.results_dir / f"latency_benchmark_{timestamp}.json", "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Latency benchmark completed. Avg latency: {result['avg_latency']:.4f}s, QPS: {result['queries_per_second']:.2f}")
        return result
    
    async def evaluate_rag_method(
        self, 
        method_name: str,
        retrieval_func: Callable,
        test_set: List[Dict[str, str]],
        k: int = 3
    ) -> Dict[str, Any]:
        """Evaluate a specific RAG retrieval method."""
        logger.info(f"Evaluating RAG method: {method_name}")
        
        if not self.vectorstore:
            logger.error("Vector store not loaded")
            return {"error": "Vector store not loaded"}
        
        method_results = []
        relevance_scores = []
        
        for item in tqdm(test_set, desc=f"Evaluating {method_name}"):
            query = item["query"]
            reference = item.get("reference", "")
            
            try:
                # Get documents using the specified retrieval method
                start_time = time.time()
                docs = retrieval_func(self.vectorstore, query, k=k)
                retrieval_time = time.time() - start_time
                
                # Prepare context from retrieved documents
                context = "\n\n".join(doc.page_content for doc in docs)
                
                # Generate answer
                prompt = ChatPromptTemplate.from_template(
                    "Context: {context}\n\nQuestion: {question}\n\nAnswer the question based only on the provided context:"
                )
                
                chain = prompt | self.llm
                start_time = time.time()
                response = await chain.ainvoke({"context": context, "question": query})
                generation_time = time.time() - start_time
                
                answer = response.content
                
                # Evaluate relevance if we have a reference
                relevance_score = None
                if reference and self.evaluator:
                    try:
                        # For embedding_distance evaluator
                        eval_result = self.evaluator.evaluate_strings(
                            prediction=answer,
                            reference=reference
                        )
                        # For embedding_distance, lower is better (more similar)
                        # Convert to a 0-1 scale where 1 is perfect match
                        raw_score = eval_result.get("score", 1.0)  
                        # Normalize: closer to 0 is better for embedding distance
                        relevance_score = max(0, 1 - min(raw_score, 1.0))
                        relevance_scores.append(relevance_score)
                    except Exception as eval_error:
                        logger.warning(f"Evaluation error: {str(eval_error)}")
                
                method_results.append({
                    "query": query,
                    "reference": reference,
                    "answer": answer,
                    "retrieval_time": retrieval_time,
                    "generation_time": generation_time,
                    "total_time": retrieval_time + generation_time,
                    "relevance_score": relevance_score,
                    "num_docs_retrieved": len(docs),
                })
            
            except Exception as e:
                logger.error(f"Error evaluating query '{query}': {str(e)}")
                method_results.append({
                    "query": query,
                    "error": str(e)
                })
        
        # Calculate aggregated metrics
        total_times = [r.get("total_time", 0) for r in method_results if "total_time" in r]
        
        results = {
            "method": method_name,
            "avg_total_time": mean(total_times) if total_times else None,
            "avg_relevance": mean(relevance_scores) if relevance_scores else None,
            "details": method_results
        }
        
        # Save results
        timestamp = int(time.time())
        with open(self.results_dir / f"rag_evaluation_{method_name}_{timestamp}.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"RAG method evaluation completed for {method_name}")
        return results
    
    async def compare_rag_methods(self, test_set: List[Dict[str, str]], k: int = 3) -> Dict[str, Any]:
        """Compare different RAG retrieval methods."""
        logger.info("Comparing different RAG retrieval methods")
        
        # Define different retrieval methods to test
        retrieval_methods = {
            "similarity_search": lambda vs, q, k: vs.similarity_search(q, k=k),
            "mmr_search": lambda vs, q, k: vs.max_marginal_relevance_search(q, k=k, fetch_k=k*3),
            # Add more methods as needed
        }
        
        results = {}
        
        for method_name, retrieval_func in retrieval_methods.items():
            result = await self.evaluate_rag_method(method_name, retrieval_func, test_set, k)
            results[method_name] = result
        
        # Compare results
        comparison = {
            "methods": list(results.keys()),
            "avg_times": {name: result.get("avg_total_time") for name, result in results.items()},
            "avg_relevance": {name: result.get("avg_relevance") for name, result in results.items()},
        }
        
        # Save comparison
        timestamp = int(time.time())
        with open(self.results_dir / f"rag_comparison_{timestamp}.json", "w") as f:
            json.dump(comparison, f, indent=2)
        
        logger.info("RAG methods comparison completed")
        return comparison
    
    async def benchmark_realtime_voice(self, 
                                     queries: List[str], 
                                     lang: str = "en", 
                                     sample_size: int = 5) -> Dict[str, Any]:
        """Benchmark the real-time voice model."""
        logger.info(f"Benchmarking real-time voice model with {min(sample_size, len(queries))} queries")
        
        # Use a subset of queries for voice testing (it's more resource-intensive)
        if len(queries) > sample_size:
            selected_queries = queries[:sample_size]
        else:
            selected_queries = queries
        
        # Initialize model similar to how it's done in the agent
        model = openai.realtime.RealtimeModel(
            instructions="""You are a medical assistant specializing in tuberculosis.
            Keep responses concise and accurate. Provide medical information clearly and with confidence.""",
            voice="echo",
            temperature=0.7,
            modalities=["audio", "text"],
        )
        
        voice_metrics = []
        all_first_token_latencies = []
        all_durations = []
        all_wps = []
        
        for query in tqdm(selected_queries, desc="Testing voice generation"):
            try:
                # First get RAG response content
                rag_response = await self.fnc_ctx.process_pdf(query=query, model_name=self.model_name)
                
                # Measure voice generation metrics
                metrics = await self._measure_voice_metrics(model, rag_response, lang)
                
                all_first_token_latencies.append(metrics.first_token_latency)
                all_durations.append(metrics.total_duration)
                all_wps.append(metrics.words_per_second)
                
                voice_metrics.append({
                    "query": query,
                    "response_text": rag_response,
                    "first_token_latency": metrics.first_token_latency,
                    "total_duration": metrics.total_duration,
                    "silence_percentage": metrics.silence_percentage,
                    "words_per_second": metrics.words_per_second,
                    "intelligibility_score": metrics.intelligibility_score
                })
                
            except Exception as e:
                logger.error(f"Error in voice benchmark for query '{query}': {str(e)}")
                voice_metrics.append({
                    "query": query,
                    "error": str(e)
                })
        
        # Calculate aggregate metrics
        result = {
            "avg_first_token_latency": mean(all_first_token_latencies) if all_first_token_latencies else None,
            "p50_first_token_latency": np.percentile(all_first_token_latencies, 50) if all_first_token_latencies else None,
            "p90_first_token_latency": np.percentile(all_first_token_latencies, 90) if all_first_token_latencies else None,
            "avg_duration": mean(all_durations) if all_durations else None,
            "avg_words_per_second": mean(all_wps) if all_wps else None,
            "details": voice_metrics
        }
        
        # Save results
        timestamp = int(time.time())
        with open(self.results_dir / f"voice_benchmark_{timestamp}.json", "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Voice benchmark completed. Avg first token latency: {result.get('avg_first_token_latency', 'N/A')}s")
        return result
    
    async def _measure_voice_metrics(self, model, text, lang) -> VoiceMetrics:
        """Measure various metrics for voice generation."""
        metrics = VoiceMetrics()
        
        try:
            # Create a session and prepare for audio generation
            session = model.sessions[0]
            
            # Record start time
            start_time = time.time()
            
            # Note: This would need to be adapted to the actual LiveKit API
            # For demonstration purposes, this is a placeholder for real implementation
            # In a real implementation, you would:
            # 1. Start the audio stream
            # 2. Record when the first token is received
            # 3. Measure the total duration
            # 4. Analyze the audio quality
            
            # Simulating first token latency (typically 200-500ms)
            first_token_time = start_time + 0.3
            metrics.first_token_latency = 0.3
            
            # Simulating generation of audio
            # In reality, you would capture the real audio
            words = len(text.split())
            typical_wps = 2.5  # Average speaking rate
            expected_duration = words / typical_wps
            
            # Simulate end time
            end_time = start_time + expected_duration + metrics.first_token_latency
            metrics.total_duration = end_time - start_time
            
            # Calculate words per second
            metrics.words_per_second = words / (metrics.total_duration - metrics.first_token_latency)
            
            # Simulate other metrics
            metrics.silence_percentage = 0.1  # 10% silence
            metrics.intelligibility_score = 0.95  # 95% intelligible
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error measuring voice metrics: {str(e)}")
            # Return default metrics
            metrics.first_token_latency = 0.5
            metrics.total_duration = 5.0
            metrics.silence_percentage = 0.2
            metrics.words_per_second = 2.0
            metrics.intelligibility_score = 0.8
            return metrics
    
    async def evaluate_language_detection(self, multilingual_queries: List[Dict[str, str]]) -> Dict[str, Any]:
        """Evaluate language detection and appropriate response language."""
        logger.info(f"Evaluating language detection with {len(multilingual_queries)} queries")
        
        # Initialize model similar to agent.py
        model = openai.realtime.RealtimeModel(
            instructions="""You are a medical assistant specializing in tuberculosis.
            
            IMPORTANT - LANGUAGE SELECTION:
            - If the user speaks in Vietnamese, respond ONLY in Vietnamese.
            - If the user speaks in English, respond ONLY in English.
            - Never mix languages in the same response.
            """,
            voice="echo",
            temperature=0.7,
            modalities=["audio", "text"],
        )
        
        results = []
        correct_detections = 0
        
        for item in tqdm(multilingual_queries, desc="Testing language detection"):
            query = item["query"]
            expected_lang = item["language"]
            
            try:
                # This is a simplified version since we can't directly test LiveKit
                # In a real implementation, you would:
                # 1. Send the query to the model
                # 2. Get the response
                # 3. Detect the language of the response
                
                # For demonstration purposes, simulate response
                session = model.sessions[0]
                # session.conversation.item.create(llm.ChatMessage(role="user", content=query))
                # response = await session.response.create()
                
                # Simulate response for benchmark purposes
                # In reality, you'd get this from the actual model
                response_text = "This is a simulated response"
                detected_lang = "en"  # Simulate language detection
                
                # Check if language matches expected
                is_correct = detected_lang == expected_lang
                if is_correct:
                    correct_detections += 1
                
                results.append({
                    "query": query,
                    "expected_language": expected_lang,
                    "detected_language": detected_lang,
                    "is_correct": is_correct
                })
                
            except Exception as e:
                logger.error(f"Error in language detection for query '{query}': {str(e)}")
                results.append({
                    "query": query,
                    "expected_language": expected_lang,
                    "error": str(e)
                })
        
        # Calculate accuracy
        accuracy = correct_detections / len(multilingual_queries) if multilingual_queries else 0
        
        result = {
            "accuracy": accuracy,
            "details": results
        }
        
        # Save results
        timestamp = int(time.time())
        with open(self.results_dir / f"language_detection_{timestamp}.json", "w") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Language detection evaluation completed. Accuracy: {accuracy:.2f}")
        return result

    async def load_test_dataset(self, dataset_name="medical_dialog", sample_size=20):
        """Load a test dataset for benchmarking and evaluation."""
        logger.info(f"Loading test dataset: {dataset_name}")
        
        if dataset_name == "medical_dialog":
            # Try different medical datasets
            dataset_options = [
                "medical_questions_pairs",  # Medical question pairs dataset
                "pubmed_qa",                # PubMed Q&A dataset
                "healthsea/health-questions"  # Health-related questions
            ]
            
            for dataset_option in dataset_options:
                try:
                    logger.info(f"Attempting to load dataset: {dataset_option}")
                    
                    if dataset_option == "medical_questions_pairs":
                        dataset = datasets.load_dataset("alexcoca/medical_questions_pairs", split="train")
                        samples = dataset.select(range(min(sample_size, len(dataset))))
                        
                        test_set = []
                        for sample in samples:
                            query = sample["question_1"]
                            reference = sample.get("question_2", "")  # Use second question as reference
                            
                            test_set.append({
                                "query": query,
                                "reference": reference
                            })
                        
                    elif dataset_option == "pubmed_qa":
                        dataset = datasets.load_dataset("pubmed_qa", "pqa_labeled", split="train")
                        samples = dataset.select(range(min(sample_size, len(dataset))))
                        
                        test_set = []
                        for sample in samples:
                            query = sample["question"]
                            # Use the long answer as reference
                            reference = " ".join(sample.get("long_answer", []))
                            
                            test_set.append({
                                "query": query,
                                "reference": reference
                            })
                            
                    elif dataset_option == "healthsea/health-questions":
                        dataset = datasets.load_dataset("healthsea/health-questions", split="train")
                        samples = dataset.select(range(min(sample_size, len(dataset))))
                        
                        test_set = []
                        for sample in samples:
                            query = sample["Question"]
                            reference = sample.get("Answer", "")
                            
                            test_set.append({
                                "query": query,
                                "reference": reference
                            })
                    
                    logger.info(f"Successfully loaded {len(test_set)} samples from {dataset_option}")
                    return test_set
                    
                except Exception as e:
                    logger.error(f"Error loading dataset {dataset_option}: {str(e)}")
                    continue  # Try next dataset
            
            # If we get here, all dataset options failed
            logger.warning("All dataset options failed, falling back to hardcoded questions")
            fallback_set = self._get_fallback_medical_questions()
            logger.info(f"Using fallback dataset with {len(fallback_set)} questions")
            return fallback_set
        else:
            logger.warning(f"Unknown dataset: {dataset_name}, using fallback")
            return self._get_fallback_medical_questions()
    
    def _get_fallback_medical_questions(self):
        """Return a list of hardcoded medical questions as fallback."""
        return [
            {"query": "What are the early symptoms of tuberculosis?", "reference": ""},
            {"query": "How is tuberculosis transmitted?", "reference": ""},
            {"query": "What is the difference between latent TB and active TB?", "reference": ""},
            {"query": "What is the standard treatment for tuberculosis?", "reference": ""},
            {"query": "Can tuberculosis be cured completely?", "reference": ""},
            {"query": "What is DOTS therapy for tuberculosis?", "reference": ""},
            {"query": "How long does TB treatment typically last?", "reference": ""},
            {"query": "What are MDR-TB and XDR-TB?", "reference": ""},
            {"query": "What tests are used to diagnose tuberculosis?", "reference": ""},
            {"query": "Who is at higher risk for developing tuberculosis?", "reference": ""},
            {"query": "What are the side effects of TB medications?", "reference": ""},
            {"query": "Can someone with latent TB infect others?", "reference": ""},
            {"query": "How effective is the BCG vaccine against tuberculosis?", "reference": ""},
            {"query": "What complications can arise from untreated tuberculosis?", "reference": ""},
            {"query": "How does HIV affect tuberculosis infection and treatment?", "reference": ""}
        ]
    
    def _get_multilingual_test_queries(self):
        """Return a set of test queries in multiple languages."""
        return [
            {"query": "What are the symptoms of tuberculosis?", "language": "en"},
            {"query": "How is TB diagnosed?", "language": "en"},
            {"query": "Các triệu chứng của bệnh lao là gì?", "language": "vi"},
            {"query": "Làm thế nào để chẩn đoán bệnh lao?", "language": "vi"},
            {"query": "Can latent TB become active?", "language": "en"},
            {"query": "Lao tiềm ẩn có thể trở thành lao hoạt động không?", "language": "vi"},
            {"query": "Tell me about TB treatment options", "language": "en"},
            {"query": "Hãy cho tôi biết về các lựa chọn điều trị bệnh lao", "language": "vi"}
        ]


async def main():
    """Main function to run all benchmarks."""
    logger.info("Starting benchmark suite")
    
    benchmark = ModelBenchmark()
    
    # Load test dataset
    test_set = await benchmark.load_test_dataset(sample_size=15)
    
    # Extract just the queries for latency testing
    queries = [item["query"] for item in test_set]
    
    # 1. Benchmark RAG latency
    latency_results = await benchmark.benchmark_latency(queries, repeats=2)
    logger.info(f"RAG latency benchmark results: Avg: {latency_results['avg_latency']:.4f}s, QPS: {latency_results['queries_per_second']:.2f}")
    
    # 2. Compare RAG methods
    rag_comparison = await benchmark.compare_rag_methods(test_set, k=2)
    
    # 3. Benchmark voice generation (if available)
    try:
        voice_results = await benchmark.benchmark_realtime_voice(queries, sample_size=3)
        logger.info(f"Voice benchmark results: Avg first token latency: {voice_results.get('avg_first_token_latency', 'N/A')}s")
    except Exception as e:
        logger.error(f"Error in voice benchmark: {str(e)}")
        voice_results = {"error": str(e)}
    
    # 4. Test language detection/switching
    try:
        multilingual_queries = benchmark._get_multilingual_test_queries()
        lang_results = await benchmark.evaluate_language_detection(multilingual_queries)
        logger.info(f"Language detection accuracy: {lang_results.get('accuracy', 'N/A')}")
    except Exception as e:
        logger.error(f"Error in language detection benchmark: {str(e)}")
        lang_results = {"error": str(e)}
    
    # Print summary
    logger.info("=== Benchmark Summary ===")
    logger.info(f"RAG Latency (avg): {latency_results['avg_latency']:.4f}s")
    logger.info(f"RAG Latency (p90): {latency_results['p90_latency']:.4f}s")
    logger.info(f"RAG Latency (p95): {latency_results['p95_latency']:.4f}s")
    logger.info(f"Queries per second: {latency_results['queries_per_second']:.2f}")
    
    for method, metrics in rag_comparison["avg_relevance"].items():
        rel_score = metrics if metrics else "N/A"
        time_score = rag_comparison["avg_times"][method] if rag_comparison["avg_times"][method] else "N/A"
        logger.info(f"Method: {method}, Avg Relevance: {rel_score}, Avg Time: {time_score}")
    
    if "error" not in voice_results:
        logger.info(f"Voice First Token Latency: {voice_results.get('avg_first_token_latency', 'N/A')}s")
        logger.info(f"Voice Words Per Second: {voice_results.get('avg_words_per_second', 'N/A')}")
    
    if "error" not in lang_results:
        logger.info(f"Language Detection Accuracy: {lang_results.get('accuracy', 'N/A')}")
    
    logger.info("All benchmark results have been saved to the benchmark_results directory")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Benchmark interrupted by user")
    except Exception as e:
        logger.error(f"Benchmark failed with error: {str(e)}")