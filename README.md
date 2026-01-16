Created By Dr. Daniel Opalka

# SQL Task Manager (SQLTM)
The SQL Task Manager is a portable framework for parallel batch computations written
in Bash. 

## Concept and workflow
- Create (perhaps by a script) input files for a compute task
- Implement a script that runs the job (there are libraries provided 
  for common tasks)
- Add input files and task script to sqlite3 database
- Move the SQLTM code to the systems where you would like to run the
  calculations
- Submit compute jobs as appropriate


## Create sqlite3 database
Two examples are provided using Python and plain Bash code:

The Python example is more suitable for large numbers of calculations 
and automated structure generation with the Atomic Simulation 
Environment (ASE). Examples for typical use cases are convergence tests.

The Bash script is ideal if a single calculation is added to a database
since it is very easy to understand and modify. The script uses template
input files, modifies and adds them to the database using standard programs 
such as awk and sed. 


## Implementation of a task script
A link to a bash script which is executed on the compute node must be
stored in the database. For some typical calculations and code routines are
already included. The recommended use is to call bash functions in a
library for the respective code. In this typically very small bash script
the details (path, executable) of the compute environment must be provided.
A few examples are provided in the templates folder which can be copied to
the bin directory and adjusted according to the target system.

1. libqe.sh/qe_scf.sh
    Self-consistent field, geometry optimization and density of states 
    calculations for Quantum Espresso.

2. libaims.sh/aims_scf.sh
    Self-consistent field and geometry optimization calculations for 
    FHI-AIMS. 


## Create archive with SQL Task Manager execution scripts
1. copy/link the following files into the sqltm/lib directory
    - sqlite3 (sqlite executable)
    - rrs (reverse remote shell executable, statically linked)
    - rrs.pem (certificate file for rrs)
    - create lock executable by running tools/make_lock.sh

2. create archive with all required file by executing make_tarball.sh
   script (optionally add name as first argument)
    
## Move SQLTM and SQLite database to target system and run calculations
Depending on the environment (batch scheduling system), the respective
script must be executed which fetches the next pending job, executes the
task script and saves the output data in the database. Example submission
scripts (require modification!) are provided as well in the examples directory.

The following scripts are available: 
- llsql.sh (LoadLeveler)
- pbssql.sh (Portable Batch System)
- slurmsql.sh (Slurm Workload Manager)

## Adjust task script on the target system
The task script is a simple bash script, which sets a few system specific
environment variables such as the MPI prefix and executable path.  Typically 
the script call routines from the corresponding library (e. g. libaims.sh).

## Additional tools and utilities
### sql_cp.py
copy/merge database files

### sql_rm.py
purge task from database including dependencies (allocated hosts)

### make_tarball.sh
create tar-archive with all files required to run SQLTM on the target
platform (includes db locker, sqlite3 executable, optional rrs, rrs.pem and SQLTM required scripts)

### make_lock.sh
compile lock program to lock sqlite3 database against concurrent write
access (this is typically a problem if the database is stored on an NFS
filesystem) 

## Rutile slab generation
Tested successfully with the following environment:
```
conda create -n sqltm python=3.12 -y
pip install numpy scipy matplotlib ase
pip install mysql-connector-python
```

### Workflow
1. Move to the slab example directory:
   `cd examples/slabs`
2. Edit `rutile.py`, which defines bulk and surface structural parameters.
 - Set the metal element:
   `metal = 'Ru' # default: 'Ru'`
 - Specify the rutile unit cell parameters:
     - `a`, `c`: lattice parameters
     - `x`: oxygen internal coordinate defining the O sublattice in the P4₂/mnm space group
3. Move to the metal-oxide-specific directory:
   `cd RuO2`
4. Check `rutile_slab.py` and ensure:
   `metal = 'Ru'`
   is consistent with the setting in `rutile.py`.
5. Generate the slab structures:
   `python rutile_slab.py`
