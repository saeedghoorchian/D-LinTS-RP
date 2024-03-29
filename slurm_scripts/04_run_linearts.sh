#!/bin/bash

#SBATCH --partition=cpu-long

#SBATCH --cpus-per-task=16
#SBATCH --nodes=1
# time in minutes
#SBATCH --time=2440

#SBATCH --output=log/04_run_linear_ts.log
#SBATCH --error=log/04_run_linear_ts.log

#SBATCH --mail-type=END
#SBATCH --mail-user=elephunker1@gmail.com

# For debug:
scontrol show job $SLURM_JOB_ID


source /home/maghsudi/ekortukov80/.bashrc
conda activate bandit_env
python 4_tune_parameters.py --data movielens --trials 30000 --dimension 15 --num-rep 3 --config config/linearts.json --tune
