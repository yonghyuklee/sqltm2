#!/usr/bin/python

import sys, os
import scipy as sp
from ase import Atoms
from ase.build import rotate,add_vacuum
import re

sys.path.append('../')
import sqltm
import asex

def create_unitcell(c):
    # Positions from Wyckoff table
    # space group 136, Ti 2a, O 4f
    x = c['x']
    cell_vectors = sp.array([[c['a'], 0, 0], [0, c['a'], 0], [0, 0, c['c']]])
    unitcell = Atoms(["Ir", "Ir", "O", "O", "O", "O"], 
        scaled_positions=[
            (0,0,0), (0.5,0.5,0.5),
            (x, x, 0.0), (-x, -x, 0.0), (-x+0.5, x+0.5, 0.5), 
            (x+0.5,-x+0.5, 0.5)],
        cell=cell_vectors,
        pbc=True)
    return unitcell

# sqlite3 database columns additional to standard schema
columns = ["orientation", "unitcell", "kgrid", "supercell", "basis",
    "program", "dft", "structure", "termination", "vacuum",
    "constraints"]
narg = len(sys.argv) 
if narg > 1:
    fn = sys.argv[1]
    sqltm.init_db(fn, columns)

# initialize task dict with some default values
task = {}
# standard schema
task['name'] = "surface_energy"
task['task_script'] = os.path.relpath("aims_scf.sh", os.path.expanduser('~'))
task['description'] = "surface energy from slab"
task['priority'] = 1000
task['ncores'] = 112
task['min_cores'] = 56
task['status'] = 1
# additional columns stored as BLOB
task['orientation'] = [0,0,1]
task['unitcell'] = [1,1,1]
task['kgrid'] = [1,1,1]
task['supercell'] = [1,1,1]
task['basis'] = "O:l_2,Ir:l_1"
task['program'] ="FHI-AIMS"
task['dft'] = "PBE"
task['structure'] = "slab"
task['termination'] = -1
task['vacuum'] = 0.0
task['constraints'] = None

# ***  create system configurations ***
# FHI-AIMS opt of conventional cell (PBE, light, O-l2, Ir-l1, smear=0.1, k_grid=11,11,15)
uc = { 'a': 4.533094, 'c': 3.182257, 'x': 0.308375 }
unitcell = create_unitcell(uc)

# orientation: direction/orientation
# supercell: slab dimension, first two elements for surface reconstruction (e. g. 1x1, 2x1), 
# the third element defines the slab thickness (in cell units)
# vacuum: vacuum (in c-vector direction, NOT necessarily z-axis)
# constraints: constrain atoms (fix atomic layers between r[0] and nlayers - r[1])
tasks = []
#cores_per_node = 2*12 # JURECA
cores_per_node = 2*14 # Medium_Node SuperMUC

# bulk
t = { 'orientation': [0,0,0], 'termination': -1,  'supercell': [1,1,1], 'constraints': None }
t['task_script'] = os.path.relpath("aims_relax.sh", os.path.expanduser('~'))
tasks.append(sqltm.merge_dicts(task,t))

directions = [ [0,0,1], [0,1,0], [1,0,1], [1,1,0] ]
terminations = [ [0,1,2], [0,1,2], [0,1,2], [0,1,2] ]
termination_layers = [ [0,1,2], [0,1,2], [0,1,2], [0,1,2] ]
nrelax = 4 # no of layers to relax (remaining atoms are fixed)
for direction,termination,tl in zip(directions,terminations,termination_layers): 
    for i in range(len(termination)):
        t = { 'orientation': direction, 'termination': termination[i],  'supercell': [1,1,6],
            'vacuum': 10.0, 'constraints': [ nrelax + tl[i], nrelax + tl[i] ] }
        t['task_script'] = os.path.relpath("aims_relax.sh", os.path.expanduser('~'))
        t['ncores'] = 8*cores_per_node
        tasks.append(sqltm.merge_dicts(task,t))
        break
input1_template = "aims_pbe_light.inp"
input2_template = "geometry.in"
re_kgrid = re.compile(r"""^.*k_grid.*$""", re.MULTILINE)
for t in tasks:
    # create slab
    slab = asex.create_slab(t, unitcell)
    asex.fix_atoms(slab, t)
    kgrid = asex.kpoint_grid(slab, dx=0.02)
    # write slab geometry
    slab.write(filename=input2_template, format="aims")
    # create input files
    with open(input1_template, 'r') as fd:
        k_str = 'k_grid {0:>4d} {1:>4d} {2:>4d}'.format(*kgrid)
        input1 = re.sub(re_kgrid, k_str, fd.read())
    with open(input2_template, 'r') as fd:
        input2 = fd.read()
    # configure task
    t['input1'] = input1
    t['input2'] = input2
    t['kgrid'] = kgrid

    # add to database
    sqltm.add(fn, t, columns)
