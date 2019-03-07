#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 12:25:45 2019

@author: aguimera
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np
import niscope
import nifgen

class SigGen(nifgen.Session):
     def SetArbSignal(self, Carr1, Carr2, offset, Fs):
        self.output_mode = nifgen.OutputMode.ARB
        Handle1 = self.create_waveform(Carr1)
        Handle2 = self.create_waveform(Carr2)
        self.channels[0].configure_arb_waveform(Handle1,gain=1,offset=offset)
        self.channels[1].configure_arb_waveform(Handle2,gain=1,offset=0)
        self.reference_clock_source = nifgen.ReferenceClockSource.PXI_CLOCK
        self.ref_clock_frequency=100e6
        self.clock_mode=nifgen.ClockMode.HIGH_RESOLUTION
        self.arb_sample_rate=Fs/2
        self.start_trigger_type = nifgen.StartTriggerType.DIGITAL_EDGE
        self.digital_edge_start_trigger_source = 'PXI_Trig0'
        self.initiate() #init_adquisitionn   
class SigScope(niscope.Session):
    def GetSignal(self, Fs):
        self.acquisition_type=niscope.AcquisitionType.NORMAL
#        self.channels[1].configure_vertical(range=2.0, coupling=niscope.VerticalCoupling.DC)
        self.channels[0,1,2,3,4,5,6,7].configure_vertical(range=1, coupling=niscope.VerticalCoupling.AC)
        self.channels[0,1,2,3,4,5,6,7].configure_chan_characteristics(1000000, 600000.0)
#        self.resolution = 12 #Id not recognized
#        niscope.Session.resolution 
#        self.binary_sample_width = 32 #ID not recognized
        self.configure_horizontal_timing(min_sample_rate=Fs,
                                         min_num_pts=int(1e3),
                                         ref_position=50.0,
                                         num_records=1,
                                         enforce_realtime=True)
        self.exported_start_trigger_output_terminal = 'PXI_Trig0'
        self.input_clock_source='PXI_Clk'
        self.configure_trigger_software()
        self.initiate()

###############################################################################


class DataAcquisitionThread(Qt.QThread):
    NewMuxData = Qt.pyqtSignal()

    def __init__(self ):
        print ('TMacqThread, DataAcqThread')
        super(DataAcquisitionThread, self).__init__()
        
        PXIGen1 = 'PXI1Slot2'
        PXIGen2 = 'PXI1Slot3'
        OptionsGen = 'Simulate=0,DriverSetup=Model:5413;Channels:0-1;BoardType:PXIe;MemorySize:268435456'
    
        PXIScope = 'PXI1Slot4'
        OptionsScope = {'simulate': False,
                        'driver_setup': {'Model': 'NI PXIe-5105',
                                     'BoardType': 'PXIe',
                                     },
                                     }
        Fs = 2e6
        Ts = 1/Fs
        self.BufferSize = int(5e3)
        t = np.arange(0, Ts*self.BufferSize, Ts)
        Fsig = np.array([1e3, 5e3, 10e3, 50e3])
        Sig0=1*np.sin(2*np.pi*Fsig[0]*t)
        Sig1=1*np.sin(2*np.pi*Fsig[1]*t)
        Sig2=1*np.sin(2*np.pi*Fsig[2]*t)
        Sig3=1*np.sin(2*np.pi*Fsig[3]*t)
        
        self.NifGen = SigGen(resource_name=PXIGen1, 
                             options=OptionsGen)
        self.NifGen2 = SigGen(resource_name=PXIGen2, 
                             options=OptionsGen)
        self.NiScope = SigScope(resource_name=PXIScope,
                                options=OptionsScope)
        self.NifGen.SetArbSignal(Sig0, Sig1)
        self.NifGen2.SetArbSignal(Sig2, Sig3)
        self.NiScope.GetSignal(Fs) 
        self.PyXI.DataEveryNEvent = self.NewData
#        self.SampKw = SampKw
#        self.AvgIndex = AvgIndex

#        self.MuxBuffer = Buffer(BufferSize=BufferSize,
#                                nChannels=self.DaqInterface.nChannels)
#        self.MuxBuffer = FileMod.FileBuffer()

    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(**self.SampKw)
        print('Run')
        Inputs = self.NiScope.channels[0,1,2,3].fetch(num_samples=self.BufferSize,
                                                      relative_to=niscope.FetchRelativeTo.READ_POINTER,
                                                      offset=0,
                                                      record_number=0,
                                                      num_records=1,
                                                      timeout=2)
        value = np.ndarray((self.BufferSize, 4))
        for i, In in enumerate(Inputs):
            InSig = np.array(In.samples)
            value[:, i] = InSig #to do a BufferSize x nChan Matrix
        loop = Qt.QEventLoop()
        loop.exec_()

    def CalcAverage(self, MuxData):
        print('CalcAverage')

#        Avg = np.mean(LinesSorted[:,-2:,:], axis=1)
        return np.mean(MuxData[:, self.AvgIndex:, :], axis=1)

    def NewData(self, aiData, MuxData):
        self.OutData = self.CalcAverage(MuxData)
        self.NewMuxData.emit()
