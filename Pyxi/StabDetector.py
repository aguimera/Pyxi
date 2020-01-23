# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 11:49:36 2019

@author: Lucia
"""
from PyQt5 import Qt
import numpy as np
from scipy.stats import linregress as lnr

import Pyxi.CalcPSD as PSD
import PyqtTools.SaveDictsModule as SaveDicts


class StbDetThread(Qt.QThread):
    NextVg = Qt.pyqtSignal()

    def __init__(self, VdVals, VgVals, MaxSlope, TimeOut, nChannels,
                 ChnName, PlotterDemodKwargs):
        '''Initialization for Stabilitation Detection Thread
           VdVals: Array. Contains the values to use in the Vd Sweep.
                          [0.1, 0.2]
           VgVals: Array. Contains the values to use in the Vg Sweep
                          [0., -0.1, -0.2, -0.3]
           MaxSlope: float. Specifies the maximum slope permited to consider
                            the system is stabilazed, so the data is correct
                            to be acquired
           TimeOut: float. Specifies the maximum amount of time to wait the
                           signal to achieve MaxSlope, if TimeOut is reached
                           the data is save even it is not stabilazed
           nChannels: int. Number of acquisition channels (rows) active
           ChnName: dictionary. Specifies the name of Row+Column beign
                                processed and its index:
                                {'Ch04Col1': 0,
                                'Ch05Col1': 1,
                                'Ch06Col1': 2}
           PlotterDemodKwargs: dictionary. Contains Demodulation Configuration
                                           an parameters
                                           {'Fs': 5000.0,
                                           'nFFT': 8.0,
                                           'scaling': 'density',
                                           'nAvg': 50 }
        '''
        super(StbDetThread, self).__init__()
        self.ToStabData = None
        self.Stable = False
        self.Datos = None

        self.MaxSlope = MaxSlope
        self.TimeOut = TimeOut

        self.VgIndex = 0
        self.VdIndex = 0

        self.Timer = Qt.QTimer()
        self.Timer.moveToThread(self)
#        print('nchannels', nChannels)
        self.threadCalcPSD = PSD.CalcPSD(nChannels=nChannels,
                                         **PlotterDemodKwargs)
        self.threadCalcPSD.PSDDone.connect(self.on_PSDDone)
        self.SaveDCAC = SaveDicts.SaveDicts(SwVdsVals=VdVals,
                                            SwVgsVals=VgVals,
                                            Channels=ChnName,
                                            nFFT=int(PlotterDemodKwargs['nFFT']),
                                            FsDemod=PlotterDemodKwargs['Fs']
                                            )
        self.SaveDCAC.PSDSaved.connect(self.on_NextVgs)

    def initTimer(self):
        self.Timer.singleShot((self.TimeOut*1000), self.printTime)
        self.Id = self.Timer.timerId()

    def run(self):
        while True:
            if self.ToStabData is not None:

                Data = np.abs(self.ToStabData[:,0])#se mira la estabilización en la priemra row adquirida
                x = np.arange(Data.size)
                self.ptrend = np.polyfit(x, Data, 1)
                trend = np.polyval(self.ptrend, x)

                slope = lnr(x, trend)[0]
                # print('ESTA ES LA PENDIENTE', slope)
                if np.abs(slope) <= self.MaxSlope:

                    self.DCIdCalc()

                self.ToStabData = None

            else:
                Qt.QThread.msleep(10)

    def AddData(self, NewData):
        if self.ToStabData is not None:
            print('Error STAB!!!!')

        if self.Stable is False:
            self.ToStabData = NewData
#            print('SaveDatos')
            self.Datos = self.ToStabData  # se guardan los datos para que no se sobreescriban
        if self.Stable is True:
            self.threadCalcPSD.AddData(NewData)
            
    def printTime(self):
        print('TimeOut')
        self.DCIdCalc()
        
    def DCIdCalc(self):
#        print('DATA STAB')
        # se descoencta el timer
        self.Timer.stop()
        self.Timer.killTimer(self.Id)

        self.ToStabData = None
        # se activa el flag de estable
        self.Stable = True
        # se activa el thread para calcular PSD
        self.threadCalcPSD.start()
        # se obtiene el punto para cada Row
        self.DCIds = np.ndarray((self.Datos.shape[1], 1))
        for ind in range(self.Datos.shape[1]):
            Data = np.abs(self.Datos[:, ind])
            x = np.arange(Data.size)
            self.ptrend = np.polyfit(x, Data, 1)

            self.DCIds[ind] = (self.ptrend[-1])/np.sqrt(2)  # Se toma el ultimo valor
        # print('DCIDS', DCIds)    

    def on_PSDDone(self):
#        print('PSD DONE RECIBED')
        self.freqs = self.threadCalcPSD.ff
        self.PSDdata = self.threadCalcPSD.psd
        # se desactiva el thread para calcular PSD
        self.threadCalcPSD.stop()
        # Se guardan los valores DC
        self.SaveDCAC.SaveDCDict(Ids=self.DCIds,
                                 SwVgsInd=self.VgIndex,
                                 SwVdsInd=self.VdIndex)
        # Se guarda en AC dicts
        self.SaveDCAC.SaveACDict(psd=self.PSDdata,
                                 ff=self.freqs,
                                 SwVgsInd=self.VgIndex,
                                 SwVdsInd=self.VdIndex
                                 )

    def on_NextVgs(self):
        # Y se emite la señal para el siguiente sweep de VG
        # print('NEXTVG EMIT')
        self.Stable = False
        self.NextVg.emit()

    def stop(self):
        self.threadCalcPSD.PSDDone.disconnect()
        self.SaveDCAC.PSDSaved.disconnect()
        self.threadCalcPSD.stop()
        self.terminate()
