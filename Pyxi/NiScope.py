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
                   'children':({'name':'Ch01',
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
                               {'name':'Ch02',
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
                               {'name':'Ch03',
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
                               {'name':'Ch04',
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
                               {'name':'Ch05',
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
                               {'name':'Ch06',
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
                               {'name':'Ch07',
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
                               {'name':'Ch08',
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

            
            
        
