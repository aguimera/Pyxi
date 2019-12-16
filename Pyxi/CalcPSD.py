# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 13:04:39 2019

@author: Lucia
"""
from PyQt5 import Qt
from scipy.signal import welch
import numpy as np

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


class CalcPSD(Qt.QThread):
    PSDDone = Qt.pyqtSignal()
    def __init__(self, Fs, nFFT, nAvg, nChannels, scaling):
        super(CalcPSD, self).__init__()

        self.scaling = scaling
        self.nFFT = 2**nFFT
        self.nChannels = nChannels
        self.Fs = Fs
        self.BufferSize = self.nFFT * nAvg
        self.Buffer = Buffer2D(self.Fs, self.nChannels,
                               self.BufferSize/self.Fs)

    def run(self, *args, **kwargs):
        while True:
            if self.Buffer.IsFilled():
                self.ff, self.psd = welch(self.Buffer,
                                fs=self.Fs,
                                nperseg=self.nFFT,
                                scaling=self.scaling,
                                axis=0)
                print('PSD DONE EMIT')
                self.PSDDone.emit()

            else:
                Qt.QCoreApplication.processEvents()
                Qt.QThread.msleep(200)

    def AddData(self, NewData):
        self.Buffer.AddData(NewData)

    def stop(self):
        self.Buffer.Reset()
        self.terminate()