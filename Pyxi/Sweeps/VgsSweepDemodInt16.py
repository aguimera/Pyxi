# -*- coding: utf-8 -*-
"""
Created on Tue May 14 16:48:19 2019

@author: aemdlabs
"""


import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

import h5py
import multiprocessing as mp

import Pyxi.DemodModule as Dem
import Pyxi.FileModule as FileMod

import gc

if __name__ == '__main__':
    
    plt.close('all')
    
    debug = False
    #llegir fitxer

    Dictname = 'VgSweep_LRB__Carr1_Row1_Fs1e6_Integer_compressed'
    FileName = Dictname +'.h5'
    hfile = h5py.File(FileName, 'r')
    RGain = 10e3
    FsOut = 5e3

    ProcsDict = FileMod.ReadArchivo(Dictname)
    #lectura de parametres

    #Calcul de Parametres per a Demodulcio
    nFFT = 2**17
    DownFact = 100

#%%
    if debug == True:
        fig, axTemp = plt.subplots()
        fig, axPsd = plt.subplots() 
        for dem, DemArgs in ProcsDict.items():
            Iin = hfile[DemArgs['dset']][:, DemArgs['dInd']]/RGain
            Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['dInd'])
            print(Lab)
            
            ff, psdadem = signal.welch(Iin, fs=DemArgs['Fs'], nperseg=nFFT, scaling='spectrum')            
            axPsd.loglog(ff, psdadem, label=Lab)
            Peaks = signal.find_peaks(psdadem, threshold=1e-17)
    
            for pi in Peaks[0]:
                print(ff[pi], '-->>', np.sqrt(psdadem[pi]))
                axPsd.plot(ff[pi], psdadem[pi], 'k*')
            axTemp.plot(Iin[:int(DemArgs['Samps'])*2], label=Lab)   


    data = {}
    for k in hfile.keys():
        data[k] = hfile[k].value
    hfile.close()
        
#%%      
    Procs = []
    Labs = []
    AcqArgs = []
    DivProcs = 9 
    results = []
    for dem, DemArgs in ProcsDict.items():
#        if DemArgs['dInd'] != 0:
#            continue
#        if DemArgs['col'] != 'Col1':
#            continue

        Iin = (data[DemArgs['dset']][:, DemArgs['dInd']])*DemArgs['LSB'][DemArgs['dInd']]/RGain

        Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['dInd'])
        print(Lab)     
        DownFact = int(DemArgs['Fs']/FsOut)
        args=(Iin, DemArgs['Fs'], DemArgs['Fc'], int(DemArgs['Samps']), DownFact)
        Labs.append(Lab)
        Procs.append(args)
        AcqArgs.append(DemArgs)

        if len(Procs) > DivProcs:
            print(len(Procs))
            po = mp.Pool(len(Procs))
            res = po.starmap(Dem.DemodProc, Procs)
            for r in res:
                results.append(r)
            po.close()
            Procs = []
            print('Collect', gc.collect())
            
        if len(Procs) > 0:        
            print(len(Procs))
            po = mp.Pool(len(Procs))
            res = po.starmap(Dem.DemodProc, Procs)
            for r in res:
                results.append(r)
            po.close()
            Procs = []
            print('Collect', gc.collect())   
        

#%%
#    plt.close('all')
    DelaySamps = 200
           
    fig, axres = plt.subplots()  
    axres.set_title('Vgs')
    xAxispar = 'Vgs' #modificar segun el AcqArgs para el que se quiera graficar
    for ind, (dem, lab, acqargs) in enumerate(zip(results, Labs, AcqArgs)):
        adems = np.abs(dem[DelaySamps:])
        x = np.arange(adems.size)
        ptrend = np.polyfit(x, adems, 1)
        trend = np.polyval(ptrend, x)
        ACarr = (2*ptrend[1])/np.sqrt(2)
        
        axres.plot(acqargs[xAxispar], ACarr, '*')
    axres.set_xlabel(xAxispar)
    
#%%

    fig, axres = plt.subplots()  
    axres.set_title('Vgs')
    xAxispar = 'Vgs' #modificar segun el AcqArgs para el que se quiera graficar
    OutDict = {}

    Trts = set([('R'+str(a['dInd'])+a['col']) for a in AcqArgs])
    Vgs = np.sort(np.unique(([a['Vgs'] for a in AcqArgs])))
    
    for t in Trts:
        OutDict[t] = np.array([])
    
    for ind, (dem, lab, acqargs) in enumerate(zip(results, Labs, AcqArgs)):
        TName = ('R'+str(acqargs['dInd'])+acqargs['col']) 
        
        adems = np.abs(dem[DelaySamps:])
        x = np.arange(adems.size)
        ptrend = np.polyfit(x, adems, 1)
        trend = np.polyval(ptrend, x)
        ACarr = (2*ptrend[1])/np.sqrt(2)
        
        OutDict[TName] = np.append(OutDict[TName], ACarr)
#        OutVar
        axres.plot(acqargs[xAxispar], ACarr, '*')
    axres.set_xlabel(xAxispar)


    plt.figure()
    GoodTrt = []
    for k, v in OutDict.items():
        if np.any(v>1e-7):
            GoodTrt.append(k)
        plt.plot(v, label=k)
    print(set(GoodTrt))    
    plt.legend()
    
    
    plt.figure()
    for k in set(GoodTrt):
        plt.plot(Vgs,OutDict[k][:-1], label=k)
    plt.legend()