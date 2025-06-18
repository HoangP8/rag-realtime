SPLIT_RATIO=0.8
LLM="gpt-4o"
MAX_SAMPLES=10

EMBEDDING_MODELS=("text-embedding-ada-002" "text-embedding-3-small" "text-embedding-3-large")
CHUNK_SIZES=(512 1024)
K_VALUES=(1 3 5)

SCRIPT_DIR="$(dirname "$0")"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
TEXT_BENCHMARK_PY="$AGENT_DIR/text_benchmark.py"

cd "$AGENT_DIR"

# Loop through each embedding model and chunk size
for MODEL in "${EMBEDDING_MODELS[@]}"; do
  for CHUNK_SIZE in "${CHUNK_SIZES[@]}"; do
    VECTORSTORE_PATH="faiss/${MODEL}/chunk_size_${CHUNK_SIZE}"
    # Only proceed if the vectorstore directory exists
    if [ -d "$VECTORSTORE_PATH" ]; then      
      for K in "${K_VALUES[@]}"; do        
        python text_benchmark.py \
          --model "$MODEL" \
          --chunk_size "$CHUNK_SIZE" \
          --split_ratio "$SPLIT_RATIO" \
          --llm "$LLM" \
          --k "$K" \
          --max_samples "$MAX_SAMPLES"
      done
    else
      echo "Incorrect vectorstore path: $VECTORSTORE_PATH"    
    fi
  done
done