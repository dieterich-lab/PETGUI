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
#SBATCH --output=logging.txt

pwd
. petgui/bin/activate
cd "$1"/pet/
python3 predict.py

