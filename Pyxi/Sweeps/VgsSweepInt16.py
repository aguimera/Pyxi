# -*- coding: utf-8 -*-
"""
Created on Thu May 16 14:16:02 2019

@author: aemdlabs
"""

import numpy as np
import time

import os

import Gen_Scope_Classes as Gen_Scope
import Pyxi.FileModule as FileMod
import FMacqThread as FMmod

if __name__ == '__main__':
    
    #File To Save
    Dictname ='VgSweep_LRB__Carr1_Row1_Fs1e6_Integer_compressed'
    FileName = Dictname +'.h5'
    
    if os.path.isfile(FileName):
        print('Remove File')
        os.remove(FileName)
    
    #Inicialització Scope    
    PXIScope = 'PXI1Slot4'
    OptionsScope = {'simulate': False,
                    'driver_setup': {'Model': '5105',
                                     'BoardType': 'PXIe',
                                     },
                   }
    ScopeSig = Gen_Scope.SigScope(resource_name=PXIScope,
                                  options=OptionsScope)
    #Calculas per al Scope
    GenFs = 20e6 #La Fs de generació es necessita aqui per asegurar que sigui multiple de FsScope
    ScopeFs = 500e3
    nFs = round(GenFs/ScopeFs)
    ScopeFs = GenFs/nFs
    tFetch = 10
    NumFetch = 1
    BufferSize = round(tFetch*ScopeFs)
    tFetch = BufferSize/ScopeFs
    ScopeOffset = int(ScopeFs*6) # Change by time
    Rows = [0, 1, 2, 3, 4, 5, 6, 7]
    rangeScope = 6  #options 0.05, 0.2, 1, 6, 30
    LSB = rangeScope/(2**16)
    PCBGain = 10e3
    MaxFileSize = 500e6
    dtype = 'int16'
    
    FileBuf = FileMod.FileBuffer(FileName=FileName,
                                 MaxSize=MaxFileSize,
                                 nChannels=len(Rows),
                                 dtype=dtype)  
    
    #Dades per crear ColsConfig i cridar a "Columns()"    
    #Modifica Cols segons els generadores que es vulguin utilitzar
#    #Cols = (('Col1', 'PXI1Slot2', 0, 0), 
#            ('Col2', 'PXI1Slot2', 1, 1), 
#            ('Col3', 'PXI1Slot3', 0, 2), 
#            ('Col4', 'PXI1Slot3', 1, 3)
##            )                      -- e.g. Standard form with all Cols
    Cols = (('Col1', 'PXI1Slot2', 0, 0), 
            ('Col2', 'PXI1Slot2', 1, 1), 
            ('Col3', 'PXI1Slot3', 0, 2), 
            ('Col4', 'PXI1Slot3', 1, 3)
            )   
    numSweeps = 10
    GenSize = 20e3
    Ts = 1/GenFs
    t = np.arange(0, Ts*GenSize, Ts)        
    A = [0.0125, 0.0125, 0.0125, 0.0125]  
    
    #definir les Fc que es volen utilitzar
    Fc=np.array([70e3, 85e3, 100e3, 115e3])

    for ind, f in enumerate(Fc):
        nc = round((GenSize*f)/GenFs)
        Fc[ind] =  (nc*GenFs)/GenSize
        
        
    #deefinir vector de CMVoltage (Vgs) que es vol fer el sweep
    CMVoltage = np.linspace(0, -0.4, num=numSweeps)
    CMVoltage = np.append(CMVoltage, 0)
    #Es crea una Cols Config que es configurará per cada Sweep amb la freq correcta
#    ColsConfig={'Col1':{'Frequency': Fc0,
#                        'amplitude': A[0],
#                        'Gain': 0.5,
#                        'Resource': 'PXI1Slot2'
#                        'Index':0},
#                'Col2':{'Frequency': Fc1,
#                        'amplitude': A[1],
#                        'Gain': 0.5,
#                        'Resource': 'PXI1Slot2'
#                        'Index':0},   
#                }
    ColsConfig={}
    for Col in Cols:
        ColsConfig[Col[0]]={'Frequency': Fc[Col[3]],
                         'Amplitude': A[Col[3]],
                         'Gain': 0.5,
                         'Resource':Col[1],
                         'Index': Col[2]}

    #Fetching    
    InFetch = np.ndarray((BufferSize, len(Rows)), dtype='int16')
    
    Procs = {}
    demind = 0
    
    for SweepInd, vgs in enumerate(CMVoltage):
        dsetname = 'Sw{0:03d}'.format(SweepInd)
            
        GenSig = FMmod.Columns(ColumnsConfig=ColsConfig, Fs=GenFs, GenSize=GenSize)
        
        GenSig.Abort()
        ScopeSig.abort()
        Sig = {}
        for col, pars in ColsConfig.items():
            PropSig = {}
            for p, val in pars.items():
                if p == 'Resource' or p == 'Index':
                    continue
                PropSig[str(p)] = val
                
            Sig[str(col)]= PropSig
            
        GenSig.SetSignal(Sig, vgs)
        GenSig.Initiate()
        ScopeSig.GetSignal(ScopeFs, Rows, Range=rangeScope)
        FileBuf.InitDset(dsetname)
        Inputs = ScopeSig.Capturar(Rows, BufferSize, offset = ScopeOffset)
        for i, In in enumerate(Inputs):
#            InFetch[:,i] = In.samples
            InFetch[:,i] = np.int16(np.round(np.array(In.samples)/LSB))
        FileBuf.AddSample(InFetch)
        for nr in range(len(Rows)):
            for col in Cols:
                ProcsArgs = {'dset': dsetname,
                             'dInd': nr, # Row index inside dataset
                             'col': col[0],
                             'cInd': col[3],
                             'Fc': Fc[col[3]],
                             'Ac': A[col[3]],
                             'Fs': ScopeFs,
                             'BuffSize': BufferSize,
                             'GenFs': GenFs,
                             'GenSize': GenSize,  
                             'Samps': GenSize/(GenFs/ScopeFs), # DemOscSize
                             'Vgs' : vgs,
                             'Gain': PCBGain,
                             'LSB': LSB}
            
                Demkey = 'Dem{0:03d}'.format(demind)
                demind += 1 
                Procs[Demkey] = ProcsArgs
    
        
    FileBuf.close()
    GenSig.Abort()
    ScopeSig.abort()    
      
    FileMod.GenArchivo(name=Dictname, dic2Save=Procs)
        
        
        
        
        
        
    
    