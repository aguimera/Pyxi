# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 08:17:10 2020

@author: Lucia
"""

import numpy as np
import pickle
import datetime
from scipy.signal import welch

import pyqtgraph.parametertree.parameterTypes as pTypes

from PyQt5 import Qt
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog

import PyGFETdb.DataStructures as PyData
import PyGFETdb.PlotDataClass as PyFETpl
import PyqtTools.PlotModule as PltBuffer2D

################PARAMETER TREE################################################

ConfigSweepsParams = {'name': 'SweepsConfig',
                      'type': 'group',
                    'children': ({'name': 'Start/Stop Sweep',
                                  # 'title': 'Start Sweep',
                                  'type': 'action', },
                                 {'name': 'Pause/ReStart Sweep',
                                  # 'title': 'Start Sweep',
                                  'type': 'action', },
                                 {'name': 'ACenable',
                                  'title': 'AC Characterization',
                                  'type': 'bool',
                                  'value': True, },
                                 {'name': 'StabCriteria',
                                  'type': 'list',
                                  'values': ['All channels', 'One Channel', 'Mean'],
                                  'value': 'Mean',
                                  'visible': True},
                                 {'name': 'VgSweep',
                                          'type': 'group',
                                          'children': ({'name': 'Vinit',
                                                        'type': 'float',
                                                        'value': 0,
                                                        'siPrefix': True,
                                                        'suffix': 'V'},
                                                       {'name': 'Vfinal',
                                                        'type': 'float',
                                                        'value': -0.4,
                                                        'siPrefix': True,
                                                        'suffix': 'V'},
                                                       {'name': 'NSweeps',
                                                        'type': 'int',
                                                        'value': 1,
                                                        'siPrefix': True,
                                                        'suffix': 'Sweeps'},
                                                       )},
                                 {'name': 'VdSweep',
                                  'type': 'group',
                                  'children': ({'name': 'Vinit',
                                                'type': 'float',
                                                'value': 0.02,
                                                'siPrefix': True,
                                                'suffix': 'VRMS'},
                                               {'name': 'Vfinal',
                                                'type': 'float',
                                                'value': 0.2,
                                                'siPrefix': True,
                                                'suffix': 'VRMS'},
                                               {'name': 'NSweeps',
                                                'type': 'int',
                                                'value': 1,
                                                'siPrefix': True,
                                                'suffix': 'Sweeps'},
                                               )},
                                 {'name': 'MaxSlope',
                                  'title': 'Maximum Slope',
                                  'type': 'float',
                                  'value': 1e-10,
                                  'siPrefix': True,
                                  'suffix': 'A/s'},
                                 {'name': 'TimeOut',
                                  'title': 'Max Time for Stabilization',
                                  'type': 'int',
                                  'value': 10,
                                  'siPrefix': True,
                                  'suffix': 's'},
                                 {'name': 'TimeBuffer',
                                  'title': 'Buffer Time for Stabilization',
                                  'type': 'int',
                                  'value': 1,
                                  'siPrefix': True,
                                  'suffix': 's'},
                                 {'name': 'DelayTime',
                                  'title': 'Time to wait for acquisition',
                                  'type': 'int',
                                  'value': 1,
                                  'siPrefix': True,
                                  'suffix': 's'},
                                 )}

SaveSweepsParams = ({'name': 'SaveSweepConfig',
                    'type': 'group',
                    'children': ({'name': 'Save File',
                                  'type': 'action'},
                                 {'name': 'Folder',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Oblea',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Disp',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Name',
                                  'type': 'str',
                                  'value': ''},
                                 {'name': 'Cycle',
                                  'type': 'int',
                                  'value': 0},
                                 )
                    })

class SweepsConfig(pTypes.GroupParameter):
    def __init__(self, QTparent, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.QTparent = QTparent
        
        self.addChild(ConfigSweepsParams)
        self.SwConfig = self.param('SweepsConfig')

        self.VgParams = self.SwConfig.param('VgSweep')
        self.VdParams = self.SwConfig.param('VdSweep')

        self.VgParams.sigTreeStateChanged.connect(self.on_Sweeps_Changed)
        self.VdParams.sigTreeStateChanged.connect(self.on_Sweeps_Changed)
        self.on_Sweeps_Changed()
        
        self.addChild(SaveSweepsParams)
        self.SvSwParams = self.param('SaveSweepConfig')
        self.SvSwParams.param('Save File').sigActivated.connect(self.FileDialog)

    def on_Sweeps_Changed(self):
        self.VgSweepVals = np.linspace(self.VgParams.param('Vinit').value(),
                                       self.VgParams.param('Vfinal').value(),
                                       self.VgParams.param('NSweeps').value())

        self.VdSweepVals = np.linspace(self.VdParams.param('Vinit').value(),
                                       self.VdParams.param('Vfinal').value(),
                                       self.VdParams.param('NSweeps').value())

    def FileDialog(self):
        RecordFile = QFileDialog.getExistingDirectory(self.QTparent,
                                                      "Select Directory",
                                                      )
        if RecordFile:
            self.SvSwParams.param('Folder').setValue(RecordFile)

    def FilePath(self):
        return self.param('Folder').value()
    
    def GetConfigSweepsParams(self):
        '''Returns de parameters to do the sweeps
           SwConfig={'Enable': True,
                     'VgSweep': array([ 0. , -0.1, -0.2, -0.3]),
                     'VdSweep': array([0.1]),
                     'MaxSlope': 1e-10,
                     'TimeOut': 10
                     }
        '''
        SwConfig = {}
        for Config in self.SwConfig.children():
            if Config.name() == 'Start/Stop Sweep':
                continue
            if Config.name() == 'Pause/ReStart Sweep':
                continue
            if Config.name() == 'VgSweep':
                SwConfig[Config.name()] = self.VgSweepVals
                continue
            if Config.name() == 'VdSweep':
                SwConfig[Config.name()] = self.VdSweepVals
                continue
            SwConfig[Config.name()] = Config.value()
        return SwConfig
    
    def GetSaveSweepsParams(self):
        '''Returns de parameters to save the caracterization
           Config={'Folder': 'C:/Users/Lucia/Dropbox (ICN2 AEMD - GAB GBIO)/
                              TeamFolderLMU/FreqMux/Lucia/DAQTests/SweepTests
                              /18_12_19',
                   'Oblea': 'testPyCont',
                   'Disp': 'Test',
                   'Name': 'Test',
                   'Cycle': 0
                   }
        '''
        Config = {}
        for Conf in self.SvSwParams.children():
            if Conf.name() == 'Save File':
                continue
            Config[Conf.name()] = Conf.value()

        return Config  

################CHARACTERIZATION THREAD#######################################
        
class StbDetThread(Qt.QThread):
    DataStab = Qt.pyqtSignal()
    NextVg = Qt.pyqtSignal()
    NextVd = Qt.pyqtSignal()
    CharactEnd = Qt.pyqtSignal()

    def __init__(self, ACenable, StabCriteria, VdSweep, VgSweep, MaxSlope, TimeOut, 
                 TimeBuffer, DelayTime, nChannels, ChnName, PlotterDemodKwargs, 
                 **kwargs):
        '''Initialization for Stabilitation Detection Thread
           VdVals: Array. Contains the values to use in the Vd Sweep.
                          [0.1, 0.2]
           VgVals: Array. Contains the values to use in the Vg Sweep
                          [0., -0.1, -0.2, -0.3]
           MaxSlope: float. Specifies the maximum slope permited to consider
                            the system is stabilazed, so the data is correct
                            to be acquired
           TimeOut: float. Specifies the maximum amount of time to wait the
                           signal to achieve MaxSlope, if TimeOut is reached
                           the data is save even it is not stabilazed
           nChannels: int. Number of acquisition channels (rows) active
           ChnName: dictionary. Specifies the name of Row+Column beign
                                processed and its index:
                                {'Ch04Col1': 0,
                                'Ch05Col1': 1,
                                'Ch06Col1': 2}
           PlotterDemodKwargs: dictionary. Contains Demodulation Configuration
                                           an parameters
                                           {'Fs': 5000.0,
                                           'nFFT': 8.0,
                                           'scaling': 'density',
                                           'nAvg': 50 }
        '''

        super(StbDetThread, self).__init__()
        # Init threads and flags
        self.threadCalcPSD = None
        self.ToStabData = None
        self.Wait = True
        self.Stable = False
        self.StabTimeOut = False
        # Define global variables
        self.ACenable = ACenable
        self.StabCriteria = StabCriteria
        self.MaxSlope = MaxSlope
        self.TimeOut = TimeOut
        self.DelayTime = DelayTime
        self.ElapsedTime = 0
        self.FsDemod = PlotterDemodKwargs['Fs']
        # Define global variables for Vg and Vd sweep
        self.VgIndex = 0
        self.VdIndex = 0
        self.VgSweepVals = VgSweep
        self.VdSweepVals = VdSweep
        self.NextVgs = self.VgSweepVals[self.VgIndex]
        self.NextVds =self.VdSweepVals[self.VdIndex]

        self.Timer = Qt.QTimer()
        # Define the buffer size
        self.Buffer = PltBuffer2D.Buffer2D(self.FsDemod,
                                           nChannels,
                                           TimeBuffer)
        #Define DC and AC dictionaries
        self.SaveDCAC = SaveDicts(ACenable=self.ACenable,
                                  SwVdsVals=VdSweep,
                                  SwVgsVals=VgSweep,
                                  Channels=ChnName,
                                  nFFT=int(PlotterDemodKwargs['nFFT']),
                                  FsDemod=self.FsDemod
                                  )
        if self.ACenable:
            self.threadCalcPSD = CalcPSD(nChns=nChannels,
                                         **PlotterDemodKwargs)
            self.threadCalcPSD.PSDDone.connect(self.on_PSDDone)
            self.SaveDCAC.PSDSaved.connect(self.on_NextVgs)
            
        else:
            self.SaveDCAC.DCSaved.connect(self.on_NextVgs)
        # Define the characterization plots   
        self.DCPlotVars = ('Ids', 'Rds', 'Gm', 'Ig')
        self.PlotSwDC = PyFETpl.PyFETPlot()
        self.PlotSwDC.AddAxes(self.DCPlotVars)

    def run(self):
        while True:
            if self.Buffer.IsFilled():
                self.CalcSlope()
                if self.Stable:
                    self.DataStab.emit()
                    self.Timer.stop()
                    self.Timer.deleteLater()
                    print('IsStable')
                    if self.ACenable:
                        self.threadCalcPSD.start()
                    self.SaveDCAC.SaveDCDict(Ids=self.DCIds,
                                             Dev=self.Dev,
                                             SwVgsInd=self.VgIndex,
                                             SwVdsInd=self.VdIndex)    
                self.Buffer.Reset()

            else:
                Qt.QThread.msleep(10)

    def AddData(self, NewData):
        if self.Stable is False:
            while self.Buffer.IsFilled():
                continue
            
            if self.Wait:
                self.ElapsedTime = self.ElapsedTime+len(NewData[:,0])*(1/self.FsDemod)
                Diff = self.DelayTime-self.ElapsedTime
                if Diff <= 0:
                    print('Delay Time finished')
                    self.Wait = False
                    self.ElapsedTime = 0
                    self.Timer = Qt.QTimer()
                    self.Timer.timeout.connect(self.printTime)
                    self.Timer.setSingleShot(True)
                    self.Timer.start(self.TimeOut*1000)
                    # self.Timer.singleShot(self.TimeOut*1000, self.printTime)
            else:            
                self.Buffer.AddData(NewData)
               
        if self.ACenable:
            if self.Stable is True:
                self.threadCalcPSD.AddData(NewData)

    def printTime(self):
        print('TimeOut')
        self.Timer.stop()
        self.Timer.deleteLater()
        self.CalcSlope()
        self.Stable = True
        self.DataStab.emit()
        if self.ACenable:
            self.threadCalcPSD.start()
        self.SaveDCAC.SaveDCDict(Ids=self.DCIds,
                                 Dev=self.Dev,
                                 SwVgsInd=self.VgIndex,
                                 SwVdsInd=self.VdIndex)  
        self.Buffer.Reset()

    def CalcSlope(self):
        self.Dev = np.ndarray((self.Buffer.shape[1],))
        self.DCIds = np.ndarray((self.Buffer.shape[1], 1))
        for ChnInd, dat in enumerate(self.Buffer.transpose()):
            r = len(dat)
            t = np.arange(0, (1/self.FsDemod)*r, (1/self.FsDemod))
            mm, oo = np.polyfit(t, dat, 1)
            self.Dev[ChnInd] = np.abs(np.mean(mm)) #slope (uA/s)
            self.DCIds[ChnInd] = oo
        print('Dev',self.Dev)
        Stab = 0
        if self.StabCriteria == 'All channels':
            for slope in self.Dev:
                if slope > self.MaxSlope:
                    Stab = -1
                    break
            if Stab == -1:
                self.Stable = False
            else:
                self.Stable = True 
        elif self.StabCriteria == 'One Channel':
            for slope in self.Dev:
                if slope < self.MaxSlope:
                    self.Stable = True
                    break
        elif self.StabCriteria == 'Mean':
            slope = np.mean(self.Dev)
            if slope < self.MaxSlope:
                self.Stable = True
                
    def on_PSDDone(self):
        self.freqs = self.threadCalcPSD.ff
        self.PSDdata = self.threadCalcPSD.psd
        self.threadCalcPSD.stop()
        self.SaveDCAC.SaveACDict(psd=self.PSDdata,
                                 ff=self.freqs,
                                 SwVgsInd=self.VgIndex,
                                 SwVdsInd=self.VdIndex
                                 )

    def on_NextVgs(self):
        self.Buffer.Reset()
        self.Stable = False
        self.VgIndex += 1
        if self.VgIndex < len(self.VgSweepVals):
            self.NextVgs = self.VgSweepVals[self.VgIndex]
            self.Wait = True
            print(self.VgIndex)
            self.UpdateSweepDcPlots(self.SaveDCAC.DevDCVals)
            self.NextVg.emit()
        else:
            self.VgIndex = 0
            self.NextVgs = self.VgSweepVals[self.VgIndex]
            self.UpdateSweepDcPlots(self.SaveDCAC.DevDCVals)
            self.on_NextVds()

    def on_NextVds(self):
        self.VdIndex += 1
        
        if self.VdIndex < len(self.VdSweepVals):
            self.NextVds = self.VdSweepVals[self.VdIndex]
            self.Wait = True
            print(self.VdIndex)
            self.NextVd.emit()

        else:
            self.VdIndex = 0
            self.NextVds = self.VdSweepVals[self.VdIndex]
            self.DCDict = self.SaveDCAC.DevDCVals
            if self.ACenable:
                self.ACDict = self.SaveDCAC.DevACVals
            else:
                self.ACDict = None
            self.CharactEnd.emit()
           
    def UpdateSweepDcPlots(self, Dcdict):
        if self.PlotSwDC:
            self.PlotSwDC.ClearAxes()
            self.PlotSwDC.PlotDataCh(Data=Dcdict)
            self.PlotSwDC.AddLegend()
            self.PlotSwDC.Fig.canvas.draw()  
            
    def stop(self):
        # self.Timer.stop()
        # self.Timer.deleteLater()
        if self.threadCalcPSD is not None:
            self.SaveDCAC.PSDSaved.disconnect()
            self.threadCalcPSD.PSDDone.disconnect()
            self.threadCalcPSD.stop()
        self.terminate()
        
################CALC PSD THREAD###############################################
        
class CalcPSD(Qt.QThread):
    PSDDone = Qt.pyqtSignal()
    def __init__(self, nChns, Fs, nFFT, nAvg, nChannels, scaling, **kwargs):
        '''Initialization of the thread that is used to calculate the PSD
           Fs: float. Sampling Frequency
           nFFT: float.
           nAvg: int.
           nChannels: int. Number of acquisition channels (rows) active
           scaling: str. Two options, Density or Spectrum
        '''
        super(CalcPSD, self).__init__()

        self.scaling = scaling
        self.nFFT = 2**nFFT
        self.nChannels = nChns
        self.Fs = Fs
        self.BufferSize = self.nFFT * nAvg
        self.Buffer = PltBuffer2D.Buffer2D(self.Fs, self.nChannels,
                                           self.BufferSize/self.Fs)

    def run(self, *args, **kwargs):
        while True:
            if self.Buffer.IsFilled():
                self.ff, self.psd = welch(self.Buffer,
                                          fs=self.Fs,
                                          nperseg=self.nFFT,
                                          scaling=self.scaling,
                                          axis=0)
                self.Buffer.Reset()
                self.PSDDone.emit()

            else:
                Qt.QCoreApplication.processEvents()
                Qt.QThread.msleep(200)

    def AddData(self, NewData):
        self.Buffer.AddData(NewData)

    def stop(self):
        self.Buffer.Reset()
        self.terminate()

################SAVE CHARACTERIZATION DICTs###################################
        
class SaveDicts(QObject):
    PSDSaved = Qt.pyqtSignal()
    DCSaved = Qt.pyqtSignal()

    def __init__(self, SwVdsVals, SwVgsVals, Channels,
                 nFFT, FsDemod, Gate=False, ACenable=True):
        '''Initialize the Dictionaries to Save the Characterization
           SwVdsVals: array. Contains the values for the Vd sweep
                             [0.1, 0.2]
           SwVgsVals: array. Contains the values for the Vg sweep
                             [ 0.,  -0.1, -0.2, -0.3]
           Channels: dictionary. Contains the names from each demodulated
                                 channel and column and its index
                                 {'Ch04Col1': 0, 'Ch05Col1': 1, 'Ch06Col1': 2}
           nFFT: int.
                   8
           FsDemod: float. Sampling Frequency used in the Demodulation Process
                           5000.0
        '''
        super(SaveDicts, self).__init__()
        # self.ChNamesList = sorted(Channels)
        # self.ChannelIndex = {}

        # index = 0
        # for ch in sorted(Channels):
        #     self.ChannelIndex[ch] = (index)
        #     index = index+1
        self.ChNamesList = sorted(Channels)
        self.ChannelIndex = Channels
        self.DevDCVals = self.InitDCRecord(nVds=SwVdsVals,
                                           nVgs=SwVgsVals,
                                           ChNames=self.ChNamesList,
                                           Gate=Gate)
        # AC dictionaries
        if ACenable:
            self.PSDnFFT = 2**nFFT
            self.PSDFs = FsDemod
    
            Fpsd = np.fft.rfftfreq(self.PSDnFFT, 1/self.PSDFs)
            nFgm = np.array([])
    
            self.DevACVals = self.InitACRecord(nVds=SwVdsVals,
                                               nVgs=SwVgsVals,
                                               nFgm=nFgm,
                                               nFpsd=Fpsd,
                                               ChNames=self.ChNamesList)
        
    def InitDCRecord(self, nVds, nVgs, ChNames, Gate):

        Time = datetime.datetime.now()
        DevDCVals={}
        for Ch in ChNames:
            DCVals={'Ids':np.ones((len(nVgs),len(nVds)))*np.NaN,
                    'Dev':np.ones((len(nVgs),len(nVds)))*np.NaN,
                    'Vds':nVds,
                    'Vgs':nVgs,
                    'ChName':Ch,
                    'Name':Ch,
                    'DateTime':Time}
            DevDCVals[Ch]=DCVals
    
        if Gate:
            GateDCVals = {'Ig':np.ones((len(nVgs),len(nVds)))*np.NaN,
                        'Vds':nVds,
                        'Vgs':nVgs,
                        'ChName':'Gate',
                        'Name':'Gate',
                        'DateTime':Time}
            DevDCVals['Gate']=GateDCVals
    
        return DevDCVals

    def InitACRecord(self, nVds, nVgs, nFgm, nFpsd, ChNames):
    
        Time = datetime.datetime.now()
        DevACVals={}
        for Ch in ChNames:
            noise = {}
            gm = {}
            for i in range(nVds.size):
                noise['Vd{}'.format(i)] = np.ones((len(nVgs),nFpsd.size))*np.NaN
                gm['Vd{}'.format(i)] = np.ones((len(nVgs),nFgm.size))*np.NaN*np.complex(1)
    
            ACVals={'PSD':noise,
                    'gm':gm,
                    'Vgs':nVgs,
                    'Vds':nVds,
                    'Fpsd':nFpsd,
                    'Fgm':nFgm,
                    'ChName':Ch,
                    'Name':Ch,
                    'DateTime':Time}
            DevACVals[Ch]=ACVals
    
        return DevACVals
    
    def SaveDCDict(self, Ids, Dev, SwVgsInd, SwVdsInd):
        '''Function that Saves Ids Data in the Dc Dict in the appropiate form
           for database
           Ids: array. Contains all the data to be saved in the DC dictionary
           SwVgsInd: int. Is the index of the actual Vg Sweep Iteration
           SwVdsInd: int. Is the Index of the actual Vd Sweep iteration
        '''
        for chn, inds in self.ChannelIndex.items():
            self.DevDCVals[chn]['Ids'][SwVgsInd,
                                       SwVdsInd] = Ids[inds]
            self.DevDCVals[chn]['Dev'][SwVgsInd,
                                       SwVdsInd] = Dev[inds]
        self.DCSaved.emit()

        # print('DCSaved')

    def SaveACDict(self, psd, ff, SwVgsInd, SwVdsInd):
        '''Function that Saves PSD Data in the AC Dict in the appropiate form
           for database
           psd: array(matrix). Contains all the PSD data to be saved in the AC
                               dictionary
           ff: array. Contains the Frequencies of the PSD to be saved in the AC
                      dictionary
           SwVgsInd: int. Is the index of the actual Vg Sweep Iteration
           SwVdsInd: int. Is the Index of the actual Vd Sweep iteration
        '''
        for chn, inds in self.ChannelIndex.items():
            self.DevACVals[chn]['PSD']['Vd{}'.format(SwVdsInd)][
                    SwVgsInd] = psd[:, inds].flatten()
            self.DevACVals[chn]['Fpsd'] = ff
       
        self.PSDSaved.emit()

    def SaveDicts(self, Dcdict, Folder, Oblea, Disp, Name, Cycle, Acdict=None):
        '''Creates the appropiate Folder NAme to be upload to the database
           Dcdict: dictionary. Dictionary with DC characterization that has
                               the structure to be read and save correctly
                               in the database
                               {'Ch04Col1': {'Ids': array([[1.94019351e-02],
                                                           [5.66072141e-08],
                                                           [5.66067698e-08],
                                                           [5.65991858e-08]
                                                           ]),
                                             'Vds': array([0.1]),
                                             'Vgs': array([ 0. , -0.1,
                                                           -0.2, -0.3]),
                                             'ChName': 'Ch04Col1',
                                             'Name': 'Ch04Col1',
                                             'DateTime': datetime.datetime
                                                         (2019, 12, 19, 16, 20,
                                                         59, 52661)
                                             },
  
           Acdict: dictionary. Dictionary with AC characterization that has the
                               structure to be read and save correctly in the
                               database
                               {'Ch04Col1': {'PSD': {'Vd0': array([
                                                            [4.67586928e-26,
                                                            1.61193712e-25],
                                                            ...
                                                            [5.64154950e-26,
                                                            2.10064857e-25]
                                                                   ])
                                                    },
                                             'gm': {'Vd0': array([],
                                                                 shape=(4, 0),
                                                                 dtype=complex128
                                                                 )
                                                    },
                                             'Vgs': array([ 0. , -0.1,
                                                           -0.2, -0.3]),
                                             'Vds': array([0.1]),
                                             'Fpsd': array([   0., 19.53125,
                                                            ...  2500.]),
                                             'Fgm': array([], dtype=float64),
                                             'ChName': 'Ch04Col1',
                                             'Name': 'Ch04Col1',
                                             'DateTime': datetime.datetime
                                                         (2019, 12, 19, 16, 20,
                                                         59, 52661)
                                             },
                               
                            }
           Folder, Oblea, Disp, Name, Cycle: str.
        '''
        self.FileName = '{}/{}-{}-{}-Cy{}.h5'.format(Folder,
                                                     Oblea,
                                                     Disp,
                                                     Name,
                                                     Cycle)
#        print(self.FileName)
        with open(self.FileName, "wb") as f:
            pickle.dump(Dcdict, f)
            if Acdict is not None:
                pickle.dump(Acdict, f)
        print('Saved')