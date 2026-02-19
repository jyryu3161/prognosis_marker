# PROMISE

**PROgnostic Marker Identification and Survival Evaluation**

AUC-driven stepwise variable selection for prognostic gene signature discovery. Supports binary classification (logistic regression) and survival analysis (Cox proportional hazards) with reproducible train/test splitting.

## Features

- **Binary classification**: Logistic regression with repeated train/test splitting and ROC analysis
- **Survival analysis**: Cox proportional hazards with time-dependent AUC and Kaplan-Meier curves
- **Stepwise selection**: Forward/backward variable selection optimizing AUC across multiple random seeds
- **P-value filtering**: Optional per-iteration univariate screening with FDR/Bonferroni correction
- **Evidence-based filtering**: Integrate Open Targets Platform gene-disease associations to prioritize candidates
- **Publication-ready figures**: High-resolution TIFF (300 DPI) and SVG outputs
- **Desktop GUI**: Tauri-based app for interactive analysis with real-time progress tracking
- **Reproducible environment**: Automated dependency management with pixi

## Installation

### Option A: Docker (All platforms including Windows)

Docker is the easiest way to get started, especially on Windows where pixi is not supported.

```bash
docker pull jyryu3161/prognosis-marker
```

That's it. See [Docker Usage](#docker) below for running analyses.

### Option B: pixi (macOS / Linux)

```bash
git clone https://github.com/jyryu3161/prognosis_marker.git
cd prognosis_marker
./install.sh
```

The script automatically installs pixi, R, all R packages, and verifies the setup.

<details>
<summary>Manual pixi install</summary>

```bash
# 1. Install pixi (package manager)
curl -fsSL https://pixi.sh/install.sh | bash
export PATH="$HOME/.pixi/bin:$PATH"

# 2. Install R and conda-forge dependencies
pixi install

# 3. Install CRAN packages (cutpointr, nsROC, coefplot, etc.)
pixi run install-r-packages

# 4. Verify installation
pixi run Rscript -e "library(cutpointr); library(nsROC); cat('All packages OK\n')"
```

</details>

### GUI Installation (Optional)

The desktop GUI requires Node.js and Rust in addition to the R environment.

```bash
# Prerequisites
# - Node.js >= 18: https://nodejs.org
# - Rust: https://rustup.rs

# Install frontend dependencies
cd gui
npm install

# Run in development mode
npx @tauri-apps/cli dev

# Build distributable app
npx @tauri-apps/cli build
```

## Usage

### Docker

Mount your working directory as `/work` and use `/work/` paths in config:

```bash
# Binary classification
docker run --rm -v $(pwd):/work jyryu3161/prognosis-marker \
  binary --config=/work/config/analysis.yaml

# Survival analysis
docker run --rm -v $(pwd):/work jyryu3161/prognosis-marker \
  survival --config=/work/config/analysis.yaml
```

Windows (Command Prompt):
```bat
docker run --rm -v %cd%:/work jyryu3161/prognosis-marker ^
  binary --config=/work/config/analysis.yaml
```

Convenience wrapper scripts are also included:
```bash
# Mac/Linux
./run_docker.sh binary --config=/work/config/analysis.yaml

# Windows
run_docker.bat binary --config=/work/config/analysis.yaml
```

In your YAML config, use `/work/` paths for data and output when running via Docker:
```yaml
workdir: "/work"
binary:
  data_file: "/work/data/my_data.csv"
  output_dir: "/work/results/binary"
```

### Option 1: Command Line (Recommended for Large Datasets)

For computationally intensive analyses (large gene sets, many iterations), use the command line directly. This avoids GUI overhead and allows running on remote servers or in background.

```bash
# Binary classification
./run_analysis.sh binary --config config/example_analysis.yaml

# Survival analysis
./run_analysis.sh survival --config config/example_analysis.yaml
```

Or call pixi directly:

```bash
pixi run Rscript Main_Binary.R --config=config/my_config.yaml
pixi run Rscript Main_Survival.R --config=config/my_config.yaml
```

**Tip**: For large datasets (>10,000 genes) with many iterations (num_seed > 50), command-line execution is strongly recommended. You can run analyses in the background with `nohup`:

```bash
nohup ./run_analysis.sh binary --config config/my_config.yaml > analysis.log 2>&1 &
```

### Option 2: Desktop GUI

The GUI provides an interactive interface for configuring and running analyses with real-time progress tracking and plot preview.

```bash
cd gui
npx @tauri-apps/cli dev
```

GUI features:
- CSV file browser with column preview
- Column mapping for sample ID, outcome, and time variables
- Parameter configuration with sensible defaults
- Real-time log output and progress bar
- Plot preview (SVG/PNG) with export to TIFF (300 DPI) for publication
- Save/load configuration files (YAML)

## Configuration

### YAML Config File

```yaml
workdir: "."

binary:
  data_file: data/my_data.csv
  sample_id: sample
  outcome: OS                    # Binary outcome column (0/1)
  time_variable: OS.year         # Optional time variable
  split_prop: 0.7               # Train/test split ratio
  num_seed: 100                 # Number of random seed iterations
  output_dir: results/binary
  freq: 50                      # Min frequency across seeds to be candidate
  exclude: []                   # Columns to exclude
  include: []                   # Columns to include (empty = all)

  # P-value filtering (optional)
  top_k: 100                    # Keep top K genes per iteration
  p_adjust_method: none         # "none", "fdr", or "bonferroni"
  p_threshold: 0.05             # Significance cutoff

  # Performance tuning (optional)
  max_candidates_per_step: 200  # Cap candidates per forward step
  prescreen_seeds: 10           # Seeds for pre-screening

survival:
  data_file: data/my_data.csv
  sample_id: sample
  time_variable: OS.year         # Survival time column
  event: OS                      # Event indicator column (0/1)
  horizon: 5                     # Time horizon for AUC
  split_prop: 0.7
  num_seed: 100
  output_dir: results/survival
  freq: 50
  exclude: []
  include: []

# Evidence-based gene filtering (optional)
evidence:
  gene_file: evidence_genes.csv  # CSV with gene_symbol and overall_score columns
  score_threshold: 0.5           # Minimum association score
  source: "Open Targets Platform"
  disease_name: "breast carcinoma"
  efo_id: "EFO_0000305"
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `num_seed` | Number of random seed iterations for stability | 100 |
| `split_prop` | Train/test split proportion | 0.7 |
| `freq` | Min frequency threshold for candidate selection | 50 |
| `top_k` | Limit candidates to top K per iteration | NULL (all) |
| `p_adjust_method` | P-value correction: `"none"`, `"fdr"`, `"bonferroni"` | `"none"` |
| `p_threshold` | Significance threshold for filtering | 0.05 |
| `max_candidates_per_step` | Cap per forward step (enables pre-screening) | NULL |
| `prescreen_seeds` | Seeds for pre-screening evaluation | NULL |
| `horizon` | Time horizon for survival AUC (years) | 5 |

## Output Files

Results are saved in the configured `output_dir`:

```
output_dir/
├── figures/
│   ├── Binary_ROCcurve.svg          # Train/test ROC curves
│   ├── Binary_ROCcurve.tiff         # 300 DPI for publication
│   ├── Binary_Variable_Importance.svg
│   ├── Binary_Variable_Importance.tiff
│   ├── Survival_KaplanMeier.svg     # Kaplan-Meier curves
│   ├── Survival_TimeDependentAUC.svg # Time-dependent AUC
│   └── Survival_DCA.svg             # Decision curve analysis
├── StepBin/ or StepSurv/
│   ├── Intermediate_Forward*.csv    # Forward step details
│   ├── Intermediate_Stepwise_Total.csv
│   └── Final_Stepwise_Total.csv     # Final selected variables
├── ExtCandidat/
│   ├── *_seed*.csv                  # Per-seed univariate results
│   └── *_UnivariateResults.csv      # Aggregated results
├── auc_iterations.csv               # AUC per seed
└── analysis.log                     # Full execution log
```

## Project Structure

```
prognosis_marker/
├── Main_Binary.R                    # Binary classification entry point
├── Main_Survival.R                  # Survival analysis entry point
├── Binary_TrainAUC_StepwiseSelection.R
├── Survival_TrainAUC_StepwiseSelection.R
├── config/                          # YAML configuration files
│   ├── example_analysis.yaml
│   └── TCGA_*_analysis.yaml         # TCGA pan-cancer configs
├── gui/                             # Tauri desktop GUI
│   ├── src/                         # React frontend
│   └── src-tauri/                   # Rust backend
├── Dockerfile                       # Docker image definition
├── docker-entrypoint.sh             # Docker entrypoint script
├── run_docker.sh                    # Docker wrapper (Mac/Linux)
├── run_docker.bat                   # Docker wrapper (Windows)
├── pixi.toml                        # Dependency specification
├── install.sh                       # Automated installer
└── run_analysis.sh                  # CLI runner script
```

## Troubleshooting

### R packages fail to install

The pixi environment includes compilers for building CRAN packages from source. If installation fails:

```bash
# Ensure compilers are available
pixi install

# Retry CRAN packages
pixi run install-r-packages

# Test specific packages
pixi run Rscript -e "library(cutpointr); library(nsROC); cat('OK\n')"
```

### "Package not found" error during analysis

The GUI sets `R_LIBS` automatically, but for CLI usage ensure you use `pixi run`:

```bash
# Correct: uses pixi's R environment
pixi run Rscript Main_Binary.R --config=my_config.yaml

# Incorrect: may use system R without required packages
Rscript Main_Binary.R --config=my_config.yaml
```

### Config errors

- Ensure column names in YAML match your CSV headers exactly
- `output_dir` can be absolute (`/home/user/results`) or relative (`results/binary`)
- For survival analysis, both `time_variable` and `event` columns must exist

### Permission denied

```bash
chmod +x install.sh run_analysis.sh
```

## Requirements

- **Docker** (recommended for Windows, works on all platforms)
- **R >= 4.3** (installed automatically via pixi on macOS/Linux)
- **pixi** (installed automatically by `install.sh`, macOS/Linux only)
- For GUI: Node.js >= 18, Rust >= 1.70
