# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 13:58:06 2019

@author: aemdlabs
"""

from __future__ import print_function
import os

import numpy as np
from scipy.signal import welch
import time
import copy
import pickle

from PyQt5 import Qt
from PyQt5.QtWidgets import QFileDialog

import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
from itertools import  cycle

import Pyxi.FileModule as FileMod
import Pyxi.SampleGenerator as SampGen
import Pyxi.PlotModule as PltMod
import Pyxi.DataAcquisition as DataAcq
import Pyxi.NifGenerator as NifGen
import Pyxi.NiScope as NiScope
import Pyxi.DemodModule as DemMod
import Pyxi.Sweep as SwMod


class MainWindow(Qt.QWidget):
    ''' Main Window '''
    def __init__(self):      
        super(MainWindow, self).__init__()
        
        self.setFocusPolicy(Qt.Qt.WheelFocus)       
        layout = Qt.QVBoxLayout(self) 
        
        self.btnStart = Qt.QPushButton("Start Gen and Adq!")
        layout.addWidget(self.btnStart)
        
        self.SaveStateParams = FileMod.SaveSateParameters(QTparent=self,
                                                          name='State')        
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.SaveStateParams,))
        
        self.SweepsParams = SwMod.SweepsParameters(name='Sweep Options')
        self.Parameters.addChild(self.SweepsParams)
        self.SweepsConfig = self.SweepsParams.param('SweepsConfig')
        
        self.NifGenParams = NifGen.NifGeneratorParameters(name='Pxi Generator')        
        self.Parameters.addChild(self.NifGenParams)
        
        self.NiScopeParams = NiScope.NiScopeParameters(name='Pxi Scope')
        self.Parameters.addChild(self.NiScopeParams) 
        
        self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')
        
        
        layout.addWidget(self.treepar)
        
        self.setGeometry(550, 10, 300, 700)
        self.setWindowTitle('MainWindow')
        self.btnStart.clicked.connect(self.on_btnStart)
        
        self.threadAqc = None
        
    def on_Params_changed(self, param, changes):
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
        
            if childName == 'Sweep Options.SweepsConfig.VgsSweep.timeXsweep':
                self.NiScopeParams.tFetch.setValue(data)
                
    def on_btnStart(self):       
        if self.threadAqc is None:
            print('started')
            self.treepar.setParameters(self.Parameters, showTop=False)
            
            self.GenKwargs = self.NifGenParams.GetGenParams()
            self.ScopeKwargs = self.NiScopeParams.GetRowParams()
            self.SweepsKwargs = self.SweepsParams.GetSweepParams()

            self.btnStart.setText("Stop Gen")
            self.OldTime = time.time()
            
            self.OnSweep = True
            self.AcSwCount = 0
            self.VgsSwCount=0
            
            self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_New_Sweep)  
            self.threadAqc.start()
            
#            self.on_Sweep()
            
        else:
            print('stopped')
            self.threadAqc.NewData.disconnect()
            self.threadAqc.stopSessions()
            self.threadAqc.terminate()
            self.threadAqc = None
            
#    def on_Sweep(self):
#        if self.OnSweep is True:
            
    def on_New_Sweep(self):
        self.threadAqc.NewData.disconnect()
        self.threadAqc.stopSessions()
        self.threadAqc.terminate()
        self.threadAqc = None
        print(self.AcSwCount, self.VgsSwCount)
        self.VgsSwCount += 1
        if self.VgsSwCount >= self.SweepsParams.VgsConfig.param('nSweeps').value():
            self.AcSwCount += 1
            if self.AcSwCount >= self.SweepsParams.AcConfig.param('nSweeps').value():
                print('stopped')
                self.btnStart.setText("Start Gen and Adq!")  
                
            else:
                self.VgsSwCount = 0
                self.GenKwargs = self.SweepsParams.NextSweep(nAcSw = self.AcSwCount,
                                                             nVgsSw = self.VgsSwCount,
                                                             **self.GenKwargs)
                self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
                self.threadAqc.NewData.connect(self.on_New_Sweep)  
                self.threadAqc.start()
        else:
            
            self.GenKwargs = self.SweepsParams.NextSweep(nAcSw = self.AcSwCount,
                                                         nVgsSw = self.VgsSwCount,
                                                         **self.GenKwargs)
            self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_New_Sweep)  
            self.threadAqc.start()
        
        print(self.AcSwCount, self.VgsSwCount)   
            
if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        