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

    def __init__(self, GenConfig, Channels, ScopeConfig, SwEnable, VgArray, VdValue, AvgIndex=5):
        super(DataAcquisitionThread, self).__init__()

        self.DaqInterface = CoreMod.ChannelsConfig(ChannelsScope=Channels,
                                                   Range=ScopeConfig['AcqVRange'],
                                                   GenConfig=GenConfig)
  
        self.Channels = Channels
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.AvgIndex = AvgIndex
        self.FsScope = ScopeConfig['Fs']
        self.EveryN = ScopeConfig['BufferSize']

        
        self.gain = ScopeConfig['GainBoard']
        self.ColsConfig = GenConfig['ColsConfig']
        self.Col1 = self.ColsConfig['Col1']
        self.Freq = self.Col1['Frequency']
        self.phase = self.Col1['Phase']
        
        if SwEnable is True:
            self.VcmValues = VgArray#array de Sweep Vgs
            self.Vcm = self.VcmValues[0] #se empieza el sweep con el primer valor
            self.OutSignal(Amp=VdValue)            
        else:
            self.Vcm =ScopeConfig['CMVoltage']
            self.OutSignal(Amp=GenConfig['ColsConfig']['Col1']['Amplitude']) 
        
        
    def OutSignal(self, Amp):

        step = 2*np.pi*(self.Freq/self.FsScope)
        self.Signal = np.float64(Amp*np.exp(1j*(step*np.arange(self.EveryN))))

            
    def run(self, *args, **kwargs):

        self.DaqInterface.StartAcquisition(Fs=self.FsScope, 
                                           EveryN=self.EveryN,
                                           Vgs=self.Vcm,
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

