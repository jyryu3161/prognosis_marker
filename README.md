# Prognosis Marker

## Project overview
This repository bundles reproducible R workflows for deriving prognostic gene signatures with repeated train/test splits and AUC-driven stepwise selection for both binary outcomes and survival endpoints. The binary workflow fits logistic regression models with caret-powered resampling and produces ROC curves and coefficient importance plots, while persisting intermediate selection results for auditability.【F:Main_Binary.R†L1-L137】【F:Binary_TrainAUC_StepwiseSelection.R†L1-L120】 The survival workflow mirrors the same strategy with Cox proportional hazards models and time-dependent ROC estimation at a configurable horizon to support disease-free or overall survival analyses.【F:Main_Survival.R†L1-L150】【F:Survival_TrainAUC_StepwiseSelection.R†L1-L140】 Example inputs (`Example_data.csv`) and a YAML configuration template are included so you can run the pipelines end-to-end without additional assets.【F:Example_data.csv†L1-L5】【F:config/example_analysis.yaml†L1-L26】

## Prerequisites
- **R ≥ 4.3** with the following packages: `caret`, `ROCR`, `pROC`, `cutpointr`, `coefplot`, `ggplot2`, `yaml`, `nsROC`, and `survival`. These are loaded explicitly inside the workflow entrypoints.【F:Main_Binary.R†L1-L9】【F:Main_Survival.R†L1-L9】  
- Ability to create output folders in the working directory so that intermediate CSVs and publication-grade figures (PNG/TIFF/SVG) can be written by the scripts.【F:Main_Binary.R†L116-L137】【F:Main_Survival.R†L122-L143】

## Environment setup with pixi
1. [Install pixi](https://pixi.sh/latest/#installation) if it is not already available.
2. From the project root run `pixi install` to create the Conda-based environment declared in `pixi.toml`. This pulls in R 4.3 and the required libraries from conda-forge.【F:pixi.toml†L1-L24】
3. (Optional) Populate any missing CRAN-only dependencies by executing the provided helper task: `pixi run install-r-packages`. This mirrors the package set referenced above by calling `install.packages()` once the interpreter is available.【F:pixi.toml†L26-L28】
4. Use `pixi run` to execute the analysis tasks:
   - `pixi run binary` to launch the binary CLI with the default configuration.
   - `pixi run survival` to run the survival analysis.
   Additional CLI flags (e.g., `--config path/to/config.yaml`) can be appended after `--` and are forwarded to the underlying `Rscript` entrypoints.【F:pixi.toml†L29-L30】【F:Main_Binary.R†L11-L33】【F:Main_Survival.R†L11-L33】

## Configuration
All run-time options are captured in YAML. The template at `config/example_analysis.yaml` documents every field, including dataset paths, outcome columns, split proportions, iteration counts, output directories, and optional feature allow/deny lists for each analysis block.【F:config/example_analysis.yaml†L1-L26】 Key fields to review before launching a run:
- `workdir` and `data_file`: control where the scripts operate and which CSV they ingest.【F:Main_Binary.R†L35-L52】【F:Main_Survival.R†L35-L52】
- `binary.*` and `survival.*`: define sample identifiers, outcome/event columns, resampling seeds, output folders, and (for survival) the evaluation horizon in years.【F:Main_Binary.R†L54-L80】【F:Main_Survival.R†L54-L84】
- Optional `features` lists restrict the candidate predictors passed into the stepwise selector if you do not want to start from all columns automatically.【F:Main_Binary.R†L60-L66】【F:Main_Survival.R†L60-L67】

## Quickstart walkthrough (Example_data.csv)
1. Copy the template config and adapt it as needed:
   ```bash
   cp config/example_analysis.yaml analysis.yaml
   ```
   Adjust column names or iteration counts in `analysis.yaml` to match your cohort.
2. Activate the pixi environment and resolve dependencies:
   ```bash
   pixi install
   pixi run install-r-packages   # optional if conda packages are sufficient
   ```
3. Run the binary classifier pipeline on the included `Example_data.csv`:
   ```bash
   pixi run binary -- --config analysis.yaml
   ```
   The CLI reads the YAML file, loads the dataset, executes `BinTrainAUCStepwise()`, and persists summary metrics along with high-resolution ROC curves and coefficient plots in the configured output directory (defaults to `results/binary`).【F:Main_Binary.R†L68-L142】
4. Run the survival workflow in the same fashion:
   ```bash
   pixi run survival -- --config analysis.yaml
   ```
   This will evaluate time-dependent ROC curves at the requested horizon and save results under `results/survival`.【F:Main_Survival.R†L68-L143】
5. Inspect the outputs:
   - `results/*/Intermediate_*.csv`: step-by-step additions/removals recorded by the train AUC selection routine.【F:Binary_TrainAUC_StepwiseSelection.R†L45-L117】【F:Survival_TrainAUC_StepwiseSelection.R†L53-L132】
   - `results/*/auc_iterations.csv`: iteration-level train/test AUC values to review stability.【F:Main_Binary.R†L138-L141】【F:Main_Survival.R†L145-L148】
   - `results/*/ROCcurve.{png,tiff,svg}`: paired train/test ROC panels exported at 300 dpi (TIFF) and vector (SVG) resolution for high-impact journal figures.【F:Main_Binary.R†L104-L137】【F:Main_Survival.R†L110-L143】
   - `results/*/Variable_Importance.{png,tiff,svg}`: standardized coefficient visualisations for manuscript-ready effect size reporting.【F:Main_Binary.R†L143-L158】【F:Main_Survival.R†L145-L160】

## Interpreting the results
- **Performance summary** – the console output and `auc_iterations.csv` files list the mean train/test AUCs (± test SD) over all seeds so you can gauge model robustness.【F:Main_Binary.R†L132-L141】【F:Main_Survival.R†L136-L148】 Large gaps between train and test AUC point toward overfitting; increasing `num_seed` or adjusting `split_prop` can help assess sensitivity.【F:Main_Binary.R†L70-L80】【F:Main_Survival.R†L70-L84】
- **ROC panels** – the left panel aggregates train folds, while the right panel tracks the held-out splits. The bold overlay represents the mean curve across all iterations, and the legend reports the corresponding mean AUC with standard deviation.【F:Main_Binary.R†L104-L132】【F:Main_Survival.R†L110-L138】 Use the TIFF export when journals request 300 dpi rasters and the SVG when vector graphics are preferred.
- **Variable importance** – the coefficient plots show standardized effect sizes with 95% confidence intervals, making it straightforward to communicate the direction and magnitude of associations in manuscripts or slide decks.【F:Main_Binary.R†L143-L158】【F:Main_Survival.R†L145-L160】 Positive coefficients increase event risk/odds, while negative coefficients are protective.

## Troubleshooting
- **Missing packages** – if `Rscript` reports that a package cannot be loaded, re-run `pixi install` followed by `pixi run install-r-packages` to provision any remaining CRAN libraries.【F:pixi.toml†L26-L28】
- **Mismatched column names** – ensure that `sample_id`, `outcome`, `time_variable`, and `event` fields in the YAML match columns in your CSV; the scripts stop with a clear error when required fields are absent.【F:Main_Binary.R†L45-L58】【F:Main_Survival.R†L45-L62】
- **Output directory conflicts** – the workflows create their output folders on demand. If you re-run with the same directory and want a clean slate, delete the folder (e.g., `rm -rf results/binary`) before launching a new job.【F:Main_Binary.R†L116-L137】【F:Main_Survival.R†L122-L143】
- **Long runtimes** – decrease `num_seed` or use a larger `split_prop` to reduce the number of resampling iterations during early experimentation.【F:config/example_analysis.yaml†L7-L15】【F:config/example_analysis.yaml†L19-L26】 Once satisfied, revert to the default (100 iterations, 70/30 split) for publication-ready estimates.

