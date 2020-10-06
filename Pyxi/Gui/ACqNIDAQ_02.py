# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 15:55:21 2020

@author: lucia
"""

from __future__ import print_function
import os

import numpy as np
import time

from PyQt5 import Qt

from pyqtgraph.parametertree import Parameter, ParameterTree

import Pyxi.DataAcquisition_02 as DataAcq
import Pyxi.GenAqcModule as NiConfig

import PyqtTools.FileModule as FileMod
import PyqtTools.DemodModule as DemMod
import PyqtTools.CharacterizationModule as Charact
from PyqtTools.PlotModule import Plotter as TimePlt
from PyqtTools.PlotModule import PlotterParameters as TimePltPars
from PyqtTools.PlotModule import PSDPlotter as PSDPlt
from PyqtTools.PlotModule import PSDParameters as PSDPltPars

class MainWindow(Qt.QWidget):
    ''' Main Window '''
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setFocusPolicy(Qt.Qt.WheelFocus)
        layout = Qt.QVBoxLayout(self)

        self.btnStart = Qt.QPushButton("Start Gen and Adq!")
        layout.addWidget(self.btnStart)
        
        self.ResetGraph = Qt.QPushButton("Reset Graphics")
        layout.addWidget(self.ResetGraph)
        
        self.threadAqc = None
        self.threadSave = None
        self.threadPlotter = None
        self.threadPsdPlotter = None
        self.threadDemodAqc = None
        self.threadDemodSave = None
        self.threadDemodPlotter = None
        self.threadDemodPsdPlotter = None
        self.threadCharact = None

# #############################Save##############################
        self.SaveStateParams = FileMod.SaveSateParameters(QTparent=self,
                                                          name='FileState',
                                                          title='Save/load config')
        # self.Parameters = Parameter.create(name='params',
        #                                    type='group',
        #                                    children=(self.SaveStateParams,))

# #############################File##############################
        self.FileParams = FileMod.SaveFileParameters(QTparent=self,
                                                     name='FileDat',
                                                     title='Save data')
        # self.Parameters.addChild(self.FileParams)

# #############################Sweep Config##############################
        self.SwParams = Charact.SweepsConfig(QTparent=self,
                                             name='Sweeps Configuration')
        
# #############################Configuration##############################
        self.GenAcqParams = NiConfig.GenAcqConfig(name='NI DAQ Configuration')
        self.DemodConfig = self.GenAcqParams.param('DemodConfig')
        # self.DemodConfig = DemMod.DemodParameters(name='DemodConfig')

# #############################NormalPlots##############################
        self.PlotParams = TimePltPars(name='TimePlt',
                                      title='Time Plot Options')

        self.PsdPlotParams = PSDPltPars(name='PSDPlt',
                                        title='PSD Plot Options')
        
        self.DemodPlotParams = TimePltPars(name='DemodTimePlt',
                                      title='Demod Time Plot Options')

        self.DemodPsdPlotParams = PSDPltPars(name='DemodPSDPlt',
                                        title='Demod PSD Plot Options')


        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.SaveStateParams,
                                                     self.SwParams,
                                                     self.FileParams,
                                                     self.GenAcqParams,
                                                     self.PlotParams,
                                                     self.PsdPlotParams,
                                                     self.DemodPlotParams,
                                                     self.DemodPsdPlotParams,
                                                     ))
        # ############Instancias para cambios#################################
        self.GenAcqParams.param('CarriersConfig').sigTreeStateChanged.connect(self.on_CarriersConfig_changed)
        self.GenAcqParams.param('AcqConfig').param('FsGen').sigValueChanged.connect(self.on_FsScope_changed)
        self.GenAcqParams.param('AcqConfig').param('FsScope').sigValueChanged.connect(self.on_FsScope_changed)
        self.GenAcqParams.param('AcqConfig').param('NRow').sigValueChanged.connect(self.on_NRow_changed)
        self.DemodConfig.param('DSFact').sigValueChanged.connect(self.on_DSFact_changed)
 
        self.PsdPlotParams.NewConf.connect(self.on_NewPSDConf)
        self.PlotParams.NewConf.connect(self.on_NewPlotConf)
        self.DemodPsdPlotParams.NewConf.connect(self.on_NewDemodPSDConf)
        self.DemodPlotParams.NewConf.connect(self.on_NewDemodPlotConf)
        
        self.SwParams.param('SweepsConfig').param('Start/Stop Sweep').sigActivated.connect(self.on_Sweep_start)
        self.SwParams.param('SweepsConfig').param('Pause/ReStart Sweep').sigActivated.connect(self.on_Sweep_paused)
        
        self.on_NRow_changed()
        self.on_FsScope_changed()
        
        self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(550, 10, 400, 700)
        self.setWindowTitle('MainWindow')
        self.btnStart.clicked.connect(self.on_btnStart)
        self.ResetGraph.clicked.connect(self.on_ResetGraph)

# #############################Changes Control##############################
    def on_Params_changed(self, param, changes):
        print("tree changes:")
        for param, change, data in changes:
            path = self.Parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        print('  parameter: %s' % childName)
        print('  change:    %s' % change)
        print('  data:      %s' % str(data))
        print('  ----------')

# #############################Changes Emits##############################
    def on_CarriersConfig_changed(self):
        self.DemodPlotParams.SetChannels(self.GenAcqParams.GetChannels(
                                              self.GenAcqParams.Rows,
                                              self.GenAcqParams.GetCarriers())
                                         )

    def on_FsScope_changed(self):
        n = round(self.GenAcqParams.FsGen.value() /
                  self.GenAcqParams.FsScope.value()
                  )

        self.GenAcqParams.param('AcqConfig').param('FsScope').setValue(
                                            self.GenAcqParams.FsGen.value() / n
                                            )
        self.PlotParams.param('Fs').setValue(self.GenAcqParams.FsScope.value())
        self.PsdPlotParams.param('Fs').setValue(self.GenAcqParams.FsScope.value())

        self.DemodConfig.param('FsDemod').setValue(self.GenAcqParams.FsScope.value()

                                                   )
        self.DemodPsdPlotParams.param('Fs').setValue(
                                                    (self.DemodConfig.param('FsDemod').value())
                                                    /(self.DemodConfig.param('DSFact').value())
                                                    )
        self.DemodPlotParams.param('Fs').setValue(
                                                (self.DemodConfig.param('FsDemod').value())
                                                /(self.DemodConfig.param('DSFact').value())
                                                )

    def on_DSFact_changed(self):
        self.GenAcqParams.ReCalc_DSFact(self.GenAcqParams.BufferSize.value())
        self.DemodPsdPlotParams.param('Fs').setValue(self.GenAcqParams.DSFs.value())
        self.DemodPlotParams.param('Fs').setValue(self.GenAcqParams.DSFs.value())
        if self.GenAcqParams.DSFs.value() >= np.min(self.GenAcqParams.Freqs):
            print('WARNING: FsDemod is higher than FsMin')

    def on_NRow_changed(self):
        self.PlotParams.SetChannels(self.GenAcqParams.GetRows())
        self.PsdPlotParams.ChannelConf = self.PlotParams.ChannelConf
        nChannels = self.PlotParams.param('nChannels').value()
        self.PsdPlotParams.param('nChannels').setValue(nChannels)
        
        self.DemodPlotParams.SetChannels(self.GenAcqParams.GetChannels(
                                              self.GenAcqParams.Rows,
                                              self.GenAcqParams.GetCarriers())
                                         )
        self.DemodPsdPlotParams.ChannelConf = self.DemodPlotParams.ChannelConf
        nChannels = self.DemodPlotParams.param('nChannels').value()
        self.DemodPsdPlotParams.param('nChannels').setValue(nChannels)
        
    def on_NewPSDConf(self):
        if self.threadPsdPlotter is not None:
            nFFT = self.PsdPlotParams.param('nFFT').value()
            nAvg = self.PsdPlotParams.param('nAvg').value()
            self.threadPsdPlotter.InitBuffer(nFFT=nFFT, nAvg=nAvg)

    def on_NewPlotConf(self):
        if self.threadPlotter is not None:
            ViewTime = self.PlotParams.param('ViewTime').value()
            self.threadPlotter.SetViewTime(ViewTime)        
            RefreshTime = self.PlotParams.param('RefreshTime').value()
            self.threadPlotter.SetRefreshTime(RefreshTime)  
            
    def on_NewDemodPSDConf(self):
        if self.threadDemodPsdPlotter is not None:
            nFFT = self.DemodPsdPlotParams.param('nFFT').value()
            nAvg = self.DemodPsdPlotParams.param('nAvg').value()
            self.threadDemodPsdPlotter.InitBuffer(nFFT=nFFT, nAvg=nAvg)

    def on_NewDemodPlotConf(self):
        if self.threadDemodPlotter is not None:
            ViewTime = self.DemodPlotParams.param('ViewTime').value()
            self.threadDemodPlotter.SetViewTime(ViewTime)        
            RefreshTime = self.DemodPlotParams.param('RefreshTime').value()
            self.threadDemodPlotter.SetRefreshTime(RefreshTime)

    def on_ResetGraph(self):
        if self.threadAqc is None:
            return

        # Plot and PSD threads are stopped
        if self.threadPlotter is not None:
            self.threadPlotter.stop()
            self.threadPlotter = None

        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.stop()
            self.threadPsdPlotter = None
            
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.stop()
            self.threadDemodPlotter = None

        if self.threadDemodPsdPlotter is not None:
            self.threadDemodPsdPlotter.stop()
            self.threadDemodPsdPlotter = None

        if self.PlotParams.param('PlotEnable').value():
            Pltkw = self.PlotParams.GetParams()
            self.threadPlotter = TimePlt(**Pltkw)
            self.threadPlotter.start()

        if self.PsdPlotParams.param('PlotEnable').value():
            PSDKwargs = self.PsdPlotParams.GetParams()
            self.threadPsdPlotter = PSDPlt(**PSDKwargs)
            self.threadPsdPlotter.start()
        
        if self.DemodPlotParams.param('PlotEnable').value():
            Pltkw = self.DemodPlotParams.GetParams()
            self.threadDemodPlotter = TimePlt(**Pltkw)
            self.threadDemodPlotter.start()

        if self.DemodPsdPlotParams.param('PlotEnable').value():            
            PSDKwargs = self.DemodPsdPlotParams.GetParams()
            print(PSDKwargs)
            self.threadDemodPsdPlotter = PSDPlt(**PSDKwargs)
            self.threadDemodPsdPlotter.start()

# #############################START Real Time Acquisition ####################
    def on_btnStart(self):
        if self.threadAqc is None:
            print('started')
            self.treepar.setParameters(self.Parameters, showTop=False)

            self.AcqKwargs = self.GenAcqParams.GetAcqParams()
            self.DemKwargs = self.GenAcqParams.GetDemThreadParams()
            # Cálculo de la tensión VdPico
            for key, val in self.AcqKwargs['CarrierConfig'].items():
                for k, v in val.items():
                    if k == 'Amplitude':
                        self.AcqKwargs['CarrierConfig'][key][k] = np.sqrt(2)*v
            
            # Cálculo de la tensión Vsg     
            self.AcqKwargs['CMVoltage'] = (-1)*self.AcqKwargs['CMVoltage']
            
            self.threadAqc = DataAcq.DataAcquisitionThread(**self.AcqKwargs) 
            self.threadAqc.NewMuxData.connect(self.on_NewSample)
            self.threadAqc.DaqInterface.SetSignal(Signal=self.threadAqc.Signal,
                                                  FsBase="",
                                                  FsGen=self.AcqKwargs['FsGen']
                                                  )

            self.on_ResetGraph()
            
            if self.DemodConfig.param('DemEnable').value() is True:
                self.threadDemodAqc = DemMod.DemodThread(Signal=self.threadAqc.Vcoi,
                                                         **self.DemKwargs,
                                                         )
                self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
                self.threadDemodAqc.start()
            
            if self.DemodConfig.param('Save Demod').value() is True:
                Fs = self.GenAcqParams.DSFs.value()
                ChnNames = self.GenAcqParams.GetChannels(self.GenAcqParams.Rows,
                                                         self.GenAcqParams.GetCarriers()).keys()
                ChnNames = np.array(list(ChnNames), dtype='S10')
                if self.FileParams.param('Enabled').value():
                    FilekwArgs = {'FileName': self.FileParams.FilePath().split(".")[0]+'_Demod.h5',
                                  'nChannels': self.GenAcqParams.NRows.value(),
                                  'Fs': Fs,
                                  'ChnNames': ChnNames,
                                  'MaxSize': self.FileParams.param('MaxSize').value(),
                                  'dtype': 'float',
                                  }

                    self.threadDemodSave = FileMod.DataSavingThread(**FilekwArgs)
                    self.threadDemodSave.start()
                    print('saveDemod')
                    print(FilekwArgs['FileName'])
                    
            else:
                Fs=self.GenAcqParams.FsScope.value(),
                ChnNames=list(self.GenAcqParams.GetChannels(self.GenAcqParams.Rows,
                                                        self.GenAcqParams.GetCarriers()).keys())
            
                ChnNames = np.array(list(ChnNames), dtype='S10')
                if self.FileParams.param('Enabled').value():
                    FilekwArgs = {'FileName': self.FileParams.FilePath(),
                                  'nChannels': self.GenAcqParams.NRows.value(),
                                  'Fs': Fs,
                                  'ChnNames': ChnNames,
                                  'MaxSize': self.FileParams.param('MaxSize').value(),
                                  'dtype': 'float',
                                  }
                    
                    self.threadSave = FileMod.DataSavingThread(**FilekwArgs)
                    self.threadSave.start()
        
            self.threadAqc.start()
            
            self.btnStart.setText("Stop Gen")
            self.OldTime = time.time()
        else:
            print('stopped')
            self.threadAqc.NewMuxData.disconnect()
            self.threadAqc.DaqInterface.Stop()
            self.threadAqc.terminate()
            self.threadAqc = None

            self.StopThreads()

            self.btnStart.setText("Start Gen and Adq!")
            
# #############################START Sweep Acquisition ####################
    def on_Sweep_start(self):
        if self.threadAqc is None:
            print('Sweep started')
            self.Paused = False
            
            self.treepar.setParameters(self.Parameters, showTop=False)

            self.AcqKwargs = self.GenAcqParams.GetAcqParams()
            self.DemKwargs = self.GenAcqParams.GetDemThreadParams()         
            self.SweepsKwargs = self.SwParams.GetConfigSweepsParams()
            self.DcSaveKwargs = self.SwParams.GetSaveSweepsParams()
          

            
            self.threadCharact = Charact.StbDetThread(nChannels=self.GenAcqParams.NRows.value()*len(self.GenAcqParams.Freqs),
                                                      ChnName=self.GenAcqParams.GetChannels(self.GenAcqParams.Rows,
                                                                                           self.GenAcqParams.GetCarriers()),
                                                      PlotterDemodKwargs=self.DemodPsdPlotParams.GetParams(),
                                                      **self.SweepsKwargs
                                                      )
            self.threadCharact.NextVg.connect(self.on_NextVg)
            self.threadCharact.NextVd.connect(self.on_NextVd)
            self.threadCharact.CharactEnd.connect(self.on_CharactEnd)

            print(self.AcqKwargs)
            self.threadAqc = DataAcq.DataAcquisitionThread(**self.AcqKwargs) 
            self.threadAqc.NewMuxData.connect(self.on_NewSample)
            self.threadAqc.OutSignal(Vds=np.sqrt(2)*self.threadCharact.NextVds)
            self.threadAqc.Vcm = (-1)*self.threadCharact.NextVgs
            self.threadAqc.DaqInterface.SetSignal(Signal=self.threadAqc.Signal,
                                                  FsBase="",
                                                  FsGen=self.AcqKwargs['FsGen']
                                                  )
            
            self.threadDemodAqc = DemMod.DemodThread(Signal=self.threadAqc.Vcoi,
                                                     **self.DemKwargs,
                                                     )
            self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
            
            self.on_ResetGraph()

            # self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)
            self.threadCharact.start()
            self.threadDemodAqc.start()
            self.threadAqc.start()
            
            self.OldTime = time.time()
            
        else:
            print('stopped')
            self.threadAqc.NewMuxData.disconnect()
            self.threadAqc.DaqInterface.Stop()
            self.threadAqc.terminate()
            self.threadAqc = None

            if self.threadCharact is not None:
                self.threadCharact.NextVg.disconnect()
                self.threadCharact.NextVd.disconnect()
                self.threadCharact.stop()
                self.threadCharact.CharactEnd.disconnect()
                self.threadCharact = None
            
            self.StopThreads()
# #############################Pause Sweep Acquisition ####################
    def on_Sweep_paused(self):
        if self.threadAqc is None:
            print('Sweep Restarted')
            
            self.treepar.setParameters(self.Parameters, showTop=False)

            self.AcqKwargs = self.GenAcqParams.GetAcqParams()
            self.DemKwargs = self.GenAcqParams.GetDemThreadParams()       
            self.SweepsKwargs = self.SwParams.GetConfigSweepsParams()
            self.DcSaveKwargs = self.SwParams.GetSaveSweepsParams()
          
            self.on_ResetGraph()
            
            self.threadCharact = Charact.StbDetThread(nChannels=self.GenAcqParams.NRows.value()*len(self.GenAcqParams.Freqs),
                                                      ChnName=self.GenAcqParams.GetChannels(self.GenAcqParams.Rows,
                                                                                           self.GenAcqParams.GetCarriers()),
                                                      PlotterDemodKwargs=self.DemodPsdPlotParams.GetParams(),
                                                      **self.SweepsKwargs
                                                      )     
            self.threadCharact.VgIndex = self.LastVgsInd
            self.threadCharact.VdIndex = self.LastVdsInd 
            self.threadCharact.NextVg.connect(self.on_NextVg)
            self.threadCharact.NextVd.connect(self.on_NextVd)
            self.threadCharact.CharactEnd.connect(self.on_CharactEnd)
            
            self.threadAqc = DataAcq.DataAcquisitionThread(**self.AcqKwargs) 
            self.threadAqc.NewMuxData.connect(self.on_NewSample)
            self.threadAqc.OutSignal(Vds=np.sqrt(2)*self.threadCharact.VdSweepVals[self.LastVdsInd])      
            self.threadAqc.Vcm = (-1)*self.threadCharact.VgSweepVals[self.LastVgsInd]
            self.threadAqc.DaqInterface.SetSignal(Signal=self.threadAqc.Signal,
                                                  FsBase="",
                                                  FsGen=self.AcqKwargs['FsGen']
                                                  )
            
            self.threadDemodAqc = DemMod.DemodThread(Signal=self.threadAqc.Vcoi,
                                                     **self.DemKwargs,
                                                     )
            self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)
            
            
            # self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)
            self.threadCharact.start()
            self.threadDemodAqc.start()
            self.threadAqc.start()
            
            self.OldTime = time.time()
            
        else:
            print('paused')
            self.Paused = True
            
            self.LastVgsInd = self.threadCharact.VgIndex
            self.LastVdsInd = self.threadCharact.VdIndex
            print(self.LastVgsInd, self.LastVdsInd)
            self.PauseDevDCDict = self.threadCharact.SaveDCAC.DevDCVals
            if self.threadCharact.ACenable:
                self.PauseDevACDict = self.threadCharact.SaveDCAC.DevACVals

            self.threadAqc.NewMuxData.disconnect()
            self.threadAqc.DaqInterface.Stop()
            self.threadAqc.terminate()
            self.threadAqc = None
            if self.threadCharact is not None:
                self.threadCharact.NextVg.disconnect()
                self.threadCharact.NextVd.disconnect()
                self.threadCharact.stop()
                self.threadCharact.CharactEnd.disconnect()
                self.threadCharact = None
            
            self.StopThreads()

# #############################New Sample Obtained############################
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        # print('NEWSAMPLE')
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        if self.threadSave is not None:
            print('saveRow')
            self.threadSave.AddData(self.threadAqc.OutData)

        if self.threadPlotter is not None:
            self.threadPlotter.AddData(self.threadAqc.OutData)

        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.AddData(self.threadAqc.OutData)

        if self.DemodConfig.param('DemEnable').value() is True:
            if self.threadDemodAqc is not None:
                self.threadDemodAqc.AddData(self.threadAqc.OutDataVolts)

        print('Sample time', Ts)

# #############################New Sample To Demodulate#######################
    def on_NewDemodSample(self):
        if self.DemodConfig.param('OutType').value() == 'Abs':
            OutDemodData = np.abs(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Real':
            OutDemodData = np.real(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Imag':
            OutDemodData = np.imag(self.threadDemodAqc.OutDemodData)
        elif self.DemodConfig.param('OutType').value() == 'Angle':
            OutDemodData = np.angle(self.threadDemodAqc.OutDemodData, deg=True)

        if self.AcqKwargs['AcqDiff'] is False:
            OutDemodData = 2*OutDemodData
            
        if self.threadCharact is not None:
            # print('Demod Done')
            self.threadCharact.AddData(OutDemodData/np.sqrt(2))  # (RMS)

        if self.threadDemodSave is not None:
            print('saveDemod')
            self.threadDemodSave.AddData(OutDemodData)
        if self.threadDemodPlotter is not None:
            # print('NewDEMODDATA')
            self.threadDemodPlotter.AddData(OutDemodData)

        if self.threadDemodPsdPlotter is not None:
            # print('NewDEMODPSDDATA')
            self.threadDemodPsdPlotter.AddData(OutDemodData)

        if self.threadDemodPsdPlotter is not None:
            self.threadDemodPsdPlotter.AddData(OutDemodData)

# #############################Restart Timer Stabilization####################
    def on_NextVg(self):
        self.threadAqc.DaqInterface.VcmOut.StopTask()
        self.threadAqc.DaqInterface.SetVcm(Vcm=(-1)*self.threadCharact.NextVgs)

        # self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)
        print('NEXT VGS SWEEP')

# #############################Nex Vd Value##############################
    def on_NextVd(self):
        self.threadAqc.NewMuxData.disconnect()
        self.threadAqc.DaqInterface.Stop()
        self.threadAqc.terminate()
        self.threadAqc = None
        
        self.threadAqc = DataAcq.DataAcquisitionThread(**self.AcqKwargs) 
        self.threadAqc.NewMuxData.connect(self.on_NewSample)
        self.threadAqc.OutSignal(Vds=np.sqrt(2)*self.threadCharact.NextVds)      
        self.threadAqc.Vcm = (-1)*self.threadCharact.NextVgs
             
        self.threadAqc.DaqInterface.SetSignal(Signal=self.threadAqc.Signal,
                                              FsBase="",
                                              FsGen=self.AcqKwargs['FsGen']
                                              )
        self.threadAqc.start()
        
        # self.threadCharact.Timer.timeout.connect(self.threadCharact.printTime)
        # self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)

    def on_CharactEnd(self):
        print('END Charact')
        self.threadCharact.NextVg.disconnect()
        self.threadCharact.NextVd.disconnect()
        self.threadCharact.CharactEnd.disconnect()
        CharactDCDict = self.threadCharact.DCDict
        CharactACDict = self.threadCharact.ACDict
        if self.Paused:
            for k, v in self.PauseDevDCDict.items():
                for indexR, dato in enumerate(v['Ids']):
                    for indexC, d in enumerate(dato):
                        if np.isnan(d):
                            continue
                        else:
                            CharactDCDict[k]['Ids'][indexR, indexC] = d
                             
            
            if CharactACDict is not None:
                self.PauseDevACDict.update(CharactACDict)
                CharactACDict = self.PauseDevACDict
                for k, v in self.PauseDevACDict.items():
                    for key, val in v['PSD'].items():
                        for indexR, dato in enumerate(val):
                            for indexC, d in enumerate(dato):
                                if np.isnan(d):
                                    continue
                                else:
                                    CharactACDict[k]['PSD'][key][indexR, indexC] = d

        self.threadCharact.SaveDCAC.SaveDicts(Dcdict=CharactDCDict,
                                              Acdict=CharactACDict,
                                              **self.DcSaveKwargs)
        self.threadAqc.NewMuxData.disconnect()
        self.threadAqc.DaqInterface.Stop()
        self.threadAqc.terminate()
        self.threadAqc = None
        self.StopThreads()
        
        # dictNew.update(DictOld) 
        # se modifica el diccionario dictNew con los pares key/value de DictOld y se sobreescriben las key coincidentes

# #############################STOP##############################
    def StopThreads(self):
        if self.threadSave is not None:
            self.threadSave.stop()
            self.threadSave = None

        if self.threadDemodAqc is not None:
            self.threadDemodAqc.stop()
            self.threadDemodAqc = None
        
        if self.threadCharact is not None:
            self.threadCharact.stop()
            self.threadCharact = None

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

# #############################MAIN##############################


if __name__ == '__main__':
    app = Qt.QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec_()
