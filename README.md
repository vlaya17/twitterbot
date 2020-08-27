# Twitter bot

Find tweets containing search pattern and reply to them

## Installation

Make sure you have python 3 (might not work with python 2)

```python --version```

Install pip

### Optional (but better): setup a python virtual environment

For instane using virtualenv

```
pip install virtualenv
virtualenv venv
source venv/bin/activate
```

### Install packages

twitterscraper is currently broken and needs a patch, so repo needs to be cloned

```
git clone https://github.com/taspinar/twitterscraper.git
cd twitterscraper
git apply ../0001-Patch-query.py.patch
python setup.py install
```

Install selenium

```
pip install selenium
```

### Provide chromedriver executable

Download chromedriver: https://chromedriver.chromium.org/ , extract zip archive and put chromedriver executable at the root of the twitterbot repo

## Usage

Create account, query, reply and limit file profiles (examples are present in profiles folder). 
See https://github.com/taspinar/twitterscraper (2.2.2 Examples of advanced queries) to know how to format your query.
The query will be used to find tweets to reply to.

If you created a virtual environment, activate it before running the bot:

```
source venv/bin/activate
```

Then run the bot and give it the profiles as parameter

```
python bot.py -a account_info_file -s search_pattern_file -t reply_file
```

Multiple bots can be launched at once
