from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
import numpy as np
from time import time, sleep
from sys import platform

class getBrainlsl:

    def __init__(self, address=None, callback=None, eeg=True, accelero=False,
             giro=False, backend='auto', interface=None, time_func=time,
             name=None):
        """Initialize"""
        self.address = address
        self.name = name
        self.callback = callback
        self.eeg = eeg
        self.accelero = accelero
        self.giro = giro
        self.interface = interface
        self.time_func = time_func

        if backend in ['auto', 'blataan', 'bleak']:
            if backend == 'auto':
                self.backend = 'bleak'
            else:
                self.backend = backend
        else:
            raise(ValueError('Backend must be auto, blataan or bleak'))
    
    def connect(self, interface=None, backend='auto'):
        """Connect to the device"""

        pass