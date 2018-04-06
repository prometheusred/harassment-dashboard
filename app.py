# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State, Event
from dash.exceptions import PreventUpdate
import dash_html_components as html
import dash_core_components as dcc
import dash_table_experiments as dt
from flask_caching import Cache
import numpy as np
import os
import pandas as pd
import plotly.graph_objs as go
import time
import json

from perspective import Perspective
from twitter import Twitter


perspective_key = os.environ.get('PERSPECTIVE_KEY')
perspective_client = Perspective(perspective_key)

twitter_consumer_key = os.environ.get('TWITTER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_SECRET')
twitter_client = Twitter(twitter_consumer_key, twitter_consumer_secret)

app = dash.Dash('harassment dashboard')
server = app.server
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'localhost:6379')
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})
app.css.append_css({"external_url": "https://codepen.io/prometheusred/pen/MVbJvO.css"})

colors = {
    'background': 'white',
    'text': 'black',
    'high': '#D400F9',
    'medium': '#6d60fe',
    'low': '#25C1F9',
}

explanation = 'This dashboard visualizes toxic language in Tweets and offers a way to engage to help the harassed.'

center_el = {'width': '600px',
             'textAlign': 'center',
             'margin': '50px auto'}

center_container = {'margin': '0px auto',
                    'justify-content': 'center',
                    'display': 'flex',
                    'textAlign': 'center'}

top_container = {'minWidth': '675px',
                 'minHeight': '500px',
                 'width': '100%'}

right_el = {'margin': '24px 0 0 2px',
            'height': '38px'}

left_graph = {'float': 'left',
              'width': '50%',
              'marginTop': '-70px'}

right_text = {'flex': '1',
              'overflow': 'hidden',
              'align-self': 'center',
              'textAlign': 'left'}

app.layout = html.Div([

    html.H1(children='Help the Harassed', style=center_el),

    html.P(children=explanation, style=center_el),

    html.Div(children=[

        html.Div(children=[

            html.Label(children='Twitter @handle'),
            dcc.Input(id='input-box',
                      type='text',
                      value='@')],),

        html.Button('Submit',
                    id='submit-button', style=right_el),],

             style=center_container),

    html.Div(id='toggle', children=[

        html.H2(children='Toxicity Summary',
                style={'margin': '120px 0 12px', 'textAlign': 'center'}),

        html.P(children='(click bars to see tweets)',
               style={'margin': '0 0 50px', 'textAlign': 'center'}),

        html.Div(children=[

            html.Div(children=[dcc.Graph(id='toxicity-bar')],
                     style={'margin': '0 50px auto'}),

            html.Div(dt.DataTable(
                rows=[{'text': 'click bar graph above to select tweets',
                       'author': 'na',
                       'time': 'na',
                       'toxicity': 'na'}],
                row_selectable=True,
                filterable=True,
                sortable=True,
                #row_height=40,
                selected_row_indices=[],
                id='datatable'
            ), style={'margin': '10px auto'})

        ],
                 style=top_container),

        #dcc.Graph(id='toxicity-area', style={'margin': '100px 10px 100px 10px'}),

        html.H2(children='Toxicity over time',
                style={'margin': '120px 0 12px', 'textAlign': 'center'}),

        html.P(children='(click on time-series to see tweets)',
               style={'margin': '0 0 50px', 'textAlign': 'center'}),


        html.Div(children=[

            dcc.Graph(id='toxicity-over-time', style={'minHeight': '500px','flex': '3'}),

            #dcc.Graph(id='toxicity-pie', style=left_graph),
            html.Div(children=[html.Div(children='Hover over time-series to see tweets...',
                                        id='full-text', style={'marginTop': '50px'}),


                               html.Div(id='join-link',
                                        children=[html.A(
                                            html.Button(children=['Join the conversation!']),
                                      href='https://twitter.com'),]),
            ],
                     style=right_text)

        ], style={'display': 'flex'})

    ]),

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
        #try:
        return global_store(input_value).to_json(date_format='iso',
                                                 orient='split')
        #except Exception as e:
            #print('**ERROR**')
            #print(e)
            #print(input_value)


@app.callback(Output('input-box', 'value'),
              [Input('signal', 'children')],
               state=[State('input-box', 'value')])
def reset(tweets, input_value):
    """
    Clear input box after user clicks submit.
    """
    if not input_value or input_value == '@':
        raise PreventUpdate('no data yet!')
    return '@'


# @app.callback(Output('join-link', 'children'),
#               [Input('submit-button', 'n_clicks')],
#               state=[State('input-box', 'value')])
# def make_link(n_clicks, value):
#     """
#     Create a link to target's twitter profile
#     """
#     if not value or not n_clicks or value == '@':
#         raise PreventUpdate('no data yet!')
#     return html.A(html.Button(children=['Join the conversation!']),
#                   id='join-link',
#                   href='https://twitter.com/' + value[1:len(value)])


@app.callback(Output('join-link', 'children'),
              [Input('toxicity-over-time', 'clickData'),
               Input('signal', 'children')])
def make_link_specific(clickData, tweets_json):
    """
    Create a link to target's twitter profile
    """
    if not tweets_json or not clickData:
        raise PreventUpdate('no data yet!')
    tweets_df = pd.read_json(tweets_json, orient='split')
    clicked_index = clickData['points'][0]['x'] - 1
    tweet_id = tweets_df.iloc[clicked_index].get('id_str')
    tweeter = tweets_df.iloc[clicked_index]['user'].get('screen_name')
    link = f"https://twitter.com/{tweeter}/status/{tweet_id}"
    return html.A(html.Button(children=['Join the conversation!']),
                  href=link)


@app.callback(Output('full-text', 'children'),
              [Input('toxicity-over-time', 'clickData'),
               Input('signal', 'children')])
def show_tweet(clickData, tweets_json):
    """
    Create text box to show tweet on hover
    """
    print(clickData)
    if not tweets_json or not clickData:
        raise PreventUpdate('no data yet!')
    tweets_df = pd.read_json(tweets_json, orient='split')
    click_index = clickData['points'][0]['x'] - 1
    full_text = tweets_df.iloc[click_index]['full_text']
    tweeter = tweets_df.iloc[click_index]['user'].get('screen_name')
    output_string = '**{}**: {}'.format(tweeter, full_text)
    return dcc.Markdown(output_string)


@app.callback(Output('datatable', 'rows'),
              [Input('toxicity-bar', 'clickData'),
               Input('signal', 'children')])
def make_table(clickData, tweets_json):
    """
    filter table data according to toxicity level clicked on in bar chart
    """
    if not tweets_json or not clickData:
        raise PreventUpdate('no data yet!')
    tweets_df = pd.read_json(tweets_json, orient='split')
    clicked_tox_level = clickData['points'][0]['x']
    if clicked_tox_level == 'Low':
        df = tweets_df[tweets_df['LOW_LEVEL'] == True]
    elif clicked_tox_level == 'Medium':
        df = tweets_df[tweets_df['MED_LEVEL'] == True]
    elif clicked_tox_level == 'High':
        df = tweets_df[tweets_df['HI_LEVEL'] == True]
    new_df = pd.DataFrame()

    #new_df['text'] = df.apply(make_link, axis=1)
    #new_df['text'] = html.A(html.Button('great'),href='https://twitter.com')
    new_df['text'] = df['full_text']
    new_df['author'] = df['screen_name']
    new_df['time'] = df['display_time']
    new_df['toxicity'] = df['TOXICITY_score']
    return new_df.to_dict('records')

@app.callback(Output('toggle', 'style'),
              [Input('submit-button', 'n_clicks')],
              state=[State('input-box', 'value')])
def toggle_graphs(n_clicks, value):
    """
    show graphs after first submission
    """
    if n_clicks:
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(Output('toxicity-bar', 'figure'),
              [Input('signal', 'children')],
              state=[State('input-box', 'value')])
def update_bar(tweets_json, handle):
    """
    Pull data from signal and updates aggregate bar graph

    This is using thresholds that combine toxicity and severe toxicity models
    suggested by Lucas.
    """
    if not tweets_json:
        raise PreventUpdate('no data yet!')

    tweets_df = pd.read_json(tweets_json, orient='split')

    low_count = tweets_df['LOW_LEVEL'].value_counts().get(True, 0)
    med_count = tweets_df['MED_LEVEL'].value_counts().get(True, 0)
    hi_count = tweets_df['HI_LEVEL'].value_counts().get(True, 0)
    begin_date = tweets_df['display_time'].iloc[-1]
    end_date = tweets_df['display_time'].iloc[0]
    title = f"tweets at {handle}: {begin_date}  –  {end_date} (UTC)"

    data = dict(
        type='bar',
        x=['Low', 'Medium', 'High'],
        y=[low_count, med_count, hi_count],
        marker=dict(
            color=[colors['low'],
                   colors['medium'],
                   colors['high']])
    )

    return {
        'data': [data],
        'layout': dict(
            type='layout',
            title=title,
            xaxis={'title': 'toxicity level'},
            yaxis={'title': 'count'},
        )
    }

'''
TODO: stacked area chart with buckets of < 10 tweets
'''

# @app.callback(Output('toxicity-area', 'figure'),
#               [Input('signal', 'children')],
#                state=[State('input-box', 'value')])
# def update_area(tweets_json, handle):
#     """
#     Pulls data from signal and updates area chart
#     """
#     if not tweets_json:
#         raise PreventUpdate('no data yet!')
#     tweets_df = pd.read_json(tweets_json, orient='split')

#     x = list(range(1, len(tweets_df) + 1))

#     step = int(len(tweets_df) / BIN_SIZE)
#     stop = len(tweets_df) + step
#     labels = range(0, stop, step)

#     #low_toxicity = tweets_df[]


#     low_trace = dict(
#         type='scatter',
#         name='low',
#         x=x,
#         y=low_count,
#         text=low_count,
#         mode='lines',
#         fill='tonexty',
#     )
#     med_trace = dict(
#         type='scatter',
#         name='medium',
#         x=x,
#         y=low_count + med_count,
#         text=med_count,
#         mode='lines',
#         fill='tonexty',
#     )
#     hi_trace = dict(
#         type='scatter',
#         name='high',
#         x=x,
#         y=low_count + med_count + hi_count,
#         text=hi_count,
#         mode='lines',
#         fill='tonexty',
#     )


#     return {
#         'data': [low_trace, med_trace, hi_trace],
#         'layout': dict(
#             type='layout',
#             title='Cumulative toxicity levels over time',
#             showLegend=True,
#             yaxis=dict(
#                 type='linear',
#                 range=[1, 100],
#                 dtick=20,
#             )
#         )
#     }

#     layout = go.Layout(
#     showlegend=True,
#     xaxis=dict(
#         type='category',
#     ),
#     yaxis=dict(
#         type='linear',
#         range=[1, 100],
#         dtick=20,
#         ticksuffix='%'
#     )
# )


@app.callback(Output('toxicity-over-time', 'figure'),
              [Input('signal', 'children')],
               state=[State('input-box', 'value')])
def update_graph(tweets_json, handle):
    """
    Pulls data from signal and updates graph

    Args:
        tweets_json(json): the data for a given @handle

    Returns: dictionary that defines line/scatter graph with given data
    """
    if not tweets_json:
        raise PreventUpdate('no data yet!')
    tweets_df = pd.read_json(tweets_json, orient='split')
    x = list(range(1, len(tweets_df) + 1))

    toxicity_trace = dict(
        x=x,
        y=tweets_df['TOXICITY_score'],
        mode='lines',
        fill='tonexty',
        name='toxicity',
        line=dict(width=0.5,
                 color='rgb(111, 200, 219)'),
        type='scatter'
    )

    return {
        'data': [toxicity_trace],
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

@cache.memoize(timeout=60*30)  # 30 minutes
def global_store(input_value):
    tweet_start = time.time()
    tweets_df = twitter_client.tweets_at(input_value)
    tweet_end = time.time()
    tweet_time = tweet_end - tweet_start

    if not tweets_df.empty:
        score_start = time.time()
        #tweets_df = perspective_client.scores(tweets_df)
        tweets_df = perspective_client.async_scores(tweets_df)
        score_end = time.time()
        score_time = score_end - score_start

        print(f"tweet request time: {tweet_time}")
        print(f"score request time: {score_time}")
        return tweets_df

if __name__ == '__main__':
    app.run_server(debug=True, processes=6)
