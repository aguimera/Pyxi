# -*- coding: utf-8 -*-
"""
Created on Wed May  8 11:11:04 2019

@author: Lucia
"""

import h5py
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np

#import ForGitHub.FileBuffer as FB
import Pyxi.FileModule as FileMod

plt.close('all')
#FileData = "F:/Dropbox (ICN2 AEMD - GAB GBIO)/PyFET/LuciaScripts/Lucia/DataSaved/phaseTests/0406"
FileData = "C://Users//aemdlabs//Desktop//InVivo-LMU//Test_Save_NoDemod_0.h5"
#FileData = "DataSaved/phaseTests/0306/4Carr_70to115_NoComp_0.h5"
FileScopeConfig = "C://Users//aemdlabs//Desktop//InVivo-LMU//Test_Save_NoDemod.h5_ScopeConfig.dat"
FileDemodConfig = "C://Users//aemdlabs//Desktop//InVivo-LMU//Test_Save_NoDemod.h5_DemodConfig.dat"

hfile = h5py.File(FileData, 'r')

ScopeConfig = FileMod.ReadArchivo(FileScopeConfig)
DemodConfig = FileMod.ReadArchivo(FileDemodConfig)

Fs = ScopeConfig['FsScope']
Ts = 1/Fs
GainBoard = ScopeConfig['GainBoard']
LSB = np.array([])
for Row, pars in ScopeConfig['RowsConfig'].items():
    LSB = np.append(LSB, pars['AcqVRange']/(2**16))
Fact = LSB/GainBoard

fig, axPsdDS = plt.subplots()   
fig, axTempDS = plt.subplots()
#Per fer PSD dels fitxers de VgsSweep

for i in range(hfile['data'].shape[1]):

    ff, psd = signal.welch(hfile['data'][:, i]*Fact[i], fs=Fs, nperseg=2**21)
    axPsdDS.loglog(ff, psd)
    
    #50 samples to avoid the stabilization peack
    axTempDS.plot(np.arange(0, Ts*(hfile['data'].shape[0]-50), Ts), hfile['data'][50:, i]*Fact[i])