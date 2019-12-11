# -*- coding: utf-8 -*-
"""
Created on Wed May 22 11:54:46 2019

@author: Lucia
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

import numpy as np
import copy
import time
import re
import numpy as np
import copy
import time
import re

import Pyxi.FMAcqCore as CoreMod
import Pyxi.StabDetector as StbDet

#DAQ Data Acq
class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()
    VgsEnd = Qt.pyqtSignal()
    VdsEnd = Qt.pyqtSignal()
    
    def __init__(self, GenConfig, Channels, ScopeConfig, AvgIndex=5):
        super(DataAcquisitionThread, self).__init__()
        print(Channels)
        print(ScopeConfig)
        print(GenConfig)
        self.DaqInterface = CoreMod.ChannelsConfig(ChannelsScope=Channels,
                                                   Range=ScopeConfig['AcqVRange'],
                                                   GenConfig=GenConfig)
        self.threadStbDet = StbDet#Aqui va el thread para hacer el psd
        self.Channels = Channels
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.AvgIndex = AvgIndex
        self.FsScope = ScopeConfig['Fs']
        self.EveryN = ScopeConfig['BufferSize']

        self.Vcm = ScopeConfig['CMVoltage'] #array de Sweep Vgs
        self.gain = ScopeConfig['GainBoard']
        self.ColsConfig = GenConfig['ColsConfig']
        self.Col1 = self.ColsConfig['Col1']
        self.OutSignal(Amp=self.Col1['Amplitude'],#1 solo valor
                       Freq=self.Col1['Frequency'],
                       phase=self.Col1['Phase'])
        
        self.Sweep = 0
        self.Scopeconfig = ScopeConfig
        self.threadStbDet.NextVg.connect(self.NextVgsSweep)#aqui va el emit de PSD acabado
        
    def OutSignal(self, Amp, Freq, phase=0):

        step = 2*np.pi*(Freq/self.FsScope)
        self.Signal = np.float64(Amp*np.exp(1j*(step*np.arange(self.EveryN))))

            
    def run(self, *args, **kwargs):
#        self.Start()
        self.DaqInterface.StartAcquisition(Fs=self.FsScope, 
                                           EveryN=self.EveryN,
                                           Vgs=self.Vcm,
#                                           Signal=self.Signal
                                           )
#DemodTest with SigTest
#        ModSig=np.float64(self.Col1['Amplitude']*0.1*np.exp(1j*(2*np.pi*(1e3/self.FsScope)*np.arange(self.GenSize))))
#        SigTest=self.Signal+(ModSig*self.Signal)
#        self.DaqInterface.StartAcquisition(Fs=self.FsScope, 
#                                           EveryN=self.EveryN,
#                                           Vgs=self.Vcm,
#                                           Signal=SigTest)
        
        loop = Qt.QEventLoop()
        loop.exec_()

    
    def NewData(self, aiData):
        self.OutData = aiData/self.gain
        self.NewMuxData.emit()

    def NextVgsSweep(self):
        self.Sweep += 1
        self.Vcm = self.ScopeConfig['CMVoltage'][self.Sweep]
        self.DaqInterface.VcmOut.ClearTask()