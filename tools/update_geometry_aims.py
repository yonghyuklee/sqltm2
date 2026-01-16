#!/usr/bin/python3
from __future__ import print_function
import sys, os
import pickle
import string
import ase.io
import ase.constraints

sys.path.append(os.environ['HOME']+'/src/parser/parser')
import common, aims
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import sqltm

db = sys.argv[1]
selector = sys.argv[2]
status = int(sys.argv[3])
#selector="id > 647"
#selector="status = 5 AND name = relax"

rows = sqltm.get(db=db, selector=selector, columns="id,name,output1")

print("{n} rows selected".format(n=len(rows)))
for r in rows:
    print("{id:>20d}{name:>60s}".format(id=r['id'], name=r['name']))
check = input("IS THIS CORRECT (y/n)? ")
if check != "y":
    print("Aborted.")
    raise SystemExit

print("\nParsing ....")
for r in rows: 
    print("{id:>20d}{name:>60s}".format(id=r['id'], name=r['name']))
    # extract geometry from output file
    w = aims.parse(r['output1'])
    common.compute_derived_data(w)
    if 'cell' in w:
        cell = ase.Atoms(symbols=w['symbols'], positions=w['xyz'], cell=w['cell'], pbc=(1,1,1))
    else:
        cell = ase.Atoms(symbols=w['symbols'], positions=w['xyz'], pbc=None)
    if 'spin_q' in w:
        cell.set_initial_magnetic_moments(w['spin_q'])
    c = ase.constraints.FixAtoms(mask=w['constrain_relaxation'])
    cell.set_constraint(c)
    ase.io.write("geometry.in", cell, format="aims")
    with open("geometry.in", 'r') as fd:
        geo = fd.read()

    #print(geo)
    # update database and set status to "pending"
    sqltm.set(db, r['id'], 'input2', geo)
    sqltm.set(db, r['id'], 'status', status)
