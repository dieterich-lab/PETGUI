#!/bin/bash

#SBATCH --partition=gpu
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH --job-name=petgui
#SBATCH --output=logging.txt

pwd
. /beegfs/biosw/petgui/dev/venv/bin/activate
cd "$1"/pet/
python3 predict.py

