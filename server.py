#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import requests
import json
import os
import ctypes
import time
import sys
import logging

logging.basicConfig(
        filename = os.path.dirname(os.path.realpath(__file__)) + '\\server_log.txt',
        filemode = 'w',
        level = logging.DEBUG,
        format = '%(levelname)-7.7s %(message)s'
        )

class Server(object):
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        self.image_dir = self.current_dir + "\\images\\"
        self.wallpapers = os.listdir(self.image_dir)
        logging.debug('Server: current_dir: %s' % self.current_dir)

        self.headers = { 'User-Agent' : 'linux:mikan_desktop_app:0.0.1' }
        self.pages = []

    def download_images(self):
        logging.debug('download_images')

        with open(self.current_dir + '\\last_completion.txt', 'r') as f:
            completion = f.read()
            if int(time.time())-int(completion) < 60:
                logging.debug('Liian vahan aikaa viime latauksesta')
                return

        with open(self.current_dir + '\\subreddits.txt', 'r') as f:
            self.pages = filter(None, f.read().strip().split('\n'))

        f = open(self.current_dir + '\\running.txt', 'w')
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
                    response = requests.get(url, headers=self.headers, stream=True)
                    file_type = response.headers['content-type'].split('/')[0]

                    logging.debug("%s: %s, file_type: %s" % (i, url, file_type))
                    time.sleep(3)

                    if response.status_code == 200 and file_type == "image":
                        file_extension = url.split('.')
                        file_extension = "." + file_extension[len(file_extension)-1]
                        filename = os.urandom(16).encode('hex')

                        count += 1
                        try:
                            with open(self.image_dir + filename + file_extension, 'wb') as f:
                                for chunk in response:
                                    f.write(chunk)
                        except IOError, e:
                            logging.error(e)

        if count > 0:
            self.delete_old_wallpapers()
            self.update_wallpapers()
            self.set_background()

        logging.debug('Ladattiin %d kpl taustakuvia' % count)

        with open(self.current_dir + '\\last_completion.txt', 'w') as f:
            f.write('%s' % int(time.time()))

        f = open(self.current_dir + '\\running.txt', 'w')
        f.write('False')
        f.close()

    def update_wallpapers(self):
        self.wallpapers = os.listdir(self.image_dir)
        logging.debug('update_wallpapers')
        logging.debug('Taustakuvien lkm: % d' % len(self.wallpapers))

    def set_background(self):
        logging.debug('set_background')
        if len(self.wallpapers) > 0:
            image_path = os.path.join(self.image_dir, self.wallpapers[0])
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, image_path, 3)

    def delete_old_wallpapers(self):
        for i in self.wallpapers:
            os.remove(self.image_dir + i)
            logging.debug('Poistetaan %s' % self.image_dir + i)

if __name__ == '__main__':
    logging.debug('Kaynnistetaan server...')

    # jotain väliltä 0-86399
    # 16:00 = 60s*60m*16 = 57600s
    update_time = 57600
    server = Server()

    try:
        with open(server.current_dir + "\\aika.txt", 'r') as f:
            user_update_time = int(f.read().strip())

            if user_update_time >= 0 and user_update_time < 86400:
                update_time = user_update_time
    except (IOError, ValueError) as e:
        pass

    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        logging.debug('--force')
        server.download_images()

    while 1:
        now = datetime.now()
        s_since_midn = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        logging.debug('s_since_midn: %d' % s_since_midn)
        logging.debug('update_time: %d' % update_time)

        if s_since_midn <= update_time:
            logging.debug('Nukutaan vahan: %d' % (update_time-s_since_midn))
            time.sleep(update_time-s_since_midn)
        else:
            logging.debug('Nukutaan huomiseen %d' % (86400-(s_since_midn-update_time)))
            time.sleep(86400-(s_since_midn-update_time))

        server.download_images()
