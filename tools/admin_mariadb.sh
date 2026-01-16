#!/bin/bash --posix
#set -x

db="${1:-test}"
user="${2:-opalka}"

script_dir="$(dirname ${BASH_SOURCE})"
mysql="${script_dir}/../sbin/mysql -u admin"

vlan72='195.37.7.0/255.255.255.0' # internal PRACE network
server='129.187.122.133' # server.theo.chemie.tu-muenchen.de
supermuc='10.7.0.0/255.255.128.0' # supermuc Haswell compute nodes
linux_cluster_mpp2='10.156.95.5/255.255.255.0' # Linux cluster mpp2 segment

echo -n "Database ${db} may be dropped and recreated - enter admin password: "
read adminpw
adminpw="Wat6thap"

# recreate test database
create_db ()
{
    local db="${1}"
    sql="DROP DATABASE IF EXISTS ${db};"
    sql+="CREATE DATABASE ${db};"
    ${mysql} --password="${adminpw}" -e "${sql}"
    return
}


# grant privileges
grant_privileges ()
{
    local db="${1}"
    shift
    local user="${1}"
    shift
    local host="${*:-$(hostname)}"
    local pw_hash="*69F47A42FA21EE54AB1383F75A89D4DFBB38161B" # sqltmdb
    #privileges="ALL"
    local privileges="INSERT,SELECT,UPDATE,DELETE,ALTER"
    sql=""
    for h in $host; do
        sql+="GRANT ${privileges} ON ${db}.* TO '${user}'@'${h}' IDENTIFIED BY PASSWORD '${pw_hash}';"
        sql+="GRANT FILE ON *.* TO '${user}'@'${h}';"
    done
    sql+="FLUSH PRIVILEGES;"
    #${mysql} --password="${adminpw}" -e "${sql}"
    echo "${mysql} --password=${adminpw} -e ${sql}"
    return
}


create_user ()
{
    local db="${1}"
    shift
    local user="${1}"
    shift
    local host="${*:-$(hostname)}"
    local pw_hash="*69F47A42FA21EE54AB1383F75A89D4DFBB38161B" # sqltmdb
    sql=""
    for h in $host; do
        sql+="DROP USER IF EXISTS '${user}'@'${h}';"
        sql+="CREATE USER '${user}'@'${h}' IDENTIFIED VIA mysql_native_password USING '${pw_hash}';"
    done
    ${mysql} --password="${adminpw}" -e "${sql}"
    return
}

create_db_schema ()
{
    local db="${1}"
    sql="DROP TABLE IF EXISTS hosts;"
    sql+="DROP TABLE IF EXISTS tasks;"
    sql+="DROP TABLE IF EXISTS jobs;"
    ${mysql} --password="${adminpw}" --database="${db}" -e "${sql}"
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
    ${mysql} --password="${adminpw}" --database="${db}" -e "${sql}"
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
    ${mysql} --password="${adminpw}" --database="${db}" -e "${sql}"
    return
}


#create_db "${db}"
#create_db_schema "${db}"
#create_user "${db}" "${user}" "127.0.0.1" "localhost" "${server}" "${supermuc}" "${vlan72}"
grant_privileges "${db}" "${user}" "127.0.0.1" "localhost" "${server}" "${supermuc}" "${vlan72}" "${linux_cluster_mpp2}" 
