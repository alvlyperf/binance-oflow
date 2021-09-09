import sys
import math

import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import plotly.graph_objects as go
from dash import callback_context
from dash.dependencies import Output, Input

from data import klines_futures, group_candles

buttons = [5, 15, 30] # Buttons representing candle size to display
app = dash.Dash()
config = {'scrollZoom': True, 'responsive': True}
styles = {
    'container': {
        'position': 'fixed',
        "top": 1,
        "left": 0,
        "bottom": 0,
        'margin-top': 0,
    },
    'graph-div': {
        'position': 'fixed',
        "top": 35,
        "left": 5,
        'right': 15,
        "bottom": 0,
        'height': '95%',
        'width': '100%'
    },
    'graph': {
        'position': 'fixed',
        "top": 35,
        "left": 5,
        'right': 15,
        "bottom": 0,
        'height': '95%',
        'width': '100%'
    },
    'button': {
        'display': 'inline-block',
        'margin-left': '5px',
        'height': '95%',
        'width': '5%'
    }}
app.layout = html.Div(

    [html.Div(
        [html.Header('liveflow', style={'display': 'inline', 'margin-left': 0, 'font-family': 'serif'})] +
        [html.Button("{}M".format(i), id=str(i),
                     style={'background-color': 'black',
                            'color': 'white',
                            'height': '20px',
                            'width': '40px',
                            'margin-left': '1px',
                            }) for i in buttons] +
        [html.H6('bid-ask',
                 style={'display': 'inline', 'margin-left': '25px', 'margin-right': '0px', 'font-family': 'serif',
                        'font-size': '2'})] +
        [daq.ToggleSwitch(id='delta-switch', value=False, size=25,
                          style={'display': 'inline-block', 'margin-left': '4px', 'margin-right': '4px', })] +
        [html.H6('delta', style={'display': 'inline', 'font-family': 'serif', 'font-size': '2'})],
        style=styles['container'])] +

    [html.Div([
        dcc.Graph(id='live-update-graph',
                  config=config, animate=False, style=styles['graph']),
        dcc.Interval(
            id='interval-component',
            interval=10000,  # in milliseconds
            n_intervals=0
        ),
        dcc.Store(id='prev_button', storage_type='Local')
    ]
        , style=styles['graph-div'])]
)


def comp(price, vol):
    res = []
    for p, v in zip(price, vol):
        res.extend(int(v / 10) * [p])
    return res


@app.callback(
    [Output('prev_button', 'data')],
    [Input(str(i), "n_clicks") for i in buttons]
)
def clicked(*args):
    return [callback_context.triggered[0]['prop_id'].split(".")[0]]


@app.callback(
    [Output('live-update-graph', 'figure')],
    [
        Input(component_id='interval-component', component_property='n_intervals'),
        Input('prev_button', 'data'),
        Input('delta-switch', 'value')
    ]
)
def func(*args):
    import datetime

    trigger = callback_context.triggered[0]
    delta = args[2]

    symbol = 'BTCUSDT'  # Symbol to display, only symbols from Binance Futures
    max = 500  # Máxima cantidad de velas devueltas por la API, valor fijo
    interval_min = 1  # Candle size in minutes to compute volume
    interval_max = int(args[1])
    price_step = 25  # Price interval to group volume
    limit = math.floor(0.75 * (500 * interval_min) / interval_max)
    interval_min_str = str(interval_min) + 'm'
    interval_max_str = str(interval_max) + 'm'

    # Collect candlestick data
    aux_df = klines_futures(symbol, limit=limit, interval=interval_max_str)

    start_aux = aux_df['Date'][0]
    start_aux = datetime.datetime.strftime(start_aux, "%Y-%m-%d %H:%M")
    df = klines_futures(symbol, start=start_aux, end='now', interval=interval_min_str)

    steps, datetime, volumes, df_violin = group_candles(df, interval_max, price_step, delta)

    fig = go.Figure(data=go.Scatter(x=datetime, y=steps, mode='markers+text', marker_symbol='line-ew', text=volumes,
                                    name='Bid&Ask Volume'))
    fig.update_traces(textposition='middle center', textfont_size=12, )
    fig.add_trace(go.Candlestick(name=symbol,
                                 x=aux_df['Date'],
                                 open=aux_df['Open'],
                                 close=aux_df['Close'],
                                 low=aux_df['Low'],
                                 high=aux_df['High'],
                                 opacity=0.5,
                                 line={'width': 0.6}
                                 # hoverinfo='skip',
                                 ))
    list_violin_buy = [comp(df['steps'], df['buy']) for df in df_violin]
    list_violin_sell = [comp(df['steps'], df['sell']) for df in df_violin]
    for i in range(len(list_violin_buy)):
        show = True if i == (len(list_violin_buy) - 1) else False
        name_buy = 'Buy Vol' if i == (len(list_violin_buy) - 1) else None
        name_sell = 'Sell Vol' if i == (len(list_violin_buy) - 1) else None
        fig.add_trace(
            go.Violin(x=len(list_violin_buy[i]) * [aux_df['Date'][i]], y=list_violin_buy[i], fillcolor='green',
                      opacity=0.1,
                      line={'width': 0.6}, name=name_buy, legendgroup='Buy', side='positive', showlegend=show))
        fig.add_trace(
            go.Violin(x=len(list_violin_sell[i]) * [aux_df['Date'][i]], y=list_violin_sell[i], fillcolor='red',
                      opacity=0.1,
                      line={'width': 0.6}, name=name_sell, legendgroup='Sell', side='negative', showlegend=show))

    fig.update_layout(
        autosize=False,
        uirevision='constant',
        dragmode='pan',
        hovermode='x unified',
        hoverdistance=0,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
        margin=go.layout.Margin(l=20,  # left margin
                                r=20,  # right margin
                                b=0,  # bottom margin
                                t=0,  # top margin)
                                )
    )
    fig.update_xaxes(showgrid=False,
                     zeroline=False,
                     rangeslider_visible=False,
                     showticklabels=True,
                     showspikes=True,
                     spikemode='across',
                     spikesnap='cursor',
                     showline=True,
                     spikedash='solid',
                     anchor='y',
                     )

    fig.update_yaxes(autorange=True,
                     fixedrange=False,
                     tickformat='.0f',
                     showspikes=True,
                     spikesnap='cursor',
                     showgrid=False,
                     zeroline=False
                     )

    fig.update_traces(xaxis="x", hoverinfo='none')

    return [fig]


if __name__ == '__main__':
    app.run_server(port=8001)
