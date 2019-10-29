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
Folder = r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Lucia\GuiSweeps\Test_29_10_2019"
File = "\Test2_2seconds"
FileData = Folder + File +"_0.h5"
#FileData = "DataSaved/phaseTests/0306/4Carr_70to115_NoComp_0.h5"
FileGenConfig = Folder + File + ".h5_GenConfig.dat"
FileScopeConfig = Folder + File + ".h5_ScopeConfig.dat"
FileSweepConfig = Folder + File + ".h5_SweepsConfig.dat"

hfile = h5py.File(FileData, 'r')
data = {}
for k in hfile.keys():
        print('data load')
        data[k] = hfile[k].value
hfile.close()
 
ScopeConfig = FileMod.ReadArchivo(FileScopeConfig)
GenConfig = FileMod.ReadArchivo(FileGenConfig)
SweepConfig = FileMod.ReadArchivo(FileSweepConfig)

Fs = ScopeConfig['FsScope']
Ts = 1/Fs
GainBoard = ScopeConfig['GainBoard']

Fact = 1/GainBoard

fig, axPsdDS = plt.subplots()   
fig, axTempDS = plt.subplots()
#Per fer PSD dels fitxers de VgsSweep

for i in range(hfile['data'].shape[1]):

    ff, psd = signal.welch(hfile['data'][:, i]*Fact, fs=Fs, nperseg=2**21)
    axPsdDS.loglog(ff, psd)
    
    #50 samples to avoid the stabilization peack
    axTempDS.plot(np.arange(0, Ts*(hfile['data'].shape[0]-50), Ts), hfile['data'][50:, i]*Fact)