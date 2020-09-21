#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 14:13:45 2019

@author: aguimera
"""
import PyqtTools.DaqInterface as DaqInt
import numpy as np


# Daq card connections mapping 'Chname':(DCout, ACout)


aiChannels = {'Ch09': ('ai0', 'ai8'),
              'Ch10': ('ai1', 'ai9'),
              'Ch11': ('ai2', 'ai10'),
              'Ch12': ('ai3', 'ai11'),
              'Ch13': ('ai4', 'ai12'),
              'Ch14': ('ai5', 'ai13'),
              'Ch15': ('ai6', 'ai14'),
              'Ch16': ('ai7', 'ai15'),
              'Ch01': ('ai16', 'ai24'),
              'Ch02': ('ai17', 'ai25'),
              'Ch03': ('ai18', 'ai26'),
              'Ch04': ('ai19', 'ai27'),
              'Ch05': ('ai20', 'ai28'),
              'Ch06': ('ai21', 'ai29'),
              'Ch07': ('ai22', 'ai30'),
              'Ch08': ('ai23', 'ai31'),
              }
DOChannels = ['port0/line0:15', ]

DOChannels = ['port0/line0:9', ]
# Decoder = ['port0/line10:15', ]

##############################################################################


class ChannelsConfig():

    ChannelIndex = None
    ChNamesList = None
    AnalogInputs = None
    DigitalOutputs = None
    SwitchOut = None
    Dec = None
    DCSwitch = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, ], dtype=np.uint8)
    ACSwitch = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=np.uint8)
    # DecDigital = np.array([0, 1, 0, 1, 1], dtype=np.uint8) # Ouput should be: P26
    # Events list
    DataEveryNEvent = None
    DataDoneEvent = None

    def _InitAnalogInputs(self):
        self.ChannelIndex = {}
        InChans = []

        index = 0
        for ch in self.ChNamesList:
            # InChans.append(aiChannels[ch])
            if self.AcqDC:
                InChans.append(aiChannels[ch][0])

            if self.AcqAC:
                InChans.append(aiChannels[ch][1])

            self.ChannelIndex[ch] = (index)
            index += 1

        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans)
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBack
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack
        

    def _InitAnalogInputsDCAC(self):
        self.ChannelIndex = {}
        InChans = []
        InChansAC = []

        index = 0
        for ch in self.ChNamesList:
            # InChans.append(aiChannels[ch])
            InChans.append(aiChannels[ch][0])
            InChansAC.append(aiChannels[ch][1])

            self.ChannelIndex[ch] = (index)
            index += 1

        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans+InChansAC)
        # self.AnalogInputsAC = DaqInt.ReadAnalog(InChans=InChansAC)
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBackDCAC
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack
        
        # self.AnalogInputsAC.EveryNEvent = self.EvertNEventCallBackAC
        
    def _InitAnalogOutputs(self, ChVds, ChVs):
        print('ChVds ->', ChVds)
        print('ChVs ->', ChVs)
        self.VsOut = DaqInt.WriteAnalog((ChVs,))
        self.VdsOut = DaqInt.WriteAnalog((ChVds,))

    def __init__(self, Channels,
                 AcqDC=True, AcqAC=False, AcqDCAC=False,
                 ChVds='ao1', ChVs='ao0', # MB4
                 # ChVds='ao0', ChVs='ao1', # old
                 ACGain=1e6, DCGain=10e3):
        print('InitChannels')
        self._InitAnalogOutputs(ChVds=ChVds, ChVs=ChVs)

        self.ChNamesList = sorted(Channels)
        self.AcqAC = AcqAC
        self.AcqDC = AcqDC
        self.ACGain = ACGain
        self.DCGain = DCGain
        if AcqDCAC:
            self._InitAnalogInputsDCAC()
        else:
            self._InitAnalogInputs()

        self.SwitchOut = DaqInt.WriteDigital(Channels=DOChannels)
        # self.Dec = DaqInt.WriteDigital(Channels=Decoder)

    def StartAcquisition(self, Fs, Refresh, Vgs, Vds, **kwargs):
        self.SetBias(Vgs=Vgs, Vds=Vds)
        if self.AcqDC:
            print('DC')
            self.SetDigitalSignal(Signal=self.DCSwitch)
        if self.AcqAC:
            print('AC')
            self.SetDigitalSignal(Signal=self.ACSwitch)

        self.Fs = Fs
        self.EveryN = Refresh*Fs # TODO check this
        self.AnalogInputs.ReadContData(Fs=Fs,
                                       EverySamps=self.EveryN)

    def SetBias(self, Vgs, Vds):
        print('ChannelsConfig SetBias Vgs ->', Vgs, 'Vds ->', Vds)
        self.VdsOut.SetVal(Vds)
        self.VsOut.SetVal(-Vgs)
        self.BiasVd = Vds-Vgs
        self.Vgs = Vgs
        self.Vds = Vds

    def SetDigitalSignal(self, Signal):
        if not self.SwitchOut:
            self.SwitchOut = DaqInt.WriteDigital(Channels=DOChannels)
        self.SwitchOut.SetDigitalSignal(Signal)
        # self.Dec.SetDigitalSignal(self.DecDigital)

    def _SortChannels(self, data, SortDict):
        (samps, inch) = data.shape
        sData = np.zeros((samps, len(SortDict)))
        for chn, inds in sorted(SortDict.items()):
            sData[:, inds] = data[:, inds]

        return sData

    def EveryNEventCallBack(self, Data):
        _DataEveryNEvent = self.DataEveryNEvent

        if _DataEveryNEvent is not None:
            if self.AcqDC:
                aiDataDC = self._SortChannels(Data, self.ChannelIndex)
                aiDataDC = (aiDataDC-self.BiasVd) / self.DCGain
                
            if self.AcqAC:
                aiDataAC = self._SortChannels(Data, self.ChannelIndex)
                aiDataAC = aiDataAC / self.ACGain

            if self.AcqAC and self.AcqDC:
                print('ERROR')
                aiData = np.hstack((aiDataDC, aiDataAC))
                _DataEveryNEvent(aiData)
            elif self.AcqAC:
                _DataEveryNEvent(aiDataAC)
            elif self.AcqDC:
                _DataEveryNEvent(aiDataDC)

    def EveryNEventCallBackDCAC(self, Data):
        _DataEveryNEvent = self.DataEveryNEvent
        if _DataEveryNEvent is not None:            
            print('Sending DC DATA')
            aiDataDC = self._SortChannels(Data[:int(len(Data)/2)], self.ChannelIndex)
            aiDataDC = (aiDataDC-self.BiasVd) / self.DCGain
            print('Sending AC DATA')
            aiDataAC = self._SortChannels(Data[int(len(Data)/2):], self.ChannelIndex)
            aiDataAC = aiDataAC / self.ACGain
            _DataEveryNEvent(aiDataDC, aiDataAC)
        
    def DoneEventCallBack(self, Data):
        print('Done callback')

    def Stop(self):
        print('Stopppp')
        self.SetBias(Vgs=0, Vds=0)
        self.AnalogInputs.StopContData()
        # self.AnalogInputsAC.StopContData()
        if self.SwitchOut is not None:
            print('Clear Digital')
            self.SwitchOut.ClearTask()
            self.SwitchOut = None



