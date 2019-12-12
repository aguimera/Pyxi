# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 11:27:12 2019

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
import Pyxi.DataAcquisition as DataAcq
import Pyxi.GenAqcCondigModule as NiConfig
import Pyxi.DemodModule as DemMod
import Pyxi.StabDetector as StbDet
import Pyxi.SaveSweepModule as SaveSw


class MainWindow(Qt.QWidget):
    ''' Main Window '''
    def __init__(self):      
        super(MainWindow, self).__init__()
        
        self.setFocusPolicy(Qt.Qt.WheelFocus)       
        layout = Qt.QVBoxLayout(self) 
        
        self.btnStart = Qt.QPushButton("Start Gen and Adq!")
        layout.addWidget(self.btnStart)
 ##############################Save############################## 
        self.SaveStateParams = FileMod.SaveSateParameters(QTparent=self,
                                                          name='State')        
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.SaveStateParams,))
 ##############################File##############################         
        self.FileParams = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParams)
        
        self.SaveSwParams = SaveSw.SaveSweepParameters(QTparent=self,
                                                         name='Sweeps File')
        self.Parameters.addChild(self.SaveSwParams)
 ##############################Configuration##############################   
        self.GenAcqParams = NiConfig.GenAcqConfig(name='NI DAQ Configuration')
        self.Parameters.addChild(self.GenAcqParams)
      
 ##############################NormalPlots##############################         
        self.PsdPlotParams = PltMod.PSDParameters(name='PSD Plot Options')
        self.PsdPlotParams.param('Fs').setValue(self.GenAcqParams.Fs.value())
        self.PsdPlotParams.param('Fmin').setValue(50)
        self.PsdPlotParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.PsdPlotParams)
        
        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.GenAcqParams.GetRows())
        self.PlotParams.param('Fs').setValue(self.GenAcqParams.Fs.value())

        self.Parameters.addChild(self.PlotParams)
 ##############################Demodulation##############################         
        self.DemodParams = DemMod.DemodParameters(name='Demod Options')     
        self.Parameters.addChild(self.DemodParams)
        self.DemodConfig = self.DemodParams.param('DemodConfig')
 ##############################Demodulation Plots##############################         
        self.DemodPsdPlotParams = PltMod.PSDParameters(name='Demod PSD Options')
        self.DemodPsdPlotParams.param('Fs').setValue(
                                                    (self.DemodConfig.param('FsDemod').value())
                                                    /(self.DemodConfig.param('DSFact').value())
                                                    )
        self.DemodPsdPlotParams.param('Fmin').setValue(50)
        self.DemodPsdPlotParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.DemodPsdPlotParams)
        
        self.DemodPlotParams = PltMod.PlotterParameters(name='Demod Plot options')
        self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.GenAcqParams.Rows, 
                                                                      self.GenAcqParams.GetCarriers())
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
#        
        self.threadAqc = None
        self.threadSave = None
        self.threadPlotter = None
        self.threadPsdPlotter = None
        self.threadDemodAqc = None
        self.threadDemodSave = None
        self.threadDemodPlotter = None
        self.threadDemodPsdPlotter = None
        self.threadStbDet = None
        
 ##############################Changes Control##############################         
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
  
        if childName == 'NI DAQ Configuration.CarriersConfig':
            self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.GenAcqParams.Rows, 
                                                                          self.GenAcqParams.GetCarriers())
                                                                          )

        if childName == 'NI DAQ Configuration.AcqConfig.Fs':
            self.PlotParams.param('Fs').setValue(self.GenAcqParams.Fs.value())
            self.PsdPlotParams.param('Fs').setValue(self.GenAcqParams.Fs.value())
            self.DemodConfig.param('FsDemod').setValue(self.GenAcqParams.Fs.value())
            
        if childName == 'NI DAQ Configuration.AcqConfig.NRow':
            self.PlotParams.SetChannels(self.GenAcqParams.GetRows())
            self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(self.GenAcqParams.Rows, 
                                                                          self.GenAcqParams.GetCarriers())
                                             )
        
        if childName == 'Demod Options.DemodConfig.DSFact':
            self.DemodParams.ReCalc_DSFact(self.GenAcqParams.BufferSize.value())
#                    
        if childName == 'Demod Options.DemodConfig.DSFs':
            self.DemodPsdPlotParams.param('Fs').setValue(data)
            self.DemodPlotParams.param('Fs').setValue(data)
            if data >= np.min(self.GenAcqParams.Freqs):
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
            if childName == 'PSD Plot Options.PSDEnable' or childName == 'Demod PSD Options.PSDEnable':
                self.Gen_Destroy_PsdPlotter() 
        
 ##############################START##############################          
    def on_btnStart(self):       
        if self.threadAqc is None:
            print('started')
            self.VdInd = 0
            self.VgInd = 0
            
            self.treepar.setParameters(self.Parameters, showTop=False)
            self.GenKwargs = self.GenAcqParams.GetGenParams()
            self.ScopeKwargs = self.GenAcqParams.GetRowParams()
            self.ScopeChns = self.GenAcqParams.GetRowsNames()
            self.DemodKwargs = self.DemodParams.GetParams()
            self.VdSweepVals = self.GenAcqParams.VdSweepVals
            self.VgSweepVals = self.GenAcqParams.VgSweepVals
            
            self.threadAqc = DataAcq.DataAcquisitionThread(GenConfig=self.GenKwargs,
                                                           Channels=self.ScopeChns, 
                                                           ScopeConfig=self.ScopeKwargs,
                                                           Vd=self.VdSweepVals[0]) #empieza por el primer valor del sweep Vd
            self.threadAqc.NewMuxData.connect(self.on_NewSample)
            
            self.Gen_Destroy_PsdPlotter()
            self.Gen_Destroy_Plotters()
            self.SaveFiles()     
            
            if self.DemodConfig.param('DemEnable').value() == True:
                self.threadDemodAqc = DemMod.DemodThread(Fcs=self.GenAcqParams.GetCarriers(), 
                                                         RowList=self.ScopeChns,
                                                         FetchSize=self.GenAcqParams.BufferSize.value(), 
                                                         Signal=self.threadAqc.Signal,
                                                         **self.DemodKwargs)
                self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
                
                self.threadStbDet = StbDet.StbDetThread(MaxSlope=self.DemodConfig.param('MaxSlope').value(),
                                                        TimeOut=self.DemodConfig.param('TimeOut').value(),
                                                        ChnName= self.DemodParams.GetChannels(self.GenAcqParams.Rows, 
                                                                      self.GenAcqParams.GetCarriers())
                                                        PlotterDemodKwargs=self.DemodPlotParams.GetParams(),
                                                        VdVals=self.VdSweepVals,
                                                        VgVals=self.VgSweepVals)
                
                self.threadDemodAqc.start()
                self.threadStbDet.NextVg.connect(self.on_NextVg)
                self.threadStbDet.initTimer() #TimerPara el primer Sweep
                self.threadStbDet.start()
                 
            self.threadAqc.DaqInterface.SetSignal(self.threadAqc.DaqInterface.Signal)
            self.threadAqc.start()
            self.btnStart.setText("Stop Gen")
            self.OldTime = time.time()
        else:
            print('stopped')
            self.threadAqc.NewMuxData.disconnect()
            self.threadStbDet.NextVg.disconnect()
            self.threadAqc.DaqInterface.Stop()
            self.threadAqc.terminate()
            self.threadAqc = None
            
            self.StopThreads()
            
            self.btnStart.setText("Start Gen and Adq!")         

 ##############################New Sample Obtained##############################      
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        if self.threadSave is not None:
#            No usar Int hasta que se haya arreglado problema
#            Problema: Range scope no es exacto con lo cual hay valores que no deberian saturar y saturan
#            self.threadSave.AddData(self.threadAqc.IntData)
            self.threadSave.AddData(self.threadAqc.OutData)
        
        if self.threadPlotter is not None:
            self.threadPlotter.AddData(self.threadAqc.OutData)
            
        if self.threadPsdPlotter is not None:  
            self.threadPsdPlotter.AddData(self.threadAqc.OutData)
       
        if self.DemodConfig.param('DemEnable').value() == True:
            if self.threadDemodAqc is not None:
                self.threadDemodAqc.AddData(self.threadAqc.OutData)
                
        print('Sample time', Ts)

 ##############################New Sample To Demodulate##############################          
    def on_NewDemodSample(self):
        if self.DemodConfig.param('OutType').value() == 'Abs':
            OutDemodData = np.abs(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Real':
            OutDemodData = np.real(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Imag':
            OutDemodData = np.imag(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Angle':
            OutDemodData = np.angle(self.threadDemodAqc.OutDemodData, deg=True)   
        
        if self.threadStbDet is not None:
            self.threadStbDet.AddData(OutDemodData)
            
        if self.threadDemodSave is not None:
            #Yo iria haciendo aqui appends, hasta que acabase el sweep de Vgs
            #una vez acaba el sweep, guardo los valores de IDS en el diccionario
            #DC, y calculo los PSD para guardar en el diccionario AC
            self.threadDemodSave.AddData(OutDemodData)
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.AddData(OutDemodData)
            
        if self.threadDemodPsdPlotter is not None:  
            self.threadDemodPsdPlotter.AddData(OutDemodData)

        if self.threadDemodPsdPlotter is not None:  
            self.threadDemodPsdPlotter.AddData(OutDemodData)
##############################Restart Timer Stabilization##############################  
    def on_NextVg(self):
        self.threadStbDet.Timer.stop()
        self.threadStbDet.Timer.killTimer(self.Id)
        
        if self.VgInd < len(self.VgSweepVals):
            self.VgInd += 1
            self.threadAqc.DaqInterface.VcmOut.ClearTask()
            self.threadAqc.Vcm = self.VgSweepVals[self.VgInd]
        
            self.threadStbDet.initTimer()
        
        else:
            self.VgInd = 0
            self.on_NextVd()
        
##############################Nex Vd Value##############################     
    def on_NextVd(self):
        self.threadAqc.NewMuxData.disconnect()
        self.threadAqc.DaqInterface.Stop()
        self.threadAqc.terminate()
        self.threadAqc = None

        if self.VdInd < len(self.VdSweepVals):
            self.VdInd += 1
            self.VdValue = self.VdSweepVals[self.VdInd]
            self.threadAqc = DataAcq.DataAcquisitionThread(GenConfig=self.GenKwargs,
                                                           Channels=self.ScopeChns, 
                                                           ScopeConfig=self.ScopeKwargs,
                                                           VcmVals=self.VgSweepVals,
                                                           Vd=self.VdValue) 
            self.threadAqc.NewMuxData.connect(self.on_NewSample)
            self.threadAqc.DaqInterface.SetSignal(self.threadAqc.DaqInterface.Signal)
            self.threadAqc.start()
            self.threadStbDet.initTimer()
        else:
            print('SweepEnded')
            self.StopThreads()
            self.btnStart.setText("Start Gen and Adq!") 
            #guardar el archivo ACDC en el formato correcto
            DCDict = self.threadStbDet.SaveDCAC.DevDCVals
            ACDict = self.threadStbDet.SaveDCAC.DevACVals
            self.SaveSwParams.SaveDicts(DCDict, ACDict)
            #Parar thread de estabilización
            self.threadStbDet.NextVg.disconnect()
            self.threadStbDet.stop()
##############################Savind Files##############################  
    def SaveFiles(self):
        FileName = self.FileParams.param('File Path').value()
        if FileName ==  '':
            print('No file')
        else:
            if os.path.isfile(FileName):
                print('Remove File')
                os.remove(FileName)  
            MaxSize = self.FileParams.param('MaxSize').value()
            if self.DemodConfig.param('DemEnable').value() == False:
                self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=self.ScopeKwargs['NRow'],
                                                           MaxSize=MaxSize,
                                                           dtype='float' #comment when int save problem solved
                                                           )
                self.threadSave.start()
            
            if self.DemodConfig.param('DemEnable').value() == True:
                self.threadDemodSave = FileMod.DataSavingThread(FileName=FileName,
                                                                nChannels=self.ScopeKwargs['NRow']*len(self.GenAcqParams.Freqs),
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
                
 ##############################Generate and Destroy Plots##############################      
    def Gen_Destroy_Plotters(self):
        if self.threadPlotter is None:
            if self.PlotParams.param('PlotEnable').value() == True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
                self.threadPlotter.start()
        if self.threadPlotter is not None:
            if self.PlotParams.param('PlotEnable').value() == False:
                self.threadPlotter.stop()
                self.threadPlotter = None
                
        if self.threadDemodPlotter is None:
            if self.DemodPlotParams.param('PlotEnable').value() == True:
                PlotterDemodKwargs = self.DemodPlotParams.GetParams()
                self.threadDemodPlotter = PltMod.Plotter(**PlotterDemodKwargs)
                self.threadDemodPlotter.start()
        if self.threadDemodPlotter is not None:
            if self.DemodPlotParams.param('PlotEnable').value() == False:
                self.threadDemodPlotter.stop()
                self.threadDemodPlotter = None

    def Gen_Destroy_PsdPlotter(self):
        if self.threadPsdPlotter is None:
            if self.PsdPlotParams.param('PSDEnable').value() == True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPsdPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                          nChannels=self.ScopeKwargs['NRow'],
                                                          **self.PsdPlotParams.GetParams())
                self.threadPsdPlotter.start() 
        if self.threadPsdPlotter is not None:
            if self.PsdPlotParams.param('PSDEnable').value() == False:
                self.threadPsdPlotter.stop()
                self.threadPsdPlotter = None 
                
        if self.threadDemodPsdPlotter is None:
            if self.DemodPsdPlotParams.param('PSDEnable').value() == True:
                PlotterDemodKwargs = self.DemodPlotParams.GetParams()
                self.threadDemodPsdPlotter = PltMod.PSDPlotter(ChannelConf=PlotterDemodKwargs['ChannelConf'],
                                                               nChannels=self.ScopeKwargs['NRow']*len(self.GenAcqParams.Freqs),
                                                               **self.DemodPsdPlotParams.GetParams())
                self.threadDemodPsdPlotter.start() 
        if self.threadDemodPsdPlotter is not None:
            if self.DemodPsdPlotParams.param('PSDEnable').value() == False:
                self.threadDemodPsdPlotter.stop()
                self.threadDemodPsdPlotter = None   
        
 ##############################STOP##############################          
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
        
 ##############################MAIN##############################  
if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
                     