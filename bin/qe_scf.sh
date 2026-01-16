#!/bin/bash --posix
#set -x

if [[ ! "$#" == "4" ]]; then
    echo "${0} requires 4 arguments"
    exit
fi

. ${TSS}/bin/qe.sh
# MPIEXEC set by TSS script
EXEC="${TSS}/bin/pw.x"

# system specific settings if necessary
if [[ "${LRZ_SYSTEM_SEGMENT}" == "Medium_Node" ]]; then
    :
elif [[ "${LRZ_SYSTEM_SEGMENT}" == "CMUC2" || "${LRZ_SYSTEM_SEGMENT}" == "MPP_IB" ]]; then
    :
elif [[ "${USER}" == "hmu231" ]]; then # JURECA
    export SLURM_HOSTFILE="${3}"
elif [[ "$(hostname -d)" == "theo.chemie.tu-muenchen.de" ]]; then
    :
fi

source "${SQLTM_BASE}/lib/libqe.sh"

# for restart set input_dir
#input_dir=""
#[[ -d "${input_dir}" ]] && ln -s "${input_dir}" input

run_scf $*
#run_relax $*
