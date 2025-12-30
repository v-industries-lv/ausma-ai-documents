#!/bin/bash

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "This is not Linux. Exiting script..."
    exit 1
fi


# Install Ollama. More info at: ollama.com
read -r -p "This application uses Ollama as default LLM runner. Do you want to install it now? (Y/n)?" ollama_answer
ollama_answer=${ollama_answer:-Y}
if [[ $ollama_answer == [Yy] ]]; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Pull some sample models.
if command -v ollama > /dev/null 2>&1;
then
    read -r -p "Use default sample models from ollama (Y/n)?" answer
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
fi

# BROKEN for now
# mkdir -p bin/linux
# url="https://dl.xpdfreader.com/xpdf-tools-linux-4.05.tar.gz"
# archive="xpdf-tools-linux-4.05.tar.gz"
# archive_root="xpdf-tools-linux-4.05"
# curl -LO "$url"

# bits=$(getconf LONG_BIT | tr -d '[:space:]')
# if [[ "$bits" == "32" ]]; then
#   pdftopng_bin="$archive_root/bin32/pdftopng"
# elif [[ "$bits" == "64" ]]; then
#   pdftopng_bin="$archive_root/bin64/pdftopng"
# else
#   echo "Unknown architecture: $bits"
#   exit 1
# fi

# tar -xzf "$archive" "$pdftopng_bin" || { echo "Extraction has failed"; exit 1; }
# mv "$pdftopng_bin" "bin/linux/pdftopng" || { echo "Failed to move file"; exit 1; }
# rm $archive_root -r


# Install virtual environment
python3 -m venv .venv

# Activate virtual environment and install required packages
source .venv/bin/activate
# Installs torch and torchvision for use with CPU only. For GPU support, visit pytorch: https://pytorch.org/get-started/locally/
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements.txt

mkdir -p documents

deactivate
