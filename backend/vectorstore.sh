BATCH_SIZE=10000

# text-embedding-ada-002
for CHUNK_SIZE in 512 1024; do
    python vectorstore.py --model text-embedding-ada-002 --chunk_size $CHUNK_SIZE --batch_size $BATCH_SIZE
done

# text-embedding-3-small
for CHUNK_SIZE in 512 1024; do
    python vectorstore.py --model text-embedding-3-small --chunk_size $CHUNK_SIZE --batch_size $BATCH_SIZE
done

# text-embedding-3-large
for CHUNK_SIZE in 512 1024; do
    python vectorstore.py --model text-embedding-3-large --chunk_size $CHUNK_SIZE --batch_size $BATCH_SIZE
done 