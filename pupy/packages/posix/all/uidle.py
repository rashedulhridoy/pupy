# -*- encoding: utf-8 -*-

import ctypes
import os
import time

from display import attach_to_display
from ctypes.util import find_library

import psutil

class XScreenSaverInfo( ctypes.Structure):
  _fields_ = [('window',      ctypes.c_ulong), # screen saver window
              ('state',       ctypes.c_int),   # off,on,disabled
              ('kind',        ctypes.c_int),   # blanked,internal,external
              ('since',       ctypes.c_ulong), # milliseconds
              ('idle',        ctypes.c_ulong), # milliseconds
              ('event_mask',  ctypes.c_ulong)] # events

try:
    xlib = ctypes.cdll.LoadLibrary(find_library('X11'))

    XOpenDisplay = xlib.XOpenDisplay
    XOpenDisplay.argtypes = [ ctypes.c_char_p ]
    XOpenDisplay.restype = ctypes.c_void_p

    XDefaultRootWindow = xlib.XDefaultRootWindow
    XDefaultRootWindow.argtypes = [ ctypes.c_void_p ]
    XDefaultRootWindow.restype = ctypes.c_ulong

    XCloseDisplay = xlib.XCloseDisplay
    XCloseDisplay.argtypes = [ ctypes.c_void_p ]
    XCloseDisplay.restype = ctypes.c_int

    XFree = xlib.XFree
    XFree.argtypes = [ ctypes.c_void_p ]
    XFree.restype = ctypes.c_int

except:
    xlib = None

try:
    xss = ctypes.cdll.LoadLibrary('libXss.so.1')

    XScreenSaverAllocInfo = xss.XScreenSaverAllocInfo
    XScreenSaverAllocInfo.restype = ctypes.POINTER(XScreenSaverInfo)

    XScreenSaverQueryInfo = xss.XScreenSaverQueryInfo
    XScreenSaverQueryInfo.argtypes = [
        ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p
    ]
    XScreenSaverQueryInfo.restype.restype = ctypes.c_int
except:
    xss = None

def get_gui_idle(display=':0'):
    if not ( xlib and xss ):
        return None

    if not os.environ.get('DISPLAY'):
        if not attach_to_display(display):
            return None

    display = XOpenDisplay(os.environ.get('DISPLAY') or display)
    if not display:
        return None

    xssinfo = XScreenSaverAllocInfo()
    if not xssinfo:
        XCloseDisplay(display)
        return None
    
    status = XScreenSaverQueryInfo(display, XDefaultRootWindow(display), xssinfo)
    idle = xssinfo.contents.idle

    XFree(xssinfo)
    XCloseDisplay(display)

    return int(idle / 1000)

def get_cli_idle():
    idle = min(
        time.time() - os.stat(
            '/dev/{}'.format(x.terminal)
            ).st_atime for x in psutil.users() if x.terminal)
    psutil._pmap = {}
    return idle

def get_idle():
    cli_idle = get_cli_idle()
    
    try:
        gui_idle = get_gui_idle()
    except:
        gui_idle = None

    if gui_idle is None:
        return cli_idle
    else:
        return min(cli_idle, gui_idle)
