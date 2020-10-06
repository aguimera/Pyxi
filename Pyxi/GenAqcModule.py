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
                                     'suffix': 'Ohms'},
                                    {'name': 'AcqDiff',
                                     'type': 'bool',
                                     'value': True, },
                                    )
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

DemodulParams = ({'name': 'DemodConfig',
                  'type': 'group',
                  'children': ({'name': 'DemEnable',
                                'title': 'On/Off',
                                'type': 'bool',
                                'value': True},
                               {'name': 'Save Demod',
                                'title': 'Save Demod Data',
                                'type': 'bool',
                                'value': True}, #if set to false, raw data is saved
                               {'name': 'FsDemod',
                                'type': 'float',
                                'value': 2e6,
                                'readonly': True,
                                'siPrefix': True,
                                'suffix': 'Hz'},
                               {'name': 'DSFs',
                                'title': 'DownSampling Fs',
                                'type': 'float',
                                'readonly': True,
                                'value': 10e3,
                                'siPrefix': True,
                                'suffix': 'Hz'},
                               {'name': 'DSFact',
                                'title': 'DownSampling Factor',
                                'type': 'int',
                                'value': 100},
                               {'name': 'FiltOrder',
                                'title': 'Filter Order',
                                'type': 'int',
                                'value': 2},
                               {'name': 'OutType',
                                'title': 'Output Var Type',
                                'type': 'list',
                                'values': ['Real', 'Imag', 'Angle', 'Abs'],
                                'value': 'Abs'},
                               )
                  })

# #######################################################################


class GenAcqConfig(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)
        ###############Config Parameters#############################
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
        
        ###############Rows Parameters#############################
        self.addChild(RowsParam)
        self.RowsConfig = self.param('RowsConfig')
        self.RowsConfig.sigTreeStateChanged.connect(self.on_RowsConfig_Changed)
        
        ###############Columns Parameters#############################
        self.addChild(ColumnsParam)
        self.ColConfig = self.param('ColumnsConfig')
        self.addChild(CarriersConfigParam)
        self.CarrierConfig = self.param('CarriersConfig')
        self.ColConfig.sigTreeStateChanged.connect(self.on_ColConfig_Changed)

        self.FsGen.sigValueChanged.connect(self.on_FreqSig_Changed)
        self.Freqs = [p.param('Frequency').value() for p in self.CarrierConfig.children()]
    
        ###############Demod Parameters#############################
        self.addChild(DemodulParams)
        self.DemConfig = self.param('DemodConfig')
        self.DemEnable = self.DemConfig.param('DemEnable')
        self.FsDem = self.DemConfig.param('FsDemod')
        self.DSFs = self.DemConfig.param('DSFs')
        self.DSFact = self.DemConfig.param('DSFact')
        self.FiltOrder = self.DemConfig.param('FiltOrder')
        self.OutType = self.DemConfig.param('OutType')

        self.FsDem.sigValueChanged.connect(self.on_FsDem_changed)
         
        ###############Init Params#############################
        self.on_Config_Changed()
        self.on_RowsConfig_Changed()
        self.on_ColConfig_Changed()
        self.on_FreqSig_Changed()
        self.on_DSFact_changed()
        
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
   
# #############################DemodConfig##############################
    def ReCalc_DSFact(self, BufferSize):
        while BufferSize % self.DSFact.value() != 0:
            self.DSFact.setValue(self.DSFact.value()+1)
        self.on_DSFact_changed()
        print('DSFactChangedTo'+str(self.DSFact.value()))

    def on_FsDem_changed(self):
        self.on_DSFact_changed()

    def on_DSFact_changed(self):
        DSFs = self.FsDem.value()/self.DSFact.value()
        self.DSFs.setValue(DSFs)

# #############################Get Params##############################
    def GetRowParams(self):
        '''
        Generates a dictionary with Active Rows properties and Adq properties

        Scope={   'FsGen': 2e6,
                  'GenSize': 20e3,
                  'FsScope': 2000000.0,
                  'BufferSize': 1000000,
                  'CMVoltage': 0.0,
                  'AcqVRange': 1,
                  'NRow': 8,
                  'GainBoard': 10000.0
                  }
        '''
        ScopeConfig = {}
        for Config in self.AcqConfig.children():
            if Config.name() == 'tFetch':
                continue
            if Config.name() == 'NRow':
                continue
            ScopeConfig[Config.name()] = Config.value()

        return ScopeConfig
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
    
    def GetGenParams(self):
        """
        Makes a dictionary which contains all te configuration for the
        Generator, the Columns and the waves to generate

        'CarrierConfig': {'Col1': {'Frequency': 100000.0,
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
                                            'Amplitude': 0,}
                                   },
                    }

        """
        CarrierConfig = {}
        for Config in self.CarrierConfig.children():
            CarrierConfig[Config.name()] = {}
            for Values in Config.children():
                CarrierConfig[Config.name()][Values.name()] = Values.value()

        return CarrierConfig

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
 
    def GetDemodParams(self):
        '''Functions that return the Parameters of the Demodulation Process
           Returns a dictionary:
           {'FsDemod': 500000.0,
            'DSFact': 100,
            'FiltOrder': 2,
            'OutType': 'Abs'}
        '''
        Demod = {}
        for Config in self.DemConfig.children():
            if Config.name() == 'DemEnable':
                continue
            if Config.name() == 'DSFs':
                continue
            Demod[Config.name()] = Config.value()
        return Demod
    
    def GetAcqParams(self):
        AcqKwargs = {'CarrierConfig': self.GetGenParams(),
                     'ColChannels': self.GetCarriers().keys(),
                     'ScopeChannels': self.GetRows().keys(),
                     }
        AcqKwargs.update(self.GetRowParams())

        return AcqKwargs

    def GetDemThreadParams(self):
        DemKwargs = {'Carriers': self.GetCarriers(),
                     'ScopeChannels': self.GetRows().keys(),
                     'BufferSize': self.BufferSize.value(),
                     'Gain': self.GainBoard.value(),
                     }
        DemKwargs.update(self.GetDemodParams())
        
        return DemKwargs
    
    def GetChannels(self, Rows, Fcs):
        '''Function that returns a dictionary with the names of demodulation
           channels and indexes
            {'Ch01Col1':0,
             'Ch02Col1':1,
             'Ch03Col1':2,
             'Ch04Col1':3,
             'Ch05Col1':4,
             'Ch06Col1':5,
             'Ch07Col1':6,
             'Ch08Col1':7,
            }
        '''
        DemChnNames = {}
        i = 0
        for r in Rows:
            for col, f in Fcs.items():
                DemChnNames[r+col] = i
                i = i + 1
        return DemChnNames

    