#!/bin/bash --posix

# make sure script is run in LoadLeveler environment
if [[ -z "${LOADLBATCH}" ]]; then
    echo "ERROR: only LoadLeveler environment supported."
    exit
fi

db_name="${1}"
shift
jobids="${@}"

sql_script="$(readlink -f ${0})"
sql_dir="$(dirname ${sql_script})"
source "${sql_dir}/libsql.sh"
re='^[0-9]+$'

printf "Purging job "
for id in ${jobids}; do
    # check whether jobids are LL ids or SQL database ids (integer)
    if ! [[ "${id}" =~ $re ]] ; then
        jobname="${id}"
        i=$(sql_get_jobid "${db_name}" "${jobname}")
        echo "${jobname} -> ${i}"
    else
        i=${id}
        jobname=$(sql_get_jobs "${db_name}" "${id}" jobname)
        echo "${i} -> ${jobname}"
    fi
    s=$(llq -l ${jobname} | awk '/Status:/{print $2}') # Running/Idle
    if [[ "${s}" == "Running" ]]; then
	echo "Job ${jobname} is still running. Continue?"
	read
        llcancel "${jobname}"
        echo "${jobname} canceled."
    fi
    sql_rm_job "${db_name}" "${i}"
    echo "Job ${i} removed from database ${db_name}."
done
echo "Done."
