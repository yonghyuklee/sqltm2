#!/bin/bash --posix
#set -x

#PREFIX="${HOME}/stow/db"
#PREFIX="${WORK}/db"
PREFIX="/export/opalka/db"
VERSION="10.3.8"
OS="linux-x86_64"
#OS="linux-glibc_214-x86_64"
fn="$(pwd)/mariadb-${VERSION}-${OS}.tar.gz"

basedir="${PREFIX}/mariadb-${VERSION}-${OS}"
datadir="${PREFIX}/data"
logdir="${PREFIX}/log"
cnf="${PREFIX}/my.cnf"
socket="${datadir}/mysql.sock"
port=3746
mysql="${basedir}/bin/mysql -P ${port}"
adminpw="Wat6thap"

install_db ()
{
    # extract archive & create directories
    if [[ ! -d "${basedir}" ]]; then
        mkdir -p "${PREFIX}"
        cd "${PREFIX}"
        tar -xzf "${fn}"
    fi
    mkdir -p "${datadir}"
    mkdir -p "${logdir}"
    chmod 750 "${PREFIX}"
    chmod 750 "${datadir}"
    chmod 750 "${logdir}"
    
    # dump configuration file
    cat > "${cnf}" << EOF
[mysqld]
datadir=${datadir}
socket=${socket}
#tmpdir=/mnt/mgmt/var/lib/mysql_tmp
bind-address = 0.0.0.0
port=${port}
local-infile=1
autocommit=1
innodb_buffer_pool_size=256M
#query_cache_size=100M
#max_connections=151
#thread_cache_size=15
skip_name_resolve=0
max_allowed_packet=100M
innodb_lock_wait_timeout=600

[mysqld_safe]
log-error=${logdir}/mysqld.log
pid-file=${logdir}/mysqld.pid

[mysqldump]
max_allowed_packet=512M
EOF

    # install database
    "${basedir}/scripts/mysql_install_db" \
	--skip-test-db \
        --datadir=${datadir} \
        --basedir="${basedir}" \
        --defaults-file="${cnf}" \
        --skip-name-resolve || exit
    echo "starting mysqld"
    cd "${basedir}"
    nohup bin/mysqld_safe --defaults-file="${cnf}" &
    return 0
}


# setup accounts, remove test data, secure database
secure_db ()
{
    local admin="admin" # root user
    # a valid pw hash can be obtained by
    # python -c 'from hashlib import sha1; print "*" + sha1(sha1("%3dfop7/").digest()).hexdigest().upper()'
    # where "%3dfop7/" is the pw

    # set password for all root accounts
    sql="UPDATE mysql.user "
    sql+="SET password = PASSWORD('${adminpw}')"
    sql+="WHERE user = 'root';"
    # delete all anonymous users if any (DROP USER does not work for empty username)
    sql+="DELETE FROM mysql.user WHERE user='';"
    # mysql by default allows anonymous access to test_* DBs
    # check: SELECT * FROM mysql.db \G
    sql+="DELETE FROM mysql.db WHERE db LIKE 'tes%' AND user='';"
    # rename root to admin user
    sql+="UPDATE mysql.user SET user='admin' WHERE user='root';"
    #sql+="RENAME USER 'root'@'localhost' to '${admin}'@'localhost';"
    #sql+="RENAME USER 'root'@'$(hostname)' to '${admin}'@'$(hostname)';"
    sql+="FLUSH PRIVILEGES;"
    # remove test database
    sql+="DROP DATABASE IF EXISTS test;"
    # drop other user accounts if any
    #sql+="DROP USER ''@'localhost';"

    ${mysql} -u root -h "127.0.0.1" -e "${sql}"
    #${mysql} -u admin -h "127.0.0.1" --password="${adminpw}" -e "${sql}"
    return 0
}

add_db ()
{
    local db="${1}"
    local host="${2:-"127.0.0.1"}"
    # create database
    sql="DROP DATABASE IF EXISTS ${db};"
    sql+="CREATE DATABASE ${db};"
    ${mysql} -u admin --password="${adminpw}" -h "${host}" -e "${sql}"
    return 0
}


add_user ()
{
    local db="${1}"
    shift
    local user="${1}"
    shift
    local host="${*:-$(hostname)}"
    # a valid pw hash can be obtained by
    # python -c 'from hashlib import sha1; print "*" + sha1(sha1("%3dfop7/").digest()).hexdigest().upper()'
    # where "%3dfop7/" is the pw
    local pw_hash="*69F47A42FA21EE54AB1383F75A89D4DFBB38161B" # default pw (sqltmdb), should be changed by user
    local privileges="ALL"
    #local privileges="SELECT,UPDATE,DELETE,ALTER"
    sql=""
    for h in $host; do
        sql+="DROP USER IF EXISTS '${user}'@'${h}';"
        sql+="CREATE USER '${user}'@'${h}' IDENTIFIED VIA mysql_native_password USING '${pw_hash}';"
        sql+="GRANT ${privileges} ON ${db}.* TO '${user}'@'${h}';"
        sql+="GRANT FILE ON *.* TO '${user}'@'${h}';"
    done
    sql+="FLUSH PRIVILEGES;"
    ${mysql} -u admin --password="${adminpw}" -h "127.0.0.1" -e "${sql}"
    return 0
}


create_db_schema ()
{
    local db="${1}"
    local host="${2:-localhost}"
    local user="admin"
    sql="DROP TABLE IF EXISTS hosts;"
    sql+="DROP TABLE IF EXISTS tasks;"
    sql+="DROP TABLE IF EXISTS jobs;"
    ${mysql} --password="${adminpw}" --database="${db}" -u "${user}" -h "${host}" -e "${sql}"
    # jobs table
    sql="CREATE TABLE IF NOT EXISTS "
    sql+="jobs"
    sql+="(id INTEGER PRIMARY KEY AUTO_INCREMENT"
    sql+=",jobname TEXT"
    sql+=",dispatch_time INTEGER"
    sql+=",time_limit INTEGER"
    #sql+=",tot_cores INTEGER"
    sql+=",scratch TEXT"
    sql+=");"
    ${mysql} --password="${adminpw}" --database="${db}" -u "${user}" -h "${host}" -e "${sql}"
    # task table
    sql="CREATE TABLE IF NOT EXISTS "
    sql+="tasks"
    sql+="(id INTEGER PRIMARY KEY AUTO_INCREMENT"
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
    sql+=",CONSTRAINT fk_task_jobid FOREIGN KEY(jobid) REFERENCES jobs(id)"
    sql+=");"
    # hosts table
    sql+="CREATE TABLE IF NOT EXISTS "
    sql+="hosts"
    sql+="(id INTEGER PRIMARY KEY AUTO_INCREMENT"
    sql+=",name TEXT"
    sql+=",jobid INTEGER DEFAULT 0"
    sql+=",taskid INTEGER"
    sql+=",status INTEGER"
    sql+=",FOREIGN KEY(jobid) REFERENCES jobs(id)"
    sql+=",FOREIGN KEY(taskid) REFERENCES tasks(id)"
    sql+=");"
    #echo "${sql}"
    ${mysql} --password="${adminpw}" --database="${db}" -u "${user}" -h "${host}" -e "${sql}"
    return 0
}

#install_db || exit
#secure_db || exit
#add_db opalka '127.0.0.1' || exit
#vlan72='195.37.7.0/255.255.255.0' # internal PRACE network
server='129.187.122.133' # server.theo.chemie.tu-muenchen.de
supermuc1='10.6.0.0/255.255.128.0' # SuperMUC Sandy Bridge + Westmere segment
supermuc2='10.7.0.0/255.255.128.0' # SuperMUC Haswell segment
curie50='132.167.142.192' # curie50 login node
curie51='132.167.142.193' # curie51 login node
#add_user opalka opalka '127.0.0.1' "${supermuc1}" "${supermuc2}" "${server}" "${curie50}" "${curie51}" "${vlan72}" 
#add_user opalka opalka '%'
#create_db_schema opalka '127.0.0.1'

#add_db yonghyuk '127.0.0.1' || exit
#add_user yonghyuk yonghyuk '%'

#add_db timmermann '127.0.0.1' || exit
#add_user timmermann timmermann '%'
#create_db_schema timmermann '127.0.0.1'

#add_db anic '127.0.0.1' || exit
#add_user anic anic '%'
#create_db_schema anic '127.0.0.1'

# start mysql
#./bin/mysqld_safe --defaults-file=..PATH TO MARIADB.../my.cnf &

# shutdown with
#bin/mysqladmin shutdown -S ../data/mysql.sock  -u admin -p
# bin/mysqladmin shutdown -h 127.0.0.1 -u root -P 3746 -p
# bin/mysqladmin shutdown -h 127.0.0.1 -u admin -P 3746 -p

# dump and restore
#bin/mysqldump -S ../data/mysql.sock db_name > backup-file.sql
#bin/mysql -S ../data/mysql.sock db_name < backup-file.sql

# ssh tunnel
#ssh -T -C -f -N -M -S ${HOME}/.ssh/tmp/hw-db-socket -L 3746:127.0.0.1:3746 hw1
#ssh -S ${HOME}/.ssh/tmp/hw-db-socket -O exit hw1

# list user accounts
# SELECT user, host from mysql.user;


#"${srcdir}/scripts/mysql_install_db" \
#    --defaults-file="${PREFIX}/my.cnf" \
#    --basedir="${PREFIX}/${VERSION}" \
#    --skip-auth-anonymous-user \
#    --datadir=${datadir} \
#    --srcdir=${srcdir} \
#    --builddir=${builddir} \
#    --skip-name-resolve


