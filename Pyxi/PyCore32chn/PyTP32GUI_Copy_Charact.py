# -*- coding: utf-8 -*-
"""
Created on Tue Sep 15 10:44:03 2020

@author: user
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
import PyqtTools.PlotModule as PltMod

#import PyTPCore.FileModule as FileMod
#import PyTPCore.PlotModule as PltMod
import PyTP32Core.TPacqThread32 as AcqMod
import PyTP32Core.CharacterizationModule as Charact


class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()

        layout = Qt.QVBoxLayout(self)

        self.btnAcq = Qt.QPushButton("Start Acq!")
        layout.addWidget(self.btnAcq)

        self.SamplingPar = AcqMod.SampSetParam(name='SampSettingConf')
        self.SampPar = self.SamplingPar.param('Sampling Settings')
        self.Parameters = Parameter.create(name='App Parameters',
                                           type='group',
                                           children=(self.SamplingPar,))

        self.SamplingPar.NewConf.connect(self.on_NewConf)
        
# #############################Sweep Config##############################
        self.SwParams = Charact.SweepsConfig(QTparent=self,
                                             name='Sweeps Configuration')
        self.Parameters.addChild(self.SwParams)
        

        self.PlotParams = PltMod.PlotterParameters(name='Plot options')
        self.PlotParams.SetChannels(self.SamplingPar.GetChannelsNames())
        self.PlotParams.param('Fs').setValue(self.SamplingPar.Fs.value())

        self.Parameters.addChild(self.PlotParams)

        self.PSDParams = PltMod.PSDParameters(name='PSD Options')
        self.PSDParams.param('Fs').setValue(self.SamplingPar.Fs.value())
        self.Parameters.addChild(self.PSDParams)
        self.Parameters.sigTreeStateChanged.connect(self.on_pars_changed)
        
        self.SwParams.param('SweepsConfig').param('Start/Stop Sweep').sigActivated.connect(self.on_Sweep_start)
        self.SampPar.sigTreeStateChanged.connect(self.on_SampsSettingConf_changed)
        self.PlotParams.param('ViewTime').sigValueChanged.connect(self.on_RawPlot_changed)
        self.PlotParams.param('RefreshTime').sigValueChanged.connect(self.on_RawPlot_changed)

        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(650, 20, 400, 800)
        self.setWindowTitle('MainWindow')

        self.btnAcq.clicked.connect(self.on_btnStart)
        self.threadAcq = None
        self.threadCharact = None
        self.threadSave = None
        self.threadPlotter = None
        self.RefreshGrapg = None

        self.FileParameters = FileMod.SaveFileParameters(QTparent=self,
                                                         name='Record File')
        self.Parameters.addChild(self.FileParameters)

        self.ConfigParameters = FileMod.SaveSateParameters(QTparent=self,
                                                           name='Configuration File')
        self.Parameters.addChild(self.ConfigParameters)

    def on_pars_changed(self, param, changes):
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

        # if childName == 'SampSettingConf.Sampling Settings.Fs':
        #     self.PlotParams.param('Fs').setValue(data)
        #     self.PSDParams.param('Fs').setValue(data)

        # if childName == 'SampSettingConf.Sampling Settings.Vgs':
        #     if self.threadAcq:
        #         Vds = self.threadAcq.DaqInterface.Vds
        #         self.threadAcq.DaqInterface.SetBias(Vgs=data, Vds=Vds)

        # if childName == 'SampSettingConf.Sampling Settings.Vds':
        #     if self.threadAcq:
        #         Vgs = self.threadAcq.DaqInterface.Vgs
        #         self.threadAcq.DaqInterface.SetBias(Vgs=Vgs, Vds=data)

        # if childName == 'Plot options.RefreshTime':
        #     if self.threadPlotter is not None:
        #         self.threadPlotter.SetRefreshTime(data)

        # if childName == 'Plot options.ViewTime':
        #     if self.threadPlotter is not None:
        #         self.threadPlotter.SetViewTime(data)

        if childName == 'SampSettingConf.Sampling Settings.Graph':
            print('ActionButton')
            self.RefreshGrapg = True
            
    def on_SampsSettingConf_changed(self):
        Fs = self.SampPar.param('Fs').value()
        self.PlotParams.param('Fs').setValue(Fs)
        self.PSDParams.param('Fs').setValue(Fs)
        if self.threadAcq:
            Vds = self.threadAcq.DaqInterface.Vds
            VgsNew = self.SampPar.param('Vgs').value()
            self.threadAcq.DaqInterface.SetBias(Vgs=VgsNew, Vds=Vds)
            Vgs = self.threadAcq.DaqInterface.Vgs
            VdsNew = self.SampPar.param('Vds').value()
            self.threadAcq.DaqInterface.SetBias(Vgs=Vgs, Vds=VdsNew)
    
    def on_RawPlot_changed(self):
        if self.threadPlotter is not None:
            ViewTime = self.PlotParams.param('ViewTime').value()
            RefreshTime = self.PlotParams.param('RefreshTime').value()
            self.threadPlotter.SetViewTime(ViewTime)           
            self.threadPlotter.SetRefreshTime(RefreshTime)
        
    def on_NewConf(self):
        self.Parameters.sigTreeStateChanged.disconnect()
        self.PlotParams.SetChannels(self.SamplingPar.GetChannelsNames())
        self.Parameters.sigTreeStateChanged.connect(self.on_pars_changed)

    def on_btnStart(self):
        if self.threadAcq is None:
            GenKwargs = self.SamplingPar.GetSampKwargs()
            GenChanKwargs = self.SamplingPar.GetChannelsConfigKwargs()
            self.threadAcq = AcqMod.DataAcquisitionThread(ChannelsConfigKW=GenChanKwargs,
                                                          SampKw=GenKwargs)
            self.threadAcq.NewTimeData.connect(self.on_NewSample)
            self.threadAcq.start()
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
            self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
            self.threadPlotter.start()

            self.threadPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                      nChannels=PlotterKwargs['nChannels'],
                                                      **self.PSDParams.GetParams())
            self.threadPSDPlotter.start()

            self.btnAcq.setText("Stop Gen")
            self.OldTime = time.time()
            self.Tss = []
        else:
            self.threadAcq.DaqInterface.Stop()
            self.threadAcq = None

            if self.threadSave is not None:
                self.threadSave.terminate()
                self.threadSave = None

            self.threadPlotter.terminate()
            self.threadPlotter = None

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

        self.threadPlotter.AddData(self.threadAcq.aiData)
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
            
            self.threadAcq = AcqMod.DataAcquisitionThread(ChannelsConfigKW=GenChanKwargs,
                                                          SampKw=GenKwargs)
            self.threadAcq.NewTimeData.connect(self.on_NewSample)

            self.threadCharact.start()
            self.threadAcq.start()
            PlotterKwargs = self.PlotParams.GetParams()

            self.threadPlotter = PltMod.Plotter(**PlotterKwargs)
            self.threadPlotter.start()

            self.threadPSDPlotter = PltMod.PSDPlotter(ChannelConf=PlotterKwargs['ChannelConf'],
                                                      nChannels=PlotterKwargs['nChannels'],
                                                      **self.PSDParams.GetParams())
            self.threadPSDPlotter.start()

            self.btnAcq.setText("Stop Gen")
            self.OldTime = time.time()
            self.Tss = []
        else:
            self.threadAcq.DaqInterface.Stop()
            self.threadAcq = None
            
            if self.threadCharact is not None:
                # self.threadCharact.NextVg.disconnect()
                # self.threadCharact.NextVd.disconnect()
                self.threadCharact.stop()
                self.threadCharact.CharactEnd.disconnect()
                self.threadCharact = None

            self.threadPlotter.terminate()
            self.threadPlotter = None

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