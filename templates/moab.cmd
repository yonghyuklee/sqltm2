# MOAB workload manager submission script
# https://computing.llnl.gov/tutorials/moab/

# submit 20 jobs and put them on hold:
# for i in {1..20}; do id=$(ccc_msub moab.cmd | awk '{print $4}'); scontrol hold $id; done

#!/bin/bash --posix
#MSUB -r SQLTM
#MSUB -n 14
#MSUB -c 1
#MSUB -T 1000
#MSUB -o %j.out
#MSUB -e %j.err
#MSUB -A ra3953
#MSUB -q standard
# #MSUB -q large
#MSUB -Q test

export TMPDIR="${SCRATCHDIR}"
export TIME_BUFFER="600"
export REVERSE_SHELL=1
export LOGIN_HOST="curie50"

export OMP_NUM_THREADS=1
export MKL_SERIAL=yes
export I_MPI_PIN_DOMAIN=omp

# set symbolic links to SQLTM and TSS root directory
export TSS="${HOME}/tss"
export SQLTM_BASE="${HOME}/sqltm"
export MYSQL_CNF="${HOME}/.curie.cnf"

#bash ${SQLTM_BASE}/lib/slurmsql.sh <db>.sqlite
bash ${SQLTM_BASE}/lib/slurmsql.sh <db>
