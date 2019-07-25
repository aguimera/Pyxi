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
    
#    plt.close('all')
    
    debug = False
    #llegir fitxer

#    Dictname = "F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DataSaved\VgsSweep_Test4x4_PhaseOpt_PostEth"
#    Dictname ="F:\\Dropbox (ICN2 AEMD - GAB GBIO)\\PyFET\\LuciaScripts\\Lucia\\DCTests\\RTest_Normal_VgsSweep_2Row_2Col_VcmToGnd"
    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DCTests\Transistor\19_07_2019\TEST_TransistorTest_DC_VgsSweep_8Row_1Col_VcmToVcm_20mV_35kHz_10sec_5sec"
    
    FileName = Dictname +'_0'+'.h5'
    hfile = h5py.File(FileName, 'r')
    RGain = 10e3
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
            axTemp.plot(Iin[:int(DemArgs['Samps'])*2], label=Lab)   
        
#%%      
#    fig, axTemp = plt.subplots()
#    for dem, DemArgs in ProcsDict.items():
#        Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['dInd'])
#        if FloatType:
#                LSB = 1
#        else:
#                LSB = DemArgs['LSB'][DemArgs['dInd']]
#                
#        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*LSB)/DemArgs['Gain']
#        axTemp.plot(Iin, label=Lab) 
#%%       
    Procs = []
    Labs = []
    AcqArgs = []
    DivProcs = 9 
    results = []
    fig, axPsd = plt.subplots() 
    
    for dem, DemArgs in ProcsDict.items():
#        if DemArgs['dInd'] != 1:
#            continue
        if DemArgs['Ac'] == 0:
            continue
#        if DemArgs['col'] != 'Col2':
#            continue
        if FloatType:
                LSB = 1
        else:
                LSB = DemArgs['LSB'][DemArgs['dInd']]
        print(DemArgs['dInd'])
        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*LSB)/DemArgs['Gain']
#        Iin = ((data[DemArgs['dset']][:, 0])*LSB)/DemArgs['Gain']
#        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*DemArgs['LSB'][DemArgs['dInd']])/DemArgs['Gain']
        
        Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['dInd'])
        print(Lab)     
        
        ff, psdadem = signal.welch(Iin, fs=DemArgs['Fs'], nperseg=nFFT, scaling='spectrum')            
        axPsd.loglog(ff, psdadem, label=Lab)
        
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
           
    xAxispar = 'Vgs' #modificar segun el AcqArgs para el que se quiera graficar
    
    fig, axR = plt.subplots()  
    for ind, (dem, lab, acqargs) in enumerate(zip(results, Labs, AcqArgs)):
        adems = np.abs(dem[DelaySamps:])
        x = np.arange(adems.size)
        ptrend = np.polyfit(x, adems, 1)
        trend = np.polyval(ptrend, x)
        ACarr = (2*ptrend[1])/np.sqrt(2)
#        R= (0.015/np.sqrt(2))/((np.max(np.abs(dem[DelaySamps:]))-np.mean(np.abs(dem[DelaySamps:])))/np.sqrt(2))
        R= (acqargs['Ac']/np.sqrt(2))/ACarr
        axR.plot(acqargs[xAxispar], R, '*')
        
#%%

    fig, axres = plt.subplots()  
    axres.set_title('Vgs')
    xAxispar = 'Vgs' #modificar segun el AcqArgs para el que se quiera graficar
    OutDict = {}

    Trts = set([('R'+str(a['dInd'])+a['col']) for a in AcqArgs])
    Vgs = np.sort(np.unique(([-a['Vgs'] for a in AcqArgs])))
    
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
#    plt.legend()