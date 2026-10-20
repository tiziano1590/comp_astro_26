# HIP 67522 c transit with batman, parameters read from the NASA Exoplanet Archive
# ps table (data/hip67522c_nasa_archive.csv, downloaded 20 Oct 2026).
#
# Why Barber et al. 2024 and not Chakraborty et al. 2026
#   Barber is the archive default (default_flag = 1) and is refereed (ApJL 973, L30),
#     while Chakraborty is still an arXiv preprint (2606.18045)
#   Barber gives the stellar Teff (5675 K) that the limb darkening below was chosen for,
#     so planet and star come from the same paper
#   the whole group (tasks F, G, H) uses the same solution
#   Chakraborty has tighter errors, so it is plotted as a comparison in transit_compare.py
#
# Why this file and not the TD table or the overview download
#   the ps table has pl_orblper (omega), which the TD table lacks, and batman needs omega
#     because Barber's eccentricity is not zero (e = 0.077)
#   one number per cell, so no splitting of "±" strings
#
# Limb darkening from Claret 2017 (TESS band, ATLAS, log g 4.5, solar metallicity,
# Teff 5675 K), not in the archive so it is set by hand

import csv
from pathlib import Path

import batman
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).parent

with open(HERE / "data" / "hip67522c_nasa_archive.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# take every parameter from one paper, mixing rows gives an orbit nobody fitted
row = next(r for r in rows if r["default_flag"] == "1")

params = batman.TransitParams()
params.t0 = 0.0                             # time of mid-transit [days]
params.per = float(row["pl_orbper"])        # orbital period [days]
params.rp = float(row["pl_ratror"])         # planet radius [stellar radii]
params.a = float(row["pl_ratdor"])          # semi-major axis [stellar radii]
params.inc = float(row["pl_orbincl"])       # inclination [deg]
params.ecc = float(row["pl_orbeccen"])
params.w = float(row["pl_orblper"])         # argument of periastron [deg]
params.u = [0.319, 0.268]
params.limb_dark = "quadratic"

print("Barber et al. 2024:", params.per, params.rp, params.a, params.inc, params.ecc, params.w)

t = np.linspace(-0.25, 0.25, 1000)  # days around mid-transit, the dip lasts ~6 hours
flux = batman.TransitModel(params, t).light_curve(params)

in_transit = t[flux < 1]
print(f"depth {100 * (1 - flux.min()):.3f} %, duration {24 * (in_transit[-1] - in_transit[0]):.2f} h")

plt.plot(t * 24, flux)            # hours are easier to read than days
plt.xlabel("Time from mid-transit [hours]")
plt.ylabel("Relative flux")
plt.title("HIP 67522 c (Barber et al. 2024)")
plt.savefig(HERE / "hip67522c_transit.png", dpi=150)
plt.show()
