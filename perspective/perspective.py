import json
import requests


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

    def score(self, text, models=['TOXICITY']):
        """
        Return scores for a string of text given a list of models to score with.
        A score represents probability that the given text is what a given model
        is looking for.  e.g. 100% TOXICITY score means the text is very likely
        to be toxic.

        Args:
            text(str): string of english <= 3000 chars
            models(:obj:'list' of str): names of perspective models to score text

        Returns:
             dict: summary scores and span scores for requested models
        """
        headers = {'content-type': 'application/json'}
        query_string = {'key': self.key}
        url = self.base_url + '/comments:analyze'
        text = text[:3000]
        requested_models = {model: {}
                             for model in models if model in self.all_models}
        payload_data = json.dumps(
            {'comment': {'text': text}, 'requestedAttributes': requested_models})
        response = requests.post(url,
                                 data=payload_data,
                                 headers=headers,
                                 params=query_string)
        return response.json()
