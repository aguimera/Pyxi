#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 12:25:45 2019

@author: aguimera
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

import numpy as np
import niscope
import nifgen
import copy
import time
import re

CarriersConfigPars={'name': 'CarriersConfig',
                    'type': 'group',
                    'children': ()}

CarrierPars = {'name':'ColX',
               'type': 'group',
               'children': ({'name': 'Frequency',
                             'value': 100e3,
                             'type': 'float',
                             'siPrefix': True,
                             'suffix': 'Hz'},
                            {'name': 'Amplitude',
                             'value': 0.25,
                             'type': 'float',
                             'siPrefix': True,
                             'suffix': 'V'},
                            {'name': 'Gain',
                             'value': 1,
                             'type': 'float',
                             'readonly': True,
                             'siPrefix': True,
                             'suffix': 'Vpk-pk'}
                            )
               }

NifGenSamplingPars =  {'name': 'SamplingConfig',
                       'type': 'group',
                       'children':({'name': 'FsGen',
                                    'title': 'Sampling Rate',
                                    'type': 'float',
                                    'value': 20e6,
                                    'readonly': True,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'GS',
                                    'title': 'Generation Size',
                                    'type': 'int',
                                    'value': int(2e3),
                                    'limits': (int(0), int(5e6)),
                                    'step': 100,
                                    'siPrefix': True,
                                    'suffix': 'Samples'},
                                   {'name': 'Offset',
                                    'value': 0.0,
                                    'type': 'float',
                                    'siPrefix': True,
                                    'suffix': 'V'})
                 }
                 
NifGenColumnsPars = {'name': 'ColumnsConfig',
                      'type': 'group',
                      'children':({'name':'Col1',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True,},
                                                {'name':'Resource',
                                                'type': 'str',
                                                'readonly': True,
                                                'value': 'PXI1Slot2'},
                                               {'name':'Index',
                                                'type': 'int',
                                                'readonly': True,
                                                'value': 0})},
                                   {'name':'Col2',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True,},
                                                {'name':'Resource',
                                                'type': 'str',
                                                'readonly': True,
                                                'value': 'PXI1Slot2'},
                                               {'name':'Index',
                                                'type': 'int',
                                                'readonly': True,
                                                'value': 1})},
                                   {'name':'Col3',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True,},
                                                {'name':'Resource',
                                                'type': 'str',
                                                'readonly': True,
                                                'value': 'PXI1Slot3'},
                                               {'name':'Index',
                                                'type': 'int',
                                                'readonly': True,
                                                'value': 0})},
                                 {'name':'Col4',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True,},
                                                {'name':'Resource',
                                                'type': 'str',
                                                'readonly': True,
                                                'value': 'PXI1Slot3'},
                                               {'name':'Index',
                                                'type': 'int',
                                                'readonly': True,
                                                'value': 1})},                                                

                                            ) 
                               }

  
##############################Generator##########################################
class NifGeneratorParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChild(NifGenColumnsPars)
        self.ColConfig = self.param('ColumnsConfig')
        self.addChild(NifGenSamplingPars)
        self.SamplingConfig = self.param('SamplingConfig')
        self.FsGen = self.SamplingConfig.param('FsGen')
        self.GS = self.SamplingConfig.param('GS')
        
        self.addChild(CarriersConfigPars)
        self.CarrierConfig = self.param('CarriersConfig')
        
        self.ColConfig.sigTreeStateChanged.connect(self.on_ColConf_Changed)
        self.on_ColConf_Changed()
        
        self.CarrierConfig.sigTreeStateChanged.connect(self.on_Fsig_Changed)
        self.on_Fs_Changed()
        self.GS.sigValueChanged.connect(self.on_Fs_Changed)
        
        
    def on_ColConf_Changed(self):
        Cols = []
        for p in self.ColConfig.children():
            if p.param('Enable').value():
                Cols.append(p.name())
        
        self.CarrierConfig.clearChildren()
        for col in Cols:
            cc = copy.deepcopy(CarrierPars)
            cc['name'] = col
            cc['children'][2]['value'] = 2*cc['children'][1]['value']
            self.CarrierConfig.addChild(cc)

    def on_Fsig_Changed(self):
        for p in self.CarrierConfig.children():
            if p.param('Frequency').sigValueChanged:
                self.on_Fs_Changed()
                
    def on_Fs_Changed(self):
        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
        Fmin = np.min(self.Freqs)
        
        Samps = self.GS.value()
        Fs = Samps*Fmin/10
        self.FsGen.setValue(Fs)
        Samps = round(Fs/Fmin)*10
        self.GS.setValue(Samps)
        for p in self.CarrierConfig.children():
            Fc = p.param('Frequency').value()
            nc = round((Samps*Fc)/Fs)
            Fnew =  (nc*Fs)/Samps
            p.param('Frequency').setValue(Fnew)
            Gain = 2*p.param('Amplitude').value()
            p.param('Gain').setValue(Gain)
        
    def GetParams(self):
        self.Generator = {'ColumnsConfig':{},
                     }
        for Config in self.CarrierConfig.children():
            self.Generator['ColumnsConfig'][Config.name()] = {}
            for Values in Config.children():
                self.Generator['ColumnsConfig'][Config.name()][Values.name()] = Values.value()
        
        for Config in self.SamplingConfig.children():
            self.Generator[Config.name()] = Config.value()
        
        for Config in self.ColConfig.children():
            for Values in Config.children():
                if Values.name() == 'Enable':
                    if Values.value() == False:
                        break
                    continue
                self.Generator['ColumnsConfig'][Config.name()][Values.name()] = Values.value()
            
        return self.Generator   
        
    def GetCarriers(self):
        Carriers = {}
        for p in self.CarrierConfig.children():
            Carriers[p.name()] = p.param('Frequency').value()

        return Carriers
 
class SigGen(nifgen.Session):    
    def SetArbSignal(self, Signal, index, gain, offset):
        Handle = self.create_waveform(Signal)
#        if index != 0: #only needed if the CM is applied through VG0 to all the channels connected
#            offset = 0  #if not done, the other channels will have 2*CM as offset

        self.channels[index].configure_arb_waveform(Handle,
                                                    gain=gain,
                                                    offset=offset)
        
OptionsGen = 'Simulate=0,DriverSetup=Model:5413;Channels:0-1;BoardType:PXIe;MemorySize:268435456'

class Columns():
    Columns = {} # {'Col1': {'session': sessionnifgen, 
#                             'index': int}}
    Resources = {} # 'PXI1Slot2': sessionnifgen
    def __init__(self, ColumnsConfig, Fs, GenSize):
        self.Fs = Fs
        self.GenSize= GenSize
        
# Init resources and store sessions
        Res = [conf['Resource'] for col, conf in ColumnsConfig.items()]                
        for res in set(Res):
            SesGen = SigGen(resource_name=res, options=OptionsGen)
            SesGen.output_mode = nifgen.OutputMode.ARB
            SesGen.reference_clock_source = nifgen.ReferenceClockSource.PXI_CLOCK
            SesGen.ref_clock_frequency=100e6
            SesGen.clock_mode=nifgen.ClockMode.HIGH_RESOLUTION
            SesGen.arb_sample_rate=Fs/2
            SesGen.start_trigger_type = nifgen.StartTriggerType.DIGITAL_EDGE
            SesGen.digital_edge_start_trigger_source = 'PXI_Trig0'
            self.Resources[res] = SesGen

# Init columns indexing dictionaries
        for col, conf in ColumnsConfig.items():
            self.Columns[col] = {'session': self.Resources[conf['Resource']],
                                 'index':conf['Index']
                                 }
    def Initiate(self):
        for res, ses in self.Resources.items():
            ses.initiate()
            
    def Abort(self):
        for res, ses in self.Resources.items():
            ses.abort()
            
    def SetSignal(self, SigsPars, Offset):
        
        self.Ts = 1/self.Fs
        t = np.arange(0, self.Ts*self.GenSize, self.Ts)
     
        for Col,pars in SigsPars.items():
            if Col == 'Offset':
                continue
#            print(pars['Amplitude'])
#            signal = pars['Amplitude']*np.sin(2*np.pi*pars['Frequency']*t)
            signal = np.sin(2*np.pi*pars['Frequency']*t)
            if Col != 'Col1':
                Offset = 0
            self.Columns[Col]['session'].SetArbSignal(index=self.Columns[Col]['index'],
                                                       Signal=signal, gain=pars['Amplitude'], 
                                                       offset=Offset)
            
##############################SCOPE##########################################


NiScopeFetchingPars =  {'name': 'FetchConfig',
                       'type': 'group',
                       'children':({'name': 'FsScope',
                                    'title': 'Sampling Rate',
                                    'type': 'float',
                                    'value': 2e6,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'BS',
                                    'title': 'Buffer Size',
                                    'type': 'int',
                                    'value': int(20e3),
                                    'readonly': True,
                                    'siPrefix': True,
                                    'suffix': 'Samples'},
                                   {'name': 'tFetch',
                                    'title': 'Fetching Time',
                                    'type': 'float',
                                    'value': 0.5,
                                    'siPrefix': True,
                                    'suffix': 's'},
                                   {'name': 'NRow',
                                    'title': 'Number of Channels',
                                    'type': 'int',
                                    'value': 0,
                                    'readonly': True,
                                    'siPrefix': True,
                                    'suffix': 'Chan'},
                                   {'name': 'OffsetRows',
                                    'value': 0,
                                    'type': 'int',
                                    'siPrefix': True,
                                    'suffix': 'Samples'},
                                   {'name': 'GainBoard',
                                    'titel': 'System Gain',
                                    'value': (10e3),
                                    'type': 'int',
                                    'siPrefix': True,
                                    'suffix': 'Ohms'},
                                   {'name':'Resource',
                                    'type': 'str',
                                    'readonly': True,
                                    'value': 'PXI1Slot4'},)
                 }
NiScopeRowsPars = {'name': 'RowsConfig',
                   'type': 'group',
                   'children':({'name':'Row1',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 0},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},
                               {'name':'Row2',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 1},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},
                               {'name':'Row3',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 2},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},
                               {'name':'Row4',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 3},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},
                               {'name':'Row5',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 4},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},
                               {'name':'Row6',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 5},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},
                               {'name':'Row7',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 6},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},  
                               {'name':'Row8',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 7},
                                            {'name': 'Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},                                              
                               ) 
                        }           

class NiScopeParameters(pTypes.GroupParameter):
        
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        
        self.addChild(NiScopeRowsPars)
        
        self.RowsConfig = self.param('RowsConfig')
        
        self.addChild(NiScopeFetchingPars)
        self.FetchConfig = self.param('FetchConfig')
        self.FsScope = self.FetchConfig.param('FsScope')
        self.BS = self.FetchConfig.param('BS')
        self.NRows = self.FetchConfig.param('NRow')
        self.OffsetRows = self.FetchConfig.param('OffsetRows')
        self.tFetch = self.FetchConfig.param('tFetch')
        self.on_BS_Changed()
        
        self.RowsConfig.sigTreeStateChanged.connect(self.on_RowConf_Changed)
        self.on_RowConf_Changed()
        self.FsScope.sigValueChanged.connect(self.on_Fs_Changed)
        self.tFetch.sigValueChanged.connect(self.on_BS_Changed)

    def on_RowConf_Changed(self):
        self.Rows = []
        for p in self.RowsConfig.children():
            if p.param('Enable').value():
                self.Rows.append(p.name())
        self.NRows.setValue(len(self.Rows))
       
    def on_Fs_Changed(self):
        self.on_BS_Changed()
        
    def on_BS_Changed(self):
        Fs = self.FsScope.value()
        tF = self.tFetch.value()
        Samples = round(tF*Fs)
        tF = Samples/Fs
        self.tFetch.setValue(tF)
        self.BS.setValue(Samples)
        
    def GetChannels(self):
        RowNames = {}
        for i,r in enumerate(self.Rows):
            RowNames[r]=i
        return RowNames

    def GetParams(self):
        Scope = {'RowsConfig':{},
               }
        for Config in self.RowsConfig.children():
            if Config.param('Enable').value() == True:
                Scope['RowsConfig'][Config.name()]={}
                for Values in Config.children():
                    if Values == 'Enable':
                        continue
                    Scope['RowsConfig'][Config.name()][Values.name()] = Values.value()
        for Config in self.FetchConfig.children():
#            if Config.name() =='Fs':
#                continue
            if Config.name() =='tFetch':
                continue
            Scope[Config.name()] = Config.value()

        return Scope
            

OptionsScope = {'simulate': False,
                'driver_setup': {'Model': 'NI PXIe-5105',
                                 'BoardType': 'PXIe',
                                 },
                }
class Rows():
#Init Scope Channels
    Rows = {} #{'Row1': Range, Index}
    def __init__(self, RowsConfig, Fs, Resource):
        self.SesScope = SigScope(resource_name=Resource, options=OptionsScope)
        self.SesScope.acquisition_type=niscope.AcquisitionType.NORMAL
        self.SesScope.configure_horizontal_timing(min_sample_rate=Fs,
                                                  min_num_pts=int(1e3),
                                                  ref_position=50.0,
                                                  num_records=1,
                                                  enforce_realtime=True)
        self.SesScope.exported_start_trigger_output_terminal = 'PXI_Trig0'
        self.SesScope.input_clock_source='PXI_Clk'
        self.SesScope.configure_trigger_software()
        self.SesScope.GetSignal(RowsConfig)
#Init Acquisition
    def Initiate(self):
        self.SesScope.initiate()

    def Abort(self):
        self.SesScope.abort()
# Init Session of Scope        
class SigScope(niscope.Session):
    def GetSignal(self, RowsConfig):#RowsConfig = {'Row1': Range, Index}
        for Rows, params in RowsConfig.items():
            self.channels[params['Index']].configure_vertical(range=params['Range'], coupling=niscope.VerticalCoupling.AC)
            self.channels[params['Index']].configure_chan_characteristics(1000000, 600000.0) #input impedance, max_input:freq        

###############################################################################

class DataAcquisitionThread(Qt.QThread):
    NewData = Qt.pyqtSignal()

    def __init__(self, ColumnsConfig, FsGen, GS, Offset, RowsConfig, FsScope, BS, NRow, OffsetRows, GainBoard, Resource):
        print ('TMacqThread, DataAcqThread')
        super(DataAcquisitionThread, self).__init__()
        
        print(ColumnsConfig)
        print(RowsConfig)
        self.Columns = Columns(ColumnsConfig, FsGen, GS)
        self.Rows = Rows(RowsConfig, FsScope, Resource)
        self.BS = BS
        self.offset = OffsetRows
        self.GainBoard = (GainBoard/2e3)
        self.LSB = np.array([])
        self.RowsList = []
        self.Channels = []
        
        self.ttimer = ((self.BS/FsScope)-0.05)*1000
        
        for Row, pars in RowsConfig.items():
            self.RowsList.append(str(Row))
            self.LSB = np.append(self.LSB, RowsConfig[str(Row)]['Range']/(2**16))
            
        for s in self.RowsList:
            self.Channels.append(int(re.split(r'(\d+)', s)[1])-1)
        Sig = {}
        for col, pars in ColumnsConfig.items():
            PropSig = {}
            for p, val in pars.items():
                if p == 'Resource' or p == 'Index':
                    continue
                PropSig[str(p)] = val
                
            Sig[str(col)]= PropSig

        self.Columns.SetSignal(Sig, Offset)
        self.Timer = Qt.QTimer()
        self.Timer.moveToThread(self)
        
    def run(self, *args, **kwargs):

        print('start ')      
        self.OutData = np.ndarray((self.BS, len(self.Channels)))
        self.BinData = np.ndarray((self.BS, len(self.Channels)))
        self.IntData = np.ndarray((self.BS, len(self.Channels)))
        self.initSessions()
#        self.Timer.singleShot(self.ttimer, self.GenData)
        loop = Qt.QEventLoop()
        loop.exec_()
    
    def GenData(self):
        if not self.isRunning():
            return
        
        try:
#            T1 = time.time()

            Inputs = self.Rows.SesScope.channels[self.Channels].fetch(num_samples=self.BS,
                                                          relative_to=niscope.FetchRelativeTo.READ_POINTER,
                                                          offset=self.offset,
                                                          record_number=0,
                                                          num_records=1,
                                                          timeout=2)
#            print('ftech', time.time()-T1)
            self.Timer.singleShot(self.ttimer, self.GenData)
            for i, In in enumerate(Inputs):
                self.OutData[:, i] = np.array(In.samples)#/self.GainBoard 
                self.BinData[:,i] = self.OutData[:,i]/self.LSB[i]
                self.IntData[:,i] = np.int16(np.round(self.BinData[:,i]))
            self.NewData.emit()


        except Exception:
            print(Exception.args)
            print('Requested data has been overwritten in memory')
            self.stopSessions()
            print('Gen and Scope Sessions Restarted')
            self.initSessions()        
                 
    def initSessions(self):
        self.Columns.Initiate()
        self.Rows.Initiate()
        self.Timer.singleShot(self.ttimer, self.GenData)
        
    def stopSessions(self):
        self.Columns.Abort()
        self.Rows.Abort()
        
    def stopTimer(self):
        self.Timer.stop()
        self.Timer.killTimer(self.Id)
        
class Acquisition():    
    def __init__(self, ColumnsConfig, FsGen, GS, RowsConfig, NRow, FsScope, ResourceScope):
        self.Columns = Columns(ColumnsConfig, FsGen, GS)
        self.Rows = Rows(RowsConfig, FsScope, ResourceScope)
        self.LSB = np.array([])
        for i in range(NRow):
            self.LSB = np.append(self.LSB, RowsConfig['Row'+str(i+1)]['Range']/(2**16))
        
    def setSignals(self, ColumnsConfig, Vgs):
        Sig = {}
        for col, pars in ColumnsConfig.items():
            PropSig = {}
            for p, val in pars.items():
                if p == 'Resource' or p == 'Index':
                    continue
                PropSig[str(p)] = val
                
            Sig[str(col)]= PropSig    
            
        self.Columns.SetSignal(Sig, Vgs)
        
    def GetData(self, FetchSize, channels, ScopeOffset):
        Inputs = self.Rows.SesScope.channels[channels].fetch(num_samples=FetchSize,
                                                              relative_to=niscope.FetchRelativeTo.READ_POINTER,
                                                              offset=ScopeOffset,
                                                              record_number=0,
                                                              num_records=1,
                                                              timeout=20)
        OutData = np.ndarray((FetchSize, len(channels))) 
        BinData = np.ndarray((FetchSize, len(channels)))
        IntData = np.ndarray((FetchSize, len(channels)))
        for i, In in enumerate(Inputs):
            OutData[:, i] = np.array(In.samples)#/self.GainBoard 
            BinData[:,i] = OutData[:,i]/self.LSB[i]
            IntData[:,i] = np.int16(np.round(BinData[:,i]))
            
        return IntData
        
        
    def initSessions(self):
        self.Columns.Initiate()
        self.Rows.Initiate()
        
    def stopSessions(self):
        self.Columns.Abort()
        self.Rows.Abort()  