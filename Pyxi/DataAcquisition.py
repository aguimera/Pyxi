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

import FMAcqCore as CoreMod

#DAQ Data Acq
class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()

    def __init__(self, ChannelsConfigKW, SampKw, AvgIndex=5):
        super(DataAcquisitionThread, self).__init__()
        self.DaqInterface = CoreMod.ChannelsConfig(**ChannelsConfigKW)
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.SampKw = SampKw
        self.AvgIndex = AvgIndex

    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(**self.SampKw)
        loop = Qt.QEventLoop()
        loop.exec_()

    def CalcAverage(self, MuxData):
        return np.mean(MuxData[:, self.AvgIndex:, :], axis=1)

    def NewData(self, aiData, MuxData):
        self.OutData = self.CalcAverage(MuxData)
        self.aiData = aiData
        self.NewMuxData.emit()
