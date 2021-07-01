import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from random import randint
import dotenv
import pyotp

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
        self.driver = webdriver.Chrome()
        self.login()
        Helper.random_sleep(15)

    def login(self):
        # goto instagram
        self.driver.get('https://www.instagram.com/accounts/login/')

        # accept cookies
        self.driver.find_element_by_xpath('/html/body/div[3]/div/div/button[1]').click()

        Helper.random_sleep()

        # insert username and password
        self.driver.find_element_by_xpath('//input[@name="username"]').send_keys(self.username)
        self.driver.find_element_by_xpath('//input[@name="password"]').send_keys(self.password)
        self.driver.find_element_by_xpath('//button[@type="submit"]').click()

        Helper.random_sleep()

        # insert 2fa key
        if self.two_fa:
            totp = pyotp.TOTP(os.getenv('INSTA_SECRET'))
            self.driver.find_element_by_xpath('//input[@name="verificationCode"]').send_keys(totp.now())
            self.driver.find_element_by_xpath(
                '//*[@id="react-root"]/section/main/div/div/div[1]/div/form/div[2]/button').click()

        Helper.random_sleep()

    def check_messages(self):
        # goto inbox
        self.driver.get('https://www.instagram.com/direct/inbox/')

        Helper.random_sleep()

        # deactivate notifications
        notification_button = self.driver.find_element_by_xpath('/html/body/div[3]/div/div/div/div[3]/button[2]')
        if notification_button is not None:
            notification_button.click()


        messages = self.driver.find_elements_by_xpath(
            '//*[@id="react-root"]/section/div/div[2]/div/div/div[1]/div[3]/div/div/div/div')
        print(messages)

    def automated_mode(self):
        while True:
            self.check_messages()
            Helper.random_sleep()


class Helper:

    @staticmethod
    def random_sleep(min_sleep=5, max_sleep=10):
        time.sleep(randint(min_sleep, max_sleep + min_sleep))


if __name__ == '__main__':
    dotenv.load_dotenv()
    instabot = InstaBot(os.getenv('INSTA_USERNAME'), os.getenv('INSTA_PASSWORD'), True)
    instabot.automated_mode()
