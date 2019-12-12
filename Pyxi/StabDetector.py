# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 11:49:36 2019

@author: Lucia
"""
from PyQt5 import Qt
import numpy as np
from scipy.stats import linregress as lnr
import Pyxi.CalcPSD as PSD
import Pyxi.SaveDicts as SaveDicts

class StbDetThread(Qt.QThread):
    NextVg = Qt.pyqtSignal()
    def __init__(self, VdVals, VgVals, MaxSlope, TimeOut, nChannels, PlotterDemodKwargs):
       super(StbDetThread, self).__init__() 
       self.ToStabData = None
       self.Stable = False
       
       self.MaxSlope = MaxSlope
       self.TimeOut = TimeOut
       
       self.Timer = Qt.QTimer()
       self.Timer.moveToThread(self)
       
       self.threadCalcPSD = PSD.CalcPSD(nChannels=nChannels,
                                        **PlotterDemodKwargs)
       self.threadCalcPSD.PSDDone.connect(self.on_PSDDone)
       
       self.SaveDCAC = SaveDicts.SaveDicts(SwVdsVals=VdVals,
                                           SwVgsVals=VgVals,
                                           Channels=nChannels,
                                           nFFT=PlotterDemodKwargs['nFFT'],
                                           FsDemod=PlotterDemodKwargs['Fs']
                                           ) 
       self.SaveDCAC.PSDSaved.connect(self.on_NextVg)
       
    def initTimer(self):
        self.Timer.singleShot(self.TimeOut, self.DCIdCalc)
        
    def run(self):       
        while True:
            if self.ToStabData is not None:
                Data = np.abs(self.ToStabData[:,0])#se mira la estabilización en la priemra row adquirida
                x = np.arange(Data.size)
                self.ptrend = np.polyfit(x, Data, 1)
                trend = np.polyval(self.ptrend, x)
                
                slope = lnr(x, trend)[0] 
                if slope <= self.MaxSlope:
                    #se descoencta el timer 
                    self.Timer.stop()
                    self.Timer.killTimer(self.Id)
                    self.DCIdCalc()
                                        
            else:
                Qt.QThread.msleep(10)

    def AddData(self, NewData):
        if self.ToStabData is not None:
            print('Error!!!!')
        if self.Stable is False:
            self.ToStabData = NewData 
        if self.Stable is True:
            self.threadCalcPSD.AddData(NewData)
    
    def DCIdCalc(self):
        Datos=self.ToStabData #se guardan los datos para que no se sobreescriban
        self.ToStabData = None
        #se activa el flag de estable
        self.Stable = True
        #se activa el thread para calcular PSD
        self.threadCalcPSD.start()
        #se obtiene el punto para cada Row
        for ind in Datos.shape[1]:
            Data = np.abs(Datos[:,ind])
            x = np.arange(Data.size)
            self.ptrend = np.polyfit(x, Data, 1)
                        
            self.DCIds[ind] = (2*self.ptrend[-1])/np.sqrt(2) #Se toma el ultimo valor
        
        #Se guardan los valores DC
        self.SaveDCAC.SaveDCDict(Ids=self.DCIds) #FALTA PASAR INDICES DE SWEEPS
        
    def on_PSDDone(self):
        self.freqs = self.threadCalcPSD.ff
        self.PSDdata = self.threadCalcPSD.psd
        #se desactiva el thread para calcular PSD
        self.threadCalcPSD.stop()
        #Se guarda en AC dicts
        self.SaveDCAC.SaveACDict(psd=self.PSDdata,
                                 ff=self.freqs
                                 )#FALTA PASAR INDICES DE SWEEPS
            
    def on_NextVg(self):
        #Y se emite la señal para el siguiente sweep de VG
        self.NextVg.emit() 
        
    def stop(self):
        self.threadCalcPSD.PSDDone.disconnect()
        self.SaveDCAC.PSDSaved.disconnect()
        self.threadCalcPSD.stop()
        self.terminate()      