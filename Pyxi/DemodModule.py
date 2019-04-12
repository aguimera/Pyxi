# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 12:45:22 2019

@author: Lucia
"""
from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph.parametertree.Parameter as pParams

from scipy import signal
import numpy as np


DemodulParams = ({'name': 'DemodConfig',
                  'type': 'group',
                  'children': ({'name': 'DemEnable',
                                'title': 'On/Off',
                                'type': 'bool',
                                'value': False},
                               {'name': 'FsDemod',
                                'type': 'float',
                                'value': 2e6,
                                'readonly': True,
                                'siPrefix': True,
                                'suffix': 'Hz'},
                               {'name': 'DSFact',
                                'title': 'DownSampling Factor',
                                'type': 'int',
                                'value': 10},
                               {'name': 'FiltOrder',
                                'title':'Filter Order',
                                'type': 'int',
                                'value': 2}
                              )
                })
                  
class DemodParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChild(DemodulParams)
        self.DemConfig = self.param('DemodConfig')
        self.DemEnable = self.DemConfig.param('DemEnable')
        self.FsDem = self.DemConfig.param('FsDemod')
        self.DSFact = self.DemConfig.param('DSFact')
        self.FiltOrder = self.DemConfig.param('FiltOrder')
    
    def GetParams(self):
        Demod = {}
        for Config in self.DemConfig.children():
            if Config.name() == 'DemEnable':
                continue
            Demod[Config.name()] = Config.value()
        
        return Demod
    
    def GetChannels(self, Rows, Fcs):
        DemChnNames = {}
        i=0
        for r in Rows:
            for col, f in Fcs.items():
                DemChnNames[r+'_'+col]=i
                i=i+1
        return DemChnNames
        
class Filter():
    def __init__(self, Fs, Freqs, btype, Order):
        freqs = np.array(Freqs)/(0.5*Fs)
        self.b, self.a = signal.butter(Order,
                                       freqs,
                                       btype,
                                       )
        self.zi = signal.lfilter_zi(self.b,
                                    self.a,
                                    )

    def Apply(self, Sig):
        sigout, self.zi = signal.lfilter(b=self.b,
                                         a=self.a,
                                         x=Sig,
                                         axis=0,
                                         zi=self.zi
                                         )
        return sigout  


class Demod():
    def __init__(self, Fc, FetchSize, Fs, DownFact, Order):

        self.Fs = Fs
        self.Fc = Fc
        self.DownFact = DownFact
        self.FsOut = Fs/DownFact
        
        self.FiltR = Filter(Fs, self.FsOut/2, 'lp', Order)
        self.FiltI = Filter(Fs, self.FsOut/2, 'lp', Order)

        step = 2*np.pi*(Fc/Fs)
        self.vcoi = np.exp(1j*(step*np.arange(FetchSize)))
        
    def Apply(self, SigIn):    
        rdem = np.real(self.vcoi*SigIn)
        idem = np.imag(self.vcoi*SigIn)
        
        FilterRPart = self.FiltR.Apply(rdem)
        FilterIPart = self.FiltI.Apply(idem)

        sObject = slice(None, None, self.DownFact)
        
        RSrdem = FilterRPart[sObject]
        RSidem = FilterIPart[sObject]
        
        adem = np.sqrt(RSrdem**2, RSidem**2) 
        
        return adem

class DemodThread(Qt.QThread):
    NewData = Qt.pyqtSignal()
    def __init__(self, Fcs, RowList, Fsize, FsDemod, DSFact, FiltOrder):
       super(DemodThread, self).__init__() 
       self.ToDemData = None
       
       self.DemOutputs = []
       for Row in RowList:
           DemOut = []
           for Cols, Freq in Fcs.items():
               Dem = Demod(Freq, Fsize, FsDemod, DSFact, FiltOrder)
               DemOut.append(Dem)
           self.DemOutputs.append(DemOut) 
       self.OutDemData = np.ndarray((int(Fsize/DSFact),int(len(RowList)*len(Fcs.keys()))))
       
    def run(self):       
        while True:
            if self.ToDemData is not None:
                ind = 0
                for ir, rows in enumerate(self.DemOutputs):
                    for instance in rows:
                        data = instance.Apply(self.ToDemData[:, ir])
                        self.OutDemData[:,ind] = data
                        ind = ind+1
#                print('OutDemData', self.OutDemData.shape)
                self.NewData.emit()
                self.ToDemData = None
            else:
                Qt.QThread.msleep(10)
#        #multiprocessing
    def AddData(self, NewData):
        if self.ToDemData is not None:
            print('Error Demod !!!!')
        self.ToDemData = NewData 
        
    def stop (self):
        self.terminate()       
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        