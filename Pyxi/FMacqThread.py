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
                             'value': 1,
                             'type': 'float',
                             'siPrefix': True,
                             'suffix': 'V'},
                            {'name': 'Gain',
                             'value': 1,
                             'type': 'float',}
                            )
               }

NifGenSamplingPars =  {'name': 'SamplingConfig',
                       'type': 'group',
                       'children':({'name': 'Fs',
                                    'title': 'Sampling Rate',
                                    'type': 'float',
                                    'value': 2e6,
                                    'step': 100,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'GS',
                                    'title': 'Generation Size',
                                    'type': 'int',
                                    'value': int(5e3),
                                    'limits': (int(0), int(2e6)),
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
        self.Fs = self.SamplingConfig.param('Fs')
        self.GS = self.SamplingConfig.param('GS')
        
        self.addChild(CarriersConfigPars)
        self.CarrierConfig = self.param('CarriersConfig')
        self.ColConfig.sigTreeStateChanged.connect(self.on_ColConf_Changed)
        self.on_ColConf_Changed()
        self.CarrierConfig.sigTreeStateChanged.connect(self.on_Fsig_Changed)
    
        self.Fs.sigValueChanged.connect(self.on_Fs_Changed)
        self.GS.sigValueChanged.connect(self.on_GS_Changed)
#
    def on_ColConf_Changed(self):
        Cols = []
        for p in self.ColConfig.children():
            if p.param('Enable').value():
                Cols.append(p.name())
        
        self.CarrierConfig.clearChildren()
        for col in Cols:
            cc = copy.deepcopy(CarrierPars)
            cc['name'] = col
            self.CarrierConfig.addChild(cc)

    def on_Fsig_Changed(self):
        Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
        Fmin = np.min(Freqs)
        
        Fs = self.Fs.value()
        Samps = round(Fs/Fmin)
        self.GS.setValue(Samps)
        for p in self.CarrierConfig.children():
            Fc = p.param('Frequency').value()
            nc = round((Samps*Fc)/Fs)
            Fnew =  (nc*Fs)/Samps
            p.param('Frequency').setValue(Fnew)
        
    def on_Fs_Changed(self):
        Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
        Fmin = np.min(Freqs)
        
        Fs = self.Fs.value()
        Samps = round(Fs/Fmin)
        Fs = Samps*Fmin
        self.Fs.setValue(Fs)
        self.on_Fsig_Changed()
        
    def on_GS_Changed(self):
        Samps = self.GS.value()
        Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
        Fmin = np.min(Freqs)
        
        Fs = Samps*Fmin
        self.Fs.setValue(Fs)
        self.on_Fsig_Changed()
        
    def GetParams(self):
        Generator = {'ColumnsConfig':{},
                     }
        for Config in self.CarrierConfig.children():
            Generator['ColumnsConfig'][Config.name()] = {}
            for Values in Config.children():
                Generator['ColumnsConfig'][Config.name()][Values.name()] = Values.value()
        
        for Config in self.SamplingConfig.children():
            Generator[Config.name()] = Config.value()
        
        for Config in self.ColConfig.children():
            for Values in Config.children():
                if Values.name() == 'Enable':
                    continue
                Generator['ColumnsConfig'][Config.name()][Values.name()] = Values.value()
            
        return Generator
 
class SigGen(nifgen.Session):    
    def SetArbSignal(self, Signal, index, gain, offset):
        Handle = self.create_waveform(Signal)
        if index != 0: #only needed if the CM is applied through VG0 to all the channels connected
            offset = 0  #if not done, the other channels will have 2*CM as offset
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
        for re in set(Res):
            SesGen = SigGen(resource_name=re, options=OptionsGen)
            SesGen.output_mode = nifgen.OutputMode.ARB
            SesGen.reference_clock_source = nifgen.ReferenceClockSource.PXI_CLOCK
            SesGen.ref_clock_frequency=100e6
            SesGen.clock_mode=nifgen.ClockMode.HIGH_RESOLUTION
            SesGen.arb_sample_rate=Fs/2
            SesGen.start_trigger_type = nifgen.StartTriggerType.DIGITAL_EDGE
            SesGen.digital_edge_start_trigger_source = 'PXI_Trig0'
            self.Resources[re] = SesGen

# Init columns indexing dictionaries
        for col, conf in ColumnsConfig.items():
            self.Columns[col] = {'session': self.Resources[conf['Resource']],
                                 'index':conf['Index']
                                 }
    def Initiate(self):
        for res, ses in self.Resources.item():
            ses.initiate()

    def SetSignal(self, SigsPars, Offset):
        
        self.Ts = 1/self.Fs
        t = np.arange(0, self.Ts*self.GenSize, self.Ts)
     
        for Col,pars in SigsPars.items():
            if Col == 'Offset':
                continue
    
            signal = pars['Amplitude']*np.sin(2*np.pi*pars['Frequency']*t)
            self.Columns[Col]['session'].SetArbSignal(index=self.Columns[Col]['index'],
                                                       Signal=signal, gain=pars['Gain'], 
                                                       offset=Offset)
##############################SCOPE##########################################


NiScopeFetchingPars =  {'name': 'FetchConfig',
                       'type': 'group',
                       'children':({'name': 'Fs',
                                    'title': 'Sampling Rate',
                                    'type': 'float',
                                    'value': 2e6,
                                    'readonly': True,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'NRow',
                                    'title': 'Number of Channels',
                                    'type': 'int',
                                    'value': 0,
                                    'readonly': True,
                                    'siPrefix': True,
                                    'suffix': 'Chan'},
                                   {'name': 'BS',
                                    'title': 'Buffer Size',
                                    'type': 'int',
                                    'value': int(20e3),
                                    'limits': (int(0), int(2e6)),
                                    'step': 100,
                                    'siPrefix': True,
                                    'suffix': 'Samples'},
                                   {'name': 'OffsetRows',
                                    'value': 0,
                                    'type': 'int',
                                    'siPrefix': True,
                                    'suffix': 'Samples'},
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
                                             'values': {"0.05": 0.05, 
                                                        "0.2": 0.2, 
                                                        "1": 1, 
                                                        "6": 6},
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
                                             'values': {"0.05": 0.05, 
                                                        "0.2": 0.2, 
                                                        "1": 1, 
                                                        "6": 6},
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
                                             'values': {"0.05": 0.05, 
                                                        "0.2": 0.2, 
                                                        "1": 1, 
                                                        "6": 6},
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
                                             'values': {"0.05": 0.05, 
                                                        "0.2": 0.2, 
                                                        "1": 1, 
                                                        "6": 6},
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
        self.Fs = self.FetchConfig.param('Fs')
        self.BS = self.FetchConfig.param('BS')
        self.NRows = self.FetchConfig.param('NRow')
        self.OffsetRows = self.FetchConfig.param('OffsetRows')
#        NifGenPars = NifGeneratorParameters()
#        self.Fs.setValue(NifGeneratorParameters.Fs.value())
        

        self.RowsConfig.sigTreeStateChanged.connect(self.on_RowConf_Changed)
        self.on_RowConf_Changed()
#        
#
    def on_RowConf_Changed(self):
        Rows = []
        for p in self.RowsConfig.children():
            if p.param('Enable').value():
                Rows.append(p.name())
#                p.param('Range').show()
#                print(p.param('Range').setVisible(True))
#                p.param('Range').setWritable()
#            else:
#               p.param('Range').setReadonly()
        self.NRows.setValue(len(Rows))
            
    def on_Fs_Changed(self):
        Fs = self.Fs.value()
        Samps = self.BS.value()
        n = round(Samps*Fs) # Fs/Ts
        Fs = n/Samps
        self.Fs.setValue(Fs)
        
    def on_BS_Changed(self):
        Fs = self.Fs.value()
        Samps = self.BS.value()
        n = round(Samps*Fs) # Fs/Ts
        Samps = n/Fs
        self.BS.setValue(Samps)
    
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
            if Config.name() =='Fs':
                continue
            Scope[Config.name()] = Config.value()

        return Scope
#     
#PXIScope = 'PXI1Slot4'
OptionsScope = {'simulate': False,
                'driver_setup': {'Model': 'NI PXIe-5105',
                                 'BoardType': 'PXIe',
                                 },
                }
class Rows():
    Rows = {} #{'Row1': Range, Index}

    #rowsconfig tiene que tener
    def __init__(self, RowsConfig, Fs, Resource):
        
        self.SesScope = SigScope(Resource, OptionsScope)
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

    def Initiate(self):
        self.SesScope.initiate()
        
class SigScope(niscope.Session):
    def GetSignal(self, RowsConfig):#RowsConfig = {'Row1': Range, Index}
        for Rows, params in RowsConfig.items():
            self.channels[params['Index']].configure_vertical(range=params['Range'], coupling=niscope.VerticalCoupling.AC)
            self.channels[params['Index']].configure_chan_characteristics(1000000, 600000.0) #input impedance, max_input:freq        

###############################################################################

class DataAcquisitionThread(Qt.QThread):
    NewData = Qt.pyqtSignal()

    def __init__(self, ColumnsConfig, Fs, GS, Offset, RowsConfig, BS, NRow, OffsetRows, Resource):
        print ('TMacqThread, DataAcqThread')
        super(DataAcquisitionThread, self).__init__()
        
        print(ColumnsConfig)
        print(RowsConfig)
        self.Columns = Columns(ColumnsConfig, Fs, GS)
        self.Rows = Rows(RowsConfig, Fs, Resource)
        self.BS = BS
        self.channels = list(range(NRow))
        self.offset = OffsetRows
        Sig = {}
        for col, pars in ColumnsConfig.items():
            PropSig = {}
            for p, val in pars.items():
                if p == 'Resource' or p == 'Index':
                    continue
                PropSig[str(p)] = val
                
            Sig[str(col)]= PropSig
        
        self.Columns.SetSignal(Sig, Offset)

    def run(self, *args, **kwargs):
        print('start ')
        self.Columns.Initiate()
        self.Rows.Initiate()
        while True:
            Inputs = self.NiScope.channels[self.channels].fetch(num_samples=self.BS,
                                                          relative_to=niscope.FetchRelativeTo.READ_POINTER,
                                                          offset=self.offset,
                                                          record_number=0,
                                                          num_records=1,
                                                          timeout=2)
            value = np.ndarray((self.BS, len(self.channels)))
            for i, In in enumerate(Inputs):
                InSig = np.array(In.samples)
            value[:, i] = InSig #to do a BufferSize x nChan Matrix
            self.NewData.emit()

