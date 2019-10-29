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
        
        #Save State
        self.SaveStateParams = FileMod.SaveSateParameters(QTparent=self,
                                                          name='State')        
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.SaveStateParams,))
        
        #SaveFile
        self.FileParams = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParams)
        
        #Sweeps
        self.SweepsParams = SwMod.SweepsParameters(name='Sweep Options')
        self.Parameters.addChild(self.SweepsParams)
        self.SweepsConfig = self.SweepsParams.param('SweepsConfig')
        
        #NifGenerator PXI
        self.NifGenParams = NifGen.NifGeneratorParameters(name='Pxi Generator')        
        self.Parameters.addChild(self.NifGenParams)
        
        #NiScope PXI
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
        self.threadSave = None
        
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
            
            #Sweep Changes
            if childName == 'Sweep Options.SweepsConfig.VgsSweep.timeXsweep':
                if data > 2:
                    self.NiScopeParams.tFetch.setValue(2)
                else:
                    self.NiScopeParams.tFetch.setValue(data)
           #Scope Changes
            if childName == 'Pxi Scope.AcqConfig.FsScope':
                n =round(self.NifGenParams.FsGen.value()/data)
                self.NiScopeParams.FsScope.setValue(self.NifGenParams.FsGen.value()/n)
            if childName == 'Pxi Scope.AcqConfig.NRow':
                self.PlotParams.SetChannels(self.NiScopeParams.GetRows())
                self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                              self.NifGenParams.GetCarriers())
                                                 )   
    def on_btnStart(self):       
        if self.threadAqc is None:
            print('started')
            self.treepar.setParameters(self.Parameters, showTop=False)
        
            self.AcSwCount = 0
            self.VgsSwCount=0
            self.TCount = 0
            self.CountTime = self.SweepsParams.CountTime

                
            self.GenKwargs = self.NifGenParams.GetGenParams()
            self.ScopeKwargs = self.NiScopeParams.GetRowParams()
            self.SweepsKwargs = self.SweepsParams.GetSweepParams()
            
            self.GenKwargs = self.SweepsParams.NextSweep(nAcSw = 0,
                                                         nVgsSw = 0,
                                                         **self.GenKwargs)
            
            self.SaveFiles()
            self.btnStart.setText("Stop Gen")
            self.OldTime = time.time()
                
            self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_New_Adq)  
            self.threadAqc.start()
            
            
        else:
            print('stopped')
            self.threadAqc.NewData.disconnect()
            self.threadAqc.stopSessions()
            self.threadAqc.terminate()
            self.threadAqc = None
            
            self.StopThreads()
            
    def on_New_Adq(self): #para que no haya overwrite en los sweeps

        print(self.TCount)
        if self.CountTime == 0:
            if self.threadSave is not None:
                    self.threadSave.NewDset(DSname='AcSw{0:03d}'.format(self.AcSwCount)+'Sw{0:03d}'.format(self.VgsSwCount))
            self.on_NewSample()
            self.on_New_Sweep()

        else:
            if self.TCount >= self.CountTime:
                if self.threadSave is not None:
                    self.threadSave.NewDset(DSname='AcSw{0:03d}'.format(self.AcSwCount)+'Sw{0:03d}'.format(self.VgsSwCount))
                self.on_NewSample()
                self.TCount = 0
                self.on_New_Sweep()
            else:
                self.on_NewSample()
                self.TCount += 1
            
    def on_New_Sweep(self):
        self.threadAqc.NewData.disconnect()
        self.threadAqc.stopSessions()
        self.threadAqc.terminate()
        self.threadAqc = None

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
                self.threadAqc.NewData.connect(self.on_New_Adq)  
                self.threadAqc.start()
        else:
            
            self.GenKwargs = self.SweepsParams.NextSweep(nAcSw = self.AcSwCount,
                                                         nVgsSw = self.VgsSwCount,
                                                         **self.GenKwargs)

            self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_New_Adq)  
            self.threadAqc.start()
      
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        if self.threadSave is not None:
#            No usar Int hasta que se haya arreglado problema
#            Problema: Range scope no es exacto con lo cual hay valores que no deberian saturar y saturan
#            self.threadSave.AddData(self.threadAqc.IntData)          
            self.threadSave.AddData(self.threadAqc.OutData)
    
    def SaveFiles(self):
        FileName = self.FileParams.param('File Path').value()
        if FileName ==  '':
            print('No file')
        else:
            if os.path.isfile(FileName):
                print('Remove File')
                os.remove(FileName)  
            MaxSize = self.FileParams.param('MaxSize').value()
            self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                       nChannels=self.ScopeKwargs['NRow'],
                                                       MaxSize=MaxSize,
                                                       dtype='float' #comment when int save problem solved
                                                       )
            self.threadSave.start()
            
            GenName = FileName+'_GenConfig.dat'
            ScopeName = FileName+'_ScopeConfig.dat'
            SweepsName = FileName+'_SweepsConfig.dat'
                
            if os.path.isfile(ScopeName):
                print('Overwriting  file')
                OutScope = input('y/n + press(Enter)')
                if OutScope =='y':
                    FileMod.GenArchivo(ScopeName, self.ScopeKwargs)
                    FileMod.GenArchivo(GenName, self.GenKwargs)
                    FileMod.GenArchivo(SweepsName, self.SweepsKwargs)
            else:
                FileMod.GenArchivo(ScopeName, self.ScopeKwargs)
                FileMod.GenArchivo(GenName, self.GenKwargs)
                FileMod.GenArchivo(SweepsName, self.SweepsKwargs)
                
    def StopThreads(self):
        if self.threadSave is not None:
            self.threadSave.stop()
            self.threadSave = None            
                
if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        