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
                 {'name': 'SampsInt',
                  'value': 4,
                  'type': 'int'},
                 {'name': 'tInt',
                  'value': 4,
                  'type': 'float',
                  'siPrefix': True,
                  'suffix': 's'},

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


def GenTestSignal(Freqs, t, Acarrier, Fsig, ModFact, Phase=0):
    out = np.zeros(t.size)
    for f in Freqs:        
        s = Acarrier*(1+ModFact[0]*np.sin(Fsig[0]*2*np.pi*(t)))*np.cos(f*2*np.pi*(t)+Phase)
        out = out + s
        if len(Fsig) == 1:
            continue
        s = Acarrier*(1+ModFact[1]*np.cos(Fsig[1]*2*np.pi*(t)))*np.sin(f*2*np.pi*(t)+Phase)
        out = out + s
    return out


class DataSamplingThread(Qt.QThread):
    ''' Data generator '''
    NewSample = Qt.pyqtSignal()

    def __init__(self):
        super(DataSamplingThread, self).__init__()

        self.Timer = Qt.QTimer()
        self.Timer.moveToThread(self)
        self.Timer.timeout.connect(self.GenData)

        Fs = 1e6
        Fsig = 1e3
        Pcycle = int(Fs/Fsig)
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
