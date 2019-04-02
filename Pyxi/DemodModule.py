# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 12:45:22 2019

@author: Lucia
"""
from PyQt5 import Qt
from scipy import signal
import numpy as np

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

def Demod(SigIn, Fs, Fc, DownFact):
    step = 2*np.pi*((Fc)/Fs)
    vcoi = np.exp(1j*(step*range(SigIn.size)))
    rdem = np.real(vcoi*SigIn)
    idem = np.imag(vcoi*SigIn)
    
    FiltR = Filter(Fs, Fc, 'lp', 2)
    FiltI = Filter(Fs, Fc, 'lp', 2)
    
    FilterRPart = FiltR.Apply(rdem)
    FilterIPart = FiltI.Apply(idem)

    rdem = signal.resample(FilterRPart, (FilterRPart.shape[0]//DownFact))
    idem = signal.resample(FilterRPart, (FilterIPart.shape[0]//DownFact))
    
    adem = np.sqrt(rdem**2, idem**2)

    filt = Filter(Fs=Fs,
                  Freqs=(Fc-1000, Fc+1000),
                  btype='bandpass',
                  Order=2) 

    Vbp = filt.Apply(SigIn)
    VinH = signal.hilbert(Vbp)
    Err = np.angle(VinH*np.conj(vcoi))
    
    return adem, rdem, idem, Err
class Demodul():
    def __init__(self, Fs, Fc):
        super(Demod, self).__init__()
        self.Fs = Fs
        self.Fc = Fc
        self.FiltR = Filter(Fs, Fc, 'lp', 2)
        self.FiltI = Filter(Fs, Fc, 'lp', 2)
        
    def run(self, SigIn, DownFact):
        step = 2*np.pi*((self.Fc)/self.Fs)
        vcoi = np.exp(1j*(step*range(SigIn.size)))
        rdem = np.real(vcoi*SigIn)
        idem = np.imag(vcoi*SigIn)
        
        FilterRPart = self.FiltR.Apply(rdem)
        FilterIPart = self.FiltI.Apply(idem)

        rdem = signal.resample(FilterRPart, (FilterRPart.shape[0]//DownFact))
        idem = signal.resample(FilterRPart, (FilterIPart.shape[0]//DownFact))
        
        adem = np.sqrt(rdem**2, idem**2)

        filt = Filter(Fs=self.Fs,
                      Freqs=(self.Fc-1000, self.Fc+1000),
                      btype='bandpass',
                      Order=2) 
    
        Vbp = filt.Apply(SigIn)
        VinH = signal.hilbert(Vbp)
        Err = np.angle(VinH*np.conj(vcoi))
        
        return adem, rdem, idem, Err