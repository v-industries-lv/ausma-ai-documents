#!/bin/bash -xe
python3 -m venv .venv

# Activate virtual environment and install required packages
source .venv/bin/activate

pip install -r requirements.txt

mkdir -p documents

deactivate

