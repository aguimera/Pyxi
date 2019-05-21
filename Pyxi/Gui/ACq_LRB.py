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
        
        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParameters)
        
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
                    if data == True:
                        self.GenPlotter()
                    if data == False:
                        self.DestroyPlotter()  
                if childName == 'PSD Options.PSDEnable' or childName == 'Demod PSD Options.PSDEnable':
                    if data == True:
                        self.GenPsdPlotter()
                    if data == False:
                        self.DestroyPsdPlotter()      

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

if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
              
        
        
        
        
        