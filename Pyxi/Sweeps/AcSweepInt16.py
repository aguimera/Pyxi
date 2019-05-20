# -*- coding: utf-8 -*-
"""
Created on Mon May 20 14:50:44 2019

@author: Lucia
"""

import numpy as np
import time

import os

#import Gen_Scope_Classes as Gen_Scope
import Pyxi.FileModule as FileMod
import Pyxi.FMacqThread as FMmod

if __name__ == '__main__':
    
    #File To Save
    Dictname ='AcSweep_LRB__4Carr_Row1_Fs1e6_NoStabilization'
    FileName = Dictname +'.h5'
    
    if os.path.isfile(FileName):
        print('Remove File')
        os.remove(FileName)


    #Calculas per al Scope
    GenFs = 20e6 #La Fs de generació es necessita aqui per asegurar que sigui multiple de FsScope
    ScopeFs = 1e6
    nFs = round(GenFs/ScopeFs)
    ScopeFs = GenFs/nFs
    tFetch = 300e-3
    NumFetch = 1
    BufferSize = round(tFetch*ScopeFs)
    tFetch = BufferSize/ScopeFs
    ScopeOffset = int(ScopeFs*6)
    #    Rows d'exemple a continuació: no borrar
#    Rows = [('Row1', 0), ('Row2', 1), ('Row3', 2), ('Row4', 3), ('Row5', 4), ('Row6', 5), ('Row7', 6), ('Row8', 7)]
    Rows = [('Row1', 0),('Row2', 1), ('Row3', 2), ('Row4', 3), ('Row5', 4), ('Row6', 5), ('Row7', 6), ('Row8', 7)]
    RowsArray = []
    rangeScope = 6  #options 0.05, 0.2, 1, 6, 30
    LSB = rangeScope/(2**16)
    PCBGain = 10e3
    MaxFileSize = 500e6
    dtype = 'int16'
    
    FileBuf = FileMod.FileBuffer(FileName=FileName,
                                 MaxSize=MaxFileSize,
                                 nChannels=len(Rows),
                                 dtype=dtype)  
    
    RowsConfig = {}
    for row in Rows:
        RowsConfig[row[0]] = {}
        RowsArray.append(row[1])
        RowsConfig[row[0]]['Enable'] = True
        RowsConfig[row[0]]['Index'] = row[1]
        RowsConfig[row[0]]['Range'] = rangeScope
    
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
    CMVoltage = 0
    #Calculs per al Generador    
    #definir les Fc que es volen utilitzar
    Fc=np.array([70e3, 85e3, 100e3, 115e3])

    for ind, f in enumerate(Fc):
        nc = round((GenSize*f)/GenFs)
        Fc[ind] =  (nc*GenFs)/GenSize
    
    A=np.ndarray((numSweeps, 4))
    A[:,0] = np.linspace(0.01,0.04, num=numSweeps) #Sweep per Col1
    A[:,1] = np.linspace(0.01,0.04, num=numSweeps)   #Sweep per Col2
    A[:,2] = np.linspace(0.01,0.04, num=numSweeps)   #Sweep per Col3
    A[:,3] = np.linspace(0.01,0.04, num=numSweeps)   #Sweep per Col4
    
    #Es crea una Cols Config que es configurará per cada Sweep amb la freq correcta
#    ColsConfig={'Col1':{'Frequency': Fc0,
#                        'amplitude': A[0],
#                        'Gain': 0.5,
#                        'Resource': 'PXI1Slot2'
#                        'Index':0},
#                'Col1':{'Frequency': Fc0,
#                        'amplitude': A[0],
#                        'Gain': 0.5,
#                        'Resource': 'PXI1Slot2'
#                        'Index':0},   
#                }
    ColsConfig={}
    for Col in Cols:
        ColsConfig[Col[0]]={'Frequency': Fc[Col[3]],
                            'Amplitude': 0,
                            'Gain': 0.5,
                            'Resource':Col[1],
                            'Index': Col[2]}

    #Fetching    
    InFetch = np.ndarray((BufferSize, len(Rows)))
    
    Procs = {}
    demind = 0
    
    for SweepInd, Ac in enumerate(A):
        dsetname = 'Sw{0:03d}'.format(SweepInd)
        
        for Col in Cols:
            ColsConfig[Col[0]]['Amplitude']=Ac[Col[3]]
         
        ACqSet = FMmod.Acquisition(ColumnsConfig=ColsConfig, 
                                   FsGen=GenFs, 
                                   GS=GenSize,
                                   RowsConfig=RowsConfig,
                                   NRow=len(RowsArray),
                                   FsScope=ScopeFs,
                                   ResourceScope='PXI1Slot4')
        
        ACqSet.stopSessions()            
        ACqSet.setSignals(ColumnsConfig=ColsConfig,
                          Vgs=CMVoltage)    
        ACqSet.initSessions()
        
        FileBuf.InitDset(dsetname)
        InFetch, LSB = ACqSet.GetData(FetchSize=BufferSize,
                                      channels=RowsArray,
                                      ScopeOffset=ScopeOffset)
        
        FileBuf.AddSample(InFetch)
        for nr in range(len(Rows)):
            for col in Cols:
                ProcsArgs = {'dset': dsetname,
                             'dInd': nr, # Row index inside dataset
                             'col': col[0],
                             'cInd': col[3],
                             'Fc': Fc[col[3]],
                             'Ac': Ac[col[3]],
                             'Fs': ScopeFs,
                             'BuffSize': BufferSize,
                             'GenFs': GenFs,
                             'GenSize': GenSize,  
                             'Samps': GenSize/(GenFs/ScopeFs), # DemOscSize
                             'Vgs' : CMVoltage,
                             'Gain': PCBGain}
            
                Demkey = 'Dem{0:03d}'.format(demind)
                demind += 1 
                Procs[Demkey] = ProcsArgs
    
        
    FileBuf.close()
    ACqSet.stopSessions()     
      
    FileMod.GenArchivo(name=Dictname, dic2Save=Procs)
        
        
        
        
        
        
    
    
