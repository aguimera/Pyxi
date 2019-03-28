# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 08:55:21 2019

@author: aemdlabs
"""

import numpy as np
import pickle

import matplotlib.pyplot as plt
import scipy

def findPeak(PSD, Fsig):
    chs = PSD.keys()

    FirHarm = np.zeros(len(chs))
    SecHarm = np.zeros(len(chs))
    ThiHarm = np.zeros(len(chs))
    
    for ich, ch in enumerate(chs):

        psd = PSD[ch]['psd']
        Fpsd = PSD[ch]['ff']
       
        indicesPeak = np.where( ((Fpsd >= Fsig-Fpsd[0]*3) & (Fpsd<=Fsig+Fpsd[0]*3)))   
        indicesPeak2 = np.where( ((Fpsd >= 2*Fsig-Fpsd[0]*3) & (Fpsd<=2*Fsig+Fpsd[0]*3)))  
        indicesPeak3 = np.where( ((Fpsd >= 3*Fsig-Fpsd[0]*3) & (Fpsd<=3*Fsig+Fpsd[0]*3)))  
        
        IDSpeak = np.sqrt(psd[np.argmax(psd[indicesPeak])+indicesPeak[0][0]]+
                                 psd[np.argmax(psd[indicesPeak])+indicesPeak[0][0]+1]+
                                 psd[np.argmax(psd[indicesPeak])+indicesPeak[0][0]-1])
        IDSpeak2 = np.sqrt(psd[np.argmax(psd[indicesPeak2])+indicesPeak2[0][0]]+
                                 psd[np.argmax(psd[indicesPeak2])+indicesPeak2[0][0]+1]+
                                 psd[np.argmax(psd[indicesPeak2])+indicesPeak2[0][0]-1])
        IDSpeak3 = np.sqrt(psd[np.argmax(psd[indicesPeak3])+indicesPeak3[0][0]]+
                                 psd[np.argmax(psd[indicesPeak3])+indicesPeak3[0][0]+1]+
                                 psd[np.argmax(psd[indicesPeak3])+indicesPeak3[0][0]-1])
            
        FirHarm[ich]= IDSpeak 
        SecHarm[ich] = IDSpeak2
        ThiHarm[ich] = IDSpeak3
    return (FirHarm, SecHarm, ThiHarm)

def integrate(PSD, Fmin, Fmax):
    chs = PSD.keys()
    Irms = np.zeros(len(chs))
    for ich, ch in enumerate(chs):
        psd = PSD[ch]['psd']
        Psd = np.zeros(len(psd))
        for iv in np.arange(len(psd)):
            Psd[iv] = psd[iv] 
        Fpsd = PSD[ch]['ff']
        indices = np.where((Fpsd >= Fmin) & (Fpsd<=Fmax))
        print(indices)
        print(Fpsd[indices])
        print(np.array(Psd[indices]))
        print(np.sqrt(scipy.integrate.cumtrapz(Psd[indices], Fpsd[indices]))[0] )
        Irms[ich] = np.sqrt(scipy.integrate.cumtrapz(Psd[indices], Fpsd[indices]))[0]      
    return Irms 

if __name__ == '__main__':

    with open('exportpsd.pkl', 'rb') as f:
        Data = pickle.load(f)
    
    Data['PsdOut'].keys()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    