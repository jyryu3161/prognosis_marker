#!/usr/bin/env python3
"""
Fetch disease-associated genes from Open Targets Platform GraphQL API.

Uses the TCGA-to-EFO mapping to query Open Targets for genes associated with
each cancer type, producing evidence CSV files for downstream filtering.

Usage:
    python3 fetch_opentargets_genes.py [--score-threshold 0.1] [--datasets TCGA_BRCA TCGA_CHOL]
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

API_URL = "https://api.platform.opentargets.org/api/v4/graphql"
MAPPING_FILE = "tcga_efo_mapping.json"
EVIDENCE_DIR = "evidence"
PAGE_SIZE = 500
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2  # seconds, exponential backoff


def load_mapping(mapping_file):
    with open(mapping_file, "r") as f:
        return json.load(f)


def graphql_query(disease_id, page_size, page_index):
    """Build GraphQL query for associated targets of a disease."""
    return {
        "query": f"""
        {{
          disease(efoId: "{disease_id}") {{
            id
            name
            associatedTargets(
              page: {{ size: {page_size}, index: {page_index} }}
            ) {{
              count
              rows {{
                target {{
                  id
                  approvedSymbol
                }}
                score
              }}
            }}
          }}
        }}
        """
    }


def fetch_page(disease_id, page_size, page_index):
    """Fetch one page of associated targets with retry logic."""
    payload = json.dumps(graphql_query(disease_id, page_size, page_index)).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "errors" in data:
                print(f"  GraphQL errors: {data['errors']}", file=sys.stderr)
                return None
            return data["data"]["disease"]
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            delay = RETRY_BASE_DELAY ** attempt
            print(
                f"  Attempt {attempt}/{MAX_RETRIES} failed: {e}. "
                f"Retrying in {delay}s...",
                file=sys.stderr,
            )
            if attempt < MAX_RETRIES:
                time.sleep(delay)
            else:
                print(f"  All {MAX_RETRIES} attempts failed.", file=sys.stderr)
                return None


def fetch_all_targets(disease_id, score_threshold):
    """Fetch all associated targets for a disease with pagination."""
    targets = []
    page_index = 0

    while True:
        result = fetch_page(disease_id, PAGE_SIZE, page_index)
        if result is None:
            break

        assoc = result.get("associatedTargets")
        if assoc is None:
            break

        disease_name = result.get("name", "")
        total_count = assoc.get("count", 0)
        rows = assoc.get("rows", [])

        if page_index == 0:
            print(f"  Total associated targets: {total_count}", file=sys.stderr)

        if not rows:
            break

        hit_threshold = False
        for row in rows:
            score = row.get("score", 0)
            if score < score_threshold:
                # Rows are sorted by score descending; stop early
                hit_threshold = True
                break
            targets.append(
                {
                    "gene_symbol": row["target"]["approvedSymbol"],
                    "ensembl_id": row["target"]["id"],
                    "score": score,
                    "disease_name": disease_name,
                }
            )

        if hit_threshold:
            break

        # Check if we've fetched all targets
        if len(rows) < PAGE_SIZE:
            break

        page_index += 1
        # Rate limiting: small delay between pages
        time.sleep(0.2)

    final_disease_name = disease_name if disease_name else ""
    final_total = total_count if total_count else len(targets)
    return targets, final_disease_name, final_total


def write_csv(targets, efo_id, output_path):
    """Write target list to CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["gene_symbol", "ensembl_id", "score", "disease_name", "efo_id"])
        for t in targets:
            writer.writerow(
                [t["gene_symbol"], t["ensembl_id"], t["score"], t["disease_name"], efo_id]
            )


def main():
    parser = argparse.ArgumentParser(
        description="Fetch disease-associated genes from Open Targets Platform"
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.1,
        help="Minimum overall association score (default: 0.1)",
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
        "--output-dir",
        default=EVIDENCE_DIR,
        help=f"Output directory for gene CSV files (default: {EVIDENCE_DIR})",
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

    os.makedirs(args.output_dir, exist_ok=True)

    # Summary tracking
    summary = {
        "fetch_date": datetime.now().isoformat(),
        "score_threshold": args.score_threshold,
        "datasets": {},
    }

    total = len(datasets)
    success_count = 0
    fail_count = 0

    print(f"Fetching genes for {total} datasets (score >= {args.score_threshold})")
    print("=" * 60)

    for i, (dataset, info) in enumerate(sorted(datasets.items()), 1):
        efo_id = info["efo_id"]
        disease_name = info["disease_name"]
        output_path = os.path.join(args.output_dir, f"{dataset}_opentargets_genes.csv")

        print(f"\n[{i}/{total}] {dataset}: {disease_name} ({efo_id})")

        targets, api_disease_name, total_count = fetch_all_targets(
            efo_id, args.score_threshold
        )

        if targets is not None:
            write_csv(targets, efo_id, output_path)
            print(f"  Saved {len(targets)} genes to {output_path}")
            summary["datasets"][dataset] = {
                "efo_id": efo_id,
                "disease_name": api_disease_name or disease_name,
                "gene_count": len(targets),
                "total_associated": total_count,
                "output_file": output_path,
            }
            success_count += 1
        else:
            # Write empty CSV on failure
            write_csv([], efo_id, output_path)
            print(f"  Failed to fetch. Empty CSV written to {output_path}")
            summary["datasets"][dataset] = {
                "efo_id": efo_id,
                "disease_name": disease_name,
                "gene_count": 0,
                "error": "API fetch failed",
                "output_file": output_path,
            }
            fail_count += 1

    # Write summary
    summary_path = os.path.join(args.output_dir, "fetch_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print(f"Done: {success_count} succeeded, {fail_count} failed")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
