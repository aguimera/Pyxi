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
import copy

ColConfPars = ({'name': 'ColX',
                'type': 'group',
                'children': ({'name': 'Enable',
                              'value': True,
                              'type': 'bool'},
                             {'name': 'Freq',
                              'value': 100e3,
                              'type': 'float',
                              'siPrefix': True,
                              'suffix': 'Hz'},
                             {'name': 'Amp',
                              'value': 1,
                              'type': 'float',
                              'siPrefix': True,
                              'suffix': 'V'},
                             {'name': 'ModFact',
                              'value': 0.1,
                              'type': 'float',},
                             {'name': 'Fsig',
                              'value': 1e3,
                              'type': 'float',
                              'siPrefix': True,
                              'suffix': 'Hz'})
                   },)

GeneratorPars = ({'name': 'Fs',
                  'value': 5e6,
                  'type': 'float',
                  'siPrefix': True,
                  'suffix': 'Hz'},
                 {'name': 'Blocks',
                  'value': 10,
                  'type': 'int'},
                 {'name': 'SampsInt',
                  'value': 4,
                  'type': 'int'},
                 {'name': 'tInt',
                  'readonly': True,
                  'value': 4,
                  'type': 'float',
                  'siPrefix': True,
                  'suffix': 's'},
                 {'name': 'Rows',
                  'value': 4,
                  'type': 'int'},                
                  )


class DataGeneratorParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChildren(GeneratorPars)
        for i in range(4):
            col = copy.deepcopy(ColConfPars)
            col[0]['name']='Col'+str(i)
            self.addChildren(col)
        self.sigTreeStateChanged.connect(self.on_ColsChanged)

    def GetParams(self):
        cols = []
        conf = {}
        for p in self.children():
            if p.hasChildren():
                col = {}
                col['name'] = p.name()
                if p.param('Enable').value():
                    for pc in p.children():
                        if pc.name() == 'Enable':
                            continue
                        col[pc.name()] = pc.value()
                    cols.append(col)
            else:
                conf[p.name()] = p.value()
        conf['Cols'] = cols
        return conf

    def GetChannels(self):
        Channels = {}
        for i in range(self.param('Rows').value()):
            chn = 'In{}'.format(i)
            Channels[chn] = i
        return Channels

    def on_ColsChanged(self):        
        conf = self.GetParams()
        cols = conf['Cols']

        Fmin = np.min([c['Fsig'] for c in cols])

        Fs = conf['Fs']
        Samps = int(Fs/Fmin)
        for c in cols:
            nc = int((Samps*c['Fsig'])/Fs)
            c['Fsig'] = (nc*Fs) / Samps
            nc = int((Samps*c['Freq'])/Fs)
            c['Freq'] = (nc*Fs) / Samps
        
        conf['SampsInt'] = Samps
        conf['tInt'] = conf['Blocks'] * Samps * (1/Fs)
        
        for pn, pv in conf.items():
            if pn == 'Cols':
                for c in pv:
                    col = c['name']
                    for cn, cv in c.items():
                        if cn == 'name':
                            continue
                        self.param(col).param(cn).setValue(cv)
            else:
                self.param(pn).setValue(pv)
        


def GenTestSignal(t, Freq, Amp, Fsig, ModFact, Phase=0, **kwargs):
    out = Amp*(1+ModFact*np.sin(Fsig*2*np.pi*t))*np.cos(Freq*2*np.pi*t+Phase)
    return out

#def GenTestSignal(Freqs, t, Acarrier, Fsig, ModFact, Phase=0):
#    out = np.zeros(t.size)
#    for f in Freqs:        
#        s = Acarrier*(1+ModFact[0]*np.sin(Fsig[0]*2*np.pi*(t)))*np.cos(f*2*np.pi*(t)+Phase)
#        out = out + s
#        if len(Fsig) == 1:
#            continue
#        s = Acarrier*(1+ModFact[1]*np.cos(Fsig[1]*2*np.pi*(t)))*np.sin(f*2*np.pi*(t)+Phase)
#        out = out + s
#    return out


class DataSamplingThread(Qt.QThread):
    ''' Data generator '''
    NewSample = Qt.pyqtSignal()

    def __init__(self, Fs, SampsInt, tInt, Rows, Cols, Blocks):
        super(DataSamplingThread, self).__init__()

        self.Timer = Qt.QTimer()
        self.Timer.moveToThread(self)
        self.Timer.timeout.connect(self.GenData)
        self.IntervalTime = tInt*1000
        self.Timer.setInterval(self.IntervalTime)

        self.Fs = Fs
        t = np.linspace(0, tInt, SampsInt*Blocks)
        Out = np.zeros((SampsInt*Blocks,))
        for c in Cols:
            Out += GenTestSignal(t, **c)

        self.OutData = np.zeros((SampsInt*Blocks, Rows))
        for r in range(Rows):
            self.OutData[:, r] = Out

#        Ts = 1/self.Fs
#        tstop = Ts*(Pcycle)
#        t = np.arange(0, tstop, Ts)
#
#        samples = np.sin(2*np.pi*Fsig*t)
#        self.InSamples = cycle(samples)
#        self.chFacts = np.linspace(0, nChannels/10, nChannels)

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
#        for isamp in range(self.nSamples):
#            samps = self.chFacts * next(self.InSamples)
#            self.OutData[isamp, :] = samps
#        self.OutData = self.OutData + np.random.sample(self.OutData.shape)            
#        self.OutData = np.random.sample(self.OutData.shape)
        self.NewSample.emit()
