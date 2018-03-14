# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
from flask_caching import Cache
import os
import pandas as pd
import plotly.graph_objs as go
import time

from perspective import Perspective
from twitter import Twitter, scrub_tweets


perspective_key = os.environ.get('PERSPECTIVE_KEY')
perspective_client = Perspective(perspective_key)

twitter_consumer_key = os.environ.get('TWITTER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_SECRET')
twitter_client = Twitter(twitter_consumer_key, twitter_consumer_secret)

app = dash.Dash('harassment dashboard')
CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'localhost:6379')}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

colors = {
    #'background': '#373365',
    'background': 'white',
    #'text': '#fff'
    'text': 'black'
}

explanation = 'This dashboard visualizes toxic language in Tweets and offers a way to engage to help the harassed.'

basic_style = {'textAlign': 'center',
               'margin': '40px 300px',
               'color': 'black'}

spread_style = {'margin': '5px'}

submit_style={'color': colors['text'],
              'borderRadius': '4px',
              'border': '1px solid black',
              'boxSizing': 'borderBox',
              'display': 'inline-block',
              'backgroundColor': 'transparent',
              'margin': spread_style['margin']}

app.layout = html.Div([

    html.H1(children='Help the Harassed',
            style=basic_style),

    html.P(children=explanation,
           style=basic_style),

    html.Div(children=[html.Label(children='Enter Twitter @handle',
                                  style=spread_style),
                       html.Div(children=dcc.Input(id='input-box',
                                                   type='text',
                                                   value='@',
                                                   style={'color': 'black'}),
                                style=spread_style),
                       html.Button('Submit',
                                   id='submit-button',
                                   style=submit_style),
                       # dcc.Dropdown(id='my-dropdown',
                       #              options=[
                       #                  {'label': '@BarackObama',
                       #                   'value': '@BarackObama'},
                       #                  {'label': '@realDonaldTrump',
                       #                   'value': '@realDonaldTrump'},
                       #                  {'label': '@amyschumer',
                       #                   'value': '@amyschumer'},
                       #                  {'label': '@alex_pentland',
                       #                   'value': '@alex_pentland'}],
                       #              value='@BarackObama',
                       #              style={}),],
                       ],
    style={'text-align': 'center'}),

    dcc.Graph(id='toxicity-over-time', style={'margin': '50px'}),

    #dcc.Graph(id='toxicity-histogram', style={'margin': '50px'}),

    html.Div(id='signal', style={'display': 'none'}),



], style={'color': 'black',
          'columnCount': 1,
          'left': 0,
          'top': 0,
          'width': '100%',
          'height': '100%',
          'position': 'fixed',
          'backgroundColor': colors['background']})


@app.callback(Output('signal', 'children'),
              [Input('submit-button', 'n_clicks')],
               state=[State('input-box', 'value')])
def request_scores(n_clicks, input_value):
    """
    Initiates tweet -> score lookup when clicking submit
    Will look for the @handle in redis cache before starting
    request process.  Data is signaled through invisible div
    so that it can be used for multiple visualizations without
    blocking or doing weird things with state.
    """
    if n_clicks > 0:
        return global_store(input_value).to_json(date_format='iso',
                                                 orient='split')

@app.callback(
    Output('toxicity-over-time', 'figure'),
    [Input('signal', 'children')])
def update_graph(tweets_json):
    """
    Pulls data from signal and updates graph

    Args:
        tweets_json(json): the data for a given @handle
    """
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
            #margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            #legend={'x': 0, 'y': 1},
            hovermode='closest',
            type='layout'
        )
    }

# @app.callback(
#     Output('toxicity-over-time', 'figure'),
#     [Input('', 'n_clicks')],)
# def update_graph(n_clicks, input_value):


# @app.callback(
#     Output('toxicity-histogram', 'figure'),
#     [Input('submit-button', 'n_clicks')],
#     state=[State('input_box', 'value')])
# def update_pie(n_clicks, input_value):


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

        print(f"tweet request time: {tweet_time}")
        print(f"score request time: {score_time}")
    return tweets_df


if __name__ == '__main__':
    app.run_server(debug=True)
