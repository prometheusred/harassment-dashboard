import json
import requests
import functools
import operator
#import asyncio
#import concurrent.futures


class Perspective(object):
    """
    Basic client for Perspective API
    https://github.com/conversationai/perspectiveapi/blob/master/api_reference.md
    """
    base_url = 'https://commentanalyzer.googleapis.com/v1alpha1'

    all_models = ['TOXICITY',
                  'SEVERE_TOXICITY',
                  'TOXICITY_FAST',
                  'ATTACK_ON_AUTHOR',
                  'ATTACK_ON_COMMENTORF',
                  'INCOHERENT',
                  'INFLAMMATORY',
                  'LIKELY_TO_REJECT',
                  'OBSCENE',
                  'SPAM',
                  'UNSUBSTANTIAL']

    def __init__(self, key):
        self.key = key
        self.s = requests.Session()
        self.headers = {'content-type': 'application/json'}
        self.query_string = {'key': self.key}
        self.url = self.base_url + '/comments:analyze'

        # r = requests.Request('POST',
        #                      url,
        #                      headers=headers,
        #                      params=query_string)
        #self.prepped_request = self.s.prepare_request(r)

    def score(self, text, models=['TOXICITY', 'SEVERE_TOXICITY']):
        """
        Get scores for a string of text given a list of models to score with.
        A score represents probability that the given text is what a given model
        is looking for.  e.g. 100% TOXICITY score means the text is very likely
        to be toxic.

        Args:
            text(str): string of english <= 3000 chars
            models(:obj:'list' of str): names of perspective models to score text

        Returns:
             dict: summary scores and span scores for requested models
        """

        # key = self.key
        # headers = {'content-type': 'application/json'}
        # query_string = {'key': self.key}
        # url = self.base_url + '/comments:analyze'

        text = text[:3000]

        requested_models = {model: {}
                             for model in models if model in self.all_models}
        payload_data = json.dumps(
            {'comment': {'text': text}, 'requestedAttributes': requested_models})

        #response = self.s.send(self.prepped_request)

        response = self.s.post(self.url,
                                data=payload_data,
                                headers=self.headers,
                                params=self.query_string)

        return response.json()

    def scores(self, tweets_df, models=['TOXICITY', 'SEVERE_TOXICITY']):
        """
        Same as score but handles a list of texts

        Args:
            DataFrame: tweets

        Returns:
            DataFrame: adds unpacked scores to what it recieves
        """
        print('scoring...')
        tweets_df['score'] = tweets_df['scrubbed_text'].apply(self.score)
        for model in models:
            tweets_df[model + '_score'] = tweets_df['score'].apply(unpack_score,
                                                                   model_name=model)
        return tweets_df

def unpack_score(score, **kwargs):
    """
    Pulls specific model score out of score json.
    If perspective can't score text, 0 is used.

    Args:
        score(dict): complete score json for a tweet
        kwargs: name of the model to unpack score

    Returns:
        model_score: integer that represents percentage score for a given model
    """
    model_name = kwargs.get('model_name')
    print(score)
    if 'attributeScores' in score:
        model_score = round(
        score['attributeScores'][model_name]['summaryScore']['value'] * 100)
    else:
        model_score = 0
    return model_score

