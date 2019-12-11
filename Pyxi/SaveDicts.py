# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 14:37:00 2019

@author: Lucia
"""
import numpy as np
import PyGFETdb.DataStructures as PyData

class SaveDicts():
     PSDSaved = None
     def __init__(self, SwVdsVals, SwVgsVals, Channels, nFFT, FsDemod, Gate=False):
        InChans = []
        self.ChNamesList = sorted(Channels)
        self.ChannelIndex = {}
        index = 0
        for ch in sorted(Channels):
            InChans.append(self.aiChannels[ch])
            self.ChannelIndex[ch] = (index)
         
         # DC dictionaries
        self.DevDCVals = PyData.InitDCRecord(nVds=self.SwVdsVals,
                                             nVgs=self.SwVgsVals,
                                             ChNames=self.ChNamesList,
                                             Gate=Gate)
        # AC dictionaries
        self.PSDnFFT = nFFT
        self.PSDFs = FsDemod
        
        Fpsd = np.fft.rfftfreq(self.PSDnFFT, 1/self.PSDFs)
        nFgm = np.array([])
        self.DevACVals = PyData.InitACRecord(nVds=self.SwVdsVals,
                                             nVgs=self.SwVgsVals,
                                             nFgm=nFgm,
                                             nFpsd=Fpsd,
                                             ChNames=self.ChNamesList)
        
        
     def SaveDCDict(self, Ids):
        for chn, inds in self.ChannelIndex.items():
            self.DevDCVals[chn]['Ids'][self.SwVgsInd,
                                       self.SwVdsInd] = Ids[inds]
   
        print('DCSaved')
        
     def SaveACDict(self, psd, ff):
        for chn, inds in self.ChannelIndex.items():
            self.DevACVals[chn]['PSD']['Vd{}'.format(self.SwVdsInd)][
                    self.SwVgsInd] = psd[:, inds]
            self.DevACVals[chn]['Fpsd'] = ff
        print('ACSaved')
        self.PSDSaved.emit()