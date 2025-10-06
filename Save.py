# -- coding: utf-8 --

import sys
from ctypes import *
import time
from datetime import datetime
from threading import Thread
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)
import multiprocessing
import threading
sys.path.append("MvImport")
from MvCameraControl_class import *
# import numpy as np
# import cv2
# import base64


# libc = CDLL("libc.so.6")


class CamHolder:
    instance = None  # 实际存储实例
    ready_event = threading.Event()
    image_file_lock = threading.Lock() 
    # 新增：用于通知有新图像可用的事件（可选，但更高效）
    new_image_event = threading.Event() 


HB_format_list = [
    PixelType_Gvsp_HB_Mono8,
    PixelType_Gvsp_HB_Mono10,
    PixelType_Gvsp_HB_Mono10_Packed,
    PixelType_Gvsp_HB_Mono12,
    PixelType_Gvsp_HB_Mono12_Packed,
    PixelType_Gvsp_HB_Mono16,
    PixelType_Gvsp_HB_BayerGR8,
    PixelType_Gvsp_HB_BayerRG8,
    PixelType_Gvsp_HB_BayerGB8,
    PixelType_Gvsp_HB_BayerBG8,
    PixelType_Gvsp_HB_BayerRBGG8,
    PixelType_Gvsp_HB_BayerGR10,
    PixelType_Gvsp_HB_BayerRG10,
    PixelType_Gvsp_HB_BayerGB10,
    PixelType_Gvsp_HB_BayerBG10,
    PixelType_Gvsp_HB_BayerGR12,
    PixelType_Gvsp_HB_BayerRG12,
    PixelType_Gvsp_HB_BayerGB12,
    PixelType_Gvsp_HB_BayerBG12,
    PixelType_Gvsp_HB_BayerGR10_Packed,
    PixelType_Gvsp_HB_BayerRG10_Packed,
    PixelType_Gvsp_HB_BayerGB10_Packed,
    PixelType_Gvsp_HB_BayerBG10_Packed,
    PixelType_Gvsp_HB_BayerGR12_Packed,
    PixelType_Gvsp_HB_BayerRG12_Packed,
    PixelType_Gvsp_HB_BayerGB12_Packed,
    PixelType_Gvsp_HB_BayerBG12_Packed,
    PixelType_Gvsp_HB_YUV422_Packed,
    PixelType_Gvsp_HB_YUV422_YUYV_Packed,
    PixelType_Gvsp_HB_RGB8_Packed,
    PixelType_Gvsp_HB_BGR8_Packed,
    PixelType_Gvsp_HB_RGBA8_Packed,
    PixelType_Gvsp_HB_BGRA8_Packed,
    PixelType_Gvsp_HB_RGB16_Packed,
    PixelType_Gvsp_HB_BGR16_Packed,
    PixelType_Gvsp_HB_RGBA16_Packed,
    PixelType_Gvsp_HB_BGRA16_Packed]

def save_non_raw_image(ip,save_type, frame_info, cam_instance):
    if save_type == 1:
        mv_image_type = MV_Image_Jpeg
        file_path = str(ip)+"/Image_w%d_h%d_fn.jpg" % (
            frame_info.stFrameInfo.nWidth, frame_info.stFrameInfo.nHeight)

    elif save_type == 2:
        mv_image_type = MV_Image_Bmp
        file_path = str(ip)+"/Image_w%d_h%d_fn%d.bmp" % (
            frame_info.stFrameInfo.nWidth, frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nFrameNum)
    elif save_type == 3:
        mv_image_type = MV_Image_Tif
        file_path = str(ip)+"/Image_w%d_h%d_fn%d.tif" % (
            frame_info.stFrameInfo.nWidth, frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nFrameNum)
    else:
        file_path = str(ip)+"/Image_w%d_h%d_fn%d.png" % (
            frame_info.stFrameInfo.nWidth, frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nFrameNum)
        mv_image_type = MV_Image_Png

    c_file_path = file_path.encode('ascii')
    with CamHolder.image_file_lock:
        try:
            #CamHolder.instance.is_saving = True # 设置状态标志
            stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
            stSaveParam.enPixelType = frame_info.stFrameInfo.enPixelType
            stSaveParam.nWidth = frame_info.stFrameInfo.nWidth
            stSaveParam.nHeight = frame_info.stFrameInfo.nHeight
            stSaveParam.nDataLen = frame_info.stFrameInfo.nFrameLen
            stSaveParam.pData = frame_info.pBufAddr
            stSaveParam.enImageType = mv_image_type
            stSaveParam.pcImagePath = create_string_buffer(c_file_path)
            stSaveParam.iMethodValue = 1
            stSaveParam.nQuality = 99
            
            mv_ret = cam_instance.MV_CC_SaveImageToFileEx(stSaveParam)
            
            if mv_ret == 0:
                # 图像保存成功后，设置 new_image_event
                CamHolder.new_image_event.set() 
                print(f"DEBUG: New image saved to {file_path}, new_image_event set.")
            else:
                print(f"DEBUG: Failed to save image with MV_CC_SaveImageToFileEx, ret[0x{mv_ret:x}]")
            return mv_ret
        except Exception as e:
            print(f"Error saving non-raw image: {e}")
            return -1 # 返回一个错误码
        finally:
            #CamHolder.instance.is_saving = False # 清除状态标志
            pass
    # stSaveParam = MV_SAVE_IMAGE_TO_FILE_PARAM_EX()
    # stSaveParam.enPixelType = frame_info.stFrameInfo.enPixelType  # ch:相机对应的像素格式 | en:Camera pixel type
    # stSaveParam.nWidth = frame_info.stFrameInfo.nWidth  # ch:相机对应的宽 | en:Width
    # stSaveParam.nHeight = frame_info.stFrameInfo.nHeight  # ch:相机对应的高 | en:Height
    # stSaveParam.nDataLen = frame_info.stFrameInfo.nFrameLen
    # stSaveParam.pData = frame_info.pBufAddr
    # stSaveParam.enImageType = mv_image_type  # ch:需要保存的图像类型 | en:Image format to save
    # stSaveParam.pcImagePath = create_string_buffer(c_file_path)
    # stSaveParam.iMethodValue = 1
    # stSaveParam.nQuality = 80  # ch: JPG: (50,99], invalid in other format
    # mv_ret = cam_instance.MV_CC_SaveImageToFileEx(stSaveParam)
    # return mv_ret


def save_raw(frame_info, cam_instance):
    if frame_info.stFrameInfo.enPixelType in HB_format_list:

        # ch:解码参数 | en: decode parameters
        stDecodeParam = MV_CC_HB_DECODE_PARAM()
        memset(byref(stDecodeParam), 0, sizeof(stDecodeParam))

        # 获取数据包大小
        stParam = MVCC_INTVALUE()
        memset(byref(stParam), 0, sizeof(stParam))

        ret = cam_instance.MV_CC_GetIntValue("PayloadSize", stParam)
        if 0 != ret:
            print("Get PayloadSize fail! ret[0x%x]" % ret)
            return ret
        nPayloadSize = stParam.nCurValue
        stDecodeParam.pSrcBuf = frame_info.pBufAddr
        stDecodeParam.nSrcLen = frame_info.stFrameInfo.nFrameLen
        stDecodeParam.pDstBuf = (c_ubyte * nPayloadSize)()
        stDecodeParam.nDstBufSize = nPayloadSize
        ret = cam.MV_CC_HBDecode(stDecodeParam)
        if ret != 0:
            print("HB Decode fail! ret[0x%x]" % ret)
            return ret
        else:
            file_path = "Image_w%d_h%d_fn%d.raw" % (stDecodeParam.nWidth, stDecodeParam.nHeight,
                                                    stOutFrame.stFrameInfo.nFrameNum)
            try:
                file_open = open(file_path.encode('ascii'), 'wb+')
                img_save = (c_ubyte * stDecodeParam.nDstBufLen)()
                memmove(byref(img_save), stDecodeParam.pDstBuf, stDecodeParam.nDstBufLen)
                file_open.write(img_save)
            except PermissionError:
                file_open.close()
                print("save error raw file executed failed!")
                return MV_E_OPENFILE
            file_open.close()
    else:
        file_path = "Image_w%d_h%d_fn%d.raw" % (
            frame_info.stFrameInfo.nWidth, frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nFrameNum)
        try:
            file_open = open(file_path.encode('ascii'), 'wb+')
            img_save = (c_ubyte * frame_info.stFrameInfo.nFrameLen)()
            memmove(byref(img_save), frame_info.pBufAddr, frame_info.stFrameInfo.nFrameLen)
            file_open.write(img_save)
        except PermissionError:
            file_open.close()
            print("save error raw file executed failed!")
            return MV_E_OPENFILE
        file_open.close()
    return 0
def get_cam_info():
    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = (MV_GIGE_DEVICE | MV_USB_DEVICE | MV_GENTL_CAMERALINK_DEVICE
                      | MV_GENTL_CXP_DEVICE | MV_GENTL_XOF_DEVICE)
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    if ret != 0:
        print("enum devices fail! ret[0x%x]" % ret)
        sys.exit()

    if deviceList.nDeviceNum == 0:
        print("find no device!")
        sys.exit()

    print("Find %d devices!" % deviceList.nDeviceNum)
    return deviceList

class MvCam():

    def __init__(self,ip):
        if ip !=0:
         
            self.is_saving = False
            self.is_working = True
            self.is_reading = False
            self.cam = MvCamera()
            self.ip = ip
            self.nSaveImageType = 1
            #deviceList = get_cam_info()
            #print(deviceList)
            #self.stDeviceList = cast(deviceList.pDeviceInfo[int(num)], POINTER(MV_CC_DEVICE_INFO)).contents
            self.ip_to_device()
            nip1 = ((self.stDeviceList.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((self.stDeviceList.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((self.stDeviceList.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (self.stDeviceList.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
            self.init_sdk()
            self.open()
            self.set_config()
            pass
        else:
            pass

    def ip_to_device(self):
        deviceList = get_cam_info()
        for i in range(deviceList.nDeviceNum):
            device = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            nip4 = (device.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            if nip4 == self.ip:
                self.stDeviceList = device
                print("找到匹配摄像头")
                break

         

    def init_sdk(self):
        MvCamera.MV_CC_Initialize()
        print("SDK初始化完成")
        pass

    def open(self):
        

        ret = self.cam.MV_CC_CreateHandle(self.stDeviceList)
        if ret != 0:
            raise Exception("create handle fail! ret[0x%x]" % ret)

        # ch:打开设备 | en:Open device
        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            raise Exception("open device fail! ret[0x%x]" % ret)
        print("设备打开成功！")
    def set_config(self):
        # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
        if self.stDeviceList.nTLayerType == MV_GIGE_DEVICE or self.stDeviceList.nTLayerType == MV_GENTL_GIGE_DEVICE:
            nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
            else:
                print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

        # ch:设置触发模式为off | en:Set trigger mode as off
        ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            raise Exception("set trigger mode fail! ret[0x%x]" % ret)
        print("摄像头参数配置完成")
        
        self.stOutFrame = MV_FRAME_OUT()
    def grab_frame(self):
        
        try:
            
            
                ret = self.cam.MV_CC_StartGrabbing()
                print("stat grabbing")
                if ret != 0:
                    raise Exception("start grabbing fail! ret[0x%x]" % ret)
                #stOutFrame = MV_FRAME_OUT()
                memset(byref(self.stOutFrame), 0, sizeof(self.stOutFrame))
                #print("开始取流")
                    
                ret = self.cam.MV_CC_GetImageBuffer(self.stOutFrame, 20000)
                if None != self.stOutFrame.pBufAddr and 0 == ret:
                   
                    # ch:如果图像是HB格式，存raw需要先解码 | en:If save raw,and the image is HB format, should to be decoded first
                    if int(self.nSaveImageType) == 0:
                        ret = save_raw(self.stOutFrame, self.cam)
                    else:
                        # while self.is_reading:
                        #     pass
                        #self.is_saving = True
                        #print(time.time())
                        ret = save_non_raw_image(self.ip,int(self.nSaveImageType), self.stOutFrame, self.cam)
                        #print(time.time())
                        #self.is_saving = False
                    #self.img = convert_img_type(self.stOutFrame, self.cam)
                    if ret != 0:
                        self.cam.MV_CC_FreeImageBuffer(self.stOutFrame)
                        raise Exception("save image fail! ret[0x%x]" % ret)
                    else:
                        print("Save image success!")
                    #binary_data = self.img.tobytes()
                    # self.height = self.stOutFrame.stFrameInfo.nHeight
                    # self.width = self.stOutFrame.stFrameInfo.nWidth
                    # self.channels = 3
                    # #meta_header = f"{height},{width},{channels}|".encode()
                    # binary_data = self.img.tobytes()
                    # # self.base64_data = base64.b64encode(meta_header + binary_data).decode()

                    #将二进制数据编码为 Base64 字符串
                    # self.base64_data = base64.b64encode(binary_data).decode('utf-8')
                    self.cam.MV_CC_FreeImageBuffer(self.stOutFrame)
                    ret = self.cam.MV_CC_StopGrabbing()
                    print("stop grabbing")
                    if ret != 0:
                        raise Exception("stop grabbing fail! ret[0x%x]" % ret)
                    
                    

                   
        except Exception as e:
            print(e)
        finally:
            pass
    
    def close(self):
        # ch:停止取流 | en:Stop grab image
        ret = self.cam.MV_CC_StopGrabbing()
        if ret != 0:
            raise Exception("stop grabbing fail! ret[0x%x]" % ret)

        # ch:关闭设备 | Close device
        ret = self.cam.MV_CC_CloseDevice()
        if ret != 0:
            raise Exception("close device fail! ret[0x%x]" % ret)

        # ch:销毁句柄 | Destroy handle0
        self.cam.MV_CC_DestroyHandle()
    
    def shutdown(self):
        ret = self.cam.MV_CC_CloseDevice()
        if ret != 0:
            raise Exception("close device fail! ret[0x%x]" % ret)
        self.cam.MV_CC_DestroyHandle()

    def uninit_sdk(self):
        MvCamera.MV_CC_Finalize()
# def convert_img_type(frame_info,cam):
#     stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
#     img_buff = None
#     if img_buff is None:
#         img_buff = (c_ubyte * frame_info.stFrameInfo.nFrameLen)()
#     memset(byref(stConvertParam), 0, sizeof(stConvertParam))
#     if IsImageColor(frame_info.stFrameInfo.enPixelType) == 'mono':
#         print("mono!")
#         stConvertParam.enDstPixelType = PixelType_Gvsp_Mono8
#         nConvertSize = frame_info.stFrameInfo.nWidth * frame_info.stFrameInfo.nHeight
#     elif IsImageColor(frame_info.stFrameInfo.enPixelType) == 'color':
#         print("color!")
#         stConvertParam.enDstPixelType = PixelType_Gvsp_BGR8_Packed  # opecv要用BGR，不能使用RGB
#         nConvertSize = frame_info.stFrameInfo.nWidth * frame_info.stFrameInfo.nHeight * 3
#     else:
#         print("not support!!!")
#     stConvertParam.nWidth = frame_info.stFrameInfo.nWidth
#     stConvertParam.nHeight = frame_info.stFrameInfo.nHeight
#     stConvertParam.pSrcData = cast(frame_info.pBufAddr, POINTER(c_ubyte))
#     stConvertParam.nSrcDataLen = frame_info.stFrameInfo.nFrameLen
#     stConvertParam.enSrcPixelType = frame_info.stFrameInfo.enPixelType
#     stConvertParam.pDstBuffer = (c_ubyte * nConvertSize)()
#     stConvertParam.nDstBufferSize = nConvertSize
#     ret = cam.MV_CC_ConvertPixelType(stConvertParam)
#     if ret != 0:
#         print("convert pixel fail! ret[0x%x]" % ret)
#         del stConvertParam.pSrcData
#         sys.exit()
#     else:
#         print("convert ok!!")
#     if IsImageColor(frame_info.stFrameInfo.enPixelType) == 'mono':
#         img_buff = (c_ubyte * stConvertParam.nDstLen)()
#         libc.memcpy(byref(img_buff), stConvertParam.pDstBuffer, stConvertParam.nDstLen)
#         img_buff = np.frombuffer(img_buff,count=int(stConvertParam.nDstLen), dtype=np.uint8)
#         img_buff = img_buff.reshape((frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nWidth))
#         print("mono ok!!")
  
#     # 彩色处理
#     if IsImageColor(frame_info.stFrameInfo.enPixelType) == 'color':
#         img_buff = (c_ubyte * stConvertParam.nDstLen)()
#         libc.memcpy(byref(img_buff), stConvertParam.pDstBuffer, stConvertParam.nDstLen)
#         img_buff = np.frombuffer(img_buff, count=int(stConvertParam.nDstBufferSize), dtype=np.uint8)
#         img_buff = img_buff.reshape(frame_info.stFrameInfo.nHeight, frame_info.stFrameInfo.nWidth, 3)
#         print("color ok!!")
#     return img_buff
     
    


def IsImageColor(enType):
    dates = {
        PixelType_Gvsp_RGB8_Packed: 'color',
        PixelType_Gvsp_BGR8_Packed: 'color',
        PixelType_Gvsp_YUV422_Packed: 'color',
        PixelType_Gvsp_YUV422_YUYV_Packed: 'color',
        PixelType_Gvsp_BayerGR8: 'color',
        PixelType_Gvsp_BayerRG8: 'color',
        PixelType_Gvsp_BayerGB8: 'color',
        PixelType_Gvsp_BayerBG8: 'color',
        PixelType_Gvsp_BayerGB10: 'color',
        PixelType_Gvsp_BayerGB10_Packed: 'color',
        PixelType_Gvsp_BayerBG10: 'color',
        PixelType_Gvsp_BayerBG10_Packed: 'color',
        PixelType_Gvsp_BayerRG10: 'color',
        PixelType_Gvsp_BayerRG10_Packed: 'color',
        PixelType_Gvsp_BayerGR10: 'color',
        PixelType_Gvsp_BayerGR10_Packed: 'color',
        PixelType_Gvsp_BayerGB12: 'color',
        PixelType_Gvsp_BayerGB12_Packed: 'color',
        PixelType_Gvsp_BayerBG12: 'color',
        PixelType_Gvsp_BayerBG12_Packed: 'color',
        PixelType_Gvsp_BayerRG12: 'color',
        PixelType_Gvsp_BayerRG12_Packed: 'color',
        PixelType_Gvsp_BayerGR12: 'color',
        PixelType_Gvsp_BayerGR12_Packed: 'color',
        PixelType_Gvsp_Mono8: 'mono',
        PixelType_Gvsp_Mono10: 'mono',
        PixelType_Gvsp_Mono10_Packed: 'mono',
        PixelType_Gvsp_Mono12: 'mono',
        PixelType_Gvsp_Mono12_Packed: 'mono',
        PixelType_Gvsp_BayerBG8: 'color'}
    return dates.get(enType, '未知')


def main_loop(cam_ip,cam:CamHolder):

    #cam_ip = [41,44]
    # for i in range(len(cam_ip)):
    #     Thread(target=(start_framing),args=(cam_ip[i],cam,)).start()
    print(f"main_loop's cam_holder object ID: {id(cam)}")
    cam_ins = MvCam(cam_ip)
    cam.instance = cam_ins
    cam.ready_event.set()
    print("main_loop 线程: 摄像机实例已赋值，ready_event 已设置。")
    # while cam.instance.is_working:
    #     #print(time.time())
    #     cam.instance.grab_frame()
    #     #print(time.time())
    #     #cam.close()
    #     time.sleep(0.3)
    #     #print(time.time())
    # cam.instance.shutdown()
    # cam.instance.uninit_sdk()
    

def start_framing(cam_ip,cam):
    cam_ins = MvCam(cam_ip)

    while cam.instance.is_working:
        cam.grab_frame()
        #cam.close()
        time.sleep(0.4)
    

if __name__ == "__main__":
    camlist = [0]*4
    
    
    try:
        main_loop(41,cam)

    except Exception as e:
        print(e)
        
    finally:
        # ch:反初始化SDK | en: finalize SDK
        MvCamera.MV_CC_Finalize()
