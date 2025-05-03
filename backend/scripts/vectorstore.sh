BATCH_SIZE=10000

# Set the path to the vectorstore.py script
SCRIPT_DIR="$(dirname "$0")"
VECTORSTORE_PY="$SCRIPT_DIR/../vectorstore.py"

# text-embedding-ada-002
for CHUNK_SIZE in 512 1024; do
    cd "$(dirname "$VECTORSTORE_PY")" && \
    python "$(basename "$VECTORSTORE_PY")" --model text-embedding-ada-002 --chunk_size $CHUNK_SIZE --batch_size $BATCH_SIZE
    cd - > /dev/null # Return to original directory
done

# text-embedding-3-small
for CHUNK_SIZE in 512 1024; do    
    cd "$(dirname "$VECTORSTORE_PY")" && \
    python "$(basename "$VECTORSTORE_PY")" --model text-embedding-3-small --chunk_size $CHUNK_SIZE --batch_size $BATCH_SIZE
    cd - > /dev/null # Return to original directory
done

# text-embedding-3-large
for CHUNK_SIZE in 512 1024; do    
    cd "$(dirname "$VECTORSTORE_PY")" && \
    python "$(basename "$VECTORSTORE_PY")" --model text-embedding-3-large --chunk_size $CHUNK_SIZE --batch_size $BATCH_SIZE
    cd - > /dev/null # Return to original directory
done