# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 10:21:52 2019

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

import Pyxi.NifGenerator as NifGen
import Pyxi.NiScope as NiScope

SweepsParam = {'name':'SweepsConfig',
               'type':'group',
               'children':({'name':'Enable',
                            'type':'bool',
                            'value':False},
                           {'name':'VgsSweep',
                            'type':'group',
                            'children':({'name':'Start',
                                         'type': 'float',
                                         'value': 0,
                                         'siPrefix': True,
                                         'suffix': 'V'},
                                        {'name':'Stop',
                                         'type': 'float',
                                         'value': -0.5,
                                         'siPrefix': True,
                                         'suffix': 'V'},
                                        {'name':'nSweeps',
                                         'type': 'int',
                                         'value': 4},
                                        {'name':'timeXsweep',
                                         'type':'int',
                                         'value':15,
                                         'siPrefix':True,
                                         'suffix':'sec'},)
                           },
                           {'name':'AcSweep',
                            'type':'group',
                            'children':({'name':'Start',
                                         'type': 'float',
                                         'value': 0.5,
                                         'siPrefix': True,
                                         'suffix': 'V'},
                                        {'name':'Stop',
                                         'type': 'float',
                                         'value': 0.5,
                                         'siPrefix': True,
                                         'suffix': 'V'},
                                        {'name':'nSweeps',
                                         'type': 'int',
                                         'value': 1},
                                        {'name':'timeXsweep',
                                         'type':'int',
                                         'value':15,
                                         'siPrefix':True,
                                         'suffix':'sec'},)                       
                           })
              }
                            
##############################Sweeps##########################################                                
class SweepsParameters(pTypes.GroupParameter):   
    
     def __init__(self, **kwargs):
         pTypes.GroupParameter.__init__(self, **kwargs)
         
         self.addChild(SweepsParam)
         
         self.SweepsConfig = self.param('SweepsConfig')
         self.VgsConfig = self.SweepsConfig.param('VgsSweep')
         self.AcConfig = self.SweepsConfig.param('AcSweep')

         self.IterVgsSweep = 0
         self.IterAcSweep = 0
         
         self.VgsSweepValues = np.linspace(self.VgsConfig.param('Start').value(),
                                           self.VgsConfig.param('Stop').value(),
                                           self.VgsConfig.param('nSweeps').value()
                                           )

         self.AcSweepValues = np.linspace(self.AcConfig.param('Start').value(),
                                          self.AcConfig.param('Stop').value(),
                                          self.AcConfig.param('nSweeps').value())
         
     def GetSweepParams(self):
         self.Sweeps = {'VgsSweep':{},
                        'AcSweep':{}
                        }
         for Config in self.VgsConfig.children():
             self.Sweeps['VgsSweep'][Config.name()] = Config.value()
             
         for Config in self.AcConfig.children():
             self.Sweeps['AcSweep'][Config.name()] = Config.value()

         return self.Sweeps

     def ChangeVCols(self, ColsConfig, FsGen, GenSize, CMVoltage):
         self.VgsSweepValues = np.linspace(self.VgsConfig.param('Start').value(),
                                           self.VgsConfig.param('Stop').value(),
                                           self.VgsConfig.param('nSweeps').value()
                                           )
         print(self.VgsSweepValues, self.IterVgsSweep)
         self.AcSweepValues = np.linspace(self.AcConfig.param('Start').value(),
                                          self.AcConfig.param('Stop').value(),
                                          self.AcConfig.param('nSweeps').value())
         print(self.AcSweepValues, self.IterAcSweep)
         if self.IterAcSweep >= len(self.AcSweepValues):
             CMVoltage=self.VgsSweepValues[self.IterVgsSweep]
        
             self.IterAcSweep = 0
             self.IterVgsSweep = self.IterVgsSweep+1
         for Col, val in ColsConfig.items():
             ColsConfig[Col]['Amplitude']=self.AcSweepValues[self.IterAcSweep]
        
         self.IterAcSweep = self.IterAcSweep+1
         self.Generator = {'ColsConfig':ColsConfig,
                           'FsGen':FsGen,
                           'GenSize':GenSize,
                           'CMVoltage':CMVoltage
                           }
         print('GeneratorOutput',self.Generator)
         if self.IterVgsSweep >= len(self.VgsSweepValues):
             EndOfSweeps = True
             self.IterAcSweep=0
             self.VgsSweepValues=0
         if self.IterVgsSweep < len(self.VgsSweepValues):
             EndOfSweeps = False
             
         return EndOfSweeps, self.Generator
        
    

























                    