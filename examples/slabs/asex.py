from __future__ import print_function
import os,sys
import scipy as sp
import scipy.linalg as LA
import numpy as np
import functools, fractions
import math
import ase.geometry
from ase.build import cut
from ase.build.tools import rotation_matrix
from ase.constraints import FixAtoms,FixBondLengths
#from ase.optimize.sciopt import SciPyFminBFGS, SciPyFminCG
#from ase.optimize.bfgslinesearch import BFGSLineSearch

def gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:      
        a, b = b, a % b
    return a

def lcm(a, b):
    """Return lowest common multiple."""
    if a == 0:
        return b
    elif b == 0:
        return a
    else:
        return a * b // gcd(a, b)

def lcmm(*args):
    """Return lcm of args."""   
    return functools.reduce(lcm, args)

def rotate_cell(atoms, R):
    atoms.positions[:] = np.dot(atoms.positions, R.T)
    atoms.cell[:] = np.dot(atoms.cell, R.T)
    return

# compute equidistant k-grid for given spacing
def kpoint_grid(cell, dx, fd_info=sys.stdout):
    rc = cell.get_reciprocal_cell()
    l_rc = np.empty(3,dtype=np.float64)
    for i in range(3):
        l_rc[i] = LA.norm(rc[i], 2)
    v = l_rc[:]/dx
    print("Balanced k-grid for spacing dx={0:12.6f} (*2pi): ".format(dx),end="",file=fd_info)
    print("{0:12.6f}{1:12.6f}{2:12.6f}".format(*v),file=fd_info)

    k_grid_large = list(map(int, np.ceil(v)))
    dx_large = l_rc[:]/list(map(float, k_grid_large[:]))
    k_grid_small =  list(map(int, np.floor(v)))
    k_grid_rounded =  list(map(int, np.rint(v)))
    for i in range(3):
        if k_grid_small[i] == 0:
	        k_grid_small[i] = 1
        if k_grid_rounded[i] == 0:
	        k_grid_rounded[i] = 1
    dx_small = l_rc[:]/list(map(float, k_grid_small[:]))
    dx_rounded = l_rc[:]/list(map(float, k_grid_rounded[:]))
    print("Closest integer k-grids (min/max/rounded): ",file=fd_info)
    print("{0:^4d}{1:^4d}{2:^4d}".format(*k_grid_large),end="",file=fd_info)
    print("{0:12.6f}{1:12.6f}{2:12.6f}".format(*dx_large),file=fd_info)
    print("{0:^4d}{1:^4d}{2:^4d}".format(*k_grid_small),end="",file=fd_info)
    print("{0:12.6f}{1:12.6f}{2:12.6f}".format(*dx_small),file=fd_info)
    print("{0:^4d}{1:^4d}{2:^4d}".format(*k_grid_rounded),end="",file=fd_info)
    print("{0:12.6f}{1:12.6f}{2:12.6f}".format(*dx_rounded),file=fd_info)
    return k_grid_rounded
 
# fix layers of atoms in the center of the slab
def fix_atoms(a,relax=None,fd_info=sys.stdout):
    if relax == None:
        return
    ilayer, dlayer = ase.geometry.get_layers(a,(0,0,1))
    natoms = len(ilayer)
    nlayers = len(dlayer)
    cmin = relax[0]
    cmax = nlayers - relax[1]
    print("{0:<60s}  {1:4d} {2:s} {3:4d} {4:s}".format(
        "Fixing all atom except", relax[0],
        "bottom layers and", relax[1], "top layers"),file=fd_info)
    indices=[i for i in range(natoms) if ilayer[i] >= cmin and ilayer[i] < cmax]
    nfix = len(indices)
    print("{0:<60s}  {1:12d} {2:12d} {3:12d}".format("No of fixed/unconstrained/total atoms:", nfix, natoms-nfix, natoms),file=fd_info)
    c = FixAtoms(indices=indices)
    a.set_constraint(c)
    #mask = np.zeros(len(a), dtype=bool)
    #mask[indices] = True
    return indices

# Create cell vectors as orthogonal as possible and with c-vector as close
# as possible to the requested direction (normal vector nv). 
# A set of internal coordinates is returned
# in internal cell vector coordinates which can be used with ASE's cut
# function
# Note: c orth to a and b is only possible for cubic systems!!!
def create_orth_basis(c, nv=[0,0,1], unitcells=1,fd_info=sys.stdout):
    # find greatest common divisor int vector
    d = abs(functools.reduce(math.gcd, nv))
    n = [ int(i / d) for i in nv ]
    # least common multiple of n[i]
    m = lcmm(*n)
    # find 0 elements in normal vector
    i0 = []
    ix = []
    ni0 = 0
    nix = 0
    for i in range(3):
        if n[i] == 0:
            i0.append(i)
            ni0 += 1
        else:
            ix.append(i)
            nix += 1

    # now distinguish the three cases 0,1,2 indices equal 0
    w = np.zeros((3,3), dtype=int)
    if nix == 3:
        w[0,0] = -n[0]
        w[0,1] = n[1]
        w[1,1] = -n[1]
        w[1,2] = n[2]
        #w[2,2] = n[2] # w[2,i] = n[i] maybe choose by orthogonality (smallest proj)
    elif nix == 2:
        #print(ix,v[ix[0]],v[ix[1]])
        w[0,i0[0]] = 1
        w[1,ix[1]] = -n[ix[1]]
        w[1,ix[0]] = n[ix[0]]
        #w[2,ix[0]] = 1 # or ix[1], maybe choose by orthogonality
    elif nix == 1:
        w[0,i0[0]] = 1
        w[1,i0[1]] = 1
        #w[2,ix[0]] = 1

    # direction vector in Cartesian coordinates
    #nc = n[0]*c[0] + n[1]*c[1] + n[2]*c[2]
    #nc_norm = LA.norm(nc, 2)
    s = np.dot(c.T,c) # metric of the lattice vectors
    #print("NORM: ", nc_norm, np.sqrt(np.dot(np.dot(n,s),n)))
    norm_nd = np.sqrt(np.dot(np.dot(n,s),n)) # norm of direction vector
    nd = np.dot(n,s)/norm_nd # direction vector with metric multiplied in
    # now search for n which maximizes <nd | n>
    # i.e. a vector as parallel as possible to n
    updated = False
    y0 = -2.0
    if unitcells < 0:
        for h, k in np.ndindex(-unitcells+1,-unitcells+1):
            for l in range(0, -unitcells-h-k+1):
                if h + k + l == 0:
                    continue
                x = [h, k, l]
                norm = np.sqrt(abs(np.dot(np.dot(x,s),x)))
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                x = [-h, k, l]
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                x = [h, -k, l]
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                x = [-h, -k, l]
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                if updated == False:
                    break
    else:
        for h, k in np.ndindex(unitcells+1,unitcells+1):
            for l in range(0, unitcells-h-k+1):
                if h + k + l == 0:
                    continue
                if h + k + l != unitcells:
                    continue
                x = [h, k, l]
                norm = np.sqrt(abs(np.dot(np.dot(x,s),x)))
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                x = [-h, k, l]
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                x = [h, -k, l]
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                x = [-h, -k, l]
                y = np.dot(nd,x)/norm - 1.0
                if y > y0:
                    y0 = y
                    x0 = x
                    updated = True
                if updated == False:
                    break
 
    print("Direction vector (surface normal): {0:^4d}{1:^4d}{2:^4d}".format(*n),file=fd_info)
    print("Max. cell size: ", abs(unitcells),file=fd_info)
    # reduce c-vector if possible
    d = abs(functools.reduce(math.gcd, x0))
    n0 = [ int(i / d) for i in x0 ]
    if np.any(n0 != x0):
        print("Cell is not minimal. Cell vector c: ", x0, " -> ", n0,file=fd_info)
    else:
        print("Cell vector c: ", x0,file=fd_info)
    an = np.rad2deg(np.arccos(round(y0 + 1.0, 10)))
    print("Angle between c vector surface normal:{0:6.2f}".format(an),file=fd_info)
    w[2,:] = n0
    nunitcells = LA.det(w)
    if nunitcells < 0:
        w = -w
        nunitcells = -nunitcells
    print("Volume of final cell {0:6.2f} x Volume of unitcell".format(nunitcells),file=fd_info)
    return w


def create_cell(unitcell, direction=None, nmax=1, fd_info=sys.stdout): 
    if direction == None or all(d == 0 for d in direction):
        print("Direction not defined. Returning conventional bulk supercell.",file=fd_info)
        cell = unitcell
    else:
        # create oriented cell of max. nmax unitcells
        cell_coord = create_orth_basis(unitcell.cell, nv=direction, unitcells=nmax)
        cell = cut(unitcell, a=cell_coord[0], b=cell_coord[1], c=cell_coord[2],
                clength=None, origo=(0.0, 0.0, 0.0), nlayers=None, extend=1.0,
                tolerance=0.01, maxatoms=None)
        R = rotation_matrix(np.cross(cell.cell[0], cell.cell[1]), [0,0,1.0], cell.cell[0], [1,0,0])
        rotate_cell(cell, R)
    # division is always possible due to the construction of cell_coord
    cell_volume = abs(LA.det(cell.cell))
    unitcell_volume = abs(LA.det(unitcell.cell))
    cell_surface = surface_area(cell)
    unitcell_surface = surface_area(unitcell)
    print("{0:<80s}  {1:12.6f}".format("Surface area of unitcell:",unitcell_surface),file=fd_info)
    print("{0:<80s}  {1:12.6f}".format("Surface area of oriented cell:",cell_surface),file=fd_info)
    print("{0:<80s}  {1:12.6f}".format("Volume of unitcell:",unitcell_volume),file=fd_info)
    print("{0:<80s}  {1:12.6f}".format("Volume of oriented cell:",cell_volume),file=fd_info)
    print("{0:<80s}  {1:12.6f}".format("Relative base area of maximally orthogonal cell w. r. t. unitcell:",cell_surface/unitcell_surface),file=fd_info)
    print("{0:<80s}  {1:12.6f}".format("Relative volume of maximally orthogonal cell w. r. t. unitcell:",cell_volume/unitcell_volume),file=fd_info)
    print("{0:<80s}  {1:6.2f}{2:6.2f}{3:6.2f} {4:6.2f} {5:6.2f} {6:6.2f}".format("Unitcell parameters:",*ase.geometry.cell_to_cellpar(unitcell.cell)),file=fd_info)
    print("{0:<80s}  {1:6.2f}{2:6.2f}{3:6.2f} {4:6.2f} {5:6.2f} {6:6.2f}".format("Cell parameters:",*ase.geometry.cell_to_cellpar(cell.cell)),file=fd_info)
    return cell

def surface_area(cell):
    return LA.norm(np.cross(cell.cell[0], cell.cell[1]),2)

# add vacuum to match given volume
def set_volume(cell, v, minvac=0.0):
    norm_c = LA.norm(cell.cell[2], 2)
    z = -cell.cell[2][2]
    scale = v/abs(LA.det(cell.cell))
    cell.cell[2] *= scale
    z += cell.cell[2][2]
    cext =  (scale - 1.0)*norm_c
    assert z >= minvac
    print("""Set volume to {v:12.6f} by extending c-vector by {cext:12.6f} ang"""
          """(corresponds to {z:12.6f} angstrom vacuum in z-direction)"""
          .format(v=v, cext=cext, z=z))
    return

# remove layers at top and bottom of cell
def create_slab(cell, dimension, termination=None, rmlayers=None, fd_info=sys.stdout):
    if termination == None:
        print("{0:<60s}  {1:4d}{2:4d}{3:4d}".format("No termination - creating supercell with dimension",*dimension),file=fd_info)
        supercell = cell.repeat(dimension)
        return supercell
    #ntot = sp.prod(dimension + [0,0,2])
    nz = dimension[2] + 2
    cell_tags = cell.get_tags()
    max_tag = max(cell_tags) # = no. of atoms in bulk unit cell - 1
    slab = cell.repeat([dimension[0], dimension[1], 1])
    # compute new tags for supercell
    slab_tags = []
    for i,j in np.ndindex(dimension[0], dimension[1]):
        slab_tags += [ t+i*max_tag+j*dimension[1]*max_tag for t in cell_tags ]
    slab.set_tags(slab_tags)
#    print(cell.get_tags())
#    print(slab.get_tags())
    slab = slab.repeat([1, 1, nz])
    # assign atoms to layers
    # ilayer[natoms]: index of atom
    # dlayer[nlayers]: distance of layer from origin/bottom layer
    ilayer, dlayer = ase.geometry.get_layers(slab,(0,0,1))
    natoms = len(ilayer)
    nlayers = len(dlayer)
    nterminations = int(nlayers/nz)
    
    # get all different terminations
    print("{0:<60s}  {1:12d}".format("No of terminations (= no of layers in unit cell):", nterminations),file=fd_info)
    print("{0:<60s}  {1:12d}".format("No of atoms in stoichiometric base cell:",len(cell)),file=fd_info)
    print("{0:<60s}  {1:12d}".format("No of atoms in stoichiometric supercell:",dimension[2]*len(cell)),file=fd_info)
    
    # remove top/bottom layers to requested termination layer
    # in order to make the slab symmetric always one layer more is
    # removed from the top, i.e. for termination 0, the top layer must
    # be added to the bottom, termination 1: +1 layer top, +2 layer bottom
    rm_list =[]
    for j in range(1,nterminations - termination): # n, n-1, ..., t+1
        #print(nlayers - j)
        rm_list += [i for i in range(natoms) if ilayer[i] == nlayers - j]
    for j in range(nterminations - termination): # 0,1,...,t-1
        #print(j)
        rm_list += [i for i in range(natoms) if ilayer[i] == j]

    # remove additional layers
    if rmlayers != None:
        #print([surf[i].symbol for i in range(len(ilayer))])
        #print([ilayer[i] for i in range(len(ilayer)) if supercell[i].symbol == 'Ir'])
        for nl in rmlayers:
            if nl < 0:
                rm_list += [i for i in range(natoms) if ilayer[i] == nlayers + nl]
            else:
                rm_list += [i for i in range(natoms) if ilayer[i] == nl]
    del slab[rm_list]
    return slab

def select_atoms(slab, selector, side='both'):
    ilayer, dlayer = ase.geometry.get_layers(slab,(0,0,1))
    nlayers = len(dlayer)
    selection = []
    if 'limit' in selector:
        limit = selector['limit']
    else:
        limit = -1
    if side == 'bottom' or side == 'both':
        for i in range(len(slab)):
            if 'layer' in selector:
                if ilayer[i] not in np.atleast_1d(selector['layer']):
                    continue
            if 'tag' in selector:
                if slab[i].tag not in np.atleast_1d(selector['tag']):
                    continue
            if 'symbol' in selector:
                if slab[i].symbol not in np.atleast_1d(selector['symbol']):
                    continue
#            if 'i' in selector:
#                if i in selector['i']:
#                    continue
            selection.append(i)
            if len(selection) == limit:
                break
    limit += len(selection)
    layers = [ nlayers - 1 - l for l in np.atleast_1d(selector['layer']) ]
    if side == 'top' or side == 'both':
        for i in range(len(slab)):
            if 'layer' in selector:
                if  ilayer[i] not in layers:
                    continue
            if 'tag' in selector:
                if slab[i].tag not in np.atleast_1d(selector['tag']):
                    continue
            if 'symbol' in selector:
                if slab[i].symbol not in np.atleast_1d(selector['symbol']):
                    continue
            selection.append(i)
            if len(selection) == limit:
                break
    return selection

def rm_atoms(slab, selector=None, side='both'):
    selection = select_atoms(slab, selector, side)
    ##for i in selection:
    ##    print(slab[i].tag, slab[i].symbol, slab[i].position)
    del slab[selection]
    return slab

### 001 // 100 // 110
def add_species(slab, species, selector=None, dist=2.0, side='both',xy=[0.0,0.0]):
    ilayer, dlayer = ase.geometry.get_layers(slab,(0,0,1))
    nlayers = len(dlayer)
    # com = species.get_center_of_mass() + (xy[0], xy[1], 0.0)
    top = []
    bottom = []
    if np.isscalar(dist):
        d = np.array([0.0,0.0, dist], dtype=np.float64)
    else:
        d = np.array(dist, dtype=np.float64)
    if side == 'top' or side == 'both':
        for i in range(len(slab)):
            top = select_atoms(slab, selector, 'top')
    if side == 'bottom' or side == 'both':
            bottom = select_atoms(slab, selector, 'bottom')

    c = FixAtoms(indices=range(len(slab)))
    slab.set_constraint(c)
 
    for i in bottom: 
        s = species.copy()
        s.set_tags(-1)
        com = species.get_center_of_mass() - (xy[0], xy[1], 0.0)
        for a in s:
            # a.x = -a.x
            # a.y = -a.y
            a.position += slab[i].position + com - d
        slab += s
    for i in top: 
        s = species.copy()
        s.set_tags(-1)
        com = species.get_center_of_mass() + (xy[0], xy[1], 0.0)
        for a in s:
            a.z = -a.z
            a.position += slab[i].position - com + d
        slab += s
    return slab 


#### 010 // 011 // 111
#def add_species(slab, species, selector=None, dist=2.0, side='both',xy=[0.0,0.0]):
#    ilayer, dlayer = ase.geometry.get_layers(slab,(0,0,1))
#    nlayers = len(dlayer)
#    # com = species.get_center_of_mass() + (xy[0], xy[1], 0.0)
#    top = []
#    bottom = []
#    if np.isscalar(dist):
#        d = np.array([0.0,0.0, dist], dtype=np.float64)
#    else:
#        d = np.array(dist, dtype=np.float64)
#    if side == 'top' or side == 'both':
#        for i in range(len(slab)):
#            top = select_atoms(slab, selector, 'top')
#    if side == 'bottom' or side == 'both':
#            bottom = select_atoms(slab, selector, 'bottom')
#
#    #c = FixAtoms(indices=range(len(slab)))
#    #slab.set_constraint(c)
#
#    for i in bottom: 
#        s = species.copy()
#        s.set_tags(-1)
#        com = species.get_center_of_mass() + (xy[0], xy[1], 0.0)
#        for a in s:
#            a.x = -a.x
#            a.y = -a.y
#            a.position += slab[i].position + com - d
#        slab += s
#    for i in top: 
#        s = species.copy()
#        s.set_tags(-1)
#        com = species.get_center_of_mass() + (xy[0], xy[1], 0.0)
#        for a in s:
#            a.z = -a.z
#            a.position += slab[i].position - com + d
#        slab += s
#    return slab 

def print_stats(slab):
    # sort by species
    species = {}
    for a in slab:
        if a.symbol not in species:
            species[a.symbol] = []
        species[a.symbol].append(a)
    print("=== slab composition ===")
    for s in species:
        print("{s:>8s}: {n:>12d}".format(s=s, n=len(species[s])))
    print("-"*24)
    print("{s:>8s}: {v:>12.6f}".format(s="Volume", v=slab.get_volume()))
    print("========================")
    return


def write_aims(fn, sym, xyz, cell=None, con=None, mom=None, lab=None):
    s = ''
    n = len(sym)
    fixed = np.zeros(n, dtype=bool)
    if con is not None:
        fixed[con] = True
    if mom is None:
        mom = np.zeros(n, dtype=np.float64)
    if lab is None:
        lab = [ None ]*n
    if cell is not None:
        for i in range(3):
            print(cell[i])
            s += 'lattice_vector {0:20.10f} {1:20.10f} {2:20.10f}\n'.format(*cell[i])
    for i in range(n):
        s += 'atom {0:20.10f} {1:20.10f} {2:20.10f} {3:4s}'.format(xyz[i][0], xyz[i][1], xyz[i][2], sym[i])
        if lab[i] is not None:
            s += ' {0:6s}'.format(str(lab[i]))
            #s += ' XYZ'.format(str(lab[i]))
        s += '\n'
        if fixed[i]:
            s += 'constrain_relaxation .true.\n'
        if abs(mom[i]) > 0.01:
            s += 'initial_moments {0:20.10f}\n'.format(mom[i])
    with open(fn, 'w') as fd:
        fd.write(s)
    return


if __name__ == '__main__':
    print("ASE eXtensions")
    import ase.spacegroup
    from ase.visualize import view
    a = 4.50513
    c = 3.15862
    x = 0.311446 # exact Oh coordination
    unitcell = ase.spacegroup.crystal(['Ir', 'O'], basis=[(0 ,0, 0), (x, x, 0.0)], spacegroup=136, cellpar=[a, a, c, 90, 90, 90])
    nz = -5 # max no of unitcells
    nv = [ 1, 1, 1 ] # direction normal vector
    #cell_coord = create_orth_basis(unitcell.cell, nv=nv, unitcells=nz, fd_info=sys.stdout)
    cell = create_cell(unitcell, nv, nmax=nz, fd_info=sys.stdout)
    # dimensions of slab-supercell (without termination in units of orthogonalized cell)
    dimension = [ 2, 2, 4 ]
    rmlayers = [-12, 12 ] # remove one unit (super) cell from top and bottom
    slab = create_slab(cell, dimension=dimension, rmlayers=rmlayers, termination=1, fd_info=sys.stdout)
    fix_atoms(slab, [4,4])
    slab.center(vacuum=10.0, axis=2)

    species = ase.build.molecule('H2O')
    pairs = []
    for i in range(len(species)):
        for j in range(i+1,len(species)):
            pairs += [i,j]
    c = FixBondLengths(pairs)
    species.set_constraint(c)
#    SciPyFminBFGS(species, logfile='-', trajectory=None) 
#    dyn = BFGSLineSearch(atoms=species, trajectory=None, restart=False)
    selector = { 'symbol': 'O', 'layer': 0 }
    slab = add_species(slab, species, selector=selector, dist=2.0, side='both')
    print_stats(slab)
    print("Setting volume to 8000.0")
    # minvac is just a check (e.g. program will raise an error if there is less
    # then minvac vacuum for a given volume)
    set_volume(slab, 8000.0, minvac=10.0)
    print_stats(slab)
    #slab.write(filename="geometry.in", format="aims")
    #view(slab)

    

