# python module to work with NIST-JANAF tables
http://kinetics.nist.gov/janaf/

kJ/mol -> eV: *0.01036410
Enthalpy Reference Temperature = Tr = 298.15 K
Standard State Pressure = p° = 0.1 MPa
col 1,2,3,4 in J/(K*mol), col 5,6,7,8 in kJ/mol

## Adding new tables:
- comment (#) lines with invalid data (at least the table header)

## Redundant columns
JANAF tables contain redundant information
col:  3      +    5 (*1000) / 1  = 3
-[G-H(Tr)]/T + H-H(Tr)*1000/T(K) = S [J/mol*K]		

show redundance in table with gnuplot:
p "JANAF_O2.txt" u 1:3 w lp, "" u 1:4 w lp, "" u 1:($4 + $5*1000/$1) w p

## plot mu(O2) vs T
p "JANAF_O2.txt" u 1:($5 - $1*$3/1000)/2*0.01036410  w lp

## chemical potential
col:  5      + 1*3 (/1000)
H-H(Tr) - T(K)*S/1000 -> G = H - TS = U + pV - TS [kJ/mol]
