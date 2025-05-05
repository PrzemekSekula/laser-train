"""
Mock functions for the client. To be replaced with the actual functions.
"""

from random import randint, random

def send_mask(mask):
    """
    Send a mask to the the laser. Probably an action from the RL perspective.
    """
    print (f"Sending mask: {mask.shape}")

def read_acf(args):
    """
    Read the ACF from the the laser. Probably a state from the RL perspective.
    """
    print (f"Reading ACF")
    
    list1 = [random() for _ in range(10000)]
    list2 = [random() for _ in range(10000)]
    return list1, list2
