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

#DAQ Data Acq
class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()

    def __init__(self, GenConfig, Channels, ScopeConfig, AvgIndex=5):
        super(DataAcquisitionThread, self).__init__()
        print(Channels)
        print(ScopeConfig)
        print(GenConfig)
        self.DaqInterface = CoreMod.ChannelsConfig(ChannelsScope=Channels, 
                                                   GenConfig=GenConfig)
        self.Channels = Channels
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.AvgIndex = AvgIndex
        self.FsScope = ScopeConfig['FsScope']
        self.EveryN = ScopeConfig['BufferSize']

        self.GenSize = GenConfig['GenSize']
        self.Vcm = GenConfig['CMVoltage']
        
        self.ColsConfig = GenConfig['ColsConfig']
        self.Col1 = self.ColsConfig['Col1']
        self.OutSignal(Amp=self.Col1['Amplitude'],
                       Freq=self.Col1['Frequency'],
                       phase=self.Col1['Phase'])
        
    def OutSignal(self, Amp, Freq, phase=0):
        Ts = 1/(self.FsScope)
        Time = np.arange(0, Ts*self.GenSize, Ts)
        self.Signal = Amp*np.sin(2*np.pi*Freq*Time+((np.pi/180)*phase))
        
    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(Fs=self.FsScope, 
                                           EveryN=self.EveryN,
                                           Vgs=self.Vcm,
                                           Signal=self.Signal[:-1])
        loop = Qt.QEventLoop()
        loop.exec_()

    
    def NewData(self, aiData):
        self.OutData = aiData
        self.NewMuxData.emit()
