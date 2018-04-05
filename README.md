
# harassment-dashboard

A hack based on Jigsaw's [Perspective API](https://www.perspectiveapi.com).  It is a simple dashboard that visualizes toxic langauge in tweets and allows you to jump into the conversation on twitter.  Just enter someone's twitter handle to see how much / if they are the target of toxicity and harassment.

## Requirements

1. python 3.6+
2. Redis (right now only used for caching but hopefully to be used for a queue for intermediate results/loading soon)

The main libraries being used are Dash, a python data viz library that wraps up flask, d3, and React, and pandas for data manipulation/filtering.  Tweepy is used for pulling tweets and asyncio/aiohttp is used for parallizing requests to the perspective api.

## Running locally

For now, I'll assume you're on a mac:

1. Make sure you have python 3.6: ``

2. Install redis with homebrew: `brew install redis` and `brew services start redis`.

3. Activte a virtualenv and install python dependencies:`pip install -r requirements`

4. From the project directory: `python app.py`

## Deploying to Heroku

One of the easiest and free-est ways to deploy is to Heroku (though it shouldn't be too much work to put it on, for example, Google App Engine).
