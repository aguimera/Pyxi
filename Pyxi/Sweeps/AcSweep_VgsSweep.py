# -*- coding: utf-8 -*-
"""
Created on Thu May 16 14:16:02 2019

@author: aemdlabs
"""

import numpy as np
import time

import os

#import Gen_Scope_Classes as Gen_Scope
import Pyxi.FileModule as FileMod
import Pyxi.DataAcquisition as DataAcq

if __name__ == '__main__':
    
    #File To Save
#    Dictname ="F:\\Dropbox (ICN2 AEMD - GAB GBIO)\\PyFET\\LuciaScripts\\Lucia\\DCTests\\RTest_DC_VgsSweep_1Row_1Col_VcmToGnd".
    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\TeamFolderLMU\FreqMux\Characterization\15_10_2019\SSP54348-T4-4x8-Acs85mV-Vgs0p27-Range1"
#    Dictname =r"F:\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DCTests\Resistors\19_09_2019\4x8array"
    FileName = Dictname +'.h5'
    
    if os.path.isfile(FileName):
        print('Remove File')
        os.remove(FileName)
    
    #Calculas per al Scope
    GenFs = 20e6 #La Fs de generació es necessita aqui per asegurar que sigui multiple de FsScope
    ScopeFs = 500e3
    nFs = round(GenFs/ScopeFs)
    ScopeFs = GenFs/nFs
    tFetch = 30
    NumFetch = 1
    BufferSize = round(tFetch*ScopeFs)
    tFetch = BufferSize/ScopeFs
    t_wait_stab = 10 #tiempo estabilización en segundos
    ScopeOffset = int(ScopeFs*t_wait_stab) #Muestras de estabilización
#    Rows d'exemple a continuació: no borrar
#    Rows = [('Row1', 0), ('Row2', 1), ('Row3', 2), ('Row4', 3), ('Row5', 4), ('Row6', 5), ('Row7', 6), ('Row8', 7)]
#    Rows = [('Row1', 0), ('Row2', 1), ('Row3', 2), ('Row4', 3), ('Row5', 4), ('Row6', 5), ('Row7', 6), ('Row8', 7)]
#    Rows = [('Row1', 0), ('Row2', 1), ('Row3', 2), ('Row4', 3), ('Row5', 4)]
#    2x2
#    Rows = [('Row 4', 3),('Row5', 4)]
#    ProbeR = ['Chn6', 'Chn14'] #Poner el número de Row real de la probe
#    ColOn = [0,1,1,0] 
#    1x1
#    Rows = [('Row6', 5),]
#    ProbeR = ['Chn6',] #Poner el número de Row real de la probe
#    ColOn = [0,1,0,0] 
#    3x3
#    Rows = [('Row1', 0),('Row4', 3),('Row5', 4)]
#    ProbeR = ['Chn6','Chn8', 'Chn14']
#    ColOn = [1,1,1,0] 

#4x8
    Rows = [('Row1', 0), ('Row2', 1), ('Row3', 2), ('Row4', 3), ('Row5', 4), ('Row6', 5), ('Row7', 6), ('Row8', 7)]
    ProbeR = ['Chn6','Chn8', 'Chn14','Chn1','Chn2','Chn3', 'Chn4','Chn5']
    ColOn = [1,1,1,1]
     
    RowsArray = []
    rangeScope = 1  #options 0.05, 0.2, 1, 6, 30
    PCBGain = 10e3
    MaxFileSize = 10e12 #(10Tb)
#    dtype = 'int16'
    dtype = 'float'
    
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
        RowsConfig[row[0]]['AcqVRange'] = rangeScope
    
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

#    numSweeps = 20
    numSweeps = 3
    nAcSweep = 11
    GenSize = 20e3
    Ts = 1/GenFs
    t = np.arange(0, Ts*GenSize, Ts)        
#    A = [0.015, 0.015, 0.015, 0.015]  
#    A = [0.0, 0.02] 
    
#    SwAc = np.linspace(0.07, 0.11, num=nAcSweep)
#    SwAc = np.linspace(0.05, 0.05, num=1)
    SwAc=np.array([0.085])#*np.sqrt(2) #,0.025,0.012]
    #definir les Fc que es volen utilitzar
    Fc=np.array([70e3, 85e3, 100e3, 115e3])
    Ph = np.array([144.596, -45.1778, -125.836, -110.565])
#    Fc=np.array([70e3, 85e3, 100e3, 115e3])
#    Ph = np.array([0, 0, 0, 0])
#    Ph = np.array([0,0,0,0])
    for ind, f in enumerate(Fc):
        nc = round((GenSize*f)/GenFs)
        Fc[ind] =  (nc*GenFs)/GenSize
        
    #deefinir vector de CMVoltage (Vgs) que es vol fer el sweep
    CMVoltage = np.linspace(-0.265, -0.275, num=numSweeps)
#    CMVoltage = np.append(CMVoltage, 0)
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
                             'Phase': Ph[Col[3]],
                             'Amplitude': 0,
                             'Gain': 0.5,
                             'Resource':Col[1],
                             'Index': Col[2]}
        
    Procs = {}
    demind = 0
    for SweepAcInd, Ac in enumerate(SwAc):
        A = np.array(ColOn)*Ac
        for Col in Cols:
            ColsConfig[Col[0]]['Amplitude']=A[Col[3]]
            
        ACqSet = DataAcq.DataAcquisition(ColsConfig=ColsConfig, 
                                             FsGen=GenFs, 
                                             GenSize=GenSize,
                                             RowsConfig=RowsConfig,
                                             FsScope=ScopeFs,
                                             GainBoard=PCBGain,
                                             ResourceScope='PXI1Slot4')
        #Fetching    
        InFetch = np.ndarray((BufferSize, len(Rows)), dtype=dtype)
        

        
        for SweepInd, vgs in enumerate(CMVoltage):
            nSwAc = 'AcSw{0:03d}'.format(SweepAcInd)
            nSwVgs = 'Sw{0:03d}'.format(SweepInd)
            print(vgs)
            dsetname = nSwAc + nSwVgs
            print(dsetname)
            ACqSet.stopSessions()            
            ACqSet.setSignals(ColsConfig=ColsConfig,
                              Vcm=vgs)   
            ACqSet.initSessions()
            
            FileBuf.InitDset(dsetname)
            InFetch, LSB = ACqSet.GetData(BufferSize=BufferSize,
                                          channels=RowsArray,
                                          OffsetRows=ScopeOffset,
                                          dtype=dtype
                                          )
            
            FileBuf.AddSample(InFetch)
            for nr in range(len(Rows)):
                for col in Cols:
                    ProcsArgs = {'dset': dsetname,
                                 'dInd':nr, # Row index inside dataset
                                 'ProbeRow': ProbeR[nr],
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
                                 'LSB': LSB,
                                 'PhaseFc': Ph
                                 }
                
                    Demkey = 'Dem{0:04d}'.format(demind)
                    demind += 1 
                    Procs[Demkey] = ProcsArgs
    
    FileBuf.close()
    ACqSet.stopSessions()     
    FileMod.GenArchivo(name=Dictname, dic2Save=Procs)

    ACqSet.setSignals(ColsConfig=ColsConfig,
                      Vcm=0)   
    ACqSet.initSessions()
    ACqSet.stopSessions() 
    

        
        
        
        
        
        
    
    