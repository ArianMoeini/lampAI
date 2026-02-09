#!/bin/bash
# RunPod H200 setup for LAMP fine-tuning
# Run this first after connecting to your pod

set -e

echo "=== LAMP Fine-Tuning Setup ==="

# Clone repo
if [ ! -d "lampAI" ]; then
    git clone https://github.com/ArianMoeini/lampAI.git
fi
cd lampAI/finetuning

# Install dependencies
pip install --upgrade pip
pip install unsloth
pip install --no-deps trl peft accelerate bitsandbytes
pip install datasets

echo ""
echo "=== Setup complete! ==="
echo "Now run: python train_all_models.py"
