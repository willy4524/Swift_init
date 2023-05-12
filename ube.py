import math
from unittest import result
import serial
import os
import serial.tools.list_ports as list_ports
import esptool as Mesptool
import imaplib

import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkFont
import PIL
from PIL import Image, ImageTk

import threading
import time
import importlib
import sys
import json

import hashlib


# 1. 折叠所有区域代码的快捷： ctrl + k      ctrl + 0
# 2. 展开所有折叠区域代码的快捷：ctrl +k      ctrl + J

# GUI圖形化宣告
window = tk.Tk()
curWidth = 400  # get current width
curHeight = 200  # get current height
scnWidth, scnHeight = window.maxsize()  # get screen width and height
tmpcnf = '%dx%d+%d+%d' % (curWidth, curHeight,
                          (scnWidth-curWidth)/2, (scnHeight-curHeight)/2)
window.title('主機板燒錄 工廠專用')
window.geometry(tmpcnf)
window.maxsize(curWidth, curHeight)
window.configure(background='#daeeff')
# ----

# 共用變數
__version__ = "1.0-dev"

# 0.變更UI


def doLoader_esp_updateUI():
    # 變更按鈕狀態
    loader_btn.configure(text="檢查中")
    loader_btn.configure(bg="yellow")
    loader_btn.configure(fg="black")
    # 判斷燒錄的晶片
    doCheckDeviceConnect_NXP()
    # ----

def doReadHashMD5():
    # 輸入檔案名稱

    #1-6 是ESP  7是 NXP
    filename = ["esp_bin/0x1000-bootloader_dio_80m.bin","esp_bin/0x8000-partitions.bin","esp_bin/0x10000-main.bin","esp_bin/0x610000-audio_basic.bin","esp_bin/0x810000-audio.bin","esp_bin/0xe000-boot_app0.bin","nxp_bin/main_nxp.bin"]
    
    filename_hash = ["66ba7fa3a11e53e48ecfacb231992004","69be2538d170ad52b880f51d4419b5c6","c0e6bb50ac9b1845f2c765124c0df5d0","512a32fcfe71b45176db56849742086f","c5572675d41f2742ce98451eae910034","8d8e32156334f5028367974642198d17","c9527d5e8220148450263cd0f9a41234"]

    m = hashlib.md5()
    
    for i in range(0,7):
        # 讀取檔案內容，計算 MD5 雜湊值
        with open(filename[i], "rb") as f:
            buf = f.read()
            m.update(buf)
            h = m.hexdigest()
            # print(filename[i]+"="+h)
            if h == filename_hash[i] :
                print(filename[i]+" OK")
            else :
                print("檔案被修改過")
                pop_up_failure("檔案損毀無法使用")
                updateUI_Loader_finish()
                break
        


# X.(未使用)取得Port資訊
def get_serial_ports():
    from serial.tools.list_ports import comports
    result = []

    for port, description, hwid in comports():
        if not port:
            continue
        if 'VID:PID' in hwid:
            result.append({
                'port': port,
                'description': description,
                'hwid': hwid
            })
    print("findPort_nxp="+str(result))
    return result
# 1.尋找Port  Silicon Labs CP210x USB USB VID:PID=10C4:EA60


def findPort_nxp():
    print("findPort_nxp 開始")
    # Find first available EiBotBoard by searching USB ports.
    # Return serial port object.
    try:
        from serial.tools.list_ports import comports
    except ImportError:
        return None
    if comports:
        com_ports_list = list(comports())
        ebb_port = None
        result_port = []
        for port in com_ports_list:
            if port[1].startswith("EiBotBoard"):
                ebb_port = port[0]  # Success; EBB found by name match.
                break  # stop searching-- we are done.
        if ebb_port is None:
            for port in com_ports_list:
                if port[2].startswith("USB VID:PID=10C4:EA60"):
                    ebb_port = port[0]  # Success; EBB found by VID/PID match.
                    # break  # stop searching-- we are done.
                    result_port.append(ebb_port)

        # print("result_port="+str(result_port))
        return result_port


# 1.宣告PORT
Port_ESP = ""
Port_NXP = ""
error_ESP = "" #存放錯誤代碼
error_NXP = "" #存放錯誤代碼

# 1.檢查是否連接到ESP和NXP  失敗跳出提示原因: 1.連接少插 2.短路PIN沒插

def doCheckDeviceConnect_NXP():
    global intProgress
    global Port_ESP
    global Port_NXP
    global error_NXP
    Port_ESP = ""
    Port_NXP = ""
    error_NXP = ""

    # ser_list = sorted(ports.device for ports in list_ports.comports())
    result_ = findPort_nxp()  # 只找的到CB 的燒錄晶片
    print("CB ser_list=")
    print(result_)
    # get_serial_ports() # 取得Port資訊
    # print("Gino取得路徑="+str(Mesptool.os.getcwd())) 獲取當前工作資料夾路徑
    if len(result_) > 0:

        for port_ in result_:
            print("確認晶片中..."+str(port_))

            response_json = os.popen(str(os.getcwd())+"/nxp_bin/sdphost.exe  -t 50000 -p "+str(port_)+",115200 -j -- error-status").read()
            print("response_json="+response_json)
            j = json.loads(str(response_json))
            # time.sleep(0.1)
            print("j['status']['value']="+str(j['status']['value']))
            if str(j['status']['value']) == '10004':
                print("未進入燒錄模式")
                error_NXP = "10004"
            else :
                 # 判斷晶片類型
                if j['response'] != []:
                    # NXP
                    print(str(port_)+" 為NXP晶片")
                    time.sleep(0.1)
                    Port_NXP = port_
                    doCheckDeviceConnect_ESP() #接著去尋找 Port_ESP 
                    break
                    # doLoader_nxp_1(port_)

                # else:
                #    # ESP
                #     print("此晶片為ESP")
                #     time.sleep(0.1)
                #     Port_ESP = port_
                #     # doLoader_esp_connect()


        doCheckFinish()

    else:
        print("沒搜尋到設備")
        pop_up_failure("沒搜尋到設備")
        updateUI_Loader_finish()

# 1.2判斷連接到ESP和NXP 狀況

def doCheckDeviceConnect_ESP():
    global intProgress
    global esp
    global Port_ESP
    global Port_NXP
    global error_ESP
    error_ESP = ""
    ser_list = sorted(ports.device for ports in list_ports.comports())
    print("Found %d serial ports" % (len)(ser_list))

    custom_commandline=None
    parser = Mesptool.argparse.ArgumentParser(description='esptool.py v%s - ESP8266 ROM Bootloader Utility' % __version__, prog='esptool')

    parser.add_argument('--chip', '-c',
                        help='Target chip type',
                        choices=['auto', 'esp8266', 'esp32'],
                        default=Mesptool.os.environ.get('esptool_CHIP', 'auto'))
    parser.add_argument(
        '--port', '-p',
        help='Serial port device',
        default=Mesptool.os.environ.get('esptool_PORT', None))
    parser.add_argument(
        '--baud', '-b',
        help='Serial port baud rate used when flashing/reading',
        type=Mesptool.arg_auto_int,
        default=Mesptool.os.environ.get('esptool_BAUD', Mesptool.ESPLoader.ESP_ROM_BAUD))
    parser.add_argument(
        '--before',
        help='What to do before connecting to the chip',
        choices=['default_reset', 'no_reset', 'no_reset_no_sync'],
        default=Mesptool.os.environ.get('esptool_BEFORE', 'default_reset'))
    parser.add_argument(
        '--after', '-a',
        help='What to do after esptool.py is finished',
        choices=['hard_reset', 'soft_reset', 'no_reset'],
        default=Mesptool.os.environ.get('esptool_AFTER', 'hard_reset'))
    parser.add_argument(
        '--no-stub',
        help="Disable launching the flasher stub, only talk to ROM bootloader. Some features will not be available.",
        action='store_true')
    parser.add_argument(
        '--trace', '-t',
        help="Enable trace-level output of esptool.py interactions.",
        action='store_true')
    parser.add_argument(
        '--override-vddsdio',
        help="Override ESP32 VDDSDIO internal voltage regulator (use with care)",
        choices=Mesptool.ESP32ROM.OVERRIDE_VDDSDIO_CHOICES,
        nargs='?')

    initial_baud = 115200
    print("initial_baud ="+str(initial_baud))
    args = parser.parse_args(custom_commandline)
    esp = None

    for each_port in reversed(ser_list):        
        if Port_NXP != each_port:    
            print("Serial port %s" % each_port) 
            try:
                if args.chip == 'auto':
                    print("args.chip == auto")
                    #印出型號 EX Detecting chip type... ESP32
                    # esp = Mesptool.ESPLoader.detect_chip(each_port, initial_baud, args.before, args.trace) 
                    
                    detect_port = Mesptool.ESPLoader(each_port, initial_baud, args.trace)
                    connect_mode= args.before
                    detect_port.connect(connect_mode, 1, detecting=True)
                    try:
                        print('Detecting chip type...', end='')
                        Mesptool.sys.stdout.flush()
                        chip_magic_value = detect_port.read_reg(Mesptool.ESPLoader.CHIP_DETECT_MAGIC_REG_ADDR)
                        for cls in [Mesptool.ESP8266ROM, Mesptool.ESP32ROM]:
                            Mchip_magic_value = ''.join(str(i) for i in cls.CHIP_DETECT_MAGIC_VALUE)
                            ValMchip_magic_value = int(Mchip_magic_value)
                            if chip_magic_value == ValMchip_magic_value:
                                # don't connect a second time
                                inst = cls(detect_port._port, initial_baud, trace_enabled=args.trace)
                                inst._post_connect()
                                print(' %s' % inst.CHIP_NAME, end='')
                                detect_port._port.close()
                                print("each_port="+each_port)
                                Port_ESP = each_port
                                break
                                # # 檢查設備完成 開始清除資料
                                # intProgress = 30    
                                # updateUI_Loader_erasing()
                                # doLoader_esp_erase_flash(each_port)   
                                
                                
                    finally:
                        print('')  # end line
                    
                
                
                else:
                    print("args.chip != auto")
                    chip_class = {
                            'esp8266': Mesptool.ESP8266ROM,
                            'esp32': Mesptool.ESP32ROM,
                        }[args.chip]
                    esp = chip_class(each_port, initial_baud, args.trace)
                    esp.connect(args.before)
                
                break
            
            except (Mesptool.FatalError, OSError) as err:
                    if args.port is not None:
                        raise
                    
                    print("%s failed to connect: %s" % (each_port, err))
                    pop_up_failure("%s failed to connect: %s" % (each_port, err))
                    updateUI_Loader_finish()
                    esp = None 
                    break    


def doCheckFinish():
    global Port_ESP
    global Port_NXP
    global error_ESP
    global error_NXP
    print("Port_ESP="+Port_ESP)
    print("Port_NXP="+Port_NXP)
    strMsg_EspCheckError = "ESP晶片 :\n 1.傳輸線未連接\n 2.短路PIN沒插\n 3.未進入燒錄模式"

    strMsg_NxpCheckError = "NXP晶片 :\n 1.傳輸線未連接\n 2.短路PIN沒插"
    strMsg_NxpCheckError_10004 = "NXP晶片 :\n 未進入燒錄模式"

    if len(Port_NXP) == 0 :
        if error_NXP == '10004':
            print(strMsg_NxpCheckError_10004)
            pop_up_failure(strMsg_NxpCheckError_10004)
            updateUI_Loader_finish()
        else:
            print(strMsg_EspCheckError)
            pop_up_failure(strMsg_NxpCheckError)
            updateUI_Loader_finish()
    else:
        if len(Port_ESP) == 0:
            print(strMsg_NxpCheckError)
            pop_up_failure(strMsg_EspCheckError)
            updateUI_Loader_finish()
        else:
            doLoader_esp_connect()



# 2.開始燒錄ESP 進度條ESP 1~50


# 3.開始燒錄NXP 進度條NXP 51~100



# --- ESP
# 1.檢查設備是否已連接_ESP
def doLoader_esp_connect():
    global intProgress
    global Port_ESP

    custom_commandline = None
    parser = Mesptool.argparse.ArgumentParser(
        description='esptool.py v%s - ESP8266 ROM Bootloader Utility' % __version__, prog='esptool')

    parser.add_argument('--chip', '-c',
                        help='Target chip type',
                        choices=['auto', 'esp8266', 'esp32'],
                        default=Mesptool.os.environ.get('esptool_CHIP', 'auto'))
    parser.add_argument(
        '--port', '-p',
        help='Serial port device',
        default=Mesptool.os.environ.get('esptool_PORT', None))
    parser.add_argument(
        '--baud', '-b',
        help='Serial port baud rate used when flashing/reading',
        type=Mesptool.arg_auto_int,
        default=Mesptool.os.environ.get('esptool_BAUD', Mesptool.ESPLoader.ESP_ROM_BAUD))
    parser.add_argument(
        '--before',
        help='What to do before connecting to the chip',
        choices=['default_reset', 'no_reset', 'no_reset_no_sync'],
        default=Mesptool.os.environ.get('esptool_BEFORE', 'default_reset'))
    parser.add_argument(
        '--after', '-a',
        help='What to do after esptool.py is finished',
        choices=['hard_reset', 'soft_reset', 'no_reset'],
        default=Mesptool.os.environ.get('esptool_AFTER', 'hard_reset'))
    parser.add_argument(
        '--no-stub',
        help="Disable launching the flasher stub, only talk to ROM bootloader. Some features will not be available.",
        action='store_true')
    parser.add_argument(
        '--trace', '-t',
        help="Enable trace-level output of esptool.py interactions.",
        action='store_true')
    parser.add_argument(
        '--override-vddsdio',
        help="Override ESP32 VDDSDIO internal voltage regulator (use with care)",
        choices=Mesptool.ESP32ROM.OVERRIDE_VDDSDIO_CHOICES,
        nargs='?')

    initial_baud = 115200
    print("initial_baud ="+str(initial_baud))
    args = parser.parse_args(custom_commandline)
    esp = None

    print("Port_ESP %s" % Port_ESP)
    try:
        if args.chip == 'auto':
            print("args.chip == auto")
            # 印出型號 EX Detecting chip type... ESP32
            # esp = Mesptool.ESPLoader.detect_chip(Port_ESP, initial_baud, args.before, args.trace)

            detect_port = Mesptool.ESPLoader( Port_ESP, initial_baud, args.trace)
            connect_mode = args.before
            detect_port.connect(connect_mode, 2, detecting=True)
            try:
                 print('Detecting chip type...', end='')
                 Mesptool.sys.stdout.flush()
                 chip_magic_value = detect_port.read_reg(Mesptool.ESPLoader.CHIP_DETECT_MAGIC_REG_ADDR)
                 for cls in [Mesptool.ESP8266ROM, Mesptool.ESP32ROM]:
                    Mchip_magic_value = ''.join(str(i) for i in cls.CHIP_DETECT_MAGIC_VALUE)
                    ValMchip_magic_value = int(Mchip_magic_value)
                    if chip_magic_value == ValMchip_magic_value:
                        # don't connect a second time
                        inst = cls(detect_port._port, initial_baud,trace_enabled=args.trace)
                        inst._post_connect()
                        print(' %s' % inst.CHIP_NAME, end='')
                        detect_port._port.close()
                        print("Port_ESP="+Port_ESP)
                        # 檢查設備完成 開始清除資料
                        intProgress = 5
                        updateUI_Loader_erasing()
                        doLoader_esp_erase_flash(Port_ESP)

            finally:
                print('')  # end line

        else:
            print("args.chip != auto")
            chip_class = {
                    'esp8266': Mesptool.ESP8266ROM,
                    'esp32': Mesptool.ESP32ROM,
                }[args.chip]
            esp = chip_class(Port_ESP, initial_baud, args.trace)
            esp.connect(args.before)

    except (Mesptool.FatalError, OSError) as err:
        if args.port is not None:
            raise

        print("%s failed to connect: %s" % (Port_ESP, err))
        pop_up_failure("%s failed to connect: %s" % (Port_ESP, err))
        updateUI_Loader_finish()
        esp = None




# 2.清除晶片_ESP
def doLoader_esp_erase_flash(port):
    global intProgress
    strOrder_erase = "esptool.py --chip esp32 --port "+port+" erase_flash"
    #1.初始化晶片
    print("晶片初始化...port ="+port)
    Mesptool.os.system(strOrder_erase)
    print("晶片初始化完成")
    intProgress = 10
    updateUI_Loader_writing()
    doLoader_esp_write_flash(port)
# 3.寫入程式_ESP
def doLoader_esp_write_flash(port):
    global intProgress
    Mreturn = 99
    #2.程式燒入晶片
    print("程式燒入晶片...1...") 
    strOrder_1 = " 0x1000 esp_bin/0x1000-bootloader.bin"
    strOrder_2 = " 0x8000 esp_bin/0x8000-partitions.bin"
    strOrder_3 = " 0x10000 esp_bin/0x10000-main.bin"
    strOrder_4 = " 0x610000 esp_bin/0x610000-audio_basic.bin"
    strOrder_5 = " 0x810000 esp_bin/0x810000-audio.bin"
    strOrder_6 = " 0xd000 esp_bin/0xd000-ota_data_initial.bin"
    Mreturn = Mesptool.os.system("esptool.py --port "+port+" --baud 921600 write_flash -fm dio -fs 16MB"+strOrder_1+strOrder_2+strOrder_3+strOrder_4+strOrder_5+strOrder_6)
    if(Mreturn == 0):
        intProgress = 40      
        print("ESP程式燒入晶片完成")  
        doLoader_nxp_1()
    else:
        messagebox.showinfo("ERR", "ESP燒入錯誤")


# --- NXP
# 1.前置動作_NXP_1
def doLoader_nxp_1():
    global intProgress
    global Port_NXP
    port = Port_NXP
    print("前置動作_NXP_1...port ="+port)
    response_ = os.system(str(os.getcwd())+"/nxp_bin/sdphost.exe  -t 50000 -p " + \
                                  port+" -- write-file 0x20208200 "+str(os.getcwd())+"/nxp_bin/ivt_flashloader.bin")
    if response_ == 0:
        print("前置動作_NXP_1成功")
        intProgress = 60
        # updateUI_Loader_writing()
        os.system(str(os.getcwd(
        ))+"/nxp_bin/sdphost.exe  -t 50000 -p "+port+" -- jump-address 0x20208200")
        time.sleep(0.1)
        doLoader_nxp_2(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 2.前置動作_NXP_2
def doLoader_nxp_2(port):
    global intProgress
    print("前置動作_NXP_2...port ="+port)
    response_ = os.system(
        str(os.getcwd())+"/nxp_bin/blhost.exe -p "+port+" -- get-property 1")
    if response_ == 0:
        print("前置動作_NXP_2成功")
        intProgress = 65
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_3_1(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 3.晶片初始檢查_NXP_3_1
def doLoader_nxp_3_1(port):
    global intProgress
    print("晶片初始檢查_NXP_3_1...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -- efuse-read-once 0x5")
    if response_ == 0:
        print("前置動作_NXP_3_1成功")
        intProgress = 70
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_3_2(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 4.晶片初始檢查_NXP_3_2
def doLoader_nxp_3_2(port):
    global intProgress
    print("晶片初始檢查_NXP_3_2...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -- efuse-read-once 0x6")
    if response_ == 0:
        print("前置動作_NXP_3_2成功")
        intProgress = 73
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_3_3(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 5.晶片初始檢查_NXP_3_3
def doLoader_nxp_3_3(port):
    global intProgress
    print("晶片初始檢查_NXP_3_3...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -- efuse-read-once 0x2d")
    if response_ == 0:
        print("前置動作_NXP_3_3成功")
        intProgress = 75
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_4_1(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 6.晶片初始設定_NXP_4_1
def doLoader_nxp_4_1(port):
    global intProgress
    print("晶片初始設定_NXP_4_1...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -- efuse-program-once 6 00000010")
    if response_ == 0:
        print("晶片初始設定_NXP_4 成功")
        intProgress = 80
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_4_2(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 7.晶片初始設定_NXP_4_2
def doLoader_nxp_4_2(port):
    global intProgress
    print("晶片初始設定_NXP_4_2...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -- efuse-read-once 0x6")
    if response_ == 0:
        print("晶片初始設定_NXP_4_2 成功")
        intProgress = 85
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_5_1(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 8.配置FLASH_NXP_5_1
def doLoader_nxp_5_1(port):
    global intProgress
    print("配置FLASH_NXP_5_1...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -j -- fill-memory 0x20202000 4 0xc0000207 word")
    if response_ == 0:
        print("配置FLASH_NXP_5_1 成功")
        intProgress = 86
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_5_2(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 9.配置FLASH_NXP_5_2
def doLoader_nxp_5_2(port):
    global intProgress
    print("配置FLASH_NXP_5_2...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -j  -- configure-memory 9 0x20202000")
    if response_ == 0:
        print("配置FLASH_NXP_5_2 成功")
        intProgress = 88
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_6(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 10.清除FASH_NXP_6
def doLoader_nxp_6(port):
    global intProgress
    print("清除FASH_NXP_6...port ="+port)
    response_ = os.system(str(os.getcwd(
    ))+"/nxp_bin/blhost.exe -p "+port+" -j -- flash-erase-region 1610612736 40960 9")
    if response_ == 0:
        print("清除FASH_NXP_6 成功")
        intProgress = 90
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_8(port)
        # doLoader_nxp_erase_flash(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 11.讀FASH_NXP_7


def doLoader_nxp_7(port):
    global intProgress
    print("讀FASH_NXP_7...port ="+port)
    response_ = os.system(str(os.getcwd())+"/nxp_bin/blhost.exe -p "+port + \
                                  " -j -- read-memory 0x60000000 40960 "+str(os.getcwd())+"/nxp_bin/flexspi.dat")
    if response_ == 0:
        print("讀FASH_NXP_7 成功")
        intProgress = 91
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_7(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 12.寫入FASH_NXP_8


def doLoader_nxp_8(port):
    global intProgress
    print("寫入FASH_NXP_8...port ="+port)
    response_ = os.system(str(os.getcwd())+"/nxp_bin/blhost.exe -p "+port + \
                                  " -j -- write-memory 0x60000000 "+str(os.getcwd())+"/nxp_bin/main_nxp.bin 9")
    if response_ == 0:
        print("寫入FASH_NXP_8 成功")
        intProgress = 55
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_9(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()
# 11.讀FASH_NXP_9


def doLoader_nxp_9(port):
    global intProgress
    print("讀FASH_NXP_9...port ="+port)
    response_ = os.system(str(os.getcwd())+"/nxp_bin/blhost.exe -p "+port + \
                                  " -j -- read-memory 0x60000000 40960 "+str(os.getcwd())+"/nxp_bin/flexspi.dat")
    if response_ == 0:
        print("讀FASH_NXP_9 成功")
        intProgress = 95
        # updateUI_Loader_writing()
        time.sleep(0.1)
        doLoader_nxp_finish(port)
    else:
        print("response_="+str(response_))
        pop_up_failure("response_="+str(response_))
        updateUI_Loader_finish()


# 20.NXP燒錄完成
def doLoader_nxp_finish(port):
    global intProgress
    intProgress = 100
    print("ESP燒錄完成")
    print("NXP燒錄完成")
    pop_up_success()
    updateUI_Loader_finish()


# 提示窗相關
def pop_up_success():
    # 我在這裡設計一個功能，也就是為了彈出視窗所設計的功能
    messagebox.showinfo("Gino_ESPLoader", "燒錄成功")
    # 括號裡面的兩個字串分別代表彈出視窗的標題(title)與要顯示的文字(index)


def pop_up_failure(strMsg):
    global intProgress
    intProgress = 404
    messagebox.showinfo("Gino_ESPLoader","錯誤 : "+strMsg)

def pop_up_Erase():
    messagebox.showinfo("Warning", "請確認ESP是否燒入完成")


# ---更新UI---


def updateUI_Loader_erasing():
    loader_btn.configure(text="初始化晶片中")
    loader_btn.configure(bg="red")
    loader_btn.configure(fg= "black")


def updateUI_Loader_writing():
    loader_btn.configure(text="燒錄中")
    loader_btn.configure(bg="red")
    loader_btn.configure(fg= "black")
# 燒入完成 可以繼續燒入


def updateUI_Loader_finish():
    loader_btn.configure(text="開始燒錄")
    loader_btn.configure(bg="#008EDA")
    loader_btn.configure(fg= "#FFFFFF")
    # 開啟按鈕
    loader_btn.configure(state=tk.NORMAL)


# ---執行續相關---
def testThead2():
    print("停止燒路")


# 開始燒錄流程
one_thread = threading.Thread(target=doLoader_esp_updateUI)
two_thread = threading.Thread(target=testThead2)


def doStartThead_1():
    # 關閉按鈕
    loader_btn.configure(state=tk.DISABLED)
    # 添加一個 thread
    one_thread = threading.Thread(target=doLoader_esp_updateUI)
    one_thread.setDaemon(True)
    # 執行 thread
    one_thread.start()

    # 添加一個 thread
    two_thread = threading.Thread(target=updateUI_Loader_progress)
    two_thread.setDaemon(True)
    # 執行 thread
    two_thread.start()


intProgress_MAX = 100
intProgress = 0  # 目前進度 0~100

# 初始化燒錄進度條


def updateUI_Loader_progress_init():
    global intProgress
    global intProgress_MAX
    # 清空进度条
    fill_line = canvas_progress.create_rectangle(
        1.5, 1.5, 0, 23, width=0, fill="white")
    x = int(500/intProgress_MAX)  # 未知变量，可更改
    n = 1  # 465是矩形填充满的次数
    while n < 500:
        n = n + 1
        # 以矩形的长度作为变量值更新
        canvas_progress.coords(fill_line, (0, 0, n, 60))
        window.update()
        time.sleep(0)  # 时间为0，即飞速清空进度条
     # 目前進度 0
    intProgress = 0

# 更新燒錄進度條


def updateUI_Loader_progress():
    global intProgress
    global intProgress_MAX
    print("更新進度條")
    # 填充进度条
    fill_line = canvas_progress.create_rectangle(
        0, 0, 0, 0, width=0, fill="green")
    print("intProgress_MAX="+str(intProgress_MAX))
    x = int(500/intProgress_MAX)  # 未知变量，可更改
    n = 1  # 465是矩形填充满的次数
    while n < 500:

        if intProgress == 404:
            print("404錯誤=")
            break

        n = x*intProgress
        canvas_progress.coords(fill_line, (0, 0, n, 60))
        window.update()
        # print("n="+str(n))
        # print("/x="+str(x))
        # print("intProgress="+str(intProgress))
        time.sleep(1)  # 控制进度条流动的速度

    # print("進度條完成n="+str(n))
    # print("進度條完成/x="+str(x))
    # print("進度條完成intProgress="+str(intProgress))

    updateUI_Loader_progress_init()


# 定義GUI元件
strBackgroudColor = "#daeeff"
fontStyle_20 = tkFont.Font(family="Lucida Grande", size=20)
fontStyle_16 = tkFont.Font(family="Lucida Grande", size=16)
fontStyle_14 = tkFont.Font(family="Lucida Grande", size=14)
fontStyle_12 = tkFont.Font(family="Lucida Grande", size=12)
# img=Image.open("logo2.jpg")
# img = Image.open('data/logo1.png')
# img = ImageTk.PhotoImage(img)
# imLabel = tk.Label(window, image=img,height = 80, width = 600, bg = strBackgroudColor)
# imLabel.pack(side=tk.TOP, ipadx=0, padx=0, ipady=0, pady=20)


# 創建進度條
canvas_progress = tk.Canvas(window, bg="#FFFFFF", height= 10, width = 100)
canvas_progress.pack(side=tk.TOP, fill='x', ipadx=0, padx=50, ipady=0, pady=20)

# 設定提示文字
lb = tk.Label(canvas_progress, text='燒錄進度: ',font=fontStyle_14, bg=strBackgroudColor )
lb.pack(side=tk.LEFT, ipadx=0, padx=0, ipady=0, pady=0)

# 顯示版本號
lb = tk.Label(window, text='ver:'+__version__,font=fontStyle_12,bg=strBackgroudColor, fg="#000000" )
lb.pack(side=tk.BOTTOM, ipadx=0, padx=0, ipady=0, pady=0)

# 燒錄按鈕
loader_btn = tk.Button(window, text='開始燒錄',font=fontStyle_16, bg = "#008EDA", fg = "#FFFFFF", height = 3, width = 20, command=doStartThead_1)
loader_btn.pack( side = tk.BOTTOM, ipadx=0, padx=20, ipady=0, pady=20)


# loader_btn1 = tk.Button(window, text="停止燒錄",command=doStartThead_StopLoad)
# loader_btn1.pack( side = tk.TOP)
# GUI圖形化 顯示

updateUI_Loader_progress_init()

#檢測BIN檔是否被更改
# doReadHashMD5()

window.mainloop()
