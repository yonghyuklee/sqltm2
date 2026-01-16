#!/usr/bin/python
from __future__ import print_function
import sys, os
import argparse
import pickle
import scipy as sp

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import thermo as td
import janaf
import components_CP2K as components 
import xls_output_plots as xop
#import components_AIMS as components 

def print_rocksteady(fn, s, cell='../IrO2.in'):
    # yaml dict for rocksteady
    data = { 
        'unit_cell': str(cell),
        'surfaces': []
    }
    for facet in s.keys():
        data['surfaces'].append({ 
            'description': str(s[facet]['description']),
            'miller_index': str(facet),
            'termination': int(s[facet]['termination']),
            'energy': float(s[facet]['surface_free_energy'])
        })
    with open(fn, 'w') as fd:
        fd.write(yaml.dump(data, default_flow_style=False))
    return


# Sun/Reuter
#zpe_slab = [ 0.015, 0.0 ] # per angstrom^2
zpe_slab = [ 0.30601, 0.0 ] # Sun2003 0.015 eV/A^2
pressure = 0.03166 # equal to liquid water at 298K
temp = 298.15
pH = 0.0
aH = td.pH_to_a(pH)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("input", type=str,
                        help="  insert pickle file here")
    parser.add_argument( '-a','--surface_area', type=str,
                        help='manually define surface area')

    args = parser.parse_args()
    
    data_raw = td.load_data(args.input)
    
    #td.write_images(data_raw)
    #raise SystemExit

    if args.surface_area:
        for k in data_raw:
            k['surface_area'] = float(args.surface_area)

#   compute density of H atoms per surface unit
    td.H_density(data_raw)

    comp = [
            components.Hp,
            components.H2O, 
            components.IrO2, 
            components.RuO2, 
            components.SnO2, 
            ]

    comp,basis = components.update_components(comp)
    activity = components.get_activity(comp, {'Hp':aH, 'O2': pressure})

    U = sp.arange(0.0, 0.1, 0.1)
    min_energy = []
    min_free_energy = []
    min_energy_O = []
    min_free_energy_O = []

    var = []
    for i in range(len(U)):
        var.append({
            'U': U[i],
            'T': temp,
            'basis': basis,
            'components': comp,
            'a': activity,
        })

    data_u = []
    for v in var:
        d = td.compute_surface_energy(v, data_raw, zpe_slab)
        data_u.append(d)
      #  emin, gmin = td.min_surface_energy(d)
      #  emin_O, gmin_O = td.min_surface_energy([ x for x in d if 'H' not in x['description']])
      #  min_energy.append(emin)
      #  min_free_energy.append(gmin)
      #  min_energy_O.append(emin_O)
      #  min_free_energy_O.append(gmin_O)
    
    # write yml file with surfaces of lowest energy
#   for v,gmin in zip(var,min_free_energy_O):
#    for v,gmin in zip(var,min_free_energy):
#        print_rocksteady("U_"+str(v['U'])+".yml", gmin, cell="../IrO2.in")

#   convert data to table (columns) 
    columns =  ['U', 'T'] + [ d['description'] for d in data_raw ]
    s = 'internal_energy'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, key=s)
    s = 'total_energy'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, data_xls=data_xls, key=s)
    s = 'entropy'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, data_xls=data_xls, key=s)
    s = 'zpe'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, data_xls=data_xls, key=s)
    s = 'enthalpy'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, data_xls=data_xls, key=s)
    s = 'free_energy'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, data_xls=data_xls, key=s)
    s = 'surface_enthalpy'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, data_xls=data_xls, key=s)
    s = 'surface_free_energy'
    data_xls = xop.make_table(data_u, var, columns, sheet=s, data_xls=data_xls, key=s)
    xop.create_xls("pH_" + str(pH) + "_" + str(temp) + "K.xlsx", data_xls, columns)
    
    s = 'surface_free_energy'
#    xop.plot_facets(data_xls, s)
#    xop.plot_min(data_xls, s, min_free_energy, suffix="_G")
#    xop.plot_min(data_xls, s, min_free_energy_O, suffix="_G_oxygen")
