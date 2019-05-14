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
import Pyxi.DemodModule as DemMod

class MainWindow(Qt.QWidget):
    debbug = True
    ''' Main Window '''
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setFocusPolicy(Qt.Qt.WheelFocus)
        
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
        self.DemodParams = DemMod.DemodParameters(name = 'Demod Options')
        self.DemConfig = self.DemodParams.param('DemodConfig')
        self.Parameters.addChild(self.DemodParams)
        
        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParameters)
        
        self.PSDParams = PltMod.PSDParameters(name='PSD Options')
        self.PSDParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
        self.PSDParams.param('Fmin').setValue(50)
        self.PSDParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.PSDParams)
        
        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.NiScopeParams.GetChannels())
        self.PlotParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())

        self.Parameters.addChild(self.PlotParams)
        
        self.DemodPSD = PltMod.PSDParameters(name='Demod PSD Options')
        self.DemodPSD.param('Fs').setValue((self.DemConfig.param('FsDemod').value())/(self.DemConfig.param('DSFact').value()))
        self.DemodPSD.param('Fmin').setValue(50)
        self.DemodPSD.param('nAvg').setValue(50)
        self.Parameters.addChild(self.DemodPSD)
        
        self.DemodPlotPars = PltMod.PlotterParameters(name='Demod Plot options')
        self.DemodPlotPars.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                    self.NifGenParams.GetCarriers())
                                      )
        self.DemodPlotPars.param('Fs').setValue((self.DemConfig.param('FsDemod').value())/(self.DemConfig.param('DSFact').value()))

        self.Parameters.addChild(self.DemodPlotPars)
        
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
        self.threadDemod = None
        self.threadDemodSave = None
        self.threadDemodPlotter = None
        self.threadDemodPSDPlotter = None

    def on_pars_changed(self, param, changes):
        if self.debbug:
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
               
#        if childName == 'NifGenerator.SamplingConfig.FsGen':
#            k =round(data/self.NiScopeParams.FsScope.value())
#            self.NiScopeParams.FsScope.setValue(data/k)
         
        if childName == 'NifGenerator.CarriersConfig':
            self.DemodPlotPars.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                        self.NifGenParams.GetCarriers())
                                          )
            
        if childName == 'Scope.FetchConfig.FsScope':
            n =round(self.NifGenParams.FsGen.value()/data)
            self.NiScopeParams.FsScope.setValue(self.NifGenParams.FsGen.value()/n)
            self.PlotParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
            self.PSDParams.param('Fs').setValue(self.NiScopeParams.FsScope.value())
            self.DemConfig.param('FsDemod').setValue(self.NiScopeParams.FsScope.value())
            
        if childName == 'Scope.FetchConfig.NRow':
            self.PlotParams.SetChannels(self.NiScopeParams.GetChannels())
            self.DemodPlotPars.SetChannels(self.DemodParams.GetChannels(self.NiScopeParams.Rows, 
                                                                        self.NifGenParams.GetCarriers())
                                          )
        if childName == 'Demod Options.DemodConfig.DSFs':
            self.DemodPSD.param('Fs').setValue(data)
            self.DemodPlotPars.param('Fs').setValue(data)
            if data >= np.min(self.NifGenParams.Freqs):
                print('WARNING: FsDemod is higher than FsMin')
            
        if childName == 'Plot options.RefreshTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetRefreshTime(data)    

        if childName == 'Plot options.ViewTime':
            if self.threadPlotter is not None:
                self.threadPlotter.SetViewTime(data)  
                
        if childName == 'Demod Plot options.RefreshTime':
            if self.threadDemodPlotter is not None:
                self.threadDemodPlotter.SetRefreshTime(data)    

        if childName == 'Demod Plot options.ViewTime':
            if self.threadDemodPlotter is not None:
                self.threadDemodPlotter.SetViewTime(data) 
                
        if childName == 'Plot options.PlotEnable':
            if self.threadAqc is not None:
                if data == True:
                    self.GenPlotter()
                if data == False:
                    self.DestroyPlotter()  
                
        if childName == 'PSD Options.PSDEnable':
            if self.threadAqc is not None:
                if data == True:
                    self.GenPSD()
                if data == False:
                    self.DestroyPSD()     
                    
        if childName == 'Demod Plot options.PlotEnable':
            if self.threadAqc is not None:
                if data == True:
                    self.GenPlotter()
                if data == False:
                    self.DestroyPlotter()  
                
        if childName == 'Demod PSD Options.PSDEnable':
            if self.threadAqc is not None:
                if data == True:
                    self.GenPSD()
                if data == False:
                    self.DestroyPSD()  
                
    def on_btnGen(self):
        print('h')
        if self.threadAqc is None:
            self.treepar.setParameters(self.Parameters, showTop=False)
            self.GenKwargs = self.NifGenParams.GetParams()
            self.ScopeKwargs = self.NiScopeParams.GetParams()
            self.DemKwargs = self.DemodParams.GetParams()
            
            self.threadAqc = FMacq.DataAcquisitionThread(**self.GenKwargs, **self.ScopeKwargs)
            self.threadAqc.NewData.connect(self.on_NewSample)
                       
            self.GenPSD()
            self.GenPlotter()
            self.SaveFiles()     
            
            if self.DemConfig.param('DemEnable').value() == True:
                self.threadDemod = DemMod.DemodThread(Fcs=self.NifGenParams.GetCarriers(), 
                                                      RowList=self.threadAqc.RowsList,
                                                      Fsize = self.threadAqc.BS, 
                                                      **self.DemKwargs)
                self.threadDemod.NewData.connect(self.on_NewDemodSample)
                self.threadDemod.start()
            
            
            self.threadAqc.start()
            self.btnGen.setText("Stop Gen")
            self.OldTime = time.time()
        else:
            self.threadAqc.NewData.disconnect()
            self.threadAqc.stopSessions()
            self.threadAqc.terminate()
            self.threadAqc = None
            
            if self.threadSave is not None:
                self.threadSave.stop()
                self.threadSave = None
                
            if self.threadDemod is not None:
                self.threadDemod.stop()
                self.threadDemod = None
            
            if self.threadPlotter is not None:
                self.threadPlotter.stop()
                self.threadPlotter = None
                
            if self.threadPSDPlotter is not None:
                self.threadPSDPlotter.stop()
                self.threadPSDPlotter = None
                
            if self.threadDemodSave is not None:
                self.threadDemodSave.stop()
                self.threadDemodSave = None
                
            if self.threadDemodPlotter is not None:
                self.threadDemodPlotter.stop()
                self.threadDemodPlotter = None
            
            if self.threadDemodPSDPlotter is not None:
                self.threadDemodPSDPlotter.stop()
                self.threadDemodPSDPlotter = None
                
            self.btnGen.setText("Start Gen")
            
    def GenPlotter(self):
        if self.threadPlotter is None:
            if self.PlotParams.param('PlotEnable').value() == True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
                self.threadPlotter.start()
                
        if self.threadDemodPlotter is None:
            if self.DemodPlotPars.param('PlotEnable').value() == True:
                PlotterKwargs = self.DemodPlotPars.GetParams()
                self.threadDemodPlotter = PltMod.Plotter(**PlotterKwargs)
                self.threadDemodPlotter.start()
        
    def GenPSD(self):
        if self.threadPSDPlotter is None:
            if self.PSDParams.param('PSDEnable').value() == True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                          nChannels=self.ScopeKwargs['NRow'],
                                                          **self.PSDParams.GetParams())
                self.threadPSDPlotter.start() 
                
        if self.threadDemodPSDPlotter is None:
            if self.DemodPSD.param('PSDEnable').value() == True:
                PlotterKwargs = self.DemodPlotPars.GetParams()
                self.threadDemodPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                               nChannels=self.ScopeKwargs['NRow']*len(self.NifGenParams.Freqs),
                                                               **self.DemodPSD.GetParams())
                self.threadDemodPSDPlotter.start() 
        

    def DestroyPlotter(self):
        if self.threadPlotter is not None:   
            if self.PlotParams.param('PlotEnable').value() == False:
                self.threadPlotter.stop()
                self.threadPlotter = None
        
        if self.threadDemodPlotter is not None:   
            if self.DemodPlotPars.param('PlotEnable').value() == False:
                self.threadDemodPlotter.stop()
                self.threadDemodPlotter = None
            
    def DestroyPSD(self):
        if self.threadPSDPlotter is not None: 
            if self.PSDParams.param('PSDEnable').value() == False:
                self.threadPSDPlotter.stop()
                self.threadPSDPlotter = None 
                
        if self.threadDemodPSDPlotter is not None: 
            if self.DemodPSD.param('PSDEnable').value() == False:
                self.threadDemodPSDPlotter.stop()
                self.threadDemodPSDPlotter = None       
                
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
       
        if self.DemConfig.param('DemEnable').value() == True:
            if self.threadDemod is not None:
#                self.tdemi = time.time()
                self.threadDemod.AddData(self.threadAqc.OutData)
                
        print('Sample time', Ts)

    def on_NewDemodSample(self):
#        Tdemod = time.time()-self.tdemi
#        print('DemodTime',Tdemod)
        if self.DemConfig.param('OutType').value() == 'Abs':
            OutDemData = np.abs(self.threadDemod.OutDemData)
        elif self.DemConfig.param('OutType').value() == 'Real':
            OutDemData = np.real(self.threadDemod.OutDemData)
        elif self.DemConfig.param('OutType').value() == 'Imag':
            OutDemData = np.imag(self.threadDemod.OutDemData)
        elif self.DemConfig.param('OutType').value() == 'Angle':
            OutDemData = np.angle(self.threadDemod.OutDemData, deg=True)   
         
        if self.threadDemodSave is not None:
            self.threadDemodSave.AddData(OutDemData)
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.AddData(OutDemData)
            
        if self.threadDemodPSDPlotter is not None:  
            self.threadDemodPSDPlotter.AddData(OutDemData)

    def SaveFiles(self):
        FileName = self.FileParameters.param('File Path').value()
        if FileName ==  '':
            print('No file')
        else:
            if os.path.isfile(FileName):
                print('Remove File')
                os.remove(FileName)  
            MaxSize = self.FileParameters.param('MaxSize').value()
            if self.DemConfig.param('DemEnable').value() == False:
                self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=self.ScopeKwargs['NRow'],
                                                           MaxSize=MaxSize)
                self.threadSave.start()
            
            if self.DemConfig.param('DemEnable').value() == True:
                self.threadDemodSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=self.ScopeKwargs['NRow']*len(self.NifGenParams.Freqs),
                                                           MaxSize=MaxSize,
                                                           dtype='float')
                
                self.threadDemodSave.start()

            GenName = FileName+'_GenConfig.dat'
            ScopeName = FileName+'_ScopeConfig.dat'
            DemName = FileName+'_DemodConfig.dat'
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
            if os.path.isfile(ScopeName):
                print('Overwriting  file')
                OutScope = input('y/n + press(Enter)')
                if OutScope =='y':
                    self.GenArchivo(DemName, self.DemKwargs)
            else:
                self.GenArchivo(DemName, self.DemKwargs)
                
    def GenArchivo(self, name, dic2Save):
        with open(name, "wb") as f:
            pickle.dump(dic2Save, f)
            
if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
        