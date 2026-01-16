#!/bin/bash --posix

sql_script="$(readlink -f ${BASH_SOURCE})"
SQLTM_BASE="${SQLTM_BASE:-${sql_script%/*/*}}"

source "${SQLTM_BASE}/lib/libsql.sh"

if [[ "$#" == "0" ]]; then
    echo "Usage: ${0} <DATABASE NAME> <SELECTOR>> <INPUT 1> [<INPUT 2> .. <INPUT N>]"
    echo "SELECTOR is used to determine the rows to be substituted."
    echo "The script adds = <FILENAME> to identify the respective row in the selection"
    echo "Example:"
    echo "name = 'surface_energy' and description"
    exit
fi
db="${1}"
selector="${2}"
shift
shift
files="$@"

echo "Replace input"
echo "You may need to update other input files before running the tasks (e.g. geometry.in)"
echo "continue?"
read

for i in $files; do
    fn="$(basename ${i})"
    sql="SELECT id FROM tasks WHERE ${selector} = ""'"${fn%%.*}"'"";"
    id=$(sql_execute "${db}" "${sql}")
    if [[ -z "${id}" ]]; then
        echo "No matching row for ${i}"
    else
        echo "${fn%%.*} Replacing input1 in row $id with $i"
        sql_set "${db}" "${id}" input1 "${i}"
    fi
done


