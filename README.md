# Prognosis Marker

Prognostic gene signature workflows with AUC-driven stepwise selection for binary outcomes and survival endpoints.

## Features

- **Binary classification**: Logistic regression with train/test splitting and ROC analysis
- **Survival analysis**: Cox proportional hazards with time-dependent ROC curves
- **Co-expression network analysis**: Gene-gene correlation networks for marker sets
- **GO enrichment analysis**: Functional annotation of marker genes and co-expressed genes
- **Reproducible**: Automated dependency management with pixi
- **Publication-ready**: High-resolution figures (PNG/TIFF/SVG) with coefficient plots

## Installation

### Quick Install

```bash
./install.sh
```

This script automatically:
- Installs pixi if needed
- Sets up the R/Python environment
- Installs all dependencies
- Launches the Streamlit web interface (optional)

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

# Co-expression and GO enrichment post-processing
# (automatically processes both binary and survival results if available)
./run_analysis.sh coexpression --config config/example_analysis.yaml
```

Or use pixi directly:

```bash
pixi run binary -- --config config/example_analysis.yaml
pixi run survival -- --config config/example_analysis.yaml
pixi run coexpression -- --config config/example_analysis.yaml
```

### Configuration

Create a YAML config file (see `config/example_analysis.yaml` for template):

```yaml
workdir: .
data_file: your_data.csv

# Co-expression network parameters
coexpression:
  correlation_threshold: 0.7  # Absolute Pearson correlation cutoff for network edges

binary:
  sample_id: sample
  outcome: OS
  split_prop: 0.7
  num_seed: 100
  output_dir: results/binary

survival:
  sample_id: sample
  time_variable: OS.year
  event: OS
  horizon: 5
  split_prop: 0.7
  num_seed: 100
  output_dir: results/survival
```

### Output Files

#### Binary/Survival Analysis Results

Main analysis results are saved in the configured output directory:
- `ROCcurve.{png,tiff,svg}`: Train/test ROC curves
- `Variable_Importance.{png,tiff,svg}`: Coefficient plots
- `auc_iterations.csv`: Performance metrics per iteration
- `Intermediate_*.csv`: Stepwise selection details

#### Co-expression Network Analysis Results

Post-processing results are saved in `{output_dir}/coexpression/`:
- `selected_genes.csv`: Marker genes and co-expressed genes
- `coexpression_edges.csv`: Gene-gene correlations (edges in the network)
- `coexpression_network.png`: Network visualization
- `go_enrichment_results.csv`: GO biological process enrichment results
- `go_enrichment_dotplot.png`: GO enrichment visualization

**Note**: The co-expression analysis automatically processes both binary and survival results if their configurations are present in the YAML file.

## Streamlit Web Interface

간단한 웹 UI로 분석 실행:

```bash
./run_server.sh
```

브라우저에서 http://localhost:8501 열기

**기능:**
- 데이터 업로드 (CSV)
- 분석 타입 선택 (Binary/Survival)
- 파라미터 설정
- 결과 시각화 및 다운로드

## Troubleshooting

- **Missing packages**: Run `pixi install` and `pixi run install-r-packages`
- **Config errors**: Ensure column names in YAML match your CSV file
- **Permission denied**: Make scripts executable: `chmod +x *.sh`

## Requirements

- R ≥ 4.3
- Python ≥ 3.9
- pixi (installed automatically by `install.sh`)