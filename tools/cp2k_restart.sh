#!/bin/bash --posix

sqltm_sbin="$(dirname $(readlink -f ${BASH_SOURCE}))"
sqltm_sbin="$(readlink -f ${sqltm_sbin}/../sbin)"
mysql_exe="${sqltm_sbin}/mysql"

# examples
# cp2k_restart.sh opalka "name like '%H2O%eq'" 0

if [[ "$#" == "0" ]]; then
    echo "Usage: ${0} <DATABASE NAME> <SELECTOR> <FLAG>"
    echo "FLAGS:"
    echo "0: restart from CP2K restart file by copying row and resetting counters (default)"
    echo "1: in place restart from input file by appending restart section (if not already present)"
    exit
fi

db_name="${1}"
selector="${2}"
flag="${3:-0}"

# restart block
read -r -d '' restart_block << EOS
\n
&EXT_RESTART
   RESTART_FILE_NAME ./restart
   RESTART_COUNTERS true
&END EXT_RESTART
EOS

case "${flag}" in
    0)
        # reset some counters (change name from *_eq -> *_pr), steps = 20000
        sql="INSERT INTO tasks (name, jobid, ncores, task_script, input1, input2, status) "
        sql+="SELECT name, jobid, ncores, task_script, input2, input2, -1 FROM tasks "
        sql+="WHERE ${selector};"
        sql+="UPDATE tasks SET "
        sql+="name = REGEXP_REPLACE(name, '^(.*)_eq$', '\\\\1_pr'),"
        sql+="input1 = REGEXP_REPLACE(input1, 'STEPS.*', 'STEPS 20000'),"
        sql+="input1 = REGEXP_REPLACE(input1, 'STEP_START_VAL.*', 'STEP_START_VAL 0'),"
        sql+="input1 = REGEXP_REPLACE(input1, 'TIME_START_VAL.*', 'TIME_START_VAL 0.0'), "
        sql+="input1 = IF(input1 REGEXP ' RESTART_FILE_NAME.*',"
        sql+="REGEXP_REPLACE(input1, '( RESTART_FILE_NAME).*', '\\\\1 ./restart'),"
        sql+="CONCAT(input1, ""'"${restart_block}"'"")) "
        sql+="WHERE status = -1;"
        sql+="UPDATE tasks SET "
        sql+="status = 0,"
        sql+="input1 = REGEXP_REPLACE(input1, 'RESTART_COUNTERS.*', 'RESTART_COUNTERS false') "
        sql+="WHERE status = -1;"
        ;;
    1)
        # append restart block to input file and set status to pending
        sql="UPDATE tasks SET "
        sql+="status = 1,"
        #sql+="status = 8,"
        #sql+="name = REGEXP_REPLACE(name, '^(.*)', '\\\\1_re') "
        sql+="input1 = REGEXP_REPLACE(input1, 'RESTART_COUNTERS.*', 'RESTART_COUNTERS true'),"
        sql+="input1 = IF(input1 REGEXP ' RESTART_FILE_NAME.*',"
        sql+="REGEXP_REPLACE(input1, '( RESTART_FILE_NAME).*', '\\\\1 ./restart'),"
        sql+="CONCAT(input1, ""'"${restart_block}"'"")) "
        sql+="WHERE ${selector};"
        ;;
    *)
        echo "Unknown flag"
        echo "Usage: ${0} <DATABASE NAME> <SELECTOR> <FLAG>"
        exit
esac

echo $sql
echo "Is this correct (cancel with ctrl-c)?"
read


${mysql_exe} --skip-column-names --silent --raw --database="${db_name}" -e "${sql}"

#'\\bRESTART_FILE_NAME\\s*..restart' and status = 5;
# qe restart
#sed '/^\s\+restart_mode\s\+=.*/{s/from_scratch/restart/}' -i "${inputfile}"
