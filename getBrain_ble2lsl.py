import asyncio
import logging
import platform
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
import numpy as np
from time import time
from pylsl import StreamInfo, StreamOutlet

DEVICE_NAME = "getBrain_nRF52_NCS_1"
SAMPLE_BYTE_NUMBER = 26
PACKET_SAMPLE_NUMBER = 1

SERVICE_GBDC_UUID = "0000310d-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_GBDC_EEG_UUID = "00004a37-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_GBDC_CTRLCMD_UUID = "00004a31-0000-1000-8000-00805f9b34fb"

ADDRESS = (
    "e0:cb:d1:71:27:5d"
    # "e4:7e:92:f7:15:e3"
    # "f7:0e:d6:5c:7a:6c"
    if platform.system() != "Darwin"
    else "0000310d-0000-1000-8000-00805f9b34fb"
)

last_tm = 0
info = info = StreamInfo('getBrain', 'EEG', 8, 250, 'float32', 'getBrain%s' % ADDRESS)

info.desc().append_child_value("manufacturer", "getBrain")
channels = info.desc().append_child("channels")

for c in ['POz', 'Oz', 'O1', 'O2', 'TP9', 'TP10', 'AF9', 'AF10']:
    channels.append_child("channel") \
        .append_child_value("label", c) \
        .append_child_value("unit", "microvolts") \
        .append_child_value("type", "EEG")
outlet = StreamOutlet(info, 1, 360)

def lsl_process(data, timestamps):
    outlet.push_sample(data, timestamps)

def decode_eeg_packet(packet):
    """Decode eeg data packet"""
    raw_eeg_data = []
    converted_eeg_data = []
    pktIndex = int((packet[1] << 8) | (packet[0] << 0))
    for index in range(8):
            raw_eeg_data.append(np.int32(((0xFF & packet[2 + index * 3 + 0]) << 16) |
                                         ((0xFF & packet[2 + index * 3 + 1]) << 8 ) |
                                         ((0xFF & packet[2 + index * 3 + 2]) << 0 )))
    for cnt in range(8):
            temp_data = raw_eeg_data[cnt]
            if temp_data & 0x00800000 > 0:
                temp_data |= 0xFF000000
            else:
                temp_data &= 0x00FFFFFF
            converted_eeg_data.append(np.float32(np.int32(temp_data) * 0.02235))
    return pktIndex, converted_eeg_data

def handle_eeg_packet(packet):
    global last_tm
    timestamp = time()
    tm, d = decode_eeg_packet(packet)

    # if tm != last_tm + 1:
    #     print("missing sample %d : %d" % (tm, last_tm))
    #     last_tm = tm
    
    lsl_process(d, timestamp)

    pass

def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    """Simple notification handler which prints the data received."""
    handle_eeg_packet(data)
    pass

async def main(address, cmd_char_uuid, eeg_char_uuid):
    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")
        
        # Write Start Command
        nus = client.services.get_service(SERVICE_GBDC_UUID)
        ctrlcmd_char = nus.get_characteristic(CHARACTERISTIC_GBDC_CTRLCMD_UUID)
        await client.write_gatt_char(ctrlcmd_char, b'\x01')

        # Start Receiving Data
        await client.start_notify(eeg_char_uuid, notification_handler)

        while client.is_connected:
            await asyncio.sleep(0.001)
            
        # await client.stop_notify(eeg_char_uuid)
        # await client.write_gatt_char(ctrlcmd_char, b'\x02')

asyncio.run(main(ADDRESS, CHARACTERISTIC_GBDC_CTRLCMD_UUID, CHARACTERISTIC_GBDC_EEG_UUID))
# if __name__ == "__main__":

    