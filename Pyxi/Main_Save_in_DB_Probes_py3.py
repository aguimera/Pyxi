# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 23:15:19 2016

@author: aguimera
"""

import matplotlib.pyplot as plt
import gc

import PyGFETdb.DBCore as Pydb
import PyGFETdb.DataStructures as PyFETData
import PyGFETdb.AnalyzeData as PyFETAnalyze
import glob
import pickle


#############################################################################
# Upload files
#############################################################################
#plt.ioff()

#MyDB = PyFETdb.PyFETdb(host='opter6.cnm.es',user='pyfet',passwd='p1-f3t17',db='pyFET')
MyDB = Pydb.PyFETdb(host='opter6.cnm.es',user='pyfet',passwd='p1-f3t17',db='pyFET')

#MyDB = PyFETdb.DBhost
#FileFilter=r'E:\*.h5'
#File = r'C:\Users\Lucia\Dropbox (ICN2 AEMD - GAB GBIO)\PyFET\LuciaScripts\Lucia\DCTests\Resistors\10_09_2019'
##Name = r"\B12708W2-M6-TransistorTest_DC_VgsSweep_8Row_1Col_VcmToGnd_20mV_35kHz_15sec_10sec_1M-Cy0.h5"
#Name = r"\SSP54348-T2-SSP54348-T2-2x2-AMmode_VgsSw_AcSw-Cy0.h5"
#
File = "C:/Users/Lucia/Dropbox (ICN2 AEMD - GAB GBIO)/Neurograph/Test/NewSw/22_10_2020/"
Name = "B13116W2-M1-Vgs_500mV20p_Vds50mV1p-Cy0.h5"
# File = "DAQTests/SweepTests/15_01_20/"
# Name = "testR-R5K-16Chnsdd-Cy0.h5"  
#File = "C:/Users/Lucia/Dropbox (ICN2 AEMD - GAB GBIO)/TeamFolderLMU/FreqMux/Characterization/16092019/"
#Name = "SSP54348-T2-2x2_ACDC_12mV_25mV_postAM_Cy0.h5"

FileFilter = File + Name
FileNames = glob.glob(FileFilter)

Fields = {}
#Fields['User'] = 'EMC'
Fields['User'] = 'LRB'
OptFields = {}
#OptFields['Solution'] = 'Epidural Implant'    
#OptFields['Comments'] = 'CharactTrt_3x3_FDM'
#OptFields['Comments'] = '32chDynamicRange'
OptFields['Comments'] = 'DAQFreqTestWithR5K'
#OptFields['FuncStep'] = 'R=10K'
#OptFields['FuncStep'] = 'NoFilter'
#OptFields['Comments'] = 'Day 64'


#TrtType = {'Name' : 'RW50L50P3CS',
#             'Length':50e-6, 
#             'Width':50e-6,
#             'Pass':3e-6,
#             'Contact':'Flat',
#             'Shape':'Rectangular'}

#TrtType = {'Name' : 'RW500L250P3CS',
#             'Length':250e-6, 
#             'Width':500e-6,
#             'Pass':3e-6,
#             'Contact':'Flat',
#             'Shape':'Rectangular'}

#TrtType = {'Name' : 'HW40L170P0CS',
#             'Length':170e-6,
#             'Width':40e-6,
#             'Pass':0,
#             'Contact':'Flat',
#             'Shape':'Rectangular'}
#
#  B type
#TrtType = {'Name' : 'RW100L50P3CS',
#             'Length':50e-6, 
#             'Width':100e-6,
#             'Pass':3e-6,
#             'Contact':'Flat',
#             'Shape':'Rectangular'}
#==============================================================================
#==============================================================================
#  T type
#TrtType = {'Name' : 'RW80L30P3CS',
#               'Length':30e-6, 
#               'Width':80e-6,
#               'Pass':3e-6,
#               'Contact':'Flat',
#               'Shape':'Rectangular'}
## Q type 
#TrtType = {'Name' : 'RW150L50P3CS',
#             'Length':150e-6, 
#             'Width':150e-6,
#             'Pass':3e-6,
#             'Contact':'Flat',
#             'Shape':'Rectangular'}

## R type 
#TrtType = {'Name' : 'RW100L50P3CS',
#             'Length':100e-6, 
#             'Width':150e-6,
#             'Pass':3e-6,
#             'Contact':'Flat',
#             'Shape':'Rectangular'}
## S type
TrtType = {'Name' : u'RW50L50P3CS',
             'Length':50e-6, 
             'Width':50e-6,
             'Pass':3e-6,
             'Contact':u'Flat',
             'Shape':u'Rectangular'}

#==============================================================================
#==============================================================================



         

GateFields={}

for ifile, filen in enumerate(FileNames):
    
    fName = filen.split('/')[-1]
    fNameP = fName.split('-')
    ##### Naming rules B9355O15-T3-*****.h5
    #####              [0] Wafer                             
    #####                       [1] Device                             
    #####                           [] anything else
    
    print ('Load {} {} of {}'.format(fName, ifile, len(FileNames))) 
    
    Fields['Wafer'] = fNameP[0]
    Fields['Device'] = '{}-{}'.format(Fields['Wafer'],fNameP[1])
    
    print ('Device ', Fields['Device']) 

    ######## Load Data
    try:    
        DevDCVals,DevACVals = PyFETData.LoadDataFromFile(filen)    
    except:
        with open(filen, "rb") as f:
           DevDCVals = pickle.load(f, encoding='latin1')
           DevACVals = pickle.load(f, encoding='latin1')
    PyFETAnalyze.CheckIsOK (DevDCVals,DevACVals, RdsRange = [300,20e3])
    PyFETAnalyze.CalcGM (DevDCVals,DevACVals)

    if DevACVals:
        PyFETAnalyze.InterpolatePSD(DevACVals,Points=100)
        PyFETAnalyze.FitACNoise(DevACVals,Fmin=5, Fmax=1e3)
        PyFETAnalyze.CalcNoiseIrms(DevACVals)    
#        PyFETAnalyze.CalcOptBiasPoint(DevACVals)
    
#    GenReportPDF (DevDCVals,DevACVals,'./Reports/{}'.format(filen.split('/')[-1]))
    
    OptFields['FileName'] = fName

    if 'Gate' in DevDCVals:
        GateFields['User'] = Fields['User']
        GateFields['Name'] = '{}-Gate'.format(Fields['Device'])
        GateFields['FileName'] = fName
        Fields['Gate_id'] = MyDB.InsertGateCharact(DevDCVals['Gate'], GateFields)
    else:
        Fields['Gate_id'] = None

    
    for ch in DevDCVals:        
        if ch=='Gate': continue
    
        Fields['Trt'] = '{}-{}'.format(Fields['Device'],                                       
                                        ch)   
        
        ##### Transistor Type definition          
 
        Fields['TrtType'] = TrtType['Name']
        print ('Trt ', Fields['Trt'], 'Type --> ', Fields['TrtType'] , ' L = ', TrtType['Length'], ' gid ', Fields['Gate_id']) 

        ###### Update DataBase        
        if DevACVals:            
            MyDB.InsertCharact(DCVals = DevDCVals[ch],
                           ACVals = DevACVals[ch],
                           Fields = Fields,
                           OptFields = OptFields,
                           TrtTypeFields = TrtType)
        else:
            MyDB.InsertCharact(DCVals = DevDCVals[ch],
                           ACVals = None,
                           Fields = Fields,
                           OptFields = OptFields,
                           TrtTypeFields = TrtType)
            

del MyDB
print ('Collect -->',gc.collect())
