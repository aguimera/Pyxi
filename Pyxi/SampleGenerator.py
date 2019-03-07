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


ColConfPars = ({'name': 'Frequency',
                'value': 100e3,
                'type': 'float',
                'siPrefix': True,
                'suffix': 'Hz'},
               {'name': 'Amplitude',
                'value': 1,
                'type': 'float',
                'siPrefix': True,
                'suffix': 'V'},
               {'name': 'ModFact',
                'value': 0.1,
                'type': 'float',},
               {'name': 'FreqMod',
                'value': 1e3,
                'type': 'float',
                'siPrefix': True,
                'suffix': 'Hz'},
               )

GeneratorPars = ({'name': 'Fs',
                  'value': 5e6,
                  'type': 'float',
                  'siPrefix': True,
                  'suffix': 'Hz'},
                 {'name': 'Rows',
                  'value': 4,
                  'type': 'int'},
                 {'name': 'Cols',
                  'type': 'group',
                  'children': ({'name': 'Col1',
                                'value': True,
                                'type': 'bool'},
                               {'name': 'Col1Conf',
                                'type': 'group',
                                'children': ColConfPars},
                               {'name': 'Col2',
                                'value': True,
                                'type': 'bool'},
                               {'name': 'Col2Conf',
                                'type': 'group',
                                'children': ColConfPars},
                               {'name': 'Col3',
                                'value': True,
                                'type': 'bool'},
                               {'name': 'Col3Conf',
                                'type': 'group',
                                'children': ColConfPars},
                               {'name': 'Col4',
                                'value': True,
                                'type': 'bool'},
                               {'name': 'Col4Conf',
                                'type': 'group',
                                'children': ColConfPars},
                                )},
                    )


class DataGeneratorParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChildren(GeneratorPars)


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
