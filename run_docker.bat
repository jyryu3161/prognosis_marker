@echo off
REM PROMISE - Docker wrapper script for Windows
REM Usage: run_docker.bat binary --config=/work/config/analysis.yaml
REM        run_docker.bat survival --config=/work/config/analysis.yaml

docker run --rm -v "%cd%:/work" jyryu3161/prognosis-marker %*
