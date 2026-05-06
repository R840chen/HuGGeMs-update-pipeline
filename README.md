# HuGGeMs-update-pipeline

A pipeline used to update the **Human Gut Microbial Gene Markers (HuGGeMs)** dataset — from new genome input to a fully updated marker set ready for metagenome profiling.

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/R840chen/HuGGeMs-update-pipeline.git
cd HuGGeMs-update-pipeline
```

### Step 2 — Create the conda environment

```bash
bash setup_huggems_env.sh
conda activate huggems-update
```

This script creates the full conda environment and installs all required tools and the `huggems` Python package in one step.

---

## Overview

This pipeline consists of two parts:

### Part I — Genome Presence Detection
Determines whether a provided genome (or species) is already represented in the HuGGeMs dataset by computing genome-level distances against the 11,167 HuGGeMs representative genome clusters.

- Uses **dRep** (compare mode) as the core tool
- Outputs a report table listing each query genome's nearest representative, ANI value, and presence/absence status

### Part II — Marker Gene Selection & Update
Given new genomes not yet represented in HuGGeMs, this part:
1. Predicts genes with **Prokka**
2. Annotates predicted genes against **UniRef90 / UniRef50** using **Diamond**
3. Identifies core genes with **MMseqs2**
4. Selects marker genes using simulated reads (**ART**), mapping (**Bowtie2** + **Samtools**), and filtering
5. Updates the HuGGeMs marker set and reference pkl files

---

## Required Databases

Three datasets are required before running the pipeline.

### 1. HuGGeMs Representative Clusters (11,167 genomes)
Used by **Part I** for genome distance comparisons.

**Download:** [https://zenodo.org/records/19601390](https://zenodo.org/records/19601390)

### 2. HuGGeMs Dataset (marker profiles / reference)
Used for metagenome profiling and marker set updates (**Part II**).

**Download:** [https://zenodo.org/records/19601390](https://zenodo.org/records/19601390)

### 3. UniRef90 and UniRef50 Databases
Used by **Part II** for protein annotation.

**Download from UniProt:**

```bash
# UniRef90 (~25 GB compressed)
wget https://ftp.ebi.ac.uk/pub/databases/uniprot/uniref/uniref90/uniref90.fasta.gz

# UniRef50 (~13 GB compressed)
wget https://ftp.ebi.ac.uk/pub/databases/uniprot/uniref/uniref50/uniref50.fasta.gz
```

After downloading, build Diamond databases:

```bash
conda activate huggems-update
diamond makedb --in uniref90.fasta.gz -d uniref90.dmnd
diamond makedb --in uniref50.fasta.gz -d uniref50.dmnd
```

> **Disk space estimate:** UniRef90 + Diamond DB ~50 GB, UniRef50 + Diamond DB ~25 GB, HuGGeMs genomes ~50–100 GB, working space 100+ GB. **Total: ~250–300 GB recommended.**

---

## Usage

### Part I — Genome Presence Detection

Check whether your query genomes are already represented in HuGGeMs:

```bash
huggems presence \
  --new-dir /path/to/query_genomes/ \
  --rep-dir /path/to/11167_representatives/ \
  --output-dir /path/to/dRep_results/ \
  --extract-unique
```

**Output:** A table listing each query genome, its nearest HuGGeMs representative, ANI value, and whether it is already represented.

| Argument | Description |
|----------|-------------|
| `--new-dir` | Directory containing query genome FASTA files |
| `--rep-dir` | Path to the 11,167 HuGGeMs representative genomes |
| `--output-dir` | Output directory for dRep results |
| `--extract-unique` | Extract genomes not represented in HuGGeMs |

---

### Part II — Marker Gene Selection & Update

Run the full integrated pipeline on genomes identified as new in Part I:

```bash
huggems markers \
  --input-dir /path/to/new_genomes/ \
  --uniref90 /path/to/uniref90.dmnd \
  --uniref50 /path/to/uniref50.dmnd \
  --huggems-ref /path/to/HuGGeMs_ref/ \
  --output-dir /path/to/results/
```

| Argument | Description |
|----------|-------------|
| `--input-dir` | Directory containing new genome FASTA files (output of Part I) |
| `--uniref90` | Path to the UniRef90 Diamond database (`.dmnd`) |
| `--uniref50` | Path to the UniRef50 Diamond database (`.dmnd`) |
| `--huggems-ref` | Path to the HuGGeMs reference directory |
| `--output-dir` | Output directory for updated marker results |

---

## Repository Structure

```
HuGGeMs-update-pipeline/
├── huggems/                        # Main Python package & pipeline scripts
├── conda.recipe/                   # Conda build recipe (meta.yaml, build.sh, run_test.py)
├── huggems.egg-info/               # Auto-generated Python package metadata (git-ignored)
├── HuGGeMs-update-environment.yml  # Conda environment definition
├── requirements.txt                # pip dependencies (drep, networkx)
├── pyproject.toml                  # Python package build config
├── build_conda.sh                  # Script to build distributable conda package
├── setup_huggems_env.sh            # Environment setup script (recommended install method)
└── HuGGeMs-datasets-download.md   # Detailed dataset download instructions
```

---

## Tips

- Always use **absolute paths** for input/output arguments to avoid ambiguity.
- Run computationally intensive steps (annotation, all-vs-all comparison) on a **multi-core cluster or high-performance server**.
- Use `wget -c` or `curl -C -` to resume interrupted database downloads.
- Users in Asia: the **EBI mirror** (`ftp.ebi.ac.uk`) often provides faster download speeds than the UniProt main server.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
