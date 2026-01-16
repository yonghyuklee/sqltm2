#!/bin/bash --posix

scriptdir="$(readlink -f ${0})"
SQLTM_BASE="${SQLTM_BASE:-${scriptdir%/*/*}}"

# LRZ Linux cluster, mpp segment
connect_mpp ()
{
    local sqltm_local="/naslx/projects/t3881/t388143/sqltm/etc"
    local ssh_db="ssh -F ssh.cfg db_mpp"
    while true; do
    	${ssh_db} "cd ${sqltm_local} && ssh -F ssh.cfg -N db_p2"
        sleep "${time_interval}"
    done
    return
}

# LRZ SuperMUC
connect_sm ()
{
    local sqltm_local="/gpfs/work/pn69hi/di49yep4/sqltm/etc"
    local ssh_db="ssh -F ssh.cfg ${1}"
    while true; do
    	${ssh_db} "killall ssh; cd ${sqltm_local} && ssh -F ssh.cfg -N db_p1"
        sleep "${time_interval}"
    done
    return
}

# TGCC Curie
connect_curie ()
{
    local sqltm_local="/ccc/work/cont005/tum/opalkada/sqltm/etc"
    local ssh_db="sshpass -f $HOME/pw ssh -F ssh.cfg curie"
    while true; do
        ${ssh_db} "ssh curie50 \"killall ssh; cd ${sqltm_local} && ssh -F ssh.cfg -N db_p1\"" 
        sleep "${time_interval}"
    done
    return
}


time_interval=10 # reconnect time interval

cd "${SQLTM_BASE}/etc" || exit

if [[ "$#" == "0" ]]; then
    echo "usage: ${0} <system name>"
    echo "valid system names: curie, hw, sb, wm, mpp"
    exit
else
    system="${1}"
fi

if [[ "${system}" == "hw" ]]; then
    connect_sm db_hw
elif [[ "${system}" == "sb" ]]; then
    connect_sm db_sb
elif [[ "${system}" == "wm" ]]; then
    connect_sm db_wm
elif [[ "${system}" == "mpp" ]]; then
    connect_mpp
elif [[ "${system}" == "curie" ]]; then
    connect_curie
fi
