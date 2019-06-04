# -*- coding: utf-8 -*-
"""
Created on Mon May 20 17:34:25 2019

@author: Lucia
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
    
#    plt.close('all')
    
    debug = False
    
    #llegir fitxer

    Dictname = "F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DataSaved\Test_4x4_NoPhaseOpt"
    FileName = Dictname +'_0'+'.h5'
    hfile = h5py.File(FileName, 'r')
    FsOut = 5e3
    
    FloatType=True
    
    ProcsDict = FileMod.ReadArchivo(Dictname)
    #lectura de parametres

    #Calcul de Parametres per a Demodulcio
    nFFT = 2**17
    DownFact = 100


    data = {}
    for k in hfile.keys():
        data[k] = hfile[k].value
    hfile.close()
#%%
    if debug == True:    
        fig, axTemp = plt.subplots()
        fig, axPsd = plt.subplots() 
        for dem, DemArgs in ProcsDict.items():
            if FloatType:
                LSB = 1
            else:
                LSB = DemArgs['LSB'][DemArgs['dInd']]
            Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*LSB)/DemArgs['Gain']
            
            Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['dInd'])
            print(Lab)
            
            ff, psdadem = signal.welch(Iin, fs=DemArgs['Fs'], nperseg=nFFT, scaling='spectrum')            
            axPsd.loglog(ff, psdadem, label=Lab)
            Peaks = signal.find_peaks(psdadem, threshold=1e-17)
    
            for pi in Peaks[0]:
                print(ff[pi], '-->>', np.sqrt(psdadem[pi]))
                axPsd.plot(ff[pi], psdadem[pi], 'k*')
            axTemp.plot(Iin[:int(DemArgs['Samps']*2)], label=Lab)   

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
        if FloatType:
                LSB = 1
        else:
                LSB = DemArgs['LSB'][DemArgs['dInd']]
        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*LSB)/DemArgs['Gain']
#        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*DemArgs['LSB'][DemArgs['dInd']])/DemArgs['Gain']
        Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['dInd'])
        print(Lab)            
        if ((DemArgs['dInd'] == 0) and (DemArgs['col']=='Col1')):
            plt.figure()
            ff, psdadem = signal.welch(Iin, fs=DemArgs['Fs'], nperseg=nFFT, scaling='spectrum')            
            plt.loglog(ff, psdadem, label=Lab)
            plt.figure()
            plt.plot(Iin)
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
    axres.set_title('Ac')
    xAxispar = 'Ac' #modificar segun el AcqArgs para el que se quiera graficar
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
    axres.set_title('Ac')
    xAxispar = 'Ac' #modificar segun el AcqArgs para el que se quiera graficar
    OutDict = {}

    Trts = set([('R'+str(a['dInd'])+a['col']) for a in AcqArgs])
    Ac = np.sort(np.unique(([a['Ac'] for a in AcqArgs])))
    
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
        plt.plot(Ac,OutDict[k], label=k)
    plt.legend()   
    