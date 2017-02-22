import os
import threading

class RawCaptureThread(threading.Thread):
    def __init__(self, freq, sample_rate, output_file):
        super(RawCaptureThread, self).__init__()
        self._stop = threading.Event()
        self.freq = freq
        self.sample_rate = sample_rate
        self.output_file = output_file

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        os.system("python ../../rawcapture/rawcapture.py -f "+ str(self.freq) +"  -s "+ str(self.sample_rate) +" -o "+ self.output_file +"")