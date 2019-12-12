# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 10:20:22 2019

@author: Lucia
"""

import pyqtgraph.parametertree.parameterTypes as pTypes
from PyQt5.QtWidgets import QFileDialog
import h5py
from PyQt5 import Qt
import os
import deepdish as dd

SaveSweepParams = [{'name': 'Save File',
                    'type': 'action'},
                   {'name': 'File Path',
                    'type': 'str',
                    'value': ''},
                   {'name': 'Oblea',
                    'type': 'str',
                    'value': ''},
                   {'name': 'Disp',
                    'type': 'str',
                    'value': ''},
                   {'name': 'Name',
                    'type': 'str',
                    'value': ''},
                   {'name': 'Cycle',
                    'type': 'int',
                    'value': 0},
                   ]
    
class SaveSweepParameters(pTypes.GroupParameter):
    def __init__(self, QTparent, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.QTparent = QTparent
        self.addChildren(SaveSweepParams)
        self.param('Save File').sigActivated.connect(self.FileDialog)
        self.File = self.param('File Path').value()
        self.Oblea = self.param('Oblea').value()
        self.Disp = self.param('Disp').value()
        self.Cycle = self.param('Cycle').value()
        
    def FileDialog(self):
        RecordFile = QFileDialog.getExistingDirectory(self.QTparent,
                                                    "Select Directory",
                                                    )
        if RecordFile:
            self.param('File Path').setValue(RecordFile)
            
    def SaveDicts(self, Dcdict, Acdict):
        self.FileName = self.File+"/"+self.Oblea+"-"+self.Disp+"-"+self.Name+"{}-Cy{}.h5".format('', self.Cycle)
        dd.io.save(self.Filename, (Dcdict, Acdict), ('zlib', 1))
        
    def FilePath(self):
        return self.param('File Path').value()
    
    