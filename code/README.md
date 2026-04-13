# Overview

This repository contains the code and notebooks used in our experiments. All notebooks are provided as **standalone Jupyter notebooks** and can be run independently.

## Directory Structure

### `./analysis`
- Contains the main code and notebooks for analyzing experimental results.
- Contains the error analysis code and notebooks for the error analysis section of the paper.

### `./ensemble`
Contains code related to ensemble analysis.

### `./prompt_ablation_figure`
Contains code used to generate the prompt ablation figure presented in the paper.

### `./inference`
Contains scripts for running model inference. These scripts were **used in our experiments** and are provided **for reference only**.

- The inference code **will not work out of the box** in this open-source release.
- Running inference requires the **complete dataset** and the **student solution**, which cannot be published Due to ***data protection law and copyright constraints***.
- These components were used in our experiments but are **not included** here.
- Please refer to the `README.txt` inside the `./inference` directory for instructions on how to execute the inference code when the required data and student solution are available.


## Mapping Files

### `model_mapping.md`
Provides a mapping from the model names used in the paper to the exact model identifiers used in our experiments.

### `prompt_mapping.md`
Provides a mapping from the prompt names used in the paper to the exact prompt identifiers used in our experiments.

---

If you are only interested in understanding or reproducing the analysis results presented in the paper, the notebooks in `./analysis`, `./ensemble`, and `./prompt_ablation_figure` are fully self-contained and runnable.
