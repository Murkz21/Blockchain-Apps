from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import datetime
import json

aa_url = 'https://api.glassnode.com/v1/metrics/addresses/active_count'

parameters = {
    'api_key' : 'YOUR GLASSNODE API KEY',
    'a' : 'BTC',
    'i' : '24h',
    'c' : 'native',
}

def get_purifed_aa_data(api_url, api_parameters):

    session = Session()
    try:
        response = session.get(api_url, params=api_parameters)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)

    df = pd.DataFrame(json.loads(response.text))
    df = df.set_index('t')
    df.index = pd.to_datetime(df.index, unit='s')
    df = df.loc[df.index > '2010-1-1']
    df.reset_index(inplace=True)
    return df

def plot_data():

    aa_data = get_purifed_aa_data(aa_url, parameters)

    fig, main_ax = plt.subplots()

    main_ax.plot(aa_data['t'], aa_data['v'], linewidth=0.2)
    main_ax.set_yscale('log')
    main_ax.grid(True)

    x = aa_data.index
    y = x**1.69
    main_ax.plot(aa_data['t'], y, linewidth=0.5)

    plt.show()

plot_data()
