#!/bin/bash
# Install Ollama. More info at: ollama.com
curl -fsSL https://ollama.com/install.sh | sh

# Pull some sample models.
read -p "Use default sample models from ollama (y/n)?" answer
answer=${answer:-Y}
case "$answer" in
  [Yy])
    echo "Pulling qwen2.5, qwen2.5vl and bge-m3 models..."
    ollama pull qwen2.5
    ollama pull qwen2.5vl
    ollama pull bge-m3
    ;;
  *)
    echo "Skipping sample models. To download them manually run 'ollama pull [model_name]'. For reference, check ollama.com."
    ;;
esac

# Install virtual environment
python3 -m venv .venv

# Activate virtual environment and install required packages
source .venv/bin/activate
pip install -r requirements.txt

mkdir -p documents

deactivate
