# Twitter bot
# Uses selenium to simulate user input
#
# Finds html elements using wonky methods which
# might break if the web UI gets slightly altered
#
# Scrapes new tweets with twitterscraper, which might
# regularly break
#
# Can get verification code on yandex email if twitter asks it

import datetime
import time
import re
import os
import sys
import json
import argparse

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from twitterscraper import query_tweets
from random import uniform

# Buffer containing tweets to reply to, sorted by date
tweets = []
# Map to keep track of tweets we already replied to
replied_tweets = {}

# Load map from file
def loadRepliedTweets():
    with open('replied_tweets.json', 'r') as f:
        data = json.load(f)

# Save map to file
def saveRepliedTweets():
    with open('replied_tweets.json', 'w+') as f:
        json.dump(replied_tweets, f)

# Remove old tweets in the map to prevent it getting too big
def cleanOldRepliedTweets():

    hours = 72

    for url in replied_tweets:
        if replied_tweets[url] < (int(time.time()) - 3600*hours):
            replied_tweets.pop(url, None)

    saveRepliedTweets()

# Might be useful to throw off bot detection
def random_sleep():
    time.sleep(uniform(2.0, 4.0))

# Refill the tweet buffer
def FindNewTweets(query, hours):

    global tweets

    tweet_file="tweets.json"

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    yesterday_date = yesterday.strftime("%Y-%m-%d")

    os.system("rm -f {}".format(tweet_file))
    cmd = "twitterscraper \"{}\" -l 1000 --lang fr -bd {} -p 1 -o {}".format(query, yesterday_date, tweet_file)
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

# Remove html tags
def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

# Yandex mail bot
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

# Get verification code twitter which twitter can ask
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
        reply_button = self.browser.find_element_by_xpath('//div[@aria-label="Reply"]')
        reply_button.send_keys(Keys.ENTER)
        random_sleep()
        reply_input = self.browser.find_element_by_xpath('''//*[@id='react-root']/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div[3]/div/div/div/div[2]/div/div/div/div/div[2]/div[1]/div/div/div/div/div/div/div/div/div/div[1]/div/div/div/div[2]/div''')
        
        reply_input.send_keys(text)
        random_sleep()
        reply_input.send_keys(Keys.CONTROL, Keys.RETURN)

# Find tweets containing search pattern and reply to them
def startRoutine(account_info, query, reply):

    print("Loggin in: {} {} {}".format(account_info["email"], account_info["username"], account_info["password"]))
    #bot = TwitterBot(account_info["email"], account_info["username"], account_info["password"])
    #bot.signIn()

    start_timestamp = time.time()

    print("Reply: {}".format(reply))
    print("Query: {}".format(query))

    while True:

        FindNewTweets(query, 48)

        for tweet in tweets:
            if not tweet['url'] in replied_tweets:

                # Keep track of the replied tweet to avoid replying it again
                replied_tweets[tweet['url']] = tweet['timestamp']
                saveRepliedTweets()

                dt = datetime.datetime.fromtimestamp(tweet['timestamp'])
                tweet_time = dt.strftime("%H:%M:%S %d-%m-%Y")
                print("Replying to {} - {}".format(tweet['url'], tweet_time))
                #bot.ReplyToTweet(tweet['url'], reply)

                random_sleep()
                random_sleep()

        random_sleep()
        random_sleep()

        # Remove old tweets once in a while
        if (time.time() - start_timestamp) > 48:
            cleanOldRepliedTweets()

def parse_account_info(name):

    with open(name, "r") as f:
        (email, username, password) = [l for l in f]
        return {"email": email, "username": username, "password": password}

def parse_query(name):

    with open(name, "r") as f:
        return f.read()

def parse_reply(name):

    with open(name, "r") as f:
        return f.read()

def parse_args():

    parser = argparse
    parser = argparse.ArgumentParser(description='Twitter bot')
    parser.add_argument('-a', nargs=1, required=False, help='account login info file')
    parser.add_argument('-q', nargs=1, required=False, help='query to use to find tweets to reply to')
    parser.add_argument('-t', nargs=1, required=False, help='tweet to use for replies')

    args = parser.parse_args()

    if args.a is None or args.q is None or args.t is None:
        parser.print_help(sys.stderr)
        exit()

    account_info = parse_account_info(args.a[0])
    query = parse_query(args.q[0])
    reply = parse_reply(args.t[0])

    startRoutine(account_info, query, reply)

parse_args()

