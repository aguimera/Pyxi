# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 11:00:49 2019

@author: Lucia
"""
#Development Square Function
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
import pickle

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
        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParameters)
        
        self.PSDParams = PltMod.PSDParameters(name='PSD Options')
        self.PSDParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
        self.PSDParams.param('Fmin').setValue(50)
        self.PSDParams.param('nAvg').setValue(50)
        self.PSDEnable = self.PSDParams.param('PSDEnable').value()
        self.Parameters.addChild(self.PSDParams)
        
        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.NiScopeParams.GetChannels())
        self.PlotParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
        self.PltEnable = self.PlotParams.param('PlotEnable').value()

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
        self.threadSave = None
        self.threadPlotter = None
        self.threadPSDPlotter = None

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

        if childName == 'Scope.FetchConfig.FsScope':
            n =round(self.NifGenParams.FsGen.value()/data)
            print(n)
            self.NifGenParams.FsGen.setValue(data*n)
            self.PlotParams.param('Fs').setValue(data)
            self.PSDParams.param('Fs').setValue(data)
            
        if childName == 'Scope.FetchConfig.NRow':
            self.PlotParams.SetChannels(self.NiScopeParams.GetChannels())
            
        if childName == 'Plot options.RefreshTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetRefreshTime(data)    

        if childName == 'Plot options.ViewTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetViewTime(data)   
                
        if childName == 'Plot options.PlotEnable':
            self.PltEnable = data
            if self.threadAqc is not None:
                self.UpdatePlots()
                
        if childName == 'PSD Options.PSDEnable':
            self.PSDEnable = data
            if self.threadAqc is not None:
                self.UpdatePlots()     
                
    def on_btnGen(self):
        print('h')
        if self.threadAqc is None:
            self.GenKwargs = self.NifGenParams.GetParams()
            self.ScopeKwargs = self.NiScopeParams.GetParams()
            
            self.threadAqc = FMacq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_NewSample)
            
            self.SaveFiles()            
                
            self.GenPlots()

            self.threadAqc.start()
            self.btnGen.setText("Stop Gen")
            self.OldTime = time.time()
        else:
            self.threadAqc.NewData.disconnect()
            self.threadAqc.stopSessions()
            self.threadAqc.stopTimer()
            self.threadAqc.terminate()
            self.threadAqc = None
            
            if self.threadSave is not None:
                self.threadSave.stop()
                self.threadSave = None
            
            self.DestroyPlotter()
            self.DestroyPSD()
                
            self.btnGen.setText("Start Gen")
            
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        if self.threadSave is not None:
            self.threadSave.AddData(self.threadAqc.IntData)
        
        if self.threadPlotter is not None:
            self.threadPlotter.AddData(self.threadAqc.OutData)
            
        if self.threadPSDPlotter is not None:  
            self.threadPSDPlotter.AddData(self.threadAqc.OutData)
            
        print('Sample time', Ts)

    def GenPlots(self):
        PlotterKwargs = self.PlotParams.GetParams()
        ScopeKwargs = self.NiScopeParams.GetParams()
        if self.threadPlotter is None:
            if self.PltEnable == True:           
                self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
                self.threadPlotter.start()
        
        if self.threadPSDPlotter is None:
            if self.PSDEnable == True:        
                self.threadPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                          nChannels=ScopeKwargs['NRow'],
                                                          **self.PSDParams.GetParams())
                self.threadPSDPlotter.start() 
                
    def DestroyPlotter(self):
        if self.threadPlotter is not None:    
            self.threadPlotter.stop()
            self.threadPlotter = None
            
    def DestroyPSD(self):
        if self.threadPSDPlotter is not None: 
            self.threadPSDPlotter.stop()
            self.threadPSDPlotter = None 
            
    def UpdatePlots(self):
        if self.PltEnable == False:
            self.DestroyPlotter()
        if self.PSDEnable == False:
            self.DestroyPSD()
        else:
            self.GenPlots()
                    
    def SaveFiles(self):
        FileName = self.FileParameters.param('File Path').value()
        if FileName ==  '':
            print('No file')
        else:
            if os.path.isfile(FileName):
                print('Remove File')
                os.remove(FileName)  
            MaxSize = self.FileParameters.param('MaxSize').value()
            self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                       nChannels=self.ScopeKwargs['NRow'],
                                                       MaxSize=MaxSize)
            self.threadSave.start()
         
            GenName = FileName+'_GenConfig.dat'
            ScopeName = FileName+'_ScopeConfig.dat'
            if os.path.isfile(GenName):
                print('Overwriting  file')
                OutGen = input('y/n + press(Enter)')
                if OutGen =='y':
                    self.GenArchivo(GenName, self.GenKwargs)
            else:
                self.GenArchivo(GenName, self.GenKwargs)
            if os.path.isfile(ScopeName):
                print('Overwriting  file')
                OutScope = input('y/n + press(Enter)')
                if OutScope =='y':
                    self.GenArchivo(ScopeName, self.ScopeKwargs)
            else:
                self.GenArchivo(ScopeName, self.ScopeKwargs)
                
    def GenArchivo(self, name, dic2Save):
        with open(name, "wb") as f:
            pickle.dump(dic2Save, f)
            
if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
        