# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 09:42:31 2019

@author: Lucia
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

import numpy as np
import copy
import time
import re

ConfigParam =  {'name': 'AcqConfig',
                       'type': 'group',
                       'children':({'name': 'Fs',
                                    'title': 'Sampling Rate',
                                    'type': 'float',
                                    'value': 2e6,
                                    'siPrefix': True,
                                    'suffix': 'Hz'},
                                   {'name': 'BufferSize',
                                    'title': 'Buffer Size',
                                    'type': 'int',
                                    'value': int(20e3),
                                    'readonly': False,
                                    'siPrefix': True,
                                    'suffix': 'Samples'},
                                   {'name': 'tFetch',
                                    'title': 'Fetching Time',
                                    'type': 'float',
                                    'readonly': True,
                                    'value': 0.5,
                                    'siPrefix': True,
                                    'suffix': 's'},
                                   {'name': 'VgSweep',
                                    'type': 'group',
                                    'children': ({'name':'Vinit',
                                                  'type':'float',
                                                  'value':0,
                                                  'siPrefix':True,
                                                  'suffix':'V'},
                                                 {'name':'Vfinal',
                                                  'type':'float',
                                                  'value':-0.4,
                                                  'siPrefix':True,
                                                  'suffix':'V'},
                                                 {'name':'Vstep',
                                                  'type':'float',
                                                  'value':0.01,
                                                  'siPrefix':True,
                                                  'suffix':'V'},)},
                                   {'name': 'VdSweep',
                                    'type': 'group',
                                    'children': ({'name':'Vinit',
                                                  'type':'float',
                                                  'value':0.02,
                                                  'siPrefix':True,
                                                  'suffix':'V'},
                                                 {'name':'Vfinal',
                                                  'type':'float',
                                                  'value':0.2,
                                                  'siPrefix':True,
                                                  'suffix':'V'},
                                                 {'name':'Vstep',
                                                  'type':'float',
                                                  'value':0.01,
                                                  'siPrefix':True,
                                                  'suffix':'V'},)}, 
                                   {'name': 'AcqVRange',
                                    'title': 'Voltage Range',
                                    'type': 'list',
                                    'values': [0.1, 0.2, 0.5, 1, 2, 5, 10],
                                    'value': 1,
                                    'visible': True},
                                   {'name': 'NRow',
                                    'title': 'Number of Acq Channels',
                                    'type': 'int',
                                    'value': 0,
                                    'readonly': True,
                                    'siPrefix': True,
                                    'suffix': 'Chan'},
                                   {'name': 'GainBoard',
                                    'titel': 'System Gain',
                                    'value': (10e3),
                                    'type': 'int',
                                    'siPrefix': True,
                                    'suffix': 'Ohms'},)
                       }

RowsParam = {'name': 'RowsConfig',
                   'type': 'group',
                   'children':({'name':'Ch01',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 0},
                                            )},
                               {'name':'Ch02',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 1},
                                            )},
                               {'name':'Ch03',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 2},
                                            )},
                               {'name':'Ch04',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 3},
                                           )},
                               {'name':'Ch05',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 4},
                                            )},
                               {'name':'Ch06',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 5},
                                            )},
                               {'name':'Ch07',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 6}, 
                                            )},  
                               {'name':'Ch08',
                                'type': 'group',
                                'children':({'name': 'Enable',
                                             'type': 'bool',
                                             'value': True,},
                                            {'name':'Index',
                                             'type': 'int',
                                             'readonly': True,
                                             'value': 7},
                                            )},                                              
                               ) 
                        }  
                                
ColumnsParam = {'name': 'ColumnsConfig',
                      'type': 'group',
                      'children':({'name':'Col1',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True,},
                                               {'name':'Analog',
                                                'type': 'bool',
                                                'value': True},
                                               {'name':'Digital',
                                                'type': 'bool',
                                                'value': False},
                                                )},
                                   {'name':'Col2',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': False,},
                                                {'name':'Analog',
                                                'type': 'bool',
                                                'value': True},
                                                {'name':'Digital',
                                                'type': 'bool',
                                                'value': False},
                                                )},
                                   {'name':'Col3',
                                   'type': 'group',
                                   'children':({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': False,},
                                                {'name':'Analog',
                                                'type': 'bool',
                                                'value': True},
                                                {'name':'Digital',
                                                'type': 'bool',
                                                'value': False},
                                               )},                                              

                                            ) 
                               }

CarriersConfigParam={'name': 'CarriersConfig',
                    'type': 'group',
                    'children': ()}

CarrierParam = {'name':'ColX',
               'type': 'group',
               'children': ({'name': 'Frequency',
                             'value': 30e3,
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

########################################################################
               
class GenAcqConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChild(ConfigParam)
        self.AcqConfig = self.param('AcqConfig')
        self.Fs = self.AcqConfig.param('Fs')
        self.BufferSize = self.AcqConfig.param('BufferSize')
        self.FetchTime = self.AcqConfig.param('tFetch')
        self.Vcm = self.AcqConfig.param('CMVoltage')
        self.NRows = self.AcqConfig.param('NRow')
        self.GainBoard = self.AcqConfig.param('GainBoard')
        
        self.VgSweepVals = np.arange(self.AcqConfig.param('VgSweep').param('Vinit'),
                                     self.AcqConfig.param('VgSweep').param('Vfinal'),
                                     self.AcqConfig.param('VgSweep').param('Vstep'))
        self.VdSweepVals = np.arange(self.AcqConfig.param('VdSweep').param('Vinit'),
                                     self.AcqConfig.param('VdSweep').param('Vfinal'),
                                     self.AcqConfig.param('VdSweep').param('Vstep'))
        
        self.Fs.sigValueChanged.connect(self.on_Config_Changed)
        self.BufferSize.sigValueChanged.connect(self.on_Config_Changed)
        
        self.addChild(RowsParam)
        self.RowsConfig = self.param('RowsConfig') 
        self.RowsConfig.sigTreeStateChanged.connect(self.on_RowsConfig_Changed)
        
        self.addChild(ColumnsParam)
        self.ColConfig = self.param('ColumnsConfig')
        self.addChild(CarriersConfigParam)
        self.CarrierConfig = self.param('CarriersConfig')
        self.ColConfig.sigTreeStateChanged.connect(self.on_ColConfig_Changed)
        
        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
        for p in self.CarrierConfig.children():
            p.param('Frequency').sigValueChanged.connect(self.on_FreqSig_Changed())
         
                
        self.on_Config_Changed()
        self.on_RowsConfig_Changed()
        self.on_ColConfig_Changed()
 ##############################GeneralConfig##############################     
    def on_Config_Changed(self):
        Fs = self.Fs.value()
        BS = self.BufferSize.value()
        tF = self.FetchTime.value()
        tF = BS/Fs
        self.FetchTime.setValue(tF)
        self.on_FreqSig_Changed()
        
  ##############################RowsConfig##############################             
    def on_RowsConfig_Changed(self):
        self.Rows = []
        for p in self.RowsConfig.children():
            if p.param('Enable').value():
                self.Rows.append(p.name())
        self.NRows.setValue(len(self.Rows))
    
    def GetRowParams(self):
        '''
        Generates a dictionary with Active Rows properties and Adq properties
        
        Scope={'RowsConfig': {'Row1': {'Enable': True, 
                                          'Index': 0, }, 
                                 'Row2': {'Enable': True, 
                                          'Index': 1, }, 
                                 'Row3': {'Enable': True, 
                                          'Index': 2, }, 
                                 'Row4': {'Enable': True, 
                                          'Index': 3, }, 
                                 'Row5': {'Enable': True, 
                                          'Index': 4, }, 
                                 'Row6': {'Enable': True, 
                                          'Index': 5, }, 
                                 'Row7': {'Enable': True, '
                                          Index': 6, }, 
                                 'Row8': {'Enable': True, 
                                          'Index': 7, }
                                 }, 
                  'Fs': 2000000.0, 
                  'BufferSize': 1000000, 
                  'CMVoltage': 0.0,
                  'AcqVRange': 1,
                  'NRow': 8,  
                  'GainBoard': 10000.0
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
    
    def GetRowsNames(self):
        '''
        Generates a array with names of rows
        
        RowNames=[]
        '''
        RowNames = []
        for Config in self.RowsConfig.children():
            if Config.param('Enable').value() == True:
                RowNames.append(Config.name())

        return RowNames
        
 ##############################GenerationConfig##############################      
    def on_FreqSig_Changed(self):
        Fs = self.Fs.value()
        Samps = self.BufferSize.value()
        
        for p in self.CarrierConfig.children():
            Fc = p.param('Frequency').value()
            nc = round((Samps*Fc)/Fs)
            Fnew =  (nc*Fs)/Samps
            p.param('Frequency').setValue(Fnew)
            
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
            p.param('Frequency').sigValueChanged.connect(self.on_FreqSig_Changed)
        
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
                    }
            
        """
        self.Generator = {'ColsConfig':{},
                          }
        for Config in self.CarrierConfig.children():
            self.Generator['ColsConfig'][Config.name()] = {}
            for Values in Config.children():
                self.Generator['ColsConfig'][Config.name()][Values.name()] = Values.value()
        
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        