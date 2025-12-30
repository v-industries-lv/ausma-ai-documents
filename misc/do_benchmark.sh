#!/bin/bash
source .venv/bin/activate
python3 benchmark.py --model "qwen2.5:latest"
python3 benchmark.py --use-cpu --model "qwen2.5:latest"
deactivate
