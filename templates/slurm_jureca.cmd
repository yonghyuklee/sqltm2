# SLURM workload manager submission script

#!/bin/bash --posix
#SBATCH --nodes=2
# #SBATCH --time=1-00:00:00
#SBATCH --time=02:00:00
#SBATCH --clusters=jureca
#SBATCH --ntasks-per-node=24
#SBATCH -J sp
#SBATCH --partition=batch
#SBATCH --cpus-per-task=1
#SBATCH --get-user-env
#SBATCH --export=none
#SBATCH --output %j.out

#. /etc/profile
#. /etc/profile.d/modules.sh

export TMPDIR="${SCRATCH}"
export TIME_BUFFER="600"
export REVERSE_SHELL=1
export LOGIN_HOST=""

export OMP_NUM_THREADS=1
export MKL_SERIAL=yes
export I_MPI_PIN_DOMAIN=omp

# set symbolic links to SQLTM and TSS root directory
export TSS="${HOME}/tss"
export SQLTM_BASE="${HOME}/sqltm"
#export MYSQL_CNF="${HOME}/.my.cnf"

# JURECA settings
#export HOME=/homea/hmu23/hmu231
#export TMPDIR=/work/hmu23/hmu231

#bash ${SQLTM_BASE}/lib/llsql.sh <db>.sqlite
bash ${SQLTM_BASE}/lib/llsql.sh <db>
