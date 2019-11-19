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

    # Events list
    DataEveryNEvent = None
    DataDoneEvent = None
    
    def __init__(self, Channels, AcqSingle=True, AcqDiff=False):
        print('InitChannels')

        self.ChNamesList = sorted(Channels)
        print(self.ChNamesList)
        self.AcqS = AcqSingle
        self.AcqD = AcqDiff
        self._InitAnalogInputs()

    def _InitAnalogInputs(self):
        print('InitAnalogInputs')
        self.SChannelIndex = {}
        self.DChannelIndex = {}
        InChans = []
        index = 0
        sortindex = 0
        for ch in self.ChNamesList:
#            if self.AcqS:
            #Output+ is always read
            InChans.append(aiChannels[ch][0]) #only Output+
            self.SChannelIndex[ch] = (index, sortindex)
            index += 1
            print(ch, 'Single -->', aiChannels[ch][0])
            print('SortIndex ->', self.SChannelIndex[ch])
            if self.AcqD:
            #Only read Output- when diff activated
                InChans.append(aiChannels[ch][1])
                self.DChannelIndex[ch] = (index, sortindex)
                index += 1
                print(ch, ' Differential -->', aiChannels[ch][1])
                print('SortIndex ->', self.DChannelIndex[ch])
            sortindex += 1
        print('Input ai', InChans)

        self.AnalogInputs = DaqInt.ReadAnalog(InChans=InChans)
        # events linking
        self.AnalogInputs.EveryNEvent = self.EveryNEventCallBack
        self.AnalogInputs.DoneEvent = self.DoneEventCallBack
        
    def StartAcquisition(self, Fs, EveryN):
#    def StartAcquisition(self, Fs, nSampsCo, nBlocks, numCols):
        print('StartAcquisition')
        print('DSig set')

#        EveryN = numCols*nSampsCo*nBlocks
        self.AnalogInputs.ReadContData(Fs=Fs,
                                       EverySamps=EveryN)


    def EveryNEventCallBack(self, Data):
        print('EveryNEventCallBack')
        _DataEveryNEvent = self.DataEveryNEvent

        if _DataEveryNEvent is not None:
            if self.AcqS:
                _DataEveryNEvent = Data
#            if self.AcqD:
#                self.AiOutput


    def DoneEventCallBack(self, Data):
        print('Done callback')

    def Stop(self):
        print('Stopppp')
        self.AnalogInputs.StopContData()