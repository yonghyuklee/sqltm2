#!/usr/bin/python

from __future__ import print_function
from __future__ import absolute_import
import sys, os
import argparse
import multiprocessing
import pickle

sys.path.append(os.path.dirname(__file__))
import sqltm
sys.path.append(os.environ['HOME']+'/src/parser/parser')
import common, aims, cp2k, qe

# python3 ~/src/sqltm/tools/parse.py --selector 'name like "11_" and status = 3 and dft = "PBE"' --keys name,description,dft,structure,orientation
# python3 ~/src/sqltm/tools/parse.py --selector 'name like "11_" and status = 3 and dft = "PBE"' --keys # name,description,dft,structure,orientation,basis,dft
# python3 ~/src/sqltm/tools/parse.py --database opalka --selector 'name = "surface_energy" and status = 3 and basis = "H:l_2,Ir:l_1,O:l_2"' --keys name,description,dft,structure,orientation,dft,basis,termination

assert sys.version_info >= (3,0)

def parse(r):
    # select parser
    if r['program'] == 'FHI-AIMS' or r['program'] == 'AIMS':
        parse = aims.parse
    elif r['program'] == 'CP2K':
        parse = cp2k.parse
    elif r['program'] == 'QE':
        parse = qe.parse
    else:
        print("ERROR (parse): program key {p} not available for ID {id}.".format(p=r['program'], id=r['id'])) 
        return {}
    # parse
    id = r['id']
    d = { 'id': id }
    for c in cols: 
        try:
            w = parse(r[c])
            common.compute_derived_data(w)
            d = { **d, **w }
        except:
            print("ERROR (parse): output file in columns {col} with ID {id} could not be parsed.".format(col=c, id=r['id'])) 
    return d

ap = argparse.ArgumentParser(description="Parse output file(s) from SQL database")
ap.add_argument("--database", dest="db", default=None,
    help="Database name (default: read from ~/.my.cnf)")
ap.add_argument("--selector", dest="sel", default=None,
    help="SQL selector (default: status = 3)")
ap.add_argument("--columns", dest="cols", default="output1", 
    help="Comma separated SQL columns, last column has highest precedence (default: output1)")
ap.add_argument("--keys", dest="keys", default="name,description",
    help="Add keys from SQL column (default: name,description)")
ap.add_argument("--print", dest="print_keys", default="id,total_time_wall,scf_time_wall,total_energy", 
    help="Comma separated list or keys to be printed in table (default: id,total_time_wall,scf_time_wall,total_energy)")
# TODO (not so easy to determine selector), ap.add_argument("--update", dest="update", default=False, help="Add rows with keys that do not yet exist in pkl file.")
args = ap.parse_args()

cols = args.cols.split(',')
selector = args.sel
db = args.db
keys = args.keys
print_keys = args.print_keys.split(',')

rows = sqltm.get(db=db, selector=selector, columns='id,program,'+args.cols+','+keys)
rows = [ dict(row) for row in rows ]

nr = len(rows)
if nr == 0:
    print("No rows selected. SQL selector was:")
    print(selector)
    raise SystemExit

# determine max no of parallel parser processes
if nr < 8:
    nproc = nr
else:
    nproc = 8

# parse
with multiprocessing.Pool(processes=nproc, maxtasksperchild=1) as pool:
    data = pool.map(parse, [ r for r in rows])

# copy rows to data dict
for i in range(len(data)):
    for k in keys.split(','):
        data[i][k] = rows[i][k]

# dump as pickle files
with open('data.pkl', 'wb') as fd:
    pickle.dump(data, fd)
 
# print table with selected keys
print('='*len(print_keys)*14)
for t in print_keys: 
    print(' {t:>12s} '.format(t=t),end="")
print()
print('-'*len(print_keys)*14)
for d in data:
    if hasattr(d[t], '__iter__'):
        v = " ".join(map(str,d[t]))
        print('  {v:>s}'.format(v=v), end="")
    try:
        for t in print_keys:
            if isinstance(d[t], int):
                print('  {v:>12d}'.format(v=d[t]), end="")
            elif isinstance(d[t], float):
                print('  {v:>12.6f}'.format(v=d[t]), end="")
            elif isinstance(d[t], str):
                print('  {v:>12s}'.format(v=d[t]), end="")
    except:
        print('    Data of {id} incomplete (check output files).'.format(id=d['id']), end="")
    print()
print('='*len(print_keys)*14)

print("Available keys: ")
print(data[-1].keys())


