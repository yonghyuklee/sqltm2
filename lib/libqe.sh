#!/bin/bash --posix
#set -x

source "${SQLTM_BASE}/lib/libsql.sh"

# define input/output columns in SQL schema
inp_scf="input1" # prefix=scf
out_scf="output1"
inp_nscf="input2" # prefix=scf
out_nscf="output2"
inp_pdos="input3"
out_pdos="output3"


run_scf ()
{
    local db="${1}"
    local id="${2}"
    local hostfile="${3}"
    local remaining_time="$(expr ${4} - $(date +%s))"
    local flag
    local workdir
    local pid
    local pid_timeout
    local step="scf"
    local program="pw.x"
    local inputfile="${step}.inp"
    local outputfile="${step}.out"
    local complete_str="JOB DONE."
    local restart_str="Program stopped by user request"

    # if workdir is already set, we assume the task is to be restarted
    workdir="$(sql_get "${db}" "${id}" workdir)"
    if [[ -d "${workdir}" ]]; then
        cd "${workdir}"
        [[ -e "scf.EXIT" ]] && rm "scf.EXIT"
        # check whether job is already complete
        if grep -q "${complete_str}" "${outputfile}"; then
            echo "Task ${id} step ${step} is already complete. Updating output."
            sql_set "${db}" "${id}" "${out_scf}" "${outputfile}"
            sql_set "${db}" "${id}" "status" "${flag_complete}"
            return
        fi
    elif [[ "${workdir}" -eq "NULL" ]]; then
        # create working directory
        mkdir "${id}"
        cd "${id}"
        workdir="$(pwd)"
        sql_set "${db}" "${id}" workdir "${workdir}"
    else
        # this branch is executed if a job is continued on another system not sharing the same workdir
        echo "Task ${id} step ${step}: ${workdir} not found. Set job status to inactive."
        sql_set "${db}" "${id}" "status" "${flag_restart}"
        return
    fi

    # retrieve input files from database
    sql_get "${db}" "${id}" "${inp_scf}" > "${inputfile}"

    # here goes the actual job command (mpirun etc)
    # also check here whether job is restarted or not
    ${MPIEXEC} -machinefile "${hostfile}" ${EXEC} -inp "${inputfile}" > "${outputfile}" &

    # this code ensures the task is finished in time to avoid db corruption
    pid=$!
    sql_set "${db}" "${id}" pid "${pid}"
    sleep "${remaining_time}" && touch scratch/scf.EXIT & pid_timeout=$!
    wait "${pid}"
    pkill -P "${pid_timeout}" 2>/dev/null
    wait "${pid_timeout}" 2>/dev/null

    if grep -q "${complete_str}" "${outputfile}"; then
        flag="${flag_complete}"
        echo "Task ${id} step ${step} complete"
    elif grep -q "${restart_str}" "${outputfile}"; then
        # append outputfile to outputfiles of preceding calculations (if any)
        cat "${outputfile}" >> "${outputfile}.bak"
        flag="${flag_restart}"
        echo "Task ${id} step ${step} incomplete - needs restart"
    else
        flag="${flag_error}"
        echo "Task ${id} step ${step} terminated with error. Check output."
    fi
    # add output file and set status flag in database
    sql_set "${db}" "${id}" "${out_scf}" "${outputfile}"
    sql_set "${db}" "${id}" "status" "${flag}"
    return
}


run_nscf ()
{
    local db="${1}"
    local id="${2}"
    local hostfile="${3}"
    local remaining_time="$(expr ${4} - $(date +%s))"
    local flag
    local workdir
    local pid
    local pid_timeout
    local step="nscf"
    local program="pw.x"
    local inputfile="${step}.inp"
    local outputfile="${step}.out"
    local complete_str="JOB DONE."
    local restart_str="Program stopped by user request"

    workdir="$(sql_get "${db}" "${id}" workdir)"
    [[ -z "${workdir}" ]] && exit
    cd "${workdir}" || exit
    flag=$(check_string "${restart_str}" "${outputfile}")
    if [[ "${flag}" -ne "${flag_complete}" ]]; then
        check_string "${complete_str}" "${outputfile}" > /dev/null && return
    fi
    [[ -e "${inputfile}" ]] || sql_get "${db}" "${id}" "${inp_nscf}" > "${inputfile}"

    ${mpi_exe} -machinefile "${hostfile}" "${exe_dir}/${program}" -inp "${inputfile}" > "${outputfile}" &
    pid=$!
    sql_set "${db}" "${id}" pid "${pid}"
    sleep "${remaining_time}" && touch scratch/scf.EXIT & pid_timeout=$!
    wait "${pid}"
    pkill -P "${pid_timeout}" 2>/dev/null
    wait "${pid_timeout}" 2>/dev/null


    flag=$(check_string "${restart_str}" "${outputfile}")
    if [[ "${flag}" -eq "${flag_complete}" ]]; then
        cat "${outputfile}" >> "${outputfile}.bak"
        sed '/^\s\+restart_mode\s\+=.*/{s/from_scratch/restart/}' -i "${inputfile}"
        flag="${flag_pending}"
    else
        flag=$(check_string "${complete_str}" "${outputfile}")
        if [[ "${flag}" -eq "${flag_complete}" ]]; then
            sql_set "${db}" "${id}" "${out_nscf}" "${outputfile}"
        fi
    fi

    sql_set "${db}" "${id}" "complete_time" "$(date +%s)"
    sql_dealloc_cores "${db}" "${id}"
    sql_set "${db}" "${id}" "status" "${flag}"
    if [[ "${flag}" -ne "${flag_complete}" ]]; then
        echo "Task ${id} step ${step} incomplete"
        exit
    fi
    return
}


run_pdos ()
{
    local db="${1}"
    local id="${2}"
    local hostfile="${3}"
    local remaining_time="$(expr ${4} - $(date +%s))"
    local flag
    local workdir
    local pid
    local pid_timeout
    local step="pdos"
    local program="projwfc.x"
    local inputfile="${step}.inp"
    local outputfile="${step}.out"
    local complete_str="Spilling Parameter"

    workdir="$(sql_get "${db}" "${id}" workdir)"
    [[ -z "${workdir}" ]] && exit
    cd "${workdir}" || exit
    check_string "${complete_str}" "${outputfile}" > /dev/null && return
    [[ -e "${inputfile}" ]] || sql_get "${db}" "${id}" "${inp_pdos}" > "${inputfile}"

    ${mpi_exe} -machinefile "${hostfile}" "${exe_dir}/${program}" -inp "${inputfile}" > "${outputfile}" &
    pid=$!
    sql_set "${db}" "${id}" pid "${pid}"
    sleep "${remaining_time}" && pkill -P "${pid}" & pid_timeout=$!
    wait "${pid}"
    pkill -P "${pid_timeout}" 2>/dev/null
    kill "${pid_timeout}" 2>/dev/null
    wait "${pid_timeout}" 2>/dev/null

    flag=$(check_string "${complete_str}" "${outputfile}")
    if [[ "${flag}" -eq "${flag_complete}" ]]; then
        sql_set "${db}" "${id}" "${out_pdos}" "scf.pdos_tot"
    fi

    sql_set "${db}" "${id}" "complete_time" "$(date +%s)"
    sql_dealloc_cores "${db}" "${id}"
    sql_set "${db}" "${id}" "status" "${flag}"
    if [[ "${flag}" -ne "${flag_complete}" ]]; then
        echo "ERROR in task ${id} step ${step}"
        exit
    fi
    return
}
