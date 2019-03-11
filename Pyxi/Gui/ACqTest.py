# -*- coding: utf-8 -*-
"""
Created on Thu Mar  7 11:00:49 2019

@author: Lucia
"""

from __future__ import print_function
import os
from PyQt5 import Qt
from PyQt5.QtWidgets import QFileDialog

import numpy as np
import time

import pyqtgraph as pg

import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType
from itertools import  cycle
import copy
from scipy.signal import welch

import Pyxi.FileModule as FileMod
import Pyxi.SampleGenerator as SampGen
import Pyxi.PlotModule as PltMod
import Pyxi.FMacqThread as FMacq

class MainWindow(Qt.QWidget):
    ''' Main Window '''

    def __init__(self):
        super(MainWindow, self).__init__()

        layout = Qt.QVBoxLayout(self) 

        self.btnGen = Qt.QPushButton("Start Gen!")
        layout.addWidget(self.btnGen)

        self.NifGenParams = FMacq.NifGeneratorParameters(name='NifGenerator')        
        self.Parameters = Parameter.create(name='params',
                                           type='group',
                                           children=(self.NifGenParams,))

#        
        self.Parameters.sigTreeStateChanged.connect(self.on_pars_changed)
        self.treepar = ParameterTree()
        self.treepar.setParameters(self.Parameters, showTop=False)
        self.treepar.setWindowTitle('pyqtgraph example: Parameter Tree')

        layout.addWidget(self.treepar)

        self.setGeometry(550, 10, 300, 700)
        self.setWindowTitle('MainWindow')
        self.btnGen.clicked.connect(self.on_btnGen)
        
        self.threadAqc = None

    def on_pars_changed(self, param, changes):
        print("tree changes:")
        for param, change, data in changes:
            path = self.Parameters.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
        print('  parameter: %s'% childName)
        print('  change:    %s'% change)
        print('  data:      %s'% str(data))
        print('  ----------')

    def on_btnGen(self):
        print('h')
        if self.threadAqc is None:
            GenKwargs = self.NifGenParams.GetParams()
            print(GenKwargs)            
            self.threadAqc = FMacq.DataAcquisitionThread(**GenKwargs)
#            self.threadAqc.NewData.connect(self.on_NewSample)
#            self.threadGen.start()
#
#            self.btnGen.setText("Stop Gen")
#            self.OldTime = time.time()
        else:
            self.threadAqc.NewData.disconnect()
            self.threadAqc.terminate()
            self.threadAqc = None
            self.btnGen.setText("Start Gen")
            
    def on_NewSample(self):
        ''' Visualization of streaming data-WorkThread. '''
        Ts = time.time() - self.OldTime
        self.OldTime = time.time()
#        if self.threadSave is not None:
#            self.threadSave.AddData(self.threadGen.OutData)
#        self.threadPlotter.AddData(self.threadGen.OutData)
#        self.threadPSDPlotter.AddData(self.threadGen.OutData)
        print('Sample time', Ts)


if __name__ == '__main__':
    app = Qt.QApplication([])
    mw  = MainWindow()
    mw.show()
    app.exec_()        
        