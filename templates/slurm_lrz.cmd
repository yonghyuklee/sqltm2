#!/bin/bash --posix
# SLURM workload manager submission script
# MPP2: 60 nodes/48 h max

# submit 20 jobs and put them on hold:
# for i in {1..20}; do id=$(sbatch slurm_lrz.cmd | awk '{print $4}'); scontrol hold $id; done

#SBATCH --nodes=20
#SBATCH --time=1-00:00:00
# #SBATCH --time=02:00:00
#SBATCH --clusters=mpp2
#SBATCH --ntasks-per-node=28
#SBATCH --cpus-per-task=1
#SBATCH -J sqltm
#SBATCH --get-user-env
#SBATCH --mail-user=opalka@ch.tum.de
#SBATCH --mail-type=begin
#SBATCH --export=none
#SBATCH --output %j.out

# set symbolic links to SQLTM and TSS root directory
export TSS="${WORK}/tss"
export MYSQL_CNF="${HOME}/.lc.cnf"
export LOGIN_HOST="mpp2-login5"


export TMPDIR="${SCRATCH}"
export REVERSE_SHELL=1
export TIME_BUFFER="600"
export OMP_NUM_THREADS=1
export MKL_SERIAL=yes
export I_MPI_PIN_DOMAIN=omp
export I_MPI_HYDRA_BOOTSTRAP=slurm

export SQLTM_BASE="${WORK}/sqltm"
export flag_pending=8

bash ${SQLTM_BASE}/lib/slurmsql.sh opalka
