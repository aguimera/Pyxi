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
#Folder = r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Lucia\GuiSweeps\Test_29_10_2019"
Folder = r"C:\Users\Lucia\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Lucia\GuiSweeps\Test_29_10_2019"
File = "\Test1_4seconds"
FileData = Folder + File +"_0.h5"
#FileData = "DataSaved/phaseTests/0306/4Carr_70to115_NoComp_0.h5"
FileGenConfig = Folder + File + ".h5_GenConfig.dat"
FileScopeConfig = Folder + File + ".h5_ScopeConfig.dat"
FileSweepConfig = Folder + File + ".h5_SweepsConfig.dat"

hfile = h5py.File(FileData, 'r')
data = {}
DataSets = []
for k in hfile.keys():
        print('data load')
        data[k] = hfile[k].value
        DataSets.append(k)
 
ScopeConfig = FileMod.ReadArchivo(FileScopeConfig)
GenConfig = FileMod.ReadArchivo(FileGenConfig)
SweepConfig = FileMod.ReadArchivo(FileSweepConfig)

Fs = ScopeConfig['FsScope']
Ts = 1/Fs
GainBoard = ScopeConfig['GainBoard']

Fact = 1/GainBoard

#fig, axPsdDS = plt.subplots()   
#fig, axTempDS = plt.subplots()
#Per fer PSD dels fitxers de VgsSweep

for DS in DataSets:
    plt.figure(DS)
    if DS == 'data':
        continue
    for i in range(hfile[DS].shape[1]):
    
        ff, psd = signal.welch(hfile[DS][:, i]*Fact, fs=Fs, nperseg=2**21)
        plt.loglog(ff, psd)
        
        #50 samples to avoid the stabilization peack
        plt.plot(np.arange(0, Ts*(hfile[DS].shape[0]-50), Ts), hfile[DS][50:, i]*Fact)

hfile.close()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    