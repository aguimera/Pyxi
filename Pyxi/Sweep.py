# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 10:21:52 2019

@author: Lucia
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

import numpy as np
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
                                        )                       
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
         
         self.AcConfig.sigTreeStateChanged.connect(self.on_Ac_Sweep_Changed)
         self.on_Ac_Sweep_Changed()
         self.VgsConfig.sigTreeStateChanged.connect(self.on_Vgs_Sweep_Changed)
         self.on_Vgs_Sweep_Changed()
         
     def on_Ac_Sweep_Changed(self):
         self.AcSweepValues = np.linspace(self.AcConfig.param('Start').value(),
                                          self.AcConfig.param('Stop').value(),
                                          self.AcConfig.param('nSweeps').value())
         
     def on_Vgs_Sweep_Changed(self):
         self.VgsSweepValues = np.linspace(self.VgsConfig.param('Start').value(),
                                           self.VgsConfig.param('Stop').value(),
                                           self.VgsConfig.param('nSweeps').value()
                                           )
         self.VgsTime = self.VgsConfig.param('timeXsweep').value()
         
         if self.VgsTime > 2:
             if self.VgsTime % 2 != 0:
                 self.VgsTime += 1
             self.CountTime = self.VgsTime/2
             print(self.VgsTime, self.CountTime)
        
         else:
             self.CountTime = 0
             print(self.VgsTime, self.CountTime)
             
     def GetSweepParams(self):
         self.Sweeps = {'VgsSweep':{},
                        'AcSweep':{}
                        }
         for Config in self.VgsConfig.children():
             self.Sweeps['VgsSweep'][Config.name()] = Config.value()
             
         for Config in self.AcConfig.children():
             self.Sweeps['AcSweep'][Config.name()] = Config.value()

         return self.Sweeps

#     def ChangeVCols(self, ColsConfig, FsGen, GenSize, CMVoltage):
#         
#         if self.IterAcSweep >= len(self.AcSweepValues):
#             CMVoltage=self.VgsSweepValues[self.IterVgsSweep]
#        
#             self.IterAcSweep = 0
#             self.IterVgsSweep = self.IterVgsSweep+1
#         for Col, val in ColsConfig.items():
#             ColsConfig[Col]['Amplitude']=self.AcSweepValues[self.IterAcSweep]
#        
#         self.IterAcSweep = self.IterAcSweep+1
#         self.Generator = {'ColsConfig':ColsConfig,
#                           'FsGen':FsGen,
#                           'GenSize':GenSize,
#                           'CMVoltage':CMVoltage
#                           }
#         
#         if self.IterVgsSweep >= len(self.VgsSweepValues):
#             EndOfSweeps = True
#             self.IterAcSweep=0
#             self.IterVgsSweep=0
#         if self.IterVgsSweep < len(self.VgsSweepValues):
#             EndOfSweeps = False
#             
#         return EndOfSweeps, self.Generator
     
     def NextSweep(self, nAcSw, nVgsSw, ColsConfig, FsGen,GenSize, CMVoltage):
        #cambiar Vgs
        CMVoltage=self.VgsSweepValues[nVgsSw]
        #cambiar Acs
        print(CMVoltage, nVgsSw)
        print(self.AcSweepValues, nAcSw)
        for Col, val in ColsConfig.items():
             ColsConfig[Col]['Amplitude']=self.AcSweepValues[nAcSw]
             
        #cambiar el diccionario del generador
        self.Generator = {'ColsConfig':ColsConfig,
                           'FsGen':FsGen,
                           'GenSize':GenSize,
                           'CMVoltage':CMVoltage
                           }
        
        return self.Generator

























                    