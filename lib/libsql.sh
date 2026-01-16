#!/bin/bash --posix
#set -x

sqltm_sbin="$(dirname $(readlink -f ${BASH_SOURCE}))"
sqltm_sbin="$(readlink -f ${sqltm_sbin}/../sbin)"
mysql_exe="${sqltm_sbin}/mysql"
mysql_cnf="${MYSQL_CNF:-${HOME}/.my.cnf}"

# status flags
flag_inactive=0
: ${flag_pending:=1} # -> idle core
flag_running=2 # -> busy core
flag_complete=3
flag_error=4
flag_restart=5

sql_execute ()
{
    local db_name="${1}"
    local sql="${2}"
    ${mysql_exe} --defaults-file="${mysql_cnf}" --skip-column-names --silent --raw --database="${db_name}" -e "${sql}"
    return
}

sql_check ()
{
    echo "Checking SQL DB connection"
    if ${sqltm_sbin}/mysqladmin \
        --defaults-file="${mysql_cnf}" \
        --connect_timeout=5 ping > /dev/null 2>&1; then
        echo "Connection alive"
        return 0
    else
        echo "No connection to database. Exiting."
        return 1
    fi
}

sql_add ()
{
    if [[ "$#" < "4" ]]; then
        echo "Usage: ${0} <DATABASE> <SELECTOR> <COLUMN> <FILENAME>"
        echo "You may wish to use extendend globbing: shopt -s extglob"
        return
    fi
    local db_name="${1}"
    local selector="${2}"
    local column="${3}"
    local fn="${4}"
    local file
    local id
    local sql="SELECT id,workdir FROM tasks WHERE ${selector};"
    # loop over rows
    sql_execute "${db_name}" "${sql}" | while IFS='\n' read row; do
        r=(${row})
        file="${r[1]}/${fn}"
        id="${r[0]}"
        if [[ ! -f "${file}" ]]; then
            echo "File ${file} does not exist. Skipping task ${id}."
        else
            sql_set "${db_name}" "${id}" "${column}" "${r[1]}/${fn}"
        fi
    done
    return
}


sql_archive ()
{
    if [[ "$#" < "4" ]]; then
        echo "Usage: ${0} <DATABASE> <SELECTOR> <ARCHIVE> <FILENAMES>"
        echo "You may wish to use extendend globbing: shopt -s extglob"
        return
    fi
    local db_name="${1}"
    shift
    local selector="${1}"
    shift
    local archive="$(pwd)/${1}"
    shift
    local fsel="${*}"
    local files
    local r
    local row
    local trf
    local prefix
    local sql="SELECT id,name,workdir FROM tasks WHERE ${selector};"
    # loop over rows
    sql_execute "${db_name}" "${sql}" | while IFS='\n' read row; do
        r=(${row})
        if [[ ! -d "${r[2]}" ]]; then
            echo "workdir ${r[2]} does not exist. Skipping task ${r[0]}."
        else
            prefix="${r[0]}_${r[1]}"
            trf="s,^,${prefix}/,S"
            cd "${r[2]}"
            files=( $(ls ${fsel} 2>/dev/null) )
            # add/substitute files in archive
            if [[ -f ${archive} ]]; then
                tar --delete -f "${archive}" "${files[@]/#/${prefix}/}" 2> /dev/null
                tar --transform "${trf}" -uf "${archive}" "${files[@]}"
            else
                tar --transform "${trf}" -cf "${archive}" "${files[@]}"
            fi
        fi
    done
    return
}


sql_rm_jobs ()
{
    if [[ "$#" < "2" ]]; then
        echo "Usage: ${0} <DATABASE> expired"
        echo "or     ${0} <DATABASE> <SELECTOR FOR JOBS TABLE)>"
        echo "or     ${0} <DATABASE> <JOBID 1> [<JOBID 2> .. <JOBID N>]"
        echo "Remove job from database including associated hosts"
        echo "Tasks with status \"running\" will be set to \"inactive\""
        return
    fi
    local db_name="${1}"
    shift
    local arg="${@}"
    local sql
    # if arg begins with integer assume jobid
    # SQL column names should not begin with a number
    if [[ ${arg} == "expired" ]]; then
        sql="SELECT id FROM jobs WHERE dispatch_time + time_limit + 600 < UNIX_TIMESTAMP();"
        echo $sql
        jobids="$(sql_execute "${db_name}" "${sql}")"
    elif [[ ${arg} =~ ^[0-9]+ ]]; then
        jobids="${arg}"
    else
        sql="SELECT id FROM jobs WHERE ${arg};"
        jobids="$(sql_execute "${db_name}" "${sql}")"
    fi
    echo "jobids = ${jobids}"
    sql="SET FOREIGN_KEY_CHECKS=0; "
    for jobid in ${jobids}; do
        sql+="DELETE FROM hosts WHERE jobid = ${jobid};"
        sql+="UPDATE tasks SET "
        sql+="status = ${flag_inactive} "
        sql+="WHERE jobid = ${jobid} AND status = ${flag_running}; "
        sql+="UPDATE tasks SET jobid = 0, pid = -1 "
        sql+="WHERE jobid = ${jobid}; "
        sql+="DELETE FROM jobs WHERE id = ${jobid}; "
    done
    sql+="SET FOREIGN_KEY_CHECKS=1; COMMIT;"
    #echo $sql
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
    sql_execute "${db_name}" "${sql}"
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
    sql_execute "${db_name}" "${sql}"
    #echo "${sql}" | ${sqlite_exe} ${db_name}
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
    sql+="BEGIN; UPDATE hosts "
    sql+="INNER JOIN tasks ON "
    sql+="tasks.jobid = hosts.jobid "
    sql+="AND tasks.id = ${taskid} "
    sql+="AND hosts.status = ${flag_pending} "
    sql+="SET hosts.status = ${flag_running}, hosts.taskid = ${taskid} "
    sql+="ORDER BY hosts.id ASC LIMIT ${ncores};"
    sql+="COMMIT;"
    sql_execute "${db_name}" "${sql}"
    sql="SELECT hosts.name FROM hosts "
    sql+="INNER JOIN tasks ON "
    sql+="tasks.jobid = hosts.jobid "
    sql+="AND tasks.id = hosts.taskid "
    sql+="WHERE hosts.taskid = ${taskid}; "
    #sql="SELECT name FROM hosts WHERE taskid = ${taskid};"
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
    sql=""
    for column in ${columns}; do
        sql+="ALTER TABLE tasks ADD COLUMN IF NOT EXISTS ${column} TEXT;"
    done
    sql_execute "${db_name}" "${sql}"
    return
}

# append new task (row) and return id
sql_new ()
{
    local db_name="${1}"
    local sql
    # add empty row and get id of inserted row
    # switch of foreign key checks since jobid does not exist 
    # The ID used in LAST_INSERT_ID() is generated on a per-connection basis 
    # and does not refer to a specific table.
    sql="BEGIN; SET FOREIGN_KEY_CHECKS=0; "
    sql+="INSERT INTO tasks (id) VALUE (DEFAULT); "
    sql+="SELECT LAST_INSERT_ID(); "
    sql+="SET FOREIGN_KEY_CHECKS=1; COMMIT;"
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
    sql="BEGIN; "
    sql+="INSERT INTO jobs () VALUES (); "
    sql+="SELECT LAST_INSERT_ID(); "
    sql+="COMMIT; "
    #echo "${sql}"
    # add allocated processors to hosts table
    jobid="$(sql_execute "${db_name}" "${sql}")"
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

    sql+="BEGIN; SET @id = "
    sql+="(SELECT id FROM tasks WHERE "
    sql+="status = ${flag_pending} "
    sql+="AND ncores <= ${avail_cores} "
    sql+="ORDER BY priority DESC, id ASC LIMIT 1 FOR UPDATE); "
    sql+="UPDATE tasks "
    sql+="SET status = ${flag_running}, jobid = ${jobid} "
    sql+="WHERE id = @id; "
    sql+="SELECT @id; COMMIT;"
    id=$(sql_execute "${db_name}" "${sql}")
    if [[ -z "${id}" || "${id}" -eq "0" ]]; then
        sql="BEGIN; SET @id = "
        sql+="(SELECT id FROM tasks WHERE "
        sql+="status = ${flag_pending} "
        sql+="AND min_cores <= ${avail_cores} "
        sql+="ORDER BY priority DESC, id ASC LIMIT 1 FOR UPDATE); "
        sql+="UPDATE tasks "
        sql+="SET status = ${flag_running}, jobid = ${jobid} "
        sql+="WHERE id = @id; "
        sql+="SELECT @id; COMMIT;"
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
    sql_execute "${db_name}" "${sql}"
    #echo "${sql}" | ${sqlite_exe} ${db_name}
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
    sql_execute "${db_name}" "${sql}"
    #echo "${sql}" | ${sqlite_exe} ${db_name}
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
    sql_execute "${db_name}" "${sql}"
    #echo "${sql}" | ${sqlite_exe} ${db_name}
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
    if [[ -f "${value}" && ${link} -eq 1 ]]; then
        local fn="$(readlink -f ${value})"
        sql="LOAD DATA LOCAL INFILE "
        sql+="'""${fn}""'"
        sql+=" INTO TABLE tasks "
        sql+="CHARACTER SET utf8 "
        sql+="FIELDS TERMINATED BY '\Z' "
        sql+="ESCAPED BY '' "
        sql+="LINES TERMINATED BY '' "
        sql+="(@v); "
    else
        sql="SET @v = ""'""${value}""'""; "
    fi
    sql+="UPDATE tasks SET ${column} = @v WHERE id = ${id};"
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
        sql+="LOAD_FILE(""'"${value}"'"")"
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
    local selector="${2}"
    local column="${3}"
    local value="${4}"
    local link="${5:-1}"
    local sql
    if [[ -f "${value}" && ${link} -eq 1 ]]; then
        local fn="$(readlink -f ${value})"
        sql="LOAD DATA LOCAL INFILE "
        sql+="'""${fn}""'"
        sql+=" INTO TABLE tasks "
        sql+="CHARACTER SET utf8 "
        sql+="FIELDS TERMINATED BY '\Z' "
        sql+="ESCAPED BY '' "
        sql+="LINES TERMINATED BY '' "
        sql+="(@v); "
    else
        sql="SET @v = ""'""${value}""'""; "
    fi
    sql+="UPDATE tasks SET ${column} = @v WHERE ${selector};"
    #echo ${sql}
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
