# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 13:08:49 2020

@author: Lucia
"""

import PyqtTools.DaqInterface as DaqInt
import numpy as np

class ChannelsConfig():

    ChannelIndex = None
    ChNamesList = None
    AnalogInputs = None
    DigitalOutputs = None
    SwitchOut = None
    Dec = None
    DCSwitch = np.array([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, ], dtype=np.uint8)
    ACSwitch = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dtype=np.uint8)
    DecDigital = np.array([0, 1, 0, 1, 1], dtype=np.uint8) # Ouput should be: P26
    # Events list
    DataEveryNEvent = None
    DataDoneEvent = None
        
    def __init__(self, Channels, Cols=None, AcqDC=False, AcqAC=False,
                 ACGain=1e6, DCGain=10e3, AcqDiff=False, Range=5,
                 aiChannels=None, aoChannels=None, diChannels=None, 
                 doChannels=None, decoder=None):
        
        print('InitChannels')
        
        self._InitAnalogOutputs(ChVgs=aoChannels[0],
                                ChVds=aoChannels[1])
        
        self.ChNamesList = sorted(Channels)
        
        self._InitAnalogInputs(aiChannels=aiChannels,
                               Diff=AcqDiff,
                               Range=Range,
                               )
        
        self.AcqAC = AcqAC
        self.AcqDC = AcqDC
        self.ACGain = ACGain
        self.DCGain = DCGain
        self.DOChannels = doChannels
        
        if doChannels is not None:
            self.SwitchOut = DaqInt.WriteDigital(Channels=doChannels)
            
        if decoder is not None:
            self.Dec = DaqInt.WriteDigital(Channels=decoder)
        
        if Cols is not None:
            self.MuxChannelNames = []
            for Row in self.ChNamesList:
                for Col in Cols:
                    self.MuxChannelNames.append(Row + Col)
        
    def _InitAnalogInputs(self, aiChannels, Diff, Range):
        self.ChannelIndex = {}
        InChans = []

        index = 0
        for ch in self.ChNamesList:
            if len(aiChannels[ch]) <= 1:
                InChans.append(aiChannels[ch])
                
            else:
                InChans.append(aiChannels[ch][0])  # only Output+
            
            self.ChannelIndex[ch] = (index)
            index += 1

        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans,
                                              Diff=Diff,
                                              Range=Range)
        
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBack
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack
        
    def _InitAnalogOutputs(self, ChVgs, ChVds):
        print('ChVgs ->', ChVgs)
        print('ChVds ->', ChVds)
        self.VgsOut = DaqInt.WriteAnalog((ChVgs,))
        self.VdsOut = DaqInt.WriteAnalog((ChVds,))

    def SetVcm(self, Vcm):
        print(Vcm)
        self.VgsOut.SetVal(Vcm)
        
    def SetBias(self, Vds, Vgs):
        print('ChannelsConfig SetBias Vgs ->', Vgs, 'Vds ->', Vds)
        self.VdsOut.SetVal(Vds)
        self.VsOut.SetVal(-Vgs)
        self.BiasVd = Vds-Vgs
        self.Vgs = Vgs
        self.Vds = Vds
        
    def SetFreqSignal(self, Signal, FsGen=2e6, FsBase=""):
        self.VdsOut.SetContSignal(Signal=Signal,
                                  nSamps=len(Signal),
                                  FsBase=FsBase,
                                  FsDiv=FsGen)
        self.Vds = None
    
    def SetDigitalSignal(self, Signal):
        if not self.SwitchOut:
            self.SwitchOut = DaqInt.WriteDigital(Channels=self.DOChannels)
        self.SwitchOut.SetDigitalSignal(Signal)
        self.Dec.SetDigitalSignal(self.DecDigital)

    def SetContSignal(self, Signal, nSamps):
        if not self.VgsOut:
            self.VgsOut = DaqInt.WriteAnalog(('ao2',))
        self.VgsOut.DisableStartTrig()
        self.VgsOut.SetContSignal(Signal=Signal,
                                  nSamps=nSamps)
        
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
            
            else:
                _DataEveryNEvent(Data)

    def DoneEventCallBack(self, Data):
        print('Done callback')
        
    def StartAcquisition(self, Fs, Vgs, Vds=None, EveryN=None, Refresh=None,
                         **kwargs):
        if Vds is not None:
            self.SetBias(Vgs=Vgs, Vds=Vds)
        else:
            self.SetVcm(Vcm=Vgs)
        
        if self.AcqDC:
            print('DC')
            self.SetDigitalSignal(Signal=self.DCSwitch)
            
        if self.AcqAC:
            print('AC')
            self.SetDigitalSignal(Signal=self.ACSwitch)
                       
        if EveryN is None:
            EveryN = Refresh*Fs # TODO check this
        self.AnalogInputs.ReadContData(Fs=Fs,
                                       EverySamps=EveryN)

    def Stop(self):
        print('Stopppp')
        
        self.AnalogInputs.StopContData()
                
        if self.Vds is None:
            self.VgsOut.StopTask()
            self.VgsOut.SetVal(0)
            self.VgsOut.ClearTask()
            self.VgsOut = None
            self.VdsOut.ClearTask()
            self.VdsOut = None
        
        else:
            self.SetBias(Vgs=0, Vds=0)

        if self.SwitchOut is not None:
            print('Clear Digital')
            self.SwitchOut.ClearTask()
            self.SwitchOut = None

