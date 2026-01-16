from __future__ import print_function
import sys, os
import re, string
import ase.io
import scipy as sp

import sqltm
import asex

def add_supercell_tasks(db, tasks, unitcell, input_template, columns, test=True):
    if not test:
        sqltm.init_db(db, columns)
    if not os.path.exists("images"):
        os.mkdir("images")
    if not os.path.exists("geometries"):
        os.mkdir("geometries")
    if not os.path.exists("input"):
        os.mkdir("input")
    re_kgrid = re.compile(r"""^.*k_grid.*$""", re.MULTILINE)
    i = 0
    for t in tasks:
        i += 1
        print("+++ Slab {i:>6d}: {s:<40s}".format(i=i,s=t['description']))
        # create supercell and compute new tags
        cell_tags = unitcell.get_tags()
        max_tag = max(cell_tags) # = no. of atoms in bulk unit cell - 1
        slab = unitcell*t['supercell']
        slab_tags = []
        for k,l in sp.ndindex(t['supercell'][0], t['supercell'][1]):
            slab_tags += [ tag+k*max_tag+l*t['supercell'][1]*max_tag for tag in cell_tags ]
        slab.set_tags(slab_tags)
        if 'kgrid' in t:
            kgrid = t['kgrid']
        else:
            kgrid = asex.kpoint_grid(slab, dx=0.02)
            t['kgrid'] = kgrid
        if 'rm_atoms' in t:
            for a in t['rm_atoms']:
                slab = asex.rm_atoms(slab, **a)
        if 'constraints' in t:
            if t['constraints'] != None:
                fixed = asex.fix_atoms(slab, [ x + t['termination'] for x in t['constraints']])
        if 'vacuum' in t:
            slab.center(vacuum=t['vacuum'], axis=2)
            kgrid[2] = 1
        if 'set_volume' in t:
            asex.set_volume(slab,t['set_volume'], minvac=10.0)
            kgrid[2] = 1
        if 'add_species' in t:
            for a in t['add_species']:
                slab = asex.add_species(slab, **a)
        if 'sort' not in t or t['sort']:
            order = abs(slab.positions[:,2]).argsort()[::-1]
            slab = slab[order]

        with open(input_template[0], 'r') as fd:
            input1 = string.Template(fd.read())
            t['input1'] = input1.substitute({ 'k_grid': 'k_grid ' + " ".join(str(i) for i in kgrid) })
        slab.write(filename=input_template[1], format="aims")
        with open(input_template[1], 'r') as fd:
            t['input2'] = fd.read()
        asex.print_stats(slab)
        # add to database
        if test:
            with open('input/'+t['description']+'.in', 'w') as fd:
                fd.write(t['input1'])
            asex.write_aims('geometries/'+t['description']+'.in', 
                    sym=slab.get_chemical_symbols(),
                    cell=slab.cell, xyz=slab.positions,
                    con=slab._constraints[0].index, 
                    mom=slab.get_initial_magnetic_moments(),
                    lab=slab.get_tags())
        else:
            sqltm.add(db, t, columns)
    return



# tasks, unitcell, input_template
def add_tasks(db, tasks, unitcell, input_template, columns, test=True):
    fd_info=sys.stdout

#    # lock sqlite3 database
#    sqltm_lock = os.path.dirname(__file__) + '/../lib/lock'
#    lockfile = db + ".lock"
#    lock_cmd = sqltm_lock + " " + lockfile
#    if not os.path.isfile(db):
#        sqltm.init_db(db, columns)
#    else:
#        if not os.path.isfile(sqltm_lock):
#            print("ERROR: {s} not found".format(s=sqltm_lock)) 
#            raise SystemExit
#        else:
#            os.system(lock_cmd)

    if not test:
        sqltm.init_db(db, columns)
    if not os.path.exists("images"):
        os.mkdir("images")
    if not os.path.exists("geometries"):
        os.mkdir("geometries")
    if not os.path.exists("input"):
        os.mkdir("input")

    re_kgrid = re.compile(r"""^.*k_grid.*$""", re.MULTILINE)
    i = 0
    for t in tasks:
        # create slab
        i += 1
        print("+++ Slab {i:>6d}: {s:<40s}".format(i=i,s=t['description']))
        cell = asex.create_cell(unitcell, t['orientation'], nmax=-3, fd_info=fd_info)
        slab = asex.create_slab(cell, dimension=t['supercell'], rmlayers=t['rmlayers'], termination=t['termination'], fd_info=fd_info)
        if 'kgrid' in t:
            kgrid = t['kgrid']
        else:
            kgrid = asex.kpoint_grid(slab, dx=0.02)
            t['kgrid'] = kgrid
        if 'rm_atoms' in t:
            for a in t['rm_atoms']:
                slab = asex.rm_atoms(slab, **a)
        if 'constraints' in t:
            if t['constraints'] != None:
                fixed = asex.fix_atoms(slab, [ x + t['termination'] for x in t['constraints']])
        if 'vacuum' in t:
            slab.center(vacuum=t['vacuum'], axis=2)
            kgrid[2] = 1
        if 'set_volume' in t:
            asex.set_volume(slab,t['set_volume'], minvac=10.0)
            kgrid[2] = 1
        if 'add_species' in t:
            for a in t['add_species']:
                slab = asex.add_species(slab, **a)
        if 'sort' not in t or t['sort']:
            # by default sort atoms by layers
            order = abs(slab.positions[:,2]).argsort()[::-1]
            slab = slab[order]
        # create input files
        with open(input_template[0], 'r') as fd:
            #k_str = 'k_grid {0:>4d} {1:>4d} {2:>4d}'.format(*kgrid)
            #input1 = re.sub(re_kgrid, k_str, fd.read())
            input1 = string.Template(fd.read())
            t['input1'] = input1.substitute({ 'k_grid': 'k_grid ' + " ".join(str(i) for i in kgrid) })
        # write and read slab geometry
        slab.write(filename=input_template[1], format="aims")
        with open(input_template[1], 'r') as fd:
            t['input2'] = fd.read()
        # configure task
        asex.print_stats(slab)
        # add to database
        if test:
            #ase.io.write('images/'+t['description']+'.png', slab * (3, 3, 1), rotation='20z,-70x')
            #ase.io.write('geometries/'+t['description']+'.in', slab * (1, 1, 1), format="aims")
            with open('input/'+t['description']+'.in', 'w') as fd:
                fd.write(t['input1'])
            #tag = slab.get_tags()
            #sym = slab.get_chemical_symbols()
            #for i in range(len(slab)):
            #    print(i, sym[i], tag[i])
            #    slab[i].symbol= sym[i] + str(tag[i])
            #with open('geometries/'+t['description']+'.in', 'w') as fd:
            #    fd.write(t['input2'])
            if t['constraints'] != None:
                asex.write_aims('geometries/'+t['description']+'.in', 
                    sym=slab.get_chemical_symbols(),
                    cell=slab.cell, xyz=slab.positions,
                    con=slab._constraints[0].index, 
                    mom=slab.get_initial_magnetic_moments(),
                    lab=slab.get_tags())
            else:
                asex.write_aims('geometries/'+t['description']+'.in', 
                    sym=slab.get_chemical_symbols(),
                    cell=slab.cell, xyz=slab.positions,
                    con=None, 
                    mom=slab.get_initial_magnetic_moments(),
                    lab=slab.get_tags())

        else:
            sqltm.add(db, t, columns)
#    # remove lockfile (if it exists)
#    if os.path.isfile(lockfile):
#        os.remove(lockfile)
    return

# tasks, unitcell, input_template
def add_tasks_cp2k(db, tasks, unitcell, input_template, columns, test=True):
    #sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'parser'))
    sys.path.append(os.environ['HOME'] + '/src/parser/parser')
    import string
    import cp2k
    fd_info=sys.stdout
    if not test:
        sqltm.init_db(db, columns)
    if not os.path.exists("images"):
        os.mkdir("images")
    if not os.path.exists("geometries"):
        os.mkdir("geometries")
    if not os.path.exists("input"):
        os.mkdir("input")
    i = 0
    for t in tasks:
        # create slab
        i += 1
        print("+++ Slab {i:>6d}: {s:<40s}".format(i=i,s=t['description']))
        cell = asex.create_cell(unitcell, t['orientation'], nmax=-3, fd_info=fd_info)
        slab = asex.create_slab(cell, dimension=t['supercell'], rmlayers=t['rmlayers'], termination=t['termination'], fd_info=fd_info)
        kgrid = asex.kpoint_grid(slab, dx=0.02)
        if 'constraints' in t:
            if t['constraints'] != None:
                asex.fix_atoms(slab, [ x + t['termination'] for x in t['constraints']])
        if 'vacuum' in t:
            slab.center(vacuum=t['vacuum'], axis=2)
            kgrid[2] = 1
        if 'set_volume' in t:
            asex.set_volume(slab,t['set_volume'], minvac=10.0)
            kgrid[2] = 1
        if 'rm_atoms' in t:
            for a in t['rm_atoms']:
                slab = asex.rm_atoms(slab, **a)
        if 'add_species' in t:
            for a in t['add_species']:
                slab = asex.add_species(slab, **a)
        # write slab geometry
        sys_str = cp2k.print_cp2k(slab.get_chemical_symbols(), slab.get_positions(), None, slab.get_cell())
        constraints = ' '.join([ str(c) for c in slab.constraints[0].get_indices() ])
        # create input files
        with open(input_template[0], 'r') as fd:
            input1 = string.Template(fd.read())
        input1 = input1.safe_substitute({'system': sys_str, 'constraint': constraints})
        # configure task
        t['input1'] = input1
        t['kgrid'] = kgrid
        asex.print_stats(slab)
        # add to database
        if test:
            ase.io.write('images/'+t['description']+'.png', slab * (3, 3, 1), rotation='20z,-70x')
            ase.io.write('geometries/'+t['description']+'.in', slab * (5, 5, 1), format="aims")
            with open('input/'+t['description']+'.in', 'w') as fd:
                fd.write(input1)
        else:
            sqltm.add(db, t, columns)
    return

# map notation
def map_v1_v1a(s):
    d = {           '0-0-1_t0': '0-0-1_0',
            '0-0-1_t0_1xH-O-b': '0-0-1_0_1xH-O-b',
            '0-0-1_t0_2xH-O-b': '0-0-1_0_2xH-O-b',
                '0-0-1_t0_1xO': '0-0-1_0_1xO',
               '0-0-1_t0_1xOH': '0-0-1_0_1xOH',
              '0-0-1_t0_1xH2O': '0-0-1_0_1xH2O',
                '0-0-1_t0_2xO': '0-0-1_0_2xO',
           '0-0-1_t0_1xOH_1xO': '0-0-1_0_1xOH_1xO',
               '0-0-1_t0_2xOH': '0-0-1_0_2xOH',
                    '0-1-0_t0': '0-1-0_0',
                    '0-1-0_t1': '0-1-0_1',
            '0-1-0_t1_1xH-O-b': '0-1-0_1_1xH-O-b',
                    '0-1-0_t2': '0-1-0_2',
            '0-1-0_t2_1xH-O-t': '0-1-0_2_1xH-O-t',
           '0-1-0_t2_1xH2-O-t': '0-1-0_2_1xH2-O-t',
                    '0-1-1_t0': '0-1-1_0',
             '0-1-1_t1_1xO-45': '0-1-1_1_1xO-45',
            '0-1-1_t1_1xOH-45': '0-1-1_1_1xOH-45',
                    '0-1-1_t1': '0-1-1_1',
            '0-1-1_t1_1xH-O-b': '0-1-1_1_1xH-O-b',
            '0-1-1_t1_2xH-O-b': '0-1-1_1_2xH-O-b',
                '0-1-1_t1_1xO': '0-1-1_1_1xO',
               '0-1-1_t1_1xOH': '0-1-1_1_1xOH',
              '0-1-1_t1_1xH2O': '0-1-1_1_1xH2O',
              '0-1-1_t1_2xH2O': '0-1-1_1_2xH2O',
                    '0-1-1_t2': '0-1-1_2',
            '0-1-1_t2_1xH-O-t': '0-1-1_2_1xH-O-t',
            '0-1-1_t2_2xH-O-t': '0-1-1_2_2xH-O-t',
                    '1-1-0_t0': '1-1-0_0',
              '1-1-0_t0_1xO-0': '1-1-0_0_1xO-0',
              '1-1-0_t0_1xO-1': '1-1-0_0_1xO-1',
             '1-1-0_t0_1xOH-0': '1-1-0_0_1xOH-0',
             '1-1-0_t0_1xOH-1': '1-1-0_0_1xOH-1',
               '1-1-0_t0_2xOH': '1-1-0_0_2xOH',
                    '1-1-0_t1': '1-1-0_1',
            '1-1-0_t1_1xH-O-b': '1-1-0_1_1xH-O-b',
                    '1-1-0_t2': '1-1-0_2',
            '1-1-0_t2_1xH-O-t': '1-1-0_2_1xH-O-t',
           '1-1-0_t2_1xH2-O-t': '1-1-0_2_1xH2-O-t',
           '1-1-0_t2_2xH-O-tb': '1-1-0_2_2xH-O-tb',
   '1-1-0_t2_1xH2-O-t_1xH-O-b': '1-1-0_2_1xH2-O-t_1xH-O-b',
                    '1-1-1_t0': '1-1-1_0',
             '1-1-1_t0_1xOH-t': '1-1-1_0_1xOH-t',
            '1-1-1_t0_1xH2O-t': '1-1-1_0_1xH2O-t',
                    '1-1-1_t2': '1-1-1_2',
                '1-1-1_t2_1xO': '1-1-1_2_1xO',
               '1-1-1_t2_1xOH': '1-1-1_2_1xOH',
              '1-1-1_t2_1xH2O': '1-1-1_2_1xH2O',
                    '1-1-1_t3': '1-1-1_3',
                   '1-1-1_t1a': '1-1-1_3_1xO',
           '1-1-1_t1a_1xH-O-t': '1-1-1_3_1xOH',
          '1-1-1_t1a_1xH2-O-t': '1-1-1_3_1xH2O'}
    if s not in d.keys():
        return s
    else:
        return d[s]

# yet another attempt to design a simple and informative notation
# <h>-<k>-<l>_<t>_<i>-<adsorbate1>_...
# hkl: Miller indices
# t: termination layer
# i: index of surface atom with adsorbate w.r.t. unit cell
# -X means the respective atom was removed
def map_v1_v2(s):
    d = {           '0-0-1_t0': '0-0-1_0',
            '0-0-1_t0_1xH-O-b': '0-0-1_0_2-H',
            '0-0-1_t0_2xH-O-b': '0-0-1_0_2-H_2-H',
                '0-0-1_t0_1xO': '0-0-1_0_0-O',
               '0-0-1_t0_1xOH': '0-0-1_0_0-OH',
              '0-0-1_t0_1xH2O': '0-0-1_0_0-H2O',
                '0-0-1_t0_2xO': '0-0-1_0_0-O-O',
           '0-0-1_t0_1xOH_1xO': '0-0-1_0_0-OH-O',
               '0-0-1_t0_2xOH': '0-0-1_0_0-OH-OH',
                    '0-1-0_t0': '0-1-0_0',
                    '0-1-0_t1': '0-1-0_1',
            '0-1-0_t1_1xH-O-b': '0-1-0_1_4-H',
                    '0-1-0_t2': '0-1-0_2',
            '0-1-0_t2_1xH-O-t': '0-1-0_2_3-H',
           '0-1-0_t2_1xH2-O-t': '0-1-0_1_0-H2O',
                    '0-1-1_t0': '0-1-1_0',
             '0-1-1_t1_1xO-45': '0-1-1_1_4-X',
            '0-1-1_t1_1xOH-45': '0-1-1_1_4-X_2-H',
                    '0-1-1_t1': '0-1-1_1',
            '0-1-1_t1_1xH-O-b': '0-1-1_1_2-H',
            '0-1-1_t1_2xH-O-b': '0-1-1_1_2-H_4-H',
                '0-1-1_t1_1xO': '0-1-1_1_1-O',
               '0-1-1_t1_1xOH': '0-1-1_1_1-OH',
              '0-1-1_t1_1xH2O': '0-1-1_1_1-H2O',
              '0-1-1_t1_2xH2O': '0-1-1_1_0-H2O_1-H2O',
                    '0-1-1_t2': '0-1-1_2',
            '0-1-1_t2_1xH-O-t': '0-1-1_2_3-H',
            '0-1-1_t2_2xH-O-t': '0-1-1_2_3-H_5-H',
                    '1-1-0_t0': '1-1-0_0',
              '1-1-0_t0_1xO-0': '1-1-0_0_0-O',
              '1-1-0_t0_1xO-1': '1-1-0_0_1-O',
             '1-1-0_t0_1xOH-0': '1-1-0_0_0-OH',
             '1-1-0_t0_1xOH-1': '1-1-0_0_1-OH',
               '1-1-0_t0_2xOH': '1-1-0_0_0-OH_1-OH',
                    '1-1-0_t1': '1-1-0_1',
            '1-1-0_t1_1xH-O-b': '1-1-0_1_3-H',
                    '1-1-0_t2': '1-1-0_2',
            '1-1-0_t2_1xH-O-t': '1-1-0_2_2-H',
           '1-1-0_t2_1xH2-O-t': '1-1-0_2_2-H-H',
           '1-1-0_t2_2xH-O-tb': '1-1-0_2_2-H_3-H',
   '1-1-0_t2_1xH2-O-t_1xH-O-b': '1-1-0_2_2-H-2_3-H',
                    '1-1-1_t0': '1-1-1_0',
             '1-1-1_t0_1xOH-t': '1-1-1_0_0-OH',
            '1-1-1_t0_1xH2O-t': '1-1-1_0_0-H2O',
                    '1-1-1_t2': '1-1-1_2',
                '1-1-1_t2_1xO': '1-1-1_2_1-O',
               '1-1-1_t2_1xOH': '1-1-1_2_1-OH',
              '1-1-1_t2_1xH2O': '1-1-1_2_1-H2O',
                    '1-1-1_t3': '1-1-1_3',
                   '1-1-1_t1a': '1-1-1_3_1-O',
           '1-1-1_t1a_1xH-O-t': '1-1-1_3_1-OH',
          '1-1-1_t1a_1xH2-O-t': '1-1-1_3_1-H2O' }
    if s not in d.keys():
        return s
    else:
        return d[s]
