# Portable Batch System (PBS), e. g. Torque, submission script
# if using an sqlite3 database, the submission directory must contain the database file

#PBS -S /bin/bash
#PBS -N sp
#PBS -j oe
#PBS -l walltime=24:00:00,nodes=2:Opteron6272:ppn=16
#PBS -l mem=1gb
#PBS -V

# environment variable setup
LANG=C                          # some programs just don't like
LC_ALL=C                        # internationalized environments!
export LANG LC_ALL

export TMPDIR="/scratch/${USER}"
export REVERSE_SHELL=1
export LOGIN_HOST=tick
export TIME_BUFFER="600"

export OMP_NUM_THREADS=1
export MKL_SERIAL=yes
export I_MPI_PIN_DOMAIN=omp

# submission directory can be accessed via ${PBS_O_WORKDIR}
#cd ${PBS_O_WORKDIR}
mkdir -p "${TMPDIR}"

# set symbolic links to SQLTM and TSS root directory
export TSS="${HOME}/tss"
export SQLTM_BASE="${HOME}/sqltm"
#export MYSQL_CNF="${HOME}/.tum.cnf"

#bash ${SQLTM_BASE}/lib/llsql.sh <db>.sqlite
bash ${SQLTM_BASE}/lib/llsql.sh <db>
