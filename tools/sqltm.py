import scipy as sp
import mysql.connector
from os.path import expanduser, isfile

def init_db(db, columns):
    if db == None:
        conn = mysql.connector.connect(option_files=expanduser("~")+"/.my.cnf")
    else:
        conn = mysql.connector.connect(database=db, option_files=expanduser("~")+"/.my.cnf")

    c = conn.cursor()
    for col in columns:
        sql = "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS {col} TEXT;".format(col=col)
        c.execute(sql)
    conn.commit()
    c.close()
    conn.close()
    return
 
def add(db, task, columns):
    if db == None:
        conn = mysql.connector.connect(option_files=expanduser("~")+"/.my.cnf")
    else:
        conn = mysql.connector.connect(database=db, option_files=expanduser("~")+"/.my.cnf")

    t = { k: task.get(k, None) for k in columns }
    for c in columns:
        if isinstance(t[c], (list, tuple, sp.ndarray)):
            t[c] = tostr(t[c])
    c = conn.cursor()
    sql = "SET FOREIGN_KEY_CHECKS=0; "
    c.execute(sql)
    sql = """INSERT INTO tasks ("""
    sql += ','.join(t.keys()) 
    sql += """) VALUES (%("""
    sql += ')s,%('.join(t.keys())
    sql += """)s); """
    c.execute(sql, t)
    conn.commit()
    c.close()
    conn.close()
    return

def set(db, id, col, val):
    conn = mysql.connector.connect(database=db, option_files=expanduser("~")+"/.my.cnf")
    c = conn.cursor()
    sql = """UPDATE tasks set {col} = %s """.format(col=col)
    sql += """WHERE id = %s;"""
    if isinstance(id, (list, tuple, sp.ndarray)):
        for i,v in zip(id, val):
            c.execute(sql, (i,v))
    else:
        c.execute(sql, (val,id))
    conn.commit()
    c.close()
    conn.close()
    return


def get(db=None, selector=None, columns="*"):
    if db is None:
        return get_mysql(db, selector, columns)
    if isfile(db):
        return get_sqlite3(db, selector, columns)
    else:
        return get_mysql(db, selector, columns)

def get_last(db, selector, columns="*"):
    if db == None:
        conn = mysql.connector.connect(option_files=expanduser("~")+"/.my.cnf")
    else:
        conn = mysql.connector.connect(database=db, option_files=expanduser("~")+"/.my.cnf")
    c = conn.cursor(dictionary=True)
    sql = """SELECT """ + columns + """ FROM tasks """
    sql += """JOIN (SELECT max(id) as id FROM tasks GROUP BY description) """
    sql += """x on x.id = tasks.id """
    if selector is not None:
        sql += """ WHERE """ + selector + ";"
    c.execute(sql)
    rows = c.fetchall()
    c.close()
    conn.close()
    return rows

def get_mysql(db, selector, columns="*"):
    if db == None:
        conn = mysql.connector.connect(option_files=expanduser("~")+"/.my.cnf")
    else:
        conn = mysql.connector.connect(database=db, option_files=expanduser("~")+"/.my.cnf")
    c = conn.cursor(dictionary=True)
    sql = """SELECT """ + columns + """ FROM tasks"""
    #sql_default = """status = 3"""
    #sql = """SELECT """ + columns + """ FROM tasks WHERE """ + sql_default
    #if selector is not None:
    #    sql += """ AND """ + selector
    if selector is not None:
        sql += """ WHERE """ + selector
    sql += """ ORDER BY id ASC;"""
    c.execute(sql)
    rows = c.fetchall()
    c.close()
    conn.close()
    return rows

def get_sqlite3(db, selector, columns="*"):
    import sqlite3
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    #sql_default = """status = 3"""
    #sql = """SELECT """ + columns + """ FROM tasks WHERE """ + sql_default + """ AND """ + selector
    sql = """SELECT """ + columns + """ FROM tasks WHERE """ + selector
    sql += """ ORDER BY id ASC;"""
    c.execute(sql)
    rows = c.fetchall()
    c.close()
    conn.close()
    return rows

def tostr(a):
    return ','.join(map(str, a))

def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

if __name__ == '__main__':
    cols = [ "input1", "input2", "output1", "output2" ]
    init_db(None, cols)
    task = { 'input1': 'this is an input file', 'input2': 'more input' }
    add(None, task, [ "input1", "input2" ])
