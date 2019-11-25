# -*- coding: utf-8 -*-
"""
Created on Wed May 22 09:55:53 2019

@author: Lucia
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

import numpy as np
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
                            )
               }

NifGenGeneratorParam =  {'name': 'GeneratorConfig',
                       'type': 'group',
                       'children':({'name': 'FsGen',
                                    'title': 'Gen Sampling Rate',
                                    'type': 'float',
                                    'readonly': True,
                                    'value': 20e6,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'GenSize',
                                    'title': 'Generation Size',
                                    'type': 'int',
                                    'readonly': True,
                                    'value': int(20e3),
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
                                               {'name':'Digital',
                                                'type': 'bool',
                                                'value': False},
                                                )},
                                   {'name':'Col2',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': False,},
                                                {'name':'Digital',
                                                'type': 'bool',
                                                'value': False},
                                                )},
                                   {'name':'Col3',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': False,},
                                                {'name':'Digital',
                                                'type': 'bool',
                                                'value': False},
                                               )},                                              

                                            ) 
                               }

  
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
        
        self.GenSize.sigValueChanged.connect(self.on_FreqCol_Changed)
        self.FsGen.sigValueChanged.connect(self.on_FreqCol_Changed)
        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]

        for p in self.CarrierConfig.children():
            p.param('Frequency').sigValueChanged.connect(self.on_FreqCol_Changed)

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
      
    def on_FreqCol_Changed(self):
        Fs = self.FsGen.value()
        Samps = self.GenSize.value()
        for p in self.CarrierConfig.children():
            Fc = p.param('Frequency').value()
            nc = round((Samps*Fc)/Fs)
            Fnew =  (nc*Fs)/Samps
            p.param('Frequency').setValue(Fnew)
            
            
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


            














