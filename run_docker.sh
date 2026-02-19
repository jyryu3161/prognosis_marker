#!/bin/bash
# PROMISE - Docker wrapper script
# Usage: ./run_docker.sh binary --config=/work/config/analysis.yaml
#        ./run_docker.sh survival --config=/work/config/analysis.yaml

docker run --rm -v "$(pwd):/work" jyryu3161/prognosis-marker "$@"
