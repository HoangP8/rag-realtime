SCRIPT_PATH="latency_test/benchmark.py"
CREDENTIALS_FILE="latency_test/serviceAcc.json"
INPUT_FILE="latency_test/input_audio/record_google.wav"
MODEL_IDS=("gpt2" "H2O" "StableMed" "phi-2" "Llama3" "Camel")
DEVICE=0

for MODEL_ID in "${MODEL_IDS[@]}"
do
    echo "Processing model: $MODEL_ID"
    python $SCRIPT_PATH \
      --credentials_file $CREDENTIALS_FILE \
      --input_file $INPUT_FILE \
      --model_id $MODEL_ID \
      --device "${DEVICE}"  
    
done

echo "All models processed."
