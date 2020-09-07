# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 13:00:44 2020

@author: Lucia
"""

import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

Vds = 0.5
fc = 30e3
Fs = 2e6
GenSize = int(2e3)
n = round(GenSize*(fc/Fs))
fc = Fs*(n/GenSize)
nFFT = 2**17
t = np.arange(0, ((1/Fs)*(GenSize)), 1/Fs)
PotNoise = 0.25
MinRange = -0.5
MaxRange = 0.5
noise = np.random.normal(0,PotNoise,(GenSize+1))

Sinus = Vds*np.sin(fc*2*np.pi*t)
SatSinus = np.clip(a=Sinus,
                   a_min=MinRange,
                   a_max=MaxRange
                   )

ffSin, PSDSinus =  signal.welch(x=Sinus,
                         fs=Fs,
                         nperseg=nFFT,
                         scaling='density',
                         )

ffSat, PSDSatSinus =  signal.welch(x=SatSinus,
                            fs=Fs,
                            nperseg=nFFT,
                            scaling='density',
                            )

plt.figure()
plt.plot(Sinus)
plt.plot(SatSinus)

plt.figure()
plt.semilogx(ffSin,PSDSinus)
plt.semilogx(ffSat, PSDSatSinus)

plt.figure()
plt.hist(Sinus, bins=100)
plt.hist(SatSinus, bins=100)

plt.figure()
plt.hist(PSDSinus, bins=100)
plt.hist(PSDSatSinus, bins=100)

HistSinus = np.histogram(a=Sinus,
                         bins=100)
HistSat = np.histogram(a=SatSinus,
                       bins=100)

VrmsSinus = (1/np.sqrt(2))*np.max(Sinus)
VrmsSat = (1/np.sqrt(2))*np.max(SatSinus)

OrdHSinusPos = -np.sort(-HistSinus[0][int(len(HistSinus[0])/2):])
OrdHSinusNeg = -np.sort(-HistSinus[0][:int(len(HistSinus[0])/2)])
OrdHSatPos = -np.sort(-HistSat[0][int(len(HistSat[0])/2):])
OrdHSatNeg = -np.sort(-HistSat[0][:int(len(HistSat[0])/2)])

if OrdHSinusPos[1] < 0.45*OrdHSinusPos[0]:
    print('Signal Saturated')
    print('Vrms', VrmsSinus)
elif OrdHSinusNeg[1] < 0.45*OrdHSinusNeg[0]:
    print('Signal Saturated')
    print('Vrms', VrmsSinus)
else: 
    print('Signal Not Saturated')
    print('Vrms', VrmsSinus)

if OrdHSatPos[1] < 0.45*OrdHSatPos[0]:
    print('Signal Saturated')
    print('Vrms', VrmsSat)
elif OrdHSatNeg[1] < 0.45*OrdHSatNeg[0]:
    print('Signal Saturated') 
    print('Vrms', VrmsSat)
else: 
    print('Signal Not Saturated')
    print('Vrms', VrmsSat)