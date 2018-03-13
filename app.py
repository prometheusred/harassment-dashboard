# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
from flask_caching import Cache
import os
import plotly.graph_objs as go
import time

from perspective import Perspective, scrub_scores
from twitter import Twitter, scrub_tweets

perspective_key = os.environ.get('PERSPECTIVE_KEY')
perspective_client = Perspective(perspective_key)

twitter_consumer_key = os.environ.get('TWITTER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_SECRET')
twitter_client = Twitter(twitter_consumer_key, twitter_consumer_secret)


app = dash.Dash('harassment dashboard')
#app = dash.Dash(__name__)
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})

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

red_box = {'backgroundColor': 'red',
           'position': 'absolute',
           'padding': '-10px -5px'}

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
                                   style=submit_style)],
             style={'text-align': 'center'}),

    dcc.Graph(id='toxicity-over-time', style={'margin': '50px'})


], style={'color': 'black',
          'columnCount': 1,
          'left': 0,
          'top': 0,
          'width': '100%',
          'height': '100%',
          'position': 'fixed',
          'backgroundColor': colors['background']})

@app.callback(
    Output('toxicity-over-time', 'figure'),
    [Input('submit-button', 'n_clicks')],
    state=[State('input-box', 'value')])
def update_graph(n_clicks, input_value):
    print(input_value)

    # tweets = twitter_client.tweets_at(input_value)
    # tweets = scrub_tweets(tweets)
    # scores = scrub_scores(perspective_client.scores(tweets))
    scores = look_up(input_value)

    print(scores)

    trace = dict(
        x=list(range(1, len(scores))),
        y=scores,
        mode='lines+markers',
        marker={
                'size': 10,
                'line': {'width': 0.5, 'color': 'black'}
        },
        type='scatter'
    )

    return {
        'data': [trace],
        'layout': dict(
            xaxis={'type': 'linear', 'title': 'tweets'},
            yaxis={'title': 'toxicity (%)', 'range': [0, 100]},
            #margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            #legend={'x': 0, 'y': 1},
            hovermode='closest',
            type='layout'
        )
    }

@cache.memoize(timeout=60*15)  # 15 minutes
def look_up(input_value):
    tweet_start = time.time()
    tweets = twitter_client.tweets_at(input_value)
    tweets = scrub_tweets(tweets)
    tweet_end = time.time()
    tweet_time = tweet_end - tweet_start

    score_start = time.time()
    scores = scrub_scores(perspective_client.scores(tweets))
    score_end = time.time()
    score_time = score_end - score_start

    print(f"tweet request time: {tweet_time}")
    print(f"score request time: {score_time}")
    return scores


if __name__ == '__main__':
    app.run_server(debug=True)
