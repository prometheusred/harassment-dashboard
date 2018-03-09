import json
import os
import re

import tweepy

#from tweepy.streaming import StreamListener
#from tweepy import OAuthHandler
#from tweepy import Stream

class Twitter(object):
    """
    Basic client for twitter API on top of tweepy
    """
    retweet_filter='-filter:retweets'

    def __init__(self, consumer_key, consumer_secret):
        self.auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
        self.auth.secure = True
        self.api = tweepy.API(self.auth,
                              wait_on_rate_limit=True,
                              wait_on_rate_limit_notify=True)

    def tweets_at(self, handle, max_tweets=100):
        """
        Get tweets at a @handle.  Retweets of that @handle are filtered out.

        Args:
            handle(str): handle of twitter user in format @handle
            max_tweets(int): max number of tweets to get

        Returns:
            list: Tweepy Status objects
        """
        search_query = handle + self.retweet_filter
        max_id = -1
        tweets_per_qry = 100
        since_id = None
        tweet_count = 0
        tweets = []
        while tweet_count < max_tweets:
            print(tweet_count)
            print()
            if (max_id <= 0):
                new_tweets = self.api.search(q=search_query,
                                             count=tweets_per_qry,
                                             tweet_mode='extended')
            else:
                new_tweets = self.api.search(q=search_query,
                                             count=tweets_per_qry,
                                             tweet_mode='extended',
                                             max_id=str(max_id - 1))
            if not new_tweets:
                print("No more tweets found")
                break
            tweet_count += len(new_tweets)
            max_id = new_tweets[-1].id
            tweets.extend(new_tweets)
        return tweets

compiled_scrub_pattern = re.compile(r'(?<![#@])\b\w+\b')
def scrub_tweets(tweets):
        """
        Currently just strips @mentions and #hashtags out of full_text field of
        tweepy Status object
        """
        print('scrubbing...!')
        scrubbed_tweet_text = []
        for tweet in tweets:
            remaining_words = compiled_scrub_pattern.findall(tweet.full_text)
            scrubbed_tweet_text.append(' '.join(remaining_words))
        return scrubbed_tweet_text
        #print(tweets[0].full_text)
