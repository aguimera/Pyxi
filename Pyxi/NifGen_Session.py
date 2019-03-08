# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 09:32:01 2019

@author: Lucia
"""


from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5 import Qt
import numpy as np
from itertools import  cycle

In_Config = ({'name': 'Frequency',
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
              'type': 'float',},
             {'name': 'Offset',
              'value': 0.0,
              'type': 'float',
              'siPrefix': True,
              'suffix': 'V'},
              )

NifGen_params = ({'name': 'Config_Var',
                          'type': 'group',
                          'children':({'name': 'Fs',
                                       'title': 'Sampling Rate',
                                       'type': 'float',
                                       'value': 2e6,
                                       'step': 100,
                                       'siPrefix': True,
                                       'suffix': 'Hz'},
                                      {'name': 'Buffer Size',
                                       'type': 'int',
                                       'value': int(5e3),
                                       'limits': (int(1e3), int(2e6)),
                                       'step': 100,
                                       'siPrefix': True,
                                       'suffix': 'Samples'})
                 },
                {'name': 'Channels',
                         'type': 'group',
                         'children': ({'name': 'Chn0',
                                       'type': 'bool',
                                       'value': True},
                                      {'name': 'In0',
                                       'type': 'group',
                                       'children': In_Config},
                                      {'name': 'Chn1',
                                       'type': 'bool',
                                       'value': True},
                                      {'name': 'In1',
                                       'type': 'group',
                                       'children': In_Config},
                                      {'name': 'Chn2',
                                       'type': 'bool',
                                       'value': True},
                                      {'name': 'In2',
                                       'type': 'group',
                                       'children': In_Config},
                                      {'name': 'Chn3',
                                       'type': 'bool',
                                       'value': True},
                                      {'name': 'In3',
                                       'type': 'group',
                                       'children': In_Config}
                                     )
                 },
                {'name': 'Info.',
                 'type': 'group',
                 'children': ({'name': 'Model',
                               'type': 'str',
                               'value': '5413'},
                              {'name': 'Resource Name 0',
                               'type': 'str',
                               'value': 'PXI1Slot2'},
                              {'name': 'Resource Name 1',
                               'type': 'str',
                               'value': 'PXI1Slot3'},
                              )
                }
               )

class NifGeneratorParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChildren(NifGen_params)