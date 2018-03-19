# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State, Event
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
from flask_caching import Cache
import numpy as np
import os
import pandas as pd
import plotly.graph_objs as go
import time
import json

from perspective import Perspective
from twitter import Twitter, scrub_tweets


perspective_key = os.environ.get('PERSPECTIVE_KEY')
perspective_client = Perspective(perspective_key)

twitter_consumer_key = os.environ.get('TWITTER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_SECRET')
twitter_client = Twitter(twitter_consumer_key, twitter_consumer_secret)

app = dash.Dash('harassment dashboard')
server = app.server
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'localhost:6379')}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
#app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})
app.css.append_css({"external_url": "https://codepen.io/prometheusred/pen/MVbJvO.css"})

colors = {
    #'background': '#373365',
    'background': 'white',
    #'text': '#fff'
    'text': 'black'
}

explanation = 'This dashboard visualizes toxic language in Tweets and offers a way to engage to help the harassed.'

center_el = {'width': '600px',
             'textAlign': 'center',
             'margin': '50px auto'}

center_container = {'margin': '0px auto',
                    'width': '340px',
                    'textAlign': 'center'}

bot_container = {'margin': '0px auto',
                 'width': '100%'}

left_el = {'float': 'left'}
right_el = {'margin': '24px 0 0 -28px',
            'height': '38px'}

left_graph = {'float': 'left',
              'width': '50%',
              'marginTop': '-70px'}
right_text = {'height': '20px',
              'width': '400px',
              'height': '400px',
              'display': 'block',
              'overflow': 'hidden',
              'margin': '50px auto',
              'textAlign': 'left'}


app.layout = html.Div([

    html.H1(children='Help the Harassed', style=center_el),

    html.P(children=explanation, style=center_el),

    html.Div(children=[

        html.Div(children=[

            html.Label(children='Twitter @handle'),
            dcc.Input(id='input-box',
                      type='text',
                      value='@')],

                 style=left_el),

        html.Button('Submit',
                    id='submit-button', style=right_el),],

             style=center_container),

    dcc.Graph(id='toxicity-over-time', style={'margin': '10px 5px 0px 5px'}),

    html.Div(children=[

        dcc.Graph(id='toxicity-pie', style=left_graph),
        html.Div(children=[html.P(children='tweet tweet!',
                                  id='full-text', style={'marginTop': 50}),
                           html.A(html.Button('Join the conversation!'),
                                  href='https://twitter.com'),],
                 style=right_text)],

             style=bot_container),



    html.Div(id='signal', style={'display': 'none'}),


], style={'color': 'black',
          'left': 0,
          'top': 0,
          'width': '100%',
          'height': '100%',
          'overflow': 'scroll',
          'position': 'fixed',
          'backgroundColor': colors['background']})


@app.callback(Output('signal', 'children'),
              [Input('submit-button', 'n_clicks')],
               state=[State('input-box', 'value')])
def request_scores(n_clicks, input_value):
    """
    Initiates tweet -> score lookup when clicking submit
    Will look for the @handle in redis before starting
    request process.  Data is signaled through invisible div
    so that it can be used for multiple visualizations without
    blocking or doing weird things with state.
    """
    if n_clicks:
        print('request_scores')
        return global_store(input_value).to_json(date_format='iso',
                                                 orient='split')

@app.callback(Output('full-text', 'children'),
              [#Input('toxicity-over-time', 'hoverData'),
               #Input('toxicity-over-time', 'selectedData'),
               Input('toxicity-over-time', 'hoverData'),
               Input('signal', 'children')])
def show_tweet(hoverData, tweets_json):

    if not tweets_json or not hoverData:
        raise PreventUpdate('no data yet!')
    tweets_df = pd.read_json(tweets_json, orient='split')
    #clicked_index = clickData['points'][0]['x'] - 1
    hovered_index = hoverData['points'][0]['x'] - 1
    full_text = tweets_df.iloc[hovered_index]['full_text']
    return full_text

@app.callback(Output('toxicity-over-time', 'figure'),
              [Input('signal', 'children')],
               state=[State('input-box', 'value')])
def update_graph(tweets_json, handle):
    """
    Pulls data from signal and updates graph

    Args:
        tweets_json(json): the data for a given @handle
    """
    if not tweets_json:
        raise PreventUpdate('no data yet!')
    tweets_df = pd.read_json(tweets_json, orient='split')
    x = list(range(1, len(tweets_df) + 1))

    toxicity_trace = dict(
        x=x,
        y=tweets_df['TOXICITY_score'],
        mode='lines+markers',
        marker={
                'size': 10,
                'line': {'width': 0.5, 'color': 'black'}
        },
        name='toxicity',
        type='scatter'
    )

    severe_trace = dict(
        x=x,
        y=tweets_df['SEVERE_TOXICITY_score'],
        mode='lines+markers',
        marker={
                'size': 10,
                'line': {'width': 0.5, 'color': 'black'}
        },
        name='severe toxicity',
        type='scatter'
    )

    return {
        'data': [toxicity_trace, severe_trace],
        'layout': dict(
            xaxis={'type': 'linear', 'title': 'tweets'},
            yaxis={'title': 'toxicity (%)', 'range': [0, 100]},
            #title=f"The last {len(x)} tweets at {handle}",
            title='The last {} tweets at {}'.format(len(x), handle),
            #margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0.1, 'y': 1.1},
            hovermode='closest',
            type='layout'
        )
    }

HIGH_THRESH = 85
LOW_THRESH = 30

@app.callback(Output('toxicity-pie', 'figure'),
              [Input('signal', 'children')])
def update_pie(tweets_json):
    """
    """
    if not tweets_json:
        raise PreventUpdate('no data yet!')
    tweets_df = pd.read_json(tweets_json, orient='split')
    labels = ['high', 'medium', 'low']
    values = [tweets_df[tweets_df['TOXICITY_score'] > HIGH_THRESH],
              tweets_df[(tweets_df['TOXICITY_score'] > LOW_THRESH) &
                        (tweets_df['TOXICITY_score'] < HIGH_THRESH)],
              tweets_df[tweets_df['TOXICITY_score'] < LOW_THRESH]]
    values = [len(value) for value in values]


    print(labels)
    print(values)

    data = dict(
        labels=labels,
        values=values,
        text='toxicity',
        hoverinfo='label+percent',
        hole=.3,
        textinfo='none',
        type='pie',
    )

    return {
        'data': [data],
        'layout': dict(
            type='layout',
            showlegend=False,
            annotations=[{
                'font': {'size': 14},
                'showarrow': False,
                'text': 'toxicity'}]
            )
    }

@cache.memoize(timeout=60*15)  # 15 minutes
def global_store(input_value):
    tweet_start = time.time()
    tweets = twitter_client.tweets_at(input_value)

    if not tweets.empty:
        tweets_df = scrub_tweets(tweets)
        tweet_end = time.time()
        tweet_time = tweet_end - tweet_start

        score_start = time.time()
        tweets_df = perspective_client.scores(tweets_df)
        score_end = time.time()
        score_time = score_end - score_start

        #print(f"tweet request time: {tweet_time}")
        #print(f"score request time: {score_time}")
    return tweets_df

if __name__ == '__main__':
    app.run_server(debug=True, processes=6)
