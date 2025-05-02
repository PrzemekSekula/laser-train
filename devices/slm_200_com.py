import ctypes
import json
import _slm_win as slm

dll = ctypes.cdll.LoadLibrary('.\SLMFunc.dll')
with open('.\SLM_STATUS.txt') as f:
    data = f.read()
# reconstructing the status data as a dictionary
SLM_states = json.loads(data)


'''USB CONNECTION'''


def SLM_USB_Open_Connection(SLM_number=1):
    """
    Connects with a SLM-200 device via USB and prints out its status.

    :param dNo: device number (1-8), default: 1
    :return: SLM_status
    """

    SLM_number = ctypes.c_int32(SLM_number)
    r_open = dll.SLM_Ctrl_Open(SLM_number)

    if str(r_open) in SLM_states:
        print(f'Open connection: {SLM_states[str(r_open)]}')

    return r_open


def SLM_USB_Read_Status(SLM_number=1):
    """
    Reads and prints out the status of the connected SLM-200 device.

    :param dNo: device number (1-8), default: 1
    :return: SLM_status
    """

    SLM_number = ctypes.c_int32(SLM_number)
    r_status = dll.SLM_Ctrl_ReadSU(SLM_number)

    if str(r_status) in SLM_states:
        print(f'Read status: {SLM_states[str(r_status)]}')

    return r_status


def SLM_USB_Close_Connection(SLM_number=1):
    """
    Closes the USB connection with a SLM-200 device and prints out its status.

    :param dNo: device number (1-8), default: 1
    :return: SLM_status
    """

    SLM_number = ctypes.c_int32(SLM_number)
    r_close = dll.SLM_Ctrl_Close(SLM_number)

    if str(r_close) in SLM_states:
        print(f'Close connection: {SLM_states[str(r_close)]}')

    return r_close


def SLM_Change_Mode(mode, SLM_number):
    """
    Change the connection mode of the SLM-200 device

    :param mode: connection mode, 0:Memory, 1: DVI
    :param dNo: device number (1-8), default: 1
    :return: SLM_status
    """

    SLM_number = ctypes.c_int32(SLM_number)
    r_mode = dll.SLM_Ctrl_WriteVI(SLM_number, mode)

    if str(r_mode) in SLM_states:
        print(f'Close connection: {SLM_states[str(r_mode)]}')

    return r_mode


'''DVI CONNECTION'''


def SLM_DVI_Open_Connection():
    """
    Searches for a SLM via DVI and reads its parameters.

    :return: width: width of the display
             height: height of the display
             display_name: name of the display
             display_number: number of the display
    """

    display_number = 2

    width = ctypes.c_ushort(0)
    height = ctypes.c_ushort(0)
    display_name = ctypes.create_string_buffer(64)

    # Search for a LCOS-SLM
    for display_number in range(2, 8):
        r_open = slm.SLM_Disp_Info2(display_number, width, height, display_name)
        if SLM_states[str(r_open)] == "SLM_OK":
            names = display_name.value.decode('CP1252').split(',')
            if (names[0] in 'LCOS-SLM'):  # 'LCOS-SLM, SOC, 8001, 2018021001'
                print(names, width, height)
                break

    if display_number >= 8:
        print(f'No SLM')
        return

    return (width, height, display_name, display_number)


def SLM_DVI_Initialize_Display(display_number=1):
    """
    Initializes chosen SLM display.

    :param display_number: display number(1, 2, ...), default: 1
    :return: SLM_status
    """

    r_init = slm.SLM_Disp_Open(display_number)

    if str(r_init) in SLM_states:
        print(f'DVI Initialization: {SLM_states[str(r_init)]}')

    return r_init


def SLM_DVI_Close_Connection(display_number=1):
    """
    Closes the connection with chosen SLM display.

    :param display_number: display number (1, 2, ...), default: 1
    :return: SLM_status
    """

    r_close = slm.SLM_Disp_Close(display_number)

    if str(r_close) in SLM_states:
        print(f'Closing DVI connection: {SLM_states[str(r_close)]}')

    return r_close


def SLM_DVI_Display_GrayScale(grayscale, display_number=1, flags=0):
    """
    Draws the entire display with GrayScale input.

    :param grayscale: specify grayscale from 0 to 1023 (0pi - 2pi)
    :param display_number: display number (1, 2, ...), default: 1
    :param flags: use this to change the display method
    :return: SLM_status
    """

    r_disp = slm.SLM_Disp_GrayScale(display_number, flags, grayscale)

    if str(r_disp) in SLM_states:
        print(f'Displaying grayscale: {SLM_states[str(r_disp)]}')

    return r_disp


def SLM_DVI_Display_Data(data, width=1920, height=1200, flags=0, display_number=1):
    """
    Displays array data on the SLM

    :param width: display width value
    :param height: display height value
    :param data: pointer to array of unsigned short data
    :param display_number: number of the display (1, 2, ...), default: 1
    :param flags: use this to change the display method
    :return: SLM_status
    """

    # c = data.ctypes.data_as(ctypes.POINTER((ctypes.c_int*height)*width)).contents
    # r_disp = slm.SLM_Disp_Data(ctypes.c_int32(display_number), ctypes.c_int16(width), ctypes.c_int16(height),\
                               # ctypes.c_int32(flags), ctypes.POINTER(ctypes.c_float(data.astype(float))))

    r_disp = slm.SLM_Disp_Data(display_number, width, height, flags, data)
    #
    # if str(r_disp) in SLM_states:
    #     print(f'Displaying data: {SLM_states[str(r_disp)]}')

    return r_disp


def SLM_DVI_Display_Read_BMP(file_name, d_type, display_number=1, flags=0):
    """
    Display BMP file (Unicode or ANSI) data on the SLM.

    :param file_name: pointer to buffer containing BMP file name
    :param d_type: type of data (unicode or ansi)
    :param display_number: number of the display (1, 2, ...), default: 1
    :param flags: use this to change the display method, default: 0
    :return: SLM_status
    """

    match d_type:
        case 'unicode':
            r_disp = slm.SLM_Disp_ReadBMP(display_number, flags, file_name)
        case 'ansi':
           r_disp = slm.SLM_Disp_ReadBMP_A(display_number, flags, file_name)
        case default:
            raise ValueError(f'No such file type')

    if str(r_disp) in SLM_states:
        print(f'Displaying bmp: {SLM_states[str(r_disp)]}')

    return r_disp


def SLM_Disp_Read_CSV(file_name, d_type, display_number=1, flags=0):
    """
    Display CSV file (Unicode or ANSI) data on the SLM.

    :param file_name: pointer to buffer containing unicode csv file name
    :param d_type: type of data (unicode or ansi)
    :param display_number: number of the display (1, 2, ...), default: 1
    :param flags: use this to change the display method, default: 0
    :return: SLM_status
    """

    match d_type:
        case 'unicode':
            r_disp = slm.SLM_Disp_ReadCSV(display_number, flags, file_name)
        case 'ansi':
            r_disp = slm.SLM_Disp_ReadCSV_A(display_number, flags, file_name)
        case default:
            raise ValueError(f'No such file type')

    if str(r_disp) in SLM_states:
        print(f'Displaying bmp: {SLM_states[str(r_disp)]}')

    return r_disp