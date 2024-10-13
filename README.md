### 1. Test Latency (Audio Input to Audio Output)

To test the latency of several pretrained models, run the provided `benchmark.sh` script.

```bash
bash benchmark.sh
```

The output is saved as .json file in folder `latency_test`.

### 2. Test Inference of Gemini API and Implement RAG
To run the notebook:
- Navigate to the `gemini_test` folder.
- Open `langchain.ipynb` in your preferred Jupyter environment.
- Follow the instructions in the notebook to:
  - Test the inference capabilities of the Gemini API.
  - Implement a Retrieval-Augmented Generation (RAG) solution.
