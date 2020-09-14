# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 09:02:01 2020

@author: Lucia
"""

from PyQt5 import Qt

import numpy as np

import Pyxi.FMAcqCore_Time_Freq as CoreMod

# estoy habrá que improtarlo de otra manera
aiChannels = {'Ch01': ('ai0', 'ai8'),
              'Ch02': ('ai1', 'ai9'),
              'Ch03': ('ai2', 'ai10'),
              'Ch04': ('ai3', 'ai11'),
              'Ch05': ('ai4', 'ai12'),
              'Ch06': ('ai5', 'ai13'),
              'Ch07': ('ai6', 'ai14'),
              'Ch08': ('ai7', 'ai15'),
              'Ch09': ('ai16', 'ai24'),
              'Ch10': ('ai17', 'ai25'),
              'Ch11': ('ai18', 'ai26'),
              'Ch12': ('ai19', 'ai27'),
              'Ch13': ('ai20', 'ai28'),
              'Ch14': ('ai21', 'ai29'),
              'Ch15': ('ai22', 'ai30'),
              'Ch16': ('ai23', 'ai31'),
              }

aoChannels = ['ao0', 'ao1']

class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()

    def __init__(self, CarrierConfig=None, ColChannels=None, FsGen=None, 
                 GenSize=None, ScopeChannels=None, FsScope=None, 
                 BufferSize=None, CMVoltage=None, AcqVRange=5, 
                 GainBoard=5e3, AcqDiff=False, AvgIndex=5, MeaType='Freq',
                 ChannelsConfigKW=None, SampKw=None):

        super(DataAcquisitionThread, self).__init__()
        
        self.SampKw = SampKw
        
        if MeaType == 'Time':
            self.DaqInterface = CoreMod.ChannelsConfig(**ChannelsConfigKW)
            self.DaqInterface.DataEveryNEvent = self.NewDataTime
        
        if MeaType == 'Freq':
            self.DaqInterface = CoreMod.ChannelsConfig(Channels=ScopeChannels,
                                                       Range=AcqVRange,
                                                       Cols=ColChannels,
                                                       AcqDiff=AcqDiff,
                                                       aiChannels=aiChannels,
                                                       aoChannels=aoChannels
                                                       )
            
            self.DaqInterface.DataEveryNEvent = self.NewDataFreq
            self.Channels = ScopeChannels
            self.AvgIndex = AvgIndex
            self.FsGen = FsGen
            self.GenSize = GenSize
            self.FsScope = FsScope
            self.EveryN = BufferSize
    
            self.gain = GainBoard
            self.Col1 = CarrierConfig['Col1']
            self.Freq = self.Col1['Frequency']
            self.phase = self.Col1['Phase']
            self.Amplitude = self.Col1['Amplitude']
            self.Vcm = CMVoltage  # se empieza el sweep con el primer valor
            self.OutSignal(Vds=self.Amplitude)

    def run(self, *args, **kwargs):
        if self.SampKw is None:
            self.DaqInterface.StartAcquisition(Fs=self.FsScope,
                                               EveryN=self.EveryN,
                                               Vgs=self.Vcm,
                                               )
        else:
            self.DaqInterface.StartAcquisition(**self.SampKw)  

        self.loop = Qt.QEventLoop()
        self.loop.exec_()

    def NewDataTime(self, aiData):
        print('Time')
        self.aiData = aiData
        self.NewTimeData.emit()
    
    def NewDataFreq(self, aiData):
        # print(self.Vcm)
        self.OutDataVolts = aiData # (Pico)
        self.OutData = (aiData/self.gain)  # (Pico)

        self.NewMuxData.emit()
        
    def OutSignal(self, Vds):
        stepScope = 2*np.pi*(self.Freq/self.FsScope)
        t = np.arange(0, ((1/self.FsGen)*(self.GenSize)), 1/self.FsGen)
        # self.Signal = np.ndarray((len(t), len(Vds)))
        # self.Vcoi = np.ndarray((self.Signal.shape))
        # for ind, Vd in enumerate(Vds):
        #     self.Signal[:,ind] = Vd*np.cos(self.Freq*2*np.pi*t)
        #     self.Vcoi = np.complex128(1*np.exp(1j*(stepScope*np.arange(self.EveryN))))

        self.Signal = Vds*np.cos(self.Freq*2*np.pi*t)
        self.Vcoi = np.complex128(1*np.exp(1j*(stepScope*np.arange(self.EveryN))))


