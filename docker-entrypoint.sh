#!/bin/bash
set -e

case "$1" in
  binary)
    shift
    exec Rscript /app/Main_Binary.R "$@"
    ;;
  survival)
    shift
    exec Rscript /app/Main_Survival.R "$@"
    ;;
  --help|"")
    echo "PROMISE - PROgnostic Marker Identification and Survival Evaluation"
    echo ""
    echo "Usage:"
    echo "  docker run --rm -v \$(pwd):/work jyryu3161/promise binary   --config=/work/config.yaml"
    echo "  docker run --rm -v \$(pwd):/work jyryu3161/promise survival --config=/work/config.yaml"
    echo ""
    echo "Commands:"
    echo "  binary     Run binary classification (logistic regression)"
    echo "  survival   Run survival analysis (Cox proportional hazards)"
    echo ""
    echo "Options:"
    echo "  --config=<path>  Path to YAML config file (use /work/ prefix for mounted files)"
    echo ""
    echo "Example:"
    echo "  docker run --rm -v \$(pwd):/work jyryu3161/promise \\"
    echo "    binary --config=/work/config/example_analysis.yaml"
    ;;
  *)
    exec "$@"
    ;;
esac
