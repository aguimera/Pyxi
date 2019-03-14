# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 11:00:49 2019

@author: Lucia
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
import Pyxi.FMacqThread as FMacq

class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()

        layout = Qt.QVBoxLayout(self) 

        self.btnGen = Qt.QPushButton("Start Gen!")
        layout.addWidget(self.btnGen)

        self.StateParams = FileMod.SaveSateParameters(QTparent=self,
                                                      name='State')
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.StateParams,))

        self.NifGenParams = FMacq.NifGeneratorParameters(name='NifGenerator')        
        self.Parameters.addChild(self.NifGenParams)

        
        self.NiScopeParams = FMacq.NiScopeParameters(name = 'Scope')
        
        self.Parameters.addChild(self.NiScopeParams)
#       
        self.PSDParams = PltMod.PSDParameters(name='PSD Options')
        self.PSDParams.param('Fs').setValue(self.NifGenParams.Fs.value())
        self.PSDParams.param('Fmin').setValue(50)
        self.PSDParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.PSDParams)
        
        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.NiScopeParams.GetChannels())
        self.PlotParams.param('Fs').setValue(self.NifGenParams.Fs.value())

        self.Parameters.addChild(self.PlotParams)

        
        
        self.Parameters.sigTreeStateChanged.connect(self.on_pars_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')
        
        
        layout.addWidget(self.treepar)

        self.setGeometry(550, 10, 300, 700)
        self.setWindowTitle('MainWindow')
        self.btnGen.clicked.connect(self.on_btnGen)
        
        self.threadAqc = None

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

        if childName == 'NifGenerator.SamplingConfig.Fs':
            self.NiScopeParams.Fs.setValue(data)
#            t = self.NiScopeParams.BS.value()/data
#            self.NiScopeParams.tFetch.setValue(t)

    def on_btnGen(self):
        print('h')
        if self.threadAqc is None:
            
            PlotterKwargs = self.PlotParams.GetParams()
            GenKwargs = self.NifGenParams.GetParams()
            ScopeKwargs = self.NiScopeParams.GetParams()
            
            self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
            self.threadPlotter.start()
            
            self.threadPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                      nChannels=ScopeKwargs['NRow'],
                                                      **self.PSDParams.GetParams())
            self.threadPSDPlotter.start()    
 

            
            self.threadAqc = FMacq.DataAcquisitionThread(**GenKwargs, **ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_NewSample)
            
            
#            self.threadGen.start()
#
            self.btnGen.setText("Stop Gen")
            self.threadAqc.start()
            self.OldTime = time.time()
        else:
            self.threadAqc.NewData.disconnect()
            self.threadAqc.terminate()
            self.threadAqc = None
            self.btnGen.setText("Start Gen")
            
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
#        if self.threadSave is not None:
#            self.threadSave.AddData(self.threadGen.OutData)
        self.threadPlotter.AddData(self.threadAqc.OutData)
        self.threadPSDPlotter.AddData(self.threadAqc.OutData)
        print('Sample time', Ts)


if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
        