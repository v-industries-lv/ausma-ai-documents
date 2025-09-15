#!/bin/bash
source .venv/bin/activate
echo "Converting documents..."
python3 document_converter.py --poppler-path "/usr/bin/" --text-model "qwen2.5" --vision-model "qwen2.5vl" --conversions "raw;ocr" --dpi 300
echo "Processing and loading documents into Chroma..."
python3 knowledge_base_creator.py
echo "Done"
deactivate
