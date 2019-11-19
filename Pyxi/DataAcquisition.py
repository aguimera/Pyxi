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

    def __init__(self, Channels, ScopeConfig, AvgIndex=5):
        super(DataAcquisitionThread, self).__init__()
        print(Channels)
        print(ScopeConfig)
        self.DaqInterface = CoreMod.ChannelsConfig(Channels)
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.AvgIndex = AvgIndex
        self.FsScope = ScopeConfig['FsScope'].value()
        self.EveryN = ScopeConfig['BufferSize'].value()

    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(Fs=self.FsScope, EveryN=self.EveryN)
        loop = Qt.QEventLoop()
        loop.exec_()

    def CalcAverage(self, MuxData):
        return np.mean(MuxData[:, self.AvgIndex:, :], axis=1)

    def CalcDiff(self, aiDataPos, aiDataNeg):
        return aiDataPos-aiDataNeg
    
    def NewData(self, aiData, MuxData):
        self.OutData = self.CalcAverage(MuxData)
        self.aiData = aiData
        self.NewMuxData.emit()
