#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import requests
import json
import os
import ctypes
import time
import sys

class Server(object):
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        self.image_dir = self.current_dir + "\\images\\"
        self.wallpapers = os.listdir(self.image_dir)

        self.headers = { 'User-Agent' : 'linux:mikan_desktop_app:0.0.1' }
        self.pages = []

    def download_images(self):

        with open(self.current_dir + '\\config\\last_completion.txt', 'r') as f:
            completion = f.read()
            if int(time.time())-int(completion) < 60:
                return

        with open(self.current_dir + '\\config\\subreddits.txt', 'r') as f:
            self.pages = filter(None, f.read().strip().split('\n'))

        f = open(self.current_dir + '\\config\\running.txt', 'w')
        f.write('True')
        f.close()

        count = 0

        for i in self.pages:
            response = requests.get(i + '.json', headers=self.headers, stream=False)
            time.sleep(3)

            if response.status_code == 200:
                json_response = response.json()

                for i, val in enumerate(json_response['data']['children']):
                    url = val['data']['url']
                    image_title = val['data']['title']
                    response = requests.get(url, headers=self.headers, stream=True)
                    file_type = response.headers['content-type'].split('/')[0]

                    time.sleep(3)

                    if response.status_code == 200 and file_type == "image":
                        file_extension = url.split('.')
                        file_extension = "." + file_extension[len(file_extension)-1]

                        # drop all kinds of unicode quotation marks
                        filename = image_title.replace(u'\u2018',
                                '').replace(u'\u2019','').replace(u'\u201c',
                                        '').replace(u'\u201d',
                                                '').replace(u'\u060c',
                                                        '').replace(u'\u2032',
                                                                '')

                        # transform unicode characters into X's
                        filename = ''.join([i if ord(i) < 127 and ord(i) > 31 else 'X' for i in filename])
                        filename = filename.encode('ascii','ignore')

                        filename = filename.replace(" ", "_")
                        filename = filename.translate(None, '@!"#$%&\'()*,/:;<=>[\\]^`{|}~')
                        filename = filename + "_" + os.urandom(1).encode('hex')

                        count += 1
                        try:
                            with open(self.image_dir + filename + file_extension, 'wb') as f:
                                for chunk in response:
                                    f.write(chunk)
                        except IOError, e:
                            pass

        if count > 0:
            self.delete_old_wallpapers()
            self.update_wallpapers()
            self.set_background()
            self.update_wallpaper_title_file()

        with open(self.current_dir + '\\config\\last_completion.txt', 'w') as f:
            f.write('%s' % int(time.time()))

        f = open(self.current_dir + '\\config\\running.txt', 'w')
        f.write('False')
        f.close()

    def update_wallpapers(self):
        self.wallpapers = os.listdir(self.image_dir)

    def update_wallpaper_title_file(self):
        with open(self.current_dir + '\\config\\image_title.txt', 'w') as f:
            f.write(self.wallpapers[0])

    def set_background(self):
        if len(self.wallpapers) > 0:
            image_path = os.path.join(self.image_dir, self.wallpapers[0])
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, image_path, 3)

    def delete_old_wallpapers(self):
        for i in self.wallpapers:
            os.remove(self.image_dir + i)

if __name__ == '__main__':

    update_time = 57600
    server = Server()

    try:
        with open(server.current_dir + "\\config\\update_time.txt", 'r') as f:
            user_update_time = int(f.read().strip())

            if user_update_time >= 0 and user_update_time < 86400:
                update_time = user_update_time
    except (IOError, ValueError) as e:
        pass

    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        server.download_images()

    while 1:
        now = datetime.now()
        s_since_midn = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

        if s_since_midn <= update_time:
            time.sleep(update_time-s_since_midn)
        else:
            time.sleep(86400-(s_since_midn-update_time))

        server.download_images()
