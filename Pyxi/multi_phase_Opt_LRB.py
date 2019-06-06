# -*- coding: utf-8 -*-
"""
Created on Mon Jun  3 15:58:43 2019

@author: Lucia
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from fractions import gcd
from scipy.optimize import minimize

plt.close("all")

def multi_phase_sim(fiq, phiq, fs, nsteps):
    """
    Multi-phase multi-carrier DT simulation
    
    fiq: I/Q carrier frequencies
    phiq: I/Q carrier phases [deg]
    fs: sampling frequency
    nsteps: number of samples

    t: time vector
    xout: output waveform
    """
    t = np.arange(nsteps) / fs
    xout = np.zeros(nsteps)

    for n in np.arange(fiq.size):
        xout = xout + np.sin(2*np.pi*(fiq[n]*t+phiq[n]/360.0))
        xout = xout + np.cos(2*np.pi*(fiq[n]*t+phiq[n]/360.0))
    
    return t, xout

# Carrier frequencies and simulation time

fs = 20e6           # Sampling frequency

#fiq = 1e3*np.array([170, 180, 190, 200])
fiq = 1e3*np.array([70, 85, 100, 115])

fgcd = fiq[0]   # gcd of all I/Q carrier frequencies
for n in range(1, fiq.size):
    fgcd = gcd(fgcd, fiq[n])
    
nsteps = int(fs / fgcd) # Overall cycle length

def mycost(x, fiq=fiq, fs=fs, nsteps=nsteps):
    t, xout = multi_phase_sim(fiq, x, fs, nsteps)
    #Calcula histograma amb 100 bins
    hist = np.histogram(xout, bins=100)
    #hacer max-min(de histograma[1],que son los bins) + desviacion estandar del histograma[1], que son counts)
    return ((np.max(hist[1])-np.min(hist[1])) + np.std(hist[0]))

x0 = np.zeros(4)
xppopt = 100

for k in range(100000):
    for n in np.arange(4):
        x0[n] = np.random.uniform(-180.0, 180.0)
    t, xout = multi_phase_sim(fiq, x0, fs, nsteps)
    xpp = np.max(xout)-np.min(xout)
    if xpp < xppopt:
        xppopt = xpp
        phiqopt = x0
#x0 = phiq
phiqloop = phiqopt
for l in range(10):
    res = minimize(mycost, phiqloop, method='SLSQP',
                   bounds=tuple([(-180.0, 180.0) for i in range(4)]),
                   options={'maxiter':1e3,
                            'ftol':1e-20,
                            'disp': True})
    phiqloop = res.x
                   
phiq = phiqloop

to, xo = multi_phase_sim(fiq, np.zeros(4), fs, nsteps)
topt, xoopt = multi_phase_sim(fiq, phiqopt, fs, nsteps)
t, xout = multi_phase_sim(fiq, phiq, fs, nsteps)

plt.figure()
plt.plot(to, xo, 'r')
plt.plot(topt, xoopt, 'y.')
plt.plot(t, xout, 'g-.')

plt.figure()
plt.hist(xo, bins=100)
plt.hist(xout, bins=100)