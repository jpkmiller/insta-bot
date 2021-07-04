"""
Inspired by https://github.com/CamTosh/instagram-bot-dm
I did not use his code on purpose, but if I did all credit goes to him.
"""

import os
import re
import time
from http.server import BaseHTTPRequestHandler
from random import randint
import logging

import dotenv
import pyotp
import selenium.common.exceptions
from selenium import webdriver


class InstaBotServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))


class InstaBot:
    def __init__(self, username: str, password: str, two_fa: bool = False):
        self.username = username
        self.password = password
        self.two_fa = two_fa
        options = webdriver.ChromeOptions()
        mobile_emulation = {
            "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        self.driver = webdriver.Chrome(options=options)
        self.login()
        Helper.random_sleep()

    def login(self):
        # goto instagram
        self.driver.get('https://www.instagram.com/accounts/login/')

        # accept cookies
        self.driver.find_element_by_xpath('/html/body/div[3]/div/div/button[1]').click()

        Helper.random_sleep()

        # insert username and password
        self.driver.find_element_by_xpath('//input[@name="username"]').send_keys(self.username)
        self.driver.find_element_by_xpath('//input[@name="password"]').send_keys(self.password)
        Helper.random_sleep()
        self.driver.find_element_by_xpath('//button[@type="submit"]').click()

        Helper.random_sleep()

        # insert 2fa key
        if self.two_fa:
            totp = pyotp.TOTP(os.getenv('INSTA_SECRET'))
            self.driver.find_element_by_xpath('//input[@name="verificationCode"]').send_keys(totp.now())
            self.driver.find_element_by_xpath('//form/div[2]/button').click()

        Helper.random_sleep()

    def check_messages(self):
        # goto inbox
        self.driver.get('https://www.instagram.com/direct/inbox/')

        Helper.random_sleep()

        # deactivate notifications
        try:
            notification_button = self.driver.find_element_by_xpath('/html/body/div[3]/div/div/div/div[3]/button[2]')
            notification_button.click()
        except selenium.common.exceptions.NoSuchElementException:
            pass

        # find all messages
        person_ids = [re.findall(r'\d+', person.get_attribute('href'))[0] for person in self.get_persons_in_dm()]
        for person_id in person_ids:
            print("check_messages: checking messages of " + person_id)
            link_to_person = self.driver.find_element_by_xpath(
                '//a[count(div[@aria-labelledby])>0][@href="/direct/t/{id}"]'.format(id=person_id))
            messages = self.driver.find_elements_by_xpath('//div[@role="listbox"]//*/span')
            for message in messages:
                print(message.text)
            link_to_person.click()

    def get_persons_in_dm(self):
        return self.driver.find_elements_by_xpath('//a[count(div[@aria-labelledby])>0][@href]')

    def automated_mode(self):
        self.check_messages()


class Helper:

    @staticmethod
    def random_sleep(min_sleep=3, max_sleep=5):
        time.sleep(randint(min_sleep, max_sleep + min_sleep))


if __name__ == '__main__':
    dotenv.load_dotenv()
    instabot = InstaBot(os.getenv('INSTA_USERNAME'), os.getenv('INSTA_PASSWORD'), True)
    instabot.automated_mode()
