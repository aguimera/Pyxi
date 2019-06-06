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
from scipy import integrate

import gc

def MeanStd(Data):
    keys = list(Data.keys())
    Arr = np.zeros([len(keys),len(Data[keys[0]])])
    for iT,TrtName in enumerate(Data.keys()):
        Arr[iT,:] = Data[TrtName]
    return np.mean(Arr,0), np.std(Arr,0)

def Integrate(PSD, Freqs, Fmin, Fmax):
    indices = np.where((Freqs >= Fmin) & (Freqs<=Fmax))
    Irms = np.sqrt(integrate.trapz(PSD[indices], Freqs[indices]))      
    return Irms 

if __name__ == '__main__':
    
    plt.close('all')
    
    debug = False
    #llegir fitxer

    Dictname = "F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DataSaved\TestVgsS_cript"
    FileName = Dictname +'_0'+'.h5'
    hfile = h5py.File(FileName, 'r')
    RGain = 10e3
    FsOut = 5e3

    FloatType=True
    
    RowNum = 8
    ColNum = 4
    ProcsDict = FileMod.ReadArchivo(Dictname)
    #lectura de parametres

    #Calcul de Parametres per a Demodulcio
    nFFT = 2**17
    DownFact = 100

    NoiseAnalysis = True
    indVgs = 2

    FitOrder = 3

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
    Procs = []
    Labs = []
    AcqArgs = []
    DivProcs = 9 
    results = []
    for dem, DemArgs in ProcsDict.items():
#En cas de penjar-se descomentar des de aqui: 
#        if DemArgs['dInd'] != 0:
#            continue
#        if DemArgs['col'] != 'Col1':
#            continue
#Fins aquí
        if FloatType:
                LSB = 1
        else:
                LSB = DemArgs['LSB'][DemArgs['dInd']]
        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*LSB)/DemArgs['Gain']

#        Iin = ((data[DemArgs['dset']][:, DemArgs['dInd']])*DemArgs['LSB'][DemArgs['dInd']])/DemArgs['Gain']

        Lab = str(DemArgs['dset']) +'-'+ str(DemArgs['dInd'])
        print(Lab)     
        DownFact = int(DemArgs['Fs']/FsOut)
        args=(Iin, DemArgs['Fs'], DemArgs['Fc'], int(DemArgs['Samps']), DownFact)
        Labs.append(Lab)
        Procs.append(args)
        AcqArgs.append(DemArgs)

#En cas de penjar-se comentar des de aqui:
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
        #Fins aquí


#En cas de penjar-se descomentar des de aqui:       
#    po = mp.Pool(len(Procs))
#    res = po.starmap(Dem.DemodProc, Procs)
#Fins aquí
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
    plt.close('all')
    fig, axres = plt.subplots()  
    axres.set_title('Vgs')
    xAxispar = 'Vgs' #modificar segun el AcqArgs para el que se quiera graficar
    OutDict = {}
    PsdAdem = {}
    IrmsAdem = {}
    
    Trts = set([('R'+str(a['dInd'])+a['col']) for a in AcqArgs])
    Vgs = np.sort(np.unique(([-a['Vgs'] for a in AcqArgs])))

    fig, axPsd = plt.subplots()  
    axPsd.set_title('Demod(V**2)')
    
    for t in Trts:
        OutDict[t] = np.array([])
        IrmsAdem[t] = np.array([])
        
    for ind, (dem, lab, acqargs) in enumerate(zip(results, Labs, AcqArgs)):
        TName = ('R'+str(acqargs['dInd'])+acqargs['col']) 
        
        adems = np.abs(dem[DelaySamps:])
        x = np.arange(adems.size)
        ptrend = np.polyfit(x, adems, 1)
        trend = np.polyval(ptrend, x)
        ACarr = (2*ptrend[1])/np.sqrt(2)
        
        if NoiseAnalysis == True:
            ff, psdadem = signal.welch(adems-trend, fs=FsOut, nperseg=nFFT, scaling='spectrum')
#            print(acqargs['Vgs'])
            if indVgs > len(Vgs):
                indVgs = len(Vgs)-1
                
            axPsd.loglog(ff, psdadem, label=lab)
            intNoise = Integrate(psdadem, ff, Fmin = 0.9, Fmax = 9)
            IrmsAdem[TName] = np.append(IrmsAdem[TName], intNoise)
                    

        OutDict[TName] = np.append(OutDict[TName], ACarr)
#        OutVar
#        axres.plot(acqargs[xAxispar], ACarr, '*')
#    axres.set_xlabel(xAxispar)


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
        

    
    plt.figure()
    for k in set(GoodTrt):
        plt.plot(Vgs,OutDict[k][:-1]*1e6, color = 'k', alpha = 0.3)
    plt.plot(([]),'k',label = 'individiual Ids')
    MeanIds, StdIds = MeanStd(OutDict)
    plt.plot(Vgs, MeanIds[:-1]*1e6,'--k', label = 'Mean Ids')
    plt.fill_between(Vgs, MeanIds[:-1]*1e6+StdIds[:-1]*1e6, MeanIds[:-1]*1e6-StdIds[:-1]*1e6, color='k', alpha=0.3)
    plt.legend()
    plt.xlabel('Vgs (V)')
     
    plt.ylabel('Ids (uA)')
    
    plt.figure()
    for k in set(GoodTrt):
        plt.semilogy(Vgs,IrmsAdem[k][:-1], color='b', alpha = 0.3)
    plt.semilogy(([]),'b',label = 'individiual Ids')
    MeanIrms, StdIrms = MeanStd(IrmsAdem)
    plt.semilogy(Vgs, MeanIrms[:-1],'--b', label='Mean Irms')
    plt.fill_between(Vgs, MeanIrms[:-1]+StdIrms[:-1], MeanIrms[:-1]-StdIrms[:-1], color = 'b', alpha = 0.3)
    plt.legend()
    plt.xlabel('Vgs (V)')
     
    plt.ylabel('Irms (A)')
    

    MeanderVal = np.zeros(len(Vgs))
    

    fit = {}
    fit2 = {}
    fit3 = {}
    der = {}    
    Urms = {}
    derVal = {}
    for k in set(GoodTrt):
        derVal[k] = np.zeros(len(Vgs))
        for ivg, vg in enumerate(Vgs):
    #             indices = (Vds >= vd - VFitRange) & (VgsRange <= vd + VFitRange)
    #             
             fit[vg] = np.polyfit(Vgs,
                        OutDict[k][:-1], FitOrder)
             VgsFit = np.linspace(Vgs[0],Vgs[-1],100)
     
             
             der[vg] = np.polyder(fit[vg], 1)
             derVal[k][ivg] = np.polyval(der[vg],vg)
             Vgsder = np.linspace(VgsFit[0],VgsFit[-1],100)

             plt.figure(13)                    
             plt.plot(VgsFit, np.polyval(fit[vg],VgsFit), Vgs, OutDict[k][:-1],'o' )
#             plt.figure(14)                    
#             plt.plot(Vgsder, np.polyval(der[vg],Vgsder))
        
        Urms[k] = IrmsAdem[k][:-1]/abs(derVal[k])
        plt.figure(15)
        plt.plot(Vgs, abs(derVal[k])*1000,'k', alpha = 0.3)
        plt.figure(16)
        plt.plot(Vgs, Urms[k],'k', alpha = 0.3)
        
        
    MeanDer, StdDer = MeanStd(derVal)

    plt.figure(15)
    plt.plot(Vgs, abs(MeanDer)*1000,'k')
    plt.fill_between(Vgs, abs(MeanDer)*1000+StdDer*1000, abs(MeanDer)*1000-StdDer*1000, color='k', alpha=0.3)
    plt.xlabel('Vgs (V)')
    plt.ylabel('Gm (mS)')
    
    MeanUrms = MeanIrms[:-1]/abs(MeanDer)
    StdUrms = np.sqrt((StdIrms[:-1]/MeanIrms[:-1])**2+(StdDer/MeanDer)**2)*MeanUrms
    
    plt.figure(16)
    plt.plot(Vgs, MeanUrms,'k')
    plt.fill_between(Vgs, MeanUrms+StdUrms, MeanUrms-StdUrms, color='k', alpha=0.3)
    plt.xlabel('Vgs (V)')
     
    plt.ylabel('Urms (V)')
    

    A=np.log10(np.ones((RowNum,ColNum))*5e-7)
    vmin=-6.8
    vmax=-3.8
    plt.figure()
    for col in np.arange(ColNum):
        Noise = {}
        for k in set(GoodTrt): 
            if int(k[-1]) == int(col+1):             
                Noise[k] = Urms[k][indVgs]


        for k in Noise.keys():
            ch = [int(k[1]),int(k[-1])]
            if np.log10(Noise[k])>=vmax:
                print(ch)
                A[ch[0],ch[1]-1] = vmin
            else:
                A[ch[0],ch[1]-1] = np.log10(Noise[k])
    
    plt.imshow(A, interpolation='nearest', vmin=vmin, vmax=vmax)
    plt.grid(True)
    cbar=plt.colorbar()
    plt.xlabel('column')
    plt.ylabel('row')
    cbar.set_label('log(Urms) BW=1-10Hz', rotation=270, labelpad=15)