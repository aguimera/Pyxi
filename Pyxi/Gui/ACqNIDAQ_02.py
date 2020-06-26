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
import PyqtTools.PlotModule as PltMod
import PyqtTools.DemodModule as DemMod
import PyqtTools.CharacterizationModule as Charact

class MainWindow(Qt.QWidget):
    ''' Main Window '''
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setFocusPolicy(Qt.Qt.WheelFocus)
        layout = Qt.QVBoxLayout(self)

        self.btnStart = Qt.QPushButton("Start Gen and Adq!")
        layout.addWidget(self.btnStart)

# #############################Save##############################
        self.SaveStateParams = FileMod.SaveSateParameters(QTparent=self,
                                                          name='State')
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.SaveStateParams,))

# #############################File##############################
        self.FileParams = FileMod.SaveFileParameters(QTparent=self,
                                                     name='Record File')
        self.Parameters.addChild(self.FileParams)

# #############################Sweep Config##############################
        self.SwParams = Charact.SweepsConfig(QTparent=self,
                                             name='Sweeps Configuration')
        self.Parameters.addChild(self.SwParams)

# #############################Configuration##############################
        self.GenAcqParams = NiConfig.GenAcqConfig(name='NI DAQ Configuration')
        self.Parameters.addChild(self.GenAcqParams)

# #############################NormalPlots##############################
        self.PsdPlotParams = PltMod.PSDParameters(name='PSD Plot Options')
        self.PsdPlotParams.param('Fs').setValue(self.GenAcqParams.FsScope.value())
        self.PsdPlotParams.param('Fmin').setValue(50)
        self.PsdPlotParams.param('nAvg').setValue(50)
        self.Parameters.addChild(self.PsdPlotParams)

        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.GenAcqParams.GetRows())
        self.PlotParams.param('Fs').setValue(self.GenAcqParams.FsScope.value())

        self.Parameters.addChild(self.PlotParams)

# #############################Demodulation##############################
        self.DemodParams = DemMod.DemodParameters(name='Demod Options')
        self.Parameters.addChild(self.DemodParams)
        self.DemodConfig = self.DemodParams.param('DemodConfig')

# #############################Demodulation Plots############################
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

        # ############Instancias para cambios#################################
        self.GenAcqParams.param('CarriersConfig').sigTreeStateChanged.connect(self.on_CarriersConfig_changed)
        self.GenAcqParams.param('AcqConfig').param('FsGen').sigValueChanged.connect(self.on_FsScope_changed)
        self.GenAcqParams.param('AcqConfig').param('FsScope').sigValueChanged.connect(self.on_FsScope_changed)
        self.GenAcqParams.param('AcqConfig').param('NRow').sigValueChanged.connect(self.on_NRow_changed)
        self.DemodConfig.param('DSFact').sigValueChanged.connect(self.on_DSFact_changed)
        self.PlotParams.param('PlotEnable').sigValueChanged.connect(self.on_PlotEnable_changed)
        self.PsdPlotParams.param('PSDEnable').sigValueChanged.connect(self.on_PSDEnable_changed)
        self.DemodPlotParams.param('PlotEnable').sigValueChanged.connect(self.on_DemodPlotEnable_changed)
        self.DemodPsdPlotParams.param('PSDEnable').sigValueChanged.connect(self.on_DemodPSDEnable_changed)
        self.PlotParams.param('RefreshTime').sigValueChanged.connect(self.on_RefreshTimePlt_changed)
        self.PlotParams.param('ViewTime').sigValueChanged.connect(self.on_SetViewTimePlt_changed)
        self.DemodPlotParams.param('RefreshTime').sigValueChanged.connect(self.on_RefreshTimeDemod_changed)
        self.DemodPlotParams.param('ViewTime').sigValueChanged.connect(self.on_SetViewTimeDemod_changed)
        
        self.SwParams.param('SweepsConfig').param('Start/Stop Sweep').sigActivated.connect(self.on_Sweep_start)
        self.SwParams.param('SweepsConfig').param('Pause Sweep').sigActivated.connect(self.on_Sweep_paused)
        
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
        self.threadCharact = None

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
        self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(
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
        self.DemodParams.ReCalc_DSFact(self.GenAcqParams.BufferSize.value())
        self.DemodPsdPlotParams.param('Fs').setValue(self.DemodParams.DSFs.value())
        self.DemodPlotParams.param('Fs').setValue(self.DemodParams.DSFs.value())
        if self.DemodParams.DSFs.value() >= np.min(self.GenAcqParams.Freqs):
            print('WARNING: FsDemod is higher than FsMin')

    def on_NRow_changed(self):
        self.PlotParams.SetChannels(self.GenAcqParams.GetRows())
        self.DemodPlotParams.SetChannels(self.DemodParams.GetChannels(
                                              self.GenAcqParams.Rows,
                                              self.GenAcqParams.GetCarriers())
                                         )

    def on_PSDEnable_changed(self):
        if self.threadAqc is not None:
            self.Gen_Destroy_PsdPlotter()

    def on_PlotEnable_changed(self):
        if self.threadAqc is not None:
            self.Gen_Destroy_Plotters()

    def on_DemodPSDEnable_changed(self):
        if self.threadAqc is not None:
            self.Gen_Destroy_PsdPlotter()

    def on_DemodPlotEnable_changed(self):
        if self.threadAqc is not None:
            self.Gen_Destroy_Plotters()
            
    def on_RefreshTimePlt_changed(self):
        if self.threadPlotter is not None:
            self.threadPlotter.SetRefreshTime(self.PlotParams.param('RefreshTime').value())

    def on_SetViewTimePlt_changed(self):
        if self.threadPlotter is not None:
            self.threadPlotter.SetViewTime(self.PlotParams.param('ViewTime').value())

    def on_RefreshTimeDemod_changed(self):
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.SetRefreshTime(self.DemodPlotParams.param('RefreshTime').value())

    def on_SetViewTimeDemod_changed(self):
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.SetViewTime(self.DemodPlotParams.param('ViewTime').value()) 

# #############################START Real Time Acquisition ####################
    def on_btnStart(self):
        if self.threadAqc is None:
            print('started')
            self.treepar.setParameters(self.Parameters, showTop=False)

            self.GenKwargs = self.GenAcqParams.GetGenParams()
            self.ScopeKwargs = self.GenAcqParams.GetRowParams()
            self.ScopeChns = self.GenAcqParams.GetRowsNames()
            self.DemodKwargs = self.DemodParams.GetParams()


            self.threadAqc = DataAcq.DataAcquisitionThread(GenConfig=self.GenKwargs,
                                                           Channels=self.ScopeChns, 
                                                           ScopeConfig=self.ScopeKwargs,
                                                           ) 
            self.threadAqc.NewMuxData.connect(self.on_NewSample)

            self.Gen_Destroy_PsdPlotter()
            self.Gen_Destroy_Plotters()
            self.SaveFiles()

            if self.DemodConfig.param('DemEnable').value() is True:
                self.threadDemodAqc = DemMod.DemodThread(Fcs=self.GenAcqParams.GetCarriers(),
                                                         RowList=self.ScopeChns,
                                                         FetchSize=self.GenAcqParams.BufferSize.value(),
                                                         Signal=self.threadAqc.Vcoi,
                                                         Gain=self.ScopeKwargs['GainBoard'],
                                                         **self.DemodKwargs)
                self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)

                self.threadDemodAqc.start()

            self.threadAqc.DaqInterface.SetSignal(Signal=self.threadAqc.Signal,
                                                  FsBase="",
                                                  FsGen=self.ScopeKwargs['FsGen']
                                                  )
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
            
            self.treepar.setParameters(self.Parameters, showTop=False)

            self.GenKwargs = self.GenAcqParams.GetGenParams()
            self.ScopeKwargs = self.GenAcqParams.GetRowParams()
            self.ScopeChns = self.GenAcqParams.GetRowsNames()
            self.nRows = len(self.ScopeChns)
            self.DemodKwargs = self.DemodParams.GetParams()
            self.SweepsKwargs = self.SwParams.GetConfigSweepsParams()
            self.DcSaveKwargs = self.SwParams.GetSaveSweepsParams()

            self.VdSweepVals = self.SweepsKwargs['VdSweep']
            self.VgSweepVals = self.SweepsKwargs['VgSweep']
            
            self.threadAqc = DataAcq.DataAcquisitionThread(GenConfig=self.GenKwargs,
                                                           Channels=self.ScopeChns, 
                                                           SwEnable=True,
                                                           VgsInit=(-1)*self.VgSweepVals[0],
                                                           VdValue=np.sqrt(2)*self.VdSweepVals[0],
                                                           **self.ScopeKwargs,) 
            self.threadAqc.NewMuxData.connect(self.on_NewSample)

            self.Gen_Destroy_PsdPlotter()
            self.Gen_Destroy_Plotters()

            self.threadDemodAqc = DemMod.DemodThread(Fcs=self.GenAcqParams.GetCarriers(),
                                                     RowList=self.ScopeChns,
                                                     FetchSize=self.ScopeKwargs['BufferSize'],
                                                     Signal=self.threadAqc.Vcoi,
                                                     Gain=self.ScopeKwargs['GainBoard'],
                                                     **self.DemodKwargs)
            self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)

            self.threadCharact = Charact.StbDetThread(nChannels=self.nRows*len(self.GenAcqParams.Freqs),
                                                      ChnName=self.DemodParams.GetChannels(self.GenAcqParams.Rows,
                                                                                           self.GenAcqParams.GetCarriers()),
                                                      PlotterDemodKwargs=self.DemodPsdPlotParams.GetParams(),
                                                      **self.SweepsKwargs
                                                      )
            
            self.threadCharact.NextVg.connect(self.on_NextVg)
            self.threadCharact.NextVd.connect(self.on_NextVd)
            self.threadCharact.CharactEnd.connect(self.on_CharactEnd)
            self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)
            self.threadCharact.start()

            self.threadDemodAqc.start()

            self.threadAqc.DaqInterface.SetSignal(Signal=self.threadAqc.Signal,
                                                  FsBase="",
                                                  FsGen=self.ScopeKwargs['FsGen']
                                                  )
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
                self.threadCharact.CharactEnd.disconnect()
            
            self.StopThreads()
# #############################Pause Sweep Acquisition ####################
    def on_Sweep_paused(self):
        if self.threadAqc is None:
            print('Sweep Restarted')
            
            self.treepar.setParameters(self.Parameters, showTop=False)

            self.GenKwargs = self.GenAcqParams.GetGenParams()
            self.ScopeKwargs = self.GenAcqParams.GetRowParams()
            self.ScopeChns = self.GenAcqParams.GetRowsNames()
            self.nRows = len(self.ScopeChns)
            self.DemodKwargs = self.DemodParams.GetParams()
            self.SweepsKwargs = self.SwParams.GetConfigSweepsParams()
            self.DcSaveKwargs = self.SwParams.GetSaveSweepsParams()

            self.VdSweepVals = self.SweepsKwargs['VdSweep']
            self.VgSweepVals = self.SweepsKwargs['VgSweep']
            
            self.threadAqc = DataAcq.DataAcquisitionThread(GenConfig=self.GenKwargs,
                                                           Channels=self.ScopeChns, 
                                                           SwEnable=True,
                                                           VgsInit=(-1)*self.VgSweepVals[self.LastVgsInd],
                                                           VdValue=np.sqrt(2)*self.VdSweepVals[self.LastVdsInd],
                                                           **self.ScopeKwargs,) 

            self.threadAqc.NewMuxData.connect(self.on_NewSample)

            self.Gen_Destroy_PsdPlotter()
            self.Gen_Destroy_Plotters()

            self.threadDemodAqc = DemMod.DemodThread(Fcs=self.GenAcqParams.GetCarriers(),
                                                     RowList=self.ScopeChns,
                                                     FetchSize=self.ScopeKwargs['BufferSize'],
                                                     Signal=self.threadAqc.Vcoi,
                                                     Gain=self.ScopeKwargs['GainBoard'],
                                                     **self.DemodKwargs)
            self.threadDemodAqc.NewData.connect(self.on_NewDemodSample)

            self.threadCharact = Charact.StbDetThread(nChannels=self.nRows*len(self.GenAcqParams.Freqs),
                                                      ChnName=self.DemodParams.GetChannels(self.GenAcqParams.Rows,
                                                                                           self.GenAcqParams.GetCarriers()),
                                                      PlotterDemodKwargs=self.DemodPsdPlotParams.GetParams(),
                                                      **self.SweepsKwargs
                                                      )
            self.threadCharact.VgIndex = self.LastVgsInd
            self.threadCharact.VdIndex = self.LastVdsInd
            self.threadCharact.NextVg.connect(self.on_NextVg)
            self.threadCharact.NextVd.connect(self.on_NextVd)
            self.threadCharact.CharactEnd.connect(self.on_CharactEnd)
            self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)
            self.threadCharact.start()

            self.threadDemodAqc.start()

            self.threadAqc.DaqInterface.SetSignal(Signal=self.threadAqc.Signal,
                                                  FsBase="",
                                                  FsGen=self.ScopeKwargs['FsGen']
                                                  )
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
                self.threadCharact.CharactEnd.disconnect()
            
            self.StopThreads()

# #############################New Sample Obtained############################
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        if self.threadSave is not None:
            # No usar Int hasta que se haya arreglado problema
            # Problema: Range scope no es exacto con lo cual
            # hay valores que no deberian saturar y saturan
            # self.threadSave.AddData(self.threadAqc.IntData)
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

        if self.threadCharact is not None:
            # print('Demod Done')
            self.threadCharact.AddData(OutDemodData/np.sqrt(2))  # (RMS)

        if self.threadDemodSave is not None:
            self.threadDemodSave.AddData(OutDemodData)
        if self.threadDemodPlotter is not None:
            self.threadDemodPlotter.AddData(OutDemodData)

        if self.threadDemodPsdPlotter is not None:
            self.threadDemodPsdPlotter.AddData(OutDemodData)

        if self.threadDemodPsdPlotter is not None:
            self.threadDemodPsdPlotter.AddData(OutDemodData)

# #############################Restart Timer Stabilization####################
    def on_NextVg(self):
        self.threadAqc.DaqInterface.VcmOut.StopTask()
        self.threadAqc.DaqInterface.SetVcm(Vcm=(-1)*self.threadCharact.NextVgs)
        # self.threadCharact.Timer.timeout.disconnect()
        # self.threadCharact.Timer.timeout.connect(self.threadCharact.printTime)
        self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)
        print('NEXT VGS SWEEP')

# #############################Nex Vd Value##############################
    def on_NextVd(self):
        self.threadAqc.NewMuxData.disconnect()
        self.threadAqc.DaqInterface.Stop()
        self.threadAqc.terminate()
        self.threadAqc = None
        
        self.threadAqc = DataAcq.DataAcquisitionThread(GenConfig=self.GenKwargs,
                                                        Channels=self.ScopeChns, 
                                                        SwEnable=True,
                                                        VgsInit=(-1)*self.VgSweepVals[0],
                                                        VdValue=np.sqrt(2)*self.threadCharact.NextVds,
                                                        **self.ScopeKwargs,
                                                         )
     
        self.threadAqc.NewMuxData.connect(self.on_NewSample)
        self.threadAqc.DaqInterface.SetSignal(self.threadAqc.Signal)
        self.threadAqc.start()
        self.threadCharact.Timer.timeout.connect(self.threadCharact.printTime)
        self.threadCharact.Timer.start(self.SweepsKwargs['TimeOut']*1000)

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

# #############################Savind Files##############################
    def SaveFiles(self):
        FileName = self.FileParams.param('File Path').value()
        if FileName == '':
            print('No file')
        else:
            if os.path.isfile(FileName):
                print('Remove File')
                os.remove(FileName)
            MaxSize = self.FileParams.param('MaxSize').value()
            if self.DemodConfig.param('DemEnable').value() is False:
                self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=self.nRows,
                                                           MaxSize=MaxSize,
                                                           Fs=self.GenAcqParams.FsScope.value(),
                                                           ChnNames=self.DemodParams.GetChannelsNames(self.GenAcqParams.Rows,
                                                                                                      self.GenAcqParams.GetCarriers()),            
                                                           # ChnNames=np.array(self.ScopeChns, dtype='S10'),
                                                           dtype='float' #comment when int save problem solved
                                                           )
                self.threadSave.start()

            if self.DemodConfig.param('DemEnable').value() is True:
                self.threadDemodSave = FileMod.DataSavingThread(FileName=FileName,
                                                                nChannels=self.nRows*len(self.GenAcqParams.Freqs),
                                                                MaxSize=MaxSize,
                                                                Fs = self.DemodParams.DSFs.value(),
                                                                ChnNames=self.DemodParams.GetChannelsNames(self.GenAcqParams.Rows,
                                                                                                            self.GenAcqParams.GetCarriers()),
                                                                dtype='float')

                self.threadDemodSave.start()

            GenName = FileName+'_GenConfig.dat'
            ScopeName = FileName+'_ScopeConfig.dat'
            DemodName = FileName+'_DemodConfig.dat'
            if os.path.isfile(GenName):
                print('Overwriting  file')
                OutGen = input('y/n + press(Enter)')
                if OutGen == 'y':
                    FileMod.GenArchivo(GenName, self.GenKwargs)
            else:
                FileMod.GenArchivo(GenName, self.GenKwargs)

            if os.path.isfile(ScopeName):
                print('Overwriting  file')
                OutScope = input('y/n + press(Enter)')
                if OutScope == 'y':
                    FileMod.GenArchivo(ScopeName, self.ScopeKwargs)
            else:
                FileMod.GenArchivo(ScopeName, self.ScopeKwargs)

            if os.path.isfile(DemodName):
                print('Overwriting  file')
                OutScope = input('y/n + press(Enter)')
                if OutScope == 'y':
                    FileMod.GenArchivo(DemodName, self.DemodKwargs)
            else:
                FileMod.GenArchivo(DemodName, self.DemodKwargs)

# #############################Generate and Destroy Plots#####################
    def Gen_Destroy_Plotters(self):
        if self.threadPlotter is None:
            if self.PlotParams.param('PlotEnable').value() is True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
                self.threadPlotter.start()
        if self.threadPlotter is not None:
            if self.PlotParams.param('PlotEnable').value() is False:
                self.threadPlotter.stop()
                self.threadPlotter = None

        if self.threadDemodPlotter is None:
            if self.DemodPlotParams.param('PlotEnable').value() is True:
                PlotterDemodKwargs = self.DemodPlotParams.GetParams()
                self.threadDemodPlotter = PltMod.Plotter(**PlotterDemodKwargs)
                self.threadDemodPlotter.start()
        if self.threadDemodPlotter is not None:
            if self.DemodPlotParams.param('PlotEnable').value() is False:
                self.threadDemodPlotter.stop()
                self.threadDemodPlotter = None

    def Gen_Destroy_PsdPlotter(self):
        if self.threadPsdPlotter is None:
            if self.PsdPlotParams.param('PSDEnable').value() is True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPsdPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                          nChannels=self.nRows,
                                                          **self.PsdPlotParams.GetParams())
                self.threadPsdPlotter.start()
        if self.threadPsdPlotter is not None:
            if self.PsdPlotParams.param('PSDEnable').value() is False:
                self.threadPsdPlotter.stop()
                self.threadPsdPlotter = None

        if self.threadDemodPsdPlotter is None:
            if self.DemodPsdPlotParams.param('PSDEnable').value() is True:
                PlotterDemodKwargs = self.DemodPlotParams.GetParams()
                self.threadDemodPsdPlotter = PltMod.PSDPlotter(ChannelConf=PlotterDemodKwargs['ChannelConf'],
                                                               nChannels=self.nRows*len(self.GenAcqParams.Freqs),
                                                               **self.DemodPsdPlotParams.GetParams())
                self.threadDemodPsdPlotter.start()
        if self.threadDemodPsdPlotter is not None:
            if self.DemodPsdPlotParams.param('PSDEnable').value() is False:
                self.threadDemodPsdPlotter.stop()
                self.threadDemodPsdPlotter = None

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
