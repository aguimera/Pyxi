# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 12:20:11 2019

@author: Lucia
"""

import Pyxi.DaqInterface as DaqInt
#import PyTMCore.DaqInterface as DaqInt
import numpy as np

# Daq card connections mapping 'Chname':(AI+, AI-)
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

##############################################################################


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
    
    def __init__(self, ChannelsScope, Range, GenConfig,  AcqDiff=True, ChVcm='ao0', ChCol1='ao1'):
        print('InitChannels')

        self._InitAnalogOutputs(ChVcm=ChVcm,
                                ChVd=ChCol1)
        self.ChNamesList = sorted(ChannelsScope)
        print(self.ChNamesList)
        self.AcqD = AcqDiff
        self.Range = Range
        self._InitAnalogInputs()

        self.Cols = []
        MuxChannelNames = []
        for Row in self.ChNamesList:
            for Col, val in GenConfig['ColsConfig'].items():
                MuxChannelNames.append(Row + Col)
                self.Cols.append(Col)
        self.MuxChannelNames = MuxChannelNames
        print(self.MuxChannelNames)
        
    def _InitAnalogInputs(self):
        print('InitAnalogInputs')
        self.SChannelIndex = {}
        self.DChannelIndex = {}
        InChans = []
        index = 0
        sortindex = 0
        for ch in self.ChNamesList:
            #Output+ is always read
            InChans.append(aiChannels[ch][0]) #only Output+
            self.SChannelIndex[ch] = (index, sortindex)
            index += 1
            print(ch, 'Single -->', aiChannels[ch][0])
            print('SortIndex ->', self.SChannelIndex[ch])
#            if self.AcqD:
#            #Only read Output- when diff activated
#                InChans.append(aiChannels[ch][1])
#                self.DChannelIndex[ch] = (index, sortindex)
#                index += 1
#                print(ch, ' Differential -->', aiChannels[ch][1])
#                print('SortIndex ->', self.DChannelIndex[ch])
#            sortindex += 1
        print('Input ai', InChans)

        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans, 
                                              Diff=self.AcqD,
                                              Range=self.Range)
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBack
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack
        
    def _InitAnalogOutputs(self, ChVcm, ChVd):
        print('ChVds ->', ChVd)
        print('ChVcm ->', ChVcm)
        self.VcmOut = DaqInt.WriteAnalog((ChVcm,))
        self.VdOut = DaqInt.WriteAnalog((ChVd,))   
        
    def StartAcquisition(self, Fs, EveryN, Vgs, Signal):
#    def StartAcquisition(self, Fs, nSampsCo, nBlocks, numCols):
        print('StartAcquisition')
        print('DSig set')
        
        self.nBlocks = EveryN       
        self.SetOutput(Vcm=Vgs,
                       Signal=Signal)
        self.OutputShape = (len(self.MuxChannelNames), int(EveryN))

        self.AnalogInputs.ReadContData(Fs=Fs,
                                       EverySamps=self.nBlocks)

    
    def SetOutput(self, Vcm, Signal):
        self.VcmOut.SetVal(Vcm)
        print(Signal, len(Signal))
        self.VdOut.SetContSignal(Signal=Signal,
                                 nSamps=len(Signal))
    
    def _SortChannels(self, data, SortDict):
        print('SortChannels')
        print(data.shape)
        # Sort by aianalog input
        (samps, inch) = data.shape
        aiData = np.zeros((samps, len(SortDict)))
        for chn, inds in sorted(SortDict.items()):
            aiData[:, inds[1]] = data[:, inds[0]]
            
        return aiData
    
    def EveryNEventCallBack(self, Data):
        print('EveryNEventCallBack')
        _DataEveryNEvent = self.DataEveryNEvent

#        aiDataChns = self._SortChannels(Data,
#                                        self.SChannelIndex)

#        _DataEveryNEvent(aiDataChns)
#        print(Data.shape)
        _DataEveryNEvent(Data)

    def DoneEventCallBack(self, Data):
        print('Done callback')

    def Stop(self):
        print('Stopppp')
#        self.VcmOut.SetVal(0)
#        self.VdOut.SetVal(0)
        self.AnalogInputs.StopContData()
        self.VcmOut.ClearTask()
        self.VcmOut=None
        self.VdOut.ClearTask()
        self.VdOut=None
        