"""
Inspired by https://github.com/CamTosh/instagram-bot-dm
I did not use his code on purpose, but if I did all credit goes to him.
"""

import io
import json
import os
import sys
import re
import time
import random
import uuid
import textwrap
from http.server import BaseHTTPRequestHandler
from typing import List
import dotenv
import pyotp
import string
import codecs
import mimetypes
from PIL import Image, ImageDraw, ImageFont
from requests.api import head
import selenium.common.exceptions
from selenium import webdriver
from instagram_private_api_extensions import media
from selenium.webdriver.remote.webelement import WebElement
import requests as req


class InstaBotServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(
            bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(
            bytes("<p>This is an example web server.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))


class InstaBot:
    def __init__(self, username: str, password: str, two_fa: bool = False):
        self.username = username
        self.password = password
        self.two_fa = two_fa

        self.user_agent = 'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        self.rollout_hash = ''

        # using mobile client
        mobile_emulation = {
            "userAgent": self.user_agent
        }
        options = webdriver.ChromeOptions()
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        self.driver = webdriver.Chrome(options=options)

    def login(self):
        """
        login to instagram
        """

        # goto instagram
        self.driver.get('https://www.instagram.com/accounts/login/')

        # accept cookies
        self._click_button("login: accepting cookies ...",
                           '/html/body/div[3]/div/div/button[1]')

        Helper.random_sleep()

        # insert username and password
        self._send_keys("login: entering username ...",
                        '//input[@name="username"]', self.username)
        self._send_keys("login: entering password ...",
                        '//input[@name="password"]', self.password)
        Helper.random_sleep()
        self._click_button("login: submitting form ...",
                           '//button[@type="submit"]')

        # generate and insert 2fa key
        if self.two_fa:
            Helper.random_sleep()
            totp = pyotp.TOTP(os.getenv('INSTA_SECRET')).now()
            self._send_keys("login: entering 2fa key " + totp +
                            " ...", '//input[@name="verificationCode"]', totp)
            self._click_button(
                "login: submitting 2fa key " + totp + " ...", '//form/div[2]/button')

        Helper.random_sleep()

        self.get_rollout_hash()

    def check_messages(self, message_type='inbox'):
        """
        check messages and create post if certain keywords are found in the message
        """
        if message_type == 'inbox':
            # goto inbox
            self.driver.get('https://www.instagram.com/direct/inbox/')
        elif message_type == 'request':
            # goto requests
            self.driver.get('https://www.instagram.com/direct/requests/')

        Helper.random_sleep()

        # deactivate notifications
        self._click_button(
            "check_messages: disabling notifications ...", '//div[3]/button[2]')

        # deactivate app usage
        self._click_button(
            "check_messages: refusing app usage ...", '//div[5]/button')

        # go through all persons
        persons = self.driver.find_elements_by_xpath(
            '//a[count(div[@aria-labelledby])>0][@href]')
        person_ids: List[str] = [re.findall(
            r'\d+', person.get_attribute('href'))[0] for person in persons]
        for person_id in person_ids:
            self._click_button("check_message: checking messages of " + person_id + " ...",
                               '//a[count(div[@aria-labelledby])>0][@href="/direct/t/{id}"]'.format(id=person_id))

            Helper.random_sleep(1, 3)

            # get all messages of person
            messages: List[WebElement] = self.driver.find_elements_by_xpath(
                '//div[@role="listbox"]//*/span')
            for message in messages:
                # get keywords from file
                with open('keywords.txt', 'r') as f:
                    keywords = [line.strip() for line in f]
                # check if in message.text are certain keywords from list
                if any(keyword in message.text for keyword in keywords):
                    # create image with text
                    Helper.create_image(message.text, name=person_id)
                print(message.text)

            self.driver.back()

    def _click_button(self, message, element):
        # find and click button
        try:
            print(message)
            self.driver.find_element_by_xpath(element).click()
        except selenium.common.exceptions.NoSuchElementException:
            pass

    def _send_keys(self, message, element, text):
        # find input and send keys
        try:
            print(message)
            self.driver.find_element_by_xpath(element).send_keys(text)
        except selenium.common.exceptions.NoSuchElementException:
            pass

    def get_rollout_hash(self):
        """
        get rollout hash from source code
        """
        self.driver.get('https://www.instagram.com/')
        Helper.random_sleep()
        page_source = self.driver.page_source
        rollout_hash = re.findall(r'"rollout_hash":\s*"([^"]+)"', page_source)
        if rollout_hash is not None and len(rollout_hash) > 0:
            self.rollout_hash = rollout_hash[0]
            print("get_rollout_hash: " + self.rollout_hash + " ...")
            return self.rollout_hash
        print("get_rollout_hash: no rollout_hash found ...")
        return None

    def create_post(self, img_id: str):
        # create post on instagram

        print("create_post: starting to add post ...")
        # https://habr.com/ru/post/486714/

        img_path = "images/" + img_id + ".jpg"

        # read binary data from image
        print("create_post: opened img " + img_id + " ...")
        data = open(img_path, "rb").read()
        width, height = Image.open(img_path).size

        cookies = json.dumps(self.driver.get_cookies())

        microseconds: str = str(int(time.time() * 1000))
        instagram_rupload_params = json.dumps(
            {"media_type": 1, "upload_id": microseconds, "upload_media_height": height, "upload_media_width": width})
        headers = {
            "User-agent": self.user_agent,
            "Accept": "*/*",
            'Accept-Encoding': 'gzip, deflate',
            "Content-Type": "image/jpeg",
            "Offset": "0",
            "x-csrftoken": self.driver.get_cookie('csrftoken')['value'],
            "x-entity-name": "fb_uploader_" + microseconds,
            "x-entity-length": str(os.path.getsize(img_path)),
            "x-instagram-ajax": self.rollout_hash,
            "x-ig-app-id": "1217981644879628",
            'x-instagram-rupload-params': instagram_rupload_params,
            "cookie": cookies
        }

        response = req.post('https://www.instagram.com/rupload_igphoto/fb_uploader_' +
                            microseconds, headers=headers, data=data)
        print(response.headers)
        print(response.text)

        headers = {
            "content-type": "application/x-www-form-urlencoded",
            "user-agent": self.user_agent,
            "x-csrftoken": "",
            "x-ig-app-id": "1217981644879628",
            "cookie": cookies
        }

        form_data = {
            "source_type": "library",
            "caption": "Test",
            "upload_id": microseconds,
            "usertags": "Test",
            "custom_accessibility_caption": "Test",
            "disable_comments": "1"
        }

        response = req.post(
            'https://www.instagram.com/create/configure/', headers=headers, files=form_data)
        print(response)

    def automated_mode(self):
        self.check_messages('requests')
        self.check_messages('inbox')

    def __del__(self):
        self.driver.close()


class Helper:

    @ staticmethod
    def random_sleep(min_sleep=3, max_sleep=5):
        # random sleep to make sure that bot is not detected
        sleep_time = random.randint(min_sleep, max_sleep)
        print("random_sleep: sleeping for " + str(sleep_time) + " seconds ...")
        time.sleep(sleep_time)

    @ staticmethod
    def create_image(message, img_id: str = None, post_type='normal'):
        # create image with text using PIL
        background_color = (45, 45, 45)
        normal_post = (251, 154, 111)

        # remove any special characters such as unicode characters from message
        message = Helper.clean_string(message)

        # select color depending on post_type
        if post_type == 'normal':
            text_color = normal_post
        else:
            text_color = (255, 255, 255)

        # create image
        W, H = (1080, 1080)
        img = Image.new(mode='RGB', size=(W, H), color=background_color)
        draw = ImageDraw.Draw(img)

        # set font
        font = ImageFont.truetype(
            "/usr/local/share/fonts/a/Avenir_Book.ttf", size=40)

        # wrap lines
        lines = textwrap.wrap(message, width=40)

        # calculate start of text in image
        # start from middle of image and go back half the line length
        y_text = W / 2 - font.getmetrics()[0] * (len(lines) / 2)

        image_width, image_height = img.size
        # https://stackoverflow.com/a/56205095 thank you https://github.com/franck-dernoncourt
        for line in lines:
            line_width, line_height = font.getsize(line)
            draw.text(((image_width - line_width) / 2, y_text),
                      line, font=font, fill=text_color)
            y_text += line_height

        if img_id is None:
            img_id = str(uuid.uuid4())
        file_name = 'images/' + img_id + '.jpg'
        img.save(file_name)

    @ staticmethod
    def clean_string(string: str):
        # remove linebreaks from string
        string = string.replace('\n', ' ').replace('\r', ' ')
        # remove emojis from string
        string = re.sub(r'[\U0001f600-\U0001f650]', '', string)
        # remove multiple spaces
        string = re.sub(r'\s+', ' ', string)
        print('clean_string: ' + string + ' now clean ...')
        return string


if __name__ == '__main__':
    dotenv.load_dotenv()
    instabot = InstaBot(os.getenv('INSTA_USERNAME'),
                        os.getenv('INSTA_PASSWORD'), True)
    instabot.login()
    instabot.create_post('Forest')
    # instabot.automated_mode()
