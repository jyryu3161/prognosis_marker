#!/usr/bin/env python3
"""
Generate Open Targets evidence-filtered analysis configuration files.

Reads existing TCGA config files and creates new configs with an 'evidence'
section and redirected output directories.

Usage:
    python3 generate_opentargets_configs.py [--datasets TCGA_BRCA TCGA_CHOL]
    python3 generate_opentargets_configs.py --score-threshold 0.2
"""

import argparse
import glob
import json
import os
import sys

import yaml

MAPPING_FILE = "tcga_efo_mapping.json"
EVIDENCE_DIR = "evidence"
CONFIG_DIR = "config"


def load_mapping(mapping_file):
    with open(mapping_file, "r") as f:
        return json.load(f)


def generate_config(dataset, base_config_path, mapping_info, score_threshold, evidence_dir):
    """Generate an opentargets-filtered config from a base config."""
    with open(base_config_path, "r") as f:
        config = yaml.safe_load(f)

    evidence_file = os.path.join(evidence_dir, f"{dataset}_opentargets_genes.csv")

    # Check that evidence file exists
    if not os.path.exists(evidence_file):
        print(f"  Warning: Evidence file not found: {evidence_file}", file=sys.stderr)
        return None

    # Add evidence section
    config["evidence"] = {
        "gene_file": evidence_file,
        "score_threshold": score_threshold,
        "source": "Open Targets Platform",
        "disease_name": mapping_info["disease_name"],
        "efo_id": mapping_info["efo_id"],
    }

    # Update output directories for binary
    if "binary" in config:
        config["binary"]["output_dir"] = f"results/{dataset}_opentargets/binary"

    # Update output directories for survival
    if "survival" in config:
        config["survival"]["output_dir"] = f"results/{dataset}_opentargets/survival"

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Generate Open Targets evidence-filtered analysis configs"
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.1,
        help="Score threshold for evidence filtering (default: 0.1)",
    )
    parser.add_argument(
        "--datasets",
        nargs="*",
        default=None,
        help="Specific TCGA dataset names (e.g., TCGA_BRCA TCGA_CHOL). Default: all.",
    )
    parser.add_argument(
        "--mapping-file",
        default=MAPPING_FILE,
        help=f"Path to TCGA-EFO mapping JSON (default: {MAPPING_FILE})",
    )
    parser.add_argument(
        "--evidence-dir",
        default=EVIDENCE_DIR,
        help=f"Directory containing evidence CSV files (default: {EVIDENCE_DIR})",
    )
    parser.add_argument(
        "--config-dir",
        default=CONFIG_DIR,
        help=f"Directory for config files (default: {CONFIG_DIR})",
    )
    args = parser.parse_args()

    # Load mapping
    if not os.path.exists(args.mapping_file):
        print(f"Error: Mapping file not found: {args.mapping_file}", file=sys.stderr)
        sys.exit(1)

    mapping = load_mapping(args.mapping_file)

    # Select datasets
    if args.datasets:
        datasets = {k: v for k, v in mapping.items() if k in args.datasets}
        missing = set(args.datasets) - set(datasets.keys())
        if missing:
            print(f"Warning: Unknown datasets: {missing}", file=sys.stderr)
    else:
        datasets = mapping

    if not datasets:
        print("No datasets to process.", file=sys.stderr)
        sys.exit(1)

    total = len(datasets)
    created = 0
    skipped = 0

    print(f"Generating opentargets configs for {total} datasets")
    print("=" * 60)

    for dataset, info in sorted(datasets.items()):
        base_config = os.path.join(args.config_dir, f"{dataset}_analysis.yaml")
        output_config = os.path.join(args.config_dir, f"{dataset}_opentargets_analysis.yaml")

        if not os.path.exists(base_config):
            print(f"  Skipping {dataset}: base config not found ({base_config})")
            skipped += 1
            continue

        config = generate_config(
            dataset, base_config, info, args.score_threshold, args.evidence_dir
        )
        if config is None:
            skipped += 1
            continue

        with open(output_config, "w") as f:
            # Write header comment
            f.write(f"# Open Targets evidence-filtered configuration for {dataset}\n")
            f.write(f"# Disease: {info['disease_name']} ({info['efo_id']})\n")
            f.write(f"# Generated from: {os.path.basename(base_config)}\n")

            # Use custom representer to quote strings that YAML would
            # otherwise interpret as non-string (e.g., "." becomes boolean)
            class QuotedDumper(yaml.SafeDumper):
                pass

            def str_representer(dumper, data):
                if data in (".", "~", "null", "true", "false", "yes", "no",
                            "on", "off", "none"):
                    return dumper.represent_scalar(
                        "tag:yaml.org,2002:str", data, style='"'
                    )
                return dumper.represent_scalar("tag:yaml.org,2002:str", data)

            QuotedDumper.add_representer(str, str_representer)

            yaml.dump(config, f, Dumper=QuotedDumper,
                      default_flow_style=False, sort_keys=False)

        print(f"  Created: {output_config}")
        created += 1

    print("\n" + "=" * 60)
    print(f"Done: {created} configs created, {skipped} skipped")


if __name__ == "__main__":
    main()
