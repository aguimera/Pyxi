# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 09:02:01 2020

@author: Lucia
"""

from PyQt5 import Qt

import numpy as np

import Pyxi.FMAcqCore_02 as CoreMod

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

    def __init__(self, CarrierConfig, ColChannels, FsGen, GenSize, 
                 ScopeChannels, FsScope, BufferSize, CMVoltage, AcqVRange=5, 
                 GainBoard=5e3, AcqDiff=False, AvgIndex=5, MeaType='Freq'):
        '''Initialization of the Thread for Acquisition
           CarrierConfig: dictionary. Configuration for each generation column
                                   {'Col1':{'Frequency':30000.0,
                                            'Phase': 0,
                                            'Amplitude': 0.25,}
                                    }
           ColChannels: List.
           ScopeChannels:  List. Contains the name of the Acquisition Channels
                            to be used
                            ['Ch01', 'Ch02', 'Ch03', 'Ch04', 'Ch05',
                            'Ch06', 'Ch07', 'Ch08']
           ScopeConfig: Dictionary. Configuration for acquisition and index
                                    of enable rows
                                    {'RowsConfig': {'Ch01': {'Enable': True,
                                                             'Index': 0},
                                                    'Ch02': {'Enable': True,
                                                             'Index': 1},
                                                    'Ch03': {'Enable': True,
                                                             'Index': 2},
                                                    'Ch04': {'Enable': True,
                                                             'Index': 3},
                                                    'Ch05': {'Enable': True,
                                                             'Index': 4},
                                                    'Ch06': {'Enable': True,
                                                             'Index': 5},
                                                    'Ch07': {'Enable': True,
                                                             'Index': 6},
                                                    'Ch08': {'Enable': True,
                                                             'Index': 7}},
                                     'FsGen':,
                                     'GenSize':,
                                     'FsScope': 2000000.0,
                                     'BufferSize': 20000,
                                     'CMVoltage': 0.0,
                                     'AcqVRange': 1,
                                     'NRow': 8,
                                     'GainBoard': 10000.0}
           SwEnable: bool. Identifies if it is a characterization sweep
                           acquisition or a real-time continuous acquisition
           VgArray: array. Contains the values of Common mode voltage for the
                           sweep
           VdValue: float. Contains the value of Vd to use in the carrier
                           signal
           MeaType: str. Freq or Time 
        '''
        super(DataAcquisitionThread, self).__init__()

        self.DaqInterface = CoreMod.ChannelsConfig(ChannelsScope=ScopeChannels,
                                                   Range=AcqVRange,
                                                   ChannelsCol=ColChannels,
                                                   AcqDiff=AcqDiff,
                                                   aiChannels=aiChannels,
                                                   aoChannels=aoChannels
                                                   )
        
        if MeaType == 'Time':
            self.DaqInterface.DataEveryNEvent = self.NewDataTime
        
        if MeaType == 'Freq':
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
        self.DaqInterface.StartAcquisition(Fs=self.FsScope,
                                           EveryN=self.EveryN,
                                           Vgs=self.Vcm,
                                           )


        self.loop = Qt.QEventLoop()
        self.loop.exec_()

    def NewDataTime(self, aiData):
        print('Time')
    
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


