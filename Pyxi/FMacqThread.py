#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 12:25:45 2019

@author: aguimera
"""

from PyQt5 import Qt
import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np


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

        self.DaqInterface = CoreMod.ChannelsConfig(**ChannelsConfigKW)
        self.DaqInterface.DataEveryNEvent = self.NewData
        self.SampKw = SampKw
        self.AvgIndex = AvgIndex

#        self.MuxBuffer = Buffer(BufferSize=BufferSize,
#                                nChannels=self.DaqInterface.nChannels)
#        self.MuxBuffer = FileMod.FileBuffer()

    def run(self, *args, **kwargs):
        self.DaqInterface.StartAcquisition(**self.SampKw)
        print('Run')
        loop = Qt.QEventLoop()
        loop.exec_()

    def CalcAverage(self, MuxData):
        print('CalcAverage')

#        Avg = np.mean(LinesSorted[:,-2:,:], axis=1)
        return np.mean(MuxData[:, self.AvgIndex:, :], axis=1)

    def NewData(self, aiData, MuxData):
        self.OutData = self.CalcAverage(MuxData)
        self.NewMuxData.emit()
