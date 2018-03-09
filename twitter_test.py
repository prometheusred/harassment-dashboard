import tweepy
import os
import json


from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

consumer_key = os.environ.get('TWITTER_KEY')
consumer_secret = os.environ.get('TWITTER_SECRET')

access_token = os.environ.get('TWITTER_ACCESS_KEY')
access_token_secret = os.environ.get('TWITTER_ACCESS_SECRET')

#auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
#auth.set_access_token(access_token, access_token_secret)

auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
auth.secure = True
searchQuery = '@amyschumer'#'@the_dismal_tide'
retweet_filter='-filter:retweets'

q=searchQuery+retweet_filter
max_id = -1
tweetsPerQry = 100
sinceId = None

tweetCount = 0
maxTweets = 10000

tweets = []

while tweetCount < maxTweets:
    print(tweetCount)
    print()
    if (max_id <= 0):
        new_tweets = api.search(q=q,
                                count=tweetsPerQry,
                                tweet_mode='extended')
    else:
        new_tweets = api.search(q=q,
                                count=tweetsPerQry,
                                tweet_mode='extended',
                                max_id=str(max_id - 1))
    if not new_tweets:
        print("No more tweets found")
        break

    tweetCount += len(new_tweets)
    max_id = new_tweets[-1].id

    tweets.extend(new_tweets)

print(f"\nDownloaded {max_id}")
print(max_id)






#api = tweepy.API(auth)
#public_tweets = api.user_timeline(['amyschumer'])
# for tweet in public_tweets:
#     print(tweet.text)

#print('ran it***************************************')

# class StdOutListener(StreamListener):
#     """ A listener handles tweets that are received from the stream.
#     This is a basic listener that just prints received tweets to stdout.
#     """
#     def on_data(self, data):
#         data = json.loads(data)
#         #print(data.get('favorite_count'))
#         print(data)
#         #print(data.keys())
#         print()
#         print('*************************')
#         return True

#     def on_error(self, status):
#         print(status)

# if __name__ == '__main__':
#     l = StdOutListener()
#     auth = OAuthHandler(consumer_key, consumer_secret)
#     auth.set_access_token(access_token, access_token_secret)

#     stream = Stream(auth, l)
#     stream.filter(track=['hate'])

#     print('ran it***************************************')
