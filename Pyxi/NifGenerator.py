# -*- coding: utf-8 -*-
"""
Created on Wed May 22 09:55:53 2019

@author: Lucia
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

CarriersConfigParam={'name': 'CarriersConfig',
                    'type': 'group',
                    'children': ()}

CarrierParam = {'name':'ColX',
               'type': 'group',
               'children': ({'name': 'Frequency',
                             'value': 100e3,
                             'type': 'float',
                             'siPrefix': True,
                             'suffix': 'Hz'},
                            {'name': 'Phase',
                             'value': 0,
                             'type': 'float',
                             'siPrefix': True,
                             'suffix': 'º'},
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

NifGenGeneratorParam =  {'name': 'GeneratorConfig',
                       'type': 'group',
                       'children':({'name': 'FsGen',
                                    'title': 'Gen Sampling Rate',
                                    'type': 'float',
                                    'readonly': True,
                                    'value': 2e6,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'GenSize',
                                    'title': 'Generation Size',
                                    'type': 'int',
                                    'readonly': True,
                                    'value': int(2e3),
                                    'siPrefix': True,
                                    'suffix': 'Samples'},
                                   {'name': 'CMVoltage',
                                    'title': 'Common Mode Voltage',
                                    'value': 0.0,
                                    'type': 'float',
                                    'siPrefix': True,
                                    'suffix': 'V'})
                 }
                 
NifGenColsParam = {'name': 'ColumnsConfig',
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
                                                'value': 1})},
                                   {'name':'Col2',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': False,},
                                                {'name':'Resource',
                                                'type': 'str',
                                                'readonly': True,
                                                'value': 'PXI1Slot2'},
                                               {'name':'Index',
                                                'type': 'int',
                                                'readonly': True,
                                                'value': 2})},
                                   {'name':'Col3',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': False,},
                                                {'name':'Resource',
                                                'type': 'str',
                                                'readonly': True,
                                                'value': 'PXI1Slot3'},
                                               {'name':'Index',
                                                'type': 'int',
                                                'readonly': True,
                                                'value': 3})},                                              

                                            ) 
                               }

GenOptions = 'Simulate=0,DriverSetup=Model:5413;Channels:0-1;BoardType:PXIe;MemorySize:268435456'
  
##############################Generator##########################################
class NifGeneratorParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChild(NifGenColsParam)
        self.ColConfig = self.param('ColumnsConfig')
        self.addChild(NifGenGeneratorParam)
        self.SamplingConfig = self.param('GeneratorConfig')
        self.FsGen = self.SamplingConfig.param('FsGen')
        self.GenSize = self.SamplingConfig.param('GenSize')
        
        self.addChild(CarriersConfigParam)
        self.CarrierConfig = self.param('CarriersConfig')
        
        self.ColConfig.sigTreeStateChanged.connect(self.on_ColConfig_Changed)
        self.on_ColConfig_Changed()
        
        self.on_FreqCol_Changed()
        self.on_AmpCol_Changed() 
        
        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
#        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
        for p in self.CarrierConfig.children():
            p.param('Frequency').sigValueChanged.connect(self.on_FreqCol_Changed)
            p.param('Amplitude').sigValueChanged.connect(self.on_AmpCol_Changed)

    def on_ColConfig_Changed(self):
        Cols = []
        for p in self.ColConfig.children():
            if p.param('Enable').value():
                Cols.append(p.name())
        
        self.CarrierConfig.clearChildren()
        for col in Cols:
            cc = copy.deepcopy(CarrierParam)
            cc['name'] = col
            cc['children'][2]['value'] = 2*cc['children'][1]['value']
            self.CarrierConfig.addChild(cc)
        for p in self.CarrierConfig.children():
            p.param('Frequency').sigValueChanged.connect(self.on_FreqCol_Changed)
            p.param('Amplitude').sigValueChanged.connect(self.on_AmpCol_Changed)
      
    def on_FreqCol_Changed(self):
        Fs = self.FsGen.value()
        Samps = self.GenSize.value()
        for p in self.CarrierConfig.children():
            Fc = p.param('Frequency').value()
            nc = round((Samps*Fc)/Fs)
            Fnew =  (nc*Fs)/Samps
            p.param('Frequency').setValue(Fnew)
            Gain = 2*p.param('Amplitude').value()
            p.param('Gain').setValue(Gain)
            
    def on_AmpCol_Changed(self):
        for p in self.CarrierConfig.children():
            Gain = 2*p.param('Amplitude').value()
            p.param('Gain').setValue(Gain)
            
    def GetGenParams(self):       
        """
        Makes a dictionary which contains all te configuration for the
        Generator, the Columns and the waves to generate
        
        Generator: {'ColsConfig': {'Col1': {'Frequency': 100000.0, 
                                            'Phase': 0, 
                                            'Amplitude': 0, 
                                            'Gain': 0, 
                                            'Resource': 'PXI1Slot2', 
                                            'Index': 0}, 
                                   'Col2': {'Frequency': 100000.0, 
                                            'Phase': 0, 
                                            'Amplitude': 0, 
                                            'Gain': 0, 
                                            'Resource': 'PXI1Slot2', 
                                            'Index': 1}, 
                                   'Col3': {'Frequency': 100000.0, 
                                            'Phase': 0, 
                                            'Amplitude': 0, 
                                            'Gain': 0, 
                                            'Resource': 'PXI1Slot3', 
                                            'Index': 0}, 
                                   'Col4': {'Frequency': 100000.0, 
                                            'Phase': 0, 
                                            'Amplitude': 0, 
                                            'Gain': 0, 
                                            'Resource': 'PXI1Slot3', 
                                            'Index': 1}}, 
                    'FsGen': 20000000.0, 
                    'GenSize': 20000, 
                    'CMVoltage': 0.0}
            
        """
        self.Generator = {'ColsConfig':{},
                          }
        for Config in self.CarrierConfig.children():
            self.Generator['ColsConfig'][Config.name()] = {}
            for Values in Config.children():
                self.Generator['ColsConfig'][Config.name()][Values.name()] = Values.value()
        
        for Config in self.SamplingConfig.children():
            self.Generator[Config.name()] = Config.value()
        
        for Config in self.ColConfig.children():
            for Values in Config.children():
                if Values.name() == 'Enable':
                    if Values.value() == False:
                        break
                    continue
                self.Generator['ColsConfig'][Config.name()][Values.name()] = Values.value()
            
        return self.Generator   
        
    def GetCarriers(self):
        """
        Makes a dictionary which contains the Column and the Carrier Frequency
        applied.
        
        Carriers: {'Col1': 100000.0, 
                   'Col2': 100000.0, 
                   'Col3': 100000.0, 
                   'Col4': 100000.0}
            
        """
        Carriers = {}
        for p in self.CarrierConfig.children():
            Carriers[p.name()] = p.param('Frequency').value()

        return Carriers

class SigGen(nifgen.Session):    
    def SetArbSignal(self, Signal, index, gain, Vcm):   
        """
        Function of NifGen Module that creates and configures the desired
        waveform
        
        Signal: numpy array with the values of the signal to be created
        index: index of the generation channel (0 or 1)
        gain: gain applied to Signal values, set to 1 to don't have gain
        Vcm: Common Mode Voltage to apply to all the generators
        """
        Handle = self.create_waveform(Signal)
        self.channels[index].configure_arb_waveform(waveform_handle=Handle,
                                                    gain=gain,
                                                    offset=Vcm)

class Columns():
    Columns = {} # {'Col1': {'session': sessionnifgen, 
#                             'index': int}}
    Resources = {} # 'PXI1Slot2': sessionnifgen
    def __init__(self, ColsConfig, FsGen, GenSize):
        """
        Class used to control all the channels of the generator of PXI
        
        ColsConfig: Dictionary that has all the information of the generators 
                    and the waveforms to be generated:
            {Col1: {Frequency: (float in Hz),
                    Phase: (in degrees),
                    Amplitude: (float in V),
                    Gain: (value Fixed at 2*Amplitude),
                    Resource: (fixed at PXI1Slot2 or PXI1Slot3),
                    Index: (between 0 and 1 depending on the generator output),
                    }
            ...
             Col4: {Frequency: ,
                    Phase: ,
                    Amplitude: ,
                    Gain: ,
                    Resource: ,
                    Index: ,
                    }
            }
            
        FsGen:Sampling Frequency of the Generator (Fixed at 20MHz)
        GenSize: Number of Samples of the generated waveforms (fixed at 20k)
        """
        self.FsGen = FsGen
        self.Ts = 1/self.FsGen
        self.GenSize = GenSize
        self.t = np.arange(0, self.Ts*self.GenSize, self.Ts)
        # Init resources and store sessions
        Res = [conf['Resource'] for col, conf in ColsConfig.items()]                
        for res in set(Res):
            SesGen = SigGen(resource_name=res, options=GenOptions)
            SesGen.output_mode = nifgen.OutputMode.ARB
            SesGen.reference_clock_source = nifgen.ReferenceClockSource.PXI_CLOCK
            SesGen.ref_clock_frequency=100e6
            SesGen.clock_mode=nifgen.ClockMode.HIGH_RESOLUTION
            SesGen.arb_sample_rate=FsGen/2
            SesGen.start_trigger_type = nifgen.StartTriggerType.DIGITAL_EDGE
            SesGen.digital_edge_start_trigger_source = 'PXI_Trig0'
            self.Resources[res] = SesGen

        # Init columns indexing dictionaries
        for col, conf in ColsConfig.items():
            self.Columns[col] = {'session': self.Resources[conf['Resource']],
                                 'index':conf['Index']
                                 }
    def Session_Gen_Initiate(self):
        for res, ses in self.Resources.items():
            ses.initiate()
            
    def Session_Gen_Abort(self):
        for res, ses in self.Resources.items():
            ses.abort()
            
    def Gen_SetSignal(self, SigsPars, Vcm):
        """
        Function used to generate the configurated signals
        
        SigsPars: Dictionary that has all the information of the generators 
                    and the waveforms to be generated:
            {Col1: {Frequency: ,
                    Phase: ,
                    Amplitude: ,
                    Gain: ,
                    Resource: ,
                    }
            ...
             Col4: {Frequency: ,
                    Phase: ,
                    Amplitude: ,
                    Gain: ,
                    Resource: ,
                    }
            }
            
        Vcm: Common Mode Voltage to apply to all the generators
        """
        for Col,pars in SigsPars.items():
            if Col == 'Offset':
                continue
            signal = pars['Amplitude']*np.sin(2*np.pi*pars['Frequency']*self.t+((np.pi/180)*pars['Phase']))
            #solo si Vcm no esta conectado a GND
            #Si Vcm esta conectado a GND, comentar if siguiente
            if Col != 'Col1':
                print('Warning: Vcm=0 en todos los canales menos Col0 (Vcm not connected to GND in PCB)')
                Vcm = 0
            self.Columns[Col]['session'].SetArbSignal(index=self.Columns[Col]['index'],
                                                      Signal=signal, 
                                                      gain = 1,
                                                      Vcm=Vcm)
            














