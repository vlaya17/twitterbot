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

LIMIT_DAYS=5

# Buffer containing tweets to reply to, sorted by date
tweets = []
# Map to keep track of tweets we already replied to
replied_tweets = {}

# Doesn't reply to tweets, used for testing
debug=False

def hours_to_ns(hours):
    return hours * 3600 * 10**9
def days_to_ns(days):
    return hours_to_ns(24 * days)

# Load map from file
def loadRepliedTweets():
    global replied_tweets
    with open('replied_tweets.json', 'r') as f:
        replied_tweets = json.load(f)

# Save map to file
def saveRepliedTweets():
    with open('replied_tweets.json', 'w+') as f:
        json.dump(replied_tweets, f)

# Remove old tweets in the map to prevent it getting too big
def cleanOldRepliedTweets():

    for url in replied_tweets:
        if replied_tweets[url] < (int(time.time()) - days_to_ns(LIMIT_DAYS)):
            replied_tweets.pop(url, None)

    saveRepliedTweets()

# Might be useful to throw off bot detection
def random_sleep():
    time.sleep(uniform(2.0, 4.0))

# Refill the tweet buffer
def FindNewTweets(query, hours, limit, days):

    global tweets

    tweet_file="tweets.json"

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=days)
    yesterday_date = yesterday.strftime("%Y-%m-%d")

    os.system("rm -f {}".format(tweet_file))

    limit_option="" if limit == "0" else "-l {}".format(limit)

    cmd = "twitterscraper \"{}\" {} -bd {} -p 1 -o {}".format(query, limit_option, yesterday_date, tweet_file)
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
def startRoutine(account_info, query_list, reply, limit, days):


    print("Loggin in: {} {} {}".format(account_info["email"], account_info["username"], account_info["password"]))

    if not debug:
        bot = TwitterBot(account_info["email"], account_info["username"], account_info["password"])
        bot.signIn()

    start_timestamp = time.time()
    last_clean = start_timestamp
    last_sleep = start_timestamp

    print("Reply: {}".format(reply))
    print("Queries: {}".format(", ".join(query_list)))

    while True:

        for query in query_list:

            FindNewTweets(query, days * 24, limit, days)

            for tweet in tweets:
                if not tweet['url'] in replied_tweets:

                    # Keep track of the replied tweet to avoid replying it again
                    replied_tweets[tweet['url']] = tweet['timestamp']
                    saveRepliedTweets()

                    dt = datetime.datetime.fromtimestamp(tweet['timestamp'])
                    tweet_time = dt.strftime("%H:%M:%S %d-%m-%Y")
                    print("Replying to {} - {}".format(tweet['url'], tweet_time))

                    if not debug:
                        bot.ReplyToTweet(tweet['url'], reply)

                        for i in range(10):
                            random_sleep()

            if not debug:
                random_sleep()
                random_sleep()

            # Sleep for a while every once in a while
            if (time.time() - last_sleep) > hours_to_ns(2):
                time.sleep(random.randint(1800, 7200))
                last_sleep = time.time()

            # Remove old tweets every once in a while
            if (time.time() - last_clean) > hours_to_ns(24):
                cleanOldRepliedTweets()
                last_clean = time.time()

def parse_account_info(name):
    with open(name, "r") as f:
        (email, username, password) = [l.strip() for l in f]
        return {"email": email, "username": username, "password": password}

def parse_query(name):
    with open(name, "r") as f:
        return [l.strip() for l in f]

def parse_reply(name):
    with open(name, "r") as f:
        return f.read().strip()

def parse_args():

    parser = argparse
    parser = argparse.ArgumentParser(description='Twitter bot')
    parser.add_argument('-l', nargs=1, required=False, help='limit used for twitterscraper')
    parser.add_argument('-d', nargs=1, required=False, help='days from which the scraping should start')
    parser.add_argument('-a', nargs=1, required=False, help='account login info file')
    parser.add_argument('-q', nargs=1, required=False, help='query to use to find tweets to reply to')
    parser.add_argument('-t', nargs=1, required=False, help='tweet to use for replies')

    args = parser.parse_args()

    if args.l is None or args.a is None or args.q is None or args.t is None:
        parser.print_help(sys.stderr)
        exit()

    loadRepliedTweets()

    account_info = parse_account_info(args.a[0])
    query_list = parse_query(args.q[0])
    reply = parse_reply(args.t[0])

    if not args.d is None:
        days = int(args.d[0])
        if days > LIMIT_DAYS:
            print("Day limit is set to {}".format(LIMIT_DAYS))
            exit()
    else:
        days = 1

    startRoutine(account_info, query_list, reply, int(args.l[0]), days)

parse_args()

