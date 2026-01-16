#!/usr/bin/python3
from __future__ import print_function
import sys, os

p = os.path.dirname(os.path.abspath(__file__))
sys.path.append(p + '/../')
import rutile as structure
import slab
#sys.path.append('/Users/yonghyuklee/Dropbox/python/parser/parser')
#import aims

# adjust basis, input etc.
metal = 'Ru'
#basis = { 'H': "l_2", 'O': "l_2", metal: "l_1" }
basis = { 'H': "t_2", 'O': "t_2", metal: "t_1" }

#dft = "PBE"
dft = "RPBE"

input_template = [ "aims_pbe_light.inp" ]
#input_template = [ "aims_pbe_tight.inp" ]
#input_template = [ "aims_rpbe_light.inp" ]
#input_template = [ "aims_rpbe_tight.inp" ]

# bulk relaxation
#input_template = [ "aims_pbe_light_cellopt.inp" ]
#input_template = [ "aims_rpbe_light_cellopt.inp" ]

#cores_per_node = 2*12 # JURECA
#cores_per_node = 2*14 # Medium_Node SuperMUC
cores_per_node = 16 # CURIE

narg = len(sys.argv) 
if narg > 1:
    db = sys.argv[1]
else:
    print("No database selected. Using default from ~/.my.cnf file.")
    db = None

tasks = []
# initialize task dict with some default values
task = {}
# standard schema
task['name'] = "surface_energy"
task['task_script'] = "aims_relax_YH.sh"
task['description'] = "surface energy from slab"
task['priority'] = 1000
task['ncores'] = 8*cores_per_node
task['min_cores'] = 6*cores_per_node
task['status'] = 8
# input/output columns
task['input1'] = None
task['input2'] = None
task['output1'] = None
task['output2'] = None
# additional columns stored as TEXT/BLOB
task['orientation'] = [0,0,1]
task['unitcell'] = [1,1,1]
task['supercell'] = [1,1,1]
task['program'] ="FHI-AIMS"
task['termination'] = None
task['constraints'] = None
task['rmlayers'] = None
task['dft'] = dft
task['basis'] = None
task['structure'] = None
task['spin'] = None

# set required column names in database
columns = list(task.keys())

# unitcell
unitcell = structure.unitcell(dft=task['dft'], basis=basis)
task['basis'] = ','.join('{}:{}'.format(k, v) for k, v in sorted(basis.items()))

# bulk cells
task['ncores'] = 8*cores_per_node
task['min_cores'] = task['ncores']
task['structure'] = "bulk"
#tasks += structure.bulk(task)

# slabs
task['vacuum'] = 10.0 # vacuum 
task['structure'] = "slab"
#task['set_volume'] = 1200.0*2
task['ncores'] = 32*cores_per_node
task['min_cores'] = task['ncores']
task['priority'] += task['ncores']
#task['constraints'] = [4, 4] # relax top/bottom 4 layers + termination
#### (001)
tasks += structure.slab_001(task)
tasks += structure.H_slab_001(task)
tasks += structure.OH_slab_001(task)
tasks += structure.H2O_slab_001(task)
#### (010)
tasks += structure.slab_010(task)
tasks += structure.H_slab_010(task)
tasks += structure.OH_slab_010(task)
tasks += structure.H2O_slab_010(task)
tasks += structure.OH_CUS_slab_010(task)
#### (011)
tasks += structure.slab_011(task)
tasks += structure.H_slab_011(task)
tasks += structure.OH_slab_011(task)
tasks += structure.H2O_slab_011(task)
#### (110)
tasks += structure.slab_110(task)
tasks += structure.H_slab_110(task)
tasks += structure.OH_slab_110(task)
tasks += structure.H2O_slab_110(task)
tasks += structure.OH_CUS_slab_110(task)
#### (111)
tasks += structure.slab_111(task)
tasks += structure.H_slab_111(task)
tasks += structure.OH_slab_111(task)
tasks += structure.H2O_slab_111(task)

#### Norskov's sketchy slab model
#task['priority'] = 2500
tasks += structure.norskov(task)

input_template.append("geometry.in")
#for t in tasks:
    #t['description'] = slab.map_v1_v2(t['description'])
    #t['name'] = 'se_light_Ir'
    #t['name'] = 'surface_energy'
    #t['name'] = 'norskov'
    #print("""{0:>30s}: {0:s},""".format(repr(t['description'])))


slab.add_tasks(db, tasks, unitcell, input_template, columns, test=True)
#slab.add_tasks(db, tasks, unitcell, input_template, columns, test=False)
