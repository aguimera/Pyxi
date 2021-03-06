#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 17:37:09 2019

@author: aguimera
"""

from __future__ import print_function
import os
from PyQt5 import Qt
from PyQt5.QtWidgets import QFileDialog

import numpy as np
import time

import pyqtgraph as pg

import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
from itertools import  cycle
import copy
from scipy.signal import welch

import Pyxi.FileModule as FileMod
import Pyxi.SampleGenerator as SampGen
import Pyxi.PlotModule as PltMod


class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()

        layout = Qt.QVBoxLayout(self) 

        self.btnGen = Qt.QPushButton("Start Gen!")
        layout.addWidget(self.btnGen)

        self.SaveStateParams = FileMod.SaveSateParameters(self, name='State')        
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.SaveStateParams,))

        self.DataGenParams = SampGen.DataGeneratorParameters(name='Data Generator')
        self.DataGenParams.param('Col0').param('Freq').setValue(75e3)
        self.DataGenParams.param('Col1').param('Freq').setValue(100e3)
        self.DataGenParams.param('Col2').param('Freq').setValue(125e3)
        self.DataGenParams.param('Col3').param('Freq').setValue(150e3)

        self.DataGenParams.param('Col0').param('Fsig').setValue(1e3)
        self.DataGenParams.param('Col1').param('Fsig').setValue(800)
        self.DataGenParams.param('Col2').param('Fsig').setValue(250)
        self.DataGenParams.param('Col3').param('Fsig').setValue(10)
        
        self.Parameters.addChild(self.DataGenParams)

        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParameters)

        self.PSDParams = PltMod.PSDParameters(name='PSD Options')
        self.PSDParams.param('Fs').setValue(self.DataGenParams.param('Fs').value())
        self.PSDParams.param('Fmin').setValue(50)
        self.PSDParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.PSDParams)
        
        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.DataGenParams.GetChannels())
        self.PlotParams.param('Fs').setValue(self.DataGenParams.param('Fs').value())

        self.Parameters.addChild(self.PlotParams)
        
        self.Parameters.sigTreeStateChanged.connect(self.on_pars_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(550, 10, 300, 700)
        self.setWindowTitle('MainWindow')
        self.btnGen.clicked.connect(self.on_btnGen)
    
        self.threadGen = None
        self.threadSave = None
        self.threadPlotter = None

 
    def on_pars_changed(self, param, changes):
        print("tree changes:")
        for param, change, data in changes:
            path = self.Parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        print('  parameter: %s'% childName)
        print('  change:    %s'% change)
        print('  data:      %s'% str(data))
        print('  ----------')

        if childName == 'Data Generator.nChannels':
            self.PlotParams.SetChannels(self.DataGenParams.GetChannels())

        if childName == 'Data Generator.Fs':
            self.PlotParams.param('Fs').setValue(data)
            self.PSDParams.param('Fs').setValue(data)

        if childName == 'Plot options.RefreshTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetRefreshTime(data)    

        if childName == 'Plot options.ViewTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetViewTime(data)
            
    def on_btnGen(self):
        if self.threadGen is None:
            GenKwargs = self.DataGenParams.GetParams()
            self.threadGen = SampGen.DataSamplingThread(**GenKwargs)
            self.threadGen.NewSample.connect(self.on_NewSample)
            self.threadGen.start()

            FileName = self.FileParameters.param('File Path').value()
            if FileName ==  '':
                print('No file')
            else:
                if os.path.isfile(FileName):
                    print('Remove File')
                    os.remove(FileName)  
                MaxSize = self.FileParameters.param('MaxSize').value()
                self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=GenKwargs['Rows'],
                                                           MaxSize=MaxSize)
                self.threadSave.start()

            PlotterKwargs = self.PlotParams.GetParams()
            print(PlotterKwargs)
            self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
            self.threadPlotter.start()
            
            self.threadPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                      nChannels=GenKwargs['Rows'],
                                                      **self.PSDParams.GetParams())
            self.threadPSDPlotter.start()            

            self.btnGen.setText("Stop Gen")
            self.OldTime = time.time()
            self.Tss = []
        else:
            self.threadGen.NewSample.disconnect()
            self.threadGen.terminate()
            self.threadGen = None

            if self.threadSave is not None:
                self.threadSave.terminate()
                self.threadSave = None

            self.threadPlotter.terminate()
            self.threadPlotter = None

            self.btnGen.setText("Start Gen")
            
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.Tss.append(Ts)
        self.OldTime = time.time()
        if self.threadSave is not None:
            self.threadSave.AddData(self.threadGen.OutData)
        self.threadPlotter.AddData(self.threadGen.OutData)
        self.threadPSDPlotter.AddData(self.threadGen.OutData)
        print('Sample time', Ts, np.mean(self.Tss))


if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
        