#!/usr/bin/env python
# This module contains the functions used to demodulate raw RF files
# in I-Q format. These functions use the gnuradio libraries to tune
# to the signal, then filter and demodulate it. 
#
# Each class below with the suffix "_flowgraph" contains all of the
# gnuradio blocks required to process the I-Q data to a digital baseband
# waveform. This baseband waveform is output to a file

from gnuradio import gr
from gnuradio import analog

from gnuradio import blocks
from gnuradio import digital
#from gnuradio import eng_notation
from gnuradio import filter
#from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from math import pi

##############################################################
# This flowgraph consists of the following blocks:
# - a File Source that 
# - a Frequency Translating FIR filter that tunes to the target signal
# - a Complex to Mag block that demodules the OOK signal
# - an Add Const block that shifts the demodulated signal downwards, centering
#   it around zero on the y-axis
# - a Binary Slicer that converts centered signal from floating point to binary
# - a File Sink that outputs 
class ook_flowgraph(gr.top_block):
    def __init__(self, samp_rate_in, samp_rate_out, center_freq, 
                 tune_freq, channel_width, transition_width, threshold,
                 iq_filename, dig_out_filename):
        gr.top_block.__init__(self)

        
        ##################################################
        # Variables
        ##################################################
        self.cutoff_freq = channel_width/2
        self.firdes_taps = firdes.low_pass(1, samp_rate_in, 
                                           self.cutoff_freq, 
                                           transition_width)
        
        ##################################################
        # Blocks
        ##################################################
        self.tuning_filter_0 = filter.freq_xlating_fir_filter_ccc(int(samp_rate_in/samp_rate_out), 
                                                                  (self.firdes_taps), 
                                                                  tune_freq-center_freq, 
                                                                  samp_rate_in)
        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, iq_filename, False)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)
        self.blocks_add_const_vxx_0 = blocks.add_const_vff((-1*threshold, ))

        # message sink is primary method of getting baseband data into waveconverter        
        self.sink_queue = gr.msg_queue()
        self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*1, self.sink_queue, False)
        
        # if directed, we also dump the baseband data into a file
        if len(dig_out_filename) > 0:
            print "Outputing baseband to waveform to " + dig_out_filename
            self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, dig_out_filename, False)
            self.blocks_file_sink_0.set_unbuffered(False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_add_const_vxx_0, 0), (self.digital_binary_slicer_fb_0, 0))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_add_const_vxx_0, 0))
        self.connect((self.blocks_file_source_0, 0), (self.tuning_filter_0, 0))
        self.connect((self.tuning_filter_0, 0), (self.blocks_complex_to_mag_0, 0))

        self.connect((self.digital_binary_slicer_fb_0, 0), (self.blocks_message_sink_0, 0))
        if len(dig_out_filename) > 0:
            self.connect((self.digital_binary_slicer_fb_0, 0), (self.blocks_file_sink_0, 0))


##############################################################
# This flowgraph consists of the following blocks:
# - a File Source that 
# - a Frequency Translating FIR filter that tunes to the target signal
# - a quadrature demod block that demodules the FSK signal
# - an Add Const block that shifts the demodulated signal downwards, centering
#   it around zero on the y-axis
# - a Binary Slicer that converts centered signal from floating point to binary
# - a File Sink that outputs 

class fsk_flowgraph(gr.top_block):
    def __init__(self, samp_rate_in, samp_rate_out, center_freq, 
                 tune_freq, channel_width, transition_width, threshold, fsk_deviation, fskSquelch,
                 iq_filename, dig_out_filename):
        gr.top_block.__init__(self)
        
        ##################################################
        # Variables
        ##################################################
        self.cutoff_freq = channel_width/2
        self.firdes_taps = firdes.low_pass(1, samp_rate_in, 
                                           self.cutoff_freq, 
                                           transition_width)
        
        ##################################################
        # Blocks
        ##################################################
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, iq_filename, False)
        self.blocks_tuning_filter_0 = filter.freq_xlating_fir_filter_ccc(int(samp_rate_in/samp_rate_out), 
                                                                         (self.firdes_taps), 
                                                                         tune_freq-center_freq, 
                                                                         samp_rate_in)
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(fskSquelch, 1, 1, False)
        self.blocks_quadrature_demod_0 = analog.quadrature_demod_cf(samp_rate_out/(2*pi*fsk_deviation/2))
        self.blocks_add_const_vxx_0 = blocks.add_const_vff((-1*threshold, ))
        self.blocks_digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        
        # swapped message sink for file sink
        #self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, dig_out_filename, False)
        #self.blocks_file_sink_0.set_unbuffered(False)
        self.sink_queue = gr.msg_queue()
        self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*1, self.sink_queue, False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.blocks_tuning_filter_0, 0))
        self.connect((self.blocks_tuning_filter_0, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.connect((self.analog_pwr_squelch_xx_0, 0), (self.blocks_quadrature_demod_0, 0))
        self.connect((self.blocks_quadrature_demod_0, 0), (self.blocks_add_const_vxx_0, 0))
        self.connect((self.blocks_add_const_vxx_0, 0), (self.blocks_digital_binary_slicer_fb_0, 0))
        
        #self.connect((self.digital_binary_slicer_fb_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_digital_binary_slicer_fb_0, 0), (self.blocks_message_sink_0, 0))
        