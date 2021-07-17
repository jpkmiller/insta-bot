"""
Inspired by https://github.com/CamTosh/instagram-bot-dm
I did not use his code on purpose, but if I did all credit goes to him.
"""

import os
import re
import time
import random
import uuid
import textwrap
# server
from http.server import BaseHTTPRequestHandler
from typing import List

import dotenv
import pyotp
from PIL import Image, ImageDraw, ImageFont

# bot
import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
import language_tool_python


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
        options = webdriver.ChromeOptions()
        mobile_emulation = {
            "userAgent": 'Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        self.driver = webdriver.Chrome(options=options)

    def login(self):
        # goto instagram
        self.driver.get('https://www.instagram.com/accounts/login/')

        # accept cookies
        self._click_button("login: accepting cookies ...",
                           '/html/body/div[3]/div/div/button[1]')

        Helper.random_sleep()

        # insert username and password
        self.driver.find_element_by_xpath(
            '//input[@name="username"]').send_keys(self.username)
        self.driver.find_element_by_xpath(
            '//input[@name="password"]').send_keys(self.password)
        Helper.random_sleep()
        self._click_button("login: submitting form ...",
                           '//button[@type="submit"]')

        # generate and insert 2fa key
        if self.two_fa:
            Helper.random_sleep()
            totp = pyotp.TOTP(os.getenv('INSTA_SECRET'))
            self.driver.find_element_by_xpath(
                '//input[@name="verificationCode"]').send_keys(totp.now())
            self._click_button(
                "login: submitting 2fa key ...", '//form/div[2]/button')

        Helper.random_sleep()

    def check_messages(self):
        # goto inbox
        self.driver.get('https://www.instagram.com/direct/inbox/')

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
                    Helper.create_image(message.text)
                print(message.text)

            self.driver.back()

    def _click_button(self, message, element):
        try:
            print(message)
            button = self.driver.find_element_by_xpath(element)
            button.click()
        except selenium.common.exceptions.NoSuchElementException:
            pass

    def create_post(self):
        pass

    def automated_mode(self):
        self.check_messages()

    def __del__(self):
        self.driver.close()


class Helper:

    @staticmethod
    def random_sleep(min_sleep=3, max_sleep=5):
        # random sleep to make sure that bot is not detected
        sleep_time = random.randint(min_sleep, max_sleep)
        print("random_sleep: sleeping for " + str(sleep_time) + " seconds ...")
        time.sleep(sleep_time)

    @staticmethod
    def create_image(message, post_type='normal'):
        # create image with text using PIL
        background_color = (45, 45, 45)
        normal_post = (251, 154, 111)

        # remove any special characters such as unicode characters from message
        message = Helper.clean_string(message)
        # message = Helper.fix_spelling(message)

        # select color depending on post_type
        if post_type == 'normal':
            text_color = normal_post
        else:
            text_color = (255, 255, 255)

        W, H = (1080, 1080)
        img = Image.new(mode='RGB', size=(W, H), color=background_color)
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype("/usr/local/share/fonts/a/Avenir_Book.ttf", size=40)

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

        file_name = 'images/' + str(uuid.uuid4()) + '.png'
        img.save(file_name)

    @staticmethod
    def clean_string(string: str):
        # remove linebreaks from string
        string = string.replace('\n', ' ').replace('\r', ' ')
        # remove emojis from string
        string = re.sub(r'[\U0001f600-\U0001f650]', '', string)
        # remove multiple spaces
        string = re.sub(r'\s+', ' ', string)
        print('clean_string: ' + string + ' now clean ...')
        return string

    @staticmethod
    def fix_spelling(string: str):
        tool = language_tool_python.LanguageToolPublicAPI('de-DE')
        string = tool.correct(string)
        return string


if __name__ == '__main__':
    dotenv.load_dotenv()
    instabot = InstaBot(os.getenv('INSTA_USERNAME'), os.getenv('INSTA_PASSWORD'), True)
    instabot.login()
    instabot.automated_mode()

    # Helper.create_image('Jo, könntest du mir ihren/seinen Account schicken? Bin zu schüchtern in die Kommentare zu schreiben und will es deswegen lieber über die DMs machenHey alles gut. Dürft ich dich an die Person weiterleiten?check_message: checking messages of 340282366841710300949128188026627057131 ...')
