#!/bin/bash --posix
#set -x

sqltm_base="$(dirname $(readlink -f ${BASH_SOURCE}))/.."
db_base="/gpfs/work/pr92me/di49yep2/db"

log ()
{
    echo "[$(date +"%D %T")] ${1}"
    return
}

check_prog()
{
    which "${1}" > /dev/null
    if [[ ! $? == 0 ]]; then
        echo "$(pwd)/${1} not found" 
        exit
    fi
    return 0
}

# check db server is running
s ()
{
    local time_interval=5
    cd "${db_base}"
    check_prog "./mysql/sbin/mysqladmin" || exit
	check_prog "./mysql/sbin/mysqld_safe" || exit
    log "Checking DB server"
    while true; do
        #./mysql/sbin/mysqladmin --connect_timeout=5 -h 192.168.1.1 ping
        ./mysql/sbin/mysqladmin --connect_timeout=5 ping > /dev/null 2>&1
        if [[ $? == 1 ]]; then
            log "DB server is not alive."
            ./mysql/sbin/mysqld_safe --defaults-file=my.cnf
            log "DB server started"
        fi
    	sleep "${time_interval}"
    done
    return
}



# clients (e.g. CURIE)
c ()
{
	local time_interval=5
    cd "${sqltm_base}"
    check_prog "./sbin/mysqladmin" || exit
    log "Checking ssh tunnel to DB server"
    while true; do
        ./sbin/mysqladmin --connect_timeout=5 ping > /dev/null 2>&1
        if [[ $? == 1 ]]; then
            log "Connection to DB server failed."
            ssh -F etc/ssh.cfg -fN dbt
            log "SSH tunnel established"
        fi
    	sleep "${time_interval}"
    done
    return
}

$@
