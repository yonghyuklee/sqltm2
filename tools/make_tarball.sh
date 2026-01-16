#!/bin/bash --posix

name="${1:-"sqltm"}"
script_dir="$(dirname ${BASH_SOURCE})"
src_dir="$(readlink -f ${script_dir}/..)"
version="$(git  -C ${src_dir} rev-parse HEAD)"
files="lib/libaims.sh
    lib/libqe.sh
    lib/libsql.sh
    lib/llsql.sh
    lib/pbssql.sh
    lib/slurmsql.sh
    tools/sql_rm.sh
    templates/ll.cmd
    templates/pbs.cmd
    templates/slurm.cmd
    templates/aims_run.sh
    templates/qe_run.sh
    lib/rrs.pem
    lib/rrs
    lib/lock
    lib/sqlite3"

#tar -C ${src_dir} -hczf "${name}-${version}.tar.gz" ${files}
tar -C ${src_dir} --transform 's,^,sqltm/,S' -hcjf "${name}-${version}.tar.bz2" ${files}
