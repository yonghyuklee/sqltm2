from __future__ import print_function
import sys, os
import ase.spacegroup
import ase.build
p = os.path.dirname(os.path.abspath(__file__))
sys.path.append(p + '/../../tools')
import sqltm

H = ase.Atoms('H', magmoms=None)
O = ase.Atoms('O', magmoms=None)
H2 = ase.Atoms('H2', positions=[(-0.8, 0, 0), (0.8, 0, 0)], magmoms=[None, None])
OH = ase.build.molecule('OH', magmoms=[None, None])
H2O = ase.build.molecule('H2O', magmoms=[None, None, None])
O2 = ase.build.molecule('O2', magmoms=[None, None]) # singlet oxygen

metal = 'Ru'
#metal = 'Sn'

def unitcell(dft=None, basis=None):
    if dft == "PBE" and basis['O'] == "l_2" and basis[metal] == "l_1":
        # FHI-AIMS opt of conventional cell (PBE, light, O-l2, Ru-l1, smear=0.1, k_grid=11,11,15)
        a = 4.52741; c = 3.12188; x = 0.30565
    elif dft == "RPBE" and basis['O'] == "l_2" and basis[metal] == "l_1":
        # FHI-AIMS opt of conventional cell (RPBE, light, O-l2, Ru-l1, smear=0.1, k_grid=11,11,15)
        a = 4.5653; c = 3.13495160; x = 0.305438
    elif dft == "PBE" and basis['O'] == "t_2" and basis[metal] == "t_1":
        # FHI-AIMS opt of conventional cell (PBE, tight, O-t2, Ru-t1, smear=0.1, k_grid=11,11,15)
        a = 4.52295; c = 3.12015; x = 0.3057
    elif dft == "RPBE" and basis['O'] == "t_2" and basis[metal] == "t_1":
        # FHI-AIMS opt of conventional cell (PBE, tight, O-t2, Ru-t1, smear=0.1, k_grid=11,11,15)
        #a = 4.5612; c = 3.13314843; x = 0.305448
        # pw.x opt of 3x3x3 supercell (RPBE, ONCV, O-1.0, Ru-1.2)
        a = 4.55045276; c = 3.14126255; x = 0.30570967
    elif dft == None:
        # experiment Bolzan1997
        a = 4.4968; c = 3.1049; x = 0.3053
        print("slab: using experimental cell parameters")
    else:
        print("ERROR (unitcell): no parameters for dft/basis available")
        raise SystemExit
    cell = ase.spacegroup.crystal([metal, 'O'], basis=[(0 ,0, 0), (x, x, 0.0)], spacegroup=136, cellpar=[a, a, c, 90, 90, 90])
    cell.set_tags(range(len(cell)))
    return cell

def bulk(task):
    tasks = []
    ## [ 0 0 0 ]
    t = { 'description': "0-0-0_b", 'orientation': [0,0,0], 'supercell': [1,1,1] }
    tasks.append(sqltm.merge_dicts(task,t))
    ## [ 0 0 1 ]
    t = { 'description': "0-0-1_b", 'orientation': [0,0,1], 'supercell': [1,1,1] }
    tasks.append(sqltm.merge_dicts(task,t))
    ## [ 0 1 0 ]
    t = { 'description': "0-1-0_b", 'orientation': [0,1,0], 'supercell': [1,1,1] }
    tasks.append(sqltm.merge_dicts(task,t))
    ## [ 1 0 1 ]
    t = { 'description': "1-0-1_b", 'orientation': [1,0,1], 'supercell': [1,1,1] }
    tasks.append(sqltm.merge_dicts(task,t))
    ## [ 1 1 0 ]
    t = { 'description': "1-1-0_b", 'orientation': [1,1,0], 'supercell': [1,1,1] }
    tasks.append(sqltm.merge_dicts(task,t))
    ## [ 1 1 1 ]
    t = { 'description': "1-1-1_b", 'orientation': [1,1,1], 'supercell': [1,1,1] }
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 0 0 1 ]
def slab_001(task):
    tasks = []
    ### stoichiometric
    t = { 'description': "0-0-1_0",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### 001-0-X2a0
    t = { 'description': "0-0-1_0-X2a0",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 001-0-X2a0-X4f0
    t = { 'description': "0-0-1_0-X2a0-X4f0",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 001-0-X4f0
    t = { 'description': "0-0-1_0-X4f0",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 001-0-X4f0-X4f1
    t = { 'description': "0-0-1_0-X4f0-X4f1",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def H_slab_001(task):
    tasks = []
    ### 1 x H on 001_0-X2a0 surface Obr sublayer
    t = { 'description': "0-0-1_0-X2a0-H_Obrsub",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 1, 'limit': 1 },
        'dist': 1.0,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H on 001-0-X2a0-X4f0 surface Obrsub
    t = { 'description': "0-0-1_0-X2a0-X4f0-H_Obrsub",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 1, 'limit': 1 },
        'dist': 1.0,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def OH_slab_001(task):
    tasks = []
    OH_A1 = OH.copy()
    OH_A1.rotate(120, 'x')
    OH_A1.rotate(-45, 'z')
    OH_A2 = OH.copy()
    OH_A2.rotate(-30, 'x')
    OH_A2.rotate(-45, 'z')
    OH_A3 = OH.copy()
    OH_A3.rotate(120, 'x')
    OH_B1 = OH.copy()
    OH_B1.rotate(80, 'x')
    OH_B1.rotate(-100, 'z')
    ### 1 x OH on 001_0-X2a0 surface Obr // generate *O-O & *H
    t = { 'description': "0-0-1_0-X2a0-OH_Obr-down",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': OH_A1, 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -0.5, -0.5 ],
        'dist': 1.2,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 001_0-X2a0 surface Obr // Norskov solvated model 
    t = { 'description': "0-0-1_0-X2a0-OH_Obr-up",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': OH_A2, 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -0.5, -0.5 ],
        'dist': 1.2,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 001_0-X2a0-X4f0 surface Obr
    t = { 'description': "0-0-1_0-X2a0-X4f0-OH_Obr-down",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': OH_A3, 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -0.2, -1.0 ],
        'dist': 0.7,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 001_0-X2a0 surface Obr // Norskov solvated model 
    t = { 'description': "0-0-1_0-X2a0-X4f0-OH_Obr-up",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': OH_A2, 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -0.5, -0.5 ],
        'dist': 1.2,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 001_0-X2a0 surface Obrsub
    t = { 'description': "0-0-1_0-X2a0-X4f0-OH_Obrsub",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': OH_B1, 
        'selector': { 'symbol': 'O', 'layer': 1, 'limit': 1 },
        'dist': 1.2,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def H2O_slab_001(task):
    tasks = []
    H2O_A = H2O.copy()
    H2O_A.rotate(60, 'x')
    H2O_A.rotate(-45, 'z')
    H2O_B = H2O.copy()
    H2O_B.rotate(-70, 'x')
    H2O_B.rotate(-15, 'z')
    
    ### 1 x H2O on 001_0-X2a0 surface Obr
    t = { 'description': "0-0-1_0-X2a0-H2O_Obr",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': H2O_A, 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -0.5, -0.5 ],
        'dist': 1.2,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H2O on 001_0-X2a0-X4f0 at X4f0 site
    t = { 'description': "0-0-1_0-X2a0-X4f0-H2O_X4f0",
            'orientation': [0,0,1], 'supercell': [1,1,6], 'termination': 0 }
    t['add_species'] = [{ 
        'species': H2O_B, 
        'selector': { 'symbol': metal, 'layer': 1 },
        'xy': [ 0.9, 0.9 ],
        'dist': 1.5,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 0 1 0 ]
def slab_010(task):
    tasks = []
    ### O poor
    t = { 'description': "0-1-0_0",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 0 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### stoichiometric
    t = { 'description': "0-1-0_1",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 1 }
    tasks.append(sqltm.merge_dicts(task,t))
    #### O rich 
    t = { 'description': "0-1-0_2",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    tasks.append(sqltm.merge_dicts(task,t))
    #### 100_2-X4f3
    t = { 'description': "0-1-0_2-X4f3",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    #### 100_2-X4f0-2x1
    t = { 'description': "0-1-0_2-X4f0-1x2",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def H_slab_010(task):
    tasks = []
    #### 1 x H on 100_2-H_Otop surface
    t = { 'description': "0-1-0_2-H_Otop",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.6, -0.4 ],
        'dist': -0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.6, 0.4 ],
        'dist': -0.1,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    #### 1 x H on 100_2-H_Otop surface
    t = { 'description': "0-1-0_2-H_Otop-1x2",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [3] },
        'xy': [ -0.6, -0.4 ],
        'dist': -0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [2] },
        'xy': [ 0.6, 0.4 ],
        'dist': -0.1,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    #### 1 x H on 100_2-H_Obr surface
    t = { 'description': "0-1-0_2-H_Obr",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ 0.6, 0.4 ],
        'dist': 0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ -0.6, -0.4 ],
        'dist': 0.1,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    #### 1 x H on 100_2-H_Obr surface
    t = { 'description': "0-1-0_2-H_Obr-1x2",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 1, 'tag': [4] },
        'xy': [ 0.6, 0.4 ],
        'dist': 0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 1, 'tag': [15] },
        'xy': [ -0.6, -0.4 ],
        'dist': 0.1,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def OH_slab_010(task):
    tasks = []
    OH_A1 = OH.copy()
    OH_A1.rotate(40, 'x')
    OH_B1 = OH.copy()
    OH_B1.rotate(-100, 'y')
    OH_B1.rotate(220, 'z')
    OH_B2 = OH_B1.copy()
    OH_B2.positions[:,0] = -OH_B1.positions[:,0]
    OH_B2.positions[:,1] = -OH_B1.positions[:,1]
    OH_C = OH.copy()
    OH_C.rotate(-100, 'x')
    ### 1 x OH on 100_2 surface Otop
    t = { 'description': "0-1-0_2-OH_Otop-down",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': OH_C, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.0, 0.8 ],
        'dist': 0.9,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 100_2 surface Otop
    t = { 'description': "0-1-0_2-OH_Otop-down-1x2",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': OH_C, 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ 0.0, 0.8 ],
        'dist': 0.9,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 100_2 surface Obr
    t = { 'description': "0-1-0_2-OH_Obr-down",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': OH_B1, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ 0.6, 0.4 ],
        'dist': 1.2,
        'side': 'top'
        },{ 
        'species': OH_B2, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ -0.6, -0.4 ],
        'dist': 1.2,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 100_2 surface Obr
    t = { 'description': "0-1-0_2-OH_Obr-down-1x2",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': OH_B1, 
        'selector': { 'symbol': 'O', 'layer': 1, 'tag': [4] },
        'xy': [ 0.6, 0.4 ],
        'dist': 1.2,
        'side': 'top'
        },{ 
        'species': OH_B2, 
        'selector': { 'symbol': 'O', 'layer': 1, 'tag': [15] },
        'xy': [ -0.6, -0.4 ],
        'dist': 1.2,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 100_2 surface Obr
    t = { 'description': "0-1-0_2-OH_Obr-up",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': OH_A1, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ 0.0, 0.7 ],
        'dist': 0.9,
        'side': 'top'
        },{ 
        'species': OH_A1, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ 0.0, 0.7 ],
        'dist': 0.9,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def H2O_slab_010(task):
    tasks = []
    H2O_A1 = H2O.copy()
    H2O_A1.rotate(-90, 'y')
    H2O_A2 = H2O_A1.copy()
    H2O_A2.positions[:,0] = -H2O_A1.positions[:,0]
    H2O_A2.positions[:,1] = -H2O_A1.positions[:,1]
    H2O_B1 = H2O.copy()
    H2O_B1.rotate(-40, 'x')
    H2O_B1.rotate(-90, 'y')
    H2O_B2 = H2O_B1.copy()
    H2O_B2.positions[:,0] = -H2O_B2.positions[:,0]
    H2O_B2.positions[:,1] = -H2O_B2.positions[:,1]
    ### 1 x H2O on 100_2 surface Obr
    t = { 'description': "0-1-0_2-H2O_Obr-1",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H2O_B1, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'dist': 1.2,
        'side': 'top'
        },{ 
        'species': H2O_B2, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'dist': 1.2,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H2O on 100_2 surface Obr
    t = { 'description': "0-1-0_2-H2O_Obr-2",
          'orientation': [0,1,0], 'supercell': [1,1,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H2O_A1, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'dist': 1.2,
        'side': 'top'
        },{ 
        'species': H2O_A2, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'dist': 1.2,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def OH_CUS_slab_010(task):
    tasks = []
    OH_C = OH.copy()
    OH_C.rotate(-100, 'x')
    OH_C.rotate(180, 'z')
    #### 100_2-X4f0-2x1 + H
    t = { 'description': "0-1-0_2-X4f0-1x2-OH_cus",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [13] },
        'side': 'top'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [12] },
        'side': 'bottom'
        }]
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.6, -0.4 ],
        'dist': -0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.6, 0.4 ],
        'dist': -0.1,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    #### O rich + H
    t = { 'description': "0-1-0_2-OH_cus",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [3] },
        'xy': [ -0.6, -0.4 ],
        'dist': -0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [2] },
        'xy': [ 0.6, 0.4 ],
        'dist': -0.1,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    #### 1 x H on 100_2-H_Otop surface + H
    t = { 'description': "0-1-0_2-H_Otop-1x2-OH_cus",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.6, -0.4 ],
        'dist': -0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.6, 0.4 ],
        'dist': -0.1,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 100_2 surface Otop + H
    t = { 'description': "0-1-0_2-OH_Otop-down-1x2-OH_cus",
          'orientation': [0,1,0], 'supercell': [1,2,6], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [3] },
        'xy': [ -0.6, -0.4 ],
        'dist': -0.1,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [2] },
        'xy': [ 0.6, -0.4 ],
        'dist': -0.1,
        'side': 'bottom'
        },{ 
        'species': OH_C, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [13] },
        'xy': [ 0.0, -0.8 ],
        'dist': 0.9,
        'side': 'top'
        },{ 
        'species': OH_C, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [12] },
        'xy': [ 0.0, -0.8 ],
        'dist': 0.9,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 0 1 1 ]
def slab_011(task):
    tasks = []
    ### O super poor
    t = { 'description': "0-1-1_0",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 0 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### 101_0-X2a0
    t = { 'description': "0-1-1_0-X2a0",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{'selector': { 'symbol': metal, 'layer': 0, 'limit': 1 }}]
    tasks.append(sqltm.merge_dicts(task,t))
    ### stoichiometric (O at bridge site)
    t = { 'description': "0-1-1_1",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 1 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### O poor (there are 2 equivalent O positions, just pick one)
    t = { 'description': "0-1-1_1-X4f0",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 1 }
    #t['rm_atoms'] = [{'selector': { 'symbol': 'O', 'layer': 0, 'tag': [2,3,4,5] }}]
    t['rm_atoms'] = [{'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4,5] }}]
    tasks.append(sqltm.merge_dicts(task,t))
    ### O super rich (2x1 terminal O) 
    t = { 'description': "0-1-1_2",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### 101_2-X4f1
    t = { 'description': "0-1-1_2-X4f1",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['rm_atoms'] = [{'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] }}]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 0 1 1 ]
def H_slab_011(task):
    tasks = []
    ### 101_2-H_Otop
    t = { 'description': "0-1-1_2-H_Otop",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] },
        'xy': [ 0.3, 0.9 ],
        'dist': 0.0,
        'side': 'top'
        },{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] },
        'xy': [ -0.3, -0.9 ],
        'dist': 0.0,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 101_2-X4f1-H_Otop
    t = { 'description': "0-1-1_2-X4f1-H_Otop",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.8, -0.5, ],
        'dist': 0.0,
        'side': 'top'
        },{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.8, 0.5, ],
        'dist': 0.0,
        'side': 'bottom'
        }]
    t['rm_atoms'] = [{'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] }}]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 0 1 1 ]
def OH_slab_011(task):
    tasks = []
    OH_A1 = OH.copy()
    OH_A1.rotate(-100, 'y')
    OH_A1.rotate(-30, 'z')
    OH_A2 = OH.copy()
    OH_A2.rotate(-100, 'y')
    OH_A2.rotate(150, 'z')
    OH_B1 = OH.copy()
    OH_B1.rotate(40, 'y')
    OH_B1.rotate(-30, 'z')
    OH_B2 = OH.copy()
    OH_B2.rotate(40, 'y')
    OH_B2.rotate(150, 'z')
    OH_C1 = OH.copy()
    OH_C1.rotate(100, 'y')
    OH_C1.rotate(-30, 'z')
    OH_C2 = OH.copy()
    OH_C2.rotate(100, 'y')
    OH_C2.rotate(150, 'z')
    OH_D1 = OH.copy()
    OH_D1.rotate(-40, 'y')
    OH_D1.rotate(-30, 'z')
    OH_D2 = OH.copy()
    OH_D2.rotate(-40, 'y')
    OH_D2.rotate(150, 'z')

    ### 101_2-OH_Otop
    t = { 'description': "0-1-1_2-OH_Otop_down",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_A1,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] },
        'xy': [ -0.5, 0.2 ],
        'dist': 0.9,
        'side': 'top'
        },{
        'species': OH_A2,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] },
        'xy': [ 0.5, -0.2 ],
        'dist': 0.9,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 101_2-OH_Otop
    t = { 'description': "0-1-1_2-OH_Otop_up",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_B1,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] },
        'xy': [ -0.5, 0.2 ],
        'dist': 0.9,
        'side': 'top'
        },{
        'species': OH_B2,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] },
        'xy': [ 0.5, -0.2 ],
        'dist': 0.9,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 101_2-X4f1-OH_Otop
    t = { 'description': "0-1-1_2-X4f1-OH_Otop_down",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_C1,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.7, -0.3 ],
        'dist': 0.4,
        'side': 'top'
        },{
        'species': OH_C2,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.7, 0.3 ],
        'dist': 0.4,
        'side': 'bottom'
        }]
    t['rm_atoms'] = [{'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] }}]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 101_2-X4f1-OH_Otop
    t = { 'description': "0-1-1_2-X4f1-OH_Otop_up",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_D1,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.5, -0.2 ],
        'dist': 0.9,
        'side': 'top'
        },{
        'species': OH_D2,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.5, 0.2 ],
        'dist': 0.9,
        'side': 'bottom'
        }]
    t['rm_atoms'] = [{'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] }}]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 0 1 1 ]
def H2O_slab_011(task):
    tasks = []
    H2O_A1 = H2O.copy()
    H2O_A1.rotate(-45, 'x')
    H2O_A2 = H2O.copy()
    H2O_A2.rotate(-45, 'x')
    H2O_A2.rotate(180, 'z')
    H2O_B1 = H2O.copy()
    H2O_B1.rotate(-60, 'x')
    H2O_B1.rotate(-120, 'z')
    H2O_B2 = H2O.copy()
    H2O_B2.rotate(-60, 'x')
    H2O_B2.rotate(60, 'z')
    ### 101_2-H2O_Otop
    t = { 'description': "0-1-1_2-H2O_Otop",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H2O_A1,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4,5] },
        'xy': [ 0.3, 0.5 ],
        'dist': 0.8,
        'side': 'top'
        },{
        'species': H2O_A2,
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4,5] },
        'xy': [ -0.3, -0.5 ],
        'dist': 0.8,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 101_2-X4f1-H2O_Otop
    t = { 'description': "0-1-1_2-X4f1-H2O_Otop",
          'orientation': [0,1,1], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H2O_B1,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.5, -0.5 ],
        'dist': 0.8,
        'side': 'top'
        },{
        'species': H2O_B2,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.5, 0.5 ],
        'dist': 0.8,
        'side': 'bottom'
        }]
    t['rm_atoms'] = [{'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4, 5] }}]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 1 1 0 ]
def slab_110(task):
    tasks = []
    ### O poor (flat), two different Ru sites
    t = { 'description': "1-1-0_0",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X2a0
    t = { 'description': "1-1-0_0-X2a0",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X2a1
    t = { 'description': "1-1-0_0-X2a1",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X4f2
    t = { 'description': "1-1-0_0-X4f2",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X2a0-X4f2
    t = { 'description': "1-1-0_0-X2a0-X4f2",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X2a1-X4f2
    t = { 'description': "1-1-0_0-X2a1-X4f2",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 1 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X2a0-X4f2-X4f3
    t = { 'description': "1-1-0_0-X2a0-X4f2-X4f3",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X2a0-X4f2-X4f3
    t = { 'description': "1-1-0_0-X2a1-X4f2-X4f3",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 1 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_0-X4f2-X4f3
    t = { 'description': "1-1-0_0-X4f2-X4f3",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    t = { 'description': "1-1-0_1",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 1 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### O rich, bridge + terminal O
    t = { 'description': "1-1-0_2",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_2-X4f1
    t = { 'description': "1-1-0_2-X4f1",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_2-X4f0
    t = { 'description': "1-1-0_2-X4f0-2x1",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 2 }
    t['rm_atoms'] = [{
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def H_slab_110(task):
    tasks = []
    ### 1 x H on 110_0-X2a0 Obr
    t = { 'description': "1-1-0_0-X2a0-H_Obr",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 2 },
        'xy': [ -0.5, -0.5 ],
        'dist': 0.7,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H on 110_2 Otop
    t = { 'description': "1-1-0_2-H_Otop",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -1.0, 0.0 ],
        'dist': 0.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H on 110_2 Otop
    t = { 'description': "1-1-0_2-H_Otop-2x1",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -1.0, 0.0 ],
        'dist': 0.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def OH_slab_110(task):
    tasks = []
    OH_A = OH.copy()
    OH_A.rotate(-90, 'y')
    OH_B = OH.copy()
    OH_B.rotate(-120, 'x')
    OH_C = OH.copy()
    OH_C.rotate(40, 'x')
    ### 1 x OH on 110_0-X2a0 Ru2a1
    t = { 'description': "1-1-0_0-X2a0-OH_Ru2a1",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['add_species'] = [{
        'species': OH_A,
        'selector': { 'symbol': metal, 'layer': 0 },
        'xy': [ -0.7, 0.0 ],
        'dist': 1.6,
        'side': 'both'
        },]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 110_2 surface Otop site
    t = { 'name': '110', 'description': "1-1-0_2-OH_Otop_down",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_B,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.0, 0.9 ],
        'dist': 0.7,
        'side': 'both'
        },]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 110_2 surface Otop site
    t = { 'name': '110', 'description': "1-1-0_2-OH_Otop_down-2x1",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_B,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ 0.0, 0.9 ],
        'dist': 0.7,
        'side': 'both'
        },]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 110_2 surface Otop site
    t = { 'name': '110', 'description': "1-1-0_2-OH_Otop_up",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_C,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.0, 0.7 ],
        'dist': 1.0,
        'side': 'both'
        },]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x OH on 110_2 surface Otop site
    t = { 'name': '110', 'description': "1-1-0_2-OH_Otop_up-2x1",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_C,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ 0.0, 0.7 ],
        'dist': 1.0,
        'side': 'both'
        },]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def H2O_slab_110(task):
    tasks = []
    H2O_A = H2O.copy()
    H2O_A.rotate(-45, 'z')
    H2O_B = H2O.copy()
    H2O_B.rotate(-45, 'x')
    ### 1 x H2O on 110_0-X2a0 Obr
    t = { 'description': "1-1-0_0-X2a0-H2O_Obr",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 0 }
    t['add_species'] = [{
        'species': H2O_A,
        'selector': { 'symbol': 'O', 'layer': 2, 'limit': 1 },
        'dist': 1.2,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0, 'tag': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H2O on 110_2 surface Otop site
    t = { 'name': '110', 'description': "1-1-0_2_H2O_Otop", 'sort': False,
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H2O_B,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.0, 0.8 ],
        'dist': 0.9,
        'side': 'both'
        },]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H2O on 110_2 surface Obr site
    t = { 'name': '110', 'description': "1-1-0_2_H2O_Obr", 'sort': False,
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H2O_B,
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ 0.0, 0.8 ],
        'dist': 0.9,
        'side': 'both'
        },]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def OH_CUS_slab_110(task):
    tasks = []
    OH_B = OH.copy()
    OH_B.rotate(-120, 'x')
    ### 1 x OH on 110_2 surface Otop site
    t = { 'name': '110', 'description': "1-1-0_2-OH_Otop_down-2x1-OH_cus",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': OH_B,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ 0.0, 0.9 ],
        'dist': 0.7,
        'side': 'both'
        },{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 2, 'tag': 7 },
        'xy': [ 0.0, 0.7 ],
        'dist': 0.7,
        'side': 'top'
        },{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 2, 'tag': 8 },
        'xy': [ 0.0, 0.7 ],
        'dist': 0.7,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H on 110_2 Otop
    t = { 'description': "1-1-0_2-2-2x1-OH_cus",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0 , 'limit': 1},
        'xy': [ -1.0, 0.0 ],
        'dist': 0.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x H on 110_2 Otop
    t = { 'description': "1-1-0_2-H_Otop-2x1-OH_cus",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -1.0, 0.0 ],
        'dist': 0.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 110_2-X4f0
    t = { 'description': "1-1-0_2-X4f0-2x1-OH_cus",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 2 }
    t['rm_atoms'] = [{
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'side': 'both'
        }]
    t['add_species'] = [{
        'species': H,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.0, 0.7 ],
        'dist': 0.7,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

# this creates a (symmetric) slab model according to Valdez2007
# on the 110 surface, specifically the OOH structure is problematic
# there are 3 different minima: 
# O
# H-up: OOH-up-Os
# H-down: OOH-down-Ot
# H-down: OOH-down-Ob
# x
# H-up: OOH-up-Ru
# H-down: OOH-down-Ru
# H-down: OOH-down-Ob (may split and protonate Ob)
def norskov(task):
    tasks = []
    OH_1 = OH.copy()
    OH_1.rotate(-40, 'x')
    OH_A = OH.copy()
    OH_A.rotate(120.0, 'x')
    OH_A.rotate(-90, 'z')
    OH_B = OH.copy()
    OH_B.rotate(10.0, 'y')
    OH_B.rotate(-40.0, 'x')
    OH_C = OH.copy()
    OH_C.rotate(90.0+40.0, 'x')
    ### OOH, x OOH-down-Ru
    t = { 'name': '110', 'description': "1-1-0_1_OOH_down_Ru", 'sort': False,
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': 0 },
        'dist': 1.9,
        'side': 'both'
        },{ 
        'species': OH_A,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -1.0, 0.3 ],
        'dist': 0.7,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### OOH, x OOH-down-Os
    t = { 'name': '110', 'description': "1-1-0_1_OOH_up_Os", 'sort': False,
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': 0 },
        'dist': 1.9,
        'side': 'both'
        },{ 
        'species': OH_B,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [-0.7,  -0.9 ],
        'dist': 0.7,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### OOH, x OOH-down-Ob
    t = { 'name': '110', 'description': "1-1-0_1_OOH_down_Ob", 'sort': False,
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': 0 },
        'dist': 1.9,
        'side': 'both'
        },{ 
        'species': OH_C,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -0.5, -1.1 ],
        'dist': 0.7,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### OH,x
    t = { 'name': '110', 'description': "1-1-0_1_OH",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{ 
        'species': OH_1, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': 0 },
        'dist': 2.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### O,x
    t = { 'name': '110', 'description': "1-1-0_1_O",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{ 
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': 0 },
        'dist': 2.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### x,x
    t = { 'name': '110', 'description': "1-1-0_1",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    tasks.append(sqltm.merge_dicts(task,t))
    # Oxygen covered surface as used by Rossmeisl2007
    ### OOH, O OOH-down-Ot
    t = { 'name': '110', 'description': "1-1-0_1_OOH_O_down_Ot", 'sort': False,
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': [0,5] },
        'dist': 1.9,
        'side': 'both'
        },{ 
        'species': OH_A,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -1.0, 0.3 ],
        'dist': 0.7,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### OOH, O OOH-up-Os
    t = { 'name': '110', 'description': "1-1-0_1_OOH_O_up_Os", 'sort': False,
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': [0,5] },
        'dist': 1.9,
        'side': 'both'
        },{ 
        'species': OH_B,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [-0.7,  -0.9 ],
        'dist': 0.7,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### OOH, O OOH-down-Ob
    t = { 'name': '110', 'description': "1-1-0_1_OOH_O_down_Ob", 'sort': False,
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': [0,5] },
        'dist': 1.9,
        'side': 'both'
        },{ 
        'species': OH_C,
        'selector': { 'symbol': 'O', 'layer': 0, 'limit': 1 },
        'xy': [ -0.5, -1.1 ],
        'dist': 0.7,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### OH,O
    t = { 'name': '110', 'description': "1-1-0_1_OH_O",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{ 
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': 5 },
        'dist': 2.0,
        'side': 'both'
        },{ 
        'species': OH_1, 
        'selector': { 'symbol': metal, 'layer': 2, 'tag': 0 },
        'dist': 2.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### O,O
    t = { 'name': '110', 'description': "1-1-0_1_O_O",
          'orientation': [1,1,0], 'supercell': [2,1,3], 'termination': 1 }
    t['add_species'] = [{ 
        'species': O, 
        'selector': { 'symbol': metal, 'layer': 1, 'tag': [0, 5]},
        'dist': 2.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 1 x O on 110_2 Otop
    t = { 'description': "1-1-0_2-OO",
          'orientation': [1,1,0], 'supercell': [1,1,3], 'termination': 2 }
    t['add_species'] = [{
        'species': O,
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.0, -1.0 ],
        'dist': 1.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 1 1 1 ]
def slab_111(task):
    tasks = []
    ### O poor
    t = { 'description': "1-1-1_0",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 0 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_1
    t = { 'description': "1-1-1_1",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 1 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### O super rich
    t = { 'description': "1-1-1_1-X2a0",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 1, 'rmlayers': [-12, 12] }
    tasks.append(sqltm.merge_dicts(task,t))
    ### stoichiometric
    t = { 'description': "1-1-1_2",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 2 }
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_2-X2a1
    t = { 'description': "1-1-1_2-X2a1",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 2 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_2-X2a1
    t = { 'description': "1-1-1_2-X2a1-X4f2",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 2 }
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        },{ 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': [4] },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### O rich
    t = { 'description': "1-1-1_3",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 3 }
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

## [ 1 1 1 ]
def H_slab_111(task):
    tasks = []
    ### 111_1-X2a0-H_Otop
    t = { 'description': "1-1-1_1-X2a0-H_Otop",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 1, 'rmlayers': [-12, 12] }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'dist': 1.0,
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_1-X2a0-H_Obr
    t = { 'description': "1-1-1_1-X2a0-H_Obr",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 1, 'rmlayers': [-12, 12] }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 2, 'tag': 4 },
        'dist': 1.0,
        'side': 'top'
        },{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 2, 'tag': 5 },
        'dist': 1.0,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_2-X2a1-H_Otop
    t = { 'description': "1-1-1_2-X2a1-H_Otop",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ 0.8, -0.6 ],
        'dist': 0.3,
        'side': 'both'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def OH_slab_111(task):
    tasks = []
    OH_A1 = OH.copy()
    OH_A1.rotate(120, 'x')
    OH_A1.rotate(90, 'z')
    OH_A2 = OH_A1.copy()
    OH_A2.positions[:,0] = -OH_A1.positions[:,0]
    OH_A2.positions[:,1] = -OH_A1.positions[:,1]
    OH_B1 = OH.copy()
    OH_B1.rotate(-45, 'x')
    OH_B1.rotate(90, 'z')
    OH_B2 = OH_B1.copy()
    OH_B2.positions[:,0] = -OH_B1.positions[:,0]
    OH_B2.positions[:,1] = -OH_B1.positions[:,1]
    OH_C1 = OH.copy()
    OH_C1.rotate(100, 'x')
    OH_C1.rotate(-30, 'z')
    OH_C2 = OH_C1.copy()
    OH_C2.positions[:,0] = -OH_C1.positions[:,0]
    OH_C2.positions[:,1] = -OH_C1.positions[:,1]
    OH_D1 = OH.copy()
    OH_D1.rotate(100, 'x')
    OH_D1.rotate(-130, 'z')
    OH_D2 = OH_D1.copy()
    OH_D2.positions[:,0] = -OH_D1.positions[:,0]
    OH_D2.positions[:,1] = -OH_D1.positions[:,1]
    ### 111_1-X2a0-OH_Otop
    t = { 'description': "1-1-1_1-X2a0-OH_Otop_down-2",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 1, 'rmlayers': [-12, 12] }
    t['add_species'] = [{ 
        'species': OH_A1, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.9, 0.0 ],
        'dist': 0.5,
        'side': 'top'
        },{ 
        'species': OH_A2, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.9, 0.0 ],
        'dist': 0.5,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_1-X2a0-OH_Otop
    t = { 'description': "1-1-1_1-X2a0-OH_Otop_up-2",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 1, 'rmlayers': [-12, 12] }
    t['add_species'] = [{ 
        'species': OH_B1, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ 0.5, 0.0 ],
        'dist': 1.0,
        'side': 'top'
        },{ 
        'species': OH_B2, 
        'selector': { 'symbol': 'O', 'layer': 0 },
        'xy': [ -0.6, 0.0 ],
        'dist': 1.0,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_2-X2a1-OH_Obr
    t = { 'description': "1-1-1_2-X2a1-OH_Obr1_down-1",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 2 }
    t['add_species'] = [{ 
        'species': OH_C1, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': 4 },
        'xy': [ -0.3, -0.3 ],
        'dist': 0.9,
        'side': 'top'
        },{ 
        'species': OH_C2, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': 5 },
        'xy': [ 0.4, 0.4 ],
        'dist': 0.9,
        'side': 'bottom'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_2-X2a1-OH_Obr
    t = { 'description': "1-1-1_2-X2a1-OH_Obr2_down-1",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 2 }
    t['add_species'] = [{ 
        'species': OH_D1, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': 5 },
        'xy': [ -0.3, 0.3 ],
        'dist': 0.9,
        'side': 'top'
        },{ 
        'species': OH_D2, 
        'selector': { 'symbol': 'O', 'layer': 0, 'tag': 4 },
        'xy': [ 0.4, -0.4 ],
        'dist': 0.9,
        'side': 'bottom'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks

def H2O_slab_111(task):
    tasks = []
    H2O_A1 = H2O.copy()
    H2O_A1.rotate( -30, 'x')
    H2O_A1.rotate( 90, 'z')
    H2O_A2 = H2O_A1.copy()
    H2O_A2.positions[:,0] = -H2O_A1.positions[:,0]
    H2O_A2.positions[:,1] = -H2O_A1.positions[:,1]
    H2O_B1 = H2O.copy()
    H2O_B1.rotate( 30, 'x')
    H2O_B1.rotate( 145, 'z')
    H2O_B2 = H2O_B1.copy()
    H2O_B2.positions[:,0] = -H2O_B1.positions[:,0]
    H2O_B2.positions[:,1] = -H2O_B1.positions[:,1]
    ### 111_1-X2a0-H2O_Obr
    t = { 'description': "1-1-1_1-X2a0-H2O_Obr-2",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 1, 'rmlayers': [-12, 12] }
    t['add_species'] = [{ 
        'species': H2O_A1, 
        'selector': { 'symbol': 'O', 'layer': 2, 'tag': 4 },
        'dist': 1.2,
        'side': 'top'
        },{ 
        'species': H2O_A2, 
        'selector': { 'symbol': 'O', 'layer': 2, 'tag': 5 },
        'dist': 1.2,
        'side': 'bottom'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    ### 111_2-X2a1-H2O_Otop
    t = { 'description': "1-1-1_2-X2a1-H2O_Otop-2",
          'orientation': [1,1,1], 'supercell': [1,1,2], 'termination': 2 }
    t['add_species'] = [{ 
        'species': H2O_B1, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ 0.2, 0.3 ],
        'dist': 1.2,
        'side': 'top'
        },{ 
        'species': H2O_B2, 
        'selector': { 'symbol': 'O', 'layer': 1 },
        'xy': [ -0.2, -0.3 ],
        'dist': 1.2,
        'side': 'bottom'
        }]
    t['rm_atoms'] = [{ 
        'selector': { 'symbol': metal, 'layer': 0 },
        'side': 'both'
        }]
    tasks.append(sqltm.merge_dicts(task,t))
    return tasks
