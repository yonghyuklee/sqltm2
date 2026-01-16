#!/usr/bin/python

from __future__ import print_function
import sys, os
import sqlite3
import string, re

# the script assumes that the basic table schema already exits (initialized automatically if table does not exist)
# The following tables/columns are not copied:
# TABLES:  jobs, hosts
# COLUMNS: id, jobid in table "tasks"
exclude = [ 'id', 'jobid' ]

if len(sys.argv) < 2:
    print("Usage: extract.py <db1> [<db2> ... <dbN>] <db out>")
    raise SystemExit

# map python data types to sqlite3 data types
def sql_type(x):
    t = type(x)
    if x is None:
        return 'NULL'
    elif t is int or t is long:
        return 'INTEGER'
    elif t is str or t is unicode: 
        return 'TEXT'
    elif t is buffer:
        return 'BLOB'

# return all columns of a table as a dict, where dict keys correspond to column
# names and the corresponding values the column definition (meta data)
# columns in 'exclude' list are removed
def get_columns(fn, tn):
    sql = """SELECT * FROM 'sqlite_master' WHERE type='table' AND name='{tn:s}';""".format(tn=tn)
    conn = sqlite3.connect(fn)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(sql)
    meta_data = c.fetchone()
    #sql = """SELECT * FROM {tn:s} LIMIT 1;""".format(tn=tn)
    #c.execute(sql)
    #data = c.fetchone()
    conn.close()
    columns = {}
    # remove "CREATE TABLE ("
    s = meta_data['sql']
    i = string.find(s, '(')
    s = s[i+1:-1]
    s = s.split(',') 
    # parse meta data and column names
    foreign_key = re.compile("""FOREIGN KEY""")
    for c in s:
        if foreign_key.match(c):
            name = c[c.index('(')+1:c.index(')')]
            columns[name] += ',' + c
        else:
            name, meta = c.strip().split(" ", 1) # split column name and metadata
            name = name.replace("""'""", "")
            columns[name] = meta
    for k in exclude:
        del columns[k]
    return columns

# add new columns to a table
def add_columns(fn, tn, keys):
    sql = """ALTER TABLE '{tn}' ADD COLUMN """.format(tn=tn)
    conn = sqlite3.connect(fn)
    c = conn.cursor()
    for k, v in keys.items():
        c.execute(sql + str(k) + " " + str(v))
    conn.commit()
    conn.close()
    return

# initialize database schema with basic columns and tables
# these columns should not be copied since this is db-specific (jobid, unique keys etc.)
def init_db(fn):
    conn = sqlite3.connect(fn)
    c = conn.cursor()
    sql = "CREATE TABLE IF NOT EXISTS tasks ("
    sql += "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    sql += "jobid INTEGER DEFAULT 0,"
    sql += "FOREIGN KEY(jobid) REFERENCES jobs(id))"
    c.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS jobs ("
    sql += "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    sql += "jobname TEXT,"
    sql += "dispatch_time INTEGER,"
    sql += "time_limit INTEGER,"
    sql += "tot_cores INTEGER,"
    sql += "scratch TEXT)"
    c.execute(sql)
    sql = "CREATE TABLE IF NOT EXISTS hosts ("
    sql += "id INTEGER PRIMARY KEY AUTOINCREMENT,"
    sql += "name TEXT,"
    sql += "jobid INTEGER DEFAULT 0,"
    sql += "taskid INTEGER,"
    sql += "status INTEGER,"
    sql += "FOREIGN KEY(jobid) REFERENCES jobs(id),"
    sql += "FOREIGN KEY(taskid) REFERENCES tasks(id))"
    c.execute(sql)
    conn.commit()
    conn.close()
    return
  
# initialize/open target db
tn = 'tasks'
tn_out = 'tasks'
fn_out = sys.argv[-1]

#if table_exists(db_out, tn='tasks'):
#try:
#   columns = get_columns(fn_out, tn_out)
#except:
#    columns = {}
#    print("""No table {tn_out:s} found in {fn_out:s}.""".format(tn_out=tn_out, fn_out=fn_out))
init_db(fn_out)
 
for fn in sys.argv[1:-1]:
    columns = get_columns(fn_out, tn_out)
    #col = get_columns(fn, tn)
    try:
        col = get_columns(fn, tn)
    except:
        print("""No table {tn:s} found in {fn:s}. No data copied.""".format(tn=tn, fn=fn))
        continue

    print("""Copying {tn:s} in {fn:s} to {tn_out:s} in {fn_out:s}."""\
        .format(tn=tn, fn=fn, tn_out=tn_out, fn_out=fn_out))

    # check for new columns
    new_columns = {}
    dk = [ x for x in col if x not in columns ]

    if dk != []:
        print("""Found {nk:d} new keys: """.format(nk=len(dk)))
        for x in dk:
            print("""{k:s}""".format(k=x), end=" ")
        print("""Add new columns to table {tn:s} in {fn:s} ((y)es/(a)ll/(n)one)/(d)one?"""\
            .format(tn=tn_out, fn=fn_out))
        for x in dk:
            print("""{k:s} """.format(k=x), end="")
            choice = raw_input().lower() 
            if choice == 'y':
                new_columns[x] = col[x]
            elif choice == 'd':
                break
            elif choice == 'a':
                print("""Adding all missing keys""")
                for y in dk:
                    print("""{k:s} """.format(k=y))
                    new_columns[y] = col[y]
                break

    # add selected new columns
    if new_columns != []:
        add_columns(fn_out, tn_out, new_columns)

    # columns to be copied
    keys = columns.keys() + new_columns.keys()
    key_str = ','.join(keys)

    # setup DB connections
    conn_out = sqlite3.connect(fn_out)
    c_out = conn_out.cursor()
    conn_in = sqlite3.connect(fn)
    c_in = conn_in.cursor()

    # fetch data
    sql = """SELECT """  + key_str + """ FROM  '{tn}'""".format(tn=tn)
    c_in.execute(sql)
    rows = c_in.fetchall()

    # insert data
    sql = """INSERT INTO '{tn}' (""".format(tn=tn_out)
    sql += key_str + """) VALUES (:"""
    sql += ',:'.join(keys)
    sql += """)"""
    c_out.executemany(sql, rows)

    # close DBs
    conn_out.commit()
    conn_out.close()
    conn_in.close()

raise SystemExit
