#!/bin/bash --posix

init_lock ()
{
    local cwd="$(pwd)"
    local pipe
    if [[ ! -e "${lock}" ]]; then
        # compile lock-file implementation as lockfile/flock etc. may not be
        # available on compute node
        pipe="${cwd}/lock_$$.c"
        lock="${cwd}/../lib/lock"
        mkfifo ${pipe}
        echo '
        #include <fcntl.h>
        #define DELAY 1
        
        int main(int argc, char **argv) {
            int fd = 0;
        
            while ((fd = open(argv[1], O_RDWR|O_CREAT|O_EXCL|O_DSYNC, 0444)) == -1) {
                sleep(DELAY);
            } 
            close(fd);
        
            return 0;
        
        }' > "${pipe}" &
        gcc -o "${lock}" "${pipe}" -static
    
        if [[ $? -ne 0 ]]; then
            echo "ERROR (init_lock): Could not compile lock. gcc compiler may not be available."
        fi
        rm -f "${pipe}"
    	echo "${lock} successfully created"
    else
        echo "WARNING (init_lock): ${lock} already exists. Compilation skipped."
    fi
    return
}

init_lock
