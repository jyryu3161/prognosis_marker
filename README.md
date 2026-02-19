# PROMISE

**PROgnostic Marker Identification and Survival Evaluation**

AUC-driven stepwise variable selection for prognostic gene signature discovery. Supports binary classification (logistic regression) and survival analysis (Cox proportional hazards) with reproducible train/test splitting.

## Features

- **Binary classification**: Logistic regression with ROC analysis
- **Survival analysis**: Cox proportional hazards with time-dependent AUC and Kaplan-Meier curves
- **Stepwise selection**: Forward/backward variable selection optimizing AUC across multiple random seeds
- **Evidence-based filtering**: Open Targets Platform gene-disease association integration
- **Publication-ready figures**: TIFF (300 DPI) and SVG outputs
- **Desktop GUI**: Interactive analysis with real-time progress tracking
- **Cross-platform**: Docker (all OS) + pixi (macOS/Linux/Windows)

## Install

### Option A: Desktop GUI (Download)

Pre-built installers are available on the [Releases](https://github.com/jyryu3161/prognosis_marker/releases) page:

| Platform | File |
|----------|------|
| macOS (Apple Silicon) | `.dmg` |
| macOS (Intel) | `.dmg` |
| Windows | `.msi` / `.exe` |
| Linux | `.deb` / `.AppImage` |

> **Note**: The GUI is for configuring and launching analyses. R and pixi must be installed separately for the analysis engine. Run `./install.sh` after downloading, or use Docker for the CLI.

### Option B: Docker CLI (All platforms)

```bash
docker pull jyryu3161/promise

# Binary classification
docker run --rm -v $(pwd):/work jyryu3161/promise \
  binary --config=/work/config/analysis.yaml

# Survival analysis
docker run --rm -v $(pwd):/work jyryu3161/promise \
  survival --config=/work/config/analysis.yaml
```

Windows:
```bat
docker run --rm -v %cd%:/work jyryu3161/promise binary --config=/work/config/analysis.yaml
```

### Option C: Native Install (macOS / Linux / Windows)

```bash
git clone https://github.com/jyryu3161/prognosis_marker.git
cd prognosis_marker
./install.sh
```

## Usage

### Command Line

```bash
# Using the run script
./run_analysis.sh binary --config config/example_analysis.yaml
./run_analysis.sh survival --config config/example_analysis.yaml

# Or pixi directly
pixi run Rscript Main_Binary.R --config=config/my_config.yaml
pixi run Rscript Main_Survival.R --config=config/my_config.yaml
```

### Desktop GUI

Pre-built installers: see [Releases](https://github.com/jyryu3161/prognosis_marker/releases).

Or build from source (requires [Node.js](https://nodejs.org) v18+ and [Rust](https://rustup.rs)):

```bash
./run_gui.sh
```

### Docker Wrapper Scripts

```bash
# Mac/Linux
./run_docker.sh binary --config=/work/config/analysis.yaml

# Windows
run_docker.bat binary --config=/work/config/analysis.yaml
```

> When using Docker, set paths relative to `/work/` in your config (e.g., `data_file: "/work/data/my_data.csv"`).

## Configuration

Create a YAML config file (see `config/example_analysis.yaml`):

```yaml
workdir: "."

binary:
  data_file: data/my_data.csv
  sample_id: sample
  outcome: OS
  split_prop: 0.7
  num_seed: 100
  output_dir: results/binary
  freq: 50

survival:
  data_file: data/my_data.csv
  sample_id: sample
  time_variable: OS.year
  event: OS
  horizon: 5
  split_prop: 0.7
  num_seed: 100
  output_dir: results/survival
  freq: 50
```

<details>
<summary>All parameters</summary>

| Parameter | Description | Default |
|-----------|-------------|---------|
| `num_seed` | Random seed iterations for stability | 100 |
| `split_prop` | Train/test split ratio | 0.7 |
| `freq` | Min frequency for candidate selection | 50 |
| `top_k` | Limit candidates to top K per iteration | NULL (all) |
| `p_adjust_method` | P-value correction: `"none"`, `"fdr"`, `"bonferroni"` | `"none"` |
| `p_threshold` | Significance threshold | 0.05 |
| `max_candidates_per_step` | Cap per forward step | NULL |
| `prescreen_seeds` | Seeds for pre-screening | NULL |
| `horizon` | Time horizon for survival AUC (years) | 5 |
| `exclude` | Columns to exclude from analysis | `[]` |
| `include` | Columns to force-include | `[]` |

**Evidence-based filtering** (optional):
```yaml
evidence:
  gene_file: evidence_genes.csv
  score_threshold: 0.5
```

</details>

## Output

Results are saved in the configured `output_dir`:

```
output_dir/
├── figures/                    # ROC curves, KM plots, variable importance (SVG + TIFF)
├── StepBin/ or StepSurv/      # Stepwise selection intermediates + final result
├── ExtCandidat/                # Per-seed univariate results
└── auc_iterations.csv          # AUC per seed
```

## Troubleshooting

- **macOS "damaged" error**: The app is not Apple-signed. Remove the quarantine flag after installing:
  ```bash
  xattr -cr /Applications/PROMISE.app
  ```
- **Missing packages**: `pixi install && pixi run install-r-packages`
- **"Package not found"**: Use `pixi run Rscript ...` instead of `Rscript ...` directly
- **Config errors**: Ensure column names in YAML match CSV headers exactly
- **Permission denied**: `chmod +x install.sh run_analysis.sh run_gui.sh`

## Requirements

| Component | Requirement |
|-----------|-------------|
| **CLI (Docker)** | Docker |
| **CLI (Native)** | macOS/Linux/Windows, pixi (auto-installed) |
| **GUI (Download)** | [Releases](https://github.com/jyryu3161/prognosis_marker/releases) page |
| **GUI (Build)** | Node.js >= 18, Rust >= 1.70 |
