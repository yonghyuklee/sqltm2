import os
import scipy as sp
from scipy.interpolate import UnivariateSpline

kJ_mol_to_eV = 0.01036410 

janaf_path = os.path.dirname(__file__)

# entropy (TS)
def mu(fn, c=1.0):
    columns=(0,2,4)
    work = sp.loadtxt(os.path.join(janaf_path, fn + '.dat'), usecols=columns)
    # compute spline for electrochemical potential mu(T, p=const.)
    dmu_raw = c*(work[:,2] - work[:,0]*work[:,1]/1000.0)*kJ_mol_to_eV
    dmu = UnivariateSpline(work[:,0], dmu_raw, s=0)
    return dmu

# free energy of formation
def g(fn, c=1.0):
    columns=(0,6)
    work = sp.loadtxt(os.path.join(janaf_path, fn + '.dat'), usecols=columns)
    g = UnivariateSpline(work[:,0], c*work[:,1]*kJ_mol_to_eV, s=0)
    return g

# free enthalpy of formation
def h(fn, c=1.0):
    columns=(0,5)
    work = sp.loadtxt(os.path.join(janaf_path, fn + '.dat'), usecols=columns)
    h = UnivariateSpline(work[:,0], c*work[:,1]*kJ_mol_to_eV, s=0)
    return h


