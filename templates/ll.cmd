# LoadLeveler (LL) workload manager submission script
# if using an sqlite3 database, the submission directory must contain the database file

#!/bin/bash --posix
#@ node = 3
#@ class = test
#@ wall_clock_limit = 00:30:00

# #@ class = micro
# #@ wall_clock_limit = 48:00:00
# #@ wall_clock_limit = 24:00:00
# #@ wall_clock_limit = 04:00:00
#@ tasks_per_node = 28
#@ job_type = MPICH
#@ island_count = 1
#@ energy_policy_tag = NONE
#@ job_name = sp
#@ network.MPI = sn_all,not_shared,us
#@ output = $(jobid).out
#@ error = $(jobid).err
#@ queue

export TMPDIR="${SCRATCH}"
export REVERSE_SHELL=1
export LOGIN_HOST=login21ib
export TIME_BUFFER="600"

export OMP_NUM_THREADS=1
export MKL_SERIAL=yes
export I_MPI_PIN_DOMAIN=omp

# set symbolic links to SQLTM and TSS root directory
export SQLTM_BASE="${HOME}/sqltm"
export TSS="${WORK}/tss_hw"
export MYSQL_CNF="${HOME}/.hw.cnf"
#export TSS="${WORK}/tss_sb"
#export MYSQL_CNF="${HOME}/.sb.cnf"
#export TSS="${WORK}/tss_wm"
#export MYSQL_CNF="${HOME}/.wm.cnf"

#bash ${SQLTM_BASE}/lib/llsql.sh <db>.sqlite
bash ${SQLTM_BASE}/lib/llsql.sh <db>
