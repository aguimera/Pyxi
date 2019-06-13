# -*- coding: utf-8 -*-
"""
Created on Wed May 22 11:39:12 2019

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

NiScopeAcqParam =  {'name': 'AcqConfig',
                       'type': 'group',
                       'children':({'name': 'FsScope',
                                    'title': 'Sampling Rate',
                                    'type': 'float',
                                    'value': 2e6,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'BufferSize',
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
                                   {'name':'ResourceScope',
                                    'type': 'str',
                                    'readonly': True,
                                    'value': 'PXI1Slot4'},)
                 }
NiScopeRowsParam = {'name': 'RowsConfig',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
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
                                            {'name': 'AcqVRange',
                                             'title': 'Voltage Range',
                                             'type': 'list',
                                             'values': [0.05, 0.2, 1, 6],
                                             'value': 1,
                                             'visible': True
                                             }
                                            )},                                              
                               ) 
                        }  
                                
OptionsScope = {'simulate': False,
                'driver_setup': {'Model': 'NI PXIe-5105',
                                 'BoardType': 'PXIe',
                                 },
                }      
                         
##############################SCOPE##########################################                                
class NiScopeParameters(pTypes.GroupParameter):
        
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        
        self.addChild(NiScopeRowsParam)
        
        self.RowsConfig = self.param('RowsConfig')
        
        self.addChild(NiScopeAcqParam)
        self.AcqConfig = self.param('AcqConfig')
        self.FsScope = self.AcqConfig.param('FsScope')
        self.BufferSize = self.AcqConfig.param('BufferSize')
        self.NRows = self.AcqConfig.param('NRow')
        self.OffsetRows = self.AcqConfig.param('OffsetRows')
        self.tFetch = self.AcqConfig.param('tFetch')
        self.on_BufferSize_Changed()
        
        self.RowsConfig.sigTreeStateChanged.connect(self.on_RowsConfig_Changed)
        self.on_RowsConfig_Changed()
        self.FsScope.sigValueChanged.connect(self.on_FsScope_Changed)
        self.tFetch.sigValueChanged.connect(self.on_BufferSize_Changed)

    def on_RowsConfig_Changed(self):
        self.Rows = []
        for p in self.RowsConfig.children():
            if p.param('Enable').value():
                self.Rows.append(p.name())
        self.NRows.setValue(len(self.Rows))
       
    def on_FsScope_Changed(self):
        self.on_BufferSize_Changed()
        
    def on_BufferSize_Changed(self):
        Fs = self.FsScope.value()
        tF = self.tFetch.value()
        Samples = round(tF*Fs)
        tF = Samples/Fs
        self.tFetch.setValue(tF)
        self.BufferSize.setValue(Samples)
     
    def GetRowParams(self):
        '''
        Generates a dictionary with Active Rows properties and Adq properties
        
        Scope={'RowsConfig': {'Row1': {'Enable': True, 
                                          'Index': 0, 
                                          'AcqVRange': 1}, 
                                 'Row2': {'Enable': True, 
                                          'Index': 1, 
                                          'AcqVRange': 1}, 
                                 'Row3': {'Enable': True, 
                                          'Index': 2, 
                                          'AcqVRange': 1}, 
                                 'Row4': {'Enable': True, 
                                          'Index': 3, 
                                          'AcqVRange': 1}, 
                                 'Row5': {'Enable': True, 
                                          'Index': 4, 
                                          'AcqVRange': 1}, 
                                 'Row6': {'Enable': True, 
                                          'Index': 5, 
                                          'AcqVRange': 1}, 
                                 'Row7': {'Enable': True, '
                                          Index': 6, 
                                          'AcqVRange': 1}, 
                                 'Row8': {'Enable': True, 
                                          'Index': 7, 
                                          'AcqVRange': 1}
                                 }, 
                  'FsScope': 2000000.0, 
                  'BufferSize': 1000000, 
                  'NRow': 8, 
                  'OffsetRows': 0, 
                  'GainBoard': 10000.0, 
                  'ResourceScope': 'PXI1Slot4'
                  }
        '''
        Scope = {'RowsConfig':{},
                }
        for Config in self.RowsConfig.children():
            if Config.param('Enable').value() == True:
                Scope['RowsConfig'][Config.name()]={}
                for Values in Config.children():
                    if Values == 'Enable':
                        continue
                    Scope['RowsConfig'][Config.name()][Values.name()] = Values.value()
        for Config in self.AcqConfig.children():
            if Config.name() =='tFetch':
                continue
            Scope[Config.name()] = Config.value()

        return Scope
    
    def GetRows(self):
        '''
        Generates a dictionary with Rows Actives and their index
        
        RowNames={'Row1': 0, 
                  'Row2': 1, 
                  'Row3': 2, 
                  'Row4': 3, 
                  'Row5': 4, 
                  'Row6': 5, 
                  'Row7': 6, 
                  'Row8': 7}
        '''
        RowNames = {}
        for i,r in enumerate(self.Rows):
            RowNames[r]=i
        return RowNames

class Rows():
#Init Scope Channels
    Rows = {} #{'Row1': Range, Index}
    def __init__(self, RowsConfig, FsScope, ResourceScope):
        """
        Class used to configure the Scope channels and adcquisition
        
        RowsConfig: Dictionary that has all the information of the generators 
                    and the waveforms to be generated:
                    (Solo deben aparecer las Rows que se van a utilizar)
            {Row1: {Enable: (True or False) ,
                    Index: (0 to 7 depending on the Row),
                    AcqVRange: (Voltage Range of the ADC)
                    }
            ...
             Row8: {Enable: ,
                    Index: ,
                    AcqVRange: ,
                    Gain: ,
                    Resource: ,
                    }
            }
            
        FsScope: Sampling Frequency for the adquisition
        ResourceScope: fixed to PXI1Slot4
        """
        self.SesScope = SigScope(resource_name=ResourceScope, options=OptionsScope)
        self.SesScope.acquisition_type=niscope.AcquisitionType.NORMAL
        self.SesScope.configure_horizontal_timing(min_sample_rate=FsScope,
                                                  min_num_pts=int(1e3),
                                                  ref_position=50.0,
                                                  num_records=1,
                                                  enforce_realtime=True)
        self.SesScope.exported_start_trigger_output_terminal = 'PXI_Trig0'
        self.SesScope.input_clock_source='PXI_Clk'
        self.SesScope.configure_trigger_software()
        self.SesScope.Scope_GetSignal(RowsConfig)

    #Init Acquisition
    def Session_Scope_Initiate(self):
        self.SesScope.initiate()

    def Session_Scope_Abort(self):
        self.SesScope.abort()
        
# Init Session of Scope        
class SigScope(niscope.Session):
    def Scope_GetSignal(self, RowsConfig):#RowsConfig = {'Row1': Range, Index}
        """
        Configure the vertical range and characteristics of the scope for the
        adcquisition
        
        RowsConfig: Dictionary that has all the information of the generators 
                    and the waveforms to be generated:
                    (Solo deben aparecer las Rows que se van a utilizar)
            {Row1: {Enable: (True or False) ,
                    Index: (0 to 7 depending on the Row),
                    AcqVRange: (Voltage Range of the ADC)
                    }
            ...
             Row8: {Enable: ,
                    Index: ,
                    AcqVRange: ,
                    Gain: ,
                    Resource: ,
                    }
            }
        """
        for Rows, params in RowsConfig.items():
            self.channels[params['Index']].configure_vertical(range=params['AcqVRange'], 
                                                              coupling=niscope.VerticalCoupling.AC)
            self.channels[params['Index']].configure_chan_characteristics(input_impedance=1000000, 
                                                                          max_input_frequency=600000.0)
            
            
        
