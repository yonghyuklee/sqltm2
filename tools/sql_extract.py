#!/usr/bin/python

from __future__ import print_function
import sys, os
sys.path.append(os.path.dirname(__file__))
import sqltm

# ~/src/sqltm/tools/sql_extract.py opalka input2 "id > 81556 and id < 82502" name

narg = len(sys.argv)
fn_key = 'id'
if narg == 1:
    print("Usage: extract.py <db> [<col>] [<selector>] [<fn_key>]")
    print("defaults: col=output1, selector='status = 4'")
    raise SystemExit
elif narg == 2:
    db = sys.argv[1]
    col = """output1"""
    selector = None
elif narg == 3:
    db = sys.argv[1]
    col = sys.argv[2]
    selector = """status = 4"""
elif narg == 4:
    db = sys.argv[1]
    col = sys.argv[2]
    selector = sys.argv[3]
else:
    db = sys.argv[1]
    col = sys.argv[2]
    selector = sys.argv[3]
    fn_key = sys.argv[4]

if ',' in col:
    print("Only one column at time can be extracted")
    raise SystemExit

data = sqltm.get(db=db, selector=selector, columns='id,'+col+','+fn_key)
print(len(data))

print("Extracting {col} from {db}".format(col=col, db=db))
for datum in data:
    if datum[col] == None:
        continue
    #fn = str(datum['id']) + "_" + col
    fn = str(datum[fn_key])
    print("{fn}".format(fn=fn))
    with open(fn, 'w') as fd:
        fd.write(datum[col])
