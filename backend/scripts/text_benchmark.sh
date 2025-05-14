SPLIT_RATIO=0.8
LLM="gpt-4o"
SCORE_THRESHOLD=0.35
MAX_SAMPLES=100

EMBEDDING_MODELS=("text-embedding-ada-002" "text-embedding-3-small" "text-embedding-3-large")
CHUNK_SIZES=(512 1024)
K_VALUES=(3 5 7)

# Set SSL_CERT_FILE variable
unset SSL_CERT_FILE

# Set the path to the text_benchmark.py script
SCRIPT_DIR="$(dirname "$0")"
TEXT_BENCHMARK_PY="$SCRIPT_DIR/../text_benchmark.py"

# Loop through each embedding model and chunk size
for MODEL in "${EMBEDDING_MODELS[@]}"; do
  for CHUNK_SIZE in "${CHUNK_SIZES[@]}"; do
    VECTORSTORE_PATH="faiss/${MODEL}/chunk_size_${CHUNK_SIZE}"
    # Only proceed if the vectorstore directory exists
    if [ -d "$VECTORSTORE_PATH" ]; then      
      for K in "${K_VALUES[@]}"; do        
        cd "$(dirname "$TEXT_BENCHMARK_PY")" && \
        python "$(basename "$TEXT_BENCHMARK_PY")" \
          --model "$MODEL" \
          --chunk_size "$CHUNK_SIZE" \
          --split_ratio "$SPLIT_RATIO" \
          --llm "$LLM" \
          --k "$K" \
          --score_threshold "$SCORE_THRESHOLD" \
          --max_samples "$MAX_SAMPLES"
        cd - > /dev/null # Return to original directory
      done
    else
      echo "Vectorstore for $MODEL with chunk size $CHUNK_SIZE does not exist."
      echo "Please ensure the vectorstore has been created by running vectorstore.sh."
      echo "If you ran the script from a different directory, verify the path is correct (should be bash scripts/text_benchmark.sh instead of cd scripts and bash text_benchmark.sh)."
      echo ""    
    fi
...existin
  done
done