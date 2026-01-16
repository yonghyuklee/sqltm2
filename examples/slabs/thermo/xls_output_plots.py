import os
import re
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import openpyxl

# font setting
mpl.rcParams.update({'text.latex.preamble': [
    r'\usepackage[version=3]{mhchem}',
    r'\usepackage[T1]{fontenc}',
    r'\usepackage[tx]{sfmath}',
    r'\usepackage{helvet}'
] })
mpl.rcParams.update({'text.latex.unicode': True, 'text.usetex': True})
mpl.rcParams.update({'font.size': 30, 'font.family': 'sans-serif', 'font.sans-serif': 'Helvetica' })

mpl.rcParams.update({'legend.numpoints': 1, 'axes.linewidth': 3})
mpl.rcParams['ytick.major.size'] = 8
mpl.rcParams['ytick.major.width'] = 3
mpl.rcParams['ytick.minor.size'] = 4
mpl.rcParams['ytick.minor.width'] = 1.5
mpl.rcParams['xtick.major.size'] = 8
mpl.rcParams['xtick.major.width'] = 3
mpl.rcParams['xtick.minor.size'] = 4
mpl.rcParams['xtick.minor.width'] = 1.5

tum_pantone301 = '#0065BD'
tum_black = 'black'
tum_orange = '#E37222'
tum_green = '#A2AD00'
tum_light_grey = '#808080'


def sort_terminations(data):
    data_sorted = {}
    k_sorted = {}
    w_001 = []; k_001 = [];
    w_010 = []; k_010 = [];
    w_011 = []; k_011 = [];
    w_110 = []; k_110 = [];
    w_111 = []; k_111 = [];
    for k,v in data.items():
        if re.match("^0-0-1", k):
            w_001.append(v); k_001.append(k)
        elif re.match("^0-1-0", k):
            w_010.append(v); k_010.append(k)
        elif re.match("^0-1-1", k):
            w_011.append(v); k_011.append(k)
        elif re.match("^1-1-0", k):
            w_110.append(v); k_110.append(k)
        elif re.match("^1-1-1", k):
            w_111.append(v); k_111.append(k)
    data_sorted['001'] = sp.sort(w_001,axis=0)[0,:]
    k_sorted['001'] = [ k_001[i] for i in sp.argmin(w_001,axis=0) ]
    data_sorted['010'] = sp.sort(w_010,axis=0)[0,:]
    k_sorted['010'] = [ k_010[i] for i in sp.argmin(w_010,axis=0) ]
    data_sorted['011'] = sp.sort(w_011,axis=0)[0,:]
    k_sorted['011'] = [ k_011[i] for i in sp.argmin(w_011,axis=0) ]
    data_sorted['110'] = sp.sort(w_110,axis=0)[0,:]
    k_sorted['110'] = [ k_110[i] for i in sp.argmin(w_110,axis=0) ]
    data_sorted['111'] = sp.sort(w_111,axis=0)[0,:]
    k_sorted['111'] = [ k_111[i] for i in sp.argmin(w_111,axis=0) ]
    return k_sorted, data_sorted

def plot_facets(data_xls, s, x='U'):
    # select columns by facet
    k_001 = [ c for c in data_xls[s].keys() if re.match("^0-0-1", c)]
    k_010 = [ c for c in data_xls[s].keys() if re.match("^0-1-0", c)]
    k_011 = [ c for c in data_xls[s].keys() if re.match("^0-1-1", c)]
    k_110 = [ c for c in data_xls[s].keys() if re.match("^1-1-0", c)]
    k_111 = [ c for c in data_xls[s].keys() if re.match("^1-1-1", c)]
    keys = { '001': k_001, '010': k_010, '011': k_011, '110': k_110, '111': k_111 }
    
    # plot  U vs surface free energy
    if x == 'U':
        for k,v in keys.items():
            plot_u_vs_gamma(data_xls[s], k, v, k, legend=True)
    elif x == 'T':
        for k,v in keys.items():
            plot_T_vs_gamma(data_xls[s], k, v, k, legend=True)
    return

def plot_min(data_xls, s, emin, suffix="", x='U'):
    # all surfaces that are lowest at some point
    w = set()
    for d in emin: 
        for k in d.keys():
            w.add(d[k]['description'])
    if x == 'U':
        plot_u_vs_gamma(data_xls[s], 'min'+suffix, list(w), legend=True)
    elif x == 'T':
        plot_T_vs_gamma(data_xls[s], 'min'+suffix, list(w), legend=True)
    return


# dict of lists: data[sheet_key][column_key][row_index]
def create_xls(fn, data, columns):
    """ Create new XLS workbook with multiple sheets.
    Data must be a dictionary commensurate with the different sheets """
    if not data:
        print("WARNING (create_xls): can not create XLS file - no data")
        return
    if not columns: 
        print("WARNING (create_xls): no columns defined")
        return
    sheets = data.keys()
    wb = openpyxl.Workbook(optimized_write=True)
    for sheet in sheets: 
        ws = wb.create_sheet(sheet)
        #columns = list(data[sheet].keys())
        ws.append(columns)
        nr = len(data[sheet][columns[0]])
        for r in range(nr): 
            ws.append([data[sheet][c][r] for c in columns])
        # add column names as comment if provided (does not work for
        # OpenOffice)
        #if column_names != None:
        #    row = next(d)
        #    row_comment = []
        #    for i in range(len(row)): 
        #        #cell = openpyxl.writer.write_only.WriteOnlyCell(ws, value=row[i])
        #        cell = openpyxl.cell.Cell(ws, row=1, col_idx=i+1, value=row[i])
        #        comment = openpyxl.comments.Comment(column_names[sheet][i], 'DOXXXXXX')
        #        cell.comment = comment
        #        row_comment.append(cell)
        #    ws.append(row_comment)
        # append remaining rows
    wb.save(fn)
    return


def plot_pH_vs_gamma(data, fn, columns, facet=None, legend=False):
    from itertools import cycle
    # plot data
    if len(columns) <= 4:
        lines = ["-"]
    else:
        lines = ["-","--","-.",":"]
    ls = cycle(lines)
    colors = [ tum_black, tum_green, tum_pantone301, tum_orange, tum_light_grey ]
    lc = cycle(colors)
    fig, ax1 = plt.subplots(1, sharex=True, sharey=True)
    if facet != None:
        ax1.set_ylabel("["+facet+"] " + r'surface free energy / meV\,/\,$\AA^2$')
        plt.text(0.1, 0.85, r'['+facet+']', fontsize=40,transform=ax1.transAxes)
    else:
        ax1.set_ylabel(r'surface free energy / meV\,/\,$\AA^2$')
    ax1.set_xlabel(r'pH')
    for c in data.keys():
        if re.match("^"+columns[0][0:5], c): 
            ax1.plot(data['pH'], sp.array(data[c])*1000.0, color=tum_light_grey, linewidth=2.5, linestyle='solid')
    if legend:
        for c in columns:
            ax1.plot(data['pH'], sp.array(data[c])*1000.0, color=next(lc), linewidth=5.0, linestyle=next(ls), label='\\verb|'+c+'|')
            #labelLines(ax1.get_lines(),align=False,fontsize=24)
            ax1.legend(loc="upper left", bbox_transform=ax1.transAxes, bbox_to_anchor=(1,1), fontsize='xx-small')
    else:
        for c in columns:
            ax1.plot(data['pH'], sp.array(data[c])*1000.0, color=next(lc), linestyle=next(ls), linewidth=5.0)
    fig.subplots_adjust(hspace=0)
    fig.set_size_inches( (8, 8) )
    plt.ylim(-100, 175)
    plt.grid(False)
    fig.set_size_inches( (8, 8) )
    plt.savefig('./' + fn + '.png', bbox_inches='tight', pad_inches=0.0, transparent=True)
    return


def plot_u_vs_gamma(data, fn, columns, facet=None, legend=False):
    from itertools import cycle

    # plot data
    if len(columns) <= 5:
        lines = ["-"]
    else:
        lines = ["-","--","-.",":"]
    ls = cycle(lines)
    colors = [ tum_black, tum_green, tum_pantone301, tum_orange, 'red', tum_light_grey ]
    lc = cycle(colors)
    fig, ax1 = plt.subplots(1, sharex=True, sharey=True)
    if facet != None:
        ax1.set_ylabel("["+facet+"] " + r'$\gamma^{hkl}$ (meV\,/\,$\AA^2$)')
        plt.text(0.1, 0.85, r'['+facet+']', fontsize=40,transform=ax1.transAxes)
    else:
        ax1.set_ylabel(r'$\gamma^{hkl}$ (meV\,/\,$\AA^2$)')
    ax1.set_xlabel(r'$U$ vs. RHE (V)')
    #plt.text(0.75,-0.14,r'$\Delta G$(OER)',rotation=0,transform=ax1.transAxes)
    #ax1.axvline(x=1.23, linewidth=5.0, linestyle='dashed', color='black')
    rect = patches.Rectangle((1.23,-50),0.2,250,linewidth=None,edgecolor=None,facecolor='gainsboro')
    ax1.add_patch(rect)
    for c in data.keys():
        #if re.match("^"+columns[0][0:5], c): 
        if c not in columns and c != 'U': 
            ax1.plot(data['U'], sp.array(data[c])*1000.0, color=tum_light_grey, linewidth=2.5, linestyle='solid')
    if legend:
        for c in columns:
#            if re.match("^1-1-0", c):
#                print(c)
#                print(data[c])
            ax1.plot(data['U'], sp.array(data[c])*1000.0, color=next(lc), linewidth=5.0, linestyle=next(ls), label='\\verb|'+c+'|')
            #labelLines(ax1.get_lines(),align=False,fontsize=24)
            ax1.legend(loc="upper left", bbox_transform=ax1.transAxes, bbox_to_anchor=(1,1), fontsize='xx-small')
    else:
        for c in columns:
            ax1.plot(data['U'], sp.array(data[c])*1000.0, color=next(lc), linestyle=next(ls), linewidth=5.0)
    #ax1.set_xticks(sp.arange(0,2.1,0.1), minor=True)
    fig.subplots_adjust(hspace=0)
    fig.set_size_inches( (8, 8) )
    #plt.grid(False)
    plt.grid()
    #plt.ylim(-50, 500)
    plt.ylim(-200, 200)
    fig.set_size_inches( (8, 8) )
    plt.savefig('./' + fn + '.png', bbox_inches='tight', pad_inches=0.0, transparent=True)
    return

def plot_T_vs_gamma(data, fn, columns, facet=None, legend=False):
    from itertools import cycle
    # plot data
    if len(columns) <= 5:
        lines = ["-"]
    else:
        lines = ["-","--","-.",":"]
    ls = cycle(lines)
    colors = [ tum_black, tum_green, tum_pantone301, tum_orange, 'red', tum_light_grey ]
    lc = cycle(colors)
    fig, ax1 = plt.subplots(1, sharex=True, sharey=True)
    if facet != None:
        ax1.set_ylabel("["+facet+"] " + r'$\gamma^{hkl}$ (meV\,/\,$\AA^2$)')
        plt.text(0.1, 0.85, r'['+facet+']', fontsize=40,transform=ax1.transAxes)
    else:
        ax1.set_ylabel(r'$\gamma^{hkl}$ (meV\,/\,$\AA^2$)')
    ax1.set_xlabel(r'$T$ (K)')
    for c in data.keys():
        if c not in columns and c != 'T': 
            ax1.plot(data['T'], sp.array(data[c])*1000.0, color=tum_light_grey, linewidth=2.5, linestyle='solid')
    if legend:
        for c in columns:
            ax1.plot(data['T'], sp.array(data[c])*1000.0, color=next(lc), linewidth=5.0, linestyle=next(ls), label='\\verb|'+c+'|')
            ax1.legend(loc="upper left", bbox_transform=ax1.transAxes, bbox_to_anchor=(1,1), fontsize='xx-small')
    else:
        for c in columns:
            ax1.plot(data['T'], sp.array(data[c])*1000.0, color=next(lc), linestyle=next(ls), linewidth=5.0)
    fig.subplots_adjust(hspace=0)
    fig.set_size_inches( (8, 8) )
    plt.grid()
    plt.ylim(-50, 200)
    fig.set_size_inches( (8, 8) )
    plt.savefig('./' + fn + '.png', bbox_inches='tight', pad_inches=0.0, transparent=True)
    return


def make_table(data_u, var, columns, sheet, data_xls=None, key='surface_free_energy'):
    if data_xls == None:
        data_xls = {}
    if sheet not in data_xls:
        data_xls[sheet] = {} 
    for c in columns:
        data_xls[sheet][c] = []
    for data, v in zip(data_u, var): 
        if 'id' in columns:
            data_xls[sheet]['id'].append(v['id'])
        if 'U' in columns:
            data_xls[sheet]['U'].append(v['U'])
        if 'pH' in columns:
            data_xls[sheet]['pH'].append(v['pH'])
        if 'T' in columns:
            data_xls[sheet]['T'].append(v['T'])
        for d in data:
            k = d['description']
            if k in columns:
                data_xls[sheet][k].append(d[key])
    return data_xls

def write_images(data):
    import ase
    import ase.io
    if not os.path.exists("images"):
        os.mkdir("images")
    if not os.path.exists("geometries"):
        os.mkdir("geometries")
    for d in data:
        cell = ase.Atoms(symbols=d['symbols'], positions=d['xyz'], cell=d['cell'], pbc=(1,1,1))
        ase.io.write('geometries/'+d['description']+'.in', cell, format="aims")
        ase.io.write('images/'+d['description']+'.png', cell * (3, 3, 1), rotation='20z,-70x')
    return

