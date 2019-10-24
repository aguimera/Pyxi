# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 13:09:18 2019

@author: aemdlabs
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

import os
import h5py
import multiprocessing as mp

import Pyxi.DemodModule as Dem
import Pyxi.FileModule as FileMod

import gc

if __name__ == '__main__':
    
    plt.close('all')
    
    debug = False
    #llegir fitxer

#    Dictname = "F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DataSaved\VgsSweep_Test4x4_PhaseOpt_PostEth"
#    Dictname ="F:\\Dropbox (ICN2 AEMD - GAB GBIO)\\PyFET\\LuciaScripts\\Lucia\\DCTests\\RTest_Normal_VgsSweep_2Row_2Col_VcmToGnd"
#    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DCTests\Transistor\30_07_2019\Transistor_AcVgsSweep_8Row_1Col_VcmToVcm_20_100mV_35kHz_15sec_10sec_20VgsSw"
#<<<<<<< HEAD
##    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DCTests\Transistor\16_09_2019\Teset_wires"
##    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DCTests\Resistors\16_09_2019\4RArray_2k"
#    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Characterization\15_10_2019\SSP54348-T4-4x8-VgsSw-Ac0p01-Range1"
##    Name = "SSP54348-T2-2x2-AMmode_VgsSw_AcSw" 
#=======
#    Dictname=r"C:\Users\Lucia\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DCTests\Transistor\19_09_2019\SSP54348-T2-3x3-Sig10mVp10Hz"
#>>>>>>> f76cb064240fab7757d563ad181ce0ea254c7eb8
    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Lucia\DCTests\Transistors\24_10_2019\TestS4_NoDCFilt_t30_stab20"

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
        print('data load')
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
#<<<<<<< HEAD
#    DivProcs = 4 
#=======
    DivProcs = 9
#>>>>>>> f76cb064240fab7757d563ad181ce0ea254c7eb8
    results = []
    for dem, DemArgs in ProcsDict.items():
#        if DemArgs['dInd'] != 1:
#            continue
#        if DemArgs['col'] == 'Col1':
#            continue
        if DemArgs['Ac'] == 0:
            continue
        if FloatType:
                LSB = 1
        else:
                LSB = DemArgs['LSB'][DemArgs['dInd']]
        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*LSB)/DemArgs['Gain']
#        Iin = ((data[DemArgs['dset']][:, 0])*LSB)/DemArgs['Gain']
#        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*DemArgs['LSB'][DemArgs['dInd']])/DemArgs['Gain']

        Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['ProbeRow']+str(DemArgs['col']))
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

    xAxispar = 'Vgs' #modificar segun el AcqArgs para el que se quiera graficar

    fig, axR = plt.subplots()  
    axR.set_title('R')
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
    DataDict = {}
#    OutDataDict = {}
    
    Trts = set([(str(a['ProbeRow'])+a['col']) for a in AcqArgs])
    AcSw = np.unique([sw['dset'].split('Sw')[1] for sw in AcqArgs])
    Vgs = np.sort(np.unique(([-a['Vgs'] for a in AcqArgs])))
    
    for t in Trts:
        for Sw in AcSw:            
            OutDict[t + 'Ac' + str(Sw)] = np.array([])
    
    for lab in Labs:
        DataDict[lab] = np.array([])
        
#    for t in Vgs:
#        OutDataDict[t] = np.array([])
    
    for ind, (dem, lab, acqargs) in enumerate(zip(results, Labs, AcqArgs)):
        TName = (str(acqargs['ProbeRow'])+acqargs['col']) 
        
        adems = np.abs(dem[DelaySamps:])
        x = np.arange(adems.size)
        ptrend = np.polyfit(x, adems, 1)
        trend = np.polyval(ptrend, x)
        ACarr = (2*ptrend[1])/np.sqrt(2)
#        print(lab.split('Sw')[1])
        OutDict[TName+'Ac'+str((lab.split('Sw'))[1])] = np.append(OutDict[TName +'Ac'+str((lab.split('Sw'))[1])], ACarr)
        if lab.split('Sw')[2][0:3] == '002':
            plt.figure(20)
#            time = np.arange(0,len(adems)*1.0/FsOut,1.0/FsOut)
            ff, PSD = signal.welch(adems,FsOut,scaling='density',nperseg=2**13)
            plt.loglog(ff,PSD)
        DataDict[lab] = np.append(DataDict[lab], (adems-trend)) #no tiene en cuenta Vgs sweep CACA
#        OutDataDict[acqargs[xAxispar]] = np.append(OutDataDict[acqargs[xAxispar]], ACarr)
#        OutVar
        axres.plot(acqargs[xAxispar], ACarr, '*')
    axres.set_xlabel(xAxispar)


    plt.figure()
    GoodTrt = []
    for k, v in OutDict.items():
        if np.any(v>1e-7):
            GoodTrt.append(k)
        plt.plot(Vgs, v, label=k)
    print(set(GoodTrt))    
    plt.legend()
    plt.savefig('2x2.svg',format='svg',dpi=1200)
    
    plt.figure()
    for k in set(GoodTrt):
        plt.plot(Vgs,OutDict[k], label=k)
#    plt.legend()
#%%
    dtype = 'float64'
    MaxFileSize = 10000e6
    SaveName = Dictname + '_AcData'+'.h5'
    if os.path.isfile(SaveName):
        print('Remove File')
        os.remove(SaveName)
    
    SaveBuf = FileMod.FileBuffer(FileName=SaveName,
                                 MaxSize=MaxFileSize,
                                 nChannels=1,
                                 dtype=dtype) 
    for Name, data in OutDict.items():
        dem = data
        print(Name)
        dsetname = str(Name) 
        print(dsetname)
        SaveBuf.InitDset(dsetname)
        dem.resize(len(dem),1)
        demArray = np.array(dem)
        SaveBuf.AddSample(demArray)  
    SaveBuf.close()
    
    SaveName = Dictname + '_RowDemodData'+'.h5'
    if os.path.isfile(SaveName):
        print('Remove File')
        os.remove(SaveName)
        
    SaveBuf = FileMod.FileBuffer(FileName=SaveName,
                             MaxSize=MaxFileSize,
                             nChannels=1,
                             dtype=dtype) 
    for Name, data in DataDict.items():
        dem = data
        print(Name)
        dsetname = str(Name) 
        print(dsetname)
        SaveBuf.InitDset(dsetname)
        dem.resize(len(dem),1)
        demArray = np.array(dem)
        SaveBuf.AddSample(demArray)  
    SaveBuf.close()
