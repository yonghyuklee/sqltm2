#!/bin/bash --posix
#set -x
if [[ ! "$#" == "4" ]]; then
    echo "${0} requires 4 arguments"
    exit
fi

. ${TSS}/bin/cp2k.sh
# MPIEXEC set by TSS script
EXEC="${TSS}/bin/cp2k.psmp"

source "${SQLTM_BASE}/lib/libsql.sh"

db="${1}"
id="${2}"
hostfile="${3}"
remaining_time="$(expr ${4} - $(date +%s))"
step="relax"
inputfile="${step}.inp"
outputfile="${step}.out"
complete_str="${complete_str:-"GEOMETRY OPTIMIZATION COMPLETED"}"

# preliminary checks: make sure "workdir" exists and job is not yet complete
workdir="$(sql_get "${db}" "${id}" workdir)"
if [[ -d "${workdir}" ]]; then
    cd "${workdir}"
    [[ -e EXIT ]] && rm EXIT
elif [[ "${workdir}" -eq "NULL" ]]; then
    # create working directory
    mkdir "${id}"
    cd "${id}"
    workdir="$(pwd)"
    sql_set "${db}" "${id}" workdir "${workdir}"
else
    # this branch is executed is a job is continued on another system not sharing the same workdir
    echo "Task ${id} step ${step}: ${workdir} not found. Set job status to inactive."
    sql_set "${db}" "${id}" "status" "${flag_restart}"
    return
fi

# retrieve input files from database
sql_get "${db}" "${id}" input1 > "${inputfile}"
sql_get "${db}" "${id}" input2 > "restart"

# check whether task is complete
if grep -q "${complete_str}" "${outputfile}"; then
    echo "Task ${id} step ${step} is already complete. Updating output."
    sql_set "${db}" "${id}" output1 "${outputfile}"
    sql_set "${db}" "${id}" input2 "restart"
    sql_set "${db}" "${id}" "status" "${flag_complete}"
    exit
fi

# here goes the actual job command (mpirun etc)
# also check here whether job is restarted or not
${MPIEXEC} -machinefile "${hostfile}" "${EXEC}" "${inputfile}" > "${outputfile}" &

# this code ensures the task is finished in time to avoid db corruption
pid=$!
sql_set "${db}" "${id}" pid "${pid}"
#sleep "${remaining_time}" && pkill -P "${pid}" & pid_timeout=$!
sleep "${remaining_time}" && touch EXIT & pid_timeout=$!
wait "${pid}"
pkill -P "${pid_timeout}" 2>/dev/null
wait "${pid_timeout}" 2>/dev/null

# check status of job (complete, otherwise assume restart)
# and push output files to database if task is complete
if grep -q "${complete_str}" "${outputfile}"; then
    flag="${flag_complete}"
    echo "Task ${id} step ${step} complete"
else
    # append outputfile to outputfiles of preceding calculations (if any)
    cat "${outputfile}" >> "${outputfile}.bak"
    flag="${flag_restart}"
    echo "Task ${id} step ${step} incomplete - needs restart"
fi

# add output file and set status flag in database
sql_set "${db}" "${id}" input2 "restart"
sql_set "${db}" "${id}" output1 "${outputfile}"
sql_set "${db}" "${id}" "status" "${flag}"
