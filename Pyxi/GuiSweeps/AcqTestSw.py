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
        
        #Demodulación
        self.DemodParams = DemMod.DemodParameters(name='Demod Options')     
        self.Parameters.addChild(self.DemodParams)
        self.DemodConfig = self.DemodParams.param('DemodConfig')
        
        
        self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')
        
        
        layout.addWidget(self.treepar)
        
        self.setGeometry(550, 10, 300, 700)
        self.setWindowTitle('MainWindow')
        self.btnStart.clicked.connect(self.on_btnStart)
        
        self.threadAqc = None
        self.threadDemodAqc = None
        self.threadDemodSave = None
        
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
            #Generator Changes
            if childName == 'Pxi Generator.CarriersConfig':
                self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                              self.NifGenParams.GetCarriers())
                                                )
            
            #Demodulation Changes
            if childName == 'Demod Options.DemodConfig.DSFact':
                self.DemodParams.ReCalc_DSFact(self.NiScopeParams.BufferSize.value())
                  
            if childName == 'Demod Options.DemodConfig.DSFs':
                self.DemodPsdPlotParams.param('Fs').setValue(data)
                self.DemodPlotParams.param('Fs').setValue(data)
                if data >= np.min(self.NifGenParams.Freqs):
                    print('WARNING: FsDemod is higher than FsMin')
                    
            
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
            self.DemodKwargs = self.DemodParams.GetParams()    
            self.SweepsKwargs = self.SweepsParams.GetSweepParams()
            
            self.GenKwargs = self.SweepsParams.NextSweep(nAcSw = 0,
                                                         nVgsSw = 0,
                                                         **self.GenKwargs)
            
            self.SaveFiles()
            self.btnStart.setText("Stop Gen")
            self.OldTime = time.time()
                
            self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_New_Adq)  
            self.threadDemodAqc = DemMod.DemodThread(Fcs=self.NifGenParams.GetCarriers(), 
                                                     RowList=self.threadAqc.RowsList,
                                                     FetchSize=self.threadAqc.BufferSize, 
                                                     **self.DemodKwargs)
            self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
            self.threadDemodAqc.start()
            self.threadAqc.start()
            
            
        else:
            print('stopped')
            self.threadAqc.NewData.disconnect()
            self.threadAqc.stopSessions()
            self.threadAqc.terminate()
            self.threadAqc = None
            
            self.StopThreads()
            
    def on_New_Adq(self): #para que no haya overwrite en los sweeps
        if self.threadDemodAqc is not None:
                self.threadDemodAqc.AddData(self.threadAqc.OutData)
            
        print(self.TCount)
        if self.CountTime == 0:
            if self.threadSweepsSave is not None:
                    self.threadSweepsSave.NewDset(DSname='AcSw{0:03d}'.format(self.AcSwCount)+'Sw{0:03d}'.format(self.VgsSwCount))
#            self.on_NewSample()
            self.on_New_Sweep()

        else:
            if self.TCount >= self.CountTime:
                if self.threadSweepsSave is not None:
                    self.threadSweepsSave.NewDset(DSname='AcSw{0:03d}'.format(self.AcSwCount)+'Sw{0:03d}'.format(self.VgsSwCount))
#                self.on_NewSample()
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
                self.threadAqc.NewData.disconnect()
                self.threadAqc.stopSessions()
                self.threadAqc.terminate()
                self.threadAqc = None
                self.StopThreads()
                
            else:
                self.VgsSwCount = 0
                self.GenKwargs = self.SweepsParams.NextSweep(nAcSw = self.AcSwCount,
                                                             nVgsSw = self.VgsSwCount,
                                                             **self.GenKwargs)
                
                self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
                self.threadAqc.NewData.connect(self.on_New_Adq)  
                self.threadDemodAqc = DemMod.DemodThread(Fcs=self.NifGenParams.GetCarriers(), 
                                                     RowList=self.threadAqc.RowsList,
                                                     FetchSize=self.threadAqc.BufferSize, 
                                                     **self.DemodKwargs)
                self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
                self.threadAqc.start()
        else:
            
            self.GenKwargs = self.SweepsParams.NextSweep(nAcSw = self.AcSwCount,
                                                         nVgsSw = self.VgsSwCount,
                                                         **self.GenKwargs)

            self.threadAqc = DataAcq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_New_Adq)  
            self.threadDemodAqc = DemMod.DemodThread(Fcs=self.NifGenParams.GetCarriers(), 
                                                     RowList=self.threadAqc.RowsList,
                                                     FetchSize=self.threadAqc.BufferSize, 
                                                     **self.DemodKwargs)
            self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
            self.threadAqc.start()
      
    def on_NewDemodSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
            
        if self.DemodConfig.param('OutType').value() == 'Abs':
            OutDemodData = np.abs(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Real':
            OutDemodData = np.real(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Imag':
            OutDemodData = np.imag(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Angle':
            OutDemodData = np.angle(self.threadDemodAqc.OutDemodData, deg=True)    
            
        if self.threadSweepsSave is not None:
            self.threadSweepsSave.AddData(OutDemodData)
            
    def SaveFiles(self):
        FileName = self.FileParams.param('File Path').value()
        if FileName ==  '':
            print('No file')
        else:
            if os.path.isfile(FileName):
                print('Remove File')
                os.remove(FileName)  
            MaxSize = self.FileParams.param('MaxSize').value()
            self.threadSweepsSave = FileMod.DataSavingThread(FileName=FileName,
                                                             nChannels=self.ScopeKwargs['NRow']*len(self.NifGenParams.Freqs),
                                                             MaxSize=MaxSize,
                                                             dtype='float')
                
            self.threadSweepsSave.start()
            
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
        if self.threadDemodAqc is not None:
            self.threadDemodAqc.NewData.disconnect()
            self.threadDemodAqc.stop()
            self.threadDemodAqc = None 
        if self.threadDemodSave is not None:
            self.threadDemodSave.stop()
            self.threadDemodSave = None
            
if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()    
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        