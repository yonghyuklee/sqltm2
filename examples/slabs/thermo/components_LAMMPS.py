import sys
import os
import scipy as sp

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import thermo as td
import janaf


# ZPEs diatomics:  Irikura2007 https://doi.org/10.1063/1.2436891 
# Water: Benedict1956
# system components


# eV to Hartree: 27.211384500


def get_basis(components_list):
    s = []
    for c in components_list:
        s.append(c['symbol'])
    basis = [item for sublist in s for item in sublist]
#    return dict((x,l.count(x)) for x in set(basis))
    return list(set(basis))

def update_components(components_list):
    basis = get_basis(components_list)
    for c in components_list:
        n = sp.zeros(len(basis))
        for i,e in enumerate(basis):
            n[i] = c['symbol'].count(e) 
        c['n'] = n
    return components_list,basis

def get_activity(components_list, act_dict):
    activity = sp.zeros(len(components_list))
    for i,c in enumerate(components_list):
        if c['name'] in act_dict:
            activity[i] = act_dict[c['name']]
        else:
            activity[i] = 1
    return activity

#########
# TODO
H2 = {
    'name': 'H2',
    'symbol':['H','H'],
    'E': -32.067483979529904,  # TAKEN FROM QE (hoping that it will not differ to much
    'ZPE': 2179.31*td.icm_to_eV, # experiment (approx. 0.27 eV)
    'mu': janaf.mu('H2')
}

H2O = {
    'name': 'H2O',
    'symbol':['H','H','O'],
    'E': -467.77509470255524,  # TAKEN FROM QE (hoping that it will not differ to much
    'ZPE': 4504.0*td.icm_to_eV, # experiment (approx. 0.56 eV)  geoopt
    'mu': janaf.mu('H2Og_1bar') # H2O(g) for error compensation due to solvation energy
}
######## 
Hp = {
    'name': 'Hp',
    'symbol':['H'],
    'E': 0.5*H2['E'],
    'ZPE': 0.5*H2['ZPE'],
    'mu': janaf.mu('H2', c=0.5)
}

O2 = {
    'name': 'O2',
    'symbol':['O','O'],
    'E': 0.0,  # HAS TO BE UPDATED
    'ZPE': 787.3806*td.icm_to_eV, # experiment (approx. 0.10 eV)
    'mu': janaf.mu('O2')
}

IrO2 = {
    'name': 'IrO2',
    'symbol':['Ir','O','O'],
    'E': 0.0,  # HAS TO BE UPDATED 

    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}

TiO2 = {

    'name': 'TiO2',
    'symbol':['Ti','O','O'],
    'E': 0.000000000,  # DUMMY

    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}

RuO2 = {
    'name': 'RuO2',
    'symbol':['Ru','O','O'],
    'E': 0.0,  #  DUMMY

    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}
