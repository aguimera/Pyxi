# -*- coding: utf-8 -*-
"""
Created on Tue May  7 17:18:31 2019

@author: Lucia
"""

import h5py
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np

import FileBuffer as FB

plt.close('all')

FileData = "DataSaved/4Cols_7Rows_100_125_150_175_25mV_Demod_0.h5"
FileScopeConfig = "DataSaved/4Cols_7Rows_100_125_150_175_25mV_Demod.h5_ScopeConfig.dat"
FileDemodConfig = "DataSaved/4Cols_7Rows_100_125_150_175_25mV_Demod.h5_DemodConfig.dat"

hfile = h5py.File(FileData, 'r')

ScopeConfig = FB.ReadArchivo(FileScopeConfig)
DemodConfig = FB.ReadArchivo(FileDemodConfig)

#Fs = ScopeConfig['FsScope']
FsDSDemod = DemodConfig['FsDemod']/DemodConfig['DSFact']
TsDSDemod = 1/FsDSDemod

fig, axPsdDS = plt.subplots()   
fig, axTempDS = plt.subplots()
#Per fer PSD dels fitxers de VgsSweep

for i in range(hfile['data'].shape[1]):

    ff, psd = signal.welch(hfile['data'][:, i], fs=FsDSDemod, nperseg=2**21)
    axPsdDS.loglog(ff, psd)
    
    #50 samples to avoid the stabilization peack
    axTempDS.plot(np.arange(0, TsDSDemod*(hfile['data'].shape[0]-50), TsDSDemod), hfile['data'][50:, i])