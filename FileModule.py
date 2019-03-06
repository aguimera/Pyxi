#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 17:42:36 2019

@author: aguimera
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5.QtWidgets import QFileDialog
import h5py
from PyQt5 import Qt
import os


SaveFilePars = [{'name': 'Save File',
                 'type': 'action'},
                {'name': 'File Path',
                 'type': 'str',
                 'value': ''},
                {'name': 'MaxSize',
                 'type': 'int',
                 'siPrefix': True,
                 'suffix': 'B',
                 'limits': (1e6, 1e12),
                 'step': 100e6,
                 'value': 50e6}
                ]


class SaveFileParameters(pTypes.GroupParameter):
    def __init__(self, QTparent, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.QTparent = QTparent
        self.addChildren(SaveFilePars)
        self.param('Save File').sigActivated.connect(self.FileDialog)

    def FileDialog(self):
        RecordFile, _ = QFileDialog.getSaveFileName(self.QTparent,
                                                    "Recording File",
                                                    "",
                                                    )
        if RecordFile:
            if not RecordFile.endswith('.h5'):
                RecordFile = RecordFile + '.h5'
            self.param('File Path').setValue(RecordFile)

    def FilePath(self):
        return self.param('File Path').value()


class FileBuffer():
    def __init__(self, FileName, MaxSize, nChannels):
        self.FileBase = FileName.split('.h5')[0]
        self.PartCount = 0
        self.nChannels = nChannels
        self.MaxSize = MaxSize
        self._initFile()

    def _initFile(self):
        if self.MaxSize is not None:
            FileName = '{}_{}.h5'.format(self.FileBase, self.PartCount)
        else:
            FileName = self.FileBase + '.h5'
        self.FileName = FileName
        self.PartCount += 1
        self.h5File = h5py.File(FileName, 'w')
        self.Dset = self.h5File.create_dataset('data',
                                               shape=(0, self.nChannels),
                                               maxshape=(None, self.nChannels),
                                               compression="gzip")

    def AddSample(self, Sample):
        nSamples = Sample.shape[0]
        FileInd = self.Dset.shape[0]
        self.Dset.resize((FileInd + nSamples, self.nChannels))
        self.Dset[FileInd:, :] = Sample
        self.h5File.flush()

        stat = os.stat(self.FileName)
        if stat.st_size > self.MaxSize:
#            print(stat.st_size, self.MaxSize)
            self._initFile()


class DataSavingThread(Qt.QThread):
    def __init__(self, FileName, nChannels, MaxSize=None):
        super(DataSavingThread, self).__init__()
        self.NewData = None
        self.FileBuff = FileBuffer(FileName=FileName,
                                   nChannels=nChannels,
                                   MaxSize=MaxSize)

    def run(self, *args, **kwargs):
        while True:
            if self.NewData is not None:
                self.FileBuff.AddSample(self.NewData)
                self.NewData = None
            else:
                Qt.QThread.msleep(10)

    def AddData(self, NewData):
        if self.NewData is not None:
            print('Error Saving !!!!')
        self.NewData = NewData
