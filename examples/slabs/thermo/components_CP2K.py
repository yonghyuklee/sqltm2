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


H2 = {
    'name': 'H2',
    'symbol':['H','H'],
    'E': -31.617596538,       # PBE, DZVP-MOLOPT-SR-GTH
#    'E': -31.620085746498816, # PBE DFTD3, DZVP-MOLOPT-SR-GTH
#    'E': -31.67589800191458,  # HSE, DZVP-MOLOPT-SR-GTH
    'ZPE': 2179.31*td.icm_to_eV, # experiment (approx. 0.27 eV)
    'mu': janaf.mu('H2')
}

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
    'E': -867.0780417898, # PBE, DZVP-MOLOPT-SR-GTH
    'ZPE': 787.3806*td.icm_to_eV, # experiment (approx. 0.10 eV)
    'mu': janaf.mu('O2')
}

H2O = {
    'name': 'H2O',
    'symbol':['H','H','O'],
    'E': -468.5675459289,     # PBE, DZVP-MOLOPT-SR-GTH
#    'E': -468.33862423910847, # HSE, DZVP-MOLOPT-SR-GTH
    'ZPE': 4504.0*td.icm_to_eV, # experiment (approx. 0.56 eV)
    'mu': janaf.mu('H2Og_1bar') # H2O(g) for error compensation due to solvation energy
}

IrO2 = {
    'name': 'IrO2',
    'symbol':['Ir','O','O'],
    'E': -3741.422860248972, # PBE, DZVP-MOLOPT-SR-GTH (5x5x5 supercell)
#    'E': -3741.4313074194537, # PBE, DZVP-MOLOPT-SR-GTH (4x4x4 supercell)
#    'E': -3741.3732410073717, # PBE, DZVP-MOLOPT-SR-GTH (3x3x3 supercell)
#    'E': -3741.589998650337, # PBE, DZVP-MOLOPT-SR-GTH (2x2x2 supercell)
#    'E': -3742.273749089785, # PBE, DZVP-MOLOPT-SR-GTH (single unit cell)

    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}

RuO2 = {
    'name': 'RuO2',
    'symbol':['Ru','O','O'],
    'E': -3449.1855084649874 ,# PBE, DZVP-MOLOPT-SR-GTH (4x4x4 supercell)  
#    'E': -3449.151343849106 , # PBE, DZVP-MOLOPT-SR-GTH (3x3x3 supercell)
#    'E': -3449.394462536165 , # PBE, DZVP-MOLOPT-SR-GTH (2x2x2 supercell)
#    'E': -3448.774993240055 , # PBE, DZVP-MOLOPT-SR-GTH (1x1x1 supercell)
    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}

MnO2 = {
    'name': 'MnO2',
    'symbol':['Mn','O','O'],
    'E': 0, # Dummy Value. NOT CALCULATED YET 
    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}


TiO2 = {
    'name': 'TiO2',
    'symbol':['Ti','O','O'],
    'E': -2462.1611233875883, # PBE-DFTD3 DZVP-MOLOPT-SR-GTH (4x4x2 supercell)
#    'E': -2460.7900434712463, # HSE, DZVP-MOLOPT-SR-GTH (2x2x2 supercell) SPC
#    'E': -2473.1670233098343, # HSE, DZVP-MOLOPT-SR-GTH (1x1x1 supercell)
    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}

SnO2 = {
    'name': 'SnO2',
    'symbol':['Sn','O','O'],
    'E': 0, # Dummy Value. NOT CALCULATED YET 
    'ZPE': 0.0, # assume this cancels
    'mu': lambda mu: 0.0
}
