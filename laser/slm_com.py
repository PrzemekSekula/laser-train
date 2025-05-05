import slm_200_com as slm
import traceback
import ctypes

slm_h = 1200
slm_w = 1920

def connect():
    try:
        slm_width, slm_height, slm_display_name, slm_display_number = slm.SLM_DVI_Open_Connection()
        slm_status = slm.SLM_DVI_Initialize_Display(display_number=2)
        return (slm_width, slm_height, slm_display_name, slm_display_number)
    except Exception as e:
        traceback.print_exc()

def send_mask(mask):
    c = mask.ctypes.data_as(ctypes.POINTER((ctypes.c_int16 * slm_h) * slm_w)).contents
    slm_status = slm.SLM_DVI_Display_Data(c, slm_w, slm_h, 0, 2)
    print(f'Mask sent.')
    return slm_status