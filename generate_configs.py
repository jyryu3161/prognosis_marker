#!/usr/bin/env python3
"""
Generate configuration files for all TCGA datasets
"""

import os
import glob

# Get all TCGA data files
data_dir = "./data"
data_files = sorted(glob.glob(os.path.join(data_dir, "TCGA_*_data.csv")))

# Extract dataset names
datasets = [os.path.basename(f).replace("_data.csv", "") for f in data_files]

# Configuration template
config_template = """# Configuration for {dataset}
workdir: "."
data_file: data/{dataset}_data.csv

binary:
  data_file: data/{dataset}_data.csv
  sample_id: sample
  outcome: OS
  time_variable: OS.year
  split_prop: 0.7
  num_seed: 100  # Number of iterations
  output_dir: results/{dataset}/binary
  freq: 50  # Cutoff for most frequent significant genes (50% of 100 iterations)
  exclude: []
  include: []
  # Optionally constrain the candidate feature set by listing column names here.
  # features:

  # P-value adjustment and filtering options
  top_k: 1000  # Select top 1000 genes by adjusted p-value per iteration
  p_adjust_method: fdr  # P-value adjustment method: "fdr" or "bonferroni"
  p_threshold: 0.05  # Adjusted p-value threshold

survival:
  data_file: data/{dataset}_data.csv
  sample_id: sample
  time_variable: OS.year
  event: OS
  horizon: 5
  split_prop: 0.7
  num_seed: 100  # Number of iterations
  output_dir: results/{dataset}/survival
  freq: 50  # Cutoff for most frequent significant genes (50% of 100 iterations)
  exclude: []
  include: []
  # Optionally constrain the candidate feature set by listing column names here.
  # features:

  # P-value adjustment and filtering options
  top_k: 1000  # Select top 1000 genes by adjusted p-value per iteration
  p_adjust_method: fdr  # P-value adjustment method: "fdr" or "bonferroni"
  p_threshold: 0.05  # Adjusted p-value threshold
"""

# Create config directory if it doesn't exist
os.makedirs("./config", exist_ok=True)

# Generate configuration files
for dataset in datasets:
    config_content = config_template.format(dataset=dataset)
    config_filename = f"./config/{dataset}_analysis.yaml"

    with open(config_filename, 'w') as f:
        f.write(config_content)

    print(f"Created: {config_filename}")

print(f"\nTotal configurations created: {len(datasets)}")
