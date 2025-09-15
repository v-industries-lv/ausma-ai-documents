#!/bin/bash
source .venv/bin/activate
echo "Email retriever:"
python3 imap_loader.py
echo "Formatting emails for RAG ingestion:"
python3 format_emails.py
echo "Processing and loading emails into Chroma..."
python3 knowledge_base_creator.py
echo "Done"
deactivate