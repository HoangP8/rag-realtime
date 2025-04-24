SPLIT_RATIO=0.8
LLM="gpt-4o"
SCORE_THRESHOLD=0.35
MAX_SAMPLES=1

EMBEDDING_MODELS=("text-embedding-ada-002" "text-embedding-3-small" "text-embedding-3-large")
CHUNK_SIZES=(512 1024)
K_VALUES=(3 5 7)

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
          --score_threshold "$SCORE_THRESHOLD" \
          --max_samples "$MAX_SAMPLES"
      done
    fi
  done
done