#!/bin/bash --posix

declare -a url=(
"https://syncandshare.lrz.de/dl/fiTEA3B35vPx7iviaM8A7Tw3/lock"
"https://syncandshare.lrz.de/dl/fiK6cqHvZLi8KY4R2iVFmobq/mysql"
"https://syncandshare.lrz.de/dl/fi8CJFWWZwvBCUwfu24ALKjr/mysqladmin"
"https://syncandshare.lrz.de/dl/fiPnWf1W2YAr8k1uYKb1NH2R/rrs"
"https://syncandshare.lrz.de/dl/fiEFdnXNGG797upMpr9sLTRc/sqlite3"
)

declare -a checksum=(
"87981c9e5ab392522a104ed251f556ab"
"35fb82e124bfd98fceda3fb69d059cd3"
"0e8b1e988b5dd861f194209fc4efbebe"
"58ae242a6b6cb9d18941bc5cac94d0eb"
"5baae6f50c8de00242ab9537c17cb202"
)

script_dir="$(dirname $(readlink -f ${BASH_SOURCE}))"
cd "${script_dir}"
git_dir="$(git rev-parse --show-toplevel)"
cd "${git_dir}/sbin"

for ((i=0; i<${#url[@]}; ++i)); do
    fn="$(basename ${url[${i}]})"
    if $(echo "${checksum[${i}]}" "${fn}" | md5sum --status --check -); then
        echo "MD5 check successful"
    else
        echo "MD5 check failed. Downloading ${fn}"
        wget "${url[${i}]}"
    fi
    chmod 750 "${fn}"
done
