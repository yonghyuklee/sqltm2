import os
import re
import scipy as sp
import pickle


# basic constants
kB = 1.3806488E-23
kBK_to_eV = 8.6173323E-05 # kB*1K
toang = 0.52917721
kJ_mol_to_eV = 0.01036410 
icm_to_eV = 0.00012398419


# determine multiplicities of a list of symbols in a basis of fixed order
def multiplicity(l, b):
    n = len(b)
    m = sp.zeros(n, dtype=sp.int32)
    for s in l: 
        m[b.index(s)] += 1
    return m

def component_coeff(C, n):
    A = sp.array([ c['n'] for c in C ], dtype=sp.float64).T
    x = sp.linalg.solve(A,n)
    return x

def component_internal_energy(C, n):
    return sp.sum([ n[i]*C[i]['E'] for i in range(len(C)) ])

def component_zpe(C, n):
    return sp.sum([ n[i]*C[i]['ZPE'] for i in range(len(C)) ])

def component_enthalpy(C, n):
    return sp.sum([ n[i]*(C[i]['E'] + C[i]['ZPE']) for i in range(len(C)) ])

def chemical_potential(v, n):
    mu_a = activity_potential(v['a'], n, v['T'])
    mu_S = entropic_potential(v, n) 
#    if n[0] == 0:
#        print(mu_a, mu_S, n)
    return mu_a + mu_S

def entropic_potential(v, n):
    mu = 0.0
    for i in range(len(n)):
        mu += n[i]*v['components'][i]['mu'](v['T'])
    return mu

# evaluate activity dependent potential from Nernst eq.
# stoichiometric coefficients: products +, reactants -
# since n is the composition of the slab, the sign needs to be inverted
# (actually this is done by subtracting mu in the function
# surface_energy())
# input: a[no unit], n[no unit], T[K]
# returns potential in eV
def activity_potential(a, n, T):
    return T*kBK_to_eV*sp.sum(sp.array(n, dtype=sp.float64)*sp.log(sp.array(a, 
           dtype=sp.float64)))

def pH_to_a(pH):
    return sp.exp(-sp.log(10.0)*pH)

def a_to_pH(a):
    return -sp.log(a)/sp.log(10.0) 

# reversible hydrogen electrode (RHE) vs SHE
# H+(aq) + e-(g) -> 1/2 H2(g)
def rhe_potential(a, T):
    if len(a) != 2:
        print("ERROR (rhe_potential): invalid activity")
        raise SystemExit
    n = [ -1, 0.5 ]
    return activity_potential(a, n, T)

def load_data(fn, remove=[],remove_structure=[]):
    with open(fn, 'rb') as fd:
        data_raw = pickle.load(fd)
    # remove selected items by key
    remove = []
    try:
        data_raw = [ d for d in data_raw if d['description'] not in remove ]
    except:
        for k in data_raw:
            k['description'] = 'dummy'
    # remove structures by structure
    try:
        data_raw = [ d for d in data_raw if d['structure'] not in remove_structure]
    except:
        for k in data_raw:
            k['structure'] = 'nanoparticle'
    return data_raw

# Enthalpy = Electronic energy + p*V
#          + Zero point energy + Vibrational energy + Rotational energy + Translational energy
#          + Contribution from Activities
# Gibbs free energy = Enthalpy - TS
# activities are currently only in G (should be fixed), but are zero w.r.t. RHE anyway
def compute_surface_energy(v,
                           data_raw, 
                           zpe_slab,
                           each_scf = False,
                           ):
    data = []
    stable = True
    for w in data_raw:

        d = w.copy()

        if d['structure'] == 'slab':
            try:
                d['surface_area']
            except:
                d['surface_area'] = sp.linalg.norm(sp.cross(d['cell'][0],d['cell'][1]))
            d['surface_area'] *= 2
        
            try:
                n = multiplicity(d['multiple_unit_cell'].prod()*d['symbols'], v['basis']) # no of atoms of each type in slab
            except:
                n = multiplicity(d['symbols'], v['basis']) # no of atoms of each type in slab
                print('Assuming multiple_unit_cell 1 1 1')
        else:
            n = multiplicity(d['symbols'], v['basis']) # no of atoms of each type in slab

        x = component_coeff(v['components'],n) # no of species of each type
        mu = chemical_potential(v,x)
        
        ### these are the only non-generic lines of code in this loop ###

        ''' Only important if H atoms are included in structure ???? '''
        try:
            nH = n[int(sp.argwhere(sp.array(v['basis']) == 'H'))]
        except:
            nH = 2*n[int(sp.argwhere(sp.array(v['basis']) == 'H2'))]
        nel = nH # no of e- = no of H+,  for H2 basis: 2.0*x[0]
        ''' Assuming that zpe_slab[0] refers to 'H' and since zpe_slab[1] == 0 '''
        # slab_zpe = n[0]*zpe_slab[0] + (n[1] - 2.0*n[2])*zpe_slab[1] # Old code: DOES NOT WORK cause n[0] refers to 'Ru'!
        slab_zpe = nH*zpe_slab[0] #  + (n[1] - 2.0*n[2])*zpe_slab[1]  TODO: I guess the second part was to include O zpe but not sure.
        #slab_zpe = n[0]*zpe_slab[0]*d['surface_area'] # for ZPE according to Sun2003

        ### formation enthalpy and free energy
        d['zpe'] = slab_zpe - component_zpe(v['components'],x)
        if not each_scf:
            d['internal_energy'] = d['total_energy'] - component_internal_energy(v['components'],x) + nel*v['U']
        elif each_scf:
            d['internal_energy'] = sp.array(d['energy_scf']) - component_internal_energy(v['components'],x) + nel*v['U']
        d['enthalpy'] = d['internal_energy'] + d['zpe']
        d['entropy'] = mu
        d['free_energy'] = d['enthalpy'] - mu
        d['surface_enthalpy'] = d['enthalpy']/d['surface_area']
        d['surface_free_energy'] = d['free_energy']/d['surface_area']

        # set stable flag for postprocessing
        if not each_scf and d['surface_free_energy'] < 0.0:
            stable = False
        data.append(d)
    v['stable'] = stable
    return data

def min_surface_energy(data):
    facets = set([ d['orientation'] for d in data if d['structure'] == 'slab' ])
    min_E = dict.fromkeys(facets, { 'surface_enthalpy': 1000.0 })
    min_G = dict.fromkeys(facets, { 'surface_free_energy': 1000.0 })
    for d in data:
        # determine termination of lowest energy for each facet
        if min_E[d['orientation']]['surface_enthalpy'] > d['surface_enthalpy']:
            min_E[d['orientation']] = d
        if min_G[d['orientation']]['surface_free_energy'] > d['surface_free_energy']:
            min_G[d['orientation']] = d
    return min_E, min_G


def H_density(data):
    for d in data:
        if 'nH' in d:
            d['rho_H'] = 0.5*d['nH']/d['surface_area']
        else:
            d['rho_H'] = 0.0
        #print("{c:12.6f}    {d:s}".format(c=d['rho_H'], d=d['description']))
    return
