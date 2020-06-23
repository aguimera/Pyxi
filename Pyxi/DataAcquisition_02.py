# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 16:24:43 2020

@author: lucia
"""

from PyQt5 import Qt

import numpy as np

import Pyxi.FMAcqCore as CoreMod


class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()

    def __init__(self, GenConfig, Channels, FsGen, GenSize, FsScope, 
                 BufferSize, CMVoltage, AcqVRange, GainBoard, AcqDiff=True, 
                 SwEnable=False, VgsInit=None, VdValue=None, AvgIndex=5,):
        '''Initialization of the Thread for Acquisition
           GenConfig: dictionary. Configuration for each generation column
                                   {'ColsConfig': {'Col1':{'Frequency':30000.0,
                                                            'Phase': 0,
                                                            'Amplitude': 0.25,
                                                            'Analog': True,
                                                            'Digital': False}
                                                }
                                    }
           Channels:  List. Contains the name of the Acquisition Channels
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
        '''
        super(DataAcquisitionThread, self).__init__()

        self.DaqInterface = CoreMod.ChannelsConfig(ChannelsScope=Channels,
                                                   Range=AcqVRange,
                                                   GenConfig=GenConfig,
                                                   AcqDiff=AcqDiff
                                                   )
        
        self.Channels = Channels
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.AvgIndex = AvgIndex
        self.FsGen = FsGen
        self.GenSize = GenSize
        self.FsScope = FsScope
        self.EveryN = BufferSize

        self.gain = GainBoard
        self.ColsConfig = GenConfig['ColsConfig']
        self.Col1 = self.ColsConfig['Col1']
        self.Freq = self.Col1['Frequency']
        self.phase = self.Col1['Phase']

        if SwEnable is True:
            self.Vcm = VgsInit  # se empieza el sweep con el primer valor
            self.OutSignal(Amp=VdValue)
        else:
            self.Vcm = CMVoltage
            self.OutSignal(Amp=np.sqrt(2)*GenConfig['ColsConfig']['Col1']['Amplitude'])

    def OutSignal(self, Amp):
        stepScope = 2*np.pi*(self.Freq/self.FsScope)
        t = np.arange(0, ((1/self.FsGen)*(self.GenSize)), 1/self.FsGen)
        self.Signal = Amp*np.cos(self.Freq*2*np.pi*t)
        self.Vcoi = np.complex128(1*np.exp(1j*(stepScope*np.arange(self.EveryN))))

    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(Fs=self.FsScope,
                                           EveryN=self.EveryN,
                                           Vgs=self.Vcm,
                                           )


        self.loop = Qt.QEventLoop()
        self.loop.exec_()

    def NewData(self, aiData):
        # print(self.Vcm)
        self.OutDataVolts = aiData # (Pico)
        self.OutData = (aiData/self.gain)  # (Pico)

        self.NewMuxData.emit()
