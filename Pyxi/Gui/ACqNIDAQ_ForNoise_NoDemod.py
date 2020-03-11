# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 16:09:59 2020

@author: Lucia
"""

from __future__ import print_function
import os

import numpy as np
import time

from PyQt5 import Qt

from pyqtgraph.parametertree import Parameter, ParameterTree

import Pyxi.DataAcquisition as DataAcq
import Pyxi.GenAqcModule as NiConfig

import PyqtTools.FileModule as FileMod
import PyqtTools.PlotModule as PltMod

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

        # ############Instancias para cambios#################################
        self.GenAcqParams.param('AcqConfig').param('FsGen').sigValueChanged.connect(self.on_FsScope_changed)
        self.GenAcqParams.param('AcqConfig').param('FsScope').sigValueChanged.connect(self.on_FsScope_changed)
        self.GenAcqParams.param('AcqConfig').param('NRow').sigValueChanged.connect(self.on_NRow_changed)
       
        self.PlotParams.param('PlotEnable').sigValueChanged.connect(self.on_PlotEnable_changed)
        self.PsdPlotParams.param('PSDEnable').sigValueChanged.connect(self.on_PSDEnable_changed)        
        self.PlotParams.param('RefreshTime').sigValueChanged.connect(self.on_RefreshTimePlt_changed)
        self.PlotParams.param('ViewTime').sigValueChanged.connect(self.on_SetViewTimePlt_changed)
        

        self.Parameters.sigTreeStateChanged.connect(self.on_Params_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(550, 20, 300, 700)
        self.setWindowTitle('MainWindow')
        self.btnStart.clicked.connect(self.on_btnStart)

        self.threadAqc = None
        self.threadSave = None
        self.threadPlotter = None
        self.threadPsdPlotter = None
        
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
    def on_FsScope_changed(self):
        n = round(self.GenAcqParams.FsGen.value() /
                  self.GenAcqParams.FsScope.value()
                  )

        self.GenAcqParams.param('AcqConfig').param('FsScope').setValue(
                                            self.GenAcqParams.FsGen.value() / n
                                            )
        self.PlotParams.param('Fs').setValue(self.GenAcqParams.FsScope.value())
        self.PsdPlotParams.param('Fs').setValue(self.GenAcqParams.FsScope.value())
        
    def on_NRow_changed(self):
        self.PlotParams.SetChannels(self.GenAcqParams.GetRows())

    def on_PSDEnable_changed(self):
        if self.threadAqc is not None:
            self.Gen_Destroy_PsdPlotter()

    def on_PlotEnable_changed(self):
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
            
# #############################START##############################
    def on_btnStart(self):
        if self.threadAqc is None:
            print('started')

            self.treepar.setParameters(self.Parameters, showTop=False)

            self.GenKwargs = self.GenAcqParams.GetGenParams()
            self.ScopeKwargs = self.GenAcqParams.GetRowParams()
            self.ScopeChns = self.GenAcqParams.GetRowsNames()

            self.threadAqc = DataAcq.DataAcquisitionThread(GenConfig=self.GenKwargs,
                                                           Channels=self.ScopeChns, 
                                                           ScopeConfig=self.ScopeKwargs
                                                           ) 
            self.threadAqc.NewMuxData.connect(self.on_NewSample)

            self.Gen_Destroy_PsdPlotter()
            self.Gen_Destroy_Plotters()
            self.SaveFiles()

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
            
# #############################New Sample Obtained############################
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
        if self.threadSave is not None:
            self.threadSave.AddData(self.threadAqc.OutData)

        if self.threadPlotter is not None:
            self.threadPlotter.AddData(self.threadAqc.OutData)

        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.AddData(self.threadAqc.OutData)

        print('Sample time', Ts)

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
            self.threadSave = FileMod.DataSavingThread(FileName=FileName,
                                                       nChannels=self.ScopeKwargs['NRow'],
                                                       MaxSize=MaxSize,
                                                       Fs=self.GenAcqParams.FsScope.value(),
                                                       ChnNames=self.GenAcqConfig.GetChannelsNames(self.GenAcqParams.Rows,
                                                                                                  self.GenAcqParams.GetCarriers()),            
                                                       dtype='float' #comment when int save problem solved
                                                       )
            self.threadSave.start()

            GenName = FileName+'_GenConfig.dat'
            ScopeName = FileName+'_ScopeConfig.dat'
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

    def Gen_Destroy_PsdPlotter(self):
        if self.threadPsdPlotter is None:
            if self.PsdPlotParams.param('PSDEnable').value() is True:
                PlotterKwargs = self.PlotParams.GetParams()
                self.threadPsdPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                          nChannels=self.ScopeKwargs['NRow'],
                                                          **self.PsdPlotParams.GetParams())
                self.threadPsdPlotter.start()
        if self.threadPsdPlotter is not None:
            if self.PsdPlotParams.param('PSDEnable').value() is False:
                self.threadPsdPlotter.stop()
                self.threadPsdPlotter = None

# #############################STOP##############################
    def StopThreads(self):
        if self.threadSave is not None:
            self.threadSave.stop()
            self.threadSave = None

        if self.threadPlotter is not None:
            self.threadPlotter.stop()
            self.threadPlotter = None

        if self.threadPsdPlotter is not None:
            self.threadPsdPlotter.stop()
            self.threadPsdPlotter = None

# #############################MAIN##############################

if __name__ == '__main__':
    app = Qt.QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec_()
