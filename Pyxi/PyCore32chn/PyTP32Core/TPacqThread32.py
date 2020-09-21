#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 12:25:45 2019

@author: aguimera
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np
# import TPacqCore32 as CoreMod
# import PyTP32Core.TPacqCore32 as CoreMod
import PyqtTools.FileModule as FileMod
import PyqtTools.FMAcqCore_Time_Freq as CoreMod

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

aoChannels = ['ao1', 'ao0']

SampSettingConf = ({'title': 'Channels Config',
                    'name': 'ChsConfig',
                    'type': 'group',
                    'children': ({'title': 'Acquire DC',
                                  'name': 'AcqDC',
                                  'type': 'bool',
                                  'value': True},
                                 {'title': 'Acquire AC',
                                  'name': 'AcqAC',
                                  'type': 'bool',
                                  'value': False},
                                 {'title': 'Acquire DC and AC',
                                  'name': 'AcqDCAC',
                                  'type': 'bool',
                                  'value': False},
                                 {'tittle': 'Channels',
                                  'name': 'Channels',
                                  'type': 'group',
                                  'children': ({'name': 'Ch01',
                                                'tip': 'Ch01',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch02',
                                                'tip': 'Ch02',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch03',
                                                'tip': 'Ch03',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch04',
                                                'tip': 'Ch04',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch05',
                                                'tip': 'Ch05',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch06',
                                                'tip': 'Ch06',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch07',
                                                'tip': 'Ch07',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch08',
                                                'tip': 'Ch08',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch09',
                                                'tip': 'Ch09',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch10',
                                                'tip': 'Ch10',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch11',
                                                'tip': 'Ch11',
                                                'type': 'bool',
                                                'value': False},
                                               {'name': 'Ch12',
                                                'tip': 'Ch12',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch13',
                                                'tip': 'Ch13',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch14',
                                                'tip': 'Ch14',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch15',
                                                'tip': 'Ch15',
                                                'type': 'bool',
                                                'value': True},
                                               {'name': 'Ch16',
                                                'tip': 'Ch16',
                                                'type': 'bool',
                                                'value': True},
                                               # {'name': 'Ch17',
                                               #  'tip': 'Ch17',
                                               #  'type': 'bool',
                                               #  'value': False},
                                               # {'name': 'Ch18',
                                               #  'tip': 'Ch18',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch19',
                                               #  'tip': 'Ch19',
                                               #  'type': 'bool',
                                               #  'value': False},
                                               # {'name': 'Ch20',
                                               #  'tip': 'Ch20',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch21',
                                               #  'tip': 'Ch21',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch22',
                                               #  'tip': 'Ch22',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch23',
                                               #  'tip': 'Ch23',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch24',
                                               #  'tip': 'Ch24',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch25',
                                               #  'tip': 'Ch25',
                                               #  'type': 'bool',
                                               #  'value': False},
                                               # {'name': 'Ch26',
                                               #  'tip': 'Ch26',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch27',
                                               #  'tip': 'Ch27',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch28',
                                               #  'tip': 'Ch28',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch29',
                                               #  'tip': 'Ch29',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch30',
                                               #  'tip': 'Ch30',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch31',
                                               #  'tip': 'Ch31',
                                               #  'type': 'bool',
                                               #  'value': True},
                                               # {'name': 'Ch32',
                                               #  'tip': 'Ch32',
                                               #  'type': 'bool',
                                               #  'value': True}, 
                                               ), },
                                 ), },

                   {'name': 'Sampling Settings',
                    'type': 'group',
                    'children': ({'title': 'Sampling Frequency',
                                  'name': 'Fs',
                                  'type': 'float',
                                  'value': 10e3,
                                  'step': 100,
                                  'siPrefix': True,
                                  'suffix': 'Hz'},
                                 {'title': 'Refresh Time',
                                  'name': 'Refresh',
                                  'type': 'float',
                                  'value': 1.0,
                                  'step': 0.01,
                                  'limits': (0.01, 500),
                                  'suffix': 's'},
                                 {'title': 'Vds',
                                  'name': 'Vds',
                                  'type': 'float',
                                  'value': 0.05,
                                  'step': 0.01,
                                  'limits': (0, 0.1)},
                                 {'title': 'Vgs',
                                  'name': 'Vgs',
                                  'type': 'float',
                                  'value': 0.1,
                                  'step': 0.1,
                                  'limits': (-0.1, 0.5)},
                                 {'title': 'Refresh graph',
                                  'name':'Graph',
                                  'type': 'action',},
                                  
                                  
                                     ), }
                   )


###############################################################################


class SampSetParam(pTypes.GroupParameter):
    NewConf = Qt.pyqtSignal()

    Chs = []
    Acq = {}

    def __init__(self, **kwargs):
        super(SampSetParam, self).__init__(**kwargs)
        self.addChildren(SampSettingConf)

        self.SampSet = self.param('Sampling Settings')
        self.Fs = self.SampSet.param('Fs')
        self.Refresh = self.SampSet.param('Refresh')

        self.ChsConfig = self.param('ChsConfig')
        self.Channels = self.ChsConfig.param('Channels')

        # Init Settings
        self.on_Acq_Changed()
        self.on_Ch_Changed()
        self.on_Fs_Changed()

        # Signals
        self.Channels.sigTreeStateChanged.connect(self.on_Ch_Changed)
        self.ChsConfig.param('AcqAC').sigValueChanged.connect(self.on_Acq_Changed)
        self.ChsConfig.param('AcqDC').sigValueChanged.connect(self.on_Acq_Changed)
        self.Fs.sigValueChanged.connect(self.on_Fs_Changed)

    def on_Acq_Changed(self):
        for p in self.ChsConfig.children():
            if p.name() is 'AcqAC':
                self.Acq[p.name()] = p.value()
            if p.name() is 'AcqDC':
                self.Acq[p.name()] = p.value()
        self.on_Fs_Changed()
        self.NewConf.emit()

    def on_Fs_Changed(self):
        if self.Chs:
            Index = 1
            if self.Acq['AcqDC'] and self.Acq['AcqAC'] is True:
                Index = 2
            if self.Fs.value() > (1e6/(len(self.Chs)*Index)):
                self.SampSet.param('Fs').setValue(1e6/(len(self.Chs)*Index))

    def on_Ch_Changed(self):
        self.Chs = []
        for p in self.Channels.children():
            if p.value() is True:
                self.Chs.append(p.name())
        self.on_Fs_Changed()
        self.NewConf.emit()

    def GetChannelsNames(self):
        Ind = 0
        ChNames = {}
        acqTys = []
        for tyn, tyv in self.Acq.items():
            if tyv:
                acqTys.append(tyn)

        if 'AcqDC' in acqTys:
            for Ch in self.Chs:
                ChNames[Ch + 'DC'] = Ind
                Ind += 1

        if 'AcqAC' in acqTys:
            for Ch in self.Chs:
                ChNames[Ch + 'AC'] = Ind
                Ind += 1

        return ChNames

    def GetSampKwargs(self):
        GenKwargs = {}
        for p in self.SampSet.children():
            GenKwargs[p.name()] = p.value()
        return GenKwargs

    def GetChannelsConfigKwargs(self):
        ChanKwargs = {}
        for p in self.ChsConfig.children():
            if p.name() is 'Channels':
                ChanKwargs[p.name()] = self.Chs
            else:
                ChanKwargs[p.name()] = p.value()
        print(ChanKwargs, 'ChanKwargs')
        return ChanKwargs

###############################################################################


class DataAcquisitionThread(Qt.QThread):
    NewTimeData = Qt.pyqtSignal()

    def __init__(self, ChannelsConfigKW, SampKw):
        super(DataAcquisitionThread, self).__init__()
        self.DaqInterface = CoreMod.ChannelsConfig(aiChannels=aiChannels,
                                                   doChannels=DOChannels,
                                                   aoChannels=aoChannels,
                                                   **ChannelsConfigKW)
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.SampKw = SampKw

    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(**self.SampKw)
        loop = Qt.QEventLoop()
        loop.exec_()

    def NewData(self, aiData, aiDataAC=None):
        self.aiData = aiData
        self.aiDataAC = aiDataAC
        self.NewTimeData.emit()
