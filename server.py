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
import imagesize

from logging.handlers import RotatingFileHandler

class Server(object):

    def __init__(self):

        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        self.image_dir = self.current_dir + "\\images\\"
        self.wallpapers = os.listdir(self.image_dir)

        self.headers = { 'User-Agent' : 'linux:mikan_desktop_app:0.0.1' }
        self.pages = []

        with open(self.current_dir + '\\config\\minimum_width.txt', 'r') as f:
            tmp = filter(lambda x: not x.startswith('#'), f.readlines())
            self.minimum_width = int([x.strip('\n') for x in tmp][0])

    def download_images(self):

        logger.debug('download_images')

        with open(self.current_dir + '\\config\\last_completion.txt', 'r') as f:
            completion = f.read()
            if int(time.time())-int(completion) < 60:
                return

        logger.debug('open subreddits.txt')

        pages = []
        with open(self.current_dir + '\\config\\subreddits.txt', 'r') as f:
            pages = filter(lambda x: not x.startswith('#'), f.readlines())
            pages = [x.strip('\n') for x in pages]

        self.pages = pages

        logger.debug("subreddits: %s" % self.pages)

        f = open(self.current_dir + '\\config\\running.txt', 'w')
        f.write('True')
        f.close()

        count = 0

        logger.debug('for i in self.pages')

        for i in self.pages:
            logger.debug('making new request')

            response = requests.get(i + '.json', headers=self.headers, stream=False)
            time.sleep(3)

            if response.status_code == 200:

                logger.debug('response == 200')

                json_response = response.json()

                for i, val in enumerate(json_response['data']['children']):
                    url = val['data']['url']
                    image_title = val['data']['title']
                    response = requests.get(url, headers=self.headers, stream=True)
                    file_type = response.headers['content-type'].split('/')[0]

                    time.sleep(3)

                    if response.status_code == 200 and file_type == "image":
                        logger.debug('response 200 == && image')

                        file_extension = url.split('.')
                        file_extension = "." + file_extension[len(file_extension)-1]

                        logger.debug('drop quotations')

                        # drop all kinds of unicode quotation marks
                        filename = image_title.replace(u'\u2018',
                                '').replace(u'\u2019','').replace(u'\u201c',
                                        '').replace(u'\u201d',
                                                '').replace(u'\u060c',
                                                        '').replace(u'\u2032',
                                                                '')

                        logger.debug('transform unicode')

                        # transform unicode characters into X's
                        filename = ''.join([i if ord(i) < 127 and ord(i) > 31 else 'X' for i in filename])
                        filename = filename.encode('ascii','ignore')

                        logger.debug('replace ascii')

                        filename = filename.replace(" ", "_")
                        filename = filename.translate(None, '@!"#$%&\'()*,/:;<=>[\\]^`{|}~')
                        filename = filename + "_" + os.urandom(1).encode('hex')

                        count += 1
                        try:
                            logger.debug('write image file')
                            with open(self.image_dir + filename + file_extension, 'wb') as f:
                                for chunk in response:
                                    f.write(chunk)

                            leveys, korkeus = imagesize.get(self.image_dir + filename + file_extension)

                            if not (leveys > korkeus and leveys >= self.minimum_width):
                                logger.debug("remove image file (wrong aspect ratio): ")
                                logger.debug("min_width: %d width: %d height: %d" % (self.minimum_width, leveys, korkeus))
                                logger.debug(filename + file_extension)

                                # rm file
                                os.remove(self.image_dir + filename + file_extension)
                                count -= 1

                        except IOError, e:
                            pass

        logger.debug("Löytyi %d uutta taustakuvaa" % count)

        if count > 0:
            logger.debug('count > 0')

            logger.debug('delete_old_wallpaper')
            self.delete_old_wallpapers()

            logger.debug('update_wallpapers')
            self.update_wallpapers()

            logger.debug('set_background')
            self.set_background()

            logger.debug('update_wallpaper_title')
            self.update_wallpaper_title_file()

        with open(self.current_dir + '\\config\\last_completion.txt', 'w') as f:
            f.write('%s' % int(time.time()))

        f = open(self.current_dir + '\\config\\running.txt', 'w')
        f.write('False')
        f.close()

        logger.debug('complete!')

    def update_wallpapers(self):
        self.wallpapers = os.listdir(self.image_dir)

    def update_wallpaper_title_file(self):
        if len(self.wallpapers) > 0:
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
    log_file = os.path.dirname(os.path.realpath(__file__)) + '\\log.txt'

    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.DEBUG)

    # add a rotating handler
    handler = RotatingFileHandler(log_file, mode='a', maxBytes=1000000, backupCount=2)
    logger.addHandler(handler)

    try:
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

    except Exception:
        logger.exception('EXCEPTION')
        raise
