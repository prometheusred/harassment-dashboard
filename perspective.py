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

    def scores(self, texts, models=['TOXICITY', 'SEVERE_TOXICITY']):
        """
        Same as score but handles a list of texts

        Returns:
            list: scores, each a dict
        """
        print ('scoring...')
        count = 1
        scores = []
        for text in texts:
            print(count)
            count += 1
            score = self.score(text, models)
            scores.append(score)
        return scores

def scrub_scores(scores):
    """
    convert score response (list of json) to list of summary scores
    for TOXICITY
    """
    new_scores = []
    for s in scores:
        if 'attributeScores' in s:
            score = s['attributeScores']['TOXICITY']['summaryScore']['value']
            new_scores.append(round(score * 100))
    return new_scores


