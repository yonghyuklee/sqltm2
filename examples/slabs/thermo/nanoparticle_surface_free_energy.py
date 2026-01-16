#!/usr/bin/python

from __future__ import print_function
import sys, os
import argparse
import pickle
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import thermo as td
import janaf
import pandas as pd
from copy import deepcopy 


# Sun/Reuter
#zpe_slab = [ 0.015, 0.0 ] # per angstrom^2
zpe_slab = [ 0.30601, 0.0 ] # Sun2003 0.015 eV/A^2
temp = 298.15
pH = 0.0

# Activities
pressure = 0.03166 # equal to liquid water at 298K
aH = td.pH_to_a(pH)

def extract_surface_free_energy(
                                data_raw,
                                components, 
                                each_scf = False,
                                mute = False,
                                dump_path = '',
                                U = 0.0,
                                vso2 = False,
                                pot=True,
                                ):

    td.H_density(data_raw)


    comp = [
            components.Hp,
            components.IrO2, 
            components.RuO2, 
            components.TiO2, 
            ]
    if vso2:
        comp.append(components.O2)
    else:
        comp.append(components.H2O)

    comp,basis = components.update_components(comp)
    activity = components.get_activity(comp, {'Hp':aH, 'O2': pressure})
    
    v = {
        'U': U,
        'T': temp,
        'basis': basis,
        'components': comp,
        'a' : activity,
        }

    d = td.compute_surface_energy(v, 
                                  data_raw, 
                                  zpe_slab,
                                  each_scf = each_scf
                                  )
    
    pickle.dump(d,open('surface_data.pkl','wb'))

    columns = ['description','surface_area','internal_energy','entropy','zpe',
                'enthalpy','free_energy', 'surface_enthalpy',
                'surface_free_energy','total_energy']
    if each_scf:
        columns = columns + ['energy_scf']

    result = pd.concat([pd.Series(s) for s in d],axis=1).transpose()
    result = result[columns]
    if not mute: 
        try:
            print('Initial SFE: %5.4f'%d[0]['surface_free_energy'][0])
            print('Final SFE: %5.4f'%d[0]['surface_free_energy'][-1])
            print('Surface area: %s'%d[0]['surface_area'])
        except:
            print(result)
        result.to_csv(dump_path + 'result_surface_energies.csv')
    if pot:
        pot_sfe_init  = []
        pot_sfe_final = []
        U = np.arange(0.0, 1.1, 0.1)
        for u in U:
            v['U'] = u
            d = td.compute_surface_energy(v, 
                                          data_raw, 
                                          zpe_slab,
                                          each_scf = True,
                                          )
            pot_sfe_init.append(d[0]['surface_free_energy'][0])
            pot_sfe_final.append(d[0]['surface_free_energy'][-1])
        print('\nPotential: %s\nSFE: %s'%(v['U'],d[0]['surface_free_energy'][-1]))
        plt.plot(U,pot_sfe_init,label='init')
        plt.plot(U,pot_sfe_final,label='final')
        potd = {
          'sfe_initial':pot_sfe_init,
          'sfe_final':pot_sfe_final,
          'potential':U,
         }
        pickle.dump(potd,open('pot_sfe.pkl','wb'))

        plt.legend()
        plt.savefig('pot_dependency')
        plt.close()

    return d



if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("input", type=str,
                        help="insert pickle file here")
    parser.add_argument( '-c','--code', type=str, default = 'qe',
                        help='which code type used: aims, cp2k, qe or lammps (default qe)')
    parser.add_argument( '-s','--structure', type=str,
                        help='manually define strucutre key')
    parser.add_argument( '-a','--surface_area', type=str,
                        help='manually define surface area')
    parser.add_argument( '--not_each_scf',  action='store_false',
                        help='calculate surface energy for each SCF step')
    parser.add_argument( '-U','--potential', type=float, default = 0.0,
                        help='Calculate SFE at given potential U')
    parser.add_argument( '-ue','--unit_energies', type=str,
                        default = 'None',
                        help='Give modified unit energies via a pickle dictionary (only LAMMPS)',
                        )
    parser.add_argument( '-vso','--vs_oxygen', action='store_true',
                        help='Calculate SFE vs. O2 not vs. H2O',
                        )

    args = parser.parse_args()
    data_raw = td.load_data(args.input)
    data_raw = deepcopy(data_raw)

    import components_CP2K as components 
    if args.code == 'aims':
        import components_AIMS as components 
        print('Loading AIMS components')

    elif args.code == 'aims-rpbe':
        import components_AIMS_RPBE as components 

    elif args.code == 'qe' or args.code == 'QE':
        import components_QE as components 
        print('Loading QE-RPBE components')
    elif args.code == 'qe-pbe':
        import components_QE_PBE as components 
        print('Loading QE-PBE components')
    elif args.code == 'lammps':
        print('Loading LAMMPS components')
        import components_LAMMPS as components 
        try:
            unit_energies = pickle.load(open(args.unit_energies,'rb'))
            components.RuO2['E'] = unit_energies['RuO2'] 
            print('Updated RuO2 unit energy')
        except:
            pass
        try:
            unit_energies = pickle.load(open(args.unit_energies,'rb'))
            components.O2['E'] = unit_energies['O2'] 
            print('Updated O unit energy')
        except:
            pass
            
    for k in data_raw:
        try:
            k['energy_scf']
        except:
            print('''
    No energy_scf column in data input. 
    Surface energy for each SCF step NOT calculated\n
                ''')
            args.not_each_scf = False

    if args.structure:
        for k in data_raw:
            k['structure'] = args.structure
    else:
        for k in data_raw:
            try:
                k['surface_area']+10
                k['structure'] = 'slab'
            except:
                k['structure'] = args.structure

    if args.surface_area:
        for k in data_raw:
            k['surface_area'] = float(args.surface_area)
    
    extract_surface_free_energy(
                                data_raw,
                                components,
                                each_scf = args.not_each_scf,
                                mute = False,
                                U = args.potential,
                                vso2 = args.vs_oxygen,
                                pot = False,
                                )
    
    if args.not_each_scf:
        data = pickle.load(open('surface_data.pkl','rb'))
        import matplotlib.pyplot as plt
        for k in data:
            plt.plot(k['surface_free_energy'],label = k['description'])
#        plt.legend()
        plt.xlabel('SCF step')
        plt.ylabel('Surface Free Energy [$eV/\AA$]')
        plt.savefig('sfe_vs_scf.png')
        plt.close()
