# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 13:04:39 2019

@author: Lucia
"""
from PyQt5 import Qt
from scipy.signal import welch
import numpy as np

import PyCont.PlotModule as PltBuffer2D

class CalcPSD(Qt.QThread):
    PSDDone = Qt.pyqtSignal()
    def __init__(self, Fs, nFFT, nAvg, nChannels, scaling):
        super(CalcPSD, self).__init__()

        self.scaling = scaling
        self.nFFT = 2**nFFT
        self.nChannels = nChannels
        self.Fs = Fs
        self.BufferSize = self.nFFT * nAvg
        self.Buffer = PltBuffer2D.Buffer2D(self.Fs, self.nChannels,
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