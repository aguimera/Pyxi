#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 18:44:39 2019

@author: aguimera
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph as pg
import copy
from PyQt5 import Qt
import numpy as np
from scipy.signal import welch


ChannelPars = {'name': 'Ch01',
               'type': 'group',
               'children': [{'name': 'name',
                             'type': 'str',
                             'value': 'Ch10'},
                            {'name': 'color',
                             'type': 'color',
                             'value': "FFF"},
                            {'name': 'width',
                             'type': 'float',
                             'value': 0.5},
                            {'name': 'Window',
                             'type': 'int',
                             'value': 1,},
                            {'name': 'Input',
                             'type': 'int',
                             'readonly': True,
                             'value': 1,}]
               }

PlotterPars = ({'name': 'Fs',
                'readonly': True,
                'type': 'float',
                'siPrefix': True,
                'suffix': 'Hz'},
               {'name': 'nChannels',
                'readonly': True,
                'type': 'int',
                'value': 1},
               {'name': 'ViewBuffer',
                'type': 'float',
                'value': 30,
                'step': 1,
                'siPrefix': True,
                'suffix': 's'},
               {'name': 'ViewTime',
                'type': 'float',
                'value': 10,
                'step': 1,
                'siPrefix': True,
                'suffix': 's'},
               {'name': 'RefreshTime',
                'type': 'float',
                'value': 4,
                'step': 1,
                'siPrefix': True,
                'suffix': 's'},
               {'name': 'Windows',
                'type': 'int',
                'value': 1},
               {'name': 'Channels',
                'type': 'group',
                'children': []},)


class PlotterParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

#        self.QTparent = QTparent
        self.addChildren(PlotterPars)
        self.param('Windows').sigValueChanged.connect(self.on_WindowsChange)

    def on_WindowsChange(self):
        print('tyest')
        chs = self.param('Channels').children()
        chPWind = int(len(chs)/self.param('Windows').value())
        for ch in chs:
            ind = ch.child('Input').value()
            ch.child('Window').setValue(int(ind/chPWind))

    def SetChannels(self, Channels):
        self.param('Channels').clearChildren()
        nChannels = len(Channels)
        self.param('nChannels').setValue(nChannels)
        chPWind = int(nChannels/self.param('Windows').value())
        Chs = []
        for chn, ind in Channels.items():
            Ch = copy.deepcopy(ChannelPars)
            pen = pg.mkPen((ind, 1.3*nChannels))
            Ch['name'] = chn
            Ch['children'][0]['value'] = chn
            Ch['children'][1]['value'] = pen.color()
            Ch['children'][3]['value'] = int(ind/chPWind)
            Ch['children'][4]['value'] = ind
            Chs.append(Ch)

        self.param('Channels').addChildren(Chs)

    def GetParams(self):
        PlotterKwargs = {}
        for p in self.children():
            if p.name() in ('Channels', 'Windows'):
                continue
            PlotterKwargs[p.name()] = p.value()

        ChannelConf = {}
        for i in range(self.param('Windows').value()):
            ChannelConf[i] = []

        for p in self.param('Channels').children():
            chp = {}
            for pp in p.children():
                chp[pp.name()] = pp.value()
            ChannelConf[chp['Window']].append(chp.copy())
        PlotterKwargs['ChannelConf'] = ChannelConf
        return PlotterKwargs

##############################################################################


class PgPlotWindow(Qt.QWidget):
    def __init__(self):
        super(PgPlotWindow, self).__init__()
        layout = Qt.QVBoxLayout(self)
        self.pgLayout = pg.GraphicsLayoutWidget()
        layout.addWidget(self.pgLayout)
        self.show()

##############################################################################


class Buffer2D(np.ndarray):
    def __new__(subtype, Fs, nChannels, ViewBuffer,
                dtype=float, buffer=None, offset=0,
                strides=None, order=None, info=None):
        # Create the ndarray instance of our type, given the usual
        # ndarray input arguments.  This will call the standard
        # ndarray constructor, but return an object of our type.
        # It also triggers a call to InfoArray.__array_finalize__
        BufferSize = int(ViewBuffer*Fs)
        shape = (BufferSize, nChannels)
        obj = super(Buffer2D, subtype).__new__(subtype, shape, dtype,
                                               buffer, offset, strides,
                                               order)
        # set the new 'info' attribute to the value passed
        obj.counter = 0
        obj.totalind = 0
        obj.Fs = float(Fs)
        obj.Ts = 1/obj.Fs
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None:
            return
        self.bufferind = getattr(obj, 'bufferind', None)

    def AddData(self, NewData):
        newsize = NewData.shape[0]
        self[0:-newsize, :] = self[newsize:, :]
        self[-newsize:, :] = NewData
        self.counter += newsize
        self.totalind += newsize

    def IsFilled(self):
        return self.counter >= self.shape[0]

    def GetTimes(self, Size):
        stop = self.Ts * self.totalind
        start = stop - self.Ts*Size
        times = np.arange(start, stop, self.Ts)
        return times[-Size:]

    def Reset(self):
        self.counter = 0

##############################################################################


labelStyle = {'color': '#FFF',
              'font-size': '7pt',
              'bold': True}


class Plotter(Qt.QThread):
    def __init__(self, Fs, nChannels, ViewBuffer, ViewTime, RefreshTime,
                 ChannelConf):
        super(Plotter, self).__init__()

        self.Winds = []
        self.nChannels = nChannels
        self.Plots = [None]*nChannels
        self.Curves = [None]*nChannels

        self.Fs = Fs
        self.Ts = 1/float(self.Fs)
        self.Buffer = Buffer2D(Fs, nChannels, ViewBuffer)
        self.SetRefreshTime(RefreshTime)
        self.SetViewTime(ViewTime)

#        print(self.RefreshInd, self.ViewInd, self.Buffer.shape)

        self.Winds = []
        for win, chs in ChannelConf.items():
            wind = PgPlotWindow()
            self.Winds.append(wind)
            xlink = None
            for ch in chs:
                wind.pgLayout.nextRow()
                p = wind.pgLayout.addPlot()
                p.hideAxis('bottom')
                p.setLabel('left',
                           ch['name'],
                           units='A',
                           **labelStyle)
                p.setDownsampling(auto=True,
                                  mode='subsample',
#                                  mode='peak',
                                  )
                p.setClipToView(True)
                c = p.plot(pen=pg.mkPen(ch['color'],
                                        width=ch['width']))
#                c = p.plot()
                self.Plots[ch['Input']] = p
                self.Curves[ch['Input']] = c

                if xlink is not None:
                    p.setXLink(xlink)
                xlink = p
            p.showAxis('bottom')
            p.setLabel('bottom', 'Time', units='s', **labelStyle)

    def SetViewTime(self, ViewTime):
        self.ViewTime = ViewTime
        self.ViewInd = int(ViewTime/self.Ts)

    def SetRefreshTime(self, RefreshTime):
        self.RefreshTime = RefreshTime
        self.RefreshInd = int(RefreshTime/self.Ts)

    def run(self, *args, **kwargs):
        while True:
            if self.Buffer.counter > self.RefreshInd:
                t = self.Buffer.GetTimes(self.ViewInd)
                self.Buffer.Reset()
                for i in range(self.nChannels):
                    self.Curves[i].setData(t, self.Buffer[-self.ViewInd:, i])
#                    self.Curves[i].setData(NewData[:, i])
#                self.Plots[i].setXRange(self.BufferSize/10,
#                                        self.BufferSize)
            else:
#                pg.QtGui.QApplication.processEvents()
                Qt.QThread.msleep(10)

    def AddData(self, NewData):
        self.Buffer.AddData(NewData)


##############################################################################

PSDPars = ({'name': 'Fs',
            'readonly': True,
            'type': 'float',
            'siPrefix': True,
            'suffix': 'Hz'},
           {'name': 'PSD Enable',
            'type': 'bool',
            'value': True},
           {'name': 'Fmin',
            'type': 'float',
            'value': 1,
            'step': 10,
            'siPrefix': True,
            'suffix': 'Hz'},
           {'name': 'nFFT',
            'title': 'nFFT 2**x',
            'type': 'int',
            'value': 15,
            'step': 1},
           {'name': 'scaling',
            'type': 'list',
            'values': ('density', 'spectrum'),
            'value': 'density'},
           {'name': 'nAvg',
            'type': 'int',
            'value': 4,
            'step': 1},
           {'name': 'AcqTime',
            'readonly': True,
            'type': 'float',
            'siPrefix': True,
            'suffix': 's'},
            )

PSDParsList = ('Fs', 'nFFT', 'nAvg', 'nChannels', 'scaling')


class PSDParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

#        self.QTparent = QTparent
        self.addChildren(PSDPars)
        self.param('Fs').sigValueChanged.connect(self.on_FsChange)
        self.param('Fmin').sigValueChanged.connect(self.on_FminChange)
        self.param('nFFT').sigValueChanged.connect(self.on_nFFTChange)
        self.param('nAvg').sigValueChanged.connect(self.on_nAvgChange)

    def on_FsChange(self):
        Fs = self.param('Fs').value()
        FMin = self.param('Fmin').value()
        nFFT = np.around(np.log2(Fs/FMin))+1
        self.param('nFFT').setValue(nFFT, blockSignal=self.on_nFFTChange)
        self.on_nAvgChange()

    def on_FminChange(self):
        Fs = self.param('Fs').value()
        FMin = self.param('Fmin').value()
        nFFT = np.around(np.log2(Fs/FMin))+1
        self.param('nFFT').setValue(nFFT, blockSignal=self.on_nFFTChange)
        self.on_nAvgChange()

    def on_nFFTChange(self):
        Fs = self.param('Fs').value()
        nFFT = self.param('nFFT').value()
        FMin = 2**nFFT/Fs
        self.param('Fmin').setValue(FMin, blockSignal=self.on_FminChange)
        self.on_nAvgChange()

    def on_nAvgChange(self):
        Fs = self.param('Fs').value()
        nFFT = self.param('nFFT').value()
        nAvg = self.param('nAvg').value()
        AcqTime = ((2**nFFT)/Fs)*nAvg
        self.param('AcqTime').setValue(AcqTime)

    def GetParams(self):
        PSDKwargs = {}
        for p in self.children():
            if p.name() not in PSDParsList:
                continue
            PSDKwargs[p.name()] = p.value()
        return PSDKwargs


class PSDPlotter(Qt.QThread):
    def __init__(self, Fs, nFFT, nAvg, nChannels, scaling, ChannelConf):
        super(PSDPlotter, self).__init__()

        self.scaling = scaling
        self.nFFT = 2**nFFT
        self.nChannels = nChannels
        self.Fs = Fs
        self.BufferSize = self.nFFT * nAvg
        self.Buffer = Buffer2D(self.Fs, self.nChannels,
                               self.BufferSize/self.Fs)

        self.Plots = [None]*nChannels
        self.Curves = [None]*nChannels

        self.wind = PgPlotWindow()
        self.wind.pgLayout.nextRow()
        p = self.wind.pgLayout.addPlot()
        p.setLogMode(True, True)
        p.setLabel('bottom', 'Frequency', units='Hz', **labelStyle)
        if scaling == 'density':
            p.setLabel('left', ' PSD', units=' V**2/Hz', **labelStyle)
        else:
            p.setLabel('left', ' PSD', units=' V**2', **labelStyle)

        for win, chs in ChannelConf.items():
            for ch in chs:
                c = p.plot(pen=pg.mkPen(ch['color'],
                                        width=ch['width']))
                self.Plots[ch['Input']] = p
                self.Curves[ch['Input']] = c

    def run(self, *args, **kwargs):
        while True:
            if self.Buffer.IsFilled():
                ff, psd = welch(self.Buffer,
                                fs=self.Fs,
                                nperseg=self.nFFT,
                                scaling=self.scaling,
                                axis=0)
                self.Buffer.Reset()
                for i in range(self.nChannels):
                    self.Curves[i].setData(ff, psd[:, i])
            else:
                Qt.QThread.msleep(10)

    def AddData(self, NewData):
        self.Buffer.AddData(NewData)



