# -*- coding: utf-8 -*-
"""
Created on Tue May  7 17:18:31 2019

@author: Lucia
"""

import h5py
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np

import Pyxi.FileModule as FileMod

plt.close('all')

Folder = r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Lucia\GuiSweeps\Test30_10_2019"
File = "\TestSweepDemod_2_4seconds"
FileData = Folder + File +"_0.h5"

FileGenConfig = Folder + File + ".h5_GenConfig.dat"
FileScopeConfig = Folder + File + ".h5_ScopeConfig.dat"
FileDemodConfig = Folder + File + ".h5_DemodConfig.dat"
FileSweepConfig = Folder + File + ".h5_SweepsConfig.dat"

hfile = h5py.File(FileData, 'r')

ScopeConfig = FileMod.ReadArchivo(FileScopeConfig)
GenConfig = FileMod.ReadArchivo(FileGenConfig)
SweepConfig = FileMod.ReadArchivo(FileSweepConfig)
DemodConfig = FileMod.ReadArchivo(FileDemodConfig)

#Fs = ScopeConfig['FsScope']
FsDSDemod = DemodConfig['FsDemod']/DemodConfig['DSFact']
TsDSDemod = 1/FsDSDemod

data = {}
DataSets = []
for k in hfile.keys():
        print('data load')
        data[k] = hfile[k].value
        DataSets.append(k)
    
    
for DS in DataSets:
#    if DS == 'data':
#        continue
    for i in range(hfile[DS].shape[1]):
    
        ff, psd = signal.welch(hfile[DS][:, i], fs=FsDSDemod, nperseg=2**21)
        plt.figure(DS)
        plt.loglog(ff, psd)
        
        #50 samples to avoid the stabilization peack
        plt.figure(DS+'temp')
        plt.plot(np.arange(0, TsDSDemod*(hfile[DS].shape[0]-50), TsDSDemod), hfile[DS][50:, i])

hfile.close()