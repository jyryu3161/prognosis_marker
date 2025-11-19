# Prognosis Marker

Prognostic gene signature workflows with AUC-driven stepwise selection for binary outcomes and survival endpoints.

## Features

- **Binary classification**: Logistic regression with train/test splitting and ROC analysis
- **Survival analysis**: Cox proportional hazards with time-dependent ROC curves
- **Reproducible**: Automated dependency management with pixi
- **Publication-ready**: High-resolution figures (TIFF/SVG) with coefficient plots

## Installation

### Quick Install

```bash
./install.sh
```

This script automatically:
- Installs pixi if needed
- Sets up the R environment
- Installs all dependencies

### Manual Install

```bash
# Install pixi
curl -fsSL https://pixi.sh/install.sh | bash

# Install dependencies
pixi install
pixi run install-r-packages
```

## Usage

### Running Analyses

Use the provided script to run analyses:

```bash
# Binary classification
./run_analysis.sh binary --config config/example_analysis.yaml

# Survival analysis
./run_analysis.sh survival --config config/example_analysis.yaml
```

Or use pixi directly:

```bash
pixi run binary -- --config config/example_analysis.yaml
pixi run survival -- --config config/example_analysis.yaml
```

### Configuration

Create a YAML config file (see `config/example_analysis.yaml` for template):

```yaml
workdir: .
data_file: your_data.csv

binary:
  sample_id: sample
  outcome: OS
  split_prop: 0.7
  num_seed: 100
  output_dir: results/binary
  freq: 50  # Frequency threshold for candidate gene selection

  # P-value adjustment and filtering (optional)
  top_k: 1000  # Select top K genes by adjusted p-value per iteration
  p_adjust_method: fdr  # P-value adjustment: "fdr" or "bonferroni"
  p_threshold: 0.05  # Adjusted p-value threshold

survival:
  sample_id: sample
  time_variable: OS.year
  event: OS
  horizon: 5
  split_prop: 0.7
  num_seed: 100
  output_dir: results/survival
  freq: 50  # Frequency threshold for candidate gene selection

  # P-value adjustment and filtering (optional)
  top_k: 1000  # Select top K genes by adjusted p-value per iteration
  p_adjust_method: fdr  # P-value adjustment: "fdr" or "bonferroni"
  p_threshold: 0.05  # Adjusted p-value threshold
```

#### Key Configuration Parameters

**Basic Parameters:**
- `sample_id`: Column name for sample identifiers
- `outcome` (binary): Binary outcome variable name (0/1)
- `event` (survival): Event indicator variable name (0/1)
- `time_variable` (survival): Survival time variable name
- `split_prop`: Train/test split proportion (default: 0.7)
- `num_seed`: Number of iterations for stability analysis
- `freq`: Minimum frequency threshold for candidate selection

**P-value Adjustment (NEW):**
- `top_k`: Limits candidates to top K genes by adjusted p-value per iteration (optional)
  - Reduces computation time when many genes are significant
  - Default: NULL (use all significant genes)
  - Recommended: 1000 for large gene sets
- `p_adjust_method`: Multiple testing correction method
  - `"fdr"`: False Discovery Rate (Benjamini-Hochberg, default, less conservative)
  - `"bonferroni"`: Bonferroni correction (more conservative)
- `p_threshold`: Significance threshold for adjusted p-values (default: 0.05)
  - Genes with adjusted p-value < threshold are selected as candidates

**Performance Optimization:**
- `max_candidates_per_step`: Maximum candidates per forward step (enables pre-screening)
- `prescreen_seeds`: Number of seeds for pre-screening evaluation

### Output Files

#### Binary/Survival Analysis Results

Main analysis results are saved in the configured output directory:
- `figures/ROCcurve.{tiff,svg}`: Train/test ROC curves
- `figures/Variable_Importance.{tiff,svg}`: Coefficient plots
- `figures/`: Additional publication-ready figures
- `auc_iterations.csv`: Performance metrics per iteration
- `Intermediate_*.csv`: Stepwise selection details

## Troubleshooting

- **Missing packages**: Run `pixi install` and `pixi run install-r-packages`
- **Config errors**: Ensure column names in YAML match your CSV file
- **Permission denied**: Make scripts executable: `chmod +x *.sh`

## Requirements

- R ≥ 4.3
- pixi (installed automatically by `install.sh`)