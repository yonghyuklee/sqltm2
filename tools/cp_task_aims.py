#!/usr/bin/python3
from __future__ import print_function
import sys, os
import pickle
import string
import ase.io
import ase.constraints
import scipy.linalg as LA

sys.path.append(os.environ['HOME']+'/src/parser/parser')
import common, qe, aims
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sqltm

def center_slab(cell, z=0.0):
    # center slab around z=0
    norm_z = LA.norm(cell.cell[2], 2)
    vz = cell.cell[2,:]/norm_z
    max_z = max(cell.positions[:,2])
    min_z = min(cell.positions[:,2])
    mid_z = 0.5*(min_z + max_z) + z
    for x in cell.positions:
        x -= mid_z/vz[2]*vz[:] # shift center of slab to 0.0 in z direction
    return cell

#rows = sqltm.get(db="opalka", selector="id = 640")
#rows = sqltm.get(db="db.sqlite", selector="id = 25")
#rows = sqltm.get_last(db="opalka", selector="tasks.id > 600")

db = sys.argv[1]
selector = sys.argv[2]
template = None
if len(sys.argv) > 3:
    template = sys.argv[3]
    print("Using input1 from {0:s} in copy".format(template))

rows = sqltm.get(db=db, selector=selector)

print("{n} rows selected".format(n=len(rows)))
for r in rows:
    print("{id:>20d}{name:>60s}".format(id=r['id'], name=r['name']))
check = input("IS THIS CORRECT (y/n)? ")
if check != "y":
    print("Aborted.")
    raise SystemExit

tasks = [ dict(row) for row in rows ]

#fn = "pbe.pkl"
#with open(fn, 'rb') as fd:
#    tasks = pickle.load(fd)

for t in tasks: 
    task_id = t['id']
    # remove keys set by SQLTM
    del t['id']
    del t['jobid']
    del t['start_time']
    del t['complete_time']
    del t['pid']
    del t['workdir'] # comment if calc. should use old workdir

    # create geometry file from output
    w = aims.parse(t['output1'])
    common.compute_derived_data(w)
    t['kgrid'] = ','.join(str(x) for x in w['kgrid'])
    # change input file
    # read input template and substitute values (if any)
    if template is not None:
        d = { 'k_grid': """k_grid {0:>4d} {1:>4d} {2:>4d}""".format(*w['kgrid'])
            }
        with open(template, 'r') as fd:
            t['input1'] = string.Template(fd.read()).substitute(d)

    if 'cell' in w:
        cell = ase.Atoms(symbols=w['symbols'], positions=w['xyz'], cell=w['cell'], pbc=(1,1,1))
    else:
        cell = ase.Atoms(symbols=w['symbols'], positions=w['xyz'], pbc=None)
    if 'spin_q' in w:
        cell.set_initial_magnetic_moments(w['spin_q'])
    if 'constrain_relaxation' in w:
        c = ase.constraints.FixAtoms(mask=w['constrain_relaxation'])
        cell.set_constraint(c)

    cell = center_slab(cell, z=0.0)
    # sort by z-coordinate
    order = abs(cell.positions[:,2]).argsort()[::-1]
    cell = cell[order]

    ase.io.write("geometry.in", cell, format="aims")
    with open("geometry.in", 'r') as fd:
        t['input2'] = fd.read()
 
    # update/reset keys as appropriate
    t['name'] += '_' + str(task_id) + '_restart'
    t['status'] = -1
    t['output1'] = None
    t['output2'] = None

#    print(t['input1'])
#    print(t['input2'])
    sqltm.add(db, t, t.keys())


print("Status set to -1")
print("Adjust rows by using sql_set_all command, for example")
print('sql_set_all ' + db + ' "status = -1" task_script aims_scf.sh')
print('sql_set_all ' + db + ' "status = -1" name "<name>"')
print('sql_set_all ' + db + ' "status = -1" status 1')
