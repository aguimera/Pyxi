# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 09:42:31 2019

@author: Lucia
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np
import copy

ConfigParam = {'name': 'AcqConfig',
                       'type': 'group',
                       'children': ({'name': 'FsGen',
                                     'title': 'Gen Sampling Rate',
                                     'type': 'float',
                                     'value': 2e6,
                                     'siPrefix': True,
                                     'suffix': 'Hz'},
                                    {'name': 'GenSize',
                                     'title': 'Gen BufferSize',
                                     'type': 'float',
                                     'readonly': True,
                                     'value': 20e3,
                                     'siPrefix': True,
                                     'suffix': 'Hz'},
                                    {'name': 'FsScope',
                                     'title': 'Acq Sampling Rate',
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
                                    {'name': 'CMVoltage',
                                     'title': 'Common Mode Voltage',
                                     'value': 0.0,
                                     'type': 'float',
                                     'siPrefix': True,
                                     'suffix': 'V'},
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
                                     'value': (5e3),
                                     'type': 'int',
                                     'siPrefix': True,
                                     'suffix': 'Ohms'},)
               }

RowsParam = {'name': 'RowsConfig',
                     'type': 'group',
                     'children': ({'name': 'Ch01',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 0},
                                                )},
                                  {'name': 'Ch02',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                'value': 1},
                                                )
                                   },
                                  {'name': 'Ch03',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 2},
                                                )
                                   },
                                  {'name': 'Ch04',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 3},
                                                )
                                   },
                                  {'name': 'Ch05',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 4},
                                                )
                                   },
                                  {'name': 'Ch06',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 5},
                                                )
                                   },
                                  {'name': 'Ch07',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 6},
                                                )
                                   },
                                  {'name': 'Ch08',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 7},
                                                )
                                   },
                                  {'name': 'Ch09',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 8},
                                                )},
                                  {'name': 'Ch10',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                'value': 9},
                                                )
                                   },
                                  {'name': 'Ch11',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 10},
                                                )
                                   },
                                  {'name': 'Ch12',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 11},
                                                )
                                   },
                                  {'name': 'Ch13',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 12},
                                                )
                                   },
                                  {'name': 'Ch14',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 13},
                                                )
                                   },
                                  {'name': 'Ch15',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 14},
                                                )
                                   },
                                  {'name': 'Ch16',
                                   'type': 'group',
                                   'children': ({'name': 'Enable',
                                                 'type': 'bool',
                                                 'value': True, },
                                                {'name': 'Index',
                                                 'type': 'int',
                                                 'readonly': True,
                                                 'value': 15},
                                                )
                                   },
                                  )
             }

ColumnsParam = {'name': 'ColumnsConfig',
                        'type': 'group',
                        'children': ({'name': 'Col1',
                                      'type': 'group',
                                      'children': ({'name': 'Enable',
                                                    'type': 'bool',
                                                    'value': True, },
                                                   {'name': 'Analog',
                                                    'type': 'bool',
                                                    'value': True},
                                                   {'name': 'Digital',
                                                    'type': 'bool',
                                                    'value': False},
                                                   )
                                      },
                                     {'name': 'Col2',
                                      'type': 'group',
                                      'children': ({'name': 'Enable',
                                                    'type': 'bool',
                                                    'value': False, },
                                                   {'name': 'Analog',
                                                    'type': 'bool',
                                                    'value': True},
                                                   {'name': 'Digital',
                                                    'type': 'bool',
                                                    'value': False},
                                                   )
                                      },
                                     {'name': 'Col3',
                                      'type': 'group',
                                      'children': ({'name': 'Enable',
                                                    'type': 'bool',
                                                    'value': False, },
                                                   {'name': 'Analog',
                                                    'type': 'bool',
                                                    'value': True},
                                                   {'name': 'Digital',
                                                    'type': 'bool',
                                                    'value': False},
                                                   )
                                      },
                                     )
                }

CarriersConfigParam = {'name': 'CarriersConfig',
                       'type': 'group',
                       'children': ()}

CarrierParam = {'name': 'ColX',
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
                              'suffix': 'VRMS'},
                             )
                }

# #######################################################################


class GenAcqConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        self.addChild(ConfigParam)
        self.AcqConfig = self.param('AcqConfig')
        self.FsGen = self.AcqConfig.param('FsGen')
        self.GenSize = self.AcqConfig.param('GenSize')
        self.FsScope = self.AcqConfig.param('FsScope')
        self.BufferSize = self.AcqConfig.param('BufferSize')
        self.FetchTime = self.AcqConfig.param('tFetch')
        self.Vcm = self.AcqConfig.param('CMVoltage')
        self.NRows = self.AcqConfig.param('NRow')
        self.GainBoard = self.AcqConfig.param('GainBoard')

        self.FsScope.sigValueChanged.connect(self.on_Config_Changed)
        self.BufferSize.sigValueChanged.connect(self.on_Config_Changed)

        self.addChild(RowsParam)
        self.RowsConfig = self.param('RowsConfig')
        self.RowsConfig.sigTreeStateChanged.connect(self.on_RowsConfig_Changed)

        self.addChild(ColumnsParam)
        self.ColConfig = self.param('ColumnsConfig')
        self.addChild(CarriersConfigParam)
        self.CarrierConfig = self.param('CarriersConfig')
        self.ColConfig.sigTreeStateChanged.connect(self.on_ColConfig_Changed)

        self.FsGen.sigValueChanged.connect(self.on_FreqSig_Changed)
        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
    
        self.on_Config_Changed()
        self.on_RowsConfig_Changed()
        self.on_ColConfig_Changed()
        self.on_FreqSig_Changed()
        
        for p in self.CarrierConfig.children():
            p.param('Frequency').sigValueChanged.connect(self.on_FreqSig_Changed)

# #############################GeneralConfig##############################

    def on_Config_Changed(self):
        Fs = self.FsScope.value()
        BS = self.BufferSize.value()
        tF = self.FetchTime.value()
        tF = BS/Fs
        self.FetchTime.setValue(tF)
        self.on_FreqSig_Changed()

# #############################RowsConfig##############################
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
                              'Row7': {'Enable': True,
                                       Index': 6, },
                              'Row8': {'Enable': True,
                                       'Index': 7, }
                              },
                  'FsGen': 2e6,
                  'GenSize': 20e3,
                  'FsScope': 2000000.0,
                  'BufferSize': 1000000,
                  'CMVoltage': 0.0,
                  'AcqVRange': 1,
                  'NRow': 8,
                  'GainBoard': 10000.0
                  }
        '''
        # Scope = {'RowsConfig': {}, }
        # for Config in self.RowsConfig.children():
        #     if Config.param('Enable').value() is True:
        #         Scope['RowsConfig'][Config.name()] = {}
        #         for Values in Config.children():
        #             if Values.name() == 'Enable':
        #                 continue
        #             Scope['RowsConfig'][Config.name()][Values.name()] = Values.value()
        Scope = {}
        for Config in self.AcqConfig.children():
            if Config.name() == 'tFetch':
                continue
            if Config.name() == 'NRow':
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
                  'Row8': 7 }
        '''
        RowNames = {}
        for i, r in enumerate(self.Rows):
            RowNames[r] = i
        return RowNames

    def GetRowsNames(self):
        '''
        Generates a array with names of rows

        RowNames=[]
        '''
        RowNames = []
        for Rw in self.Rows:
            RowNames.append(Rw)

        return RowNames
    
    def GetChannelsNames(self, Rows, Fcs):
        '''Function that returns an array with the names of demodulation
           channels in dtype S10
            ['Ch01Col1',
             'Ch02Col1',
             'Ch03Col1',
             'Ch04Col1',
             'Ch05Col1',
             'Ch06Col1',
             'Ch07Col1',
             'Ch08Col1',
            ]
        '''
        ChnNames = []
        for r in Rows:
            for col, f in Fcs.items():
                ChnNames.append(r+col)
        Chns = np.array(ChnNames, dtype='S10')
        return Chns

# #############################GenerationConfig##############################
    def on_FreqSig_Changed(self):
        Fs = self.FsGen.value()
        Samps = self.GenSize.value()

        for p in self.CarrierConfig.children():
            Fc = p.param('Frequency').value()
            nc = round((Samps*Fc)/Fs)
            Fnew = (nc*Fs)/Samps
            p.param('Frequency').setValue(Fnew)
        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]

    def on_ColConfig_Changed(self):
        Cols = []
        for p in self.ColConfig.children():
            if p.param('Enable').value():
                Cols.append(p.name())

        self.CarrierConfig.clearChildren()
        for col in Cols:
            cc = copy.deepcopy(CarrierParam)
            cc['name'] = col
#            cc['children'][2]['value'] = 2*cc['children'][1]['value']
            self.CarrierConfig.addChild(cc)

    def GetGenParams(self):
        """
        Makes a dictionary which contains all te configuration for the
        Generator, the Columns and the waves to generate

        Generator: {'ColsConfig': {'Col1': {'Frequency': 100000.0,
                                            'Phase': 0,
                                            'Amplitude': 0, },
                                   'Col2': {'Frequency': 100000.0,
                                            'Phase': 0,
                                            'Amplitude': 0, },
                                   'Col3': {'Frequency': 100000.0,
                                            'Phase': 0,
                                            'Amplitude': 0, },
                                   'Col4': {'Frequency': 100000.0,
                                            'Phase': 0,
                                            'Amplitude': 0,}},
                    }

        """
        self.Generator = {'ColsConfig': {}, }
        for Config in self.CarrierConfig.children():
            self.Generator['ColsConfig'][Config.name()] = {}
            for Values in Config.children():
                self.Generator['ColsConfig'][Config.name()][Values.name()] = Values.value()

        for Config in self.ColConfig.children():
            for Values in Config.children():
                if Values.name() == 'Enable':
                    if Values.value() is False:
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
                   'Col4': 100000.0 }
        """
        Carriers = {}
        for p in self.CarrierConfig.children():
            Carriers[p.name()] = p.param('Frequency').value()

        return Carriers
