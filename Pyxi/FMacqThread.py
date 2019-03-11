#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 12:25:45 2019

@author: aguimera
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
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
                                   {'name': 'BS',
                                    'title': 'Buffer Size',
                                    'type': 'int',
                                    'value': int(5e3),
                                    'limits': (int(1e3), int(2e6)),
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
#NifGen_params = ({'name': 'ColumnsConfig',
#                  'type': 'group',
#                  'children':({'name': 'Fs',
#                                       'title': 'Sampling Rate',
#                                       'type': 'float',
#                                       'value': 2e6,
#                                       'step': 100,
#                                       'siPrefix': True,
#                                       'suffix': 'Hz'},
#                                      {'name': 'BS',
#                                       'title': 'Buffer Size',
#                                       'type': 'int',
#                                       'value': int(5e3),
#                                       'limits': (int(1e3), int(2e6)),
#                                       'step': 100,
#                                       'siPrefix': True,
#                                       'suffix': 'Samples'},
#                                      {'name': 'Offset',
#                                       'value': 0.0,
#                                       'type': 'float',
#                                       'siPrefix': True,
#                                       'suffix': 'V'})
#                 },
#                {'name': 'Channels',
#                         'type': 'group',
#                         'children': ({'name': 'Chn0',
#                                       'type': 'bool',
#                                       'value': True},
#                                      {'name': 'In0',
#                                       'type': 'group',
#                                       'children': CarrierPars},
#                                      {'name': 'Chn1',
#                                       'type': 'bool',
#                                       'value': True},
#                                      {'name': 'In1',
#                                       'type': 'group',
#                                       'children': CarrierPars},
#                                      {'name': 'Chn2',
#                                       'type': 'bool',
#                                       'value': True},
#                                      {'name': 'In2',
#                                       'type': 'group',
#                                       'children': CarrierPars},
#                                      {'name': 'Chn3',
#                                       'type': 'bool',
#                                       'value': True},
#                                      {'name': 'In3',
#                                       'type': 'group',
#                                       'children': CarrierPars}
#                                     )
#                 },
#                {'name': 'Info.',
#                 'type': 'group',
#                 'children': ({'name': 'Model',
#                               'type': 'str',
#                               'value': '5413'},
#                              {'name': 'Resource Name 0',
#                               'type': 'str',
#                               'value': 'PXI1Slot2'},
#                              {'name': 'Resource Name 1',
#                               'type': 'str',
#                               'value': 'PXI1Slot3'},
#                              )
#                }
#               )

class NifGeneratorParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChild(NifGenColumnsPars)
        self.ColConfig = self.param('ColumnsConfig')
        self.addChild(NifGenSamplingPars)
        self.SamplingConfig = self.param('SamplingConfig')
        
        self.addChild(CarriersConfigPars)
        self.CarrierConfig = self.param('CarriersConfig')

        self.ColConfig.sigTreeStateChanged.connect(self.on_ColConf_Changed)
        self.CarrierConfig.sigTreeStateChanged.connect(self.on_Fsig_Changed)
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
        conf = self.GetParams()
        Freqs = np.array([])
        print(conf)
        for Cols, params in conf.items():
            if Cols is 'Fs' or Cols is 'BS' or Cols is 'Offset':
                continue
            for pars, val in params.items():
                if pars != 'Frequency':
                        continue
                Freqs = np.append(Freqs, val)
        Fmin = np.min(Freqs)
        Fs = conf['Fs']
        Samps = int(Fs/Fmin)
        print(Samps)
    
    def GetParams(self):
        Generator = {}
        for Config in self.CarrierConfig.children():
            Generator[Config.name()] = {}
            for Values in Config.children():
                Generator[Config.name()][Values.name()] = Values.value()
        
        for Config in self.SamplingConfig.children():
            Generator[Config.name()] = Config.value()
        
        for Config in self.ColConfig.children():
            for Values in Config.children():
                if Values.name() == 'Enable':
                    continue
                Generator[Config.name()][Values.name()] = Values.value()
            
        return Generator
            
#    def GetParams(self):
#        
#        Generator = {}
#        for var in self.param('Config_Var').children():
#             Generator[var.name()] = var.value()
#
#        for child in self.param('Channels').children():
#             Config = {}
#             if child.name() is 'Chn0' or 'Chn1' or 'Chn2' or 'Chn3':
#                  continue
#             for conf in child.children:
#                  Config[conf.name()] = conf.value()
#             Generator[child.name()] = Config
#
#        return Generator
   
class SigGen(nifgen.Session):    
    def SetArbSignal(self, Signal, index, gain, offset):
        Handle = self.create_waveform(Signal)
        self.channels[index].configure_arb_waveform(Handle,
                                                    gain=gain,
                                                    offset=offset)
        self.initiate() #To check

#        
#PXIGen1 = 'PXI1Slot2'
#PXIGen2 = 'PXI1Slot3'
#OptionsGen = 'Simulate=0,DriverSetup=Model:5413;Channels:0-1;BoardType:PXIe;MemorySize:268435456'

#ColumnsConfig={'Col1': {'resource_name': 'PXI1Slot2',
#                        'index': 0},
#               'Col2': {'resource_name': 'PXI1Slot2',
#                        'index': 1},
#               'Col3': {'resource_name': 'PXI1Slot3',
#                        'index': 0},
#               'Col4': {'resource_name': 'PXI1Slot3',
#                        'index': 1},
#                }


class Columns():
    Columns = {} # {'Col1': {'session': sessionnifgen, 
#                             'index': int}}
    Resoures = {} # 'PXI1Slot2': sessionnifgen
    def __init_(self, ColumnsConfig, Fs, BufferSize):
        self.Fs = Fs
        self.BufferSize= BufferSize
        
# Init resources and store sessions
        Res = [conf['resource_name'] for col, conf in ColumnsConfig.items()]                
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
            self.Columns[col] = {'session': self.Resources[conf['resource_name']],
                                 'index':conf['index']
                                 }
#    
#    def SetSignal(self, Col='Col0', Freq, Amp, gain, offset):
#        Fr
##        Ts = 1/Fs
###        offset = 0
##        self.BS = int(BS)
##        t = np.arange(0, Ts*self.BS, Ts)
##        Fsig = np.array([1e3, 5e3, 10e3, 50e3])
#
#        
#        self.Columns[Col]['session'].SetArbbritary(index=self.Columns[Col]['index'],
#                                                    signal, gain, offset)
#          
         

        
class SigScope(niscope.Session):
    def GetSignal(self, Fs):
        self.acquisition_type=niscope.AcquisitionType.NORMAL
        self.channels[0,1,2,3,4,5,6,7].configure_vertical(range=1, coupling=niscope.VerticalCoupling.AC)
        self.channels[0,1,2,3,4,5,6,7].configure_chan_characteristics(1000000, 600000.0)
        self.configure_horizontal_timing(min_sample_rate=Fs,
                                         min_num_pts=int(1e3),
                                         ref_position=50.0,
                                         num_records=1,
                                         enforce_realtime=True)
        self.exported_start_trigger_output_terminal = 'PXI_Trig0'
        self.input_clock_source='PXI_Clk'
        self.configure_trigger_software()
        self.initiate()

###############################################################################


class DataAcquisitionThread(Qt.QThread):
    NewData = Qt.pyqtSignal()

    def __init__(self, Fs, BS, Offset, ch0='In0', ch1='In1', ch2='In2', ch3='In3'):
        print ('TMacqThread, DataAcqThread')
        super(DataAcquisitionThread, self).__init__()
        
        PXIGen1 = 'PXI1Slot2'
        PXIGen2 = 'PXI1Slot3'
        OptionsGen = 'Simulate=0,DriverSetup=Model:5413;Channels:0-1;BoardType:PXIe;MemorySize:268435456'
    
        PXIScope = 'PXI1Slot4'
        OptionsScope = {'simulate': False,
                        'driver_setup': {'Model': 'NI PXIe-5105',
                                     'BoardType': 'PXIe',
                                     },
                                     }
#        Fs = 2e6
        print(Fs)
        Ts = 1/Fs
#        offset = 0
        self.BS = int(BS)
        t = np.arange(0, Ts*self.BS, Ts)
        Fsig = np.array([1e3, 5e3, 10e3, 50e3])
        Sig0=Asig[0]*np.sin(2*np.pi*Fsig[0]*t)
        Sig1=Asig[1]*np.sin(2*np.pi*Fsig[1]*t)
        Sig2=Asig[2]*np.sin(2*np.pi*Fsig[2]*t)
        Sig3=Asig[3]*np.sin(2*np.pi*Fsig[3]*t)
        
        self.NifGen = SigGen(resource_name=PXIGen1, 
                             options=OptionsGen)
        self.NifGen2 = SigGen(resource_name=PXIGen2, 
                             options=OptionsGen)
        self.NiScope = SigScope(resource_name=PXIScope,
                                options=OptionsScope)
        self.NifGen.SetArbSignal(Sig0, Sig1, offset, Fs)
        self.NifGen2.SetArbSignal(Sig2, Sig3, offset, Fs)
        self.NiScope.GetSignal(Fs) 
#        self.SampKw = SampKw
#        self.AvgIndex = AvgIndex

#        self.MuxBuffer = Buffer(BufferSize=BufferSize,
#                                nChannels=self.DaqInterface.nChannels)
#        self.MuxBuffer = FileMod.FileBuffer()

    def run(self, *args, **kwargs):
        print('start ')
        while True:
            Inputs = self.NiScope.channels[0,1,2,3].fetch(num_samples=self.BS,
                                                          relative_to=niscope.FetchRelativeTo.READ_POINTER,
                                                          offset=0,
                                                          record_number=0,
                                                          num_records=1,
                                                          timeout=2)
            value = np.ndarray((self.BS, 4))
            for i, In in enumerate(Inputs):
                InSig = np.array(In.samples)
            value[:, i] = InSig #to do a BufferSize x nChan Matrix
            self.NewData.emit()

