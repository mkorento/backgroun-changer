#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ctypes
import win32api
import win32con
import win32gui_struct
from win32process import DETACHED_PROCESS
import subprocess

try:
    import winxpgui as win32gui
except ImportError:
    import win32gui

class Client(object):
    def __init__(self):
        self.current_dir = sys.argv[0]
        self.current_dir = "\\".join(self.current_dir.split('\\')[:-1])
        self.image_dir = self.current_dir + "\\images\\"

        self.wallpapers = os.listdir(self.image_dir)
        self.current_wallpaper = ''
        self.wallpaper_i = 0

        f = open(self.current_dir + '\\config\\running.txt', 'w')
        f.write('False')
        f.close()

        if not os.path.exists(self.current_dir + '\\config\\subreddits.txt'):
            sys.exit(1)

        self.subprocess = None

        self.start_subprocess()

    def start_subprocess(self, forced=False):

        if forced:
            self.subprocess = subprocess.Popen(['python.exe', "\\".join(sys.argv[0].split('\\')[:-1]) + '\\server.py', '--force'], creationflags=DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)
        else:
            self.subprocess = subprocess.Popen(['python.exe', "\\".join(sys.argv[0].split('\\')[:-1]) + '\\server.py'], creationflags=DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)


    def kill_subprocess(self, SysTrayIcon=None):
        # win32api.TerminateProcess(int(self.subprocess._handle), -1)
        ctypes.windll.kernel32.TerminateProcess(int(self.subprocess._handle), -1)

    def download_images(self, SysTrayIcon):
        if self.download_running():
            SysTrayIcon.icon = "icons\icon_busy.ico"
            SysTrayIcon.refresh_icon()
            return

        self.kill_subprocess()
        self.start_subprocess(True)
        SysTrayIcon.icon = "icons\icon_busy.ico"
        SysTrayIcon.refresh_icon()

    def update_wallpapers(self):
        self.wallpapers = os.listdir(self.image_dir)
        if len(self.wallpapers) > 0:
            self.current_wallpaper = self.wallpapers[0]
            self.wallpaper_i = 0
        else:
            self.current_wallpaper = ''

    def download_running(self):
        f = open(self.current_dir + '\\config\\running.txt', 'r')
        running = f.read()
        f.close()
        return running == 'True'

    def needing_update(self):
        return self.wallpapers != os.listdir(self.image_dir)

    def next_background(self, SysTrayIcon):

        if self.download_running():
            SysTrayIcon.icon = "icons\icon_busy.ico"
            SysTrayIcon.refresh_icon()
            return

        if self.needing_update():

            SysTrayIcon.icon = "icons\icon_ready.ico"
            SysTrayIcon.refresh_icon()
            self.update_wallpapers()

        if len(self.wallpapers) > 0:
            if len(self.current_wallpaper) == 0:

                self.set_background(self.wallpapers[0])
                self.wallpaper_i = 0
            else:

                self.wallpaper_i += 1
                if self.wallpaper_i == len(self.wallpapers):
                    self.wallpaper_i = 0
                self.set_background(self.wallpapers[self.wallpaper_i])

    def previous_background(self, SysTrayIcon):

        if self.download_running():
            SysTrayIcon.icon = "icons\icon_busy.ico"
            SysTrayIcon.refresh_icon()
            return

        if self.needing_update():
            self.update_wallpapers()
            SysTrayIcon.icon = "icons\icon_ready.ico"
            SysTrayIcon.refresh_icon()

        if len(self.wallpapers) > 0:
            if len(self.current_wallpaper) == 0:
                self.set_background(self.wallpapers[0])
                self.wallpaper_i = 0
            else:
                self.wallpaper_i -= 1
                if self.wallpaper_i < 0:
                    self.wallpaper_i = len(self.wallpapers)-1
                self.set_background(self.wallpapers[self.wallpaper_i])

    def set_background(self, image):
        image_path = os.path.join(self.image_dir, image)
        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, image_path, 3)
        self.current_wallpaper = image

class SysTrayIcon(object):
    QUIT = 'QUIT'
    SPECIAL_ACTIONS = [QUIT]

    FIRST_ID = 1023

    def __init__(self,
                 icon,
                 hover_text,
                 menu_options,
                 on_quit=None,
                 default_menu_index=None,
                 window_class_name=None,):

        self.icon = icon
        self.hover_text = hover_text
        self.on_quit = on_quit

        menu_options = menu_options + (('Exit', None, self.QUIT),)
        self._next_action_id = self.FIRST_ID
        self.menu_actions_by_id = set()
        self.menu_options = self._add_ids_to_menu_options(list(menu_options))
        self.menu_actions_by_id = dict(self.menu_actions_by_id)
        del self._next_action_id

        self.default_menu_index = (default_menu_index or 0)
        self.window_class_name = window_class_name or "SysTrayIconPy"

        message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
                       win32con.WM_DESTROY: self.destroy,
                       win32con.WM_COMMAND: self.command,
                       win32con.WM_USER+20 : self.notify,}

        # Register the Window class.
        window_class = win32gui.WNDCLASS()
        hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
        window_class.lpszClassName = self.window_class_name
        window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        window_class.hbrBackground = win32con.COLOR_WINDOW
        window_class.lpfnWndProc = message_map # could also specify a wndproc.
        classAtom = win32gui.RegisterClass(window_class)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom,
                                          self.window_class_name,
                                          style,
                                          0,
                                          0,
                                          win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT,
                                          0,
                                          0,
                                          hinst,
                                          None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()

        win32gui.PumpMessages()

    def _add_ids_to_menu_options(self, menu_options):
        result = []
        for menu_option in menu_options:
            option_text, option_icon, option_action = menu_option
            if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
                self.menu_actions_by_id.add((self._next_action_id, option_action))
                result.append(menu_option + (self._next_action_id,))
            elif non_string_iterable(option_action):
                result.append((option_text,
                               option_icon,
                               self._add_ids_to_menu_options(option_action),
                               self._next_action_id))
            else:
                print 'Unknown item', option_text, option_icon, option_action
            self._next_action_id += 1
        return result

    def refresh_icon(self):
        # Try and find a custom icon
        hinst = win32gui.GetModuleHandle(None)
        if os.path.isfile(self.icon):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst,
                                       self.icon,
                                       win32con.IMAGE_ICON,
                                       0,
                                       0,
                                       icon_flags)
        else:
            print "Can't find icon file - using default."
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        if self.notify_id: message = win32gui.NIM_MODIFY
        else: message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd,
                          0,
                          win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                          win32con.WM_USER+20,
                          hicon,
                          self.hover_text)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def restart(self, hwnd, msg, wparam, lparam):
        self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
        if self.on_quit:self.on_quit(self)

        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam==win32con.WM_LBUTTONDBLCLK:
            self.execute_menu_option(self.default_menu_index + self.FIRST_ID)
        elif lparam==win32con.WM_RBUTTONUP:
            self.show_menu()
        elif lparam==win32con.WM_LBUTTONUP:
            self.show_menu()
        return True

    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        self.create_menu(menu, self.menu_options)
        #win32gui.SetMenuDefaultItem(menu, 1000, 0)

        pos = win32gui.GetCursorPos()
        # See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
        # TODO: tässä kohtaa tulee joku bugi joskus?
        # kun rämppää hiirtä siinä iconin päällä
        win32gui.SetForegroundWindow(self.hwnd)
        # pywintypes.error: (0, 'SetForegroundWindow, 'No error message is available')
        win32gui.TrackPopupMenu(menu,
                                win32con.TPM_LEFTALIGN,
                                pos[0],
                                pos[1],
                                0,
                                self.hwnd,
                                None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def create_menu(self, menu, menu_options):
        for option_text, option_icon, option_action, option_id in menu_options[::-1]:
            if option_icon:
                option_icon = self.prep_menu_icon(option_icon)

            if option_id in self.menu_actions_by_id:                
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                wID=option_id)
                win32gui.InsertMenuItem(menu, 0, 1, item)
            else:
                submenu = win32gui.CreatePopupMenu()
                self.create_menu(submenu, option_action)
                item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
                                                                hbmpItem=option_icon,
                                                                hSubMenu=submenu)
                win32gui.InsertMenuItem(menu, 0, 1, item)

    def prep_menu_icon(self, icon):
        # First load the icon.
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)
        hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

        hdcBitmap = win32gui.CreateCompatibleDC(0)
        hdcScreen = win32gui.GetDC(0)
        hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
        hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
        # Fill the background.
        brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
        win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
        # unclear if brush needs to be feed.  Best clue I can find is:
        # "GetSysColorBrush returns a cached brush instead of allocating a new
        # one." - implies no DeleteObject
        # draw the icon
        win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        win32gui.SelectObject(hdcBitmap, hbmOld)
        win32gui.DeleteDC(hdcBitmap)

        return hbm

    def command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        self.execute_menu_option(id)

    def execute_menu_option(self, id):
        menu_action = self.menu_actions_by_id[id]
        if menu_action == self.QUIT:
            win32gui.DestroyWindow(self.hwnd)
        else:
            menu_action(self)

def non_string_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return not isinstance(obj, basestring)

if __name__ == '__main__':

    hover_text = "Background changer"
    icon = "icons\icon_ready.ico"
    client = Client()

    menu_options = (('Next', None, client.next_background),
                    ('Previous', None, client.previous_background),
                    ('Download images', None, client.download_images))

    SysTrayIcon(icon, hover_text, menu_options, on_quit=client.kill_subprocess, default_menu_index=1)
