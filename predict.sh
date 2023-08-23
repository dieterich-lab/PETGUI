#!/bin/bash

#SBATCH --gres=gpu:pascal:1
#SBATCH --partition=gpu
#SBATCH --job-name=petgui
#SBATCH --output=logging.txt

pwd
. /beegfs/biosw/petgui/dev/env/bin/activate
cd "$1"/pet/
python3 predict.py
