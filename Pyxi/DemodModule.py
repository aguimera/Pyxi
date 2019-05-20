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
                                'value': 10},
                               {'name': 'FiltOrder',
                                'title':'Filter Order',
                                'type': 'int',
                                'value': 2},
                               {'name': 'OutType',
                                'title': 'Output Var Type',
                                'type': 'list',
                                'values': ['Real', 'Imag', 'Angle', 'Abs'],
                                'value': 'Abs'}
                              )
                })
                  
class DemodParameters(pTypes.GroupParameter):
    def __init__(self, **kwargs):
        pTypes.GroupParameter.__init__(self, **kwargs)

        self.addChild(DemodulParams)
        self.DemConfig = self.param('DemodConfig')
        self.DemEnable = self.DemConfig.param('DemEnable')
        self.FsDem = self.DemConfig.param('FsDemod')
        self.DSFs = self.DemConfig.param('DSFs')
        self.DSFact = self.DemConfig.param('DSFact')
        self.on_DSFact_changed()
        self.DSFact.sigValueChanged.connect(self.on_DSFact_changed)
        self.FsDem.sigValueChanged.connect(self.on_FsDem_changed)
        self.FiltOrder = self.DemConfig.param('FiltOrder')
        self.OutType = self.DemConfig.param('OutType')
        
    def on_FsDem_changed(self):
        self.on_DSFact_changed()
        
    def on_DSFact_changed(self):
        DSFs = self.FsDem.value()/self.DSFact.value()
        self.DSFs.setValue(DSFs)
        
    def GetParams(self):
        Demod = {}
        for Config in self.DemConfig.children():
            if Config.name() == 'DemEnable':
                continue
            if Config.name() == 'DSFs':
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
        
        complexDem = RSrdem + (RSidem*1j)

        return complexDem

def DemodProc(Iin, Fs, Fc, Samps, DownFact, Order=2):
    dem = Demod(Fs=Fs, 
                Fc=Fc, 
                FetchSize=Samps, 
                DownFact=DownFact, 
                Order=Order)
    DemOut = np.array([])
    for IndDemod in np.arange(0, Iin.size, Samps):  
        SigIn = Iin[IndDemod:(IndDemod+Samps)]
        if not SigIn.size == Samps:
            continue

        Complexdem = dem.Apply(SigIn)
        DemOut = np.append(DemOut, Complexdem)
        
    print(Fc, 'end')
    return DemOut

class DemodThread(Qt.QThread):
    NewData = Qt.pyqtSignal()
    def __init__(self, Fcs, RowList, Fsize, FsDemod, DSFact, FiltOrder,**Keywards):
       super(DemodThread, self).__init__() 
       self.ToDemData = None
       
       self.DemOutputs = []
       for Row in RowList:
           DemOut = []
           for Cols, Freq in Fcs.items():
               Dem = Demod(Freq, Fsize, FsDemod, DSFact, FiltOrder)
               DemOut.append(Dem)
           self.DemOutputs.append(DemOut) 
       self.OutDemData = np.ndarray((round(Fsize/DSFact),round(len(RowList)*len(Fcs.keys()))), dtype=complex)
       
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        