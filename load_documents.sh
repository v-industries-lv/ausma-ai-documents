#!/bin/bash
source .venv/bin/activate
echo "Converting documents..."
python3 prepare_documents.py --poppler-path "/usr/bin/" --text-model "qwen2.5" --vision-model "qwen2.5vl" --conversions "raw;ocr_llm" --dpi 300
echo "Processing and loading documents into Chroma..."
python3 rag_processor.py --llm-model "qwen2.5" --embedding-model "bge-m3" --chroma-path "chroma" --document-path "text"
echo "Done"
deactivate
