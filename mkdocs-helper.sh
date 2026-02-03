#!/bin/bash
# Helper script to run mkdocs commands with correct PYTHONPATH
# Usage: ./mkdocs-helper.sh [mkdocs-command-and-arguments]

# Set PYTHONPATH to user site-packages where mkdocs is installed
export PYTHONPATH="C:\Users\MohithGupta\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages"

# Run mkdocs with the provided arguments
python -m mkdocs "$@"
