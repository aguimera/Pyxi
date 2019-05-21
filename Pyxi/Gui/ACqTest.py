# -*- coding: utf-8 -*-
"""
Created on Tue May 21 14:20:23 2019

@author: Lucia
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
import Pyxi.FMacqThread as FMacq
import Pyxi.DemodModule as DemMod

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
        
        self.FileParams = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParams)
        
        self.NifGenParams = FMacq.NifGeneratorParameters(name='Pxi Generator')        
        self.Parameters.addChild(self.NifGenParams)
        
        self.NiScopeParams = FMacq.NiScopeParameters(name='Pxi Scope')
        self.Parameters.addChild(self.NiScopeParams)
        
        self.PsdPlotParams = PltMod.PSDParameters(name='PSD Plot Options')
        self.PsdPlotParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
        self.PsdPlotParams.param('Fmin').setValue(50)
        self.PsdPlotParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.PsdPlotParams)
        
        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.NiScopeParams.GetChannels())
        self.PlotParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())

        self.Parameters.addChild(self.PlotParams)
        
        self.DemodParams = DemMod.DemodParameters(name = 'Demod Options')     
        self.Parameters.addChild(self.DemodParams)
        self.DemodConfig = self.DemodParams.param('DemodConfig')
        
        self.DemodPsdPlotParams = PltMod.PSDParameters(name='Demod PSD Options')
        self.DemodPsdPlotParams.param('Fs').setValue(
                                                    (self.DemodConfig.param('FsDemod').value())
                                                    /(self.DemodConfig.param('DSFact').value())
                                                    )
        self.DemodPsdPlotParams.param('Fmin').setValue(50)
        self.DemodPsdPlotParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.DemodPsdPlotParams)
        
        self.DemodPlotParams = PltMod.PlotterParameters(name='Demod Plot options')
        self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                    self.NifGenParams.GetCarriers())
                                      )
        self.DemodPlotParams.param('Fs').setValue(
                                                (self.DemodConfig.param('FsDemod').value())
                                                /(self.DemodConfig.param('DSFact').value())
                                                )

        self.Parameters.addChild(self.DemodPlotParams)
        
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
        self.threadPlotter = None
        self.threadPsdPlotter = None
        self.threadDemodAqc = None
        self.threadDemodSave = None
        self.threadDemodPlotter = None
        self.threadDemodPsdPlotter = None
        
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
  
            if childName == 'NifGenerator.CarriersConfig':
                self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                              self.NifGenParams.GetCarriers())
                                                                              )
            
            if childName == 'Scope.FetchConfig.FsScope':
                n =round(self.NifGenParams.FsGen.value()/data)
                self.NiScopeParams.FsScope.setValue(self.NifGenParams.FsGen.value()/n)
                self.PlotParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
                self.PsdParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
                self.DemodConfig.param('FsDemod').setValue(self.NiScopeParams.FsScope.value())
                
            if childName == 'Scope.FetchConfig.NRow':
                self.PlotParams.SetChannels(self.NiScopeParams.GetChannels())
                self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                            self.NifGenParams.GetCarriers())
                                                 )
            
            if childName == 'Demod Options.DemodConfig.DSFs':
                self.DemodPsdPlotParams.param('Fs').setValue(data)
                self.DemodPlotParams.param('Fs').setValue(data)
                if data >= np.min(self.NifGenParams.Freqs):
                    print('WARNING: FsDemod is higher than FsMin')
            
            if self.threadPlotter is not None: 
                if childName == 'Plot options.RefreshTime':
                    self.threadPlotter.SetRefreshTime(data)    
                if childName == 'Plot options.ViewTime':
                    self.threadPlotter.SetViewTime(data)  
                    
            if self.threadDemodPlotter is not None:         
                if childName == 'Demod Plot options.RefreshTime':
                    self.threadDemodPlotter.SetRefreshTime(data)       
                if childName == 'Demod Plot options.ViewTime':
                    self.threadDemodPlotter.SetViewTime(data) 
             
            if self.threadAqc is not None:  
                if childName == 'Plot options.PlotEnable' or childName == 'Demod Plot options.PlotEnable' :
                    self.Gen_Destroy_Plotters()
                if childName == 'PSD Options.PSDEnable' or childName == 'Demod PSD Options.PSDEnable':
                    self.Gen_Destroy_PsdPlotter() 

    def Gen_Destroy_Plotters(self):
        if self.threadPlotter is None:
            if self.PlotParams.param('PlotEnable').value() == True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
                self.threadPlotter.start()
            if self.PlotParams.param('PlotEnable').value() == False:
                self.threadPlotter.stop()
                self.threadPlotter = None
                
        if self.threadDemodPlotter is None:
            if self.DemodPlotParams.param('PlotEnable').value() == True:
                PlotterDemodKwargs = self.DemodPlotParams.GetParams()
                self.threadDemodPlotter = PltMod.Plotter(**PlotterDemodKwargs)
                self.threadDemodPlotter.start()
            if self.DemodPlotParams.param('PlotEnable').value() == False:
                self.threadDemodPlotter.stop()
                self.threadDemodPlotter = None

    def Gen_Destroy_PsdPlotter(self):
        if self.threadPsdPlotter is None:
            if self.PsdPlotParams.param('PSDEnable').value() == True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPsdPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                          nChannels=self.ScopeKwargs['NRow'],
                                                          **self.PSDParams.GetParams())
                self.threadPsdPlotter.start() 
            if self.PsdPlotParams.param('PSDEnable').value() == False:
                self.threadPSDPlotter.stop()
                self.threadPSDPlotter = None 
                
        if self.threadDemodPsdPlotter is None:
            if self.DemodPsdPlotParams.param('PSDEnable').value() == True:
                PlotterDemodKwargs = self.DemodPlotParams.GetParams()
                self.threadDemodPsdPlotter = PltMod.PSDPlotter(ChannelConf=PlotterDemodKwargs['ChannelConf'],
                                                               nChannels=self.ScopeKwargs['NRow']*len(self.NifGenParams.Freqs),
                                                               **self.DemodPsdPlotParams.GetParams())
                self.threadDemodPsdPlotter.start() 
            if self.DemodPsdPlotParams.param('PSDEnable').value() == False:
                self.threadDemodPsdPlotter.stop()
                self.threadDemodPsdPlotter = None   
                
    def on_btnStart(self):
        print('started')
        if self.threadAqc is None:
            self.treepar.setParameters(self.Parameters, showTop=False)
            self.GenKwargs = self.NifGenParams.GetParams()
            self.ScopeKwargs = self.NiScopeParams.GetParams()
            self.DemodKwargs = self.DemodParams.GetParams()
            
            self.threadAqc = FMacq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_NewSample)
                       
            self.GenPsdPlotter()
            self.GenPlotter()
            self.SaveFiles()     
            
            if self.DemodConfig.param('DemEnable').value() == True:
                self.threadDemodAqc = DemMod.DemodThread(Fcs=self.NifGenParams.GetCarriers(), 
                                                         RowList=self.threadAqc.RowsList,
                                                         FetchSize=self.threadAqc.BufferSize, 
                                                         **self.DemodKwargs)
                self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
                self.threadDemodAqc.start()
            
            
            self.threadAqc.start()
            self.btnGen.setText("Stop Gen")
            self.OldTime = time.time()
        else:
            self.threadAqc.NewData.disconnect()
            self.threadAqc.stopSessions()
            self.threadAqc.terminate()
            self.threadAqc = None
            
            self.StopThreads()
            
            self.btnGen.setText("Start Gen")           

    def StopThreads(self):
        if self.threadSave is not None:
            self.threadSave.stop()
            self.threadSave = None
                
        if self.threadDemodAqc is not None:
            self.threadDemodAqc.stop()
            self.threadDemodAqc = None
        
        if self.threadPlotter is not None:
            self.threadPlotter.stop()
            self.threadPlotter = None
            
        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.stop()
            self.threadPsdPlotter = None
            
        if self.threadDemodSave is not None:
            self.threadDemodSave.stop()
            self.threadDemodSave = None
            
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.stop()
            self.threadDemodPlotter = None
        
        if self.threadDemodPsdPlotter is not None:
            self.threadDemodPsdPlotter.stop()
            self.threadDemodPsdPlotter = None

    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        if self.threadSave is not None:
            self.threadSave.AddData(self.threadAqc.IntData)
        
        if self.threadPlotter is not None:
            self.threadPlotter.AddData(self.threadAqc.OutData)
            
        if self.threadPSDPlotter is not None:  
            self.threadPsdPlotter.AddData(self.threadAqc.OutData)
       
        if self.DemodConfig.param('DemEnable').value() == True:
            if self.threadDemodAqc is not None:
                self.threadDemodAqc.AddData(self.threadAqc.OutData)
                
        print('Sample time', Ts)

    def on_NewDemodSample(self):
        if self.DemodConfig.param('OutType').value() == 'Abs':
            OutDemodData = np.abs(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Real':
            OutDemodData = np.real(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Imag':
            OutDemodData = np.imag(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Angle':
            OutDemodData = np.angle(self.threadDemodAqc.OutDemodData, deg=True)   
         
        if self.threadDemodSave is not None:
            self.threadDemodSave.AddData(OutDemodData)
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.AddData(OutDemodData)
            
        if self.threadDemodPsdPlotter is not None:  
            self.threadDemodPsdPlotter.AddData(OutDemodData)

        if self.threadDemodPsdPlotter is not None:  
            self.threadDemodPsdPlotter.AddData(OutDemodData)

    def SaveFiles(self):
        FileName = self.FileParameters.param('File Path').value()
        if FileName ==  '':
            print('No file')
        else:
            if os.path.isfile(FileName):
                print('Remove File')
                os.remove(FileName)  
            MaxSize = self.FileParameters.param('MaxSize').value()
            if self.DemodConfig.param('DemEnable').value() == False:
                self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=self.ScopeKwargs['NRow'],
                                                           MaxSize=MaxSize)
                self.threadSave.start()
            
            if self.DemodConfig.param('DemEnable').value() == True:
                self.threadDemodSave = FileMod.DataSavingThread(FileName=FileName,
                                                                nChannels=self.ScopeKwargs['NRow']*len(self.NifGenParams.Freqs),
                                                                MaxSize=MaxSize,
                                                                dtype='float')
                
                self.threadDemodSave.start()

            GenName = FileName+'_GenConfig.dat'
            ScopeName = FileName+'_ScopeConfig.dat'
            DemodName = FileName+'_DemodConfig.dat'
            if os.path.isfile(GenName):
                print('Overwriting  file')
                OutGen = input('y/n + press(Enter)')
                if OutGen =='y':
                    FileMod.GenArchivo(GenName, self.GenKwargs)
            else:
                FileMod.GenArchivo(GenName, self.GenKwargs)
                
            if os.path.isfile(ScopeName):
                print('Overwriting  file')
                OutScope = input('y/n + press(Enter)')
                if OutScope =='y':
                    FileMod.GenArchivo(ScopeName, self.ScopeKwargs)
            else:
                FileMod.GenArchivo(ScopeName, self.ScopeKwargs)
                
            if os.path.isfile(DemodName):
                print('Overwriting  file')
                OutScope = input('y/n + press(Enter)')
                if OutScope =='y':
                    FileMod.GenArchivo(DemodName, self.DemodKwargs)
            else:
                FileMod.GenArchivo(DemodName, self.DemodKwargs)
            
if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
              
        
        
    