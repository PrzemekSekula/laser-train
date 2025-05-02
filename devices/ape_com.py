'''
Communication with APE autocorrelator device
'''

import ape_device
import numpy as np
import traceback
import re
#import matplotlib.pyplot as plt

device_dns_name = "pulsecheck-S09797"
tcp_port = 5025

def separate_acf(buffer):
    even_list = []
    odd_list = []

    for index, element in enumerate(buffer):
        if index % 2 == 0:
            even_list.append(element)
        else:
            odd_list.append(element)

    delay = even_list
    intensity = odd_list

    return delay, intensity

def read_acf(pulseCheck):
    acf_binary_data = bytes(pulseCheck.query("CALCULATE:DATA:ALL?", True))
    acf = np.frombuffer(acf_binary_data, dtype=np.float32)
    delay, intensity = separate_acf(acf)
    return delay, intensity

def disconnect(pulseCheck):
    # Close the TCP connection
    if type(pulseCheck) is not None:
        pulseCheck.disconnect()

def connect(device_dns_name, tcp_port):
    try:
        # Open TCP connection to the device using the APE Device class
        pulseCheck = ape_device.ape_device(device_dns_name, tcp_port)

    except Exception as e:
        traceback.print_exc()

    else:
        try:
            #Read device identification
            idn = pulseCheck.idn()
            print("Device identification: {}\n".format(pulseCheck.idn()))

            # Check if the connected device is a pulseCheckNX, not an older pulseCheck USB
            # (Older devices use different data types and commands)
            if re.findall('(mini|pulselink)', idn.lower()) != []:
                raise Exception(
                    'Error. The specified connection details point to an APE miniUSB or pulseLink USB device.\n'
                    'This script is not compatible with these devices.\n'
                    'Please refer to the pulseCheck_getACF.py script for these devices.')

        except Exception as e:
            traceback.print_exc()

    finally:
        return pulseCheck

'''
pulseCheck = connect(device_dns_name, tcp_port)
delay, acf = read_acf(pulseCheck)
plt.plot(delay, acf)
plt.show()
disconnect(pulseCheck)
'''