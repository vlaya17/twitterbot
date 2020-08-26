from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from twitterscraper import query_tweets
from random import uniform

import datetime
import time
import re
import os
import json

tweets = []
tweets_done = {}

def loadTweetsDone():
    with open('tweets_done.json', 'r') as f:
        data = json.load(f)

def saveTweetsDone():
    with open('tweets_done.json', 'w+') as f:
        json.dump(tweets_done, f)

def cleanOldTweetsDone():

    hours = 72

    for url in tweets_done:
        if tweets_done[url] < (int(time.time()) - 3600*hours):
            tweets_done.pop(url, None)

    save_tweets_done()

def random_sleep():
    time.sleep(uniform(2.0, 4.0))

def FindNewTweets(search, hours):

    global tweets

    tweet_file="tweets.json"

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    yesterday_date = yesterday.strftime("%Y-%m-%d")

    os.system("rm -f {}".format(tweet_file))
    cmd = "twitterscraper \"{}\" -l 1000 --lang fr -bd {} -p 1 -o {}".format(search, yesterday_date, tweet_file)
    print(cmd)
    os.system(cmd)

    with open(tweet_file) as f:
        data = json.load(f)

        for d in data:

            timestamp = d['timestamp_epochs']

            #If tweet is recent enough
            if timestamp > (int(time.time()) - 3600*hours):
                tweets.append({'url': d['tweet_url'], 'text': d['text'], 'timestamp': timestamp})

    tweets = sorted(tweets, key=lambda x : x['timestamp'])
    tweets = tweets[-1000:]

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

class MailBot():
    def __init__(self,username,password):
        self.browser=webdriver.Chrome("chromedriver")
        self.username=username
        self.password=password

    def signIn(self):
        self.browser.get("https://passport.yandex.com/auth?from=mail")
        random_sleep()
        usernameInput=self.browser.find_element_by_name("login")
        usernameInput.send_keys(self.username)
        usernameInput.send_keys(Keys.ENTER)
        random_sleep()
        passwordInput=self.browser.find_element_by_name("passwd")
        passwordInput.send_keys(self.password)
        passwordInput.send_keys(Keys.ENTER)
        random_sleep()


    def getCode(self):
        self.browser.get("https://mail.yandex.com/")
        random_sleep()
        mail = self.browser.find_element_by_xpath("/html/body/div[2]/div[5]/div/div[3]/div[3]/div[2]/div[5]/div[1]/div/div/div[2]/div/div[1]/div/div/div/a")
        mail.click()
        random_sleep()
        text_element = self.browser.find_element_by_xpath("/html/body/div[2]/div[5]/div/div[3]/div[3]/div[2]/div[5]/div[1]/div/div[3]/div")
        code = cleanhtml(str(text_element.get_attribute('innerHTML')))
        code = code.split(" the following single-use code. ")[1]
        code = code.split(" If")[0]
        return code

def get_code():
    bot = MailBot("mitchelllawrence17@yandex.com", "0WOu(yLok)u.w6&2")
    bot.signIn()
    return bot.getCode()

class TwitterBot():
    def __init__(self,email,username,password):
        self.browser=webdriver.Chrome("chromedriver")
        self.email=email
        self.username=username
        self.password=password

    def signIn(self):
        self.browser.get("https://www.twitter.com/login")
        random_sleep()
        usernameInput=self.browser.find_element_by_name("session[username_or_email]")
        passwordInput=self.browser.find_element_by_name("session[password]")
        usernameInput.send_keys(self.username)
        passwordInput.send_keys(self.password)
        passwordInput.send_keys(Keys.ENTER)
        random_sleep()
        text_element = self.browser.find_element_by_xpath("/html/body")
        text = cleanhtml(str(text_element.get_attribute('innerHTML')))

        if "Verify your identity by entering the email address" in text:
            codeInput = self.browser.find_element_by_xpath('//*[@id="challenge_response"]')
            codeInput.send_keys(self.email)
            codeInput.send_keys(Keys.ENTER)
            random_sleep()

        if "Check your email" in text:
            codeInput = self.browser.find_element_by_xpath('//*[@id="challenge_response"]')
            codeInput.send_keys(get_code())
            codeInput.send_keys(Keys.ENTER)
            random_sleep()


    def TweetSomething(self, text):
        tweet = self.browser.find_element_by_xpath('''//*[@id='react-root']/div/div/div[2]/main/div/div/div/div/div
                                                      /div[2]/div/div[2]/div[1]/div/div/div/div[2]/div[1]/div/div
                                                      /div/div/div/div/div/div/div/div[1]/div/div/div/div[2]/div
                                                      /div/div/div''')
        tweet.send_keys(text)
        tweet.send_keys(Keys.CONTROL, Keys.RETURN)

    def ReplyToTweet(self, url, text):
        self.browser.get("https://www.twitter.com" + url)
        random_sleep()
        self.browser.refresh()
        random_sleep()
        #reply_button = self.browser.find_element_by_xpath("/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/section/div/div/div[1]/div/div/article/div/div/div/div[3]/div[3]/div[1]/div")
        reply_button = self.browser.find_element_by_xpath('//div[@aria-label="Reply"]')
        reply_button.send_keys(Keys.ENTER)
        random_sleep()
        reply_input = self.browser.find_element_by_xpath('''//*[@id='react-root']/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div[3]/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div/div/div/div[1]/div/div/div/div[2]/div''')
        
        reply_input.send_keys(text)
        random_sleep()
        reply_input.send_keys(Keys.CONTROL, Keys.RETURN)

def startRoutine():

    bot = TwitterBot("mitchelllawrence17@yandex.com", "esaptichigu", "0WOu(yLok)u.w6&2")
    bot.signIn()
    search = "femme biologique trans"

    while True:

        FindNewTweets(search)

        for tweet in tweets:
            if not tweet['url'] in tweets_done:

                bot.ReplyToTweet(tweet['url'], "https://toutesdesfemmes.fr/")
                tweets_done[tweet['url']] = tweet['timestamp']
                random_sleep()
                random_sleep()
                random_sleep()

        random_sleep()
        random_sleep()

startRoutine()
