#!/bin/bash --posix
export LOGIN_HOST="127.0.0.1"
#export LOGIN_HOST="login21ib"

libsql_dir="$(dirname $(readlink -f ${BASH_SOURCE}))/../../lib"
source "${libsql_dir}/libsql.sh"
#db="${1:-"db.sqlite"}"
db="${1:-"${USER}"}"
template="${2:-"aims_pbe_light.inp"}"
datafile="${3:-"k_grid.dat"}"

# set some runtime parameters and append new AIMS job to database
add ()
{
    local db="${1}"
    local id
    # create tables if they do not yet exist
    sql_init "${db}" orientation unitcell kgrid supercell basis program dft structure termination vacuum input1 input2 output1 output2
    id=$(sql_new "${db}")
    # standard schema
    sql_set "${db}" "${id}" name "${name}"
    sql_set "${db}" "${id}" task_script "${task_script}" 0
    sql_set "${db}" "${id}" description "${description}"
    sql_set "${db}" "${id}" priority "${priority}"
    sql_set "${db}" "${id}" status "${flag_pending}"
    sql_set "${db}" "${id}" ncores "${ncores}"
    sql_set "${db}" "${id}" min_cores "${min_cores}"
    #sql_set "${db}" "${id}" workdir "${HOME}/tmp/aims/${id}"

    # additional columns stored as BLOB
    sql_set "${db}" "${id}" orientation "${orientation}"
    sql_set "${db}" "${id}" unitcell "${unitcell}"
    sql_set "${db}" "${id}" kgrid "${kgrid}"
    sql_set "${db}" "${id}" supercell "${supercell}"
    sql_set "${db}" "${id}" basis "${basis}"
    sql_set "${db}" "${id}" program "${program}"
    sql_set "${db}" "${id}" dft "${dft}"
    sql_set "${db}" "${id}" structure "${structure}"
    sql_set "${db}" "${id}" termination "${termination}"
    sql_set "${db}" "${id}" vacuum "${vacuum}"

    # input
#    sql_set "${db}" "${id}" input1 "$(readlink -f ${input1})"
#    sql_set "${db}" "${id}" input2 "$(readlink -f ${input2})"
    sql_set "${db}" "${id}" input1 "$(<${input1})"
    sql_set "${db}" "${id}" input2 "$(<${input2})"
    return
}

#if [[ "$#" == "1" ]]; then
#    echo "Add control.in and geometry.in to ${1}?"
#    read
#    add "${1}"
#    exit
#else
#    echo "usage: ${0} [${db} ${template} ${datafile}]"
#    echo "Create database/add files to ${1}?"
#    read
#fi

# configure job (standard schema)
name="convergence"
#task_script="$(pwd)/aims_scf.sh"
task_script="aims_scf.sh"
description="convergence of k-point grid and smearing"
priority="1000"
ncores="7"
min_cores="7"
# additional columns stored as BLOB
orientation="0,0,1"
unitcell="1,1,1"
kgrid="1,1,1"
supercell="1,1,1"
basis="O:l_2,Ir:l_1"
program="FHI-AIMS"
dft="PBE"
structure="bulk"
termination="-1"
vacuum="0.0"

# smearing in eV
smearing="0.10 0.20 0.30"
 
# for each row in datafile substitute %i% in template(s) and add to
# database
input1="control.in"
input2="geometry.in"

# create example geometry.in file (Oxygen molecule)
cat > ${input2} << EOF
atom 0.0000000000000000 0.0000000000000000 0.0000000000000000 O
atom 0.0000000000000000 0.0000000000000000 1.2000000000000000 O
EOF

n=10
for ((i=0; i<${n}; ++i)); do
    echo "Adding point ${i} to database"
    add "${db}"
done

#while read line
#do
#    [[ "${line}" =~ ^# ]] && continue
#    data=(${line})
#    for smear in $smearing; do
#        cp "${template}" "control.in"
#        for (( k=0; k<${#data[*]}; k++ )); do
#            sed "s/%${k}%/${data[${k}]}/g" -i "control.in" &> /dev/null
#        done
#        sed "s/%smear%/${smear}/g" -i "control.in" &> /dev/null
#        kgrid="${data[0]},${data[1]},${data[2]}"
#        add "${db}"
#        echo "Added point ${data[@]} (${smear})"
#    done
#	exit
#done < "${datafile}"
