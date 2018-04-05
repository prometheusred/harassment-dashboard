
# harassment-dashboard

A hack based on Jigsaw's [Perspective API](https://www.perspectiveapi.com).  It is a simple dashboard that visualizes toxic langauge in tweets and allows you to jump into the conversation on twitter.  Just enter someone's twitter handle to see how much / if they are the target of toxicity and harassment.

![Alt text](/images/toxicity-summary-image-obfuscated.png?raw=true "Toxicity Summary")


![Alt text](/images/toxicity-over-time-image-obfuscated.png?raw=true "Toxicity over time")

## Requirements

1. python 3.6+
2. Redis (right now only used for caching but hopefully to be used for a queue for intermediate results/loading in the near future)
3. Your own keys for Twitter and the Perspective API (note: this app currently uses an app-wide key for twitter (no oauth for users) and hence there are security and rate-limit implications to keep in mind).

The main libraries being used are Dash, a python data viz library that wraps up flask, d3, and React, and pandas for data manipulation/filtering.  Tweepy is used for pulling tweets and asyncio/aiohttp is used for parallizing requests to the perspective api.

## Running locally

For now, I'll assume you're on a mac:

1. Make sure you have [python 3.6+](http://docs.python-guide.org/en/latest/starting/install3/osx/): `brew update`, and then `brew upgrade python` or `brew install python` (this should install python 3, not 2).

2. Install redis with [homebrew](https://medium.com/@petehouston/install-and-config-redis-on-mac-os-x-via-homebrew-eb8df9a4f298): `brew install redis` and `brew services start redis`.

3. Activate a [virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/) and install python dependencies:`pip install -r requirements`

4. Set environment variables for your keys: 

`export PERSPECTIVE_KEY=[your-key-here]`
`export TWITTER_KEY=[your-key-here]`
`export TWITTER_SECRET=[your-key-here]`

5. Run locally with `python app.py` from the project directory and go to http://localhost:8050/ in your browser.

6. You could also run locally with Gunicorn, e.g.: `gunicorn app:server -w 4 -k gevent`

## Deploying to Heroku

One of the easiest and free-est ways to deploy is with Heroku (though it shouldn't be too much work to put it on, for example, Google App Engine).

1. [Create a Heroku account](https://devcenter.heroku.com/articles/getting-started-with-python#set-up), download the CLI, and run `heroku login` to auth.

2. [Hook up Heroku](https://devcenter.heroku.com/articles/getting-started-with-python#deploy-the-app) with `heroku create` in the project directory and [connect a free-tier instance of Redis](https://devcenter.heroku.com/articles/heroku-redis) to your Heroku project with `heroku addons:create heroku-redis:hobby-dev -a harassment-dashboard`.

3. Set environment variables for your keys in the [heroku dashboard or in terminal](https://medium.com/taqtilebr/managing-herokus-app-environment-variables-d13fd99610b).

4. And finally, deploy with `git push heroku master`.  Go to the address generated to confirm the app is deployed.  You can [adjust Gunicorn settings](https://devcenter.heroku.com/articles/python-gunicorn) in the Procfile. And you can [see logs](https://devcenter.heroku.com/articles/logging) for your project with `heroku logs -a harassment-dashboard`.
