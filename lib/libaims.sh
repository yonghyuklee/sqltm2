#!/bin/bash --posix
#set -x
# This file contains some standard routines for FHI-AIMS calculations
# The purpose of separating these into a library of bash functions is to simplify 
# their use with different FHI-AIMS version, e. g.
# ...
# MPIEXEC=<some mpiexec>
# EXEC=<some fhi-aims exec>
# run_scf $*
# ...
# of course, these may be used as templates for more specific scripts, for example 
# to implement automated restarts for geometry optimizations

source "${SQLTM_BASE}/lib/libsql.sh"

# define input/output columns in SQL schema
inp_scf="input1"
out_scf="output1"
inp_relax="input1"
out_relax="output1"
inp_geo="input2"
out_geo="output2"

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
    local inputfile="control.in"
    local outputfile="${step}.out"
    local complete_str="${complete_str:-"Self-consistency cycle converged."}"
    local restart_str="${restart_str:-"scf_solver: SCF cycle not converged."}"

    # preliminary checks: make sure "workdir" exists and job is not yet complete
    workdir="$(sql_get "${db}" "${id}" workdir)"
    if [[ -d "${workdir}" ]]; then
        cd "${workdir}"
        [[ -e abort_scf ]] && rm abort_scf
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
    sql_get "${db}" "${id}" "${inp_geo}" > "geometry.in"

    # here goes the actual job command (mpirun etc)
    # also check here whether job is restarted or not
    ${MPIEXEC} -machinefile "${hostfile}" "${EXEC}" "${inputfile}" > "${outputfile}" &

    # this code ensures the task is finished in time to avoid db corruption
    pid=$!
    sql_set "${db}" "${id}" pid "${pid}"
    #sleep "${remaining_time}" && pkill -P "${pid}" & pid_timeout=$!
    sleep "${remaining_time}" && touch abort_scf & pid_timeout=$!
    wait "${pid}"
    pkill -P "${pid_timeout}" 2>/dev/null
    wait "${pid_timeout}" 2>/dev/null

    # check status of job (complete, restart, error etc.)
    # and push output files to database if task is complete
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


run_relax ()
{
    local db="${1}"
    local id="${2}"
    local hostfile="${3}"
    local remaining_time="$(expr ${4} - $(date +%s))"
    local flag
    local workdir
    local pid
    local pid_timeout
    local step="relax"
    local inputfile="control.in" # ${inp_relax}
    local outputfile="${step}.out" # ${out_relax}
    local complete_str="Present geometry is converged."
    local restart_str="Present geometry is not yet converged."

    # preliminary checks: make sure "workdir" exists and job is not yet complete
    workdir="$(sql_get "${db}" "${id}" workdir)"
    if [[ -d "${workdir}" ]]; then
        cd "${workdir}"
        [[ -e abort_scf ]] && rm abort_scf
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
        # this branch is executed is a job is continued on another system not sharing the same workdir
        echo "Task ${id} step ${step}: ${workdir} not found. Set job status to restart."
        sql_set "${db}" "${id}" "status" "${flag_restart}"
        return
    fi

    # retrieve input files from database
    sql_get "${db}" "${id}" "${inp_relax}" > "${inputfile}"
    sql_get "${db}" "${id}" "${inp_geo}" > "geometry.in"

    # here goes the actual job command (mpirun etc)
    # also check here whether job is restarted or not
    ${MPIEXEC} -machinefile "${hostfile}" "${EXEC}" "${inputfile}" > "${outputfile}" &

    # this code ensured the task is finished in time to avoid db corruption
    pid=$!
    sleep "${remaining_time}" && pkill -P "${pid}" & pid_timeout=$!
    #sleep "${remaining_time}" && pkill -P "${pid}" && echo "${restart_str}" >> "${outputfile}" & pid_timeout=$!
    # clean exit does not work since iteration time may be very long
    #sleep "${remaining_time}" && touch abort_opt & pid_timeout=$!
    sql_set "${db}" "${id}" pid "${pid}"
    wait "${pid}"
    pkill -P "${pid_timeout}" 2>/dev/null
    wait "${pid_timeout}" 2>/dev/null

    # check status of job (complete, restart, error etc.)
    # and push output files to database if task is complete
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
    sql_set "${db}" "${id}" "${out_relax}" "${outputfile}"
    sql_set "${db}" "${id}" "status" "${flag}"
    return
}
