#!/bin/bash
# HuGGeMs-update Environment Setup Script
# Usage: bash setup_huggems_env.sh

set -e

ENV_NAME="huggems-update"

echo "=========================================="
echo "HuGGeMs-update Environment Setup"
echo "=========================================="

# Create conda environment
echo "[1/5] Creating conda environment: $ENV_NAME"
conda create -n $ENV_NAME python=3.9 -y

# Activate environment
echo "[2/5] Activating environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate $ENV_NAME

# Install prokka first (with version)
echo "[3/5] Installing prokka..."
conda install -c bioconda prokka==1.14.6 -y

# Install other bioinformatics tools
echo "[4/5] Installing other bioinformatics tools..."
conda install -c bioconda \
    diamond \
    mmseqs2 \
    art \
    bowtie2 \
    samtools \
    bamutil \
    biopython \
    mash \
    mummer \
    fastani \
    -y

# Install dRep via pip (not available in conda)
echo "[5/5] Installing dRep via pip..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To activate the environment, run:"
echo "  conda activate $ENV_NAME"
echo ""
echo "To verify installation, run:"
echo "  conda activate $ENV_NAME"
echo "  prokka --version"
echo "  dRep -v"
echo "  mash --version"
