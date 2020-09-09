# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 12:20:11 2019

@author: Lucia
"""

import PyqtTools.DaqInterface as DaqInt
import numpy as np

class ChannelsConfig():

    # DCChannelIndex[ch] = (index, sortindex)
    DCChannelIndex = None
    ACChannelIndex = None
    ChNamesList = None
    AnalogInputs = None
    DigitalOutputs = None
    VcmOut = None
    VdOut = None

    # Events list
    DataEveryNEvent = None
    DataDoneEvent = None

    def __init__(self, ChannelsScope, ChannelsCol, aiChannels, aoChannels, 
                 diChannels=None, doChannels=None, AcqDiff=False, Range=5,):
        '''Initialazion for Channels Configuration:
           ChannelsScope: List. Contains the name of the Acquisition Channels
                                to be used
                           ['Ch01', 'Ch02', 'Ch03', 'Ch04', 'Ch05', 'Ch06',
                           'Ch07', 'Ch08']
           Range: float. Acquisition Range
           GenConfig: dictionary. Contains Generation information for each
                                  Column.
                        {'ColsConfig': {'Col1': {'Frequency': 30000.0,
                                                 'Phase': 0,
                                                 'Amplitude': 0.25,
                                        }
                        }
           AcqDiff: bool. Specifies if the Acquisition is Differential or
                          Single
           ChVcm: str. Name of the output channel for common mode voltage
           ChCol1: str. Name ofthe output channel for Column0.
        '''
        print('InitChannels')

        self._InitAnalogOutputs(ChVcm=aoChannels[0],
                                ChVd=aoChannels[1])
        self.ChNamesList = sorted(ChannelsScope)
        self.Cols = ChannelsCol
        self._InitAnalogInputs(aiChannels=aiChannels,
                               Diff=AcqDiff,
                               Range=Range,
                               )

        self.Cols = []
        self.MuxChannelNames = []
        for Row in self.ChNamesList:
            for Col in ChannelsCol:
                self.MuxChannelNames.append(Row + Col)

    def _InitAnalogInputs(self, aiChannels, Diff, Range):
        print('InitAnalogInputs')
        self.SChannelIndex = {}
        self.DChannelIndex = {}
        InChans = []
        index = 0
        sortindex = 0
        for ch in self.ChNamesList:
            InChans.append(aiChannels[ch][0])  # only Output+
            self.SChannelIndex[ch] = (index, sortindex)
            index += 1

        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans,
                                              Diff=Diff,
                                              Range=Range)
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBack
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack

    def _InitAnalogOutputs(self, ChVcm, ChVd):
        self.VcmOut = DaqInt.WriteAnalog((ChVcm,))
        self.VdOut = DaqInt.WriteAnalog((ChVd,))

    def StartAcquisition(self, Fs, EveryN, Vgs):
        '''Starts the generation of the signals in the different channels
           and starts de acquisition process.
           Fs: float. Sampling Frequency for generation and acquisition
           EveryN: int. Size of the Buffer to acquire
           Vgs: float. Value of Gate-Source Voltage (Common Mode Voltage)
        '''
        self.SetVcm(Vcm=Vgs)
        self.AnalogInputs.ReadContData(Fs=Fs,
                                       EverySamps=EveryN)

    def SetVcm(self, Vcm):
        print(Vcm)
        self.VcmOut.SetVal(Vcm)
        
    def SetSignal(self, Signal, FsGen=2e6, FsBase=""):
        self.VdOut.SetContSignal(Signal=Signal,
                                 nSamps=len(Signal),
                                 FsBase=FsBase,
                                 FsDiv=FsGen)

    def EveryNEventCallBack(self, Data):
        _DataEveryNEvent = self.DataEveryNEvent

        _DataEveryNEvent(Data)

    def DoneEventCallBack(self, Data):
        print('Done callback')

    def Stop(self):
        print('Stopppp')

        self.AnalogInputs.StopContData()
        self.VcmOut.StopTask()
        self.VcmOut.SetVal(0)
        self.VcmOut.ClearTask()
        self.VcmOut = None
        self.VdOut.ClearTask()
        self.VdOut = None
