#!/bin/bash --posix
#set -x

if [[ "$#" == "0" ]]; then
    echo "usage: ${0} <db name>"
    exit
fi

# make sure script is run in SLURM environment
if [[ -z "${SLURM_JOB_ID}" ]]; then
    echo "ERROR: $0 not running in SLURM environment."
    exit
fi

# export environment for other scripts (if not already done)
sql_script="$(readlink -f ${0})"
export SQLTM_BASE="${SQLTM_BASE:-${sql_script%/*/*}}"

db="${1:-$USER}"
time_buffer="${TIME_BUFFER:-600}"
source "${SQLTM_BASE}/lib/libsql.sh"
sql_check || exit
#scratch="${TMPDIR:-/tmp}"

# *** system specific settings ***
if [[ -z "${SLURM_CLUSTER_NAME}" ]]; then
    jobname="${SLURM_JOB_ID}" # the job id used in queries
    jobinfo="$(squeue -j ${SLURM_JOB_ID} --format="%.20S %.12l" | tail -n 1)"
else
    jobname="${SLURM_CLUSTER_NAME}-${SLURM_JOB_ID}" # the job id used in queries
    jobinfo="$(squeue --clusters=${SLURM_CLUSTER_NAME} -j ${SLURM_JOB_ID} --format="%.20S %.12l" | tail -n 1)"
fi

# *** setup reverse shell ***
reverse_shell="${RRS:-${SQLTM_BASE}/sbin/rrs}"
cert="${CERT:-${SQLTM_BASE}/etc/rrs.pem}"
login_host="${LOGIN_HOST:-${SLURM_SUBMIT_HOST}}"
if [[ -e "${reverse_shell}" && -n "${login_host}" ]]; then 
    # IANA unregistered port range: 49152 - 65535 (16384 available ports)
    port=$(expr $$ % 16384 + 49152)
    rs="$(pwd)/rs_${jobname}.sh"
    ${reverse_shell} -D -s -q -R 30 -t 5 -P ${cert} ${login_host} ${port}
    echo -e "${reverse_shell} -ls --pem ${cert} -p${port}" > "${rs}"
fi
scratch="$(mktemp -d)"
cd "${scratch}"

hostfile="hosts.dat"
srun $(which hostname) | sort > "${hostfile}"
dispatch_time="$(echo -e ${jobinfo} | awk -F' ' '{ print $1 }' | sed 's/T/ /')"
dispatch_time=$(date -d "${dispatch_time}" "+%s")
time_limit=$(echo ${jobinfo} | awk -F' ' '{ print $2 }' | awk -F':' '{ sub("-",":"); if ($4 == "") {$4=$3; $3=$2; $2=$1; $1=0}; print ($1*86400) + ($2 * 3600) + ($3 * 60) + $4 }')
tot_cores=$(wc -l ${hostfile} | cut -f 1 -d " ")
idle_cores="${tot_cores}"
# *** end system specific settings ***


run_task ()
{
    task_script="$(sql_get ${db} ${taskid} task_script)"
    sql_set "${db}" "${taskid}" "start_time" "$(date +%s)"
    bash "${SQLTM_BASE}/bin/${task_script}" "${db}" "${taskid}" "${task_hostfile}" "${termination_time}"
    sql_set "${db}" "${taskid}" "complete_time" "$(date +%s)"
    sql_set "${db}" "${taskid}" pid -1
    sql_dealloc_cores "${db}" "${taskid}"
    return
}

# create row with job parameters in job table
jobid=$(sql_new_job "${db}" "${hostfile}")
sql_set_jobs "${db}" "${jobid}" jobname "${jobname}"
sql_set_jobs "${db}" "${jobid}" time_limit "${time_limit}"
sql_set_jobs "${db}" "${jobid}" dispatch_time "${dispatch_time}"
sql_set_jobs "${db}" "${jobid}" scratch "${scratch}"

# in principle this is an optimization task:
# distribute ALL cores among task_cores with the constraints:
# * as little as possible deviation from ncores
declare -i taskid=0
declare -i task_cores=0
termination_time="$(expr ${dispatch_time} + ${time_limit} - ${time_buffer})"
while [[ "$(expr ${termination_time} - $(date +%s))" -gt "0" ]]; do
    # first check if there are any cores available
    idle_cores=$(sql_get_idle_cores ${db} ${jobid})
    #echo "Idle cores: ${idle_cores}" 
    if [[ ${idle_cores} -eq 0 ]]; then
        sleep 30
        continue
    fi
    # find next pending job 
    # sql_next: sets jobid and run flag (blocked for other processes)
    taskid=$(sql_next ${db} ${jobid} ${idle_cores})
    #echo "Next taskid: ${taskid}" 
    if [[ -z "${taskid}" || "${taskid}" -eq "0" ]]; then
        if [[ "${idle_cores}" -eq "${tot_cores}" ]]; then
            echo "No suitable jobs left. Exiting loop with ${idle_cores} idle cores."
            echo "There may be unfinished jobs that need to be restarted."
            break
        fi
        sleep 30
    else
        # if optimal no of cores is not available, reduce MPI tasks
        # this code can not be in run_task due to concurrency issues 
        task_cores=$(sql_get ${db} ${taskid} ncores)
        if [[ "${task_cores}" -gt "${idle_cores}" ]]; then
            task_cores="${idle_cores}"
        fi
        task_hostfile="$(pwd)/${jobid}.${taskid}"
        #echo "Allocating ${task_cores} cores for ${taskid}"
        sql_alloc_cores "${db}" "${taskid}" "${task_cores}" > "${task_hostfile}"
        run_task &
    fi
done

echo "Waiting for remaining tasks to finish."
wait
echo "All tasks complete."

# *** clean up ***
sql_rm_hosts "${db}" "${jobid}"
if [[ -e "${rs}" ]]; then
    rm "${rs}"
    killall rrs
fi
