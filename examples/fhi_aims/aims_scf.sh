#!/bin/bash --posix

input_dir=""
libdir="${HOME}/src/sqltm_dev/lib"
source "${libdir}/libaims.sh"

if [[ "${LRZ_SYSTEM_SEGMENT}" == "Medium_Node" ]]; then
    module purge
    module load intel
    mpi_exe=/lrz/sys/intel/impi/5.1.3.181/intel64/bin/mpirun
    exe_dir="${HOME}/stow/aims/bin"
    program="aims.160322.scalapack.mpi.x"
else
    mpi_exe="/usr/local/stow/Intel_MPI/share/impi/5.1.1.109/bin64/mpiexec.hydra"
    exe_dir="${HOME}/stow/aims/bin"
    program="aims.160328_3.scalapack.mpi.x"
fi

if [[ "$#" == "4" ]]; then 
    run_scf $*
    #run_relax $*
else
    echo "${0} requires 4 arguments"
fi
