# GradeLegal: Automated Grading for German Legal Cases

This repository accompanies the ICAIL 2026 paper  
**“GradeLegal: Automated Grading for German Legal Cases.”**

## Repository Structure

> **Each subfolder contains its own README with additional details where relevant.**

- `code/`: Standalone Jupyter notebooks and code for analysis, ensembling, inference (reference), and figures.
- `data/`: released data artifacts (instructor materials and model outputs/grades).
- `prompts/`: prompt skeletons used in the experiments (German originals + English translations for reference).

## Environments



This repository provides **two conda environments**:

- `environment_icail2026.yml`: use for **all analysis/code** (default).
- `environment_cuda_icail2026.yml`: use **only for vLLM-based inference** (CUDA/GPU required).






## Quickstart

Clone the repository and set up the environments:

```bash
git clone <REPO_URL>
cd <REPO_DIR>

# create the default (CPU) environment – use for analysis and most code
conda env create -f environment_icail2026.yml
conda activate environment_icail2026

# (optional) create the CUDA environment – use only for vLLM-based inference
conda deactivate
conda env create -f environment_cuda_icail2026.yml
conda activate environment_cuda_icail2026
