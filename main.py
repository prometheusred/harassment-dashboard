import os

from perspective import Perspective
from twitter import Twitter, scrub_tweets


perspective_key = os.environ.get('PERSPECTIVE_KEY')
perspective_client = Perspective(perspective_key)

twitter_consumer_key = os.environ.get('TWITTER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_SECRET')
twitter_client = Twitter(twitter_consumer_key, twitter_consumer_secret)


# text = 'You are a giant lovely garbage can and i love you. click on coca-cola.com. \
# In addition, I belive that the cow jumped over the moon. And the robot killed \
# all humans.  I love that.  And you suck.'

tweets = twitter_client.tweets_at('@the_dismal_tide')
tweet_texts = scrub_tweets(tweets)

scores = perspective_client.scores(tweet_texts)

#tprint ('got scores?!')
# data = perspective_client.score(text)


# for key, val in sorted(data['attributeScores'].items()):
#     percentage = '{:.2%}'.format(val['summaryScore']['value'])
#     print(str(key).ljust(19),
#           '---------------------->'.center(7),
#           str(percentage).rjust(7))

    # print('\nspans:\n')

    # for span_score in val['spanScores']:
    #     span = text[span_score['begin']:span_score['end']]
    #     percentage = '{:.2%}'.format(span_score['score']['value'])
    #     print(span)
    #     print(percentage)
    #     print()
