#!/bin/bash

#>>> ADJUST THE FOLLOWING
#SBATCH --partition=gpu
#SBATCH --gres=gpu:pascal:1
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH --job-name=petgui

#<<< DON'T CHANGE THE FOLLOWING
#SBATCH --output=petgui_logging.txt

pwd
. petgui/bin/activate
pip install -r "$1"/pet/requirements.txt
cd "$1"/pet/
python3 run.py

