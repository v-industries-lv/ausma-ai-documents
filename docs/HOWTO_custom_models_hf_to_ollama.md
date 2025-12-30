# Run a huggingface model
## Download a huggingface model
0. Before starting, define a huggingface LLM runner in settings. Remember to set API token.
1. Choose your preferred an INSTRUCT trained model from huggingface. Model must be in .safetensors format.
```text
Example:

utter-project/EuroLLM-9B-Instruct
```
2. Get the model. Pull the model using ausma.ai app:
```bash
curl -X POST --data '{"model":"utter-project/EuroLLM-9B-Instruct"}' http://127.0.0.1:5000/api/llm_runners/models/pull -H "Content-Type: application/json"
```

3. You can run the model as-is right now in the app.

NOTE: model will be full precision which means longer compute times. If speed is preferred, then see the following section.

## Quantization and Ollama
If you would like to speed up the generation, then you can use llama.cpp to convert this huggingface model to GGUF format with quantization. Be aware that that quantization, while speeding up generation, usually comes at a small cost of performance depending on the quantization method chosen.
1. Clone the llama.cpp repo and open it:
```bash
cd ~/
git clone https://github.com/ggml-org/llama.cpp 
cd llama.cpp
```
2. Create a virtual environment, activate it and install the requirements.txt 
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt 
```
3. Refer to llama.cpp/docs/build.md, to build it from repo.
4. Use llama.cpp  convert_hf_to_gguf.py to convert safetensors to GGUF. Check input model path - it can be different if a newer version of the model repo is available.
```bash
mkdir ~/EuroLLM9B_to_gguf
python3 convert_hf_to_gguf.py ~/ausma-ai-documents/.hf_model_cache/models--utter-project--EuroLLM-9B-Instruct/snapshots/f7ae2bc3bcbb538c0b93fa6cfbf388d9898b1ace --outfile ~/EuroLLM9B_to_gguf/EuroLLM_9B.gguf
```
5. Use llama.cpp lama-quantize to quantize the model to desired level. Here Q4_K_M is chosen.
```bash
./build/bin/llama-quantize ~/EuroLLM9B_to_gguf/EuroLLM_9B.gguf ~/EuroLLM9B_to_gguf/EuroLLM_9B_Q4_K_M.gguf Q4_K_M
```
6. Create a file "Modelfile" for the quantized model in the output file folder. This wil be used by Ollama to create an Ollama compatible model.
```text
FROM ~/EuroLLM9B_to_gguf/EuroLLM_9B_Q4_K_M.gguf
PARAMETER repeat_penalty 1
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.6
PARAMETER top_k 20
PARAMETER top_p 0.95
TEMPLATE """{{- if .System }}
<|im_start|>system {{ .System }}<|im_end|>
{{end}}
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""
```
NOTE: 

FROM - contains the GGUF of out quantized model

PARAMETER - model specific parameters. Refer to original repo on huggingface to get these and any other parameters that might be needed. See Ollama documentation for correct bindings.

TEMPLATE - this is how the generation is controlled. If the repo contains a template, then just paste it here (keep in mind the triple quotes). If you cannot use the template found in the repo or it does not have one, then it will take some experimenting to choose correct one. The best way to find a working template is to try out ones from similar models.

7. Create the model with Ollama:
```bash
cd ~/EuroLLM9B_to_gguf
ollama create EuroLLM9B-Q4-K-M -f Modelfile
```

8. Check if the model is visible in Ollama:
```bash
ollama list
```

9. The model now should be available to be run from Ollama. To do a quick test, run the model:
```bash
ollama run EuroLLM9B-Q4-K-M
```

Now you can use the quantized model with ausma.ai app.