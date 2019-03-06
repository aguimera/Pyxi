#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 18:16:26 2019

@author: aguimera
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5 import Qt
import numpy as np
from itertools import  cycle


GenFsPar = {'name': 'Fs',
            'tip': 'FsKw.Fs',
            'type': 'float',
            'value': 1e4,
            'step': 100,
            'siPrefix': True,
            'suffix': 'Hz'}

GenIntTimePar = {'name': 'IntervalTime',
                 'tip': 'FsKw.Fs',
                 'type': 'float',
                 'value': 0.9,
                 'step': 0.1,
                 'siPrefix': True,
                 'suffix': 's'}

GenIntSamplesPar = {'name': 'nSamples',
                    'tip': 'Interval samples',
                    'type': 'int',
                    'value': 1e4,
                    }

GenNChannelsPar = {'name': 'nChannels',
                   'tip': 'Channels Number',
                   'type': 'int',
                   'value': 16,
                   'limits': (1, 128),
                   'step': 1}


class DataGeneratorParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChild(GenFsPar)
        self.addChild(GenIntTimePar)
        self.addChild(GenIntSamplesPar)
        self.addChild(GenNChannelsPar)
        self.Fs = self.param(GenFsPar['name'])
        self.IntTime = self.param(GenIntTimePar['name'])
        self.IntSamples = self.param(GenIntSamplesPar['name'])
        self.NChannels = self.param(GenNChannelsPar['name'])

        self.Fs.sigValueChanged.connect(self.on_Fs_Changed)
        self.IntTime.sigValueChanged.connect(self.on_Time_Changed)
        self.IntSamples.sigValueChanged.connect(self.on_Samples_Changed)

    def on_Fs_Changed(self):
        Fs = self.Fs.value()
        Ts = 1/Fs
        nSamps = self.IntSamples.value()

        nTime = nSamps * Ts
        self.IntTime.setValue(nTime, blockSignal=self.on_Time_Changed)

    def on_Time_Changed(self):
        Fs = self.Fs.value()
        Ts = 1/Fs
        nTime = self.IntTime.value()

        nSamps = int(nTime/Ts)
        self.IntSamples.setValue(nSamps, blockSignal=self.on_Samples_Changed)

    def on_Samples_Changed(self):
        Fs = self.Fs.value()
        Ts = 1/Fs
        nSamps = self.IntSamples.value()

        nTime = nSamps * Ts
        self.IntTime.setValue(nTime, blockSignal=self.on_Time_Changed)

    def GetParams(self):
        GenKwargs = {}
        for p in self.children():
            GenKwargs[p.name()] = p.value()
        return GenKwargs

    def GetChannels(self):
        Channels = {}
        for i in range(self.NChannels.value()):
            chn = 'Ch{0:02}'.format(i)
            Channels[chn] = i
        return Channels


class DataSamplingThread(Qt.QThread):
    ''' Data generator '''
    NewSample = Qt.pyqtSignal()

    def __init__(self, Fs, nChannels, nSamples, IntervalTime):
        super(DataSamplingThread, self).__init__()

        self.Timer = Qt.QTimer()
        self.Timer.moveToThread(self)
        self.Timer.timeout.connect(self.GenData)

        self.Fs = float(Fs)
        self.nChannels = int(nChannels)
        self.nSamples = int(nSamples)
        self.OutData = np.ndarray((self.nSamples, self.nChannels))
        self.IntervalTime = IntervalTime*1000
        self.Timer.setInterval(self.IntervalTime)

        Pcycle = np.round(self.Fs/10)
        Fsig = Fs/Pcycle

        Ts = 1/self.Fs
        tstop = Ts*(Pcycle)
        t = np.arange(0, tstop, Ts)

        samples = np.sin(2*np.pi*Fsig*t)
        self.InSamples = cycle(samples)
        self.chFacts = np.linspace(0, nChannels/10, nChannels)

#        for isamp in range(self.nSamples):
#            samps = self.chFacts * next(self.InSamples)
#            self.OutData[isamp, :] = samps

    def run(self, *args, **kwargs):
        self.Timer.start()
        loop = Qt.QEventLoop()
        loop.exec_()

#        while True:
#            Qt.QThread.msleep(self.IntervalTime)
#            self.OutData = np.random.sample(self.OutData.shape)
#            self.NewSample.emit()

    def GenData(self):
        for isamp in range(self.nSamples):
            samps = self.chFacts * next(self.InSamples)
            self.OutData[isamp, :] = samps
        self.OutData = self.OutData + np.random.sample(self.OutData.shape)            
#        self.OutData = np.random.sample(self.OutData.shape)
        self.NewSample.emit()
