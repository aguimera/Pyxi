# -*- coding: utf-8 -*-
"""
Created on Wed May 22 11:54:46 2019

@author: Lucia
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

import numpy as np
import niscope
import nifgen
import copy
import time
import re

import Pyxi.NifGenerator as NifGen
import Pyxi.NiScope as NiScope

class DataAcquisitionThread(Qt.QThread):
    NewData = Qt.pyqtSignal()

    def __init__(self, ColsConfig, FsGen, GenSize, CMVoltage, RowsConfig, FsScope, BufferSize, NRow, OffsetRows, GainBoard, ResourceScope):
        print ('TMacqThread, DataAcqThread')
        super(DataAcquisitionThread, self).__init__()
        
        print(ColsConfig)
        print(RowsConfig)
        self.Cols = NifGen.Columns(ColsConfig=ColsConfig, 
                                   FsGen=FsGen, 
                                   GenSize=GenSize)
        self.Rows = NiScope.Rows(RowsConfig=RowsConfig, 
                                 FsScope=FsScope, 
                                 ResourceScope=ResourceScope)
        self.BufferSize = BufferSize
        self.OffsetRows = OffsetRows
        self.GainBoard = (GainBoard)
        self.LSB = np.array([])
        self.RowsList = []
        self.Channels = []
        
        self.ttimer = ((self.BufferSize/FsScope)-0.05)*1000
        
        for Row, pars in RowsConfig.items():
            self.RowsList.append(str(Row))
            self.LSB = np.append(self.LSB, RowsConfig[str(Row)]['AcqVRange']/(2**16))
            
        for s in self.RowsList:
            self.Channels.append(int(re.split(r'(\d+)', s)[1])-1)
        Sig = {}
        for col, pars in ColsConfig.items():
            PropSig = {}
            for p, val in pars.items():
                if p == 'ResourceScope' or p == 'Index':
                    continue
                PropSig[str(p)] = val
                
            Sig[str(col)]= PropSig
        print(Sig)   
        self.Cols.Gen_SetSignal(SigsPars=Sig, 
                                Vcm=CMVoltage)
        self.Timer = Qt.QTimer()
        self.Timer.moveToThread(self)
        
    def run(self, *args, **kwargs):
        print('start ')      
        self.OutData = np.ndarray((self.BufferSize, len(self.Channels)))
        self.BinData = np.ndarray((self.BufferSize, len(self.Channels)))
        self.IntData = np.ndarray((self.BufferSize, len(self.Channels)))
        self.initSessions()
        loop = Qt.QEventLoop()
        loop.exec_()
    
    def GenData(self):
        if not self.isRunning():
            return
        try:
            Inputs = self.Rows.SesScope.channels[self.Channels].fetch(num_samples=self.BufferSize,
                                                                      relative_to=niscope.FetchRelativeTo.READ_POINTER,
                                                                      offset=self.OffsetRows,
                                                                      record_number=0,
                                                                      num_records=1,
                                                                      timeout=2)
            
            self.Timer.singleShot(self.ttimer, self.GenData)
            for i, In in enumerate(Inputs):
                self.OutData[:, i] = np.array(In.samples)/self.GainBoard 
#                self.BinData[:,i] = np.array(In.samples)[:,i]/self.LSB[i]
                self.BinData[:,i] = np.array(In.samples)/self.LSB[i]
                self.IntData[:,i] = np.int16(np.round(self.BinData[:,i]))
            self.NewData.emit()

        except Exception:
            print(Exception.args)
            print('Requested data has been overwritten in memory')
            self.stopSessions()
            print('Gen and Scope Sessions Restarted')
            self.initSessions()        
                 
    def initSessions(self):
        self.Cols.Session_Gen_Initiate()
        self.Rows.Session_Scope_Initiate()
        self.Timer.singleShot(self.ttimer, self.GenData)
        
    def stopSessions(self):
        self.Cols.Session_Gen_Abort()
        self.Rows.Session_Scope_Abort()
        
    def stopTimer(self):
        self.Timer.stop()
        self.Timer.killTimer(self.Id)
        
##############################NoThread##########################################         
class DataAcquisition():    
    def __init__(self, ColsConfig, FsGen, GenSize, RowsConfig, FsScope, GainBoard, ResourceScope):
        self.Columns = NifGen.Columns(ColsConfig, FsGen, GenSize)
        self.Rows = NiScope.Rows(RowsConfig, FsScope, ResourceScope)
        self.GainBoard = GainBoard
        self.LSB = np.array([])
        self.RowsList = []
        for Row, pars in RowsConfig.items():
            self.RowsList.append(str(Row))
            self.LSB = np.append(self.LSB, RowsConfig[str(Row)]['AcqVRange']/(2**16))
        
        self.Channels=[]
        for s in self.RowsList:
            self.Channels.append(int(re.split(r'(\d+)', s)[1])-1)
       
        
    def setSignals(self, ColsConfig, Vcm):
        Sig = {}
        for col, pars in ColsConfig.items():
            PropSig = {}
            for p, val in pars.items():
                if p == 'ResourceScope' or p == 'Index':
                    continue
                PropSig[str(p)] = val
                
            Sig[str(col)]= PropSig

        self.Columns.Gen_SetSignal(Sig, Vcm)  
        
    def GetData(self, BufferSize, channels, OffsetRows, dtype):                
        Inputs = self.Rows.SesScope.channels[channels].fetch(num_samples=BufferSize,
                                                              relative_to=niscope.FetchRelativeTo.READ_POINTER,
                                                              offset=OffsetRows,
                                                              record_number=0,
                                                              num_records=1,
                                                              timeout=60)
        OutData = np.ndarray((BufferSize, len(channels))) 
        BinData = np.ndarray((BufferSize, len(channels)))
        IntData = np.ndarray((BufferSize, len(channels)), dtype='int16')
        for i, In in enumerate(Inputs):
            OutData[:, i] = np.array(In.samples)#/self.GainBoard 
            BinData[:,i] = OutData[:,i]/self.LSB[i]
            IntData[:,i] = np.int16(np.round(BinData[:,i]))
        if dtype == 'int16':
            Output = IntData
        else:
            Output = OutData
        return Output, self.LSB
        
    def initSessions(self):
        self.Columns.Session_Gen_Initiate()
        self.Rows.Session_Scope_Initiate()
        
    def stopSessions(self):
        self.Columns.Session_Gen_Abort()
        self.Rows.Session_Scope_Abort()