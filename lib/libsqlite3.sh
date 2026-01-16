#!/bin/bash --posix

libsql_dir="$(dirname $(readlink -f ${BASH_SOURCE}))"
sqlite_exe="${SQLITE3_EXE:-${libsql_dir}/sqlite3}"
lock="${SQLITE3_LOCK:-${libsql_dir}/lock}"

# status flags
flag_inactive=0
flag_pending=1 # -> idle core
flag_running=2 # -> busy core
flag_complete=3
flag_error=4

# wrap SQL queries due to broken lock mechanism of SQLITE3 on NFS file systems
sql_execute ()
{
    local db_name="${1}"
    local sql="${2}"
    ${lock} "${db_name}.lock"
    echo "${sql}" | ${sqlite_exe} ${db_name}
    rm -f "${db_name}.lock"
    return
}

sql_rm_job ()
{
    local db_name="${1}"
    local jobid="${2}"
    local sql
    sql_rm_hosts "${db_name}" "${jobid}"
    sql="UPDATE tasks SET status=${flag_pending} WHERE jobid=${jobid} AND status=${flag_running};"
    sql_execute "${db_name}" "${sql}"
    return
}

# get internal (integer) jobid from jobid used by resource manager
sql_get_jobid ()
{
    local db_name="${1}"
    local id="${2}"
    local sql
    sql="SELECT id FROM jobs WHERE jobname=\"${id}\";"
    echo "${sql}" | ${sqlite_exe} ${db_name}
    return
}

sql_rm_hosts ()
{
    local db_name="${1}"
    local jobid="${2}"
    local sql
    sql="DELETE FROM hosts WHERE (jobid = ${jobid});"
    sql_execute "${db_name}" "${sql}"
    return
}

sql_get_idle_cores ()
{
    local db_name="${1}"
    local jobid="${2}"
    local sql
    sql+="SELECT COUNT(*) FROM hosts WHERE ("
    sql+="status = ${flag_pending} AND jobid = ${jobid}"
    sql+=') ORDER BY id ASC; '
    echo "${sql}" | ${sqlite_exe} ${db_name}
    return
}

sql_dealloc_cores ()
{
    local db_name="${1}"
    local taskid="${2}"
    local ncores="${3}"
    local sql
    sql+='UPDATE hosts SET '
    sql+="status = ${flag_pending} "
    sql+="WHERE taskid = ${taskid};"
    #echo "${sql}" 
    sql_execute "${db_name}" "${sql}"
    return
}

sql_alloc_cores ()
{
    local db_name="${1}"
    local taskid="${2}"
    local ncores="${3}"
    local sql
    sql="BEGIN TRANSACTION;"
    sql+='UPDATE hosts SET '
    sql+="status = ${flag_running}, taskid = ${taskid} "
    sql+="WHERE id IN ("
    sql+="SELECT id FROM hosts WHERE jobid IN ("
    sql+="SELECT jobid FROM tasks WHERE ("
    sql+="id = ${taskid}"
    sql+=")) AND status = ${flag_pending} ORDER BY id ASC LIMIT ${ncores}); "
    sql+="SELECT name FROM hosts WHERE taskid = ${taskid};"
    sql+='COMMIT;'
    #echo "${sql}" 
    sql_execute "${db_name}" "${sql}"
    return
}


# initial sql table schema to store I/O files
# TODO: add query ncores > min AND ncores < max AND status = pending ORDER BY priority LIMIT 1
# for load balancing
sql_init ()
{
    local db_name="${1}"
    shift
    local columns="${@}"
    local sql
    local i
    sql="BEGIN TRANSACTION;"
    # task table
    sql+="CREATE TABLE IF NOT EXISTS "
    sql+="tasks"
    sql+="(id INTEGER PRIMARY KEY AUTOINCREMENT"
    sql+=",name TEXT"
    sql+=",description TEXT"
    sql+=",status INTEGER DEFAULT 0"
    sql+=",priority INTEGER DEFAULT 100"
    sql+=",start_time INTEGER"
    sql+=",complete_time INTEGER"
    sql+=",jobid INTEGER DEFAULT 0"
    sql+=",task_script TEXT"
    sql+=",ncores INTEGER DEFAULT 28"
    sql+=",min_cores INTEGER DEFAULT 28"
    sql+=",workdir TEXT"
    sql+=",pid INTEGER"
    for i in {1..10}; do
        sql+=",input${i} BLOB,output${i} BLOB"
    done
    for column in ${columns}; do
        sql+=",${column} BLOB"
    done
    sql+=",FOREIGN KEY(jobid) REFERENCES jobs(id)"
    sql+=");"
    # jobs table
    sql+="CREATE TABLE IF NOT EXISTS "
    sql+="jobs"
    sql+="(id INTEGER PRIMARY KEY AUTOINCREMENT"
    sql+=",jobname TEXT"
    sql+=",dispatch_time INTEGER"
    sql+=",time_limit INTEGER"
    sql+=",tot_cores INTEGER"
    sql+=",scratch TEXT"
    sql+=");"
    # hosts table
    sql+="CREATE TABLE IF NOT EXISTS "
    sql+="hosts"
    sql+="(id INTEGER PRIMARY KEY AUTOINCREMENT"
    sql+=",name TEXT"
    sql+=",jobid INTEGER DEFAULT 0"
    sql+=",taskid INTEGER"
    sql+=",status INTEGER"
    sql+=",FOREIGN KEY(jobid) REFERENCES jobs(id)"
    sql+=",FOREIGN KEY(taskid) REFERENCES tasks(id)"
    sql+=");"
    sql+="COMMIT;"
    #echo "${sql}"
    sql_execute "${db_name}" "${sql}"
    return
}

# append new task (row) and return id
sql_new ()
{
    local db_name="${1}"
    local sql
    # add empty row and get id of inserted row
    sql='BEGIN TRANSACTION; '
    sql+='INSERT INTO tasks DEFAULT VALUES; '
    sql+='SELECT id FROM tasks ORDER BY id DESC LIMIT 1;'
    sql+='COMMIT; '
    #echo "${sql}"
    sql_execute "${db_name}" "${sql}"
    return 
}

sql_new_job ()
{
    local db_name="${1}"
    local hostfile="${2}"
    local -a hosts
    local sql
    local jobid
    #readarray -t hosts < "${hostfile}"
    hosts=( $(cat "${hostfile}") )
    # add empty row and get id of inserted row
    sql='BEGIN TRANSACTION; '
    sql+='INSERT INTO jobs DEFAULT VALUES; '
    sql+='SELECT id FROM jobs ORDER BY id DESC LIMIT 1; '
    sql+='COMMIT;'
    #echo "${sql}"
    # add allocated processors to hosts table
    jobid="$(echo "${sql}" | ${sqlite_exe} ${db_name})"
    sql='INSERT INTO hosts (name, jobid, status) VALUES '
    sql+="(""'"${hosts[0]}"'"", ${jobid}, ${flag_pending})"
    for (( i=1; i<${#hosts[@]}; i++ )); do
        sql+=",(""'"${hosts[${i}]}"'"", ${jobid}, ${flag_pending})"
    done
    sql+='; '
    #echo "${sql}"
    #echo "${sql}" | "${sqlite_exe}" "${db_name}"
    sql_execute "${db_name}" "${sql}"
    echo "${jobid}"
    return 
}

# return id of next pending job (status flag is "pending")
# workaround if sqlite3 was not compiled with SQLITE ENABLE UPDATE DELETE LIMIT
sql_next ()
{
    local db_name="${1}"
    local jobid="${2}"
    local avail_cores="${3:-1000000}"
    local sql
    local id
    sql='BEGIN TRANSACTION; '
    sql+="SELECT id FROM tasks WHERE ("
    sql+="status = ${flag_pending} "
    sql+="AND ncores <= ${avail_cores}"
    sql+=') ORDER BY priority DESC LIMIT 1; '
    sql+='UPDATE tasks SET '
    sql+="status = ${flag_running}, jobid = ${jobid} "
    sql+="WHERE id IN (SELECT id FROM tasks WHERE ("
    sql+="status = ${flag_pending} "
    sql+="AND ncores <= ${avail_cores}"
    sql+=') ORDER BY priority DESC LIMIT 1); '
    # alternative if UPDATE supports ORDER BY
    #sql+='WHERE status = '
    #sql+='ORDER BY priority DESC LIMIT 1; '
    sql+='COMMIT;'
    #echo "${sql}"
    #id=$(echo "${sql}" | ${sqlite_exe} ${db_name})
    id=$(sql_execute "${db_name}" "${sql}")
    if [[ -z "${id// }" ]]; then
        sql='BEGIN TRANSACTION; '
        sql+="SELECT id FROM tasks WHERE ("
        sql+="status = ${flag_pending} "
        sql+="AND min_cores <= ${avail_cores}"
        sql+=') ORDER BY priority DESC LIMIT 1; '
        sql+='UPDATE tasks SET '
        sql+="status = ${flag_running}, jobid = ${jobid} "
        sql+="WHERE id IN (SELECT id FROM tasks WHERE ("
        sql+="status = ${flag_pending} "
        sql+="AND min_cores <= ${avail_cores}"
        sql+=') ORDER BY priority DESC LIMIT 1); '
        sql+='COMMIT;'
        #id=$(echo "${sql}" | ${sqlite_exe} ${db_name})
        id=$(sql_execute "${db_name}" "${sql}")
    fi
    echo "${id}"
    return
}

# get entry from database (to stdout)
sql_get ()
{
    local db_name="${1}"
    local id="${2}"
    shift
    shift
    local columns="${@}"
    local sql

    sql="SELECT "
    sql+="("
    for column in ${columns}; do
        sql+="${column}"
    done
    sql+=")"
    sql+=" FROM tasks WHERE id=\"${id}\";"
    #echo "${sql}" > /dev/stderr
    echo "${sql}" | ${sqlite_exe} ${db_name}
    return
}

# get all tasks assigned to one job with a given status
sql_get_tasks ()
{
    local db_name="${1}"
    local jobid="${2}"
    local status="${3}"
    local sql

    sql="SELECT id FROM tasks WHERE "
    sql+="(jobid = ${jobid} AND status = ${status});"
    #echo "${sql}"
    echo "${sql}" | ${sqlite_exe} ${db_name}
    return
}

# get entry from jobs table (to stdout)
sql_get_jobs ()
{
    local db_name="${1}"
    local id="${2}"
    shift
    shift
    local columns="${@}"
    local sql

    sql="SELECT "
    sql+="("
    for column in ${columns}; do
        sql+="${column}"
    done
    sql+=")"
    sql+=" FROM jobs WHERE id=\"${id}\";"
    #echo "${sql}"
    echo "${sql}" | ${sqlite_exe} ${db_name}
    return
}

# set field (either from argument or - if a file with this name exists - file contents)
sql_set ()
{
    local db_name="${1}"
    local id="${2}"
    local column="${3}"
    local value="${4}"
    local link="${5:-1}"
    local sql
    #sql="INSERT OR REPLACE INTO "
    sql="UPDATE "
    sql+="tasks SET "
    sql+="${column}"
    sql+=" = "
    if [[ -f "${value}" && ${link} -eq 1 ]]; then
        sql+="readfile(""'"${value}"'"")"
    else
        sql+="'"${value}"'"
    fi
    sql+=" WHERE id = ${id};"
    #echo ${sql}
    #echo "${sql}" | ${sqlite_exe} ${db_name}
    sql_execute "${db_name}" "${sql}"
    return
}

# increment/decrement integer value (difference escaping required)
sql_inc ()
{
    local db_name="${1}"
    local id="${2}"
    local column="${3}"
    local value="${4}"
    local table="${5:-"jobs"}"
    local sql
    sql="UPDATE ${table} SET ${column} = ${column}${value} "
    sql+="WHERE id = ${id};"
    #echo ${sql}
    #echo "${sql}" | ${sqlite_exe} ${db_name}
    sql_execute "${db_name}" "${sql}"
    return
}


# set field in jobs table
sql_set_jobs ()
{
    local db_name="${1}"
    local id="${2}"
    local column="${3}"
    local value="${4}"
    local link="${5:-1}"
    local sql
    #sql="INSERT OR REPLACE INTO "
    sql="UPDATE "
    sql+="jobs SET "
    sql+="${column}"
    sql+=" = "
    if [[ -f "${value}" && ${link} -eq 1 ]]; then
        sql+="readfile(""'"${value}"'"")"
    else
        sql+="'"${value}"'"
    fi
    sql+=" WHERE id = ${id};"
    #echo ${sql}
    #echo "${sql}" | ${sqlite_exe} ${db_name}
    sql_execute "${db_name}" "${sql}"
    return
}

# set entire column to some value (maybe a file)
sql_set_all ()
{
    local db_name="${1}"
    local column="${2}"
    local value="${3}"
    local sql
    sql="UPDATE tasks SET "
    sql+="${column} = "
    if [[ -f "${value}" ]]; then
        sql+="readfile(""'"${value}"'"")"
    else
        sql+="${value}"
    fi
    sql+=";"
    #echo ${sql}
    #echo "${sql}" | ${sqlite_exe} ${db_name}
    sql_execute "${db_name}" "${sql}"
    return
}

# check if file 2 contains string 1
# return 1 if string found, 0 otherwise
check_string ()
{
    grep "${1}" "${2}" &> /dev/null
    OK=$?
    if [[ "${OK}" -eq "0" ]]; then
        echo "${flag_complete}"
    else
        echo "${flag_error}"
    fi
    return ${OK}
}


if [[ ${1} == "-f" ]]; then
    echo "ARGUMENTS to libbatch.sh: $*" >&2
    shift
    $*
fi

