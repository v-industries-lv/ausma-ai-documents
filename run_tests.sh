#!/bin/bash
source .venv/bin/activate
echo "Running test: test_prepare_documents.py"
python3 test_prepare_documents.py
python3 test_rag_processor.py
echo "Done"
deactivate