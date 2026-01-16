#!/usr/bin/python

from __future__ import print_function
import sys, os
sys.path.append(os.path.dirname(__file__))
import sqltm

narg = len(sys.argv)
if narg == 1:
    print("Usage: extract.py <db> <col> [<selector>]")
    print("Display table of selected columns: extract.py <db>")
    raise SystemExit
elif narg == 2:
    db = sys.argv[1]
    col = """id,status,name,description"""
    selector = None
elif narg == 3:
    db = sys.argv[1]
    col = sys.argv[2]
    selector = None
else:
    db = sys.argv[1]
    col = sys.argv[2]
    selector = sys.argv[3]

data = sqltm.get(db=db, selector=selector, columns=col)

# process data/write to files
keys = data[0].keys()
for key in keys:
    if key == 'description':
        print("{0:^40s}".format(key), end="")
    else:
        print("{0:^12s}".format(key), end="")
print()
# print values
for datum in data:
    for key in keys:
        if key == 'description':
            print("{0:^40s}".format(str(datum[key])), end="")
        else:
            print("{0:^12s}".format(str(datum[key])), end="")
    print()
print()
