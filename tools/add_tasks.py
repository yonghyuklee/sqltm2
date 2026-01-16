#!/usr/bin/python3
from __future__ import print_function
import sys, os
import string
import glob
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sqltm

if len(sys.argv) < 5:
    print('Usage: ' + sys.argv[0] + ' <db> <parameter file> <task script> <ncores>')
    print('The field "name" in the database is set to the basename of <parameter file>')
    raise SystemExit

# read arguments and fill mandatory fields in standard db schema
task = {}
db=sys.argv[1]
fn=sys.argv[2] # parameters file
task['task_script'] =sys.argv[3] # task_script
task['ncores'] = int(sys.argv[4]) # no of MPI processes
path, fn_p = os.path.split(fn)
task['name'] = os.path.splitext(fn_p)[0]
task['min_cores'] = task['ncores']
task['status'] = 1
task['priority'] = 1000 + int(task['ncores'])
#task['description'] = ""

# read parameter table
with open(fn, 'r') as fd:
    columns = fd.readline().strip('#').split()
parameters = pd.read_csv(fn, 
    sep="\s+",
    header=0,
    names=columns,
    comment='#',
    dtype=str)

# add columns to table if necessary
sqltm.init_db(db, columns)

# read input templates
templates = {}
for fn_t in glob.glob(os.path.normpath(path) + '/input*.inp'):
    k = os.path.splitext(os.path.basename(fn_t))[0]
    with open(fn_t, 'r') as fd:
        templates[k] = string.Template(fd.read())

# read templates and add to database
for p in parameters.T.to_dict().values():
    for k in templates.keys():
        task[k] = templates[k].safe_substitute(p)
    for k,v in p.items():
        if os.path.isfile(v): 
            with open(v, 'r') as fd:
                work = string.Template(fd.read())
            task[k] = work.safe_substitute(p)
        else:
            task[k] = v
    #print(task)
    #print(template.safe_substitute(p))
    #raise SystemExit
    sqltm.add(db, task, task.keys())


