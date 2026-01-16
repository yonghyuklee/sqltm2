#!/bin/bash --posix

if [[ "$#" == "0" ]]; then
    echo "Usage: ${0} <DATABASE NAME>"
    exit
fi

libsql_dir="$(dirname $(readlink -f ${BASH_SOURCE}))/../lib"
source "${libsql_dir}/libsql.sh"
db="${1}"

# set some runtime parameters and append new AIMS job to database
add ()
{
    local db="${1}"
    local id
    # create tables if they do not yet exist
    sql_init "${db}" input1 input2 output1 output2
    id=$(sql_new "${db}")
    # standard schema
    sql_set "${db}" "${id}" name "${name}"
    sql_set "${db}" "${id}" task_script "${task_script}" 0
    sql_set "${db}" "${id}" description "${description}"
    sql_set "${db}" "${id}" priority "${priority}"
    sql_set "${db}" "${id}" status "${flag_pending}"
    sql_set "${db}" "${id}" ncores "${ncores}"
    sql_set "${db}" "${id}" min_cores "${min_cores}"
#    sql_set "${db}" "${id}" workdir "${workdir}"

    # input
    sql_set "${db}" "${id}" input1 "$(<${input1})"
    sql_set "${db}" "${id}" input2 "$(<${input2})"
    return
}

# configure job (standard schema)
name="test"
#task_script="$(pwd)/run.sh"
task_script="aims_scf.sh"
description=""
priority="2000"
ncores="560"
min_cores="560"
#workdir="$(pwd)"
input1="control.in"
input2="geometry.in"

add "${db}"
