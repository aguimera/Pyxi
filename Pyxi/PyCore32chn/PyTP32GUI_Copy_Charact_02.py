# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 13:19:19 2020

@author: Lucia
"""

from __future__ import print_function
from PyQt5 import Qt
from qtpy.QtWidgets import (QHeaderView, QCheckBox, QSpinBox, QLineEdit,
                            QDoubleSpinBox, QTextEdit, QComboBox,
                            QTableWidget, QAction, QMessageBox, QFileDialog,
                            QInputDialog)

from qtpy import QtWidgets, uic
import numpy as np
import time
import os
import sys
from pyqtgraph.parametertree import Parameter, ParameterTree

import PyqtTools.FileModule as FileMod

from PyqtTools.PlotModule import Plotter as TimePlt
from PyqtTools.PlotModule import PlotterParameters as TimePltPars
from PyqtTools.PlotModule import PSDPlotter as PSDPlt
from PyqtTools.PlotModule import PSDParameters as PSDPltPars

import PyTP32Core.CharacterizationModule as Charact
import PyqtTools.DataAcquisition_Time_Freq as AcqMod


class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()

        layout = Qt.QVBoxLayout(self)

        self.btnAcq = Qt.QPushButton("Start Acq!")
        layout.addWidget(self.btnAcq)

        self.ResetGraph = Qt.QPushButton("Reset Graphics")
        layout.addWidget(self.ResetGraph)
        
        self.threadAcq = None
        self.threadCharact = None
        self.threadSave = None
        self.threadPlotter = None
        self.threadPSDPlotter = None
        
        
        self.SamplingPar = AcqMod.SampSetParam(name='SampSettingConf')
        self.SampPar = self.SamplingPar.param('Sampling Settings')
# #############################Save##############################
        self.ConfigParameters = FileMod.SaveSateParameters(QTparent=self,
                                                           name='Configuration File')

# #############################File##############################
        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        
# #############################Sweep Config##############################
        self.SwParams = Charact.SweepsConfig(QTparent=self,
                                             name='Sweeps Configuration')

# #############################NormalPlots##############################
        self.PlotParams = TimePltPars(name='TimePlt',
                                      title='Time Plot Options')

        self.PsdPlotParams = PSDPltPars(name='PSDPlt',
                                        title='PSD Plot Options')
        
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.ConfigParameters,
                                                     self.SwParams,
                                                     self.FileParameters,
                                                     self.SamplingPar,
                                                     self.PlotParams,
                                                     self.PsdPlotParams,
                                                     ))

        self.SamplingPar.param('Sampling Settings').param('Fs').sigValueChanged.connect(self.on_FsChanged)
        self.SamplingPar.NewConf.connect(self.on_NewConf)

        self.PsdPlotParams.NewConf.connect(self.on_NewPSDConf)
        self.PlotParams.NewConf.connect(self.on_NewPlotConf)
        
        self.SwParams.param('SweepsConfig').param('Start/Stop Sweep').sigActivated.connect(self.on_Sweep_start)
        
        self.on_NewConf()
        self.on_FsChanged()
        
        self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')
        
        layout.addWidget(self.treepar)

        self.setGeometry(650, 20, 400, 800)
        self.setWindowTitle('MainWindow')
        self.btnAcq.clicked.connect(self.on_btnStart)
        self.ResetGraph.clicked.connect(self.on_ResetGraph)
        
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
      
        if childName == 'SampSettingConf.Sampling Settings.Vgs':
            if self.threadAcq:
                Vds = self.threadAcq.DaqInterface.Vds
                self.threadAcq.DaqInterface.SetBias(Vgs=data, Vds=Vds)

        if childName == 'SampSettingConf.Sampling Settings.Vds':
            if self.threadAcq:
                Vgs = self.threadAcq.DaqInterface.Vgs
                self.threadAcq.DaqInterface.SetBias(Vgs=Vgs, Vds=data)
    
    def on_NewConf(self):
        self.PlotParams.SetChannels(self.SamplingPar.GetChannelsNames())
        self.PsdPlotParams.ChannelConf = self.PlotParams.ChannelConf
        nChannels = self.PlotParams.param('nChannels').value()
        self.PsdPlotParams.param('nChannels').setValue(nChannels)
        
    def on_FsChanged(self):
        self.PlotParams.param('Fs').setValue(self.SamplingPar.Fs.value())
        self.PsdPlotParams.param('Fs').setValue(self.SamplingPar.Fs.value())

    def on_NewPSDConf(self):
        if self.threadPSDPlotter is not None:
            nFFT = self.PsdPlotParams.param('nFFT').value()
            nAvg = self.PsdPlotParams.param('nAvg').value()
            self.threadPSDPlotter.InitBuffer(nFFT=nFFT, nAvg=nAvg)

    def on_NewPlotConf(self):
        if self.threadPlotter is not None:
            ViewTime = self.PlotParams.param('ViewTime').value()
            self.threadPlotter.SetViewTime(ViewTime)        
            RefreshTime = self.PlotParams.param('RefreshTime').value()
            self.threadPlotter.SetRefreshTime(RefreshTime)   
     
    def on_ResetGraph(self):
        if self.threadAcq is None:
            return

        # Plot and PSD threads are stopped
        if self.threadPlotter is not None:
            self.threadPlotter.stop()
            self.threadPlotter = None

        if self.threadPSDPlotter is not None:
            self.threadPSDPlotter.stop()
            self.threadPSDPlotter = None

        if self.PlotParams.param('PlotEnable').value():
            Pltkw = self.PlotParams.GetParams()
            self.threadPlotter = TimePlt(**Pltkw)
            self.threadPlotter.start()

        if self.PsdPlotParams.param('PlotEnable').value():
            PSDKwargs = self.PsdPlotParams.GetParams()
            self.threadPSDPlotter = PSDPlt(**PSDKwargs)
            self.threadPSDPlotter.start()

    def on_btnStart(self):
        if self.threadAcq is None:
            GenKwargs = self.SamplingPar.GetSampKwargs()
            GenChanKwargs = self.SamplingPar.GetChannelsConfigKwargs()
            self.threadAcq = AcqMod.DataAcquisitionThread(MeaType='Time',
                                                          ChannelsConfigKW=GenChanKwargs,
                                                          SampKw=GenKwargs)
            self.threadAcq.NewTimeData.connect(self.on_NewSample)
            self.threadAcq.start()
            self.on_ResetGraph()
            PlotterKwargs = self.PlotParams.GetParams()

#            FileName = self.Parameters.param('File Path').value()
            FileName = self.FileParameters.FilePath()
            print('Filename', FileName)
            if FileName == '':
                print('No file')
            else:
                if os.path.isfile(FileName):
                    print('Remove File')
                    os.remove(FileName)
                MaxSize = self.FileParameters.param('MaxSize').value()
                ch = (list(self.SamplingPar.GetChannelsNames()))
                self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                           nChannels=PlotterKwargs['nChannels'],
                                                           MaxSize=MaxSize,
                                                           Fs=self.SamplingPar.SampSet.param('Fs').value(),
                                                           ChnNames=np.array(ch, dtype='S10'),
                                                           )
                self.threadSave.start()

            self.btnAcq.setText("Stop Gen")
            self.OldTime = time.time()
            self.Tss = []
        else:
            self.threadAcq.DaqInterface.Stop()
            self.threadAcq = None

            if self.threadSave is not None:
                self.threadSave.terminate()
                self.threadSave = None
            
            if self.threadPlotter is not None:
                self.threadPlotter.stop()
                self.threadPlotter.terminate()
                self.threadPlotter = None
            
            if self.threadPSDPlotter is not None:
                self.threadPSDPlotter.stop()
                self.threadPSDPlotter.terminate()
                self.threadPSDPlotter = None
            
            self.btnAcq.setText("Start Gen")

    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.Tss.append(Ts)
        self.OldTime = time.time()

        if self.threadSave is not None:
            self.threadSave.AddData(self.threadAcq.aiData)
            if self.RefreshGrapg:
                self.threadSave.FileBuff.RefreshPlot()
                self.RefreshGrapg = None

        if self.threadCharact is not None:
            if self.threadCharact.Stable and self.threadCharact.ACenable is True:
                self.threadCharact.AddData(self.threadAcq.aiDataAC)
            else:
                self.threadCharact.AddData(self.threadAcq.aiData)  # (RMS)

        if self.threadPlotter is not None:
            self.threadPlotter.AddData(self.threadAcq.aiData)

        if self.threadPSDPlotter is not None:
            if self.threadAcq.aiDataAC is not None:
                self.threadPSDPlotter.AddData(self.threadAcq.aiDataAC)
            else:
                self.threadPSDPlotter.AddData(self.threadAcq.aiData)

        
        print('Sample time', Ts, np.mean(self.Tss))

    def on_Sweep_start(self):
        if self.threadAcq is None:
            self.Paused = False
            
            GenKwargs = self.SamplingPar.GetSampKwargs()            
            GenChanKwargs = self.SamplingPar.GetChannelsConfigKwargs()
            self.SweepsKwargs = self.SwParams.GetConfigSweepsParams()
            self.DcSaveKwargs = self.SwParams.GetSaveSweepsParams()
            
            self.threadCharact = Charact.StbDetThread(nChannels=self.PlotParams.GetParams()['nChannels'],
                                                      ChnName=self.SamplingPar.GetChannelsNames(),
                                                      PlotterDemodKwargs=self.PSDParams.GetParams(),
                                                      **self.SweepsKwargs
                                                      )
            # self.threadCharact.DataStab.connect(self.on_dataStab)
            self.threadCharact.NextVg.connect(self.on_NextVg)
            self.threadCharact.NextVd.connect(self.on_NextVd)
            self.threadCharact.CharactEnd.connect(self.on_CharactEnd)
            
            GenKwargs['Vgs'] = self.threadCharact.NextVgs
            GenKwargs['Vds'] = self.threadCharact.NextVds
            
            self.threadAcq = AcqMod.DataAcquisitionThread(MeaType='Time',
                                                          ChannelsConfigKW=GenChanKwargs,
                                                          SampKw=GenKwargs)
            self.threadAcq.NewTimeData.connect(self.on_NewSample)

            self.threadCharact.start()
            self.threadAcq.start()
            PlotterKwargs = self.PlotParams.GetParams()

            self.on_ResetGraph()

            self.btnAcq.setText("Stop Gen")
            self.OldTime = time.time()
            self.Tss = []
        else:
            self.threadAcq.DaqInterface.Stop()
            self.threadAcq = None
            
            if self.threadCharact is not None:
                self.threadCharact.stop()
                self.threadCharact.CharactEnd.disconnect()
                self.threadCharact = None

              if self.threadPlotter is not None:
                self.threadPlotter.stop()
                self.threadPlotter.terminate()
                self.threadPlotter = None
            
            if self.threadPSDPlotter is not None:
                self.threadPSDPlotter.stop()
                self.threadPSDPlotter.terminate()
                self.threadPSDPlotter = None

            self.btnAcq.setText("Start Gen")
            
# #############################Restart Timer Stabilization####################
    def on_NextVg(self):
        self.threadAcq.DaqInterface.SetBias(Vgs=self.threadCharact.NextVgs,
                                            Vds=self.threadCharact.NextVds,
                                            )

        print('NEXT VGS SWEEP')

# #############################Nex Vd Value##############################
    def on_NextVd(self):        
        self.threadAcq.DaqInterface.SetBias(Vgs=self.threadCharact.NextVgs,
                                            Vds=self.threadCharact.NextVds,
                                            )
        
    def on_CharactEnd(self):
        print('END Charact')
        self.threadCharact.NextVg.disconnect()
        self.threadCharact.NextVd.disconnect()
        self.threadCharact.CharactEnd.disconnect()
        CharactDCDict = self.threadCharact.DCDict
        CharactACDict = self.threadCharact.ACDict

        self.threadCharact.SaveDCAC.SaveDicts(Dcdict=CharactDCDict,
                                              Acdict=CharactACDict,
                                              **self.DcSaveKwargs)
        self.threadAcq.NewTimeData.disconnect()
        
        self.threadAcq.DaqInterface.Stop()
        self.threadAcq.terminate()
        self.threadAcq = None

        self.threadPlotter.terminate()
        self.threadPlotter = None


if __name__ == '__main__':
    app = Qt.QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec_()