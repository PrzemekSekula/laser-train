"""
Mock functions for the client. To be replaced with the actual functions.
"""

from random import randint

def send_mask(mask):
    """
    Send a mask to the the laser. Probably an action from the RL perspective.
    """
    print (f"Sending mask: {mask}")

def read_acf(args):
    """
    Read the ACF from the the laser. Probably a state from the RL perspective.
    """
    print (f"Reading ACF")
    return randint(0, 100)
